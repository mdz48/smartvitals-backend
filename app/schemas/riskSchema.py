from pydantic import BaseModel, ConfigDict, EmailStr, Field
from typing import Optional, Dict
from app.schemas.userSchema import userResponseSchema

class RisksSchema(BaseModel):
    hipotermia: bool
    fiebre: bool
    arritmia: bool
    hipoxemia: bool
    hipertension: bool
    hipotension: bool

    

