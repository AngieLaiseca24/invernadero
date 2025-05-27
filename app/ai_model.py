import pandas as pd
from sklearn.linear_model import LinearRegression
import numpy as np

model = None

def entrenar_modelo(datos):
    global model
    df = pd.DataFrame(datos)
    if df.shape[0] < 3:
        return False
    df['index'] = range(len(df))
    X = df[['index']]
    y = df['temperatura']
    model = LinearRegression()
    model.fit(X, y)
    return True

def predecir_temperatura_futura(pasos=1):
    if model is None:
        return None
    pred = model.predict(np.array([[model.n_features_in_ + pasos - 1]]))
    return float(pred[0])