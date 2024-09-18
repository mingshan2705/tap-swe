import streamlit as st
import requests
import pandas as pd
from datetime import datetime

# Set your FastAPI backend URL
API_URL = "http://localhost:8000"

st.set_page_config(page_title="Football Championship", layout="centered")

# Sidebar Navigation
st.sidebar.title("Navigation")
page = st.sidebar.radio("Go to", ["Scoreboard", "Add Teams", "Edit Teams", "Teams", "Add Matches", "Edit Matches", "Matches", "Clear All Data"])

# Utility function to fetch rankings and teams data from backend
def fetch_rankings():
    try:
        response = requests.get(f"{API_URL}/rankings/")
        if response.status_code == 200:
            return response.json()
        else:
            st.error("Failed to fetch rankings data from backend.")
            st.write(response.text)
            return {}
    except requests.exceptions.RequestException as e:
        st.error("Error connecting to the API.")
        st.write(e)
        return {}

# 1. Scoreboard Page
if page == "Scoreboard":
    st.title("Football Championship Scoreboard")
    rankings_data = fetch_rankings()

    if rankings_data and "rankings" in rankings_data:
        # Split teams by group
        group_1 = [team for team in rankings_data["rankings"] if team.get("group_number", 0) == 1]
        group_2 = [team for team in rankings_data["rankings"] if team.get("group_number", 0) == 2]

        # Display Group 1 Rankings
        st.subheader("Group 1 Rankings")
        df_group_1 = pd.DataFrame(group_1)
        if not df_group_1.empty:
            df_group_1 = df_group_1[["team_name", "match_points", "goals_scored", "alternate_points", "registration_date"]]
            st.table(df_group_1)

        # Display Group 2 Rankings
        st.subheader("Group 2 Rankings")
        df_group_2 = pd.DataFrame(group_2)
        if not df_group_2.empty:
            df_group_2 = df_group_2[["team_name", "match_points", "goals_scored", "alternate_points", "registration_date"]]
            st.table(df_group_2)

# 2. Add Teams Page
elif page == "Add Teams":
    st.title("Add Teams")
    
    # Multiline input for team details (group number is part of the input)
    team_input = st.text_area("Enter team details in the following format (one per line):\n<Team Name> <Registration Date DD/MM> <Group Number>", height=200)
    
    if st.button("Add Teams"):
        teams = team_input.split('\n')
        for team in teams:
            team_data = team.split()
            if len(team_data) == 3:
                team_name, registration_date, group_number = team_data
                data = {
                    "name": team_name,
                    "registration_date": registration_date,
                    "group_number": int(group_number)
                }
                # Send request to the backend
                response = requests.post(f"{API_URL}/teams/", json=data)
                if response.status_code == 200:
                    st.success(f"Added Team: {team_name}")
                else:
                    st.error(f"Failed to add Team: {response.json()['detail']}")
            else:
                st.error(f"Invalid format for line: {team}")



# 3. View Teams Page (for viewing/searching teams)
elif page == "Teams":
    st.title("Teams")

    # Fetch rankings and teams data
    rankings_data = fetch_rankings()

    if "rankings" in rankings_data:
        df_teams = pd.DataFrame(rankings_data["rankings"])  # Convert to DataFrame for display

        # Search for specific teams
        search_term = st.text_input("Search for a team by name:")
        if search_term:
            df_teams = df_teams[df_teams["team_name"].str.contains(search_term, case=False)]
        
        # Display the teams table
        if not df_teams.empty:
            st.dataframe(df_teams)

# 4. Add Matches Page (for adding new matches)
elif page == "Add Matches":
    st.title("Add Matches")

    # Multiline input for match details
    st.subheader("Add New Matches")
    match_input = st.text_area("Enter match details in the following format (one per line):\n<Team A Name> <Team B Name> <Goals A> <Goals B>", 
                               height=200)
    
    if st.button("Add Matches"):
        matches = match_input.split('\n')
        for match in matches:
            match_data = match.split()
            if len(match_data) == 4:
                team_a, team_b, goals_a, goals_b = match_data
                if team_a == team_b:
                    st.error("Team A and Team B must be different.")
                else:
                    data = {
                        "team_a": team_a,
                        "team_b": team_b,
                        "goals_a": int(goals_a),
                        "goals_b": int(goals_b)
                    }
                    # Send request to the backend
                    response = requests.post(f"{API_URL}/matches/", json=data)
                    if response.status_code == 200:
                        st.success(f"Added Match: {team_a} vs {team_b}")
                    else:
                        # Display the error message returned by the backend
                        st.error(f"Failed to add Match: {response.json()['detail']}")
            else:
                st.error(f"Invalid format for line: {match}")



