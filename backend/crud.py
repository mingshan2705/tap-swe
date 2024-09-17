from sqlalchemy.orm import Session
from . import models, schemas

# Create a new team
def create_team(db: Session, team: schemas.TeamCreate):
    db_team = models.Team(**team.dict())
    db.add(db_team)
    db.commit()
    db.refresh(db_team)
    return db_team

# Create a new match
def create_match(db: Session, match: schemas.MatchCreate):
    db_match = models.Match(**match.dict())
    db.add(db_match)
    db.commit()
    db.refresh(db_match)
    return db_match

# Get all teams in a specific group
def get_teams_by_group(db: Session, group_number: int):
    return db.query(models.Team).filter(models.Team.group_number == group_number).all()

# Get all matches
def get_all_matches(db: Session):
    return db.query(models.Match).all()

# Get a specific team by name
def get_team(db: Session, team_name: str):
    return db.query(models.Team).filter(models.Team.name == team_name).first()

# Clear all teams and matches from the database
def clear_all_data(db: Session):
    db.query(models.Team).delete()
    db.query(models.Match).delete()
    db.commit()
