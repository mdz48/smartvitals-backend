from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from typing import Optional
import logging

from app.shared.services.sensor_service import sensor_service
from app.shared.config.middleware.security import get_current_user
from app.models.user import User

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
        return SensorStatusSchema(
            temperatura=sensor_service.sensor_data['temperatura'],
            oxigeno=sensor_service.sensor_data['oxigeno'],
            presion=sensor_service.sensor_data['presion'],
            ritmo_cardiaco=sensor_service.sensor_data['ritmo_cardiaco'],
            current_patient_id=sensor_service.current_patient_id,
            current_doctor_id=sensor_service.current_doctor_id
        )
    except Exception as e:
        logging.error(f"Error al obtener estado de sensores: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error al obtener estado de sensores"
        )

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