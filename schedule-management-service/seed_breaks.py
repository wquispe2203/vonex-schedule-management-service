from app.database import SessionLocal
from app.models import BreakConfig
from datetime import time

def seed_breaks():
    db = SessionLocal()
    existing = db.query(BreakConfig).first()
    if not existing:
        print("Configurando Receso por defecto...")
        b = BreakConfig(start_time=time(8, 50), end_time=time(9, 10), description="Receso General")
        db.add(b)
        db.commit()
    else:
        print("Recesos ya configurados.")
    db.close()

if __name__ == '__main__':
    seed_breaks()
