# Backend Evotek

## Configuración Inicial

Para el correcto funcionamiento del backend ejecutar los siguientes comandos:

### 1. Instalación de dependencias
```bash
pip install -r requirements.txt
```

### 2. Configuración de variables de entorno
Crear un archivo `.env` en la raíz del proyecto con la configuración de la base de datos:
```
DATABASE_URL=mysql+pymysql://usuario:contraseña@localhost:3306/nombre_base_datos
```

## Ejecutar el servidor
```bash
uvicorn main:app --reload
```

## Notas importantes
- Las tablas se crean automáticamente al iniciar la aplicación
- Para cambios en la estructura de la base de datos, eliminar las tablas manualmente y reiniciar la aplicación