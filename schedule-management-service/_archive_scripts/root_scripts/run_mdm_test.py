import requests
import json
import uuid
from app.database import SessionLocal
from app.models import User
from app.core.security import create_access_token

# 1. Create a JWT Token Directly
db = SessionLocal()
user = db.query(User).filter_by(username="admin@vonex.edu.pe").first()
if not user:
    print("User not found")
    exit(1)

access_token_expires = 300
token = create_access_token(
    subject=str(user.id)
)

headers = {"Authorization": f"Bearer {token}", "X-Request-ID": f"mdm-test-{uuid.uuid4()}"}

# 2. Upload XML
upload_url = "http://127.0.0.1:8000/api/schedule/upload"
with open("test_mdm.xml", "rb") as f:
    files = {"file": ("test_mdm.xml", f, "text/xml")}
    data = {
        "start_date": "2026-05-01",
        "end_date": "2026-05-07",
        "force_overwrite": "true"
    }
    print("Uploading XML to test MDM matching...")
    res = requests.post(upload_url, headers=headers, files=files, data=data)
    print("Status Code:", res.status_code)
    print("Response JSON:", json.dumps(res.json(), indent=2))
