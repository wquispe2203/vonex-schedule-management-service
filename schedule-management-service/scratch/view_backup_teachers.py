import json

def run():
    with open('backup_json/teachers_backup.json', 'r', encoding='utf-8') as f:
        teachers = json.load(f)
    for t in teachers:
        if t.get('dni') is None:
            print({
                "id": t.get('id'),
                "first_name": t.get('first_name'),
                "last_name": t.get('last_name'),
                "status": t.get('status'),
                "is_active": t.get('is_active'),
                "is_assigned": t.get('is_assigned'),
                "source": t.get('source')
            })

if __name__ == "__main__":
    run()
