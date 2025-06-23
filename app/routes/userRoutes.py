from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status, File, UploadFile, Form
from datetime import datetime, timedelta

from app.models.user import User
from app.schemas.userSchema import userSchema, userCreateSchema, userResponseSchema, userLoginSchema, loginResponseSchema
from app.shared.config.database import SessionLocal
from sqlalchemy.orm import Session
from app.shared.config.database import get_db
from app.shared.config.middleware.security import get_password_hash, get_current_user, verify_password, ACCESS_TOKEN_EXPIRE_MINUTES, create_access_token
from app.shared.config.s3Files import upload_file_to_s3, upload_files_to_s3

userRouter = APIRouter()

# Ruta para crear un nuevo usuario
@userRouter.post("/users", response_model=userResponseSchema, status_code=201, tags=["users"])
async def create_user(user: userCreateSchema, db: Session = Depends(get_db)):
    # Verifiamos que el usuario no exista
    existing_user = db.query(User).filter(User.email == user.email).first()
    if existing_user:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="El usuario ya existe con este correo electrónico.")

    # Creamos el nuevo usuario con la constraseña hasheada
    hashed_password = get_password_hash(user.password)      
    new_user = User(
        name=user.name,
        lastname=user.lastname,
        email=user.email,
        password=hashed_password,  # Password hasheada
        role=user.role,
        profile_picture=user.profile_picture
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user

@userRouter.get("/users", response_model=list[userResponseSchema], tags=["users"], status_code=200)
async def get_users(db: Session = Depends(get_db)):
    users = db.query(User).where(User.deleted.is_(None)).all()  # Filtramos usuarios no eliminados
    if not users:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No se encontraron usuarios") 
    return users
 
@userRouter.get("/users/{user_id}", response_model=userResponseSchema, tags=["users"], status_code=200)
async def get_user(user_id: int, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Usuario no encontrado")
    return user

# Ruta para actualizar un usuario
@userRouter.put("/users/{user_id}", response_model=userResponseSchema, tags=["users"], status_code=200)
async def update_user(
    user_id: int, 
    name: Optional[str] = Form(None),
    lastname: Optional[str] = Form(None),
    email: Optional[str] = Form(None),
    password: Optional[str] = Form(None),
    profile_picture: Optional[UploadFile] = File(None),
    
    db: Session = Depends(get_db)):

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Usuario no encontrado")
    
    if profile_picture and profile_picture.content_type not in ["image/jpeg", "image/png"]:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Formato de imagen no soportado. Use JPEG o PNG.")

    # Actualizamos los campos del usuario
    if name:
        user.name = name
    if lastname:
        user.lastname = lastname
    if email:
        user.email = email
    if password:
        user.password = get_password_hash(password)
    if profile_picture:
        user.profile_picture = upload_file_to_s3(profile_picture)

    db.commit()
    db.refresh(user)
    return user

@userRouter.delete("/users/{user_id}", status_code=204, tags=["users"])
async def delete_user(user_id: int, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Usuario no encontrado")
    
    # Eliminacion lógica: ponemos fecha en el campo deleted
    user.deleted = datetime.now()
    db.add(user)
    db.commit()
    db.refresh(user)
    return {"detail": "Usuario eliminado exitosamente"}

@userRouter.post("/users/login", response_model=loginResponseSchema, tags=["users"], status_code=200)
async def login_user(user: userLoginSchema, db: Session = Depends(get_db)):
    # Buscar usuario por email
    existing_user = db.query(User).filter(User.email == user.email).first()
    
    # Verificar credenciales
    if not existing_user or not verify_password(user.password, existing_user.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, 
            detail="Email o contraseña incorrectos"
        )
    
    # Crear token
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": existing_user.email}, 
        expires_delta=access_token_expires
    )
    
    # Retornar token y datos del usuario
    return loginResponseSchema(
        access_token=access_token,
        token_type="bearer",
        user=existing_user  
    )

@userRouter.get("/users/me", response_model=userResponseSchema, tags=["users"], status_code=200)
async def get_current_user_info(current_user: User = Depends(get_current_user)):
    return current_user


# ruta de prueb para subir archivos
@userRouter.post("/users/upload", tags=["users"], status_code=200)
async def upload_files(files: list[UploadFile] = File(...), db: Session = Depends(get_db)):
    if not files:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No se han subido archivos")
    
    file_urls = upload_files_to_s3(files)
    
    if not file_urls:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Error al subir los archivos")
    
    return {"file_urls": file_urls}

