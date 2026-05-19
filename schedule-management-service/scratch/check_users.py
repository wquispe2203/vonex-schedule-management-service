import os
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

load_dotenv()
db_url = os.getenv("DATABASE_URL")
engine = create_engine(db_url)

with engine.connect() as conn:
    res = conn.execute(text("SELECT username, password_hash FROM users"))
    for row in res:
        print(f"USER: {row[0]} | HASH: {row[1]}")
