import sys
sys.path.insert(0, '.')
from app.database import SessionLocal
from app.models import Teacher, Observation, ScheduleSession, Lesson
from sqlalchemy import or_
import datetime

def fix_db():
    db = SessionLocal()
    
    # 1. Check AR1 Activity
    active_teachers = db.query(Teacher).filter(
        or_(
            db.query(ScheduleSession).join(Lesson).filter(Lesson.teacher_id == Teacher.id).exists(),
            db.query(Observation).filter(Observation.replacement_teacher_id == Teacher.id).exists()
        )
    ).all()
    
    for t in active_teachers:
        if "AR1" in (t.last_name or "").upper() or "TR1" in (t.last_name or "").upper():
            # Check WHY it's active
            sess_count = db.query(ScheduleSession).join(Lesson).filter(Lesson.teacher_id == t.id).count()
            obs_count = db.query(Observation).filter(Observation.replacement_teacher_id == t.id).count()
            print(f"DUMMY TEACHER FOUND IN ACTIVE! {t.last_name} {t.first_name} - Sessions: {sess_count}, Obs: {obs_count}")

    # 2. Fix MAGNO and GONZALEZ in Teacher table
    print("Fixing Teachers...")
    teachers = db.query(Teacher).all()
    for t in teachers:
        fname = (t.first_name or "").upper()
        lname = (t.last_name or "").upper()
        
        if lname == "MAGNO" and "CORDOVA" in fname:
            t.last_name = "MAGNO CORDOVA"
            t.first_name = fname.replace("CORDOVA ", "").replace("CORDOVA", "").strip()
            print(f"Fixed Teacher: {t.last_name}, {t.first_name}")
            
        elif lname == "GONZALEZ" and "MORENO" in fname:
            t.last_name = "GONZALEZ MORENO"
            t.first_name = fname.replace("MORENO ", "").replace("MORENO", "").strip()
            print(f"Fixed Teacher: {t.last_name}, {t.first_name}")

    # 3. Fix MAGNO and GONZALEZ in Observation table
    print("Fixing Observations...")
    obs = db.query(Observation).all()
    for o in obs:
        rname = (o.replacement_teacher_name or "").upper()
        if not rname: continue
        
        if "MAGNO" in rname and "CORDOVA" in rname:
            new_name = "MAGNO CORDOVA, ITALO FRANZ"
            if rname != new_name:
                o.replacement_teacher_name = new_name
                print(f"Fixed Obs ID {o.id}: {rname} -> {new_name}")
                
        elif "GONZALEZ" in rname and "MORENO" in rname:
            new_name = "GONZALEZ MORENO, RAUL IVAN"
            if rname != new_name:
                o.replacement_teacher_name = new_name
                print(f"Fixed Obs ID {o.id}: {rname} -> {new_name}")

    db.commit()
    print("Migration complete!")

if __name__ == "__main__":
    fix_db()
