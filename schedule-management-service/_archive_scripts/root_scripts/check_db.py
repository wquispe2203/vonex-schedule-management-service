from app.database import engine
from sqlalchemy import text
c = engine.connect()
rows = c.execute(text("SELECT docente, fecha_clase, hora_inicio, hora_fin, curso, horas_dictadas, ciclo, sede, receso FROM rpt_planilla WHERE docente = 'PEDRO GLICERIO PEDROZO GARGATE' AND curso = 'BIOLOGIA' AND fecha_clase = '2026-03-02' ORDER BY hora_inicio")).fetchall()
for r in rows:
    print(r)
c.close()
