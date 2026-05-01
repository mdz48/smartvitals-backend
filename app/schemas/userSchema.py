from datetime import datetime
from pydantic import BaseModel, ConfigDict, EmailStr, Field
from typing import Optional
from app.models.interfaces import userRole, userGender

class userSchema(BaseModel):
    name: str 
    lastname: str 
    email: EmailStr 
    age: int 
    gender: userGender 
    pregnant: bool | None = False 
    role: userRole 
    profile_picture: str | None = "https://kgivveczmdaqzomanqag.supabase.co/storage/v1/object/public/smartvitals-bucket/Blue%20Modern%20Education%20Logo%20(1920%20x%201080%20px).svg" 
    model_config = ConfigDict(from_attributes=True)
        
    
class userLoginSchema(BaseModel):
    email: EmailStr 
    password: str 

class userCreateSchema(userSchema):
    password: str 
    
class userResponseSchema(userSchema):
    id: int
    created_at: datetime
    updated_at: datetime
    deleted: Optional[datetime] = None

class loginResponseSchema(BaseModel):
    access_token: str
    token_type: str = "bearer"
    id: int
    name: str
    lastname : str
    email: str
    age: int
    gender: userGender
    pregnant: bool
    role : userRole
    profile_picture: Optional[str] = None
    
    
    model_config = ConfigDict(from_attributes=True)