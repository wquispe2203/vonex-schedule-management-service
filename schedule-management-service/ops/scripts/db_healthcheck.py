import sys
import os
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

# Importar configuración de la app para obtener el DB_URL
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))
from app.core.config import settings

def run_healthcheck():
    print("--- [DB PERFORMANCE AUDIT] Starting Safety Scan ---")
    
    # Usamos la base de datos configurada (o la de test si TESTING=True)
    engine = create_engine(str(settings.database_url))
    Session = sessionmaker(bind=engine)
    session = Session()

    try:
        # 1. DETECCIÓN DE SEQUENTIAL SCANS (Índices Faltantes)
        print("\n[AUDIT] Checking for Sequential Scans (Possible missing indexes):")
        query_seq_scans = text("""
            SELECT relname AS table_name, 
                   seq_scan, 
                   seq_tup_read, 
                   idx_scan, 
                   idx_tup_fetch
            FROM pg_stat_user_tables
            WHERE seq_scan > 100
            ORDER BY seq_tup_read DESC
            LIMIT 5;
        """)
        results = session.execute(query_seq_scans).fetchall()
        if not results:
            print("  - PASS: No significant sequential scans detected.")
        for row in results:
            print(f"  - WARNING: Table '{row.table_name}' has {row.seq_scan} seq_scans. Reads: {row.seq_tup_read}")

        # 2. DETECCIÓN DE LOCKS ACTIVOS
        print("\n[AUDIT] Checking for active Locks:")
        query_locks = text("""
            SELECT pid, 
                   now() - query_start AS duration, 
                   query, 
                   state
            FROM pg_stat_activity
            WHERE wait_event_type IS NOT NULL
            AND state = 'active';
        """)
        results = session.execute(query_locks).fetchall()
        if not results:
            print("  - PASS: No active locks detected.")
        for row in results:
            print(f"  - CAUTION: PID {row.pid} locked for {row.duration}. Query: {row.query[:50]}...")

        # 3. TAMAÑO DE TABLAS CRÍTICAS
        print("\n[AUDIT] Table Size Audit:")
        query_size = text("""
            SELECT relname AS table_name,
                   pg_size_pretty(pg_total_relation_size(relid)) AS total_size
            FROM pg_catalog.pg_statio_user_tables
            ORDER BY pg_total_relation_size(relid) DESC;
        """)
        results = session.execute(query_size).fetchall()
        for row in results:
            print(f"  - {row.table_name:20} | Size: {row.total_size}")

        print("\n[DB_HEALTH_REPORT] Audit finished successfully.")
        
    except Exception as e:
        print(f"[ERROR] Healthcheck failed: {str(e)}")
        sys.exit(1)
    finally:
        session.close()

if __name__ == "__main__":
    run_healthcheck()
