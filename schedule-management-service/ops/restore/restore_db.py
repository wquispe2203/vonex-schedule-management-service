import os
import sys
import subprocess
import datetime
import gzip
import shutil
import hashlib
import logging
import json
from pathlib import Path

# --- CONFIGURATION ---
BASE_DIR = Path(__file__).resolve().parent.parent.parent
OPS_DIR = BASE_DIR / "ops"
BACKUP_DIR = OPS_DIR / "backups"
LOG_DIR = OPS_DIR / "logs"
LOG_FILE = LOG_DIR / "restore.log"

# PostgreSQL bin paths
PG_BIN_DIR = r"C:\Program Files\PostgreSQL\18\bin"
PG_RESTORE_PATH = os.path.join(PG_BIN_DIR, "pg_restore.exe")
PSQL_PATH = os.path.join(PG_BIN_DIR, "psql.exe")

# Logging Setup
LOG_DIR.mkdir(parents=True, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format='%(message)s',
    handlers=[
        logging.FileHandler(LOG_FILE),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger("db_restore")

def log_structured(level, action, message, extra=None):
    log_data = {
        "timestamp": datetime.datetime.utcnow().isoformat() + "Z",
        "level": level,
        "action": action,
        "message": message
    }
    if extra:
        log_data.update(extra)
    logger.info(json.dumps(log_data))

def get_checksum(file_path):
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def run_cmd(cmd, env, action):
    result = subprocess.run(cmd, env=env, capture_output=True, text=True)
    if result.returncode != 0:
        log_structured("ERROR", f"{action} FAILED", result.stderr)
        return False, result.stderr
    return True, result.stdout

def restore_backup(backup_file, dry_run=True, target_db="schedule_restore_tmp"):
    backup_path = BACKUP_DIR / backup_file
    temp_sql = BACKUP_DIR / "temp_restore.sql"
    
    log_structured("INFO", "[RESTORE START]", f"Initiating restore for {backup_file} to {target_db} (DRY_RUN={dry_run})")

    if not backup_path.exists():
        log_structured("ERROR", "[RESTORE FAILED]", f"Backup file not found: {backup_file}")
        return

    # 1. Decompress
    log_structured("INFO", "[RESTORE PROGRESS]", "Decompressing backup...")
    try:
        with gzip.open(backup_path, 'rb') as f_in:
            with open(temp_sql, 'wb') as f_out:
                shutil.copyfileobj(f_in, f_out)
    except Exception as e:
        log_structured("ERROR", "[RESTORE FAILED]", f"Decompression error: {str(e)}")
        return

    # 2. Validation
    log_structured("INFO", "[RESTORE PROGRESS]", "Validating backup integrity...")
    env = os.environ.copy()
    v_cmd = [PG_RESTORE_PATH if os.path.exists(PG_RESTORE_PATH) else "pg_restore", "-l", str(temp_sql)]
    success, output = run_cmd(v_cmd, env, "[RESTORE VALIDATION]")
    if not success:
        temp_sql.unlink()
        return

    log_structured("INFO", "[RESTORE VALIDATED]", "Backup metadata is readable")

    if dry_run:
        log_structured("INFO", "[RESTORE SUCCESS]", "Dry-run completed successfully. No changes applied.")
        temp_sql.unlink()
        return

    # 3. Create Temp DB
    log_structured("INFO", "[RESTORE PROGRESS]", f"Preparing target database: {target_db}")
    drop_cmd = [PSQL_PATH if os.path.exists(PSQL_PATH) else "psql", "-c", f"DROP DATABASE IF EXISTS {target_db};", "postgres"]
    create_cmd = [PSQL_PATH if os.path.exists(PSQL_PATH) else "psql", "-c", f"CREATE DATABASE {target_db};", "postgres"]
    
    run_cmd(drop_cmd, env, "[DB PREP]")
    success, err = run_cmd(create_cmd, env, "[DB PREP]")
    if not success:
        temp_sql.unlink()
        return

    # 4. Restore
    log_structured("INFO", "[RESTORE PROGRESS]", "Executing pg_restore...")
    restore_cmd = [
        PG_RESTORE_PATH if os.path.exists(PG_RESTORE_PATH) else "pg_restore",
        "-d", target_db,
        # "-c", # Removed -c for fresh DBs to avoid 'not exist' errors
        str(temp_sql)
    ]
    
    # pg_restore often returns non-zero for minor warnings. 
    # We check if the command finished and then verify data.
    result = subprocess.run(restore_cmd, env=env, capture_output=True, text=True)
    
    if result.returncode != 0:
        # Check if errors are critical or just warnings about existing/non-existing objects
        if "ERROR" in result.stderr and "already exists" not in result.stderr:
             log_structured("ERROR", "[RESTORE] FAILED", result.stderr)
             log_structured("ERROR", "[ROLLBACK ACTIVATED]", "Restoration failed. Dropping corrupt temp database.")
             run_cmd(drop_cmd, env, "[ROLLBACK]")
             temp_sql.unlink()
             return
        else:
             log_structured("WARNING", "[RESTORE PROGRESS]", "pg_restore finished with minor warnings (ignoring).")

    # 5. Verification
    log_structured("INFO", "[RESTORE PROGRESS]", "Verifying restored data...")
    count_cmd = [PSQL_PATH if os.path.exists(PSQL_PATH) else "psql", "-d", target_db, "-c", "SELECT count(*) FROM rpt_planilla;", "-t"]
    success, count = run_cmd(count_cmd, env, "[VERIFICATION]")
    
    if success:
        log_structured("INFO", "[RESTORE SUCCESS]", f"Restoration verified. Records in rpt_planilla: {count.strip()}")
    else:
        log_structured("ERROR", "[RESTORE FAILED]", "Verification query failed.")

    temp_sql.unlink()

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python restore_db.py <backup_file.gz> [--full]")
        sys.exit(1)
    
    b_file = sys.argv[1]
    is_full = "--full" in sys.argv
    restore_backup(b_file, dry_run=not is_full)
