#!/usr/bin/env python3
"""
Script para consumir mensajes MQTT de RabbitMQ (plugin MQTT) y procesar datos de sensores.
"""
import logging
import signal
import sys
from app.shared.config.mqtt import get_mqtt_client, SENSOR_TOPICS, MQTT_HOST, MQTT_PORT
from app.shared.services.sensor_service import sensor_service

def on_connect(client, userdata, flags, rc):
    if rc == 0:
        logging.info("Conectado exitosamente a RabbitMQ MQTT!")
        for topic in SENSOR_TOPICS:
            client.subscribe(topic)
            logging.info(f"Suscrito al topic: {topic}")
    else:
        logging.error(f"Fallo la conexión MQTT, código: {rc}")

def on_message(client, userdata, msg):
    payload = msg.payload.decode('utf-8')
    logging.info(f"Mensaje recibido en {msg.topic}: {payload}")
    sensor_service.process_mqtt_message(msg.topic, payload)

def main():
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    client = get_mqtt_client(on_connect, on_message)
    client.connect(MQTT_HOST, MQTT_PORT, 60)

    def stop_loop(signum, frame):
        logging.info("Deteniendo consumidor MQTT...")
        client.disconnect()
        sys.exit(0)

    signal.signal(signal.SIGINT, stop_loop)
    signal.signal(signal.SIGTERM, stop_loop)

    logging.info("Iniciando loop MQTT...")
    client.loop_forever()

if __name__ == "__main__":
    main() 