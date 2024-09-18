import streamlit as st
import requests
import pandas as pd
from datetime import datetime

# Set your FastAPI backend URL
API_URL = "http://host.docker.internal:8000"

# Configure the page layout and theme
st.set_page_config(page_title="Football Championship", layout="wide", page_icon="⚽")

# Sidebar Main Navigation
st.sidebar.title("🏆 Football Championship")
main_page = st.sidebar.selectbox("Main Menu", ["Scoreboard", "Teams", "Matches", "Data Change Log", "Clear All Data"])

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

# Scoreboard Page
if main_page == "Scoreboard":
    st.title("🏆 Football Championship Scoreboard")
    rankings_data = fetch_rankings()

    if rankings_data and "rankings" in rankings_data:
        # Split teams by group
        group_1 = [team for team in rankings_data["rankings"] if team.get("group_number", 0) == 1]
        group_2 = [team for team in rankings_data["rankings"] if team.get("group_number", 0) == 2]

        # Display Group 1 Rankings
        st.subheader("⚽ Group 1 Rankings")
        df_group_1 = pd.DataFrame(group_1)
        if not df_group_1.empty:
            df_group_1 = df_group_1[["team_name", "match_points", "goals_scored", "alternate_points", "registration_date"]]
            st.table(df_group_1.style.set_table_styles([
                {'selector': 'thead th', 'props': [('font-weight', 'bold')]}
            ]))

        # Display Group 2 Rankings
        st.subheader("⚽ Group 2 Rankings")
        df_group_2 = pd.DataFrame(group_2)
        if not df_group_2.empty:
            df_group_2 = df_group_2[["team_name", "match_points", "goals_scored", "alternate_points", "registration_date"]]
            st.table(df_group_2.style.set_table_styles([
                {'selector': 'thead th', 'props': [('font-weight', 'bold')]}
            ]))

# Teams Sub-menu
elif main_page == "Teams":
    team_option = st.sidebar.radio("Select Action", ["Add Teams", "Edit Teams", "View Teams"])

    # Add Teams Page
    if team_option == "Add Teams":
        st.title("⚽ Add New Teams")

        # Multiline input for team details (group number is part of the input)
        team_input = st.text_area("Enter team details (one per line):\n<Team Name> <Registration Date DD/MM> <Group Number>", height=200)

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
                        st.success(f"✅ Team Added: {team_name}")
                    else:
                        st.error(f"❌ Failed to add Team: {response.json()['detail']}")
                else:
                    st.error(f"⚠ Invalid format for line: {team}")

    # Edit Teams Page
    elif team_option == "Edit Teams":
        st.title("⚽ Edit Teams")

        if "reload_teams" not in st.session_state:
            st.session_state.reload_teams = 0

        reload_key = f"reload_{st.session_state.get('reload_teams', 0)}"
        rankings_data = fetch_rankings()

        if "rankings" in rankings_data:
            df_teams = pd.DataFrame(rankings_data["rankings"])

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
                    st.error("⚠ Invalid date format. Please use DD/MM format.")
                
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
                        st.success(f"✅ Team Updated: {selected_team}")
                        st.session_state.reload_teams += 1
                    else:
                        st.error(f"❌ Failed to update Team: {selected_team}. {response.text}")

    # View Teams Page
    elif team_option == "View Teams":
        st.title("⚽ View Teams")

        rankings_data = fetch_rankings()
        if "rankings" in rankings_data:
            df_teams = pd.DataFrame(rankings_data["rankings"])

            # Search for specific teams
            search_term = st.text_input("🔍 Search for a team:")
            if search_term:
                df_teams = df_teams[df_teams["team_name"].str.contains(search_term, case=False)]

            # Display the teams table
            if not df_teams.empty:
                st.table(df_teams.style.set_table_styles([
                    {'selector': 'thead th', 'props': [('font-weight', 'bold')]}
                ]))

# Matches Sub-menu
elif main_page == "Matches":
    match_option = st.sidebar.radio("Select Action", ["Add Matches", "Edit Matches", "View Matches"])

    # Add Matches Page
    if match_option == "Add Matches":
        st.title("⚽ Add Matches")

        # Multiline input for match details
        match_input = st.text_area("Enter match details:\n<Team A Name> <Team B Name> <Goals A> <Goals B>", height=200)

        if st.button("Add Matches"):
            matches = match_input.split('\n')
            for match in matches:
                match_data = match.split()
                if len(match_data) == 4:
                    team_a, team_b, goals_a, goals_b = match_data
                    if team_a == team_b:
                        st.error("⚠ Team A and Team B must be different.")
                    else:
                        data = {
                            "team_a": team_a,
                            "team_b": team_b,
                            "goals_a": int(goals_a),
                            "goals_b": int(goals_b)
                        }
                        response = requests.post(f"{API_URL}/matches/", json=data)
                        if response.status_code == 200:
                            st.success(f"✅ Match Added: {team_a} vs {team_b}")
                        else:
                            st.error(f"❌ Failed to add Match: {response.json()['detail']}")
                else:
                    st.error(f"⚠ Invalid format for line: {match}")

    # Edit Matches Page
    elif match_option == "Edit Matches":
        st.title("⚽ Edit Matches")
        rankings_data = fetch_rankings()

        if "matches" in rankings_data and rankings_data["matches"]:
            df_matches = pd.DataFrame(rankings_data["matches"])

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
                        "team_a": selected_match_data["team_a"],
                        "team_b": selected_match_data["team_b"],
                        "goals_a": new_goals_a,
                        "goals_b": new_goals_b
                    }
                    response = requests.put(f"{API_URL}/matches/{selected_match_id}", json=update_data)
                    if response.status_code == 200:
                        st.success(f"✅ Match Updated: {selected_match_data['team_a']} vs {selected_match_data['team_b']}")
                    else:
                        st.error(f"❌ Failed to update Match: {response.json()['detail']}")
            else:
                st.warning("No match IDs available to select. Please ensure matches have been added.")
        else:
            st.warning("No matches available. Please add some matches first.")

    # View Matches Page
    elif match_option == "View Matches":
        st.title("⚽ View Matches")
        rankings_data = fetch_rankings()

        if "matches" in rankings_data:
            df_matches = pd.DataFrame(rankings_data["matches"])

            search_term = st.text_input("🔍 Search for a match by team name:")
            if search_term:
                df_matches = df_matches[df_matches.apply(lambda row: search_term.lower() in row["team_a"].lower() or search_term.lower() in row["team_b"].lower(), axis=1)]

            if not df_matches.empty:
                st.table(df_matches.style.set_table_styles([
                    {'selector': 'thead th', 'props': [('font-weight', 'bold')]}
                ]))

# Data Change Log Page
elif main_page == "Data Change Log":
    st.title("📝 Data Change Log")
    
    try:
        with open("data_change_log.txt", "r") as f:
            log_data = f.read()
            if log_data:
                st.text_area("📝 Data Change Log", log_data, height=400)
            else:
                st.info("No data changes logged yet.")
    except FileNotFoundError:
        st.error("Log file not found.")

# Clear All Data Page
elif main_page == "Clear All Data":
    st.title("⚠ Clear All Data")
    st.warning("This will delete all teams and matches from the database. This action cannot be undone.")

    if st.button("Clear All Data"):
        response = requests.delete(f"{API_URL}/clear/")
        if response.status_code == 200:
            st.success("✅ All data cleared from the database.")
        else:
            st.error("❌ Failed to clear the database.")
