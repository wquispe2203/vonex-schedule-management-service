# Rollback Cleanup Plan (Draft)

**Status**: PENDING USER APPROVAL
**Target Database**: `schedule_db` (PostgreSQL)

This rollback plan details the immediate recovery steps to revert the academic reset to the exact pre-cleanup database state in case of any anomaly.

## 1. Automated Snapshot (Restore Point)
Prior to deleting any row, the cleanup executor WILL run a full logical database dump:
* **Tool**: `pg_dump`
* **Output File**: `d:/Desktop/MOD HOR/schedule-management-service/backup_json/pre_cleanup_backup.sql`
* **Command**:
  ```powershell
  pg_dump --host=localhost --port=5432 --username=postgres --dbname=schedule_db --clean --if-exists --file="d:/Desktop/MOD HOR/schedule-management-service/backup_json/pre_cleanup_backup.sql"
  ```

## 2. Manual/Emergency Rollback Procedure
If any validation fails or if you decide to revert the cleanup, follow these steps:

### Step 1: Detach active server connections
Stop the backend API server if running:
* Terminate Uvicorn process.

### Step 2: Restore from SQL Backup
Run the recovery command using PostgreSQL client `psql`:
```powershell
psql --host=localhost --port=5432 --username=postgres --dbname=schedule_db --file="d:/Desktop/MOD HOR/schedule-management-service/backup_json/pre_cleanup_backup.sql"
```
* The `--clean` flag in our backup ensures that all restored tables are automatically dropped and recreated exactly as they were, eliminating any data mismatch or orphan reference.

### Step 3: Verify Restoration State
Execute the post-restoration audit script to confirm:
- Total sessions: **8,422**
- Total RPT lines: **4,862**
- Total teachers: **371**
- Fixture upload `complex_mdm_test_v2.xml` is present.
