# Configuración de RabbitMQ para Sensores Médicos

## Descripción

Esta API está configurada para recibir mensajes de 4 sensores médicos a través de RabbitMQ:
- **Temperatura** (cola: `temperatura`)
- **Oxígeno** (cola: `oxigeno`)
- **Presión arterial** (cola: `presion`)
- **Ritmo cardíaco** (cola: `ritmo_cardiaco`)

## Configuración

### 1. Variables de Entorno

Agrega estas variables a tu archivo `.env`:

```env
# Configuración de RabbitMQ
RABBITMQ_HOST=tu_ip_rabbitmq
RABBITMQ_PORT=5672
RABBITMQ_USER=guest
RABBITMQ_PASSWORD=guest
RABBITMQ_VIRTUAL_HOST=/
```

### 2. Instalación de Dependencias

```bash
pip install -r requirements.txt
```

### 3. Estructura de Mensajes

Los mensajes deben enviarse en formato JSON. La API puede manejar diferentes formatos:

#### Formato Recomendado:
```json
{
  "temperature": 36.5,
  "timestamp": "2024-01-15T10:30:00Z",
  "patient_id": 123
}
```

#### Formatos Alternativos Soportados:
```json
// Para temperatura
{"temperatura": 36.5}
{"temp": 36.5}
{"value": 36.5}

// Para oxígeno
{"oxygen_saturation": 98.5}
{"oxigeno": 98.5}
{"saturation": 98.5}

// Para presión
{"blood_pressure": 120.5}
{"presion": 120.5}
{"pressure": 120.5}

// Para ritmo cardíaco
{"heart_rate": 75.0}
{"ritmo_cardiaco": 75.0}
{"heartrate": 75.0}
```

## Uso

### 1. Iniciar la API

```bash
uvicorn main:app --reload
```

### 2. Configurar Sensores (Solo Doctores)

```bash
# Configurar paciente y doctor para recibir datos
curl -X POST "http://localhost:8000/sensors/configure" \
  -H "Authorization: Bearer TU_TOKEN_JWT" \
  -H "Content-Type: application/json" \
  -d '{
    "patient_id": 123,
    "doctor_id": 456
  }'
```

### 3. Iniciar Consumo de Mensajes

```bash
# Iniciar consumo de todas las colas
curl -X POST "http://localhost:8000/sensors/start" \
  -H "Authorization: Bearer TU_TOKEN_JWT"
```

### 4. Verificar Estado

```bash
# Ver estado actual de los sensores
curl -X GET "http://localhost:8000/sensors/status" \
  -H "Authorization: Bearer TU_TOKEN_JWT"
```

### 5. Consumidor Independiente (Opcional)

Si prefieres ejecutar el consumidor de RabbitMQ independientemente:

```bash
python rabbitmq_consumer.py
```

## Flujo de Datos

1. **Recepción**: Los sensores envían datos a RabbitMQ
2. **Procesamiento**: La API recibe y procesa los mensajes
3. **Acumulación**: Los datos se acumulan hasta tener los 4 valores
4. **Creación**: Se crea automáticamente un registro médico
5. **Reinicio**: Los datos se reinician para el siguiente conjunto

## Endpoints Disponibles

| Método | Endpoint | Descripción |
|--------|----------|-------------|
| POST | `/sensors/configure` | Configurar paciente y doctor |
| GET | `/sensors/status` | Ver estado de sensores |
| POST | `/sensors/start` | Iniciar consumo de mensajes |
| POST | `/sensors/stop` | Detener consumo de mensajes |
| POST | `/sensors/reset` | Reiniciar datos acumulados |

## Seguridad

- Solo los doctores pueden configurar y gestionar sensores
- Se requiere autenticación JWT para todos los endpoints
- Los mensajes se procesan de forma segura con manejo de errores

## Troubleshooting

### Error de Conexión a RabbitMQ
- Verifica que RabbitMQ esté ejecutándose
- Confirma las credenciales en el archivo `.env`
- Verifica que el puerto 5672 esté abierto

### Mensajes No Procesados
- Verifica el formato JSON de los mensajes
- Confirma que las colas estén declaradas
- Revisa los logs de la aplicación

### Registros Médicos No Creados
- Asegúrate de que el paciente esté configurado
- Verifica que todos los 4 sensores hayan enviado datos
- Revisa la configuración de la base de datos 