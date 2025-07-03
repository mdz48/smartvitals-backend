# Backend Evotek

## Configuración Inicial

Para el correcto funcionamiento del backend ejecutar los siguientes comandos:

### 1. Instalación de dependencias
```bash
pip install -r requirements.txt
```

### 2. Configuración de variables de entorno

Crear un archivo `.env` en la raíz del proyecto con la siguiente configuración:

```
DATABASE_URL=mysql://root:root@localhost:3306/evotek
SECRET_KEY=
AWS_S3_BUCKET_NAME=

DATABASE_USER=
DATABASE_PASSWORD=
DB_HOST=
DB_NAME=
DB_PORT=

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
> - Llena los valores de `aws_access_key_id`, `aws_secret_access_key`, `aws_session_token` y `aws_region` con tus credenciales de AWS.
> - Si la instancia AWS no esta prendida, entonces se utilizará una Base de datos de manera local.

## Ejecutar el servidor REST
```bash
uvicorn main:app --reload
```

## Ejecutar el servidor Websocket
```bash
uvicorn websocket:app --reload --port 8001
```

## Conectarse a Ws para guardar un expediente
```bash
ws://localhost:8001/ws/sensores
{"action": "start", "patient_id": 5}
{"action": "stop", "patient_id": 5}
```

## Notas importantes
- Las tablas se crean automáticamente al iniciar la aplicación.
- Para cambios en la estructura de la base de datos, elimina las tablas manualmente y reinicia la aplicación.