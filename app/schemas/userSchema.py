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
    profile_picture: str | None = "https://smartvitals-bucket.s3.us-east-1.amazonaws.com/default_profile_picture.png" 
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