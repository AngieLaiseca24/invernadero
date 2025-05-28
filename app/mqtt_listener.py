import json
import base64
import io
from PIL import Image
from datetime import datetime
from gridfs import GridFS
import paho.mqtt.client as mqtt
from db import get_db

# === CONFIGURACIÓN DEL BROKER MQTT ===
MQTT_BROKER = "192.168.222.191"
MQTT_PORT = 1883

# === TOPICS ===
TOPIC_AMBIENTE = "iot/ambiente"
TOPIC_NIVEL = "iot/nivel"
TOPIC_IMAGEN = "camara/foto"

# === CALLBACK GENERAL ===
def on_message(client, userdata, msg):
    try:
        db = get_db()

        if msg.topic == TOPIC_AMBIENTE:
            data = json.loads(msg.payload.decode())
            print("[📡] Ambiente:", data)

            if 'temperatura' in data:
                db["Temperatura"].insert_one({
                    "tipo": "temperatura",
                    "valor": float(data["temperatura"]),
                    "timestamp": datetime.utcnow()
                })
                print(f"  → Temperatura guardada: {data['temperatura']}")

            if 'humedad' in data:
                db["Humedad"].insert_one({
                    "tipo": "humedad",
                    "valor": float(data["humedad"]),
                    "timestamp": datetime.utcnow()
                })
                print(f"  → Humedad guardada: {data['humedad']}")

        elif msg.topic == TOPIC_NIVEL:
            data = json.loads(msg.payload.decode())
            print("[📡] Nivel de agua:", data)

            if 'horizontal' in data:
                db["NivelAguaHorizontal"].insert_one({
                    "tipo": "nivelaguahorizontal",
                    "valor": data["horizontal"],  # tipo string (e.g., "MAXIMO")
                    "timestamp": datetime.utcnow()
                })
                print(f"  → Nivel horizontal guardado: {data['horizontal']}")

            if 'vertical' in data:
                db["NivelAguaVertical"].insert_one({
                    "tipo": "nivelaguavertical",
                    "valor": data["vertical"],  # tipo string (e.g., "VACIO")
                    "timestamp": datetime.utcnow()
                })
                print(f"  → Nivel vertical guardado: {data['vertical']}")

        elif msg.topic == TOPIC_IMAGEN:
            imagen_base64 = msg.payload.decode()

            if ',' in imagen_base64:
                imagen_base64 = imagen_base64.split(',')[1]

            imagen_bytes = base64.b64decode(imagen_base64)
            imagen_pil = Image.open(io.BytesIO(imagen_bytes))
            imagen_pil.verify()

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

        else:
            print(f"[⚠️] Topic no manejado: {msg.topic}")

    except Exception as e:
        print(f"[✗] Error procesando mensaje MQTT ({msg.topic}): {e}")

# === INICIAR CLIENTE MQTT ===
def iniciar_mqtt():
    client = mqtt.Client()
    client.on_message = on_message

    client.connect(MQTT_BROKER, MQTT_PORT)

    client.subscribe(TOPIC_AMBIENTE)
    client.subscribe(TOPIC_NIVEL)
    client.subscribe(TOPIC_IMAGEN)

    print("📡 Suscrito a:")
    print(f" - {TOPIC_AMBIENTE}")
    print(f" - {TOPIC_NIVEL}")
    print(f" - {TOPIC_IMAGEN}")

    client.loop_forever()

if __name__ == "__main__":
    iniciar_mqtt()
