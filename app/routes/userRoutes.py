from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status, File, UploadFile, Form
from datetime import datetime, timedelta

from app.models.user import User
from app.models.doctorPatient import DoctorPatient
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
        age = user.age,
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
    # Eliminamos compleamente el usuario
    db.delete(user)
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
        id=existing_user.id,
        name=existing_user.name,
        lastname=existing_user.lastname,
        age=existing_user.age,
        email=existing_user.email,
        role=existing_user.role,
        profile_picture=existing_user.profile_picture
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


# Ruta para añadir un paciente a un doctor
@userRouter.post("/doctors/{doctor_id}/patients/{patient_email}", status_code=201, tags=["users"])
async def add_patient_to_doctor(doctor_id: int, patient_email: str, db: Session = Depends(get_db)):
    doctor = db.query(User).filter(User.id == doctor_id, User.role == 'doctor').first()
    if not doctor:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Doctor no encontrado")

    patient = db.query(User).filter(User.email == patient_email, User.role == 'patient').first()
    if not patient:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Paciente no encontrado")
    
    # Verificar si la relación ya existe
    existing_relation = db.query(DoctorPatient).filter(
        DoctorPatient.doctor_id == doctor_id,
        DoctorPatient.patient_id == patient.id
    ).first()
    
    if existing_relation:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="El paciente ya está asignado a este doctor")
    
    # Crear nueva relación usando la tabla DoctorPatient
    new_relation = DoctorPatient(doctor_id=doctor_id, patient_id=patient.id)
    db.add(new_relation)
    db.commit()
    
    return {"detail": "Paciente añadido al doctor exitosamente"}

# Ruta para obtener los pacientes de un doctor
@userRouter.get("/doctors/{doctor_id}/patients", response_model=list[userResponseSchema], tags=["users"], status_code=200)
async def get_doctor_patients(doctor_id: int, db: Session = Depends(get_db)):
    doctor = db.query(User).filter(User.id == doctor_id, User.role == 'doctor').first()
    if not doctor:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Doctor no encontrado")

    # Obtener pacientes a través de la tabla DoctorPatient
    patient_relations = db.query(DoctorPatient).filter(DoctorPatient.doctor_id == doctor_id).all()
    patient_ids = [relation.patient_id for relation in patient_relations]
    patients = db.query(User).filter(User.id.in_(patient_ids), User.role == 'patient').all()
    
    return patients

# Ruta para obtener los doctores de un paciente
@userRouter.get("/patients/{patient_id}/doctors", response_model=list[userResponseSchema], tags=["users"], status_code=200)
async def get_patient_doctors(patient_id: int, db: Session = Depends(get_db)):
    patient = db.query(User).filter(User.id == patient_id, User.role == 'patient').first()
    if not patient:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Paciente no encontrado")
    # Obtener doctores a través de la tabla DoctorPatient
    doctor_relations = db.query(DoctorPatient).filter(DoctorPatient.patient_id == patient_id).all()
    doctor_ids = [relation.doctor_id for relation in doctor_relations]
    doctors = db.query(User).filter(User.id.in_(doctor_ids), User.role == 'doctor').all()
    return doctors

# Ruta para obtener todos los doctores
@userRouter.get("/doctors", response_model=list[userResponseSchema], tags=["users"], status_code=200)
async def get_doctors(db: Session = Depends(get_db)):
    doctors = db.query(User).filter(User.role == 'doctor', User.deleted.is_(None)).all()
    return doctors

# Ruta para registrar a un nuevo usuario(paciente) como doctor y añadirlo automaticamente a su lista de pacientes
@userRouter.post("/doctors/{doctor_id}/register/patient", response_model=userResponseSchema, tags=["users"], status_code=201)
async def register_patient_as_doctor(user: userCreateSchema, doctor_id: int, db: Session = Depends(get_db)):
    # Usamos la funcino para crear un nuevo usuario
    newUser = await create_user(user, db)
    # Añadir el nuevo paciente a la lista de pacientes del doctor
    doctor = db.query(User).filter(User.id == doctor_id, User.role == 'doctor').first()
    if not doctor:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Doctor no encontrado")
    new_relation = DoctorPatient(doctor_id=doctor_id, patient_id=newUser.id)
    db.add(new_relation)
    db.commit()
    db.refresh(new_relation)
    return newUser
    
    
# Ruta para eliminar un paciente de un doctor
@userRouter.delete("/doctors/{doctor_id}/patients/{patient_id}", status_code=204, tags=["users"])
async def remove_patient_from_doctor(doctor_id: int, patient_id: int, db: Session = Depends(get_db)):
    doctor = db.query(User).filter(User.id == doctor_id, User.role == 'doctor').first()
    if not doctor:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Doctor no encontrado")

    patient = db.query(User).filter(User.id == patient_id, User.role == 'patient').first()
    if not patient:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Paciente no encontrado")
    
    # Eliminar la relación entre el doctor y el paciente
    relation = db.query(DoctorPatient).filter(
        DoctorPatient.doctor_id == doctor_id,
        DoctorPatient.patient_id == patient_id
    ).first()
    
    if not relation:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="La relación entre el doctor y el paciente no existe")
    
    db.delete(relation)
    db.commit()
    
    return {"detail": "Paciente eliminado del doctor exitosamente"}