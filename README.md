# Smartvitals Backend

Backend REST y WebSocket para la plataforma Smartvitals. Este servicio gestiona usuarios, pacientes, doctores, expedientes médicos y captura de datos biométricos.

## Frontend

La interfaz web correspondiente se encuentra en:

https://github.com/mdz48/smartvitals-frontend

## Tecnologías

- FastAPI
- SQLAlchemy
- PostgreSQL
- WebSockets
- AWS S3

## Requisitos

- Python 3.10 o superior
- PostgreSQL
- Variables de entorno configuradas

## Instalación

1. Instala las dependencias:

```bash
pip install -r requirements.txt
```

2. Crea un archivo `.env` en la raíz del proyecto con una configuración similar a esta:

```env
DB_URL=postgresql+psycopg2://usuario:contraseña@localhost:5432/smartvitals
SECRET_KEY=
AWS_S3_BUCKET_NAME=

DB_USER=
DB_PASSWORD=
DB_HOST=localhost
DB_NAME=smartvitals
DB_PORT=5432

RABBITMQ_HOST=
RABBITMQ_USER=
RABBITMQ_PASSWORD=
RABBITMQ_PORT=
RABBITMQ_VIRTUAL_HOST=/
MQTT_PORT=

aws_region=
aws_access_key_id=
aws_secret_access_key=
aws_session_token=
```

> **Nota:**
>
> - Llena los valores de `aws_access_key_id`, `aws_secret_access_key`, `aws_session_token` y `aws_region` con tus credenciales de AWS.
> - Si la instancia AWS no esta prendida, entonces se utilizará una Base de datos de manera local.

## Ejecución

### Servidor REST

```bash
uvicorn main:app --reload
```

### Servidor WebSocket

```bash
uvicorn websocket:app --reload --port 8001
```

## WebSocket de sensores

Conéctate a:

```text
ws://localhost:8001/ws/sensores
```

Ejemplos de mensajes:

```json
{ "action": "start", "patient_id": 5 }
```

```json
{ "action": "stop", "patient_id": 5 }
```

