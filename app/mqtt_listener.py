import base64
import io
from PIL import Image
from datetime import datetime
from gridfs import GridFS
from bson.binary import Binary
import paho.mqtt.client as mqtt
from db import get_db  # importa tu función de conexión

# === CONFIGURACIÓN DEL BROKER MQTT ===
MQTT_BROKER = "192.168.222.191"
MQTT_PORT = 1883
MQTT_TOPIC = "camara/foto"  # el topic que publica la imagen base64

# === CALLBACK CUANDO LLEGA UN MENSAJE ===
def on_message(client, userdata, msg):
    try:
        imagen_base64 = msg.payload.decode()

        # Quitar prefijo si lo tiene
        if ',' in imagen_base64:
            imagen_base64 = imagen_base64.split(',')[1]

        imagen_bytes = base64.b64decode(imagen_base64)

        # Validar que sea imagen válida
        imagen_pil = Image.open(io.BytesIO(imagen_bytes))
        imagen_pil.verify()

        # Guardar en GridFS
        db = get_db()
        fs = GridFS(db)

        metadata = {
            'timestamp': datetime.utcnow(),
            'source': 'mqtt_esp32',
            'content_type': 'image/jpeg'
        }

        file_id = fs.put(
            imagen_bytes,
            filename=f"mqtt_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.jpg",
            metadata=metadata
        )

        print(f"[✓] Imagen guardada desde MQTT con ID: {file_id}")

    except Exception as e:
        print(f"[✗] Error procesando imagen desde MQTT: {e}")

# === INICIAR CLIENTE MQTT ===
def iniciar_mqtt():
    client = mqtt.Client()
    client.on_message = on_message

    client.connect(MQTT_BROKER, MQTT_PORT)
    client.subscribe(MQTT_TOPIC)

    print(f"📡 Escuchando en topic: {MQTT_TOPIC}")
    client.loop_forever()

if __name__ == "__main__":
    iniciar_mqtt()
