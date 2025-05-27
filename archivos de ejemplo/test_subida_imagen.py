#Este archivo es un ejemplo de cómo debería de enviarse la imagen a la base de datos ya sea como imágen o como binario raw bytes

import os
import requests
import base64

# Puede ser una ruta como "foto.jpg" o una cadena en base64 o directamente bytes crudos
entrada_imagen = ""  # Asignar aquí la ruta de la imagen (../imagen.jpg) o el binario en raw bytes (una cadena de caracteres bastante larga)

# URL del endpoint
url = "http://localhost:5000/api/sensores" # Conexión con el endpoint en el que se va a almacenar la imagen

# Función que determina si la entrada es un archivo o un raw byte
def es_archivo(ruta):
    return isinstance(ruta, str) and os.path.isfile(ruta)

try:
    # Caso 1: es una ruta válida a un archivo
    if es_archivo(entrada_imagen):
        with open(entrada_imagen, "rb") as f:
            imagen_bytes = f.read()
    
    # Caso 2: ya son bytes en base64 o crudos
    else:
        # Si es una cadena en base64, la decodificamos (verificamos si tiene padding típico '=' o comienza con '/9j' para JPEG)
        if isinstance(entrada_imagen, str):
            try:
                imagen_bytes = base64.b64decode(entrada_imagen) #Aquí se decodifica el código almacenado en "entrada_imagen" debido a la complejidad de la cadena de caracteres
            except Exception:
                raise ValueError("La cadena no es base64 válida.")
        elif isinstance(entrada_imagen, bytes):
            imagen_bytes = entrada_imagen
        else:
            raise ValueError("Formato no reconocido para la imagen.")

    # Enviar la imagen al backend
    response = requests.post(
        url,
        headers={"Content-Type": "application/octet-stream"},
        data=imagen_bytes
    )

    # Mostrar respuesta
    print("Código de estado:", response.status_code)
    print("Respuesta:", response.json())

except Exception as e:
    print("Error al procesar la imagen:", str(e))
