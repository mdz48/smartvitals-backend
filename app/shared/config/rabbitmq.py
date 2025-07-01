import os
import pika
import json
import logging
from typing import Dict, Any
from dotenv import load_dotenv

load_dotenv()

# Configuración de RabbitMQ
RABBITMQ_HOST = os.getenv('RABBITMQ_HOST', 'localhost')
RABBITMQ_PORT = int(os.getenv('RABBITMQ_PORT', '5672'))
RABBITMQ_USER = os.getenv('RABBITMQ_USER', 'guest')
RABBITMQ_PASSWORD = os.getenv('RABBITMQ_PASSWORD', 'guest')
RABBITMQ_VIRTUAL_HOST = os.getenv('RABBITMQ_VIRTUAL_HOST', '/')

# Nombres de las colas y routing keys
QUEUES = {
    'temperatura': 'temperatura',
    'oxigeno': 'oxigeno', 
    'presion': 'presion',
    'ritmo_cardiaco': 'ritmo_cardiaco'
}

class RabbitMQConnection:
    def __init__(self):
        self.connection = None
        self.channel = None
        self.setup_connection()
    
    def setup_connection(self):
        """Establece la conexión con RabbitMQ"""
        try:
            # Credenciales
            credentials = pika.PlainCredentials(RABBITMQ_USER, RABBITMQ_PASSWORD)
            
            # Parámetros de conexión
            parameters = pika.ConnectionParameters(
                host=RABBITMQ_HOST,
                port=RABBITMQ_PORT,
                virtual_host=RABBITMQ_VIRTUAL_HOST,
                credentials=credentials,
                heartbeat=600,
                blocked_connection_timeout=300
            )
            
            # Crear conexión
            self.connection = pika.BlockingConnection(parameters)
            self.channel = self.connection.channel()
            
            # Declarar el exchange
            self.channel.exchange_declare(
                exchange='sensores_exchange',
                exchange_type='topic',
                durable=True
            )
            
            # Declarar las colas y vincularlas al exchange
            for queue_name in QUEUES.values():
                self.channel.queue_declare(queue=queue_name, durable=True)
                # Vincular la cola al exchange con su routing key
                self.channel.queue_bind(
                    exchange='sensores_exchange',
                    queue=queue_name,
                    routing_key=queue_name
                )
            
            logging.info(f"Conexión establecida con RabbitMQ en {RABBITMQ_HOST}:{RABBITMQ_PORT}")
            
        except Exception as e:
            logging.error(f"Error al conectar con RabbitMQ: {e}")
            raise
    
    def publish_message(self, queue_name: str, message: Dict[str, Any]):
        """Publica un mensaje en una cola específica"""
        try:
            if not self.connection or self.connection.is_closed:
                self.setup_connection()
            
            # Convertir mensaje a JSON
            message_body = json.dumps(message, ensure_ascii=False)
            
            # Publicar mensaje
            self.channel.basic_publish(
                exchange='sensores_exchange',
                routing_key=queue_name,
                body=message_body,
                properties=pika.BasicProperties(
                    delivery_mode=2,  # Hacer el mensaje persistente
                )
            )
            
            logging.info(f"Mensaje publicado en cola {queue_name}: {message}")
            
        except Exception as e:
            logging.error(f"Error al publicar mensaje en cola {queue_name}: {e}")
            raise
    
    def consume_messages(self, queue_name: str, callback):
        """Consume mensajes de una cola específica"""
        try:
            if not self.connection or self.connection.is_closed:
                self.setup_connection()
            
            # Configurar callback
            self.channel.basic_consume(
                queue=queue_name,
                on_message_callback=callback,
                auto_ack=False
            )
            
            logging.info(f"Iniciando consumo de mensajes de la cola: {queue_name}")
            
        except Exception as e:
            logging.error(f"Error al configurar consumo de cola {queue_name}: {e}")
            raise
    
    def start_consuming(self):
        """Inicia el consumo de mensajes"""
        try:
            self.channel.start_consuming()
        except KeyboardInterrupt:
            self.stop_consuming()
        except Exception as e:
            logging.error(f"Error durante el consumo de mensajes: {e}")
            raise
    
    def stop_consuming(self):
        """Detiene el consumo de mensajes"""
        if self.channel:
            self.channel.stop_consuming()
        if self.connection and not self.connection.is_closed:
            self.connection.close()
        logging.info("Consumo de mensajes detenido")
    
    def close(self):
        """Cierra la conexión"""
        if self.connection and not self.connection.is_closed:
            self.connection.close()
        logging.info("Conexión con RabbitMQ cerrada")

# Instancia global
rabbitmq_connection = RabbitMQConnection() 