# Restore Gap Report

Generated on: 2026-05-18T12:43:18.326198

Comparing the quantities of records currently in the PostgreSQL Active DB (`schedule_db`) versus those available in the historical JSON backups (`backup_json/`).

| Entity / Table | Active DB Count | Backup JSON Count | Gap (Backup - Active) | Status / Action |
| :--- | :---: | :---: | :---: | :--- |
| **teachers** | 181 | 190 | 9 | Missing historical teachers. Will be restored via UPSERT. |
| **users** | 4 | 2 | -2 | Main administrative users differ. Will merge historical users. |
| **subjects** | 21 | 236 | 215 | Restoring historical course listings. |
| **classes** | 31 | 153 | 122 | Restoring historical classrooms / grades mappings. |
| **lessons** | 25 | 4092 | 4067 | Restoring full master lessons mapping. |
| **schedule_sessions** | 20 | 8402 | 8382 | Restoring completed academic schedules. |
| **observations** | 0 | 137 | 137 | Restoring historical observations/replacements. |
| **rpt_planilla** | 43 | 4819 | 4776 | Restoring consolidated payroll registers. |

### Observations
* The active database contains seed data that represents only a tiny fraction of the historical records.
* The gap analysis proves that a bulk restoration is highly necessary to restore historical reports viability.
