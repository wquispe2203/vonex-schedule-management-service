from app.core.database import SessionLocal
from app.models import RptPlanilla

db = SessionLocal()
try:
    res = db.query(RptPlanilla.curso).distinct().all()
    print("DISTINCT COURSES IN RPT:")
    for r in res[:20]:
        print(f" - {r[0]}")
finally:
    db.close()
