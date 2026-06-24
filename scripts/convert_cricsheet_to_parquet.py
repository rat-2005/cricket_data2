import os
import json
import zipfile
import pandas as pd

# Define Cricsheet zip files in the current directory
ZIPS = ["odis_json.zip", "t20s_json.zip", "tests_json.zip"]
OUTPUT_DIR = os.path.join("data", "cricsheet_parquet")
os.makedirs(OUTPUT_DIR, exist_ok=True)

def process_cricsheet_match(json_data, filename):
    match_id = filename.replace('.json', '')
    info = json_data.get("info", {})
    innings = json_data.get("innings", [])
    
    rows = []
    
    for inning_idx, inning in enumerate(innings):
        team = inning.get("team")
        overs = inning.get("overs", [])
        
        for over in overs:
            over_num = over.get("over")
            deliveries = over.get("deliveries", [])
            
            for ball_idx, d in enumerate(deliveries):
                runs = d.get("runs", {})
                extras = d.get("extras", {})
                
                row = {
                    "match_id": match_id,
                    "match_type": info.get("match_type"),
                    "date": info.get("dates", [None])[0],
                    "gender": info.get("gender"),
                    "inning": inning_idx + 1,
                    "batting_team": team,
                    "over": over_num,
                    "ball": ball_idx + 1,
                    "batter": d.get("batter"),
                    "bowler": d.get("bowler"),
                    "non_striker": d.get("non_striker"),
                    "batter_runs": runs.get("batter", 0),
                    "extras_runs": runs.get("extras", 0),
                    "total_runs": runs.get("total", 0),
                }
                
                # Check for wickets
                if "wickets" in d:
                    row["is_wicket"] = True
                    row["dismissal_kind"] = d["wickets"][0].get("kind")
                    row["player_out"] = d["wickets"][0].get("player_out")
                else:
                    row["is_wicket"] = False
                    row["dismissal_kind"] = None
                    row["player_out"] = None
                    
                rows.append(row)
                
    return rows

def convert_zips_to_parquet():
    for zip_name in ZIPS:
        if not os.path.exists(zip_name):
            print(f"Skipping {zip_name} (not found)")
            continue
            
        print(f"Processing {zip_name}...")
        all_rows = []
        
        with zipfile.ZipFile(zip_name, 'r') as z:
            for filename in z.namelist():
                if not filename.endswith('.json'):
                    continue
                    
                # Read the JSON directly out of the ZIP without extracting to disk
                with z.open(filename) as f:
                    try:
                        data = json.load(f)
                        rows = process_cricsheet_match(data, filename)
                        all_rows.extend(rows)
                    except Exception as e:
                        print(f"Failed to process {filename}: {e}")
                        
        if all_rows:
            df = pd.DataFrame(all_rows)
            out_name = os.path.join(OUTPUT_DIR, zip_name.replace('_json.zip', '.parquet'))
            df.to_parquet(out_name, index=False)
            print(f"Saved {len(all_rows)} deliveries to {out_name}")

if __name__ == "__main__":
    print("Starting Cricsheet JSON -> Parquet conversion...")
    convert_zips_to_parquet()
    print("Done!")
