from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from . import models, schemas, crud
from .database import engine, get_db
from datetime import datetime
import logging

# Configure logging
logging.basicConfig(filename="data_change_log.txt", level=logging.INFO, format="%(asctime)s - %(message)s")

# Helper function to log changes
def log_change(action, item_type, item_name, details):
    log_message = f"{action} {item_type}: {item_name} - {details}"
    logging.info(log_message)
    
# Initialize the database tables
models.Base.metadata.create_all(bind=engine)

app = FastAPI()

# Add a new team
@app.post("/teams/", response_model=schemas.Team)
def add_team(team: schemas.TeamCreate, db: Session = Depends(get_db)):
    # Validate date format
    try:
        datetime.strptime(team.registration_date, "%d/%m")
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid date format. Expected DD/MM.")
    
    # Validate group number
    if team.group_number not in [1, 2]:
        raise HTTPException(status_code=400, detail="Group number must be 1 or 2.")
    
    # Check group capacity
    group_count = db.query(models.Team).filter(models.Team.group_number == team.group_number).count()
    if group_count >= 6:
        raise HTTPException(status_code=400, detail=f"Group {team.group_number} already has 6 teams. No more teams can be added.")

    db_team = crud.get_team(db, team.name)
    if db_team:
        raise HTTPException(status_code=400, detail="Team already exists")
    
    created_team = crud.create_team(db, team)

    # Log the change
    log_change("Added", "Team", team.name, f"Group {team.group_number}, Registration Date {team.registration_date}")

    return created_team


# Update a team's details
@app.put("/teams/{team_name}", response_model=schemas.Team)
def update_team(team_name: str, team: schemas.TeamCreate, db: Session = Depends(get_db)):
    db_team = crud.get_team(db, team_name)
    if db_team is None:
        raise HTTPException(status_code=404, detail="Team not found")
    
    old_name = db_team.name

    # Update the team details
    db_team.name = team.name
    db_team.registration_date = team.registration_date
    db_team.group_number = team.group_number
    db.commit()
    db.refresh(db_team)

    # Update team name in matches where it is referenced
    db.query(models.Match).filter(models.Match.team_a == old_name).update({"team_a": team.name})
    db.query(models.Match).filter(models.Match.team_b == old_name).update({"team_b": team.name})
    db.commit()

    # Log the change
    log_change("Updated", "Team", old_name, f"New Name: {team.name}, New Group: {team.group_number}")

    return db_team


# Add a new match
@app.post("/matches/", response_model=schemas.Match)
def add_match(match: schemas.MatchCreate, db: Session = Depends(get_db)):
    # Check if team_a and team_b are different
    if match.team_a == match.team_b:
        raise HTTPException(status_code=400, detail="Team A and Team B must be different.")
    
    # Check if team_a exists
    db_team_a = crud.get_team(db, match.team_a)
    if db_team_a is None:
        raise HTTPException(status_code=400, detail=f"Team '{match.team_a}' not recognized")
    
    # Check if team_b exists
    db_team_b = crud.get_team(db, match.team_b)
    if db_team_b is None:
        raise HTTPException(status_code=400, detail=f"Team '{match.team_b}' not recognized")
    
    # Ensure both teams are in the same group
    if db_team_a.group_number != db_team_b.group_number:
        raise HTTPException(status_code=400, detail=f"No cross-group matches allowed. Teams '{match.team_a}' and '{match.team_b}' are in different groups.")
    
    # Check if a match between team_a and team_b already exists (in either order)
    existing_match = db.query(models.Match).filter(
        ((models.Match.team_a == match.team_a) & (models.Match.team_b == match.team_b)) |
        ((models.Match.team_a == match.team_b) & (models.Match.team_b == match.team_a))
    ).first()
    
    if existing_match:
        raise HTTPException(status_code=400, detail=f"A match between {match.team_a} and {match.team_b} already exists.")
    
    # Create the match
    created_match = crud.create_match(db, match)

    # Log the addition of the match
    log_change("Added", "Match", f"{match.team_a} vs {match.team_b}", f"Score: {match.goals_a}-{match.goals_b}")

    return created_match


