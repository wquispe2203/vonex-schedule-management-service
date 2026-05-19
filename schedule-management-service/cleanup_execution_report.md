# Cleanup Execution Report (Draft)

**Status**: PENDING USER APPROVAL
**Target Database**: `schedule_db` (PostgreSQL)

This document details the exact surgical cleanup query blocks that will be executed upon approval to remove academic test data.

## 1. Safety Measures (Pre-Flight checklist)
Before executing the cleanup transaction, the script will:
1. Initialize an enterprise log event: `[ACADEMIC CLEANUP INITIALIZED]`.
2. Take a full logical backup of `schedule_db` using `pg_dump` to `backup_json/pre_cleanup_backup.sql`.
3. Open a single PostgreSQL transaction block.

## 2. Planned Surgical Database Mutations

### Step 1: Delete Observations from Test Sessions
```sql
DELETE FROM observations 
WHERE session_id IN (
    SELECT id FROM schedule_sessions 
    WHERE xml_upload_id = 'fd241a1c-0beb-4640-bf65-2c3ce92ab4b0'
);
```
* **Target Count**: 0 observations (verified during audit).

### Step 2: Delete RPT Planilla records belonging to test XML
```sql
DELETE FROM rpt_planilla 
WHERE xml_upload_id = 'fd241a1c-0beb-4640-bf65-2c3ce92ab4b0';
```
* **Target Count**: 43 records.

### Step 3: Delete schedule_sessions belonging to test XML
```sql
DELETE FROM schedule_sessions 
WHERE xml_upload_id = 'fd241a1c-0beb-4640-bf65-2c3ce92ab4b0';
```
* **Target Count**: 20 sessions.

### Step 4: Delete temporary lessons
```sql
DELETE FROM lessons 
WHERE id NOT IN (
    SELECT DISTINCT lesson_id FROM schedule_sessions
) AND id IN (
    -- Identify lessons that are not referenced by historical sessions
    SELECT l.id FROM lessons l
    LEFT JOIN teachers t ON l.teacher_id = t.id
    WHERE t.id NOT IN (/* List of 190 historical teacher UUIDs */)
);
```
* **Target Count**: Will be cleaned dynamically based on unreferenced relations.

### Step 5: Delete Test/Temporary Teachers
```sql
DELETE FROM teachers 
WHERE id NOT IN (
    -- List of 190 historical teacher UUIDs loaded from backup
    '...'
);
```
* **Target Count**: 181 teachers.

### Step 6: Delete Test XML Upload Log entries
```sql
DELETE FROM xml_uploads 
WHERE id = 'fd241a1c-0beb-4640-bf65-2c3ce92ab4b0';
```
* **Target Count**: 1 entry.

## 3. Preserved Context Verification
We will verify that:
- **`historical_xml_import_202603.xml`** (`8bc2c3a5-fa43-4cb2-8971-ebd07ccb5b84`) is untouched.
- **`190` Real Historical Teachers** are untouched.
- **`8,402` Sessions** are untouched.
- **`4,819` RPT Planilla** rows are untouched.
- **`137` Observations** are untouched.
