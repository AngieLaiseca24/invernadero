import numpy as np
import pandas as pd
from sklearn.linear_model import LinearRegression
from ultralytics import YOLO
import cv2

modelo_yolo = YOLO("yolov8n.pt")

modelo_temp = None
modelo_hum = None

# Variables para guardar el último índice entrenado
ultimo_index_temp = 0
ultimo_index_hum = 0

def entrenar_modelo(datos, tipo="temperatura"):
    global modelo_temp, modelo_hum, ultimo_index_temp, ultimo_index_hum
    df = pd.DataFrame(datos)

    if df.shape[0] < 3:
        return False

    df['index'] = range(len(df))
    X = df[['index']]
    y = df['valor']

    if tipo == "temperatura":
        modelo_temp = LinearRegression()
        modelo_temp.fit(X, y)
        ultimo_index_temp = df['index'].iloc[-1]
    elif tipo == "humedad":
        modelo_hum = LinearRegression()
        modelo_hum.fit(X, y)
        ultimo_index_hum = df['index'].iloc[-1]
    else:
        return False

    return True

def predecir_futuro(pasos=1, tipo="temperatura"):
    if tipo == "temperatura" and modelo_temp is not None:
        pred = modelo_temp.predict(np.array([[ultimo_index_temp + pasos]]))
        return float(pred[0])
    elif tipo == "humedad" and modelo_hum is not None:
        pred = modelo_hum.predict(np.array([[ultimo_index_hum + pasos]]))
        return float(pred[0])
    return None

def detectar_objetos(imagen_np):
    imagen_bgr = cv2.cvtColor(imagen_np, cv2.COLOR_RGB2BGR)
    resultados = modelo_yolo(imagen_bgr)

    objetos = []
    for r in resultados:
        nombres = r.names
        clases_detectadas = r.boxes.cls.tolist()
        objetos = [nombres[int(clase)] for clase in clases_detectadas]

    return objetos
