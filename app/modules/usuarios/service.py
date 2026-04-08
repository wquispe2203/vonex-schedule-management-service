from . import schemas, repository
from sqlalchemy.orm import Session

def get_users(db: Session):
    return repository.get_users(db)

def create_user(db: Session, data):
    return repository.create_user(db, data)

def update_user(db: Session, user_id, data):
    return repository.update_user(db, user_id, data)

def delete_user(db: Session, user_id):
    return repository.delete_user(db, user_id)

def authenticate_user(db: Session, username, password):
    return repository.authenticate_user(db, username, password)

def assign_roles_to_user(db: Session, user_id, role_ids):
    return repository.assign_roles_to_user(db, user_id, role_ids)

def get_roles(db: Session):
    return repository.get_roles(db)

def create_role(db: Session, name):
    return repository.create_role(db, name)

def assign_permissions_to_role(db: Session, role_id, permission_ids):
    return repository.assign_permissions_to_role(db, role_id, permission_ids)

def get_permissions(db: Session):
    return repository.get_permissions(db)

def update_user_password(db: Session, user_id, new_password):
    return repository.update_user_password(db, user_id, new_password)
