import matplotlib.pyplot as plt
import numpy as np
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, date
from sqlalchemy.orm import Session
from app.models.medicalRecord import MedicalRecord

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
    
    return stats 