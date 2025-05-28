from flask import Blueprint, request, jsonify, send_file
from bson.binary import Binary
from bson import ObjectId
from .db import get_db
from .ai_model import entrenar_modelo, predecir_temperatura_futura, detectar_objetos
from PIL import Image
from gridfs import GridFS
import numpy as np
import io
import base64
from datetime import datetime
from io import BytesIO

bp = Blueprint('api', __name__)

# este endpoint es para obtener la imagen desde la base de datos
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
        mimetype='image/jpeg',  
        as_attachment=False,
        download_name=f"imagen_{indice}.jpg"
    )



@bp.route('/api/objetos/<int:indice>', methods=['GET'])
def detectar_objetos_en_base64(indice):
    db = get_db()
    documentos = list(db.sensores.find({}))  # cambiar 'sensores' si el grupo usa otra colección

    if indice < 0 or indice >= len(documentos):
        return jsonify({"error": "Índice fuera de rango"}), 404

    doc = documentos[indice]

    if "imagen_base64" not in doc:
        return jsonify({"error": "No se encontró la imagen en base64"}), 404  # cambair'imagen_base64' si usan otro campo

    try:
        imagen_bytes = base64.b64decode(doc["imagen_base64"])
        imagen = Image.open(io.BytesIO(imagen_bytes)).convert("RGB").resize((640, 640))  # cambiar el tamaño si YOLO necesita otro input :)
        imagen_np = np.array(imagen)

        objetos = detectar_objetos(imagen_np)

        db.sensores.update_one({"_id": doc["_id"]}, {  # volver a cambiar 'sensores' si usan otra colección
            "$set": {
                "objetos_detectados": objetos,
                "fecha_deteccion": datetime.utcnow()
            }
        })

        return jsonify({
            "mensaje": "Detección completada (base64)",
            "objetos_detectados": objetos
        })

    except Exception as e:
        return jsonify({"error": f"Error procesando la imagen: {str(e)}"}), 500



@bp.route('/api/objetos/gridfs/<string:file_id>', methods=['GET'])
def detectar_objetos_en_gridfs(file_id):
    db = get_db()
    fs = GridFS(db)  

    try:
        file = fs.get(ObjectId(file_id))  # cambiarr si el ID viene en otro formato o campo distinto
        imagen_bytes = file.read()

        imagen = Image.open(io.BytesIO(imagen_bytes)).convert("RGB").resize((640, 640))
        imagen_np = np.array(imagen)

        objetos = detectar_objetos(imagen_np)

        return jsonify({
            "mensaje": "Detección completada (GridFS)",
            "objetos_detectados": objetos
        })

    except Exception as e:
        return jsonify({"error": f"Error leyendo desde GridFS: {str(e)}"}), 500



@bp.route('/api/temperatura', methods=['GET'])
def predecir_temperatura():
    db = get_db()

    documentos = list(db.sensores.find(
        {"tipo": "temperatura"},  # cambiar 'tipo' y 'temperatura' si usan otra forma de filtrar
        {"valor": 1, "_id": 0}    # cambiar'valor' si se llama de otra forma
    ))

    if not documentos or len(documentos) < 3:
        return jsonify({"error": "No hay suficientes datos"}), 400

    try:
        if entrenar_modelo(documentos):
            pred = predecir_temperatura_futura(pasos=1)
            return jsonify({
                "mensaje": "Predicción completada",
                "prediccion_temperatura": round(pred, 2),
                "datos_utilizados": len(documentos)
            })
        else:
            return jsonify({"error": "No se pudo entrenar el modelo"}), 500

    except Exception as e:
        return jsonify({"error": f"Error procesando la predicción: {str(e)}"}), 500

