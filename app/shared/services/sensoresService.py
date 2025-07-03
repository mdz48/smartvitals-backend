import threading
import time
from collections import defaultdict
from sqlalchemy.orm import Session
from app.models.medicalRecord import MedicalRecord
from app.shared.config.database import SessionLocal

# Estructura para acumular datos por paciente
data_buffer = defaultdict(lambda: {
    "temperature": [],
    "blood_pressure": [],
    "oxygen_saturation": [],
    "heart_rate": [],
    "doctor_id": None,
    "patient_id": None
})

# Llamar a esta función cada vez que recibas un dato de sensor
def add_sensor_data(patient_id, doctor_id, temperature, blood_pressure, oxygen_saturation, heart_rate):
    buf = data_buffer[patient_id]
    if temperature is not None:
        buf["temperature"].append(temperature)
    if blood_pressure is not None:
        buf["blood_pressure"].append(blood_pressure)
    if oxygen_saturation is not None:
        buf["oxygen_saturation"].append(oxygen_saturation)
    if heart_rate is not None:
        buf["heart_rate"].append(heart_rate)
    buf["doctor_id"] = doctor_id
    buf["patient_id"] = patient_id

# Proceso que cada minuto promedia y guarda en la base de datos
def process_and_save_records():
    while True:
        time.sleep(2)  # Espera 1 minuto
        for patient_id, buf in list(data_buffer.items()):
            if len(buf["temperature"]) == 0:
                continue  # No hay datos nuevos

            def safe_avg(lst):
                values = [x for x in lst if x is not None]
                return sum(values) / len(values) if values else 0

            avg_temp = safe_avg(buf["temperature"])
            avg_bp = safe_avg(buf["blood_pressure"])
            avg_ox = safe_avg(buf["oxygen_saturation"])
            avg_hr = safe_avg(buf["heart_rate"])

            # Crea el registro médico
            db: Session = SessionLocal()
            try:
                record = MedicalRecord(
                    patient_id=buf["patient_id"],
                    doctor_id=buf["doctor_id"],
                    temperature=avg_temp,
                    blood_pressure=avg_bp,
                    oxygen_saturation=avg_ox,
                    heart_rate=avg_hr,
                    diagnosis="Automático por sensores",
                    treatment="",
                    notes="Registro generado automáticamente por promedio de sensores"
                )
                db.add(record)
                db.commit()
                print(f"Expediente médico creado para paciente {patient_id}")
            except Exception as e:
                db.rollback()
                print(f"Error al guardar registro médico: {e}")
            finally:
                db.close()

            # Limpia el buffer de ese paciente
            data_buffer[patient_id] = {
                "temperature": [],
                "blood_pressure": [],
                "oxygen_saturation": [],
                "heart_rate": [],
                "doctor_id": buf["doctor_id"],
                "patient_id": buf["patient_id"]
            }

# Inicia el hilo de procesamiento
threading.Thread(target=process_and_save_records, daemon=True).start()