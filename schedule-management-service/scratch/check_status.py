
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
import os
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("TEST_DATABASE_URL", "postgresql://postgres:C%40rden4s2k24@localhost:5432/schedule_test_db")
engine = create_engine(DATABASE_URL)
Session = sessionmaker(bind=engine)
db = Session()

print(f"--- DIAGNÓSTICO STATUS ---")

res = db.execute(text("SELECT id, last_name, first_name, status, dni FROM teachers WHERE last_name LIKE '%OCAMPO%'")).fetchall()
for row in res:
    print(f"ID: {row[0]} | Name: {row[1]}, {row[2]} | Status: {row[3]} | DNI: {row[4]}")

db.close()
