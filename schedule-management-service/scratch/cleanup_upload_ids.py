import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.core.database import SessionLocal
from sqlalchemy import text

db = SessionLocal()
try:
    print("=== STARTING XML UPLOAD DATA CONSOLIDATION ===")
    
    # 1. Archive older overlapping COMPLETED uploads
    print("\n1. Archiving older overlapping COMPLETED uploads...")
    # Find overlapping uploads and archive the older ones
    overlapping_query = text("""
        SELECT u1.id, u1.filename, u1.start_date, u1.end_date, u1.created_at
        FROM xml_uploads u1
        WHERE u1.status = 'COMPLETED'
          AND EXISTS (
              SELECT 1 FROM xml_uploads u2
              WHERE u2.status = 'COMPLETED'
                AND u2.start_date = u1.start_date
                AND u2.end_date = u1.end_date
                AND u2.created_at > u1.created_at
          );
    """)
    to_archive = db.execute(overlapping_query).fetchall()
    
    if to_archive:
        print(f"Found {len(to_archive)} older completed uploads to archive:")
        for r in to_archive:
            print(f"  - Archiving: ID={r[0]} | File={r[1]} | Range={r[2]} to {r[3]} | Created={r[4]}")
            db.execute(text("UPDATE xml_uploads SET status = 'ARCHIVED' WHERE id = :uid;"), {"uid": r[0]})
        db.commit()
        print("Archiving completed successfully.")
    else:
        print("No older overlapping completed uploads found.")

    # 2. Re-assign all rpt_planilla and schedule_sessions records to the LATEST active COMPLETED upload for their respective weeks
    print("\n2. Consolidating rpt_planilla and schedule_sessions mappings...")
    
    # Get all active completed uploads, sorted by range duration DESC (broadest first, most specific last)
    active_uploads = db.execute(text("""
        SELECT id, start_date, end_date, filename 
        FROM xml_uploads 
        WHERE status = 'COMPLETED' 
        ORDER BY (end_date - start_date) DESC;
    """)).fetchall()
    
    print(f"Active completed uploads in database: {len(active_uploads)}")
    for u in active_uploads:
        uid, s_date, e_date, fname = u
        print(f"  - Active Upload: ID={uid} | File={fname} | Range={s_date} to {e_date}")
        
        # Update schedule_sessions for this date range to point to the active upload
        sess_upd = db.execute(text("""
            UPDATE schedule_sessions 
            SET xml_upload_id = :uid 
            WHERE session_date >= :s_date 
              AND session_date <= :e_date;
        """), {"uid": uid, "s_date": s_date, "e_date": e_date})
        
        # Update rpt_planilla for this date range to point to the active upload
        rpt_upd = db.execute(text("""
            UPDATE rpt_planilla 
            SET xml_upload_id = :uid 
            WHERE fecha_clase >= :s_date 
              AND fecha_clase <= :e_date;
        """), {"uid": uid, "s_date": s_date, "e_date": e_date})
        
        db.commit()
        print(f"    -> Updated {sess_upd.rowcount} sessions and {rpt_upd.rowcount} RPT records.")

    print("\n3. Verifying consolidation results...")
    dist_sess = db.execute(text("SELECT xml_upload_id, COUNT(*) FROM schedule_sessions GROUP BY xml_upload_id;")).fetchall()
    print("Sessions by xml_upload_id:")
    for d in dist_sess:
        print(f"  - Upload ID: {d[0]} | Count: {d[1]}")
        
    dist_rpt = db.execute(text("SELECT xml_upload_id, COUNT(*) FROM rpt_planilla GROUP BY xml_upload_id;")).fetchall()
    print("RPT records by xml_upload_id:")
    for d in dist_rpt:
        print(f"  - Upload ID: {d[0]} | Count: {d[1]}")

    print("\n=== CONSOLIDATION COMPLETED SUCCESSFULLY ===")
finally:
    db.close()
