
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
import os
from dotenv import load_dotenv

load_dotenv()

# Usar la URL de .env
DATABASE_URL = os.getenv("TEST_DATABASE_URL", "postgresql://postgres:C%40rden4s2k24@localhost:5432/schedule_test_db")
engine = create_engine(DATABASE_URL)
Session = sessionmaker(bind=engine)
db = Session()

print(f"--- DIAGNÓSTICO DB: {DATABASE_URL.split('/')[-1]} ---")

try:
    print("\n--- ESTRUCTURA DE LA TABLA TEACHERS ---")
    res = db.execute(text("SELECT column_name, data_type FROM information_schema.columns WHERE table_name = 'teachers'")).fetchall()
    for row in res:
        print(f"Column: {row[0]} | Type: {row[1]}")

    print("\n--- DOCENTES (OCAMPO) ---")
    # Intentar sin status primero para no fallar
    res = db.execute(text("SELECT id, first_name, last_name, normalized_name, dni FROM teachers WHERE last_name LIKE '%OCAMPO%' OR first_name LIKE '%OCAMPO%'")).fetchall()
    for row in res:
        print(f"ID: {row[0]} | Name: {row[2]}, {row[1]} | Norm: {row[3]} | DNI: {row[4]}")

except Exception as e:
    print(f"ERROR: {e}")

db.close()
