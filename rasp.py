import time
import json
import paho.mqtt.client as mqtt
import pika
from smbus2 import SMBus
from max30102 import MAX30102
import hrcalc

# ---------- Configuracion RabbitMQ ----------
RABBITMQ_HOST = "100.28.59.47"
RABBITMQ_USER = "admin"
RABBITMQ_PASSWORD = "password"
EXCHANGE = 'amq.topic'

# ---------- Configuracion MQTT ----------
mqtt_host = "100.28.59.47"
mqtt_port = 1883
mqtt_user = "admin"
mqtt_password = "password"
mqtt_topic_temp = "temperatura"
mqtt_topic_oxi = "oxigeno"

# ---------- Variables globales ----------
current_medical_file_id = None  # ID del expediente activo

# ---------- Sensor MLX90614 ----------
class MLX90614:
    MLX90614_TOBJ1 = 0x07

    def __init__(self, address=0x5A, bus=1):
        self.bus = SMBus(bus)
        self.address = address

    def read_temp(self, reg):
        temp = self.bus.read_word_data(self.address, reg)
        return round(temp * 0.02 - 273.15, 2)

    def get_object_temp(self):
        return self.read_temp(self.MLX90614_TOBJ1)

# ---------- Funcion para enviar datos a RabbitMQ ----------
def send_to_rabbitmq(topic, data):
    try:
        credentials = pika.PlainCredentials(RABBITMQ_USER, RABBITMQ_PASSWORD)
        parameters = pika.ConnectionParameters(host=RABBITMQ_HOST, credentials=credentials)
        connection = pika.BlockingConnection(parameters)
        channel = connection.channel()
        message = json.dumps(data)
        channel.basic_publish(
            exchange=EXCHANGE,
            routing_key=topic,
            body=message,
            properties=pika.BasicProperties(delivery_mode=2)
        )
        print(f"Datos enviados a RabbitMQ - {topic}: {message}")
        connection.close()
    except Exception as e:
        print(f"Error enviando a RabbitMQ: {e}")

# ---------- Funcion para recibir configuracion de usuario ----------
def receive_user_config():
    global current_medical_file_id
    try:
        credentials = pika.PlainCredentials(RABBITMQ_USER, RABBITMQ_PASSWORD)
        parameters = pika.ConnectionParameters(host=RABBITMQ_HOST, credentials=credentials)
        connection = pika.BlockingConnection(parameters)
        channel = connection.channel()
        channel.queue_declare(queue='user_config', durable=True)
        channel.queue_bind(exchange=EXCHANGE, queue='user_config', routing_key='user_config')
        def config_callback(ch, method, properties, body):
            global current_medical_file_id
            try:
                config = json.loads(body)
                current_medical_file_id = config.get("medical_file_id", current_medical_file_id)
                print(f"Configuracion recibida: Expediente {current_medical_file_id}")
            except Exception as e:
                print(f"Error procesando configuracion: {e}")
        channel.basic_consume(queue='user_config', on_message_callback=config_callback, auto_ack=True)
        connection.process_data_events(time_limit=1)
        connection.close()
    except Exception as e:
        print(f"Error recibiendo configuracion: {e}")

# ---------- Funcion para comunicar el estatus de los sensores ----------     
def get_sensors_status():
    status = {
        "raspberry": True,
        "MAX30102": False,
        "MLX90614": False,
        "ADB8232": False,
        "MP520N004D": False
    }
    try:
        _ = sensor_temp.get_object_temp()
        status["MLX90614"] = True
    except Exception:
        pass
    try:
        bpm, spo2 = leer_bpm_spo2(sensor_oxi)
        status["MAX30102"] = True
    except Exception:
        pass
    return status

def send_status():
    status = get_sensors_status()
    status["timestamp"] = time.time()
    send_to_rabbitmq("sensor", status)

# ---------- MQTT Config ----------
client = mqtt.Client()
client.username_pw_set(mqtt_user, mqtt_password)
client.connect(mqtt_host, mqtt_port, keepalive=60)
client.loop_start()

# ---------- Inicializar sensores ----------
sensor_temp = MLX90614()
sensor_oxi = MAX30102()

# ---------- Funcion para obtener BPM y SpO2 ----------
def leer_bpm_spo2(sensor):
    red_buf = []
    ir_buf = []
    for i in range(100):
        red, ir = sensor.read_fifo()
        red_buf.append(red)
        ir_buf.append(ir)
        time.sleep(0.03)
    bpm, valid_bpm, spo2, valid_spo2 = hrcalc.calc_hr_and_spo2(ir_buf, red_buf)
    if not valid_bpm:
        bpm = 0
    if not valid_spo2:
        spo2 = 0
    return round(bpm, 2), round(spo2, 2)

# ---------- Loop principal ----------
try:
    print(f"Iniciando sensores para Expediente ID: {current_medical_file_id}")
    ciclo = 0
    while True:
        # Recibe la configuración (incluye medical_file_id)
        receive_user_config()
        if current_medical_file_id is None:
            print("Esperando configuracion de expediente...")
            time.sleep(2)
            continue

        # Enviar estatus al front
        ciclo += 1
        if ciclo % 2 == 0:
            send_status()

        # Lectura temperatura
        temperatura = sensor_temp.get_object_temp()
        rabbitmq_temp_data = {
            "medical_file_id": current_medical_file_id,
            "temperature": temperatura,
            "timestamp": time.time()
        }
        send_to_rabbitmq("temperatura", rabbitmq_temp_data)
        mensaje_temp = json.dumps({
            "medical_file_id": current_medical_file_id,
            "temperature": temperatura,
            "timestamp": time.time()
        })
        client.publish(mqtt_topic_temp, mensaje_temp)
        print("Temperatura enviada:", mensaje_temp)

        # Lectura MAX30102
        bpm, spo2 = leer_bpm_spo2(sensor_oxi)
        rabbitmq_oxi_data = {
            "medical_file_id": current_medical_file_id,
            "oxygen_saturation": spo2,
            "heart_rate": bpm,
            "timestamp": time.time()
        }
        send_to_rabbitmq("oxigeno", rabbitmq_oxi_data)
        send_to_rabbitmq("ritmo_cardiaco", rabbitmq_oxi_data)
        mensaje_oxi = json.dumps({
            "medical_file_id": current_medical_file_id,
            "bpm": bpm,
            "spo2": spo2,
            "timestamp": time.time()
        })
        client.publish(mqtt_topic_oxi, mensaje_oxi)
        print("Oxigeno enviado:", mensaje_oxi)

        time.sleep(2)

except KeyboardInterrupt:
    print("Interrumpido por el usuario.")
finally:
    client.loop_stop()
    client.disconnect()
    print("MQTT desconectado.")
