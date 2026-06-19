import psycopg2
import os
import pandas as pd
from dotenv import load_dotenv

load_dotenv()
conn = psycopg2.connect(os.environ.get('DATABASE_URL'))

# Target teams mapping team_id -> team_name
teams = {
    '1': 'England',
    '2': 'Australia',
    '3': 'South Africa',
    '4': 'West Indies',
    '5': 'New Zealand',
    '6': 'India',
    '7': 'Pakistan',
    '8': 'Sri Lanka',
    '25': 'Bangladesh',
    '40': 'Afghanistan'
}

print("Counting international matches for top 10 teams...\n")

results = []
for team_id, team_name in teams.items():
    # Count Cricinfo matches using team_id
    cricinfo_query = """
    SELECT COUNT(DISTINCT c.id) as match_count
    FROM cricket.competitions c
    JOIN cricket.competitors comp ON comp.competition_id = c.id
    WHERE comp.team_id = %s AND c.class_name IN ('Test', 'ODI', 'T20I', 'Twenty20')
    """
    df_ci = pd.read_sql_query(cricinfo_query, conn, params=(team_id,))
    cricinfo_matches = df_ci['match_count'].iloc[0]
    
    # Count Cricsheet matches using team_name
    cricsheet_query = """
    SELECT COUNT(DISTINCT id) as match_count
    FROM cricket.cricsheet_matches 
    WHERE (team1 = %s OR team2 = %s) AND format IN ('Test', 'ODI', 'T20', 'MD')
    """
    df_cs = pd.read_sql_query(cricsheet_query, conn, params=(team_name, team_name))
    cricsheet_matches = df_cs['match_count'].iloc[0]
    
    total = cricinfo_matches + cricsheet_matches
    results.append({
        'Team': team_name,
        'Team ID': team_id,
        'Cricinfo Matches': cricinfo_matches,
        'Cricsheet Matches': cricsheet_matches,
        'Total International Matches': total
    })

# Convert to DataFrame for nice printing
df_results = pd.DataFrame(results)
# Sort by total descending
df_results = df_results.sort_values(by='Total International Matches', ascending=False).reset_index(drop=True)
print(df_results.to_string())

# Optional: save to CSV
df_results.to_csv('team_international_matches.csv', index=False)
print("\nResults saved to team_international_matches.csv")
