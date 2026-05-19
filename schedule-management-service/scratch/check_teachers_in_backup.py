import json
from app.core.database import SessionLocal
from app.models import Teacher

with open('backup_json/teachers_backup.json', 'r', encoding='utf-8') as f:
    backup_teachers = json.load(f)

backup_ids = {t['id'] for t in backup_teachers if 'id' in t}
backup_source_ids = {t.get('source_id') for t in backup_teachers if t.get('source_id')}

db = SessionLocal()
try:
    db_teachers = db.query(Teacher).all()
    print(f"Auditing {len(db_teachers)} database teachers against backup:")
    for t in db_teachers:
        in_backup_by_id = str(t.id) in backup_ids
        in_backup_by_source_id = t.source_id in backup_source_ids
        print(f"Teacher: {t.last_name}, {t.first_name}")
        print(f"  - DB ID: {t.id} (In backup by ID: {in_backup_by_id})")
        print(f"  - Source ID: {t.source_id} (In backup by source_id: {in_backup_by_source_id})")
        print(f"  - Source: {t.source}")
        print(f"  - Status: {t.status}")
finally:
    db.close()
