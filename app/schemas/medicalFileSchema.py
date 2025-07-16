from pydantic import BaseModel, ConfigDict
from typing import Optional, List
from datetime import datetime
from app.schemas.userSchema import userResponseSchema
from app.schemas.medicalRecordSchema import medicalRecordResponseSchema

class MedicalFileCreateSchema(BaseModel):
    patient_id: int
    doctor_id: Optional[int] = None
    diagnosis: Optional[str] = None
    treatment: Optional[str] = None
    notes: Optional[str] = None

class MedicalFileResponseSchema(BaseModel):
    id: int
    patient_id: int
    doctor_id: Optional[int] = None
    diagnosis: Optional[str] = None
    treatment: Optional[str] = None
    notes: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    patient: Optional[userResponseSchema] = None
    doctor: Optional[userResponseSchema] = None
    records: List[medicalRecordResponseSchema] = []
    
    model_config = ConfigDict(from_attributes=True)

class MedicalFileWithRecordsResponseSchema(MedicalFileResponseSchema):
    records: List[dict] = [] 