import os
import sys
import zipfile
import json
import logging
import datetime
from pathlib import Path

# --- CONFIGURATION ---
BASE_DIR = Path(__file__).resolve().parent.parent.parent
SNAPSHOT_DIR = BASE_DIR / "ops" / "snapshots"
RESTORE_TMP = BASE_DIR / "ops" / "restore" / "xml_tmp"
LOG_DIR = BASE_DIR / "ops" / "logs"
LOG_FILE = LOG_DIR / "restore_xml.log"

# Logging Setup
LOG_DIR.mkdir(parents=True, exist_ok=True)
RESTORE_TMP.mkdir(parents=True, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format='%(message)s',
    handlers=[
        logging.FileHandler(LOG_FILE),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger("restore_xml")

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

def restore_snapshot(snapshot_file, dry_run=True):
    snapshot_path = SNAPSHOT_DIR / snapshot_file
    
    log_structured("INFO", "[RESTORE XML START]", f"Initiating XML restore for {snapshot_file} (DRY_RUN={dry_run})")

    if not snapshot_path.exists():
        log_structured("ERROR", "[RESTORE FAILED]", f"Snapshot file not found: {snapshot_file}")
        return

    # 1. Validation
    log_structured("INFO", "[RESTORE PROGRESS]", "Validating ZIP integrity...")
    try:
        with zipfile.ZipFile(snapshot_path, 'r') as zipf:
            corrupt = zipf.testzip()
            if corrupt:
                log_structured("ERROR", "[RESTORE FAILED]", f"ZIP is corrupt. First bad file: {corrupt}")
                return
            
            if dry_run:
                log_structured("INFO", "[RESTORE SUCCESS]", "Dry-run: Snapshot is valid and readable.")
                return

            # 2. Extract to temp
            log_structured("INFO", "[RESTORE PROGRESS]", f"Extracting to {RESTORE_TMP}...")
            zipf.extractall(RESTORE_TMP)
            
            log_structured("INFO", "[RESTORE SUCCESS]", f"XML Snapshot extracted to {RESTORE_TMP}. Ready for manual verification.")

    except Exception as e:
        log_structured("ERROR", "[RESTORE FAILED]", f"Unexpected error: {str(e)}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python restore_xml.py <snapshot_file.zip> [--full]")
        sys.exit(1)
    
    s_file = sys.argv[1]
    is_full = "--full" in sys.argv
    restore_snapshot(s_file, dry_run=not is_full)
