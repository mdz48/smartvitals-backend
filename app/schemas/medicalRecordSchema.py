from datetime import datetime
from pydantic import BaseModel, ConfigDict, EmailStr, Field
from typing import Optional
from app.schemas.userSchema import userResponseSchema
from app.schemas.riskSchema import RisksSchema

class medicalRecordSchema(BaseModel):
    medical_file_id: int
    temperature: float
    blood_pressure: float
    oxygen_saturation: float
    heart_rate: float

    model_config = ConfigDict(from_attributes=True)
    
class medicalRecordResponseSchema(medicalRecordSchema):
    id: int
    created_at: datetime
    updated_at: datetime
    deleted: Optional[datetime] = None
    medical_file_id: int

    model_config = ConfigDict(from_attributes=True)
    
class medicalRecordWithRisksResponseSchema(medicalRecordResponseSchema):
    risks: RisksSchema

    model_config = ConfigDict(from_attributes=True)
    
