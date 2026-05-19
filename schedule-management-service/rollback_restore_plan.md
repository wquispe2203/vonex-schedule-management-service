# Rollback Restore Plan

Generated on: 2026-05-18T12:43:50-05:00

To guarantee that the restoration is fully reversible, this document defines the surgical rollback strategy and provides a ready-to-run automation script.

## 1. Rollback Strategy

Because all historical records are isolated and bound to the newly introduced Virtual XML Upload (`id: 8bc2c3a5-fa43-4cb2-8971-ebd07ccb5b84`), we can target and remove the restored records cleanly. 

The rollback operates in strict reverse-dependency order:
1. Delete records in `observations` referencing restored sessions.
2. Delete records in `schedule_sessions` linked to `xml_upload_id = '8bc2c3a5-fa43-4cb2-8971-ebd07ccb5b84'`.
3. Delete records in `rpt_planilla` linked to `xml_upload_id = '8bc2c3a5-fa43-4cb2-8971-ebd07ccb5b84'`.
4. Delete the virtual XML record in `xml_uploads`.

This preserves all other active data, seed data, and other independent XML uploads (like `complex_mdm_test_v2.xml`) with zero collateral damage.

## 2. Execution Command

To execute the rollback, simply run the dedicated script from PowerShell:

```powershell
python "C:\Users\SISTEMAS2\.gemini\antigravity\brain\632fbacc-9451-451a-805c-a4110b33cc72\scratch\rollback_restore.py"
```

## 3. Post-Rollback State Verification

After execution, the following counts should be verified to confirm full return to the pre-restored state:
- **`schedule_sessions`**: Count should return to original pre-restore value.
- **`rpt_planilla`**: Count should return to original pre-restore value.
- **`observations`**: Count should return to 0.
- **`xml_uploads`**: Virtual upload `historical_xml_import_202603.xml` must no longer exist.
