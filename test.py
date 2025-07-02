import os
import paho.mqtt.publish as publish
import json
import time
from dotenv import load_dotenv
import paho.mqtt.client as mqtt

load_dotenv()

# Configuración de tu EC2
EC2_HOST = os.getenv('RABBITMQ_HOST') 
EC2_PORT = int(os.getenv('MQTT_PORT', '1883'))
USERNAME = os.getenv('RABBITMQ_USER')
PASSWORD = os.getenv('RABBITMQ_PASSWORD')

def enviar_datos_sensor():
    """Envía datos de prueba a todos los sensores"""
    
    # Datos de temperatura
    temperatura_data = {"temperature": 36.5, "timestamp": "2024-01-15T10:30:00Z"}
    publish.single(
        "temperatura", 
        json.dumps(temperatura_data), 
        hostname=EC2_HOST, 
        port=EC2_PORT, 
        auth={'username': USERNAME, 'password': PASSWORD}
    )
    print(f"Enviado temperatura: {temperatura_data}")
    
    # Datos de oxígeno
    oxigeno_data = {"oxygen_saturation": 98.5, "timestamp": "2024-01-15T10:30:00Z"}
    publish.single(
        "oxigeno", 
        json.dumps(oxigeno_data), 
        hostname=EC2_HOST, 
        port=EC2_PORT, 
        auth={'username': USERNAME, 'password': PASSWORD}
    )
    print(f"Enviado oxígeno: {oxigeno_data}")
    
    # Datos de presión
    presion_data = {"blood_pressure": 120.5, "timestamp": "2024-01-15T10:30:00Z"}
    publish.single(
        "presion", 
        json.dumps(presion_data), 
        hostname=EC2_HOST, 
        port=EC2_PORT, 
        auth={'username': USERNAME, 'password': PASSWORD}
    )
    print(f"Enviado presión: {presion_data}")
    
    # Datos de ritmo cardíaco
    ritmo_data = {"heart_rate": 75.0, "timestamp": "2024-01-15T10:30:00Z"}
    publish.single(
        "ritmo_cardiaco", 
        json.dumps(ritmo_data), 
        hostname=EC2_HOST, 
        port=EC2_PORT, 
        auth={'username': USERNAME, 'password': PASSWORD}
    )
    print(f"Enviado ritmo cardíaco: {ritmo_data}")

if __name__ == "__main__":
    print("Enviando datos de prueba a RabbitMQ en EC2...")
    enviar_datos_sensor()
    print("Datos enviados exitosamente!")