from app.schemas.riskSchema import RisksSchema

def detectar_riesgos(record):
    return RisksSchema(
        hipotermia=(record.temperature is not None and record.temperature != 0 and record.temperature < 35.0),
        fiebre=(record.temperature is not None and record.temperature != 0 and record.temperature > 37.5),
        arritmia=(record.heart_rate is not None and record.heart_rate != 0 and (record.heart_rate < 60 or record.heart_rate > 100)),
        hipoxemia=(record.oxygen_saturation is not None and record.oxygen_saturation != 0 and record.oxygen_saturation < 90.0),
        hipertension=(record.blood_pressure is not None and record.blood_pressure != 0 and record.blood_pressure > 140.0),
        hipotension=(record.blood_pressure is not None and record.blood_pressure != 0 and record.blood_pressure < 90.0)
    )
    
def get_respiratory_rate_range(age):
    # Devuelve el rango normal de frecuencia respiratoria según la edad
    if age < (2/12):  # Menos de 2 meses
        return (30, 50)
    elif age < (6/12):  # 2 a 5 meses
        return (25, 45)
    elif age < 1:  # 6 a 12 meses
        return (20, 40)
    elif age < 3:  # 1 a 3 años
        return (20, 35)
    elif age < 6:  # 3 a 5 años
        return (20, 30)
    elif age < 13:  # 6 a 12 años
        return (15, 30)
    elif age < 18:  # 13 a 18 años
        return (14, 20)
    elif age < 65:  # Adultos
        return (12, 20)
    else:  # Vejez
        return (12, 16)

def get_heart_rate_range(age):
    return (60, 100)  # Valor para adultos


def riesgo_taquicardia(record):
    min_hr, max_hr = get_heart_rate_range(record.patient.age)
    return record.heart_rate > max_hr