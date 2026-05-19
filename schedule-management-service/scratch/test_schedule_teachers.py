import os
from dotenv import load_dotenv
load_dotenv()

from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

response = client.post("/api/users/login", data={"username": "admin@vonex.edu.pe", "password": "Admin123*"})
token = response.json().get("access_token")

print("\n--- TEST /api/schedule/classes ---")
response = client.get("/api/schedule/classes", headers={"Authorization": f"Bearer {token}"})
print(f"SCHEDULE CLASSES response keys: {response.json().keys()}")

if "success" in response.json():
    print(f"success: {response.json().get('success')}")

data = response.json().get("data", {})
print(f"data type: {type(data)}")

if isinstance(data, dict):
    print(f"data keys: {data.keys()}")
    if "data" in data:
        print(f"data.data length: {len(data['data'])}")
elif isinstance(data, list):
    print(f"data length: {len(data)}")
