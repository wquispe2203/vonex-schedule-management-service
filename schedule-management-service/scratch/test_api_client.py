import os
from jose import jwt
from dotenv import load_dotenv
load_dotenv()

from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

# Test dev-login
response = client.get("/api/users/dev-login")
print("Dev Login Status:", response.status_code)
if response.status_code == 200:
    token = response.json().get("access_token")
    print("Dev Login Token received.")
    
    # Let's decode the token to inspect the claims
    from app.core.security import SECRET_KEY, ALGORITHM
    payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    print("Decoded Claims:")
    print("  Subject:", payload.get("sub"))
    print("  Username:", payload.get("username"))
    print("  Roles:", payload.get("roles"))
    print("  Is Superadmin:", payload.get("is_superadmin"))
    print("  Permissions Count:", len(payload.get("permissions", [])))
    
    # Test GET /api/users/me with this token
    headers = {"Authorization": f"Bearer {token}"}
    r_me = client.get("/api/users/me", headers=headers)
    print("GET /me Status:", r_me.status_code)
    print("GET /me User:", r_me.json().get("data", {}).get("username"))
else:
    print("Dev Login Failed:", response.json())
