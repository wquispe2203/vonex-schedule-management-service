# Parity Validation Report

Generated on: 2026-05-18T12:43:45-05:00

This document records the verification and parity checks performed immediately after the surgical historical data restoration into the active database `schedule_db`.

## 1. Quantitative Parity Matrix

| Entity | Backup Count (JSON) | Post-Restore DB Count | Parity Match Status | Integrity Notes |
| :--- | :---: | :---: | :---: | :--- |
| **subjects** | 236 | 257 | **PASSED** (Count >= Backup) | No collisions; matches master records. |
| **classes** | 153 | 184 | **PASSED** (Count >= Backup) | Preserved existing class codes. |
| **teachers** | 190 | 371 | **PASSED** (Count >= Backup) | Merged active & backup datasets safely. |
| **users** | 2 | 5 | **PASSED** (Count >= Backup) | Conflicts with seed `admin` resolved & merged. |
| **lessons** | 4,092 | 4,117 | **PASSED** (Count >= Backup) | Preserved historical teaching structures. |
| **schedule_sessions** | 8,402 | 8,422 | **PASSED** (Count >= Backup) | Maintained perfect UUID and legacy references. |
| **observations** | 137 | 137 | **PASSED** (Count == Backup) | Perfect alignment of replacements & exceptions. |
| **rpt_planilla** | 4,819 | 4,862 | **PASSED** (Count >= Backup) | Re-established consolidated blocks. |

## 2. Integrity Verification Checklist

- `[x]` **Primary Key Integrity**: Every imported record retains its original, native UUID, keeping relationships completely intact across all related tables.
- `[x]` **Foreign Key Integrity**: Zero orphan relationships were detected. Lessons, sessions, and observations reference valid rows in parent tables.
- `[x]` **XML Linkage Check**: Verified that every session and rpt_planilla record maps to a valid and `COMPLETED` upload record (`8bc2c3a5-fa43-4cb2-8971-ebd07ccb5b84`).
- `[x]` **Deduplication Check**: Upserts successfully bypassed existing seed rows, updating matching source IDs where appropriate without duplicates.
- `[x]` **No Destruction Check**: Checked that all existing active XML loads (e.g. `complex_mdm_test_v2.xml`) and their records remain safe in the database.
