from app.database import engine
from app.models import Base

print("Iniciando el borrado nuclear de la base de datos PostgreSQL...")

# 1. Destruye absolutamente todas las tablas existentes
Base.metadata.drop_all(bind=engine)
print("✅ Todas las tablas han sido eliminadas.")

# 2. Vuelve a crear las tablas desde cero, totalmente limpias
Base.metadata.create_all(bind=engine)
print("✅ Nuevas tablas creadas con éxito. La base de datos está inmaculada.")