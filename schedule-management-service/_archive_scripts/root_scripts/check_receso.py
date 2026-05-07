from app.database import SessionLocal
from sqlalchemy import text
import sys

def check():
    db = SessionLocal()
    query = """
    SELECT docente, fecha_clase, hora_inicio, hora_fin, curso, ciclo, sede, receso 
    FROM rpt_planilla 
    WHERE docente IN ('CARLOS DANIEL PALOMINO LESCANO', 'VICTOR ANGEL CARDENAS HUAYTAYA', 'MARIA MERCEDES MAURICIO ALMEIDA') 
    ORDER BY docente, fecha_clase, hora_inicio
    """
    rows = db.execute(text(query)).fetchall()
    for r in rows:
        print(r)
    db.close()

if __name__ == "__main__":
    check()
