import json
import logging
from typing import Dict, Any, Optional
from datetime import datetime
from sqlalchemy.orm import Session
from app.models.medicalRecord import MedicalRecord
from app.shared.config.database import SessionLocal
import asyncio

class SensorService:
    def __init__(self):
        self.sensor_data = {
            'temperatura': [],
            'oxigeno': [],
            'presion': [],
            'ritmo_cardiaco': []
        }
        self.current_patient_id = None
        self.current_doctor_id = None
        self.websocket_manager = None
        self.main_event_loop = None
    
    def set_websocket_manager(self, manager):
        """Establece el manager de WebSocket para enviar datos"""
        self.websocket_manager = manager
        logging.info("WebSocket manager configurado en SensorService")
    
    def set_patient_and_doctor(self, patient_id: int, doctor_id: int = None):
        """Establece el paciente y doctor actual para los datos de sensores"""
        self.current_patient_id = patient_id
        self.current_doctor_id = doctor_id
        logging.info(f"Paciente configurado: {patient_id}, Doctor: {doctor_id}")
    
    def process_mqtt_message(self, topic: str, payload: str):
        """Procesa un mensaje MQTT recibido en un topic de sensor"""
        try:
            message_data = json.loads(payload)
            logging.info(f"Procesando mensaje MQTT de {topic}: {message_data}")
            sensor_value = self._extract_sensor_value(topic, message_data)
            if sensor_value is not None:
                self.sensor_data[topic].append(sensor_value)
                logging.info(f"Valor acumulado para {topic}: {self.sensor_data[topic]}")
                
                # Enviar por WebSocket si hay clientes conectados
                self._send_to_websocket(topic, sensor_value)
                
        except json.JSONDecodeError as e:
            logging.error(f"Error al parsear JSON del mensaje de {topic}: {e}")
        except Exception as e:
            logging.error(f"Error al procesar mensaje de {topic}: {e}")
    
    def _send_to_websocket(self, topic: str, value: float):
        """Envía datos al WebSocket si hay conexiones activas"""
        try:
            if self.websocket_manager and self.websocket_manager.active_connections:
                data_to_send = {
                    "topic": topic,
                    "value": value,
                    "timestamp": datetime.now().isoformat(),
                    "patient_id": self.current_patient_id,
                    "doctor_id": self.current_doctor_id
                }
                logging.info(f"Enviando al WebSocket: {data_to_send}")
                if self.main_event_loop and self.main_event_loop.is_running():
                    asyncio.run_coroutine_threadsafe(
                        self.websocket_manager.broadcast(json.dumps(data_to_send)),
                        self.main_event_loop
                    )
                else:
                    logging.error("No hay event loop principal disponible para enviar al WebSocket.")
            else:
                logging.info(f"No hay conexiones WebSocket activas. Conexiones: {len(self.websocket_manager.active_connections) if self.websocket_manager else 0}")
        except Exception as e:
            logging.error(f"Error al enviar al WebSocket: {e}")
    
    def _extract_sensor_value(self, topic: str, message_data: Dict[str, Any]) -> Optional[float]:
        """Extrae el valor del sensor del mensaje"""
        try:
            # Mapeo de nombres de cola a claves en el mensaje
            value_keys = {
                'temperatura': ['temperature', 'temperatura', 'temp', 'value'],
                'oxigeno': ['oxygen_saturation', 'oxigeno', 'saturation', 'value'],
                'presion': ['blood_pressure', 'presion', 'pressure', 'value'],
                'ritmo_cardiaco': ['heart_rate', 'ritmo_cardiaco', 'heartrate', 'value']
            }
            
            keys_to_try = value_keys.get(topic, ['value'])
            
            for key in keys_to_try:
                if key in message_data:
                    value = message_data[key]
                    if isinstance(value, (int, float)):
                        return float(value)
                    elif isinstance(value, str):
                        try:
                            return float(value)
                        except ValueError:
                            continue
            
            logging.warning(f"No se pudo extraer valor de sensor para {topic} en: {message_data}")
            return None
            
        except Exception as e:
            logging.error(f"Error al extraer valor de sensor {topic}: {e}")
            return None
    
    def get_sensor_averages(self) -> Dict[str, Optional[float]]:
        """Devuelve el promedio de cada sensor o None si no hay datos"""
        return {
            sensor: (sum(values) / len(values) if values else None)
            for sensor, values in self.sensor_data.items()
        }
    
    def create_medical_record_with_averages(self, diagnosis: Optional[str] = None, treatment: Optional[str] = None, notes: Optional[str] = None):
        """Crea un registro médico con el promedio de los datos acumulados y limpia los datos"""
        if not self.current_patient_id:
            logging.error("No hay paciente configurado para crear registro médico")
            return None
        averages = self.get_sensor_averages()
        if not all(averages.values()):
            logging.error("No hay datos suficientes para crear el expediente médico")
            return None
        try:
            db = SessionLocal()
            medical_record = MedicalRecord(
                patient_id=self.current_patient_id,
                doctor_id=self.current_doctor_id,
                temperature=averages['temperatura'],
                blood_pressure=averages['presion'],
                oxygen_saturation=averages['oxigeno'],
                heart_rate=averages['ritmo_cardiaco'],
                diagnosis=diagnosis,
                treatment=treatment,
                notes=notes
            )
            db.add(medical_record)
            db.commit()
            db.refresh(medical_record)
            logging.info(f"Registro médico creado exitosamente: ID {medical_record.id}")
            self._reset_sensor_data()
            return medical_record
        except Exception as e:
            logging.error(f"Error al crear registro médico: {e}")
            if db:
                db.rollback()
            return None
        finally:
            if db:
                db.close()
    
    def _reset_sensor_data(self):
        """Reinicia los datos de sensores después de crear un registro"""
        self.sensor_data = {
            'temperatura': [],
            'oxigeno': [],
            'presion': [],
            'ritmo_cardiaco': []
        }
        logging.info("Datos de sensores reiniciados")

# Instancia global del servicio
sensor_service = SensorService() 