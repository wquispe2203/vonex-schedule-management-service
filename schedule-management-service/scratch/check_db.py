
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
import os
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/schedule_db")
engine = create_engine(DATABASE_URL)
Session = sessionmaker(bind=engine)
db = Session()

print("--- DIAGNÓSTICO DE DOCENTES (OCAMPO) ---")
res = db.execute(text("SELECT id, first_name, last_name, normalized_name, status, dni FROM teachers WHERE last_name LIKE '%OCAMPO%' OR first_name LIKE '%OCAMPO%'")).fetchall()

for row in res:
    print(f"ID: {row[0]} | Name: {row[2]}, {row[1]} | Norm: {row[3]} | Status: {row[4]} | DNI: {row[5]}")

print("\n--- CONTEO POR STATUS ---")
res = db.execute(text("SELECT status, count(*) FROM teachers GROUP BY status")).fetchall()
for row in res:
    print(f"Status: {row[0]} | Count: {row[1]}")

print("\n--- XML UPLOADS ---")
res = db.execute(text("SELECT id, filename, status, created_at FROM xml_uploads ORDER BY created_at DESC LIMIT 5")).fetchall()
for row in res:
    print(f"ID: {row[0]} | File: {row[1]} | Status: {row[2]} | Created: {row[3]}")

db.close()
