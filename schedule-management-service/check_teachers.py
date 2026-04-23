from sqlalchemy import create_engine, text
import pandas as pd

engine = create_engine("postgresql://postgres:C%40rden4s2k24@localhost/schedule_db")

query = """
SELECT docente, fecha_clase, hora_inicio, hora_fin, receso, horas_dictadas, curso
FROM rpt_planilla
WHERE docente ILIKE '%JANAMPA%' OR docente ILIKE '%IZAGUIRRE%'
ORDER BY docente, fecha_clase, hora_inicio;
"""

with engine.connect() as conn:
    df = pd.read_sql(text(query), conn)
    print(df.to_string())
