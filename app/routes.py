from flask import Blueprint, request, jsonify, send_file
from bson.binary import Binary
import io
from io import BytesIO
from .db import get_db
from .ai_model import entrenar_modelo, predecir_temperatura_futura
from PIL import Image
import numpy as np

bp = Blueprint('api', __name__)


#Endpoint para guardar la imagen en la base de datos en la colección "sensores"
@bp.route('/api/sensores', methods=['POST'])
def guardar_imagen():
    """
    Guarda una imagen enviada como binary raw bytes en MongoDB.
    """
    if request.content_type != 'application/octet-stream':
        return jsonify({"error": "Content-Type debe ser 'application/octet-stream'"}), 400

    imagen_bytes = request.get_data() #Se obtiene la data pasada en el script de subir imagen
    if not imagen_bytes:
        return jsonify({"error": "No se recibió la imagen en el cuerpo de la solicitud"}), 400

    data = {
        "imagen": Binary(imagen_bytes)
    }

    db = get_db()
    db.sensores.insert_one(data)
    return jsonify({"mensaje": "Imagen almacenada correctamente"}), 201



#Endpoint para obtener la imagen desde la base de datos
@bp.route('/api/sensores/<int:indice>', methods=['GET'])
def obtener_imagen(indice):
    db = get_db()
    documentos = list(db.sensores.find({}))

    if indice < 0 or indice >= len(documentos):
        return jsonify({"error": "Índice fuera de rango"}), 404

    doc = documentos[indice]
    if "imagen" not in doc:
        return jsonify({"error": "No se encontró la imagen"}), 404

    imagen_binaria = doc["imagen"]

    return send_file(
        BytesIO(imagen_binaria),
        mimetype='image/jpeg',  # o 'image/png' si lo prefieres
        as_attachment=False,
        download_name=f"imagen_{indice}.jpg"
    )


#Endpoint para obtener las imagenes de la base de datos y utilizarlas para una predicción (lo puede modificar completamente a su gusto, es solo un esqueleto para que se guien)
@bp.route('/api/prediccion', methods=['GET'])
def obtener_prediccion():
    #Simulación de predicción basada en imágenes.

    db = get_db()
    documentos = list(db.sensores.find({"imagen": {"$exists": True}}, {"imagen": 1, "_id": 0})) #Listar las imagenes de la base de datos
    
    if not documentos or len(documentos) < 1: #Verifica que haya imagenes
        return jsonify({"error": "No hay imágenes disponibles para predecir"}), 400

    try: #Procesar las imagenes y convertirlas
        # Procesar las imágenes para el futuro modelo
        imagenes = []
        for doc in documentos:
            imagen = Image.open(io.BytesIO(doc["imagen"])).convert("RGB").resize((224, 224))
            imagen_np = np.array(imagen) / 255.0  # Normalizar
            imagenes.append(imagen_np)

        imagenes = np.array(imagenes)  # Este array estará listo para usarse en una red neuronal convolucional

        #Simulación de predecir (Aqui pueden poner el modelo y consumirlo para la predicción)
        prediccion_simulada = 0.85  # Valor simulado

        return jsonify({ #Respuesta en Json luego de simular
            "mensaje": "Predicción simulada. El modelo aún no está integrado.",
            "prediccion_simulada": prediccion_simulada,
            "cantidad_imagenes_procesadas": len(imagenes) #Dice cuantas imagenes de la base de datos tomó y procesó
        })

    except Exception as e:
        return jsonify({"error": f"Ocurrió un error procesando las imágenes: {str(e)}"}), 500
