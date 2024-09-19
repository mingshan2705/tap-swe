# Football Championship App

## Overview

This project is a **Football Championship Management System** designed to manage football teams, matches, and rankings. It provides a user-friendly interface for adding and editing teams and matches, viewing rankings, and tracking data changes. The system is implemented with **FastAPI** for the backend, **Streamlit** for the frontend, and **SQLite** as the database. The application is containerized with Docker.

---

## Architecture

### 1. **Backend (FastAPI)**
The backend is responsible for handling API requests from the frontend, managing the SQLite database, performing business logic (such as ranking teams), and logging changes to teams and matches.

#### Key Features:
- **Teams Management**: Add or update teams. Each team belongs to one of two groups (Group 1 or Group 2).
- **Matches Management**: Add or update matches between teams, with automatic ranking updates.
- **Rankings Calculation**: Automatically ranks teams based on match results and predefined criteria.
- **Data Logging**: All data changes (team and match additions, updates, deletions) are logged. 
  
#### Endpoints:
- `/teams/` – Create a new team.
- `/teams/{team_name}` – Update or delete a specific team.
- `/matches/` – Create a new match.
- `/matches/{match_id}` – Update or delete a match.
- `/rankings/` – Fetch current team rankings.
- `/clear/` – Clear all teams and matches to start a new championship.

### 2. **Frontend (Streamlit)**
The frontend provides a simple and intuitive interface for managing teams, matches, and viewing the rankings. It communicates with the FastAPI backend to fetch and update data.

#### Key Pages:
- **Scoreboard**: View the rankings of teams in each group.
- **Add/Edit Teams**: Add new teams or update existing teams.
- **Add/Edit Matches**: Add new matches or update existing ones.
- **Data Change Log**: View a log of all data changes.
- **Clear All Data**: Reset the championship by clearing all teams and matches.

### 3. **Database (SQLite)**
SQLite is used as the database to store teams and matches persistently. The database (`database.db`) is generated automatically.

---

## Peronsal Implementation and Assumptions

- **No Cross-Group Matches**: Teams from different groups cannot play against each other. The system enforces this when adding matches.
  
- **Maximum 6 Teams per Group**: Each group can have a maximum of 6 teams. The system rejects attempts to add more teams to a full group.

- **Only One User**: There are no distinct roles for users of this app. Assume that the user is the one hosting the Football Championship and wants to use the app to help in registering teams and recording matches.

- **Logging**: All changes to teams and matches (additions, updates, and deletions) are logged for auditing purposes in a file (`data_change_log.txt`).

- **Championship Data**: When the User "Clears All Data" from the current Championship, all the current Championship data (Teams and Matches) will be wiped from the database and a new Championship will start. This action will be logged and logs persists across Championships.

---

## Running the Application

Before running the application, ensure that you have Docker installed on your machine. You can install Docker by following the instructions [here](https://docs.docker.com/get-docker/).

Once Docker is installed, follow these steps to run the application:

1. **Build the Docker container**:
   ```bash
   docker build -t football-championship-app .
   ```

1. **Run the container**:
   ```bash 
   docker run -p 8000:8000 -p 8501:8501 football-championship-app .
   ```

    This will start the backend at localhost:8000 and the frontend at localhost:8501.

    The SQLite database (database.db) will be created automatically in the container. If you need to reset the data, you can clear it using the "Clear All Data" page in the frontend or by deleting the database.db file.

---

## Running My Own Tests

1. Can add teams (with multiline) in the given format, reject if format is wrong.

1. Validation for Date input (team's registration date).
1. Can add matches (with multiline) in the given format, 
reject if format is wrong.
1. Multiline inputs will only process lines that are correct, any wrong lines will throw an alert to the User and not be processed.
1. Reject match adding that involves a non-existent team.
1. Reject match adding that involves 2 of the same team.
1. Reject match adding that involves 2 teams from different groups (No cross matches).
1. Team should only be in group 1 or 2.
1. Reject adding/editing teams into a group with has the maximum capacity of 6 teams.
1. Existing matches cannot be added again. Changes to match scoring should be done in the 'Edit Match' page.
1. Can view teams and matches after adding.
1. Can view scoreboard with correct ranking.
1. Edits are displayed consistently across pages.

    