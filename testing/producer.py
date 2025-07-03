import pika
import json
from dotenv import load_dotenv
import os
load_dotenv()

# Configuración de RabbitMQ
RABBITMQ_HOST = os.getenv('RABBITMQ_HOST')
RABBITMQ_USER = os.getenv('RABBITMQ_USER')
RABBITMQ_PASSWORD = os.getenv('RABBITMQ_PASSWORD')
EXCHANGE = 'sensores_exchange'
TOPICS = ['temperatura', 'oxigeno', 'presion', 'ritmo_cardiaco']

# Conexión a RabbitMQ
credentials = pika.PlainCredentials(RABBITMQ_USER, RABBITMQ_PASSWORD)
parameters = pika.ConnectionParameters(host=RABBITMQ_HOST, credentials=credentials)
connection = pika.BlockingConnection(parameters)
channel = connection.channel()

# Declarar el exchange tipo 'topic'
channel.exchange_declare(exchange=EXCHANGE, exchange_type='topic', durable=True)

# Función para enviar un mensaje a un topic
def send_message(topic, data):
    message = json.dumps(data)
    channel.basic_publish(
        exchange=EXCHANGE,
        routing_key=topic,
        body=message,
        properties=pika.BasicProperties(delivery_mode=2)  # Hacer el mensaje persistente
    )
    print(f"Mensaje enviado a '{topic}': {message}")

# Ejemplo de envío de mensajes a cada topic
data_examples = {
    'temperatura': {'temperature': 36.5},
    'oxigeno': {'oxigen': 98},
    'presion': {'pressure': 120},
    'ritmo_cardiaco': {'heart_rate': 75}
}

for topic in TOPICS:
    send_message(topic, data_examples[topic])

connection.close()
