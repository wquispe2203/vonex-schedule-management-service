from app.core.database import SessionLocal
from app.modules.reportes.service import process_rpt_logic
from app.models.reports import RptPlanilla
from app.models.infrastructure import RecessRule
from datetime import date
from sqlalchemy import text
import unittest
import contextlib
import io

class TestRecessParity(unittest.TestCase):
    def setUp(self):
        self.db = SessionLocal()
        # Seed rules if missing
        if self.db.query(RecessRule).count() == 0:
            from seed_recess_rules import seed
            seed()
        
        # Fetch real RPT records
        self.test_records = self.db.query(RptPlanilla).limit(200).all()
        self.fecha_init = date(2026, 3, 1)
        self.fecha_end = date(2026, 5, 30)

    def tearDown(self):
        self.db.close()

    def test_recess_parity_real_db_toggle(self):
        print("\n[PARITY] Starting Real DB Toggle Parity Test...")
        
        # 1. Hybrid Run (Rules in DB)
        f = io.StringIO()
        with contextlib.redirect_stdout(f):
            hybrid_results = process_rpt_logic(self.db, self.test_records, self.fecha_init, self.fecha_end)
        
        # 2. Clear Rules to force Fallback
        self.db.query(RecessRule).delete()
        self.db.commit()
        print("[PARITY] Recess rules deleted from DB. Forcing fallback...")
        
        # 3. Fallback Run
        f2 = io.StringIO()
        with contextlib.redirect_stdout(f2):
            fallback_results = process_rpt_logic(self.db, self.test_records, self.fecha_init, self.fecha_end)
            
        # 4. Restore Rules
        from seed_recess_rules import seed
        seed()
        print("[PARITY] Recess rules restored.")
        
        # 5. Validation
        hybrid_total = sum(r["receso"] for r in hybrid_results)
        fallback_total = sum(r["receso"] for r in fallback_results)
        
        print(f"[PARITY] Hybrid Length: {len(hybrid_results)} | Fallback Length: {len(fallback_results)}")
        print(f"[PARITY] Hybrid Total: {hybrid_total} | Fallback Total: {fallback_total}")
        
        self.assertEqual(len(hybrid_results), len(fallback_results), "Length mismatch!")
        
        divergences = []
        for i in range(len(hybrid_results)):
            h = hybrid_results[i]
            fb = fallback_results[i]
            if abs(h["receso"] - fb["receso"]) > 0.001:
                divergences.append(f"Block {i}: {h['docente']} {h['hora_init']}-{h['hora_fin']} | H:{h['receso']} FB:{fb['receso']}")
        
        if divergences:
            for d in divergences[:5]: print(f"[DIVERGENCE] {d}")
            self.fail(f"Found {len(divergences)} divergences!")
        
        self.assertAlmostEqual(hybrid_total, fallback_total, places=2)
        print("[RECESS ENGINE PARITY OK] Mathematical Parity Confirmed.")

if __name__ == "__main__":
    unittest.main()
