import json
import os
import pika
import time
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from dotenv import load_dotenv
import threading
from app.shared.services.sensoresService import add_sensor_data, process_and_save_records, validar_datos, medicion_activa


load_dotenv()

app = FastAPI()
clients = set()

# Configuración de RabbitMQ
RABBITMQ_HOST = os.getenv('RABBITMQ_HOST')
RABBITMQ_USER = os.getenv('RABBITMQ_USER')
RABBITMQ_PASSWORD = os.getenv('RABBITMQ_PASSWORD')
EXCHANGE = 'amq.topic'  
TOPICS = ['temperatura', 'oxigeno', 'presion', 'ritmo_cardiaco', 'sensor']

user_ws_map = {}  # Mapa para almacenar WebSockets por usuario

def rabbitmq_consumer():
    credentials = pika.PlainCredentials(RABBITMQ_USER, RABBITMQ_PASSWORD)
    parameters = pika.ConnectionParameters(host=RABBITMQ_HOST, credentials=credentials)
    connection = pika.BlockingConnection(parameters)
    channel = connection.channel()
    channel.exchange_declare(exchange=EXCHANGE, exchange_type='topic', durable=True)
    for topic in TOPICS:
        channel.queue_declare(queue=topic, durable=True)
        channel.queue_bind(exchange=EXCHANGE, queue=topic, routing_key=topic)

    def make_callback(topic_name):
        def callback(ch, method, properties, body):
            data = json.loads(body)
            message = json.dumps({"topic": topic_name, "data": data})
            # Enviar a todos los clientes conectados
            for ws in clients.copy():
                try:
                    import asyncio
                    asyncio.run(ws.send_text(message))
                except Exception:
                    clients.discard(ws)
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
                # Enviar solo al paciente
                patient_ws = user_ws_map.get(str(data.get("patient_id")))
                if patient_ws:
                    try:
                        import asyncio
                        asyncio.run(patient_ws.send_text(alerta_msg))
                    except Exception:
                        clients.discard(patient_ws)
                # Enviar solo al doctor (si existe)
                doctor_id = data.get("doctor_id")
                if doctor_id:
                    doctor_ws = user_ws_map.get(str(doctor_id))
                    if doctor_ws:
                        try:
                            import asyncio
                            asyncio.run(doctor_ws.send_text(alerta_msg))
                        except Exception:
                            clients.discard(doctor_ws)
            add_sensor_data(
                data.get("patient_id"),
                data.get("doctor_id"),
                data.get("temperature"),
                data.get("blood_pressure"),
                data.get("oxygen_saturation"),
                data.get("heart_rate")
            )
        return callback

    for topic in TOPICS:
        channel.basic_consume(queue=topic, on_message_callback=make_callback(topic), auto_ack=True)
    channel.start_consuming()

@app.websocket("/ws/sensores")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    # Espera a que el cliente envíe su identificación
    msg = await websocket.receive_text()
    data = json.loads(msg)
    user_id = data.get("user_id")
    rol = data.get("rol")  # "paciente" o "doctor"
    if user_id:
        user_ws_map[user_id] = websocket
    clients.add(websocket)
    
    # Enviar configuración a la Raspberry Pi
    if rol == "paciente":
        # Enviar configuración de paciente a RabbitMQ
        user_config = {
            "patient_id": int(user_id),
            "doctor_id": data.get("doctor_id"),  # Si tiene doctor asignado
            "timestamp": time.time()
        }
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
            print(f"Configuración enviada a Raspberry Pi: {message}")
            connection.close()
        except Exception as e:
            print(f"Error enviando configuración: {e}")
    try:
        while True:
            msg = await websocket.receive_text()
            try:
                data = json.loads(msg)
                if data.get("action") == "start":
                    patient_id = data["patient_id"]
                    medicion_activa[patient_id] = True
                    await websocket.send_text(json.dumps({
                        "type": "info",
                        "message": f"Medición iniciada para paciente {patient_id}"
                    }))
                elif data.get("action") == "stop":
                    patient_id = data["patient_id"]
                    medicion_activa[patient_id] = False
                    await websocket.send_text(json.dumps({
                        "type": "info",
                        "message": f"Medición iniciada para paciente {patient_id}"
                    }))
            except Exception as e:
                print(f"Error procesando mensaje WebSocket: {e}")
    except WebSocketDisconnect:
        clients.discard(websocket)
        if user_id in user_ws_map:
            del user_ws_map[user_id]

# Iniciar el consumidor de RabbitMQ en un hilo aparte
threading.Thread(target=rabbitmq_consumer, daemon=True).start()