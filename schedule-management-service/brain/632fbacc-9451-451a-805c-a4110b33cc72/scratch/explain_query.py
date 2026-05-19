from app.core.database import SessionLocal
from sqlalchemy import text

db = SessionLocal()
sql = "EXPLAIN ANALYZE SELECT * FROM rpt_planilla WHERE fecha_clase = '2026-03-02'"
res = db.execute(text(sql))
for row in res:
    print(row[0])
