import pika
import json
from dotenv import load_dotenv
import os
load_dotenv()

# Configuración de RabbitMQ
RABBITMQ_HOST = os.getenv('RABBITMQ_HOST')  # Cambia esto si tu RabbitMQ está en otro host
RABBITMQ_USER = os.getenv('RABBITMQ_USER')    # Cambia por tu usuario
RABBITMQ_PASSWORD = os.getenv('RABBITMQ_PASSWORD')  # Cambia por tu contraseña
EXCHANGE = 'sensores_exchange'
TOPICS = ['temperatura', 'oxigeno', 'presion', 'ritmo_cardiaco']

# Conexión a RabbitMQ
credentials = pika.PlainCredentials(RABBITMQ_USER, RABBITMQ_PASSWORD)
parameters = pika.ConnectionParameters(host=RABBITMQ_HOST, credentials=credentials)
connection = pika.BlockingConnection(parameters)
channel = connection.channel()

# Declarar el exchange tipo 'topic' y las colas
channel.exchange_declare(exchange=EXCHANGE, exchange_type='topic', durable=True)

for topic in TOPICS:
    channel.queue_declare(queue=topic, durable=True)
    channel.queue_bind(exchange=EXCHANGE, queue=topic, routing_key=topic)

print(f"Esperando mensajes en las colas: {', '.join(TOPICS)}. Para salir presiona CTRL+C.")

def make_callback(topic_name):
    def callback(ch, method, properties, body):
        try:
            data = json.loads(body)
            print(f"[{topic_name}] Mensaje recibido: {data}")
            # Aquí puedes procesar el mensaje como quieras
        except Exception as e:
            print(f"[{topic_name}] Error procesando el mensaje: {e}")
    return callback

for topic in TOPICS:
    channel.basic_consume(queue=topic, on_message_callback=make_callback(topic), auto_ack=True)

try:
    channel.start_consuming()
except KeyboardInterrupt:
    print("Interrumpido por el usuario.")
finally:
    connection.close()
