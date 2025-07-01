import os
from dotenv import load_dotenv
import paho.mqtt.client as mqtt

load_dotenv()

MQTT_HOST = os.getenv('RABBITMQ_HOST')
MQTT_PORT = int(os.getenv('MQTT_PORT'))
MQTT_USER = os.getenv('RABBITMQ_USER')
MQTT_PASSWORD = os.getenv('RABBITMQ_PASSWORD')

# Topics de los sensores
SENSOR_TOPICS = [
    'temperatura',
    'oxigeno',
    'presion',
    'ritmo_cardiaco'
]

def get_mqtt_client(on_connect, on_message):
    client = mqtt.Client()
    client.username_pw_set(MQTT_USER, MQTT_PASSWORD)
    client.on_connect = on_connect
    client.on_message = on_message
    return client 