# Update a match's details
@app.put("/matches/{match_id}", response_model=schemas.Match)
def update_match(match_id: int, match: schemas.MatchCreate, db: Session = Depends(get_db)):
    db_match = db.query(models.Match).filter(models.Match.id == match_id).first()
    if db_match is None:
        raise HTTPException(status_code=404, detail="Match not found")
    
    if match.goals_a < 0 or match.goals_b < 0:
        raise HTTPException(status_code=400, detail="Goals cannot be negative")
    
    # Log before updating the match
    log_change("Updated", "Match", f"{db_match.team_a} vs {db_match.team_b}", f"Old Score: {db_match.goals_a}-{db_match.goals_b}")

    # Update the match details
    db_match.team_a = match.team_a
    db_match.team_b = match.team_b
    db_match.goals_a = match.goals_a
    db_match.goals_b = match.goals_b
    db.commit()
    db.refresh(db_match)

    # Log after updating the match
    log_change("Updated", "Match", f"{match.team_a} vs {match.team_b}", f"New Score: {match.goals_a}-{match.goals_b}")

    return db_match

# Get rankings and top 4 teams
@app.get("/rankings/")
def get_rankings(db: Session = Depends(get_db)):
    teams_group_1 = crud.get_teams_by_group(db, 1)
    teams_group_2 = crud.get_teams_by_group(db, 2)
    matches = crud.get_all_matches(db)

    # Initialize ranking dictionary for each team
    rankings = {team.name: {
        "match_points": 0,
        "goals_scored": 0,
        "alternate_points": 0,
        "registration_date": datetime.strptime(team.registration_date, "%d/%m"),  # Convert to datetime for comparison
        "group_number": team.group_number
    } for team in teams_group_1 + teams_group_2}

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

    # Sort teams based on ranking criteria, with registration date as the last tiebreaker
    sorted_teams_group_1 = sorted(teams_group_1, key=lambda team: (
        -rankings[team.name]["match_points"],
        -rankings[team.name]["goals_scored"],
        -rankings[team.name]["alternate_points"],
        rankings[team.name]["registration_date"]
    ))

    sorted_teams_group_2 = sorted(teams_group_2, key=lambda team: (
        -rankings[team.name]["match_points"],
        -rankings[team.name]["goals_scored"],
        -rankings[team.name]["alternate_points"],
        rankings[team.name]["registration_date"]
    ))

    # Get top 4 teams for each group based on correct tiebreaker
    top_4_group_1 = sorted_teams_group_1[:4]
    top_4_group_2 = sorted_teams_group_2[:4]

    # Format team rankings
    team_rankings = [
        {
            "team_name": team.name,
            "match_points": rankings[team.name]["match_points"],
            "goals_scored": rankings[team.name]["goals_scored"],
            "alternate_points": rankings[team.name]["alternate_points"],
            "registration_date": team.registration_date,  # Keep as string for display
            "group_number": team.group_number
        }
        for team in sorted_teams_group_1 + sorted_teams_group_2
    ]

    # Return rankings and matches, and send top 4 teams for both groups
    return {
        "rankings": team_rankings,
        "matches": [
            {
                "id": match.id,
                "team_a": match.team_a,
                "team_b": match.team_b,
                "goals_a": match.goals_a,
                "goals_b": match.goals_b
            }
            for match in matches
        ],
        "top_4_group_1": [{"team_name": team.name} for team in top_4_group_1],
        "top_4_group_2": [{"team_name": team.name} for team in top_4_group_2]
    }

# Clear all teams and matches from the database
@app.delete("/clear/")
def clear_data(db: Session = Depends(get_db)):
    log_change("Cleared", "Championship", "", "Previous Championship Data Deleted. Starting New Championship!")
    crud.clear_all_data(db)
    
    return {"message": "All data cleared"}
