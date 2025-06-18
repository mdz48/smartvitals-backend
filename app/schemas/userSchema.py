from datetime import datetime
from pydantic import BaseModel, ConfigDict, EmailStr, Field
from typing import Optional
from app.models.interfaces import userRole

class userSchema(BaseModel):
    name: str | None = "mdz" # SOLO PARA DESARROLLO, NO USAR EN PRODUCCIÓN!!!
    lastname: str | None = "none" # SOLO PARA DESARROLLO, NO USAR EN PRODUCCIÓN!!!
    email: EmailStr | None = "1@1.com" # SOLO PARA DESARROLLO, NO USAR EN PRODUCCIÓN!!!
    role: userRole | None = userRole.PATIENT # SOLO PARA DESARROLLO, NO USAR EN PRODUCCIÓN!!!
    profile_picture: Optional[str] = None
    model_config = ConfigDict(from_attributes=True)
        
    
class userLoginSchema(BaseModel):
    email: EmailStr | None = "1@1.com" # SOLO PARA DESARROLLO, NO USAR EN PRODUCCIÓN!!!
    password: str | None = "1" # SOLO PARA DESARROLLO, NO USAR EN PRODUCCIÓN!!!

class userCreateSchema(userSchema):
    password: str | None = "1" # SOLO PARA DESARROLLO, NO USAR EN PRODUCCIÓN!!!
    
class userResponseSchema(userSchema):
    id: int
    created_at: datetime
    updated_at: datetime
    deleted: Optional[datetime] = None

class loginResponseSchema(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user : userResponseSchema
    
    model_config = ConfigDict(from_attributes=True)