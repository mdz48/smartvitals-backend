from fastapi import APIRouter, Depends, HTTPException, status
from datetime import timedelta

from app.models.medicalRecord import MedicalRecord
from app.routes.medicalRecordRoutes import get_patient_medical_records, get_doctor_medical_records
from app.models.user import User

from app.shared.config.database import SessionLocal
from sqlalchemy.orm import Session, joinedload
from app.shared.config.database import get_db
from app.shared.config.middleware.security import get_current_user

from app.shared.services.stadisticsService import get_medical_record_statistics

stadisticsRouter = APIRouter()


# Ruta para obtener la estadistica de un paciente en base a sus expedientes
@stadisticsRouter.get("/statistics/{patient_id}", status_code=200)
async def get_patient_statistics(patient_id: int, db: Session = Depends(get_db)):
    records = await get_patient_medical_records(patient_id, db)
    if not records:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No se encontraron registros médicos para este paciente")
    statistics = await get_medical_record_statistics(db, records)
    return statistics

# Rutas para obtener las estadísticas de los pacientes de un doctor
@stadisticsRouter.get("/statistics/{doctor_id}/patients", tags=["stadistics"], status_code=200)
async def get_doctor_patients_statistics(doctor_id: int, db: Session = Depends(get_db)):
    records = await get_doctor_medical_records(doctor_id, db)
    if not records:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No se encontraron registros médicos para este doctor")
    statistics = await get_medical_record_statistics(db, records)
    return statistics

# Ruta para obtener la estadisica de los registros medicos dentro de un rango de fechas de un paciente
@stadisticsRouter.get("/statistics/{patient_id}/range", tags=["stadistics"], status_code=200)
async def get_medical_records_by_date_range(patient_id: int, start_date: str, end_date: str, db: Session = Depends(get_db)):
    records = db.query(MedicalRecord).filter(
        MedicalRecord.patient_id == patient_id,
        MedicalRecord.created_at >= start_date,
        MedicalRecord.created_at <= end_date
    ).all()
    
    if not records:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No se encontraron registros médicos en el rango de fechas especificado")
    
    stadistics = await get_medical_record_statistics(db, records)
    if not stadistics:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No se encontraron estadísticas para los registros médicos en el rango de fechas especificado")
    
    return stadistics

# Ruta para obtener las estadísticas de un doctor dentro de un rango de fechas
@stadisticsRouter.get("/statistics/{doctor_id}/patients/range", tags=["stadistics"], status_code=200)
async def get_doctor_statistics_by_date_range(doctor_id: int, start_date: str, end_date: str, db: Session = Depends(get_db)):
    records = await get_doctor_medical_records(doctor_id, db)
    if not records:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No se encontraron registros médicos para este doctor")
    statistics = await get_medical_record_statistics(db, records, start_date, end_date)
    return statistics