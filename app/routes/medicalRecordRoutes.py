from fastapi import APIRouter, Depends, HTTPException, status, Query
from datetime import timedelta, datetime

from app.models.medicalRecord import MedicalRecord
from app.schemas.medicalRecordSchema import medicalRecordSchema, medicalRecordResponseSchema, medicalRecordWithRisksResponseSchema
from app.schemas.riskSchema import RisksSchema
from app.models.user import User
from app.models.doctorPatient import DoctorPatient
from app.models.medicalFile import MedicalFile
from app.schemas.medicalFileSchema import MedicalFileResponseSchema

from app.shared.config.database import SessionLocal
from sqlalchemy.orm import Session, joinedload
from app.shared.config.database import get_db
from app.shared.config.middleware.security import get_current_user

from app.shared.services.stadisticsService import get_medical_record_statistics

medicalRecordRouter = APIRouter()

# Ruta para crear un nuevo registro médico
@medicalRecordRouter.post("/medicalRecords", response_model=medicalRecordResponseSchema, status_code=201, tags=["medical_records"])
async def create_medical_record(medical_record: medicalRecordSchema, db: Session = Depends(get_db)):
    # Validar que el expediente existe
    medical_file = db.query(MedicalFile).filter(MedicalFile.id == medical_record.medical_file_id).first()
    if not medical_file:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Expediente médico no encontrado")

    try:
        medical_record_data = medical_record.model_dump()
        new_record = MedicalRecord(**medical_record_data)
        db.add(new_record)
        db.commit() 
        db.refresh(new_record)
        return new_record
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
                          detail="Error al crear el registro médico")
        
# Ruta para obtener todos los registros médicos
@medicalRecordRouter.get("/medicalRecords", response_model=list[medicalRecordResponseSchema], tags=["medical_records"], status_code=200)
async def get_medical_records(db: Session = Depends(get_db)):
    records = db.query(MedicalRecord).all()
    return records

# Ruta para obtener un registro médico por ID
@medicalRecordRouter.get("/medicalRecords/{record_id}", response_model=medicalRecordResponseSchema, tags=["medical_records"], status_code=200)
async def get_medical_record(record_id: int, db: Session = Depends(get_db)):
    record = db.query(MedicalRecord).filter(MedicalRecord.id == record_id).first()
    if not record:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Registro médico no encontrado")

    # Obtener el expediente asociado
    medical_file = db.query(MedicalFile).filter(MedicalFile.id == record.medical_file_id).first()
    medical_file_data = MedicalFileResponseSchema.model_validate(medical_file) if medical_file else None

    # Convertir el registro a dict y anidar el expediente
    record_dict = record.__dict__.copy()
    record_dict.pop("_sa_instance_state", None)
    record_dict["medical_file"] = medical_file_data
    return record_dict

# Ruta para obtener los registros médicos de un paciente específico
@medicalRecordRouter.get("/patients/{patient_id}/medicalRecords", response_model=list[medicalRecordResponseSchema], tags=["medical_records"], status_code=200)
async def get_patient_medical_records(patient_id: int, db: Session = Depends(get_db)):
    records = db.query(MedicalRecord).filter(MedicalRecord.patient_id == patient_id).all()
    if not records:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No se encontraron registros médicos para este paciente")
    return records

# Ruta para actualizar un registro médico
@medicalRecordRouter.put("/medicalRecords/{record_id}", response_model=medicalRecordResponseSchema, tags=["medical_records"], status_code=200)
async def update_medical_record(record_id: int, medical_record: medicalRecordSchema, db: Session = Depends(get_db)):
    existing_record = db.query(MedicalRecord).filter(MedicalRecord.id == record_id).first()
    if not existing_record:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Registro médico no encontrado")

    for key, value in medical_record.model_dump(exclude_unset=True).items():
        setattr(existing_record, key, value)

    db.commit()
    # Recarga el registro con las relaciones
    updated_record = db.query(MedicalRecord)\
        .options(joinedload(MedicalRecord.doctor), joinedload(MedicalRecord.patient))\
        .filter(MedicalRecord.id == record_id).first()
    return updated_record

# Ruta para obtener los registros médicos de un doctor específico
@medicalRecordRouter.get("/doctors/{doctor_id}/medicalRecords", response_model=list[medicalRecordResponseSchema], tags=["medical_records"], status_code=200)
async def get_doctor_medical_records(doctor_id: int, db: Session = Depends(get_db)):
    records = db.query(MedicalRecord).filter(MedicalRecord.doctor_id == doctor_id).all()
    if not records:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No se encontraron registros médicos para este doctor")
    return records

# Ruta para eliminar un registro médico
@medicalRecordRouter.delete("/medicalRecords/{record_id}", status_code=204, tags=["medical_records"])
async def delete_medical_record(record_id: int, db: Session = Depends(get_db)):
    record = db.query(MedicalRecord).filter(MedicalRecord.id == record_id).first()
    if not record:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Registro médico no encontrado")
    
    db.delete(record)
    db.commit()
    return {"detail": "Registro médico eliminado exitosamente"}

# Ruta para obtener los registros medicos dentro de un rango de fechas de un paciente
@medicalRecordRouter.get("/patients/{patient_id}/medicalRecords/range", response_model=list[medicalRecordResponseSchema], tags=["medical_records"], status_code=200)
async def get_medical_records_by_date_range(
    patient_id: int, 
    start_date: str = Query(..., description="Formato: YYYY-MM-DD"), 
    end_date: str = Query(..., description="Formato: YYYY-MM-DD"), 
    db: Session = Depends(get_db)
):
    # Validar formato de fecha
    try:
        start = datetime.strptime(start_date, "%Y-%m-%d")
        end = datetime.strptime(end_date, "%Y-%m-%d")
    except ValueError:
        raise HTTPException(status_code=400, detail="Formato de fecha inválido. Usa YYYY-MM-DD.")

    # Validar rango
    if start > end:
        raise HTTPException(status_code=400, detail="La fecha de inicio no puede ser mayor que la fecha de fin.")

    end = end + timedelta(days=1)
    # Buscar registros en el rango (incluyendo ambos extremos)
    records = db.query(MedicalRecord).filter(
        MedicalRecord.patient_id == patient_id,
        MedicalRecord.created_at >= start,
        MedicalRecord.created_at < end
    ).all()

    return records

# Ruta para obtener los registros médicos dentro de un rango de fechas de los pacientes de un doctor
@medicalRecordRouter.get("/doctors/{doctor_id}/medicalRecords/range", response_model=list[medicalRecordResponseSchema], tags=["medical_records"], status_code=200)
async def get_doctor_medical_records_by_date_range(
    doctor_id: int, 
    start_date: str = Query(..., description="Formato: YYYY-MM-DD"), 
    end_date: str = Query(..., description="Formato: YYYY-MM-DD"), 
    db: Session = Depends(get_db)
):
    # Validar formato de fecha
    try:
        start = datetime.strptime(start_date, "%Y-%m-%d")
        end = datetime.strptime(end_date, "%Y-%m-%d")
    except ValueError:
        raise HTTPException(status_code=400, detail="Formato de fecha inválido. Usa YYYY-MM-DD.")

    # Validar rango
    if start > end:
        raise HTTPException(status_code=400, detail="La fecha de inicio no puede ser mayor que la fecha de fin.")

    end = end + timedelta(days=1)
    # Buscar registros en el rango (incluyendo ambos extremos)
    records = db.query(MedicalRecord).filter(
        MedicalRecord.patient_id == doctor_id,
        MedicalRecord.created_at >= start,
        MedicalRecord.created_at < end
    ).all()

    return records