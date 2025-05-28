import json
import base64
import io
from PIL import Image
from datetime import datetime
from gridfs import GridFS
import paho.mqtt.client as mqtt
from db import get_db
import threading
import time
import numpy as np
from ai_model import entrenar_modelo, predecir_futuro, detectar_objetos

# === CONFIGURACIÓN DEL BROKER MQTT ===
MQTT_BROKER = "192.168.204.153"
MQTT_PORT = 1883

# === TOPICS ===
TOPIC_AMBIENTE = "iot/ambiente"
TOPIC_NIVEL = "iot/nivel"
TOPIC_IMAGEN = "camara/foto"
TOPIC_DETECCION = "deteccion/personas"
TOPIC_TEMP_PRED = "iot/temperatura/prediccion"
TOPIC_HUM_PRED = "iot/humedad/prediccion"

# === FUNCIONES ===

def publicar_a_mqtt(payload, topic):
    try:
        client = mqtt.Client()
        client.connect(MQTT_BROKER, MQTT_PORT, 60)
        client.publish(topic, json.dumps(payload))
        client.disconnect()
    except Exception as e:
        print(f"[MQTT] Error al publicar: {e}")

def prediccion_automatica():
    while True:
        try:
            db = get_db()

            # === Temperatura ===
            datos_temp = list(db["Temperatura"].find({"tipo": "temperatura"}, {"valor": 1, "_id": 0}))
            if len(datos_temp) >= 3 and entrenar_modelo(datos_temp, tipo="temperatura"):
                pred_temp = predecir_futuro(pasos=1, tipo="temperatura")
                payload_temp = {
                    "mensaje": "Predicción automática temperatura",
                    "prediccion_temperatura": round(pred_temp, 2),
                    "timestamp": datetime.utcnow().isoformat()
                }
                publicar_a_mqtt(payload_temp, TOPIC_TEMP_PRED)
                print(f"[🌡️] Predicción temperatura: {payload_temp}")

            # === Humedad ===
            datos_hum = list(db["Humedad"].find({"tipo": "humedad"}, {"valor": 1, "_id": 0}))
            if len(datos_hum) >= 3 and entrenar_modelo(datos_hum, tipo="humedad"):
                pred_hum = predecir_futuro(pasos=1, tipo="humedad")
                payload_hum = {
                    "mensaje": "Predicción automática humedad",
                    "prediccion_humedad": round(pred_hum, 2),
                    "timestamp": datetime.utcnow().isoformat()
                }
                publicar_a_mqtt(payload_hum, TOPIC_HUM_PRED)
                print(f"[💧] Predicción humedad: {payload_hum}")

        except Exception as e:
            print(f"[✗] Error en predicción automática: {e}")

        time.sleep(5)

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
                    "valor": data["horizontal"],
                    "timestamp": datetime.utcnow()
                })
                print(f"  → Nivel horizontal guardado: {data['horizontal']}")

            if 'vertical' in data:
                db["NivelAguaVertical"].insert_one({
                    "tipo": "nivelaguavertical",
                    "valor": data["vertical"],
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

            imagen_pil = Image.open(io.BytesIO(imagen_bytes)).convert("RGB").resize((640, 640))
            imagen_np = np.array(imagen_pil)

            objetos = detectar_objetos(imagen_np)

            resultado = {
                "mensaje": "Detección automática desde MQTT",
                "objetos_detectados": objetos,
                "file_id": str(file_id),
                "fecha_deteccion": datetime.utcnow().isoformat()
            }

            publicar_a_mqtt(resultado, TOPIC_DETECCION)
            print(f"[🎯] Objetos detectados automáticamente: {objetos}")

        else:
            print(f"[⚠️] Topic no manejado: {msg.topic}")

    except Exception as e:
        print(f"[✗] Error procesando mensaje MQTT ({msg.topic}): {e}")

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
    hilo_pred = threading.Thread(target=prediccion_automatica, daemon=True)
    hilo_pred.start()

    iniciar_mqtt()
