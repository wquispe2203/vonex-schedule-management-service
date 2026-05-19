from app.core.database import SessionLocal
from app.models.user import User, Role, Permission
from app.dependencies.auth import require_permission
from uuid import uuid4
import unittest
from unittest.mock import MagicMock

class TestSuperadminSecurity(unittest.TestCase):
    def setUp(self):
        self.db = SessionLocal()
        # Create a test user
        self.test_user = User(
            username=f"test_audit_{uuid4().hex[:6]}@vonex.edu.pe",
            is_active=True
        )
        self.db.add(self.test_user)
        self.db.commit()

    def tearDown(self):
        self.db.delete(self.test_user)
        self.db.commit()
        self.db.close()

    def test_structural_bypass(self):
        print("\n[VALIDATION] Testing Structural Bypass (is_protected=True)...")
        # Create a role that IS protected but has a different name
        role = Role(name=f"PROTECTED_DEV_{uuid4().hex[:4]}", is_protected=True)
        self.db.add(role)
        self.db.commit()
        
        self.test_user.roles = [role]
        self.db.commit()
        
        # require_permission('any_code') should return the user
        checker = require_permission("some_permission_code")
        mock_request = MagicMock()
        result = checker(request=mock_request, current_user=self.test_user, db=self.db)
        
        self.assertEqual(result, self.test_user)
        print("[RBAC STRUCTURAL VALIDATION OK] Bypass worked via flag.")
        
        # Cleanup
        # Note: can't delete via service, but can via DB in test
        self.db.delete(role)
        self.db.commit()

    def test_legacy_fallback(self):
        print("\n[VALIDATION] Testing Legacy Fallback (name='SUPERADMIN')...")
        # Use existing SUPERADMIN role
        role = self.db.query(Role).filter(Role.name == "SUPERADMIN").first()
        
        # Ensure it's NOT protected for this specific test to force legacy path
        original_protected = role.is_protected
        role.is_protected = False
        self.db.commit()
        
        self.test_user.roles = [role]
        self.db.commit()
        
        checker = require_permission("some_permission_code")
        mock_request = MagicMock()
        result = checker(request=mock_request, current_user=self.test_user, db=self.db)
        
        self.assertEqual(result, self.test_user)
        print("[LEGACY STRING FALLBACK USED] Bypass worked via name.")
        
        # Restore
        role.is_protected = original_protected
        self.db.commit()

    def test_role_protection_blocked(self):
        from app.modules.usuarios.service import delete_role, update_role
        print("\n[VALIDATION] Testing Role Protection Blocking...")
        
        role = Role(name=f"CRITICAL_SYSTEM_{uuid4().hex[:4]}", is_protected=True)
        self.db.add(role)
        self.db.commit()
        
        # Test Delete
        with self.assertRaises(ValueError) as cm:
            delete_role(self.db, role.id)
        self.assertIn("estructural protegido", str(cm.exception))
        print(f"[PROTECTED ROLE BLOCKED] Delete blocked as expected: {str(cm.exception)}")
        
        # Test Update
        with self.assertRaises(ValueError) as cm:
            update_role(self.db, role.id, "NEW_NAME")
        self.assertIn("estructural protegido", str(cm.exception))
        print(f"[PROTECTED ROLE BLOCKED] Rename blocked as expected: {str(cm.exception)}")
        
        self.db.delete(role)
        self.db.commit()

if __name__ == "__main__":
    unittest.main()
