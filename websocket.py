import json
import os
import pika
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from dotenv import load_dotenv
import threading
from app.shared.services.sensoresService import add_sensor_data, process_and_save_records
from app.shared.services.sensoresService import medicion_activa

load_dotenv()

app = FastAPI()
clients = set()

# Configuración de RabbitMQ
RABBITMQ_HOST = os.getenv('RABBITMQ_HOST')
RABBITMQ_USER = os.getenv('RABBITMQ_USER')
RABBITMQ_PASSWORD = os.getenv('RABBITMQ_PASSWORD')
EXCHANGE = 'sensores_exchange'
TOPICS = ['temperatura', 'oxigeno', 'presion', 'ritmo_cardiaco']

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
            add_sensor_data(
            data["patient_id"],
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
    clients.add(websocket)
    try:
        while True:
            msg = await websocket.receive_text()
            try:
                data = json.loads(msg)
                if data.get("action") == "start":
                    patient_id = data["patient_id"]
                    medicion_activa[patient_id] = True
                    await websocket.send_text(f"Medición iniciada para paciente {patient_id}")
                elif data.get("action") == "stop":
                    patient_id = data["patient_id"]
                    medicion_activa[patient_id] = False
                    await websocket.send_text(f"Medición detenida para paciente {patient_id}")
            except Exception:
                pass  # Si no es un comando, simplemente ignóralo
    except WebSocketDisconnect:
        clients.discard(websocket)

# Iniciar el consumidor de RabbitMQ en un hilo aparte
threading.Thread(target=rabbitmq_consumer, daemon=True).start()