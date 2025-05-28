import numpy as np
import pandas as pd
from sklearn.linear_model import LinearRegression
from ultralytics import YOLO
import cv2


modelo_yolo = YOLO("yolov8n.pt") 

modelo = None  # Modelo pa predicción de temperatura

def entrenar_modelo(datos):
    """
    Entrena un modelo de regresión lineal simple para predecir temperatura.
    Espera una lista de diccionarios con clave 'valor'.
    """
    global modelo
    df = pd.DataFrame(datos)

    if df.shape[0] < 3:
        return False

    df['index'] = range(len(df))
    X = df[['index']]
    y = df['valor']                      # Cambiar si el campo no es 'valor'
    modelo = LinearRegression()
    modelo.fit(X, y)
    return True

def predecir_temperatura_futura(pasos=1):
    """
    Predice la temperatura futura usando el modelo entrenado.
    """
    if modelo is None:
        return None
    pred = modelo.predict(np.array([[modelo.n_features_in_ + pasos - 1]]))
    return float(pred[0])

def detectar_objetos(imagen_np):
    """
    Aplica YOLOv8 para detectar objetos en una imagen NumPy.
    """
    imagen_bgr = cv2.cvtColor(imagen_np, cv2.COLOR_RGB2BGR)
    resultados = modelo_yolo(imagen_bgr)

    objetos = []
    for r in resultados:
        nombres = r.names
        clases_detectadas = r.boxes.cls.tolist()
        objetos = [nombres[int(clase)] for clase in clases_detectadas]

    return objetos
