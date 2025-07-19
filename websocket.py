import json
import os
import pika
import time
import asyncio
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from dotenv import load_dotenv
import threading
import logging
from concurrent.futures import ThreadPoolExecutor
import queue
from app.shared.services.sensoresService import add_sensor_data, process_and_save_records, validar_datos, medicion_activa

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()

app = FastAPI()
clients = set()
user_ws_map = {}  # Mapa para almacenar WebSockets por usuario

# Configuración de RabbitMQ
RABBITMQ_HOST = os.getenv('RABBITMQ_HOST')
RABBITMQ_USER = os.getenv('RABBITMQ_USER')
RABBITMQ_PASSWORD = os.getenv('RABBITMQ_PASSWORD')
EXCHANGE = 'amq.topic'  
TOPICS = ['temperatura', 'oxigeno', 'presion', 'ritmo_cardiaco', 'sensor']

# Cola thread-safe para comunicación entre hilos (usando queue estándar)
message_queue = queue.Queue()
# Variable global para el event loop principal
main_loop = None

async def websocket_sender():
    """Proceso asíncrono que envía mensajes a WebSockets"""
    while True:
        try:
            # Usar un bucle no bloqueante para revisar la cola
            try:
                message_data = message_queue.get_nowait()
            except queue.Empty:
                await asyncio.sleep(0.1)  # Esperar un poco antes de revisar de nuevo
                continue
            
            message_type = message_data.get("type")
            message = message_data.get("message")
            
            if message_type == "broadcast":
                # Enviar a todos los clientes
                disconnected_clients = set()
                for ws in clients.copy():
                    try:
                        await ws.send_text(message)
                    except Exception as e:
                        logger.error(f"Error enviando mensaje broadcast: {e}")
                        disconnected_clients.add(ws)
                
                # Limpiar clientes desconectados
                for ws in disconnected_clients:
                    clients.discard(ws)
                    
            elif message_type == "targeted":
                # Enviar a usuarios específicos
                target_users = message_data.get("target_users", [])
                for user_id in target_users:
                    user_ws = user_ws_map.get(str(user_id))
                    if user_ws:
                        try:
                            await user_ws.send_text(message)
                        except Exception as e:
                            logger.error(f"Error enviando mensaje a usuario {user_id}: {e}")
                            clients.discard(user_ws)
                            if str(user_id) in user_ws_map:
                                del user_ws_map[str(user_id)]
                                
        except Exception as e:
            logger.error(f"Error en websocket_sender: {e}")
            await asyncio.sleep(1)

def add_message_to_queue(message_type, message, target_users=None):
    """Función thread-safe para agregar mensajes a la cola"""
    try:
        message_data = {
            "type": message_type,
            "message": message,
            "target_users": target_users or []
        }
        # Usar queue.Queue estándar que es thread-safe
        message_queue.put(message_data)
        logger.debug(f"Mensaje agregado a cola: {message_type}")
    except Exception as e:
        logger.error(f"Error agregando mensaje a cola: {e}")

def rabbitmq_consumer():
    """Consumidor de RabbitMQ que corre en hilo separado"""
    max_retries = 5
    retry_delay = 5
    
    for attempt in range(max_retries):
        try:
            credentials = pika.PlainCredentials(RABBITMQ_USER, RABBITMQ_PASSWORD)
            parameters = pika.ConnectionParameters(
                host=RABBITMQ_HOST, 
                credentials=credentials,
                heartbeat=600,
                blocked_connection_timeout=300
            )
            connection = pika.BlockingConnection(parameters)
            channel = connection.channel()
            
            # Configurar exchange y colas
            channel.exchange_declare(exchange=EXCHANGE, exchange_type='topic', durable=True)
            for topic in TOPICS:
                channel.queue_declare(queue=topic, durable=True)
                channel.queue_bind(exchange=EXCHANGE, queue=topic, routing_key=topic)

            def make_callback(topic_name):
                def callback(ch, method, properties, body):
                    try:
                        data = json.loads(body)
                        logger.info(f"Mensaje recibido en topic {topic_name}: {data}")
                        
                        # Mensaje para broadcast
                        broadcast_message = json.dumps({"topic": topic_name, "data": data})
                        add_message_to_queue("broadcast", broadcast_message)
                        
                        # Validar datos y enviar alertas si es necesario
                        alertas = validar_datos(
                            data.get("temperature"),
                            data.get("blood_pressure"),
                            data.get("oxygen_saturation"),
                            data.get("heart_rate")
                        )
                        
                        if alertas:
                            alerta_msg = json.dumps({
                                "type": "alerta",
                                "patient_id": data.get("patient_id"),
                                "doctor_id": data.get("doctor_id"),
                                "alertas": alertas
                            })
                            
                            # Enviar alerta a usuarios específicos
                            target_users = []
                            if data.get("patient_id"):
                                target_users.append(data.get("patient_id"))
                            if data.get("doctor_id"):
                                target_users.append(data.get("doctor_id"))
                            
                            if target_users:
                                add_message_to_queue("targeted", alerta_msg, target_users)
                        
                        # Guardar datos en base de datos
                        add_sensor_data(
                            data.get("patient_id"),
                            data.get("doctor_id"),
                            data.get("temperature"),
                            data.get("blood_pressure"),
                            data.get("oxygen_saturation"),
                            data.get("heart_rate")
                        )
                        
                    except json.JSONDecodeError as e:
                        logger.error(f"Error decodificando JSON: {e}")
                    except Exception as e:
                        logger.error(f"Error procesando mensaje: {e}")
                        
                return callback

            # Configurar consumidores
            for topic in TOPICS:
                channel.basic_consume(
                    queue=topic, 
                    on_message_callback=make_callback(topic), 
                    auto_ack=True
                )
            
            logger.info("Iniciando consumo de RabbitMQ...")
            channel.start_consuming()
            
        except pika.exceptions.AMQPConnectionError as e:
            logger.error(f"Error de conexión a RabbitMQ (intento {attempt + 1}/{max_retries}): {e}")
            if attempt < max_retries - 1:
                time.sleep(retry_delay)
            else:
                logger.error("No se pudo conectar a RabbitMQ después de varios intentos")
                raise
        except Exception as e:
            logger.error(f"Error inesperado en consumidor RabbitMQ: {e}")
            raise

