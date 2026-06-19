import os
import sys
import requests
import psycopg2
from dotenv import load_dotenv

def ingest_match(match_id):
    load_dotenv()
    api_key = os.environ.get("SPORTRADAR_API_KEY", "").strip('" ')
    db_url = os.environ.get('DATABASE_URL')
    
    if not api_key:
        print("Error: SPORTRADAR_API_KEY not found in .env")
        return
        
    url = f"https://api.sportradar.com/cricket-t2/en/matches/{match_id}/timeline.json?api_key={api_key}"
    print(f"Fetching timeline for {match_id}...")
    
    response = requests.get(url)
    if response.status_code != 200:
        print(f"API Error {response.status_code}: {response.text[:200]}")
        return
        
    data = response.json()
    timeline = data.get('timeline', [])
    deliveries = [t for t in timeline if t.get('type') == 'delivery']
    
    print(f"Found {len(deliveries)} deliveries in timeline.")
    if not deliveries:
        return
        
    conn = psycopg2.connect(db_url)
    cur = conn.cursor()
    
    inserted_count = 0
    
    for d in deliveries:
        over_number = d.get('over')
        ball_number = d.get('delivery')
        
        bp = d.get('bowling_params', {})
        batp = d.get('batting_params', {})
        fp = d.get('fielding_params', {})
        
        # Only ingest if we have pitch coordinates or we want all?
        # The user wants line and length, so pitch_x/pitch_y are most important, but they asked for all
        pitch_x = bp.get('pitch_x')
        pitch_y = bp.get('pitch_y')
        
        if pitch_x is None and pitch_y is None:
            # Maybe skip if no coordinate data?
            pass
            
        bowler = bp.get('bowler', {})
        striker = batp.get('striker', {})
        non_striker = batp.get('non_striker', {})
        
        try:
            cur.execute("""
                INSERT INTO cricket.sportradar_pitch_data (
                    sr_match_id, over_number, ball_number,
                    bowler_id, bowler_name, bowler_country,
                    striker_id, striker_name, striker_country,
                    non_striker_id, non_striker_name,
                    bowling_from, delivery_type, beat_bat, pitch_x, pitch_y, extra_runs_conceded, bowling_end,
                    connect, shot_type, hit_to_boundary, runs_scored, angle_traversed, zone_played_in,
                    runs_saved, overthrows, run_out_missed, catch_dropped, fielded, fielded_wicket_keeper, misfielded, stumping_missed, pressure_applied
                ) VALUES (
                    %s, %s, %s,
                    %s, %s, %s,
                    %s, %s, %s,
                    %s, %s,
                    %s, %s, %s, %s, %s, %s, %s,
                    %s, %s, %s, %s, %s, %s,
                    %s, %s, %s, %s, %s, %s, %s, %s, %s
                ) ON CONFLICT (sr_match_id, over_number, ball_number) DO NOTHING;
            """, (
                match_id, over_number, ball_number,
                bowler.get('id'), bowler.get('name'), bowler.get('country_code'),
                striker.get('id'), striker.get('name'), striker.get('country_code'),
                non_striker.get('id'), non_striker.get('name'),
                bp.get('bowling_from'), bp.get('delivery_type'), bp.get('beat_bat'), pitch_x, pitch_y, bp.get('extra_runs_conceded'), bp.get('bowling_end'),
                batp.get('connect'), batp.get('shot_type'), batp.get('hit_to_boundary'), batp.get('runs_scored'), batp.get('angle_traversed'), batp.get('zone_played_in'),
                fp.get('runs_saved'), fp.get('overthrows'), fp.get('run_out_missed'), fp.get('catch_dropped'), fp.get('fielded'), fp.get('fielded_wicket_keeper'), fp.get('misfielded'), fp.get('stumping_missed'), fp.get('pressure_applied')
            ))
            if cur.rowcount > 0:
                inserted_count += 1
        except Exception as e:
            print(f"Error inserting over {over_number} ball {ball_number}: {e}")
            conn.rollback()
            continue
            
    conn.commit()
    conn.close()
    print(f"Successfully inserted {inserted_count} new deliveries with pitch data for {match_id}!")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python fetch_sportradar.py sr:match:XXXXXX")
    else:
        ingest_match(sys.argv[1])
