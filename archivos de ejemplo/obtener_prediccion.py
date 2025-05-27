#Este es un archivo para dejar un ejemplo de cómo obtener las imagenes para una predicción (obtiene todas las que están en la base de datos)

import requests

# Endpoint de predicción
url = f"http://localhost:5000/api/prediccion"

# Realizar GET
response = requests.get(url)

# Mostrar respuesta
print("Código de estado:", response.status_code)
print("Respuesta JSON:", response.json())