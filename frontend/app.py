import streamlit as st
import requests
import pandas as pd

# Set your FastAPI backend URL
API_URL = "http://localhost:8000"

st.set_page_config(page_title="Football Championship", layout="centered")

# Sidebar Navigation
st.sidebar.title("Navigation")
page = st.sidebar.radio("Go to", ["Scoreboard", "Add Teams", "Edit Teams", "Teams", "Add Matches", "Edit Matches", "Matches", "Clear All Data"])

# 1. Scoreboard Page
if page == "Scoreboard":
    st.title("Football Championship Scoreboard")

    # Fetch rankings and match data from the backend
    try:
        response = requests.get(f"{API_URL}/rankings/")
        if response.status_code == 200:
            rankings_data = response.json()
        else:
            st.error("Failed to fetch rankings data from backend.")
            st.write(response.text)
    except requests.exceptions.RequestException as e:
        st.error("Error connecting to the API.")
        st.write(e)

    # Display rankings in two tables: Group 1 and Group 2
    if rankings_data and "rankings" in rankings_data:
        # Safely extract group number, use a default of 0 if missing
        group_1 = [team for team in rankings_data["rankings"] if team.get("group_number", 0) == 1]
        group_2 = [team for team in rankings_data["rankings"] if team.get("group_number", 0) == 2]

        # Display Group 1 in a table
        st.subheader("Group 1 Rankings")
        df_group_1 = pd.DataFrame(group_1)
        if not df_group_1.empty:
            df_group_1 = df_group_1[["team_name", "match_points", "goals_scored", "alternate_points", "registration_date"]]
            st.table(df_group_1)

        # Display Group 2 in a table
        st.subheader("Group 2 Rankings")
        df_group_2 = pd.DataFrame(group_2)
        if not df_group_2.empty:
            df_group_2 = df_group_2[["team_name", "match_points", "goals_scored", "alternate_points", "registration_date"]]
            st.table(df_group_2)




# 2. Add Teams Page
elif page == "Add Teams":
    st.title("Add Teams")
    
    team_input = st.text_area("Enter team details in the following format (one per line):\n<Team Name> <Registration Date DD/MM> <Group Number>", 
                              height=200)
    
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
                response = requests.post(f"{API_URL}/teams/", json=data)
                if response.status_code == 200:
                    st.success(f"Added Team: {team_name}")
                else:
                    st.error(f"Failed to add Team: {team_name}. {response.text}")
            else:
                st.error(f"Invalid format for line: {team}")

# 3. View Teams Page (for viewing/searching teams)
elif page == "Teams":
    st.title("Teams")

    # Function to fetch teams data
    def fetch_teams():
        try:
            response = requests.get(f"{API_URL}/rankings/")
            if response.status_code == 200:
                teams_data = response.json()["rankings"]
                df_teams = pd.DataFrame(teams_data)  # Convert to DataFrame for display
                return df_teams
            else:
                st.error("Failed to fetch teams data from backend.")
                st.write(response.text)
        except requests.exceptions.RequestException as e:
            st.error("Error connecting to the API.")
            return pd.DataFrame()

    df_teams = fetch_teams()  # Initial fetch

    # Search for specific teams
    search_term = st.text_input("Search for a team by name:")
    if search_term:
        df_teams = df_teams[df_teams["team_name"].str.contains(search_term, case=False)]
    
    # Display the teams table
    if not df_teams.empty:
        st.dataframe(df_teams)

# Add Matches Page (for adding new matches)
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
                data = {
                    "team_a": team_a,
                    "team_b": team_b,
                    "goals_a": int(goals_a),
                    "goals_b": int(goals_b)
                }
                response = requests.post(f"{API_URL}/matches/", json=data)
                if response.status_code == 200:
                    st.success(f"Added Match: {team_a} vs {team_b}")
                else:
                    st.error(f"Failed to add Match: {team_a} vs {team_b}. {response.text}")
            else:
                st.error(f"Invalid format for line: {match}")

# 4. View Matches Page (for viewing/searching matches)
elif page == "Matches":
    st.title("Matches")

    # Fetch matches from the backend
    try:
        response = requests.get(f"{API_URL}/rankings/")
        if response.status_code == 200:
            matches_data = response.json()["matches"]
            df_matches = pd.DataFrame(matches_data)  # Convert to DataFrame for display
        else:
            st.error("Failed to fetch matches data from backend.")
            st.write(response.text)
    except requests.exceptions.RequestException as e:
        st.error("Error connecting to the API.")
        matches_data = []

    # Search for specific matches
    search_term = st.text_input("Search for a match by team name:")
    if search_term:
        df_matches = df_matches[df_matches.apply(lambda row: search_term.lower() in row["team_a"].lower() or search_term.lower() in row["team_b"].lower(), axis=1)]
    
    # Display the matches table
    if not df_matches.empty:
        st.dataframe(df_matches)
        
