from app.database import SessionLocal
from app.models import User

db = SessionLocal()
mock_user = db.query(User).filter_by(id=1).first()

if not mock_user:
    mock_user = User(
        id=1,
        username="admin",
        password_hash="password",
        role="ADMIN"
    )
    db.add(mock_user)
    db.commit()
    print("Usuario mock ID 1 insertado correctamente.")
else:
    print("Usuario mock ID 1 ya existe.")
db.close()
