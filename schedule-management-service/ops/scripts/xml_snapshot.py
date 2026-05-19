import os
import zipfile
import hashlib
import datetime
import json
import logging
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

# --- CONFIGURATION ---
BASE_DIR = Path(__file__).resolve().parent.parent.parent
STORAGE_DIR = BASE_DIR / "storage" / "xml_uploads"
SNAPSHOT_DIR = BASE_DIR / "ops" / "snapshots"
LOG_DIR = BASE_DIR / "ops" / "logs"
LOG_FILE = LOG_DIR / "xml_snapshot.log"

# Logging Setup
LOG_DIR.mkdir(parents=True, exist_ok=True)
SNAPSHOT_DIR.mkdir(parents=True, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format='%(message)s',
    handlers=[
        logging.FileHandler(LOG_FILE),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger("xml_snapshot")

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

def validate_xml(file_path):
    try:
        ET.parse(file_path)
        return True, None
    except ET.ParseError as e:
        return False, str(e)
    except Exception as e:
        return False, str(e)

def get_checksum(file_path):
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def create_snapshot():
    timestamp = datetime.datetime.utcnow().strftime("%Y%m%d_%H%M%SZ")
    snapshot_filename = f"xml_storage_snapshot_{timestamp}.zip"
    snapshot_path = SNAPSHOT_DIR / snapshot_filename
    manifest_filename = f"manifest_{timestamp}.json"
    manifest_path = SNAPSHOT_DIR / manifest_filename

    log_structured("INFO", "[XML SNAPSHOT START]", f"Starting XML storage snapshot: {snapshot_filename}")

    if not STORAGE_DIR.exists():
        log_structured("ERROR", "[XML SNAPSHOT FAILED]", f"Storage directory not found: {STORAGE_DIR}")
        return

    manifest = {
        "snapshot_time": timestamp,
        "files": [],
        "errors": []
    }

    try:
        with zipfile.ZipFile(snapshot_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for root, dirs, files in os.walk(STORAGE_DIR):
                for file in files:
                    if file.endswith(".xml"):
                        file_path = Path(root) / file
                        rel_path = file_path.relative_to(STORAGE_DIR)
                        
                        # Validation
                        is_valid, error = validate_xml(file_path)
                        checksum = get_checksum(file_path)
                        
                        file_meta = {
                            "path": str(rel_path),
                            "checksum": checksum,
                            "valid": is_valid
                        }
                        
                        if is_valid:
                            zipf.write(file_path, rel_path)
                            manifest["files"].append(file_meta)
                            log_structured("DEBUG", "[XML VALIDATION PASSED]", f"File: {file}")
                        else:
                            file_meta["error"] = error
                            manifest["errors"].append(file_meta)
                            log_structured("WARNING", "[XML VALIDATION FAILED]", f"File: {file} - Error: {error}")

        # Save Manifest
        with open(manifest_path, 'w') as f:
            json.dump(manifest, f, indent=4)

        log_structured("INFO", "[XML SNAPSHOT COMPLETE]", f"Snapshot saved to {snapshot_filename}. Files: {len(manifest['files'])}, Errors: {len(manifest['errors'])}")

    except Exception as e:
        log_structured("ERROR", "[XML SNAPSHOT FAILED]", f"Unexpected error: {str(e)}")

if __name__ == "__main__":
    create_snapshot()
