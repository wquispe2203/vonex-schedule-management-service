from app.core.database import SessionLocal
from app.models.user import User
from app.core.security import get_password_hash

db = SessionLocal()
try:
    user = db.query(User).filter(User.username == 'admin@vonex.edu.pe').first()
    if user:
        user.password_hash = get_password_hash('123456')
        db.commit()
        print('[AUTH] admin@vonex.edu.pe password reset to 123456')
    else:
        print('[AUTH ERROR] admin@vonex.edu.pe not found')
finally:
    db.close()
