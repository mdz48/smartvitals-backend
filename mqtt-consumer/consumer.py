# mqtt-consumer/consumer.py
import paho.mqtt.client as mqtt
import pika
import json
import os

# Configuración MQTT
MQTT_HOST = os.getenv('RABBITMQ_HOST')
MQTT_PORT = int(os.getenv('MQTT_PORT', '1883'))

# Configuración RabbitMQ (AMQP)
RABBIT_HOST = os.getenv('RABBITMQ_HOST')
RABBIT_PORT = int(os.getenv('RABBITMQ_PORT', '5672'))
RABBIT_USER = os.getenv('RABBITMQ_USER')
RABBIT_PASS = os.getenv('RABBITMQ_PASSWORD')
EXCHANGE = 'sensores_exchange'

# Conexión a RabbitMQ (AMQP)
credentials = pika.PlainCredentials(RABBIT_USER, RABBIT_PASS)
connection = pika.BlockingConnection(pika.ConnectionParameters(RABBIT_HOST, RABBIT_PORT, '/', credentials))
channel = connection.channel()
channel.exchange_declare(exchange=EXCHANGE, exchange_type='topic', durable=True)

def on_message(client, userdata, msg):
    # Reenvía el mensaje recibido por MQTT a RabbitMQ (AMQP)
    channel.basic_publish(exchange=EXCHANGE, routing_key='', body=msg.payload)

mqtt_client = mqtt.Client()
mqtt_client.on_message = on_message
mqtt_client.connect(MQTT_HOST, MQTT_PORT, 60)
mqtt_client.subscribe("temperatura")
mqtt_client.subscribe("oxigeno")
mqtt_client.subscribe("presion")
mqtt_client.subscribe("ritmo_cardiaco")
mqtt_client.loop_forever()