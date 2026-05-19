import uuid
from datetime import date, time
from app.models.user import User, Role, Permission
from app.models.teacher import Teacher
from app.models.schedule import Lesson, ScheduleSession
from app.models.infrastructure import XmlUpload

class TestFactory:
    @staticmethod
    def create_role(db, name="ADMIN"):
        role = Role(name=name)
        db.add(role)
        db.commit()
        db.refresh(role)
        return role

    @staticmethod
    def create_user(db, username="test@vonex.edu.pe", role_names=["ADMIN"]):
        user = User(
            username=username,
            password_hash="$2b$12$EixZaYVK1fsbw1ZfbX3OXePaWxn96p36WQoeG6Lruj3vjPGGa31lW", # "password"
            is_active=True,
            area="SISTEMAS"
        )
        for r_name in role_names:
            role = db.query(Role).filter_by(name=r_name).first()
            if not role:
                role = Role(name=r_name)
                db.add(role)
            user.roles.append(role)
        
        db.add(user)
        db.commit()
        db.refresh(user)
        return user

    @staticmethod
    def create_teacher(db, name="DOCENTE PRUEBA", source_id="T1"):
        teacher = Teacher(
            normalized_name=name,
            source_id=source_id,
            is_active=True
        )
        db.add(teacher)
        db.commit()
        db.refresh(teacher)
        return teacher

    @staticmethod
    def create_xml_upload(db, filename="test.xml"):
        upload = XmlUpload(
            filename=filename,
            status='COMPLETED',
            start_date=date(2026, 3, 1),
            end_date=date(2026, 3, 31)
        )
        db.add(upload)
        db.commit()
        db.refresh(upload)
        return upload

    @staticmethod
    def create_session(db, teacher_id, session_date=None, xml_upload_id=None):
        if not session_date:
            session_date = date(2026, 3, 2)
        
        # Create Lesson first
        lesson = Lesson(teacher_id=teacher_id, subject_id=1, class_id=1)
        db.add(lesson)
        db.commit()
        
        session = ScheduleSession(
            lesson_id=lesson.id,
            session_date=session_date,
            start_time=time(8, 0),
            end_time=time(9, 40),
            xml_upload_id=xml_upload_id
        )
        db.add(session)
        db.commit()
        db.refresh(session)
        return session
    @staticmethod
    def create_user_with_token(db, username="guest@vonex.edu.pe", role_name="GUEST_ROLE"):
        """Crea un usuario, su rol y genera un token JWT válido."""
        from app.models.user import User, Role
        from app.core.security import create_access_token
        
        role = db.query(Role).filter(Role.name == role_name).first()
        if not role:
            role = Role(name=role_name)
            db.add(role)
            db.flush()
        
        user = User(
            username=username,
            password_hash="hashed_password",
            is_active=True
        )
        user.roles.append(role)
        db.add(user)
        db.flush()
        
        token = create_access_token(subject=str(user.id))
        return user, token
