from app.database import engine, Base
from app.models import RptPlanilla, RptPlanillaLog

def create_new_tables():
    print("Creando nuevas tablas en la base de datos...")
    # Esto creará SOLO las tablas que no existen y están definidas en Base
    RptPlanilla.__table__.create(bind=engine, checkfirst=True)
    RptPlanillaLog.__table__.create(bind=engine, checkfirst=True)
    print("Tablas 'rpt_planilla' y 'rpt_planilla_logs' creadas exitosamente.")

if __name__ == "__main__":
    create_new_tables()
