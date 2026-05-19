from app.core.database import SessionLocal
from sqlalchemy import text

db = SessionLocal()
try:
    cards = db.execute(text("SELECT COUNT(*) FROM cards")).scalar()
    print(f"Cards count: {cards}")
finally:
    db.close()
