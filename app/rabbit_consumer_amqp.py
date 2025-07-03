import pika
import json
import os
import asyncio

def start_rabbit_consumer(manager):
    RABBIT_HOST = os.getenv('RABBITMQ_HOST')
    RABBIT_PORT = int(os.getenv('RABBITMQ_PORT', '5672'))
    RABBIT_USER = os.getenv('RABBITMQ_USER')
    RABBIT_PASS = os.getenv('RABBITMQ_PASSWORD')
    EXCHANGE = 'sensores_exchange'

    credentials = pika.PlainCredentials(RABBIT_USER, RABBIT_PASS)
    connection = pika.BlockingConnection(pika.ConnectionParameters(RABBIT_HOST, RABBIT_PORT, '/', credentials))
    channel = connection.channel()
    channel.exchange_declare(exchange=EXCHANGE, exchange_type='topic', durable=True)
    result = channel.queue_declare(queue='', exclusive=True)
    queue_name = result.method.queue
    channel.queue_bind(exchange=EXCHANGE, queue=queue_name)

    def callback(ch, method, properties, body):
        try:
            data = json.loads(body)
        except Exception:
            data = body.decode('utf-8')
        loop = manager.main_event_loop
        if loop and loop.is_running():
            asyncio.run_coroutine_threadsafe(
                manager.broadcast(json.dumps(data)),
                loop
            )

    channel.basic_consume(queue=queue_name, on_message_callback=callback, auto_ack=True)
    channel.start_consuming() 