async def send_raspberry_config(user_config):
    """Enviar configuración a Raspberry Pi de forma asíncrona"""
    try:
        credentials = pika.PlainCredentials(RABBITMQ_USER, RABBITMQ_PASSWORD)
        parameters = pika.ConnectionParameters(host=RABBITMQ_HOST, credentials=credentials)
        connection = pika.BlockingConnection(parameters)
        channel = connection.channel()
        
        message = json.dumps(user_config)
        channel.basic_publish(
            exchange=EXCHANGE,
            routing_key="user_config",
            body=message,
            properties=pika.BasicProperties(delivery_mode=2)
        )
        logger.info(f"Configuración enviada a Raspberry Pi: {message}")
        connection.close()
    except Exception as e:
        logger.error(f"Error enviando configuración: {e}")

@app.websocket("/ws/sensores")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    user_id = None
    
    try:
        # Esperar identificación del cliente
        msg = await websocket.receive_text()
        data = json.loads(msg)
        user_id = data.get("user_id")
        rol = data.get("rol")  # "paciente" o "doctor"
        
        if user_id:
            user_ws_map[str(user_id)] = websocket
        clients.add(websocket)
        
        logger.info(f"Cliente conectado: user_id={user_id}, rol={rol}")
        
        # Bucle principal de manejo de mensajes
        while True:
            msg = await websocket.receive_text()
            try:
                data = json.loads(msg)
                
                if data.get("action") == "start":
                    patient_id = data["patient_id"]
                    medicion_activa[patient_id] = True
                    
                    # Enviar configuración al Raspberry Pi
                    user_config = {
                        "patient_id": int(patient_id),
                        "doctor_id": data.get("doctor_id"),
                        "timestamp": time.time(),
                        "action": "start"
                    }
                    await send_raspberry_config(user_config)
                    
                    await websocket.send_text(json.dumps({
                        "type": "info",
                        "message": f"Medición iniciada para paciente {patient_id}"
                    }))
                    logger.info(f"Medición iniciada para paciente {patient_id}")
                    
                elif data.get("action") == "stop":
                    patient_id = data["patient_id"]
                    medicion_activa[patient_id] = False
                    
                    # Enviar configuración de stop al Raspberry Pi
                    user_config = {
                        "patient_id": int(patient_id),
                        "doctor_id": data.get("doctor_id"),
                        "timestamp": time.time(),
                        "action": "stop"
                    }
                    await send_raspberry_config(user_config)
                    
                    await websocket.send_text(json.dumps({
                        "type": "info",
                        "message": f"Medición detenida para paciente {patient_id}"
                    }))
                    logger.info(f"Medición detenida para paciente {patient_id}")
                    
                elif data.get("action") == "doctor_config":
                    # Nueva acción para configuración de doctor
                    doctor_id = data.get("doctor_id")
                    patient_id = data.get("patient_id")
                    
                    if doctor_id and patient_id:
                        # Enviar configuración al RabbitMQ con doctor_id como patient_id
                        doctor_config = {
                            "patient_id": int(doctor_id),  # Usar doctor_id como patient_id
                            "doctor_id": int(doctor_id),
                            "monitored_patient_id": int(patient_id),  # ID del paciente que está monitoreando
                            "timestamp": time.time(),
                            "config_type": "doctor_monitoring"
                        }
                        
                        await send_raspberry_config(doctor_config)
                        logger.info(f"Configuración de doctor enviada: doctor_id={doctor_id}, monitored_patient={patient_id}")
                        
                        await websocket.send_text(json.dumps({
                            "type": "info",
                            "message": f"Configuración de doctor enviada para monitorear paciente {patient_id}"
                        }))
                        
            except json.JSONDecodeError:
                logger.error("Error: Mensaje JSON inválido recibido")
            except Exception as e:
                logger.error(f"Error procesando mensaje WebSocket: {e}")
                
    except WebSocketDisconnect:
        logger.info(f"Cliente desconectado: user_id={user_id}")
    except Exception as e:
        logger.error(f"Error en WebSocket: {e}")
    finally:
        # Limpiar cliente desconectado
        clients.discard(websocket)
        if user_id and str(user_id) in user_ws_map:
            del user_ws_map[str(user_id)]

@app.on_event("startup")
async def startup_event():
    # Guardar referencia al event loop principal
    global main_loop
    main_loop = asyncio.get_event_loop()
    
    # Iniciar el sender de WebSocket
    asyncio.create_task(websocket_sender())
    
    # Iniciar el consumidor de RabbitMQ en un hilo separado
    threading.Thread(target=rabbitmq_consumer, daemon=True).start()
    
    logger.info("Servicios iniciados correctamente")

@app.on_event("shutdown")
async def shutdown_event():
    logger.info("Cerrando servicios...")