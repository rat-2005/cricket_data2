import os
import json
import psycopg2
from psycopg2.extras import execute_values
from dotenv import load_dotenv

load_dotenv()

DB_URL = os.environ.get("DATABASE_URL")

def create_table():
    conn = psycopg2.connect(DB_URL, sslmode='require')
    cur = conn.cursor()
    
    cur.execute("""
        CREATE SCHEMA IF NOT EXISTS cricket;
        
        CREATE TABLE IF NOT EXISTS cricket.icc_pitch_data (
            id SERIAL PRIMARY KEY,
            icc_game_id VARCHAR(50),
            inning_no INT,
            over_no VARCHAR(10),
            ball_number INT,
            bowler_name VARCHAR(100),
            batsman_name VARCHAR(100),
            ball_speed VARCHAR(20),
            shot_type VARCHAR(100),
            ball_line_length VARCHAR(255),
            uid BIGINT,
            oid FLOAT,
            zad VARCHAR(50),
            is_wicket BOOLEAN,
            venue VARCHAR(255),
            format VARCHAR(100),
            tournament VARCHAR(255),
            match_date VARCHAR(50)
        );
        
        CREATE INDEX IF NOT EXISTS idx_icc_pitch_game ON cricket.icc_pitch_data(icc_game_id);
    """)
    conn.commit()
    cur.close()
    conn.close()
    print("Table cricket.icc_pitch_data created/verified successfully.")

def load_master_schedule():
    schedule_path = os.path.join(INPUT_DIR, "icc_master_schedule.json")
    if not os.path.exists(schedule_path):
        print("Warning: Master schedule not found. Metadata will be empty.")
        return {}
        
    with open(schedule_path, 'r', encoding='utf-8') as f:
        matches = json.load(f)
        
    meta_dict = {}
    for match in matches:
        game_id = str(match.get('match_id'))
        meta_dict[game_id] = {
            'venue': match.get('venue', ''),
            'format': match.get('match_type', ''),
            'tournament': match.get('tour_name', '') or match.get('series_name', ''),
            'match_date': match.get('match_date_local', '')
        }
    print(f"Loaded metadata for {len(meta_dict)} matches.")
    return meta_dict

INPUT_DIR = "d:/cricket/fresh_data/icc_json"

def ingest_data():
    conn = psycopg2.connect(DB_URL, sslmode='require')
    cur = conn.cursor()
    
    meta_dict = load_master_schedule()
    
    # We will process in batches for extremely fast inserts
    batch_size = 50000
    insert_query = """
        INSERT INTO cricket.icc_pitch_data (
            icc_game_id, inning_no, over_no, ball_number, bowler_name, batsman_name,
            ball_speed, shot_type, ball_line_length, uid, oid, zad, is_wicket,
            venue, format, tournament, match_date
        ) VALUES %s
    """
    
    values_to_insert = []
    total_inserted = 0
    
    files = [f for f in os.listdir(INPUT_DIR) if f.startswith('icc_game_') and f.endswith('.json')]
    print(f"Found {len(files)} innings files to process.")
    
    for idx, filename in enumerate(files):
        # Extract game_id and inning_no from filename: icc_game_123_inning_1.json
        parts = filename.replace('.json', '').split('_')
        try:
            game_id = parts[2]
            inning_no = int(parts[4])
        except (IndexError, ValueError):
            continue
            
        filepath = os.path.join(INPUT_DIR, filename)
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
        except Exception:
            continue
            
        if not data or not data.get('data'):
            continue
            
        commentary = data.get('data', {}).get('Commentary', [])
        
        meta = meta_dict.get(game_id, {})
        venue = meta.get('venue', '')
        fmt = meta.get('format', '')
        tour = meta.get('tournament', '')
        mdate = meta.get('match_date', '')
        
        for ball in commentary:
            # Only store actual deliveries (must have a batsman and bowler)
            batsman = ball.get('Batsman_Name', '').strip()
            bowler = ball.get('Bowler_Name', '').strip()
            
            if not batsman or not bowler:
                continue
                
            # Safely handle integers/floats
            try:
                ball_num = int(ball.get('Ball_Number', 0))
            except ValueError:
                ball_num = 0
                
            uid = ball.get('UID')
            if uid == "": uid = None
            elif uid is not None: uid = int(uid)
            
            oid = ball.get('OID')
            if oid == "": oid = None
            elif oid is not None: oid = float(oid)
            
            is_wicket = ball.get('Iswicket')
            if is_wicket is None:
                # Fallback to checking detail
                is_wicket = (ball.get('Detail', '') == 'W')
            
            val = (
                game_id,
                inning_no,
                ball.get('Over', ''),
                ball_num,
                bowler,
                batsman,
                ball.get('Ball_Speed', ''),
                ball.get('Shot_Type', ''),
                ball.get('Ball_Line_Length', ''),
                uid,
                oid,
                ball.get('ZAD', ''),
                is_wicket,
                venue,
                fmt,
                tour,
                mdate
            )
            values_to_insert.append(val)
            
            if len(values_to_insert) >= batch_size:
                execute_values(cur, insert_query, values_to_insert)
                conn.commit()
                total_inserted += len(values_to_insert)
                print(f"Inserted {total_inserted} balls...")
                values_to_insert = []
                
        if (idx + 1) % 500 == 0:
            print(f"Processed {idx + 1}/{len(files)} files...")
            
    # Insert any remaining values
    if values_to_insert:
        execute_values(cur, insert_query, values_to_insert)
        conn.commit()
        total_inserted += len(values_to_insert)
        
    cur.close()
    conn.close()
    print(f"SUCCESS! Total balls inserted into database: {total_inserted}")

if __name__ == "__main__":
    create_table()
    ingest_data()
