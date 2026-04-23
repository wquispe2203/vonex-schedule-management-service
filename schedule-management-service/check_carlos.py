from app.database import SessionLocal
from sqlalchemy import text

def check():
    db = SessionLocal()
    query = """
    SELECT docente, fecha_clase, hora_inicio, hora_fin, curso, sede, receso 
    FROM rpt_planilla 
    WHERE docente LIKE '%PALOMINO LESCANO%'
    ORDER BY fecha_clase, hora_inicio
    """
    rows = db.execute(text(query)).fetchall()
    for r in rows:
        if r[1].weekday() == 2: # Wednesday is 2
            print(r)
    db.close()

if __name__ == "__main__":
    check()
