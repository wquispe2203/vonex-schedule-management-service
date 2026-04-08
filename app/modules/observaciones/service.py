from . import schemas, repository
from sqlalchemy.orm import Session

def get_observation_logs_list(db: Session):
    return repository.get_observation_logs(db)

def get_observations_list(db: Session, teacher_id, start_date, end_date):
    return repository.get_observations(db, teacher_id, start_date, end_date)

def process_observation_creation(db: Session, data):
    return repository.create_observation(db, data)

def delete_observation_logic(db: Session, obs_id):
    return repository.delete_observation(db, obs_id)

def get_grouped_sessions_for_incidencias(db: Session, teacher_id, start_date, end_date):
    return repository.get_sessions_for_incidencias(db, teacher_id, start_date, end_date)
