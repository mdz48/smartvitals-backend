import json
import logging
from typing import Dict, Any
from datetime import datetime
from sqlalchemy.orm import Session
from app.models.medicalRecord import MedicalRecord
from app.shared.config.database import SessionLocal

class SensorService:
    def __init__(self):
        self.sensor_data = {
            'temperatura': None,
            'oxigeno': None,
            'presion': None,
            'ritmo_cardiaco': None
        }
        self.current_patient_id = None
        self.current_doctor_id = None
    
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
                self.sensor_data[topic] = sensor_value
                if self._has_complete_sensor_data():
                    self._create_medical_record()
                    self._reset_sensor_data()
        except json.JSONDecodeError as e:
            logging.error(f"Error al parsear JSON del mensaje de {topic}: {e}")
        except Exception as e:
            logging.error(f"Error al procesar mensaje de {topic}: {e}")
    
    def _extract_sensor_value(self, topic: str, message_data: Dict[str, Any]) -> float:
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
    
    def _has_complete_sensor_data(self) -> bool:
        """Verifica si tenemos todos los datos de sensores necesarios"""
        return all(value is not None for value in self.sensor_data.values())
    
    def _create_medical_record(self):
        """Crea un registro médico con los datos de los sensores"""
        if not self.current_patient_id:
            logging.error("No hay paciente configurado para crear registro médico")
            return
        
        try:
            db = SessionLocal()
            
            # Crear el registro médico
            medical_record = MedicalRecord(
                patient_id=self.current_patient_id,
                doctor_id=self.current_doctor_id,
                temperature=self.sensor_data['temperatura'],
                blood_pressure=self.sensor_data['presion'],
                oxygen_saturation=self.sensor_data['oxigeno'],
                heart_rate=self.sensor_data['ritmo_cardiaco'],
                diagnosis="",  # Vacío por defecto
                treatment="",  # Vacío por defecto
                notes=f"Registro automático generado desde sensores - {datetime.now()}"
            )
            
            db.add(medical_record)
            db.commit()
            db.refresh(medical_record)
            
            logging.info(f"Registro médico creado exitosamente: ID {medical_record.id}")
            
        except Exception as e:
            logging.error(f"Error al crear registro médico: {e}")
            if db:
                db.rollback()
        finally:
            if db:
                db.close()
    
    def _reset_sensor_data(self):
        """Reinicia los datos de sensores después de crear un registro"""
        self.sensor_data = {
            'temperatura': None,
            'oxigeno': None,
            'presion': None,
            'ritmo_cardiaco': None
        }
        logging.info("Datos de sensores reiniciados")

# Instancia global del servicio
sensor_service = SensorService() 