from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from . import models, schemas, crud
from .database import engine, get_db
from datetime import datetime

# Initialize the database tables
models.Base.metadata.create_all(bind=engine)

app = FastAPI()

# Add a new team
@app.post("/teams/", response_model=schemas.Team)
def add_team(team: schemas.TeamCreate, db: Session = Depends(get_db)):
    db_team = crud.get_team(db, team.name)
    if db_team:
        raise HTTPException(status_code=400, detail="Team already exists")
    return crud.create_team(db, team)

# Add a new match
@app.post("/matches/", response_model=schemas.Match)
def add_match(match: schemas.MatchCreate, db: Session = Depends(get_db)):
    return crud.create_match(db, match)

# Get details of a team by name
@app.get("/teams/{team_name}", response_model=schemas.Team)
def get_team(team_name: str, db: Session = Depends(get_db)):
    team = crud.get_team(db, team_name)
    if team is None:
        raise HTTPException(status_code=404, detail="Team not found")
    return team

# Update a team's details
@app.put("/teams/{team_name}", response_model=schemas.Team)
def update_team(team_name: str, team: schemas.TeamCreate, db: Session = Depends(get_db)):
    db_team = crud.get_team(db, team_name)
    if db_team is None:
        raise HTTPException(status_code=404, detail="Team not found")
    db_team.name = team.name
    db_team.registration_date = team.registration_date
    db_team.group_number = team.group_number
    db.commit()
    db.refresh(db_team)
    return db_team

# Delete a team
@app.delete("/teams/{team_name}")
def delete_team(team_name: str, db: Session = Depends(get_db)):
    db_team = crud.get_team(db, team_name)
    if db_team is None:
        raise HTTPException(status_code=404, detail="Team not found")
    db.delete(db_team)
    db.commit()
    return {"message": f"Team {team_name} deleted successfully"}

# Update a match's details
@app.put("/matches/{match_id}", response_model=schemas.Match)
def update_match(match_id: int, match: schemas.MatchCreate, db: Session = Depends(get_db)):
    db_match = db.query(models.Match).filter(models.Match.id == match_id).first()
    if db_match is None:
        raise HTTPException(status_code=404, detail="Match not found")
    db_match.team_a = match.team_a
    db_match.team_b = match.team_b
    db_match.goals_a = match.goals_a
    db_match.goals_b = match.goals_b
    db.commit()
    db.refresh(db_match)
    return db_match

# Delete a match
@app.delete("/matches/{match_id}")
def delete_match(match_id: int, db: Session = Depends(get_db)):
    db_match = db.query(models.Match).filter(models.Match.id == match_id).first()
    if db_match is None:
        raise HTTPException(status_code=404, detail="Match not found")
    db.delete(db_match)
    db.commit()
    return {"message": f"Match {db_match.team_a} vs {db_match.team_b} deleted successfully"}

# Clear all teams and matches from the database
@app.delete("/clear/")
def clear_data(db: Session = Depends(get_db)):
    crud.clear_all_data(db)
    return {"message": "All data cleared"}

# Get rankings based on the criteria
# Get rankings based on the criteria
@app.get("/rankings/")
def get_rankings(db: Session = Depends(get_db)):
    teams = crud.get_teams_by_group(db, 1) + crud.get_teams_by_group(db, 2)
    matches = crud.get_all_matches(db)

    # Initialize ranking dictionary for each team
    rankings = {team.name: {
        "match_points": 0,
        "goals_scored": 0,
        "alternate_points": 0,
        "registration_date": datetime.strptime(team.registration_date, "%d/%m"),
        "group_number": team.group_number  # Make sure to include group_number here
    } for team in teams}

    # Calculate match points, goals, and alternate points
    for match in matches:
        if match.goals_a > match.goals_b:  # Team A wins
            rankings[match.team_a]["match_points"] += 3
            rankings[match.team_a]["alternate_points"] += 5
            rankings[match.team_b]["alternate_points"] += 1
        elif match.goals_a < match.goals_b:  # Team B wins
            rankings[match.team_b]["match_points"] += 3
            rankings[match.team_b]["alternate_points"] += 5
            rankings[match.team_a]["alternate_points"] += 1
        else:  # Draw
            rankings[match.team_a]["match_points"] += 1
            rankings[match.team_b]["match_points"] += 1
            rankings[match.team_a]["alternate_points"] += 3
            rankings[match.team_b]["alternate_points"] += 3
        
        # Add goals scored
        rankings[match.team_a]["goals_scored"] += match.goals_a
        rankings[match.team_b]["goals_scored"] += match.goals_b

    # Sort teams based on ranking criteria
    sorted_teams = sorted(teams, key=lambda team: (
        rankings[team.name]["match_points"],
        rankings[team.name]["goals_scored"],
        rankings[team.name]["alternate_points"],
        rankings[team.name]["registration_date"]
    ), reverse=True)

    # Format team rankings
    team_rankings = [
        {
            "team_name": team.name,
            "match_points": rankings[team.name]["match_points"],
            "goals_scored": rankings[team.name]["goals_scored"],
            "alternate_points": rankings[team.name]["alternate_points"],
            "registration_date": team.registration_date,
            "group_number": team.group_number  # Ensure this field is included in the response
        }
        for team in sorted_teams
    ]

    # Return rankings and matches with match_id
    return {
        "rankings": team_rankings,
        "matches": [
            {
                "id": match.id,  # Include match_id here
                "team_a": match.team_a,
                "team_b": match.team_b,
                "goals_a": match.goals_a,
                "goals_b": match.goals_b
            }
            for match in matches
        ]
    }



@app.delete("/clear/")
def clear_database(db: Session = Depends(get_db)):
    try:
        # Clear all teams
        db.query(models.Team).delete()
        # Clear all matches
        db.query(models.Match).delete()
        # Commit the changes
        db.commit()
        return {"message": "All data cleared from the database."}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))
