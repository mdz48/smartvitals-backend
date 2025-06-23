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

aws_region=
aws_access_key_id=
aws_secret_access_key=
aws_session_token=
```

> **Nota:**  
> - Llena los valores de `aws_access_key_id`, `aws_secret_access_key`, `aws_session_token` y `aws_region` con tus credenciales de AWS.
> - `DATABASE_USER` y `DATABASE_PASSWORD` son opcionales si ya están incluidos en `DATABASE_URL`.

## Ejecutar el servidor
```bash
uvicorn main:app --reload
```

## Notas importantes
- Las tablas se crean automáticamente al iniciar la aplicación.
- Para cambios en la estructura de la base de datos, elimina las tablas manualmente y reinicia la aplicación.