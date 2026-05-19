import os
from dotenv import load_dotenv
load_dotenv()
from app.core.database import SessionLocal
from app.modules.docentes.repository import fetch_all_teachers_paginated
from app.modules.horarios.repository import fetch_all_teachers

db = SessionLocal()

print("== DOCENTES PAGINATED ==")
res = fetch_all_teachers_paginated(db, filter_mode="all", status_filter="all")
print("Total:", res['total'], "Items count:", len(res['items']))
if res['items']:
    print("First item:", res['items'][0].first_name, res['items'][0].last_name)

print("\n== DOCENTES HORARIOS ==")
res2 = fetch_all_teachers(db)
print("Total in horarios:", len(res2))

db.close()
