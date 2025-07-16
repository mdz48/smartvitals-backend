from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.models.medicalFile import MedicalFile
from app.models.medicalRecord import MedicalRecord
from app.models.user import User
from app.shared.config.database import get_db
from typing import List
from datetime import datetime
from app.schemas.medicalFileSchema import MedicalFileCreateSchema, MedicalFileResponseSchema, MedicalFileWithRecordsResponseSchema
from app.schemas.medicalRecordSchema import medicalRecordResponseSchema
from app.shared.services.stadisticsService import get_medical_record_statistics

medicalFileRouter = APIRouter()

# Crear un expediente médico
@medicalFileRouter.post("/medicalFiles", response_model=MedicalFileResponseSchema, status_code=201)
def create_medical_file(medical_file: MedicalFileCreateSchema, db: Session = Depends(get_db)):
    patient = db.query(User).filter(User.id == medical_file.patient_id).first()
    if not patient:
        raise HTTPException(status_code=404, detail="Paciente no encontrado")
    doctor = None
    if medical_file.doctor_id:
        doctor = db.query(User).filter(User.id == medical_file.doctor_id).first()
        if not doctor:
            raise HTTPException(status_code=404, detail="Doctor no encontrado")
    new_file = MedicalFile(
        patient_id=medical_file.patient_id,
        doctor_id=medical_file.doctor_id,
        diagnosis=medical_file.diagnosis,
        treatment=medical_file.treatment,
        notes=medical_file.notes,
        created_at=datetime.now(),
        updated_at=datetime.now()
    )
    db.add(new_file)
    db.commit()
    db.refresh(new_file)
    return new_file

# Endpoint para actualizar expediente médico
@medicalFileRouter.put("/medicalFiles/{file_id}", response_model=MedicalFileResponseSchema, status_code=200)
def update_medical_file(file_id: int, medical_file: MedicalFileCreateSchema, db: Session = Depends(get_db)):
    file = db.query(MedicalFile).filter(MedicalFile.id == file_id).first()
    if not file:
        raise HTTPException(status_code=404, detail="Expediente no encontrado")
    file.diagnosis = medical_file.diagnosis
    file.treatment = medical_file.treatment
    file.notes = medical_file.notes
    file.doctor_id = medical_file.doctor_id
    db.commit()
    db.refresh(file)
    return file

# Obtener expedientes de un paciente
@medicalFileRouter.get("/patients/{patient_id}/medicalFiles", response_model=List[MedicalFileResponseSchema], status_code=200)
def get_medical_files_by_patient(patient_id: int, db: Session = Depends(get_db)):
    files = db.query(MedicalFile).filter(MedicalFile.patient_id == patient_id).all()
    result = []
    for file in files:
        records = db.query(MedicalRecord).filter(MedicalRecord.medical_file_id == file.id).all()
        records_data = [medicalRecordResponseSchema.model_validate(r).model_dump() for r in records]
        file_data = MedicalFileResponseSchema.model_validate({
            **file.__dict__,
            "records": records_data
        })
        result.append(file_data)
    return result

# Obtener registros de un expediente
@medicalFileRouter.get("/medicalFiles/{file_id}/records", response_model=MedicalFileWithRecordsResponseSchema, status_code=200)
def get_records_by_medical_file(file_id: int, db: Session = Depends(get_db)):
    file = db.query(MedicalFile).filter(MedicalFile.id == file_id).first()
    if not file:
        raise HTTPException(status_code=404, detail="Expediente no encontrado")
    records = db.query(MedicalRecord).filter(MedicalRecord.medical_file_id == file_id).all()
    records_data = [medicalRecordResponseSchema.model_validate(r).model_dump() for r in records]
    file_dict = MedicalFileWithRecordsResponseSchema.model_validate({
        **file.__dict__,
        "records": records_data
    })
    return file_dict

@medicalFileRouter.get("/medicalFiles/{file_id}/full", status_code=200)
def get_full_file_info(file_id: int, db: Session = Depends(get_db)):
    file = db.query(MedicalFile).filter(MedicalFile.id == file_id).first()
    if not file:
        raise HTTPException(status_code=404, detail="Expediente no encontrado")
    records = db.query(MedicalRecord).filter(MedicalRecord.medical_file_id == file_id).all()
    records_data = [medicalRecordResponseSchema.model_validate(r).model_dump() for r in records]
    # Estadística
    statistics = None
    if records:
        statistics = db.run_sync(lambda: get_medical_record_statistics(db, records)) if hasattr(db, 'run_sync') else get_medical_record_statistics(db, records)
        if hasattr(statistics, '__await__'):
            import asyncio
            statistics = asyncio.run(statistics)
    # Riesgos: si algún registro tiene valores fuera de rango
    riesgos = []
    for r in records:
        riesgo = {}
        riesgo["hipotermia"] = r.temperature < 35.0
        riesgo["fiebre"] = r.temperature > 37.5
        riesgo["arritmia"] = r.heart_rate < 60 or r.heart_rate > 100
        riesgo["hipoxemia"] = r.oxygen_saturation < 90.0
        riesgo["hipertension"] = r.blood_pressure > 140.0
        riesgo["hipotension"] = r.blood_pressure < 90.0
        riesgos.append({"record_id": r.id, **riesgo})
    return {
        "file": file,
        "records": records_data,
        "statistics": statistics,
        "riesgos": riesgos
    } 