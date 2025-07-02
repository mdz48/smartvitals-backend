from fastapi import FastAPI, Depends,status, HTTPException
from sqlalchemy.orm import Session
from fastapi.middleware.cors import CORSMiddleware
import logging
import threading
from app.shared.config.mqtt import get_mqtt_client, SENSOR_TOPICS, MQTT_HOST, MQTT_PORT
from app.shared.services.sensor_service import sensor_service
import asyncio

from app.shared.config.database import engine, Base, SessionLocal

from app.routes.userRoutes import userRouter
from app.routes.medicalRecordRoutes import medicalRecordRouter
from app.routes.sensorRoutes import sensorRouter
from app.routes.sensorWs import wsRouter, manager
from app.shared.services.sensor_service import sensor_service

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

app = FastAPI()

# Conectar WebSocket manager con SensorService
sensor_service.set_websocket_manager(manager)
logging.info("WebSocket manager conectado con SensorService")

app.include_router(userRouter, tags=["users"])
app.include_router(medicalRecordRouter, tags=["medical_records"])
app.include_router(sensorRouter, tags=["sensors"])
app.include_router(wsRouter)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # Cambiar en producción para permitir solo dominios específicos
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

Base.metadata.create_all(bind=engine)

def on_connect(client, userdata, flags, rc):
    if rc == 0:
        for topic in SENSOR_TOPICS:
            client.subscribe(topic)
    # ...

def on_message(client, userdata, msg):
    payload = msg.payload.decode('utf-8')
    sensor_service.process_mqtt_message(msg.topic, payload)

def start_mqtt_consumer():
    client = get_mqtt_client(on_connect, on_message)
    client.connect(MQTT_HOST, MQTT_PORT, 60)
    client.loop_forever()

# Al final de tu main.py, después de crear la app:
threading.Thread(target=start_mqtt_consumer, daemon=True).start()

main_event_loop = asyncio.get_event_loop()
sensor_service.main_event_loop = main_event_loop