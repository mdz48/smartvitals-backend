import threading
import time
import json
from collections import defaultdict
from sqlalchemy.orm import Session
from app.models.medicalRecord import MedicalRecord
from app.shared.config.database import SessionLocal
import pandas as pd
from app.models.recordSensorData import RecordSensorData


medicion_activa = {}  # {patient_id: True/False}

# Variable global para la función de notificación WebSocket
notification_callback = None

def set_notification_callback(callback_func):
    """Configura la función de callback para notificaciones WebSocket"""
    global notification_callback
    notification_callback = callback_func

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
def save_record_sensor_data(patient_id, doctor_id, temperature, blood_pressure, oxygen_saturation, heart_rate, medical_record_id=None):
    db = SessionLocal()
    # try:
    #     raw_data = RecordSensorData(
    #         patient_id=patient_id,
    #         doctor_id=doctor_id,
    #         temperature=temperature,
    #         blood_pressure=blood_pressure,
    #         oxygen_saturation=oxygen_saturation,
    #         heart_rate=heart_rate,
    #         medical_record_id=medical_record_id
    #     )
    #     db.add(raw_data)
    #     db.commit()
    # except Exception as e:
    #     db.rollback()
    #     print(f"Error guardando RecordSensorData: {e}")
    # finally:
    #     db.close()

def add_sensor_data(patient_id, doctor_id, temperature, blood_pressure, oxygen_saturation, heart_rate):
    save_record_sensor_data(patient_id, doctor_id, temperature, blood_pressure, oxygen_saturation, heart_rate)
    if not medicion_activa.get(patient_id, False):
        return # No procesar si la medición no está activa
    buf = data_buffer[patient_id]
    if temperature is not None and temperature != 0:
        buf["temperature"].append(temperature)
    # Para presión arterial, aceptar valores aunque contengan 0 (detección parcial)
    if blood_pressure is not None:
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

            def safe_avg_blood_pressure(bp_list):
                """Promedio especial para presión arterial que maneja valores parciales"""
                if not bp_list:
                    return 0
                
                sistolica_vals = []
                diastolica_vals = []
                
                for bp in bp_list:
                    if bp is not None:
                        try:
                            sis, dia = map(float, str(bp).split('/'))
                            if sis > 0:
                                sistolica_vals.append(sis)
                            if dia > 0:
                                diastolica_vals.append(dia)
                        except:
                            continue
                
                # Calcular promedios
                avg_sis = sum(sistolica_vals) / len(sistolica_vals) if sistolica_vals else 0
                avg_dia = sum(diastolica_vals) / len(diastolica_vals) if diastolica_vals else 0
                
                return f"{avg_sis:.0f}/{avg_dia:.0f}"

            avg_temp = safe_avg(buf["temperature"])
            avg_bp = safe_avg_blood_pressure(buf["blood_pressure"])
            avg_ox = safe_avg(buf["oxygen_saturation"])
            avg_hr = safe_avg(buf["heart_rate"])

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
                db.refresh(record)
                print(f"Expediente médico creado para paciente {patient_id}")

                # Enviar notificación WebSocket sobre la creación del expediente
                if notification_callback:
                    notification_message = json.dumps({
                        "type": "medical_record_created",
                        "patient_id": buf["patient_id"],
                        "doctor_id": buf["doctor_id"],
                        "record_id": record.id,
                        "timestamp": time.time(),
                        "data": {
                            "temperature": avg_temp,
                            "blood_pressure": avg_bp,
                            "oxygen_saturation": avg_ox,
                            "heart_rate": avg_hr
                        },
                        "message": f"Nuevo expediente médico creado para el paciente {patient_id}"
                    })
                    
                    # Enviar notificación a usuarios específicos (paciente y doctor)
                    target_users = [buf["patient_id"], buf["doctor_id"]]
                    notification_callback("targeted", notification_message, target_users)

                # Asociar los RecordSensorData crudos a este MedicalRecord
                # db.query(RecordSensorData).filter(
                #     RecordSensorData.patient_id == buf["patient_id"],
                #     RecordSensorData.doctor_id == buf["doctor_id"],
                #     RecordSensorData.medical_record_id == None
                # ).update({RecordSensorData.medical_record_id: record.id})
                # db.commit()
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
            
            # Validar solo los valores detectados (diferentes de 0)
            if sistolica > 0 and diastolica > 0:
                # Ambos valores detectados
                if sistolica < 90 or diastolica < 60:
                    alertas.append("Hipotensión: Presión arterial baja")
                elif sistolica > 140 or diastolica > 90:
                    alertas.append("Hipertensión: Presión arterial alta")
            elif sistolica > 0:
                # Solo sistólica detectada
                if sistolica < 90:
                    alertas.append("Hipotensión sistólica: Presión sistólica baja")
                elif sistolica > 140:
                    alertas.append("Hipertensión sistólica: Presión sistólica alta")
            elif diastolica > 0:
                # Solo diastólica detectada
                if diastolica < 60:
                    alertas.append("Hipotensión diastólica: Presión diastólica baja")
                elif diastolica > 90:
                    alertas.append("Hipertensión diastólica: Presión diastólica alta")
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