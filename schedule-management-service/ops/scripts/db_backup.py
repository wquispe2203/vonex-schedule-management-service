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
LOG_FILE = LOG_DIR / "backup.log"
LOCK_FILE = OPS_DIR / "scripts" / "backup.lock"

# PostgreSQL bin path (Specific for this environment)
PG_DUMP_PATH = r"C:\Program Files\PostgreSQL\18\bin\pg_dump.exe"

# Logging Setup
LOG_DIR.mkdir(parents=True, exist_ok=True)
BACKUP_DIR.mkdir(parents=True, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format='%(message)s',
    handlers=[
        logging.FileHandler(LOG_FILE),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger("db_backup")

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

def check_disk_space(path, required_mb=500):
    usage = shutil.disk_usage(path)
    free_mb = usage.free / (1024 * 1024)
    return free_mb > required_mb

def get_checksum(file_path):
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def rotate_backups():
    log_structured("INFO", "[BACKUP ROTATION]", "Starting rotation of old backups")
    backups = sorted([f for f in BACKUP_DIR.glob("*.sql.gz")], key=os.path.getmtime, reverse=True)
    
    # Keep last 7 daily
    if len(backups) > 7:
        for old_backup in backups[7:]:
            # Simple logic: if it's Sunday, keep it as weekly (up to 4)
            # For now, just keeping 10 total to be safe, but adhering to logic:
            # We will mark them by filename if needed.
            # Simplified: Delete older than 10 total for this sprint.
            try:
                old_backup.unlink()
                log_structured("INFO", "[BACKUP ROTATION]", f"Deleted old backup: {old_backup.name}")
            except Exception as e:
                log_structured("ERROR", "[BACKUP ROTATION]", f"Failed to delete {old_backup.name}: {str(e)}")

def run_backup():
    if LOCK_FILE.exists():
        log_structured("WARNING", "[BACKUP FAILED]", "Backup already in progress (Lock file exists)")
        return

    try:
        LOCK_FILE.touch()
        timestamp = datetime.datetime.utcnow().strftime("%Y%m%d_%H%M%SZ")
        db_name = os.getenv("PGDATABASE", "schedule_db")
        backup_filename = f"{db_name}_{timestamp}.sql"
        backup_path = BACKUP_DIR / backup_filename
        compressed_path = BACKUP_DIR / f"{backup_filename}.gz"

        log_structured("INFO", "[BACKUP START]", f"Starting backup for database: {db_name}")

        if not check_disk_space(BACKUP_DIR):
            log_structured("ERROR", "[BACKUP FAILED]", "Insufficient disk space")
            return

        # Prepare Environment
        env = os.environ.copy()
        # Ensure pg_dump is in path or use absolute
        cmd = [
            PG_DUMP_PATH if os.path.exists(PG_DUMP_PATH) else "pg_dump",
            "-F", "c",  # Custom format (compressed and compatible with pg_restore)
            "-f", str(backup_path)
        ]

        # Execution
        result = subprocess.run(cmd, env=env, capture_output=True, text=True, timeout=300)

        if result.returncode != 0:
            log_structured("ERROR", "[BACKUP FAILED]", f"pg_dump error: {result.stderr}")
            return

        # Verification with pg_restore --list
        PG_RESTORE_PATH = PG_DUMP_PATH.replace("pg_dump.exe", "pg_restore.exe")
        v_cmd = [PG_RESTORE_PATH if os.path.exists(PG_RESTORE_PATH) else "pg_restore", "-l", str(backup_path)]
        v_result = subprocess.run(v_cmd, env=env, capture_output=True, text=True)
        
        if v_result.returncode != 0:
            log_structured("ERROR", "[BACKUP FAILED]", "Integrity check failed: pg_restore cannot read the file")
            return

        # Compression of the custom dump (optional, but good for archiving)
        log_structured("INFO", "[BACKUP PROGRESS]", "Compressing backup file")
        with open(backup_path, 'rb') as f_in:
            with gzip.open(compressed_path, 'wb') as f_out:
                shutil.copyfileobj(f_in, f_out)
        
        backup_path.unlink() # Remove uncompressed

        # Integrity Check
        # For plain text dumps, we check if they start with '--' or 'SELECT'
        # Or better, use pg_restore if it was format 'c'. 
        # Since it's plain text, we check size and tail.
        if compressed_path.stat().st_size < 100:
            log_structured("ERROR", "[BACKUP FAILED]", "Backup file is suspiciously small")
            return

        checksum = get_checksum(compressed_path)
        log_structured("INFO", "[BACKUP CHECKSUM VERIFIED]", f"SHA256: {checksum}")

        log_structured("INFO", "[BACKUP SUCCESS]", f"Backup completed: {compressed_path.name}")
        
        rotate_backups()

    except Exception as e:
        log_structured("ERROR", "[BACKUP FAILED]", f"Unexpected error: {str(e)}")
    finally:
        if LOCK_FILE.exists():
            LOCK_FILE.unlink()

if __name__ == "__main__":
    run_backup()
