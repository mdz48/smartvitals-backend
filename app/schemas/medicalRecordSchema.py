from datetime import datetime
from pydantic import BaseModel, ConfigDict, EmailStr, Field
from typing import Optional
from app.schemas.userSchema import userResponseSchema

class medicalRecordSchema(BaseModel):
    patient_id: int
    # doctor_id: Optional[int] = None
    temperature: float
    blood_pressure: float
    oxygen_saturation: float
    heart_rate: float
    diagnosis: str
    treatment: str
    notes: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)
    
class medicalRecordResponseSchema(medicalRecordSchema):
    id: int
    doctor_id: int
    patient_id: int
    created_at: datetime
    updated_at: datetime
    deleted: Optional[datetime] = None
    doctor: Optional[userResponseSchema] = None
    patient: Optional[userResponseSchema] = None

    model_config = ConfigDict(from_attributes=True)
    
