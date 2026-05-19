# Pre-Reset Audit Report

Generated on: 2026-05-18T12:59:18.966227

This report lists the current status of all academic and XML-derived tables in `schedule_db` prior to the cleanup of test data.

## 1. XML Uploads Inventory

### 🔴 Fixture & Test Uploads (To be cleaned)
*No fixture uploads detected.*

### 🟢 Historical & Virtual Uploads (To be preserved)
- **Filename**: `historical_xml_import_202603.xml`
  - **UUID**: `8bc2c3a5-fa43-4cb2-8971-ebd07ccb5b84`
  - **Status**: `COMPLETED`
  - **Range**: `2026-03-02` to `2026-03-20`
  - **Created**: `2026-04-08 00:00:00-05:00`

## 2. Teachers Directory Segmentation

* **Total Teachers in Database**: 190
* **Historical/Real Teachers (To be preserved)**: 190
* **Test/Temporary Teachers (To be cleaned)**: 0

### Sample Test/Temporary Teachers to delete:
*No test/temporary teachers found.*

## 3. Session & Payroll Linkage Metrics

### Schedule Sessions Distribution
- **Total Sessions**: 8402
- **Virtual Historical**: 8402 sessions

### RPT Planilla Distribution
- **Total Payroll Rows**: 4819
- **Virtual Historical**: 4819 records

### Observations Distribution
- **Total Observations**: 137
- **Linked to Historical Upload**: 137
- **Linked to Fixture/Test Uploads**: 0
- **Unlinked / Other**: 0
