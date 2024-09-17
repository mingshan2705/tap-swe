from pydantic import BaseModel

class TeamBase(BaseModel):
    name: str
    registration_date: str
    group_number: int

class TeamCreate(TeamBase):
    pass

class Team(TeamBase):
    id: int
    class Config:
        orm_mode = True

class MatchBase(BaseModel):
    team_a: str
    team_b: str
    goals_a: int
    goals_b: int

class MatchCreate(MatchBase):
    pass

class Match(MatchBase):
    id: int
    class Config:
        orm_mode = True
