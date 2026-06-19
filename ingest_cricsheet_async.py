import asyncio
import asyncpg
import json
import zipfile
import requests
import io
import os
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.environ.get('DATABASE_URL')

def is_match_covered(covered_matches, match_type, start_date, teams):
    if match_type == 'MD': match_type = 'Test'
    t1, t2 = teams[0].lower(), teams[1].lower()
    
    for fmt, date_str, name in covered_matches:
        if fmt == match_type and date_str == start_date:
            if (t1 in name and t2 in name):
                return True
    return False

def download_file(url, filename):
    print(f"Downloading {filename}...")
    response = requests.get(url, stream=True)
    with open(filename, 'wb') as fd:
        for chunk in response.iter_content(chunk_size=128):
            fd.write(chunk)

async def process_zip_file(pool, zip_filename, mapping, covered_matches):
    print(f"Extracting and processing {zip_filename}...")
    
    match_inserts = []
    delivery_inserts = []
    
    # Read sequentially from ZIP, it's very fast, we will insert concurrently
    with zipfile.ZipFile(zip_filename, 'r') as z:
        for filename in z.namelist():
            if not filename.endswith('.json'): continue
            
            with z.open(filename) as f:
                data = json.load(f)
            
            info = data.get('info', {})
            match_id = filename.split('.')[0]
            match_type = info.get('match_type')
            
            dates = info.get('dates', [])
            start_date = dates[0] if dates else None
            
            teams = info.get('teams', [])
            if len(teams) < 2: continue
            
            if is_match_covered(covered_matches, match_type, start_date, teams):
                continue
                
            gender = info.get('gender')
            start_date_obj = None
            if start_date:
                try:
                    start_date_obj = datetime.strptime(start_date, '%Y-%m-%d').date()
                except ValueError:
                    pass
                    
            match_inserts.append((match_id, start_date_obj, match_type, teams[0], teams[1], gender))
            
            for innings_idx, innings_dict in enumerate(data.get('innings', [])):
                for over_dict in innings_dict.get('overs', []):
                    over_num = over_dict.get('over')
                    for ball_num_0idx, ball_data in enumerate(over_dict.get('deliveries', [])):
                        ball_num = ball_num_0idx + 1
                        
                        batter_name = ball_data.get('batter')
                        bowler_name = ball_data.get('bowler')
                        
                        registry = info.get('registry', {}).get('people', {})
                        batter_reg_id = registry.get(batter_name)
                        bowler_reg_id = registry.get(bowler_name)
                        
                        batter_id = mapping.get(batter_reg_id)
                        bowler_id = mapping.get(bowler_reg_id)
                        
                        if not batter_id or not bowler_id:
                            continue

                        runs = ball_data.get('runs', {})
                        batsman_runs = runs.get('batter', 0)
                        extras = runs.get('extras', 0)
                        runs_scored = batsman_runs + extras
                        
                        extra_details = ball_data.get('extras', {})
                        is_wide = 'wides' in extra_details
                        is_no_ball = 'noballs' in extra_details
                        is_bye = 'byes' in extra_details
                        is_leg_bye = 'legbyes' in extra_details
                        
                        # Boundary check isn't trivial in basic JSON without checking runs, but rough approx:
                        is_boundary = (batsman_runs in [4, 6])
                        
                        dismissal_type = None
                        if 'wickets' in ball_data:
                            dismissal_type = ball_data['wickets'][0].get('kind')
                            
                        delivery_inserts.append((
                            match_id, innings_idx + 1, over_num, ball_num, 
                            batter_id, bowler_id, runs_scored, batsman_runs,
                            is_wide, is_no_ball, is_bye, is_leg_bye, is_boundary, dismissal_type
                        ))

    print(f"Found {len(match_inserts)} missing matches to insert from {zip_filename}!")
    
    if not match_inserts: return
    
    async with pool.acquire() as conn:
        print(f"Inserting matches for {zip_filename}...")
        await conn.executemany("""
            INSERT INTO cricket.cricsheet_matches (id, match_date, format, team1, team2, gender)
            VALUES ($1, $2::date, $3, $4, $5, $6)
            ON CONFLICT (id) DO NOTHING
        """, match_inserts)
        
        print(f"Inserting deliveries for {zip_filename}...")
        # Batch insert deliveries
        batch_size = 50000
        for i in range(0, len(delivery_inserts), batch_size):
            batch = delivery_inserts[i:i+batch_size]
            await conn.executemany("""
                INSERT INTO cricket.cricsheet_deliveries 
                (match_id, innings, over_number, ball_number, batsman_id, bowler_id, 
                 runs_scored, batsman_runs, is_wide, is_no_ball, is_bye, is_leg_bye, is_boundary, dismissal_type)
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14)
            """, batch)
            print(f"Inserted batch of {len(batch)} deliveries from {zip_filename}")

async def main():
    import csv
    
    print("Loading people registry...")
    mapping = {}
    with open('people.csv', 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row['key_cricinfo']:
                mapping[row['identifier']] = row['key_cricinfo']
            
    pool = await asyncpg.create_pool(DATABASE_URL)
    
    async with pool.acquire() as conn:
        print("Loading existing Cricinfo matches...")
        matches_records = await conn.fetch("""
            SELECT c.class_name as format, e.date::date as match_date, e.name
            FROM cricket.competitions c
            JOIN cricket.events e ON c.event_id = e.id
        """)
        covered_matches = [(r['format'], str(r['match_date']), r['name'].lower()) for r in matches_records]
    
    urls = [
        ('tests_json.zip', 'https://cricsheet.org/downloads/tests_json.zip'),
        ('odis_json.zip', 'https://cricsheet.org/downloads/odis_json.zip'),
        ('t20s_json.zip', 'https://cricsheet.org/downloads/t20s_json.zip')
    ]
    
    for filename, url in urls:
        if not os.path.exists(filename):
            download_file(url, filename)
    
    tasks = []
    for filename, url in urls:
        tasks.append(process_zip_file(pool, filename, mapping, covered_matches))
        
    await asyncio.gather(*tasks)
    await pool.close()
    print("All done!")

if __name__ == '__main__':
    asyncio.run(main())
