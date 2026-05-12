from app.core.database import SessionLocal
from app.models import User
from app.core.security import get_password_hash
db = SessionLocal()
user = db.query(User).filter(User.username == 'admin@vonex.edu.pe').first()
if user:
    user.password_hash = get_password_hash('admin123')
    db.commit()
    print("Correctly set user.password_hash to admin123")
else:
    print("User not found")
db.close()
