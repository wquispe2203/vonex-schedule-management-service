import requests
import os

url = "http://localhost:8000/api/schedule/upload"
xml_path = "storage/xml_uploads/asctt2012.xml"

if not os.path.exists(xml_path):
    print(f"Error: {xml_path} no existe.")
    exit(1)

files = {'file': open(xml_path, 'rb')}
data = {
    'start_date': '2026-03-01',
    'end_date': '2026-06-30',
    'overwrite': 'true'
}

print(f"Enviando {xml_path} a {url}...")
try:
    # Aumentamos el timeout a 120 segundos por si acaso
    response = requests.post(url, files=files, data=data, timeout=120)
    print("Status Code:", response.status_code)
    print("JSON:", response.json())
except Exception as e:
    print("Error durante la petición:", str(e))
