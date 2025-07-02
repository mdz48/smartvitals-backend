from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from typing import Optional
import logging

from app.shared.services.sensor_service import sensor_service
from app.shared.config.middleware.security import get_current_user
from app.models.user import User
from app.schemas.medicalRecordSchema import medicalRecordResponseSchema

sensorRouter = APIRouter()

class SensorConfigSchema(BaseModel):
    patient_id: int
    doctor_id: Optional[int] = None

class SensorStatusSchema(BaseModel):
    temperatura: Optional[float] = None
    oxigeno: Optional[float] = None
    presion: Optional[float] = None
    ritmo_cardiaco: Optional[float] = None
    current_patient_id: Optional[int] = None
    current_doctor_id: Optional[int] = None

class MedicalRecordCreateFromSensorsSchema(BaseModel):
    diagnosis: Optional[str] = None
    treatment: Optional[str] = None
    notes: Optional[str] = None

@sensorRouter.post("/sensors/configure", status_code=200, tags=["sensors"])
async def configure_sensors(
    config: SensorConfigSchema,
    current_user: User = Depends(get_current_user)
):
    """
    Configura el paciente y doctor para recibir datos de sensores.
    Solo doctores pueden configurar sensores.
    """
    if current_user.role.value != 'doctor':
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Solo los doctores pueden configurar sensores"
        )
    try:
        sensor_service.set_patient_and_doctor(
            patient_id=config.patient_id,
            doctor_id=config.doctor_id or current_user.id
        )
        logging.info(f"Sensores configurados para paciente {config.patient_id} por doctor {current_user.id}")
        return {
            "message": "Sensores configurados exitosamente",
            "patient_id": config.patient_id,
            "doctor_id": config.doctor_id or current_user.id
        }
    except Exception as e:
        logging.error(f"Error al configurar sensores: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error al configurar sensores"
        )

@sensorRouter.get("/sensors/status", response_model=SensorStatusSchema, tags=["sensors"])
async def get_sensor_status(current_user: User = Depends(get_current_user)):
    """
    Obtiene el estado actual de los sensores y la configuración.
    """
    try:
        # Devuelve el último valor recibido de cada sensor
        return SensorStatusSchema(
            temperatura=sensor_service.sensor_data['temperatura'][-1] if sensor_service.sensor_data['temperatura'] else None,
            oxigeno=sensor_service.sensor_data['oxigeno'][-1] if sensor_service.sensor_data['oxigeno'] else None,
            presion=sensor_service.sensor_data['presion'][-1] if sensor_service.sensor_data['presion'] else None,
            ritmo_cardiaco=sensor_service.sensor_data['ritmo_cardiaco'][-1] if sensor_service.sensor_data['ritmo_cardiaco'] else None,
            current_patient_id=sensor_service.current_patient_id,
            current_doctor_id=sensor_service.current_doctor_id
        )
    except Exception as e:
        logging.error(f"Error al obtener estado de sensores: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error al obtener estado de sensores"
        )

@sensorRouter.post("/sensors/save-medical-record", response_model=medicalRecordResponseSchema, tags=["sensors"])
async def save_medical_record_from_sensors(
    data: MedicalRecordCreateFromSensorsSchema,
    current_user: User = Depends(get_current_user)
):
    """
    Crea un expediente médico con el promedio de los datos acumulados y limpia los datos.
    """
    record = sensor_service.create_medical_record_with_averages(
        diagnosis=data.diagnosis,
        treatment=data.treatment,
        notes=data.notes
    )
    if not record:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No hay datos suficientes para crear el expediente médico o no hay paciente configurado."
        )
    return record

@sensorRouter.post("/sensors/reset", status_code=200, tags=["sensors"])
async def reset_sensor_data(current_user: User = Depends(get_current_user)):
    """
    Reinicia los datos de sensores acumulados.
    Solo doctores pueden reiniciar los datos.
    """
    if current_user.role.value != 'doctor':
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Solo los doctores pueden reiniciar los datos de sensores"
        )
    try:
        sensor_service._reset_sensor_data()
        logging.info("Datos de sensores reiniciados exitosamente")
        return {
            "message": "Datos de sensores reiniciados exitosamente"
        }
    except Exception as e:
        logging.error(f"Error al reiniciar datos de sensores: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error al reiniciar datos de sensores"
        ) 