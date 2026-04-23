import psycopg
import json
import os
from app.database import SQLALCHEMY_DATABASE_URL

def backup_domain_data():
    conn_str = SQLALCHEMY_DATABASE_URL.replace("postgresql://", "postgresql://")
    tables = [
        "teachers", "users", "lessons", "observations", 
        "schedule_sessions", "classes", "subjects", "rpt_planilla"
    ]
    
    backup_dir = "d:/Desktop/MOD HOR/schedule-management-service/backup_json"
    os.makedirs(backup_dir, exist_ok=True)
    
    try:
        with psycopg.connect(conn_str) as conn:
            with conn.cursor() as cur:
                print(f"--- INICIANDO RESPALDO DE SEGURIDAD (FASE 1) ---")
                for table in tables:
                    print(f"Respaldando tabla: {table}")
                    cur.execute(f"SELECT * FROM {table}")
                    columns = [desc[0] for desc in cur.description]
                    data = [dict(zip(columns, row)) for row in cur.fetchall()]
                    
                    # Guardar como JSON serializado
                    def json_serial(obj):
                        from datetime import date, datetime, time
                        from uuid import UUID
                        from decimal import Decimal
                        if isinstance(obj, (datetime, date, time)):
                            return obj.isoformat()
                        if isinstance(obj, UUID):
                            return str(obj)
                        if isinstance(obj, Decimal):
                            return float(obj)
                        raise TypeError (f"Type %s not serializable" % type(obj))

                    filepath = os.path.join(backup_dir, f"{table}_backup.json")
                    with open(filepath, "w", encoding="utf-8") as f:
                        json.dump(data, f, default=json_serial, indent=2, ensure_ascii=False)
                    print(f"  OK: {len(data)} registros guardados en {filepath}")

    except Exception as e:
        print(f"ERROR EN RESPALDO: {e}")
        raise

if __name__ == "__main__":
    backup_domain_data()
