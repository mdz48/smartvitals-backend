import matplotlib.pyplot as plt
import numpy as np
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, date
from sqlalchemy.orm import Session
from app.models import medicalRecord
from app.models.medicalRecord import MedicalRecord
from app.schemas.riskSchema import RisksSchema
from app.models.user import User
from app.shared.utils.riskService import get_heart_rate_range, get_respiratory_rate_range

async def get_medical_record_statistics(db: Session, medical_records: List[MedicalRecord]) -> Dict[str, Any]:
    """
    Calcula estadísticas básicas de los registros médicos de un paciente
    """
    if not medical_records:
        return {"error": "No hay registros médicos para analizar"}
    
    # Extraer datos de cada métrica
    temperatures = [record.temperature for record in medical_records]
    blood_pressures = [record.blood_pressure for record in medical_records]
    oxygen_saturations = [record.oxygen_saturation for record in medical_records]
    heart_rates = [record.heart_rate for record in medical_records]
    
    # Extraemos al paciente
    patient = medical_records[0].patient
    
    # Calcular estadísticas básicas para cada métrica
    def calculate_basic_stats(data: List[float]) -> Dict[str, float]:
        if not data:
            return {}
        
        return {
            "media": float(np.mean(data).round(2)),
            "mediana": float(np.median(data).round(2)),
            "moda": float(calculate_mode(data)),
            "desviacion_estandar": float(np.std(data).round(2)),
            "minimo": float(np.min(data)),
            "maximo": float(np.max(data)),
            "rango": float(np.max(data) - np.min(data))
        }
    
    def calculate_mode(data: List[float]) -> float:
        """Calcula la moda de una lista de datos"""
        if not data:
            return 0.0
        
        # Redondear a 1 decimal para agrupar valores similares
        rounded_data = [round(x, 1) for x in data]
        values, counts = np.unique(rounded_data, return_counts=True)
        mode_index = np.argmax(counts)
        return float(values[mode_index])
    
    # Calcular estadísticas para cada métrica
    stats = {
        "temperatura": calculate_basic_stats(temperatures),
        "presion_arterial": calculate_basic_stats(blood_pressures),
        "saturacion_oxigeno": calculate_basic_stats(oxygen_saturations),
        "frecuencia_cardiaca": calculate_basic_stats(heart_rates),
        "resumen": {
            "total_registros": len(medical_records),
            "periodo_analisis": {
                "fecha_inicio": min(record.created_at for record in medical_records).strftime("%Y-%m-%d"),
                "fecha_fin": max(record.created_at for record in medical_records).strftime("%Y-%m-%d")
            }
        }
    }
    
    """
    SECCION DE PARA OBTENER LOS RANGOS PARA EL PACIENTE DEPENDIENTO DE SU INFORMACION
    """
    parametros = {
        "rango_bradicardia": get_heart_rate_range(patient.age)[0] - 10,
        "rango_taquicardia": get_heart_rate_range(patient.age)[1] + 10,
        "rango_bradiapnea": get_respiratory_rate_range(patient.age)[0] - 5,
        "rango_taquipnea": get_respiratory_rate_range(patient.age)[1] + 5,
        "rango_hipotermia": 35.0,  # < a 35.0 es hipotermia
        "rango_fiebre": 38.0,  # > 38.0 es fiebre
        "rango_hipertension": 140.0,  # > 140.0 es hipertensión
        "rango_hipotension": 50.0,  # < 50.0 es hipotensión
        "rango_baja_saturacion": 90.0  # < 90.0 es baja saturación
    }


    """
    SECCION DE PROBABILIDAD
    """
    def calcular_probabilidad(condicion, registros):
        if not registros:
            return 0.0
        return round(100 * sum(1 for r in registros if condicion(r)) / len(registros), 2)

    risk_probabilities = {
        # Taquicardia y bradicardia según edad
        "riesgo_taquicardia": calcular_probabilidad(
            lambda r: r.heart_rate is not None and r.heart_rate > get_heart_rate_range(r.patient.age)[1],
            medical_records
        ),
        "riesgo_bradicardia": calcular_probabilidad(
            lambda r: r.heart_rate is not None and r.heart_rate < get_heart_rate_range(r.patient.age)[0],
            medical_records
        ),
        # Frecuencia respiratoria anormal según edad
        "riesgo_taquipnea": calcular_probabilidad(
            lambda r: hasattr(r, 'respiratory_rate') and r.respiratory_rate is not None and r.respiratory_rate > get_respiratory_rate_range(r.patient.age)[1],
            medical_records
        ),
        "riesgo_bradipnea": calcular_probabilidad(
            lambda r: hasattr(r, 'respiratory_rate') and r.respiratory_rate is not None and r.respiratory_rate < get_respiratory_rate_range(r.patient.age)[0],
            medical_records
        ),
        # Fiebre e hipotermia
        "riesgo_fiebre": calcular_probabilidad(
            lambda r: r.temperature is not None and r.temperature > 38.0,
            medical_records
        ),
        "riesgo_hipotermia": calcular_probabilidad(
            lambda r: r.temperature is not None and r.temperature < 35.0,
            medical_records
        ),
        # Hipertensión e hipotensión con valores estandarizados para adultos
        "riesgo_hipertension": calcular_probabilidad(
            lambda r: r.blood_pressure is not None and r.blood_pressure > 140.0,
            medical_records
        ),
        "riesgo_hipotension": calcular_probabilidad(
            lambda r: r.blood_pressure is not None and r.blood_pressure < 50.0,
            medical_records
        ),
        # Baja saturación 
        "riesgo_baja_saturacion": calcular_probabilidad(
            lambda r: r.oxygen_saturation is not None and r.oxygen_saturation < 90.0 and r.oxygen_saturation > 0.0,
            medical_records
        ),
    }
    
    return {
    "estadisticas": stats,
    "probabilidades_riesgo": risk_probabilities,
    "parametros": parametros,
    }
