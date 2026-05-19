import os
import requests
import json

# Fetching token
response = requests.post("http://127.0.0.1:8000/api/users/login", data={"username": "admin@vonex.edu.pe", "password": "Admin123*"})
token = response.json().get("access_token")

headers = {"Authorization": f"Bearer {token}"}
response = requests.get("http://127.0.0.1:8000/api/docentes?status=all", headers=headers)
print("DOCENTES:", response.json())

response = requests.get("http://127.0.0.1:8000/api/schedule/xml-uploads?page=1&limit=20", headers=headers)
print("XML UPLOADS:", response.json())
