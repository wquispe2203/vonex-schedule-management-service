import os
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

load_dotenv()
engine = create_engine(os.getenv("DATABASE_URL"))

with engine.begin() as conn:
    print("Iniciando migración manual...")
    conn.execute(text("ALTER TABLE xml_uploads ADD COLUMN IF NOT EXISTS status VARCHAR(20) DEFAULT 'COMPLETED';"))
    conn.execute(text("ALTER TABLE xml_uploads ADD COLUMN IF NOT EXISTS total_records INTEGER DEFAULT 0;"))
    conn.execute(text("ALTER TABLE xml_uploads ADD COLUMN IF NOT EXISTS processed_records INTEGER DEFAULT 0;"))
    conn.execute(text("ALTER TABLE xml_uploads ADD COLUMN IF NOT EXISTS error_summary TEXT;"))
    print("Migración finalizada.")