# Edit Teams Page (for updating/deleting teams)
elif page == "Edit Teams":
    st.title("Edit Teams")

    # Use a key based on session state to force re-rendering of components
    reload_key = f"reload_{st.session_state.get('reload_teams', 0)}"

    # Function to fetch updated teams data
    def fetch_teams():
        try:
            response = requests.get(f"{API_URL}/rankings/")
            if response.status_code == 200:
                teams_data = response.json()["rankings"]
                df_teams = pd.DataFrame(teams_data)  # Convert to DataFrame for display
                return df_teams
            else:
                st.error("Failed to fetch teams data from backend.")
                st.write(response.text)
        except requests.exceptions.RequestException as e:
            st.error("Error connecting to the API.")
            return pd.DataFrame()

    df_teams = fetch_teams()  # Initial fetch

    # Select a team to edit
    selected_team = st.selectbox("Select a team to edit", df_teams["team_name"].tolist() if not df_teams.empty else [], key=f"select_{reload_key}")
    
    if selected_team:
        selected_team_data = df_teams[df_teams["team_name"] == selected_team].iloc[0]
        
        # Display fields for editing
        new_team_name = st.text_input("New Team Name", value=selected_team_data["team_name"], key=f"name_{reload_key}")
        new_registration_date = st.text_input("New Registration Date", value=selected_team_data["registration_date"], key=f"date_{reload_key}")
        
        # Ensure that group_number is present
        if "group_number" in selected_team_data:
            new_group_number = st.number_input("New Group Number", min_value=1, max_value=2, value=int(selected_team_data["group_number"]), key=f"group_{reload_key}")
        else:
            st.warning("Group number not available.")
        
        # Update team
        if st.button("Update Team", key=f"update_{reload_key}"):
            update_data = {
                "name": new_team_name,
                "registration_date": new_registration_date,
                "group_number": new_group_number
            }
            response = requests.put(f"{API_URL}/teams/{selected_team}", json=update_data)
            if response.status_code == 200:
                st.success(f"Updated Team: {selected_team}")
            else:
                st.error(f"Failed to update Team: {selected_team}. {response.text}")

        # Delete team
        if st.button("Delete Team", key=f"delete_{reload_key}"):
            response = requests.delete(f"{API_URL}/teams/{selected_team}")
            if response.status_code == 200:
                st.success(f"Deleted Team: {selected_team}")
            else:
                st.error(f"Failed to delete Team: {selected_team}. {response.text}")

# 4. View Matches Page (for viewing/searching matches)
elif page == "Matches":
    st.title("Matches")

    # Fetch matches from the backend
    try:
        response = requests.get(f"{API_URL}/rankings/")
        if response.status_code == 200:
            matches_data = response.json()["matches"]
            df_matches = pd.DataFrame(matches_data)  # Convert to DataFrame for display
        else:
            st.error("Failed to fetch matches data from backend.")
            st.write(response.text)
    except requests.exceptions.RequestException as e:
        st.error("Error connecting to the API.")
        matches_data = []

    # Search for specific matches
    search_term = st.text_input("Search for a match by team name:")
    if search_term:
        df_matches = df_matches[df_matches.apply(lambda row: search_term.lower() in row["team_a"].lower() or search_term.lower() in row["team_b"].lower(), axis=1)]
    
    # Display the matches table
    if not df_matches.empty:
        st.dataframe(df_matches)


# Edit Matches Page (for updating/deleting matches)
elif page == "Edit Matches":
    st.title("Edit Matches")

    # Fetch matches from the backend
    try:
        response = requests.get(f"{API_URL}/rankings/")
        if response.status_code == 200:
            matches_data = response.json()["matches"]
            df_matches = pd.DataFrame(matches_data)  # Convert to DataFrame for display
        else:
            st.error("Failed to fetch matches data from backend.")
            st.write(response.text)
    except requests.exceptions.RequestException as e:
        st.error("Error connecting to the API.")
        matches_data = []

    # Select a match to edit based on its index in the table
    if not df_matches.empty:
        # Display match_id in the dropdown to ensure correct match selection
        selected_match_id = st.selectbox("Select a match to edit", df_matches['id'].tolist())

        selected_match_data = df_matches[df_matches['id'] == selected_match_id].iloc[0]

        # Display fields for editing
        new_team_a = st.text_input("New Team A", value=selected_match_data["team_a"])
        new_team_b = st.text_input("New Team B", value=selected_match_data["team_b"])
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



# 6. Clear All Data Page
elif page == "Clear All Data":
    st.title("Clear All Data")

    st.warning("This will delete all teams and matches from the database. This action cannot be undone.")

    if st.button("Clear All Data"):
        response = requests.delete(f"{API_URL}/clear/")
        if response.status_code == 200:
            st.success("All data cleared from the database.")
        else:
            st.error("Failed to clear the database.")
