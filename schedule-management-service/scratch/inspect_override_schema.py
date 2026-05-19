import os
import sys
from sqlalchemy import text

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.core.database import SessionLocal

db = SessionLocal()
res = db.execute(text("SELECT column_name, data_type FROM information_schema.columns WHERE table_name = 'teacher_name_overrides'")).mappings().all()
for r in res:
    print(dict(r))
db.close()
