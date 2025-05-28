import requests
import base64

BASE_URL = "http://localhost:5000"

def test_post_sensores():
    data = {
        "temperatura": 25.5,
        "humedad": 60,
        "timestamp": "2025-05-26T14:00:00Z"
    }
    r = requests.post(f"{BASE_URL}/api/sensores", json=data)
    print("POST sensores:", r.status_code, r.json())

def test_get_sensores():
    r = requests.get(f"{BASE_URL}/api/sensores")
    print("GET sensores:", r.status_code, r.json())

def test_post_imagen():
    with open("../IMG_20250517_180841_1.jpg", "rb") as img_file:
        img_base64 = base64.b64encode(img_file.read()).decode('utf-8')

    data = {
        "imagen_base64": img_base64
    }
    r = requests.post(f"{BASE_URL}/api/imagenes", json=data)
    print("POST imagen:", r.status_code, r.json())

def test_get_imagen(file_id):
    r = requests.get(f"{BASE_URL}/api/imagenes/{file_id}")
    print("GET imagen:", r.status_code)
    with open("imagen_descargada.jpg", "wb") as f:
        f.write(r.content)

if __name__ == "__main__":
    test_post_sensores()
    test_get_sensores()
    test_post_imagen()
    test_get_imagen("68368a94c1ab0d6a5ba13992") # <- se obtiene al almacenar la imagen en la response arrojada en la petición de POST
