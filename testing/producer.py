
import pika
import json
import time
import random
import math
from dotenv import load_dotenv
import os
load_dotenv()

# Configuración de RabbitMQ
RABBITMQ_HOST = os.getenv('RABBITMQ_HOST')
RABBITMQ_USER = os.getenv('RABBITMQ_USER')
RABBITMQ_PASSWORD = os.getenv('RABBITMQ_PASSWORD')
EXCHANGE = 'amq.topic'  # Cambiar al exchange por defecto
TOPICS = ['temperatura', 'oxigeno', 'ritmo_cardiaco']

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
    print(f"📤 Enviado a '{topic}': {message}")

# Función para generar datos variando
def generate_varying_data(cycle):
    # Datos base que varían con el tiempo
    base_temp = 36.5 + 2 * math.sin(cycle * 0.1) + random.uniform(-0.5, 0.5)
    base_oxygen = 95 + 3 * math.sin(cycle * 0.15) + random.uniform(-2, 2)
    base_heart_rate = 70 + 10 * math.sin(cycle * 0.2) + random.uniform(-5, 5)
    
    # Asegurar rangos realistas
    base_temp = max(35.0, min(39.0, base_temp))
    base_oxygen = max(85, min(100, base_oxygen))
    base_heart_rate = max(50, min(120, base_heart_rate))
    
    return {
        'temperatura': {
            'patient_id': 8,
            'doctor_id': 2,
            'temperature': round(base_temp, 1),
            'timestamp': time.time()
        },
        'oxigeno': {
            'patient_id': 8,
            'doctor_id': 3,
            'oxygen_saturation': round(base_oxygen, 1),
            'timestamp': time.time()
        },
        'ritmo_cardiaco': {
            'patient_id': 8,
            'doctor_id': 2,
            'heart_rate': round(base_heart_rate, 1),
            'timestamp': time.time()
        }
    }

# Loop principal para enviar datos cada segundo
try:
    print("🚀 Iniciando productor de datos de sensores...")
    print("📊 Enviando datos cada segundo a: temperatura, oxigeno, ritmo_cardiaco")
    print("🛑 Presiona Ctrl+C para detener")
    
    cycle = 0
    while True:
        # Generar datos variando
        data = generate_varying_data(cycle)
        
        # Enviar a cada topic
        for topic in TOPICS:
            send_message(topic, data[topic])
        
        cycle += 1
        time.sleep(1)  # Esperar 1 segundo

except KeyboardInterrupt:
    print("\n🛑 Productor detenido por el usuario.")
finally:
    connection.close()
    print("🔌 Conexión cerrada.")