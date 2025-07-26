import os
from dotenv import load_dotenv
load_dotenv()
from passlib.context import CryptContext
from jose import jwt, JWTError
from datetime import datetime, timedelta
from fastapi import HTTPException, status, Depends, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import List, Optional
from app.models.user import User
from app.models.interfaces import userRole
from app.shared.config.database import get_db
from sqlalchemy.orm import Session

SECRET_KEY = os.getenv('SECRET_KEY')
if not SECRET_KEY:
    raise ValueError("SECRET_KEY no se encuentra en el archivo .env")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 1440  # Tiempo de expiración del token en minutos, 24 horas

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
security = HTTPBearer()

def verify_password(plain_password, hashed_password):
    """Verifica si la contraseña en texto plano coincide con la contraseña hasheada."""
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    """Genera un hash para la contraseña proporcionada."""
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta=None):
    """Crea un token de acceso JWT con los datos proporcionados y una fecha de expiración opcional."""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security), db: Session = Depends(get_db)):
    """Obtiene el usuario actual a partir del token JWT proporcionado."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Credenciales no válidas",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        token = credentials.credentials
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    user = db.query(User).filter(User.email == email).first()
    if user is None:
        raise credentials_exception
    return user

def require_roles(allowed_roles: List[userRole]):
    """
    Decorator de dependencia que requiere que el usuario tenga uno de los roles especificados.
    Los admins tienen acceso a todo lo que puede hacer un doctor.
    """
    def role_dependency(current_user: User = Depends(get_current_user)):
        # Si el usuario es admin, tiene acceso a todo lo que puede hacer un doctor
        if current_user.role == userRole.ADMIN:
            return current_user
        
        # Verificar si el usuario tiene uno de los roles permitidos
        if current_user.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"No tienes permisos para acceder a este recurso. Roles requeridos: {[role.value for role in allowed_roles]}"
            )
        return current_user
    return role_dependency

# Dependencias específicas para cada rol
def require_admin(current_user: User = Depends(get_current_user)):
    """Requiere rol de administrador"""
    if current_user.role != userRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Solo los administradores pueden acceder a este recurso"
        )
    return current_user

def require_doctor_or_admin(current_user: User = Depends(get_current_user)):
    """Requiere rol de doctor o administrador"""
    if current_user.role not in [userRole.DOCTOR, userRole.ADMIN]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Solo los doctores y administradores pueden acceder a este recurso"
        )
    return current_user

def require_patient_or_admin(current_user: User = Depends(get_current_user)):
    """Requiere rol de paciente o administrador"""
    if current_user.role not in [userRole.PATIENT, userRole.ADMIN]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Solo los pacientes y administradores pueden acceder a este recurso"
        )
    return current_user

def require_own_resource_or_doctor_or_admin(resource_user_id: int, current_user: User = Depends(get_current_user)):
    """Requiere que sea el propio usuario, o un doctor, o un admin"""
    if (current_user.id != resource_user_id and 
        current_user.role not in [userRole.DOCTOR, userRole.ADMIN]):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Solo puedes acceder a tus propios recursos, o ser doctor/administrador"
        )
    return current_user


