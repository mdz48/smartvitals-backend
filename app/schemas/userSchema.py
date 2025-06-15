from datetime import datetime
from pydantic import BaseModel, ConfigDict, EmailStr, Field
from typing import Optional
from app.models.interfaces import userRole

class userSchema(BaseModel):
    name: str
    lastname: str
    email: EmailStr
    role: userRole
    profile_picture: Optional[str] = None
    
    model_config = ConfigDict(from_attributes=True)
        
    
class userLoginSchema(BaseModel):
    password: str
    
class userCreateSchema(userSchema):
    password: str 
    
class userResponseSchema(userSchema):
    id: int
    created_at: datetime
    updated_at: datetime
    deleted: Optional[datetime] = None
    

