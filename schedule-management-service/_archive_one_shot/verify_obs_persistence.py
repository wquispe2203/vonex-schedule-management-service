from sqlalchemy.orm import Session
from app.core.database import SessionLocal
from app.modules.observaciones import service
from app.models import Teacher, ScheduleSession, User
import uuid

db = SessionLocal()

try:
    # Find a valid session to create an observation for
    session_obj = db.query(ScheduleSession).first()
    teacher_obj = db.query(Teacher).first()
    user_obj = db.query(User).first()
    
    if not session_obj or not teacher_obj or not user_obj:
        print("TEST FAIL: Dependencies not present (Session, Teacher, or User missing).")
    else:
        payload = {
            "session_id": str(session_obj.id),
            "teacher_id": str(teacher_obj.id),
            "user_id": str(user_obj.id),
            "type": "FALTA",
            "discount_type": "SIMPLE",
            "description": "AUTOTEST OBS PERSISTENCE FIX FINAL"
        }
        print("TESTING WITH REAL USER ID:", payload["user_id"])
        obs = service.process_observation_creation(db, payload)
        print("TEST SUCCESS: Observation successfully saved. ID:", obs.id)
        
        # Clean up
        db.delete(obs)
        db.commit()
        print("TEST CLEANUP COMPLETED.")
except Exception as e:
    import traceback
    print("TEST FAILED:")
    traceback.print_exc()
finally:
    db.close()
