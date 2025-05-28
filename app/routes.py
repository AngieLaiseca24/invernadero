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

#Este endpoint es para guardar los datos de temperatura en la base de datos
@bp.route('/api/temperatura', methods=['POST'])
def guardar_datos_temperatura():
    data = request.get_json()

    if not data:
        return jsonify({"error": "Datos JSON faltantes"}), 400
    
    if 'temperatura' not in data:
        return jsonify({"error": "Se requiere 'temperatura'"}), 400

    data['timestamp'] = datetime.utcnow()
    db = get_db()
    db['Temperatura'].insert_one(data)

    return jsonify({"mensaje": "Datos ambientales guardados"}), 201


#Este es para humedad, si se quiere guardar
@bp.route('/api/humedad', methods=['POST'])
def guardar_datos_humedad():
    data = request.get_json()

    if not data:
        return jsonify({"error": "Datos JSON faltantes"}), 400
    
    if 'humedad' not in data:
        return jsonify({"error": "Se requiere 'humedad'"}), 400

    data['timestamp'] = datetime.utcnow()
    db = get_db()
    db['Humedad'].insert_one(data)

    return jsonify({"mensaje": "Datos ambientales guardados"}), 201

#Este es para humedad, si se quiere guardar
@bp.route('/api/nivelaguahorizontal', methods=['POST'])
def guardar_datos_nivelaguahorizontal():
    data = request.get_json()

    if not data:
        return jsonify({"error": "Datos JSON faltantes"}), 400
    
    if 'nivelaguahorizontal' not in data:
        return jsonify({"error": "Se requiere 'nivel agua horizontal'"}), 400

    data['timestamp'] = datetime.utcnow()
    db = get_db()
    db['NivelAguaHorizontal'].insert_one(data)

    return jsonify({"mensaje": "Datos ambientales guardados"}), 201

#Este es para humedad, si se quiere guardar
@bp.route('/api/nivelaguavertical', methods=['POST'])
def guardar_datos_nivelaguavertical():
    data = request.get_json()

    if not data:
        return jsonify({"error": "Datos JSON faltantes"}), 400
    
    if 'nivelaguavertical' not in data:
        return jsonify({"error": "Se requiere 'nivel agua vertical'"}), 400

    data['timestamp'] = datetime.utcnow()
    db = get_db()
    db['NivelAguaVertical'].insert_one(data)

    return jsonify({"mensaje": "Datos ambientales guardados"}), 201




#Este endpoint es para extraer los datos guardados en la base de datos
@bp.route('/api/humedad', methods=['GET'])
def obtener_datos_humedad():
    db = get_db()
    datos = list(db['Humedad'].find({}, {"_id": 0}))
    return jsonify(datos)

@bp.route('/api/temperatura', methods=['GET'])
def obtener_datos_temperatura():
    db = get_db()
    datos = list(db['Temperatura'].find({}, {"_id": 0}))
    return jsonify(datos)

@bp.route('/api/nivelaguahorizontal', methods=['GET'])
def obtener_datos_nivelaguahorizontal():
    db = get_db()
    datos = list(db['NivelAguaHorizontal'].find({}, {"_id": 0}))
    return jsonify(datos)

@bp.route('/api/nivelaguavertical', methods=['GET'])
def obtener_datos_nivelaguavertical():
    db = get_db()
    datos = list(db['NivelAguaVertical'].find({}, {"_id": 0}))
    return jsonify(datos)




@bp.route('/api/imagenes', methods=['POST'])
def guardar_imagen_esp32():
    try:
        data = request.get_json()
        
        # Validar que llegue la imagen en base64
        if not data or 'imagen_base64' not in data:
            return jsonify({"error": "El campo 'imagen_base64' es obligatorio"}), 400
        
        imagen_base64 = data['imagen_base64']
        
        # Decodificar base64 a bytes
        try:
            # Remover prefijo si existe (data:image/jpeg;base64,)
            if ',' in imagen_base64:
                imagen_base64 = imagen_base64.split(',')[1]
            
            imagen_bytes = base64.b64decode(imagen_base64)
        except Exception as e:
            return jsonify({"error": f"Error decodificando base64: {str(e)}"}), 400
        
        # Validar que sea una imagen válida
        try:
            imagen_pil = Image.open(io.BytesIO(imagen_bytes))
            imagen_pil.verify()  # Verifica que sea una imagen válida
        except Exception as e:
            return jsonify({"error": f"Archivo no es una imagen válida: {str(e)}"}), 400
        
        # Guardar en GridFS
        db = get_db()
        fs = GridFS(db)
        
        # Metadatos básicos
        metadata = {
            'timestamp': datetime.utcnow(),
            'source': 'esp32',
            'content_type': 'image/jpeg'
        }
        
        # Guardar imagen en GridFS
        file_id = fs.put(
            imagen_bytes,
            filename=f"esp32_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.jpg",
            metadata=metadata
        )
        
        return jsonify({
            "mensaje": "Imagen guardada exitosamente",
            "file_id": str(file_id)
        }), 201
        
    except Exception as e:
        return jsonify({"error": f"Error interno del servidor: {str(e)}"}), 500

@bp.route('/api/imagenes/<string:file_id>', methods=['GET'])
def obtener_imagen_gridfs(file_id):
    try:
        db = get_db()
        fs = GridFS(db)
        
        file = fs.get(ObjectId(file_id))
        
        return send_file(
            BytesIO(file.read()),
            mimetype='image/jpeg',
            as_attachment=False,
            download_name=f"imagen_{file_id}.jpg"
        )
        
    except Exception as e:
        return jsonify({"error": f"Error obteniendo imagen: {str(e)}"}), 404

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

