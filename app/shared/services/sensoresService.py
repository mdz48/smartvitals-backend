import threading
import time
from collections import defaultdict
from sqlalchemy.orm import Session
from app.models.medicalRecord import MedicalRecord
from app.shared.config.database import SessionLocal

medicion_activa = {}  # {patient_id: True/False}

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
    if not medicion_activa.get(patient_id, False):
        return # No procesar si la medición no está activa
    buf = data_buffer[patient_id]
    if temperature is not None and temperature != 0:
        buf["temperature"].append(temperature)
    if blood_pressure is not None and blood_pressure != 0:
        buf["blood_pressure"].append(blood_pressure)
    if oxygen_saturation is not None and oxygen_saturation != 0:
        buf["oxygen_saturation"].append(oxygen_saturation)
    if heart_rate is not None and heart_rate != 0:
        buf["heart_rate"].append(heart_rate)
    buf["doctor_id"] = doctor_id
    buf["patient_id"] = patient_id

# Proceso que cada minuto promedia y guarda en la base de datos
def process_and_save_records():
    while True:
        time.sleep(60)  # Espera 1 minuto
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
                    diagnosis="",
                    treatment="",
                    notes=""
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