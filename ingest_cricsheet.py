import os
import json
import urllib.request
import zipfile
import csv
import psycopg2
from psycopg2.extras import execute_batch
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

DB_URL = os.environ.get("DATABASE_URL")

def download_file(url, filename):
    print(f"Downloading {url}...")
    urllib.request.urlretrieve(url, filename)

def load_people_mapping():
    print("Loading people.csv mapping...")
    mapping = {}
    with open('people.csv', 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row['key_cricinfo']:
                mapping[row['identifier']] = row['key_cricinfo']
    return mapping

def get_db_covered_matches(conn):
    print("Fetching covered matches from DB...")
    cur = conn.cursor()
    # Find all matches that already have deliveries
    cur.execute("""
        SELECT DISTINCT c.class_name, e.date::date, e.name
        FROM cricket.competitions c
        JOIN cricket.events e ON c.event_id = e.id
        JOIN cricket.deliveries d ON c.id = d.competition_id
    """)
    rows = cur.fetchall()
    covered = set()
    for row in rows:
        fmt, date_obj, name = row
        if fmt == 'T20I': fmt = 'T20'
        elif fmt == 'Test': fmt = 'MD' # Cricsheet uses MD for test matches, wait actually Cricsheet JSON says "Test" in match_type
        # Let's just use the exact DB format and map later
        covered.add((fmt, str(date_obj), name.lower()))
    return covered

def is_match_covered(covered_matches, match_type, start_date, teams):
    if match_type == 'MD': match_type = 'Test'
    t1, t2 = teams[0].lower(), teams[1].lower()
    
    # Try different combinations
    for fmt, date_str, name in covered_matches:
        if fmt == match_type and date_str == start_date:
            if (t1 in name and t2 in name):
                return True
    return False

def ingest_cricsheet_zip(zip_filename, mapping, covered_matches, conn):
    print(f"Extracting and processing {zip_filename}...")
    
    match_inserts = []
    delivery_inserts = []
    
    with zipfile.ZipFile(zip_filename, 'r') as z:
        for filename in z.namelist():
            if not filename.endswith('.json'): continue
            
            with z.open(filename) as f:
                data = json.load(f)
                
            info = data.get('info', {})
            gender = info.get('gender')
            if gender != 'male': continue # Only ingest men's matches for now
            
            match_type = info.get('match_type')
            if match_type not in ('Test', 'ODI', 'T20', 'T20I'): continue
            if match_type == 'T20': match_type = 'T20I'
            
            dates = info.get('dates', [])
            if not dates: continue
            start_date = dates[0]
            
            teams = info.get('teams', [])
            if len(teams) != 2: continue
            
            # Check if covered
            if is_match_covered(covered_matches, match_type, start_date, teams):
                continue
                
            match_id = filename.split('.')[0]
            
            match_inserts.append((
                match_id, start_date, match_type, teams[0], teams[1], gender
            ))
            
            # Parse deliveries
            for innings_idx, innings_dict in enumerate(data.get('innings', [])):
                for over_dict in innings_dict.get('overs', []):
                    over_num = over_dict.get('over')
                    for ball_num_0idx, ball_data in enumerate(over_dict.get('deliveries', [])):
                        ball_num = ball_num_0idx + 1
                        
                        batsman_cricsheet = ball_data.get('batter')
                        bowler_cricsheet = ball_data.get('bowler')
                        
                        registry = info.get('registry', {}).get('people', {})
                        batsman_reg_id = registry.get(batsman_cricsheet)
                        bowler_reg_id = registry.get(bowler_cricsheet)
                        
                        batsman_id = mapping.get(batsman_reg_id)
                        bowler_id = mapping.get(bowler_reg_id)
                        
                        if not batsman_id or not bowler_id:
                            continue # Skip ball if we can't map players to Cricinfo
                            
                        runs = ball_data.get('runs', {})
                        batsman_runs = runs.get('batter', 0)
                        total_runs = runs.get('total', 0)
                        
                        extras = ball_data.get('extras', {})
                        is_wide = 'wides' in extras
                        is_no_ball = 'noballs' in extras
                        is_bye = 'byes' in extras
                        is_leg_bye = 'legbyes' in extras
                        
                        is_boundary = 'non_boundary' not in runs and batsman_runs in (4, 6)
                        
                        dismissal_type = None
                        if 'wickets' in ball_data:
                            dismissal_type = ball_data['wickets'][0].get('kind')
                            
                        delivery_inserts.append((
                            match_id, innings_idx + 1, over_num, ball_num,
                            batsman_id, bowler_id, total_runs, batsman_runs,
                            is_wide, is_no_ball, is_bye, is_leg_bye, is_boundary, dismissal_type
                        ))

    print(f"Found {len(match_inserts)} missing matches to insert from {zip_filename}!")
    
    if not match_inserts: return
    
    cur = conn.cursor()
    print("Inserting matches...")
    execute_batch(cur, """
        INSERT INTO cricket.cricsheet_matches (id, match_date, format, team1, team2, gender)
        VALUES (%s, %s, %s, %s, %s, %s)
        ON CONFLICT (id) DO NOTHING
    """, match_inserts)
    
    print("Inserting deliveries...")
    execute_batch(cur, """
        INSERT INTO cricket.cricsheet_deliveries 
        (match_id, innings, over_number, ball_number, batsman_id, bowler_id, 
         runs_scored, batsman_runs, is_wide, is_no_ball, is_bye, is_leg_bye, is_boundary, dismissal_type)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    """, delivery_inserts)
    conn.commit()

def main():
    if not os.path.exists('people.csv'):
        download_file('https://cricsheet.org/register/people.csv', 'people.csv')
    
    mapping = load_people_mapping()
    
    conn = psycopg2.connect(DB_URL)
    covered_matches = get_db_covered_matches(conn)
    
    urls = [
        ('tests_json.zip', 'https://cricsheet.org/downloads/tests_json.zip'),
        ('odis_json.zip', 'https://cricsheet.org/downloads/odis_json.zip'),
        ('t20s_json.zip', 'https://cricsheet.org/downloads/t20s_json.zip')
    ]
    
    for filename, url in urls:
        if not os.path.exists(filename):
            download_file(url, filename)
        ingest_cricsheet_zip(filename, mapping, covered_matches, conn)
        
    print("All Cricsheet data ingested successfully!")

if __name__ == '__main__':
    main()
