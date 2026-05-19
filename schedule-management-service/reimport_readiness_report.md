# Reimport Readiness Report (Draft)

**Status**: PENDING USER APPROVAL
**Target Database**: `schedule_db` (PostgreSQL)

This report details how the database schema and constraints are prepared to accept new academic XML and Excel files post-cleanup.

## 1. Constraint and Index Analysis

### unique constraints on xml_uploads
- **Table**: `xml_uploads`
- **Constraint**: Unique on `filename` and `(start_date, end_date)` overlaps.
- **Verification**: Once the test XML upload `complex_mdm_test_v2.xml` is removed, uploading it again under the same filename or range will NOT raise duplicate or overlap errors. It will proceed cleanly as a new completed upload lifecycle.

### teacher unique constraints
- **Table**: `teachers`
- **Constraint**: Unique on `source_id` (e.g. `EXCEL_...` or custom codes).
- **Verification**: Removing the 181 test teachers ensures that importing a new Excel file containing these teachers (or different ones) will not violate the `source_id` unique constraint. They will be inserted cleanly with new UUIDs and complete referential integrity.

### schedule_sessions constraints
- **Table**: `schedule_sessions`
- **Verification**: Cleared test sessions will prevent session hour/overlap collisions with the incoming new XML.

## 2. Security and Auth Isolation (RBAC)
The cleanup script operates strictly inside the academic data layer:
- **Zero changes** to `users` and `user_roles`.
- **Zero changes** to `roles` and `permissions`.
- **Zero changes** to login endpoint parameters.
- All requests to API routes will remain fully secured and audited by the RBAC middleware.

## 3. Observability and Performance Gates
- **Traceability**: All import actions will log structured events using `log_event(rpt_logger, ...)` with unique `trace_id` values.
- **Deduplication Mode**: The system's binary replacement deduplication algorithm (keying on `(rpt_record.id, session_id)`) is fully preserved and active for the new import.
- **Performance**: Index configurations are preserved, guaranteeing database lookup queries run under **500ms** even with massive academic uploads.
