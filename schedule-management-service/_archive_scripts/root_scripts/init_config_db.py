from app.database import engine, Base
import app.models

print("Asegurando creación de tablas...")
Base.metadata.create_all(bind=engine)
print("Tablas verificadas/creadas correctamente.")
