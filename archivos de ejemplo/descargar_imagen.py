#Este archivo es un ejempo de cómo obtener las imagenes de la base de datos en caso de que se quieran guardar en una carpeta local

import requests

indice = 0  # Índice de la imagen que deseas obtener de la base de datos MongoDB (indice 0 significa la primera imagen en la DB)

url = f"http://localhost:5000/api/sensores/{indice}" # Conexión al endpoint pasando el indice

response = requests.get(url)

if response.status_code == 200:
    with open(f"imagen_recuperada_{indice}.jpg", "wb") as f: #Aquí se transforma el código binario a imagen y se descarga a la carpeta contenedora de descargar_imagen.py
        f.write(response.content)
    print("✅ Imagen descargada correctamente")
else:
    print("❌ Error:", response.status_code, response.json())
