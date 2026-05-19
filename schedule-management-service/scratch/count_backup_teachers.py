import json

with open('backup_json/teachers_backup.json', 'r', encoding='utf-8') as f:
    teachers = json.load(f)

print(f"Total teachers in teachers_backup.json: {len(teachers)}")

active_count = 0
for t in teachers:
    if t.get('status') == 'ACTIVO' or t.get('status') is None:
        active_count += 1

print(f"ACTIVO in backup: {active_count}")
