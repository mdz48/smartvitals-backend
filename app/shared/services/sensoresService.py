import threading
import time
from collections import defaultdict
from sqlalchemy.orm import Session
from app.models.medicalRecord import MedicalRecord
from app.shared.config.database import SessionLocal
import pandas as pd
import json
from app.models.medicalFile import MedicalFile


medicion_activa = {}  # {patient_id: True/False}

# Estructura para acumular datos por expediente
data_buffer = defaultdict(lambda: {
    "temperature": [],
    "blood_pressure": [],
    "oxygen_saturation": [],
    "heart_rate": []
})

# Llamar a esta función cada vez que recibas un dato de sensor
def add_sensor_data(medical_file_id, temperature, blood_pressure, oxygen_saturation, heart_rate):
    buf = data_buffer[medical_file_id]
    if temperature is not None and temperature != 0:
        buf["temperature"].append(temperature)
    if blood_pressure is not None and blood_pressure != 0:
        buf["blood_pressure"].append(blood_pressure)
    if oxygen_saturation is not None and oxygen_saturation != 0:
        buf["oxygen_saturation"].append(oxygen_saturation)
    if heart_rate is not None and heart_rate != 0:
        buf["heart_rate"].append(heart_rate)

# Proceso que cada minuto promedia y guarda en la base de datos
def process_and_save_records():
    while True:
        time.sleep(2)
        for medical_file_id, buf in list(data_buffer.items()):
            if len(buf["temperature"]) == 0:
                continue

            def safe_avg(lst):
                values = [x for x in lst if x is not None]
                return sum(values) / len(values) if values else 0

            avg_temp = safe_avg(buf["temperature"])
            avg_bp = safe_avg(buf["blood_pressure"])
            avg_ox = safe_avg(buf["oxygen_saturation"])
            avg_hr = safe_avg(buf["heart_rate"])

            db: Session = SessionLocal()
            try:
                record = MedicalRecord(
                    medical_file_id=medical_file_id,
                    temperature=avg_temp,
                    blood_pressure=avg_bp,
                    oxygen_saturation=avg_ox,
                    heart_rate=avg_hr
                )
                db.add(record)
                db.commit()
                print(f"Registro médico creado para expediente {medical_file_id}")

                # Notificar al WebSocket
                try:
                    from websocket import add_message_to_queue
                    nuevo_registro = {
                        "id": record.id,
                        "medical_file_id": record.medical_file_id,
                        "temperature": record.temperature,
                        "blood_pressure": record.blood_pressure,
                        "oxygen_saturation": record.oxygen_saturation,
                        "heart_rate": record.heart_rate,
                        "created_at": str(record.created_at)
                    }
                    # Aquí debes definir los user_id interesados. Por ejemplo, puedes obtenerlos del expediente:
                    medical_file = db.query(MedicalFile).filter(MedicalFile.id == record.medical_file_id).first()
                    target_users = []
                    paciente_id = doctor_id = None
                    if medical_file:
                        if medical_file.patient_id:
                            target_users.append(medical_file.patient_id)
                            paciente_id = medical_file.patient_id
                        if medical_file.doctor_id:
                            target_users.append(medical_file.doctor_id)
                            doctor_id = medical_file.doctor_id
                    add_message_to_queue(
                        "targeted",
                        json.dumps({
                            "type": "nuevo_registro",
                            "medical_file_id": record.medical_file_id,
                            "record": nuevo_registro,
                            "paciente_id": paciente_id,
                            "doctor_id": doctor_id
                        }),
                        target_users=target_users
                    )
                except Exception as e:
                    print(f"Error notificando al WebSocket: {e}")
            except Exception as e:
                db.rollback()
                print(f"Error al guardar registro médico: {e}")
            finally:
                db.close()

            data_buffer[medical_file_id] = {
                "temperature": [],
                "blood_pressure": [],
                "oxygen_saturation": [],
                "heart_rate": []
            }
            
def validar_datos(temperature, blood_pressure, oxygen_saturation, heart_rate):
    alertas = []

    # Temperatura
    if temperature is not None:
        if temperature < 35:
            alertas.append("Hipotermia: Temperatura menor a 35°C")
        elif 37.5 <= temperature < 38:
            alertas.append("Febrícula: Temperatura entre 37.5°C y 38°C")
        elif 38 <= temperature < 39:
            alertas.append("Fiebre: Temperatura entre 38°C y 39°C")
        elif temperature >= 39:
            alertas.append("Hipertermia: Temperatura mayor a 39°C")

    # Presión arterial (ejemplo para sistólica/diastólica)
    if blood_pressure is not None:
        try:
            sistolica, diastolica = map(float, str(blood_pressure).split('/'))
            if sistolica < 90 or diastolica < 60:
                alertas.append("Hipotensión: Presión arterial baja")
            elif sistolica > 140 or diastolica > 90:
                alertas.append("Hipertensión: Presión arterial alta")
        except Exception:
            pass  # Si el formato no es correcto, ignora

    # Oxigenación
    if oxygen_saturation is not None:
        if oxygen_saturation < 90:
            alertas.append("Oxigenación grave: SpO2 menor a 90%")
        elif 90 <= oxygen_saturation < 93:
            alertas.append("Oxigenación leve: SpO2 entre 90% y 92%")

    # Ritmo cardíaco
    if heart_rate is not None:
        if heart_rate < 50:
            alertas.append("Bradicardia: Ritmo cardíaco menor a 50 lpm")
        elif heart_rate > 100:
            alertas.append("Taquicardia: Ritmo cardíaco mayor a 100 lpm")

    return alertas

# Inicia el hilo de procesamiento
threading.Thread(target=process_and_save_records, daemon=True).start()