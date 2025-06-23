from fastapi import APIRouter, Depends, HTTPException, status
from datetime import timedelta

from app.models.medicalRecord import MedicalRecord
from app.schemas.medicalRecordSchema import medicalRecordSchema, medicalRecordResponseSchema
from app.models.user import User

from app.shared.config.database import SessionLocal
from sqlalchemy.orm import Session, joinedload
from app.shared.config.database import get_db
from app.shared.config.middleware.security import get_current_user

medicalRecordRouter = APIRouter()

# Ruta para crear un nuevo registro médico
@medicalRecordRouter.post("/medicalRecords", response_model=medicalRecordResponseSchema, status_code=201, tags=["medical_records"])
async def create_medical_record(medical_record: medicalRecordSchema, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    print (f"Current User: {current_user.id}, Role: {current_user.role}")
    new_record = MedicalRecord(**medical_record.model_dump(), doctor_id=current_user.id)
    db.add(new_record)
    db.commit() 
    db.refresh(new_record)
    return new_record

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
    return record

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