# 5. Edit Teams Page (for updating/deleting teams)
elif page == "Edit Teams":
    st.title("Edit Teams")

    # Ensure that 'reload_teams' is initialized in session_state
    if "reload_teams" not in st.session_state:
        st.session_state.reload_teams = 0

    reload_key = f"reload_{st.session_state.get('reload_teams', 0)}"
    rankings_data = fetch_rankings()

    if "rankings" in rankings_data:
        df_teams = pd.DataFrame(rankings_data["rankings"])  # Convert to DataFrame for display

        # Select a team to edit
        selected_team = st.selectbox("Select a team to edit", df_teams["team_name"].tolist() if not df_teams.empty else [], key=f"select_{reload_key}")
        
        if selected_team:
            selected_team_data = df_teams[df_teams["team_name"] == selected_team].iloc[0]
            
            # Display fields for editing
            new_team_name = st.text_input("New Team Name", value=selected_team_data["team_name"], key=f"name_{reload_key}")
            new_registration_date = st.text_input("New Registration Date (DD/MM)", value=selected_team_data["registration_date"], key=f"date_{reload_key}")
            
            # Validate registration date
            valid_date = True
            try:
                datetime.strptime(new_registration_date, "%d/%m")  # Validate date format
            except ValueError:
                valid_date = False
                st.error("Invalid date format. Please enter the date in DD/MM format.")
            
            # Ensure group_number is present
            new_group_number = st.number_input("New Group Number", min_value=1, max_value=2, value=int(selected_team_data["group_number"]), key=f"group_{reload_key}")
            
            # Update team (only if the date is valid)
            if st.button("Update Team", key=f"update_{reload_key}") and valid_date:
                update_data = {
                    "name": new_team_name,
                    "registration_date": new_registration_date,
                    "group_number": new_group_number
                }
                response = requests.put(f"{API_URL}/teams/{selected_team}", json=update_data)
                if response.status_code == 200:
                    st.success(f"Updated Team: {selected_team}")
                    st.session_state.reload_teams += 1  # Reload the page to reflect the updates
                else:
                    st.error(f"Failed to update Team: {selected_team}. {response.text}")

            # Delete team
            if st.button("Delete Team", key=f"delete_{reload_key}"):
                response = requests.delete(f"{API_URL}/teams/{selected_team}")
                if response.status_code == 200:
                    st.success(f"Deleted Team: {selected_team}")
                else:
                    st.error(f"Failed to delete Team: {selected_team}. {response.text}")


# 6. View Matches Page (for viewing/searching matches)
elif page == "Matches":
    st.title("Matches")
    rankings_data = fetch_rankings()

    if "matches" in rankings_data:
        df_matches = pd.DataFrame(rankings_data["matches"])  # Convert to DataFrame for display

        # Search for specific matches
        search_term = st.text_input("Search for a match by team name:")
        if search_term:
            df_matches = df_matches[df_matches.apply(lambda row: search_term.lower() in row["team_a"].lower() or search_term.lower() in row["team_b"].lower(), axis=1)]
        
        # Display the matches table
        if not df_matches.empty:
            st.dataframe(df_matches)

# 7. Edit Matches Page (for updating/deleting matches)
elif page == "Edit Matches":
    st.title("Edit Matches")
    rankings_data = fetch_rankings()

    # Check if "matches" exist in the rankings data
    if "matches" in rankings_data and rankings_data["matches"]:
        df_matches = pd.DataFrame(rankings_data["matches"])  # Convert to DataFrame for display

        if 'id' in df_matches.columns:
            # Select a match to edit
            selected_match_id = st.selectbox("Select a match to edit", df_matches['id'].tolist())

            selected_match_data = df_matches[df_matches['id'] == selected_match_id].iloc[0]

            # Display the team names as non-editable text
            st.text(f"Team A: {selected_match_data['team_a']}")
            st.text(f"Team B: {selected_match_data['team_b']}")

            # Display fields for editing
            new_goals_a = st.number_input("New Goals for Team A", min_value=0, value=selected_match_data["goals_a"])
            new_goals_b = st.number_input("New Goals for Team B", min_value=0, value=selected_match_data["goals_b"])

            # Update match
            if st.button("Update Match"):
                update_data = {
                    "team_a": new_team_a,
                    "team_b": new_team_b,
                    "goals_a": new_goals_a,
                    "goals_b": new_goals_b
                }
                response = requests.put(f"{API_URL}/matches/{selected_match_id}", json=update_data)
                if response.status_code == 200:
                    st.success(f"Updated Match: {new_team_a} vs {new_team_b}")
                else:
                    st.error(f"Failed to update Match: {new_team_a} vs {new_team_b}. {response.text}")
        else:
            st.warning("No match IDs available to select. Please ensure matches have been added.")
    else:
        st.warning("No matches available. Please add some matches first.")

# 8. Clear All Data Page
elif page == "Clear All Data":
    st.title("Clear All Data")

    st.warning("This will delete all teams and matches from the database. This action cannot be undone.")

    if st.button("Clear All Data"):
        response = requests.delete(f"{API_URL}/clear/")
        if response.status_code == 200:
            st.success("All data cleared from the database.")
        else:
            st.error("Failed to clear the database.")
