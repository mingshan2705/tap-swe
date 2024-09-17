from sqlalchemy import Column, Integer, String
from .database import Base

class Team(Base):
    __tablename__ = "teams"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True)
    registration_date = Column(String, nullable=False)
    group_number = Column(Integer, nullable=False)

class Match(Base):
    __tablename__ = "matches"

    id = Column(Integer, primary_key=True, index=True)
    team_a = Column(String, nullable=False)
    team_b = Column(String, nullable=False)
    goals_a = Column(Integer, nullable=False)
    goals_b = Column(Integer, nullable=False)
