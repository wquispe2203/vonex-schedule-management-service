import sqlalchemy
from sqlalchemy import create_engine, text

def debug_data():
    engine = create_engine('postgresql://postgres:C@rden4s2k24@localhost:5432/schedule_test_db')
    with engine.connect() as conn:
        print("--- SESSIONS ---")
        res = conn.execute(text("SELECT session_date, start_time, end_time, lesson_id FROM schedule_sessions"))
        for row in res:
            print(row)
        
        print("\n--- RPT ---")
        res = conn.execute(text("SELECT docente, hora_inicio, horas_dictadas, receso FROM rpt_planilla"))
        for row in res:
            print(row)

if __name__ == "__main__":
    debug_data()
