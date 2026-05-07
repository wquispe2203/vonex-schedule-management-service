import logging
import json
from typing import List, Dict, Any, Type
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from datetime import datetime, timezone

logger = logging.getLogger("app.bulk_service")

class BulkOperationResult:
    def __init__(self, model_name: str):
        self.model_name = model_name
        self.total_received = 0
        self.valid_count = 0
        self.error_count = 0
        self.errors = []
        self.start_time = datetime.now(timezone.utc)
        self.end_time = None

    def add_error(self, message: str, data: Dict = None):
        self.error_count += 1
        self.errors.append({"message": message, "data": data})

    def finish(self):
        self.end_time = datetime.now(timezone.utc)
        duration = (self.end_time - self.start_time).total_seconds()
        
        summary = {
            "model": self.model_name,
            "total": self.total_received,
            "valid": self.valid_count,
            "errors": self.error_count,
            "duration_sec": duration
        }
        logger.info(f"Bulk Operation Summary: {json.dumps(summary)}")
        return summary

class BulkValidator:
    @staticmethod
    def validate_mappings(model: Type, mappings: List[Dict[str, Any]], required_fields: List[str]) -> List[Dict[str, Any]]:
        """
        Validates a list of mappings before bulk insertion.
        Returns only valid mappings.
        """
        valid_mappings = []
        for mapping in mappings:
            # 1. Check required fields
            missing = [f for f in required_fields if f not in mapping or mapping[f] is None]
            if missing:
                logger.warning(f"Validation Error: Model {model.__name__} missing fields {missing}")
                continue
            
            # 2. Check for empty strings in critical fields
            if any(isinstance(mapping.get(f), str) and not mapping.get(f).strip() for f in required_fields):
                logger.warning(f"Validation Error: Model {model.__name__} has empty required strings")
                continue
                
            valid_mappings.append(mapping)
            
        return valid_mappings

from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy import text
import hashlib
import time

class PostgresAdvisoryLock:
    def __init__(self, db: Session, lock_id: int):
        self.db = db
        self.lock_id = lock_id

    def __enter__(self):
        # Transaction-level advisory lock
        self.db.execute(text(f"SELECT pg_advisory_xact_lock({self.lock_id})"))
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        # Lock is automatically released at the end of the transaction
        pass

def safe_bulk_insert(db: Session, model: Type, mappings: List[Dict[str, Any]], batch_size: int = 1000, use_upsert: bool = False, conflict_cols: List[str] = None):
    """
    Performs bulk insertion in batches with transaction control and optional UPSERT.
    """
    result = BulkOperationResult(model.__name__)
    result.total_received = len(mappings)
    
    if not mappings:
        return result.finish()

    try:
        start_time = time.time()
        # Process in batches
        for i in range(0, len(mappings), batch_size):
            batch = mappings[i:i + batch_size]
            
            if use_upsert and conflict_cols:
                stmt = pg_insert(model).values(batch)
                update_dict = {c.name: c for c in stmt.excluded if c.name not in conflict_cols and c.name != 'id'}
                stmt = stmt.on_conflict_do_update(
                    index_elements=conflict_cols,
                    set_=update_dict
                )
                db.execute(stmt)
            else:
                db.bulk_insert_mappings(model, batch)
            
            db.flush() # Verify integrity per batch
            result.valid_count += len(batch)
            
        db.commit()
        duration = time.time() - start_time
        throughput = result.valid_count / duration if duration > 0 else 0
        logger.info(f"Bulk Operation: {model.__name__} | Throughput: {throughput:.2f} rec/sec")
        
    except IntegrityError as e:
        db.rollback()
        error_msg = f"Integrity Error during bulk insert for {model.__name__}: {str(e.orig)}"
        logger.error(error_msg)
        result.add_error(error_msg)
        raise e
    except Exception as e:
        db.rollback()
        logger.error(f"Unexpected error in bulk insert for {model.__name__}: {str(e)}")
        result.add_error(str(e))
        raise e
        
    return result.finish()

def get_file_hash(file_path: str) -> str:
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()
