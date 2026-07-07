import os
import json
import zipfile
import pandas as pd
import requests
import gc

# Define Cricsheet zip files in the current directory
ZIPS = ["all_json.zip"]
MATCHES_DIR = os.path.join("data", "cricsheet_matches")
DELIVERIES_DIR = os.path.join("data", "cricsheet_deliveries")
PEOPLE_DIR = os.path.join("data", "cricsheet_people")

os.makedirs(MATCHES_DIR, exist_ok=True)
os.makedirs(DELIVERIES_DIR, exist_ok=True)
os.makedirs(PEOPLE_DIR, exist_ok=True)

def download_if_missing(filename, url):
    if not os.path.exists(filename):
        print(f"Downloading {filename} from {url} (This may take a minute...)")
        response = requests.get(url, stream=True)
        response.raise_for_status()
        with open(filename, 'wb') as fd:
            for chunk in response.iter_content(chunk_size=8192):
                fd.write(chunk)
        print(f"Finished downloading {filename}.")

def load_people_mapping():
    """Returns a dict mapping Cricsheet ID -> Cricinfo ID and converts CSV to Parquet"""
    mapping = {}
    
    download_if_missing('people.csv', 'https://cricsheet.org/downloads/people.csv')
    
    if not os.path.exists('people.csv'):
        print("people.csv not found, player IDs will not be mapped.")
        return mapping
        
    df = pd.read_csv('people.csv', dtype=str)
    
    # Save a copy as Parquet in the people folder
    parquet_path = os.path.join(PEOPLE_DIR, "people.parquet")
    df.to_parquet(parquet_path, index=False)
    print(f"Saved people.csv to {parquet_path}")
    
    # The Cricsheet identifier is 'identifier', Cricinfo is 'key_cricinfo'
    for _, row in df.iterrows():
        cric_id = row.get('key_cricinfo')
        if pd.notna(cric_id):
            mapping[row['identifier']] = cric_id
    return mapping

def process_cricsheet_match(json_data, filename, global_mapping):
    match_id = filename.replace('.json', '')
    info = json_data.get("info", {})
    innings = json_data.get("innings", [])
    
    # Extract the match-specific name-to-cricsheet_id registry
    registry = info.get("registry", {}).get("people", {})
    
    # === EXTRACT METADATA (MATCH LEVEL) ===
    outcome = info.get("outcome", {})
    outcome_by = outcome.get("by", {})
    
    match_row = {
        "match_id": match_id,
        "match_type": info.get("match_type"),
        "date": info.get("dates", [None])[0],
        "gender": info.get("gender"),
        "team1": info.get("teams", [None, None])[0],
        "team2": info.get("teams", [None, None])[1] if len(info.get("teams", [])) > 1 else None,
        "toss_winner": info.get("toss", {}).get("winner"),
        "toss_decision": info.get("toss", {}).get("decision"),
        "venue": info.get("venue"),
        "city": info.get("city"),
        "outcome_winner": outcome.get("winner"),
        "outcome_by_runs": outcome_by.get("runs"),
        "outcome_by_wickets": outcome_by.get("wickets"),
        "outcome_result": outcome.get("result"), # e.g. "tie", "no result"
        "player_of_match": ", ".join([str(p) for p in info.get("player_of_match", []) if p]),
    }
    
    # === EXTRACT DELIVERIES (BALL-BY-BALL) ===
    delivery_rows = []
    
    for inning_idx, inning in enumerate(innings):
        team = inning.get("team")
        overs = inning.get("overs", [])
        
        for over in overs:
            over_num = over.get("over")
            deliveries = over.get("deliveries", [])
            
            for ball_idx, d in enumerate(deliveries):
                runs = d.get("runs", {})
                extras = d.get("extras", {})
                
                batter_name = d.get("batter")
                bowler_name = d.get("bowler")
                
                # Convert names -> Cricsheet ID -> Cricinfo ID
                batter_cs_id = registry.get(batter_name)
                bowler_cs_id = registry.get(bowler_name)
                
                batter_id = global_mapping.get(batter_cs_id) if batter_cs_id else None
                bowler_id = global_mapping.get(bowler_cs_id) if bowler_cs_id else None
                
                row = {
                    "match_id": match_id,
                    "inning": inning_idx + 1,
                    "batting_team": team,
                    "over": over_num,
                    "ball": ball_idx + 1,
                    "batter": batter_name,
                    "batter_id": batter_id,
                    "bowler": bowler_name,
                    "bowler_id": bowler_id,
                    "non_striker": d.get("non_striker"),
                    "batter_runs": runs.get("batter", 0),
                    "extras_runs": runs.get("extras", 0),
                    "total_runs": runs.get("total", 0),
                    
                    # Extras breakdown
                    "wides": extras.get("wides", 0),
                    "noballs": extras.get("noballs", 0),
                    "byes": extras.get("byes", 0),
                    "legbyes": extras.get("legbyes", 0),
                    "penalty": extras.get("penalty", 0),
                }
                
                # Check for wickets
                if "wickets" in d:
                    row["is_wicket"] = True
                    row["dismissal_kind"] = d["wickets"][0].get("kind")
                    row["player_out"] = d["wickets"][0].get("player_out")
                    fielders = d["wickets"][0].get("fielders", [])
                    row["fielders"] = ", ".join([str(f.get("name")) for f in fielders if f.get("name")])
                else:
                    row["is_wicket"] = False
                    row["dismissal_kind"] = None
                    row["player_out"] = None
                    row["fielders"] = None
                    
                delivery_rows.append(row)
                
    return match_row, delivery_rows

def convert_zips_to_parquet(global_mapping):
    for zip_name in ZIPS:
        download_if_missing(zip_name, f"https://cricsheet.org/downloads/{zip_name}")
        
        if not os.path.exists(zip_name):
            print(f"Skipping {zip_name} (failed to download)")
            continue
            
        print(f"Processing {zip_name}...")
        all_matches = []
        all_deliveries = []
        
        chunk_index = 1
        base_name = zip_name.replace('_json.zip', '')
        
        # Load existing match IDs from merged dataset to avoid redundant processing
        existing_match_ids = set()
        merged_file = os.path.join("data_merged", "cricsheet_matches", "data.parquet")
        if os.path.exists(merged_file):
            try:
                import duckdb
                con = duckdb.connect(":memory:")
                res = con.execute(f"SELECT DISTINCT match_id FROM read_parquet('{merged_file}')").fetchall()
                existing_match_ids = set(str(r[0]) for r in res if r[0] is not None)
                print(f"Found {len(existing_match_ids)} existing matches. Will skip parsing them.")
                con.close()
            except Exception as e:
                print(f"Warning: Could not read merged parquet file for existing matches: {e}")

        with zipfile.ZipFile(zip_name, 'r') as z:
            for filename in z.namelist():
                if not filename.endswith('.json'):
                    continue
                    
                match_id = filename.replace('.json', '')
                if match_id in existing_match_ids:
                    continue
                    
                with z.open(filename) as f:
                    try:
                        data = json.load(f)
                        match_row, delivery_rows = process_cricsheet_match(data, filename, global_mapping)
                        all_matches.append(match_row)
                        all_deliveries.extend(delivery_rows)
                        
                        # --- THE FIX: Micro-Batching at 100,000 rows ---
                        if len(all_deliveries) >= 100000:
                            deliv_df = pd.DataFrame(all_deliveries)
                            out_name = os.path.join(DELIVERIES_DIR, f"{base_name}_part_{chunk_index}.parquet")
                            deliv_df.to_parquet(out_name, index=False)
                            print(f"Saved chunk {chunk_index} ({len(all_deliveries)} deliveries) to {out_name}")
                            
                            # Aggressive Memory Clearing
                            del deliv_df 
                            all_deliveries.clear() 
                            gc.collect() # Force garbage collection
                            
                            chunk_index += 1
                            
                    except Exception as e:
                        print(f"Failed to process {filename}: {e}")
                        
        # Save any remaining match metadata
        if all_matches:
            matches_df = pd.DataFrame(all_matches)
            out_name = os.path.join(MATCHES_DIR, f"{base_name}_matches.parquet")
            matches_df.to_parquet(out_name, index=False)
            print(f"Saved {len(all_matches)} matches metadata to {out_name}")
            
        # Save whatever deliveries are left over in the final chunk
        if all_deliveries:
            deliv_df = pd.DataFrame(all_deliveries)
            out_name = os.path.join(DELIVERIES_DIR, f"{base_name}_part_{chunk_index}.parquet")
            deliv_df.to_parquet(out_name, index=False)
            print(f"Saved final chunk {chunk_index} ({len(all_deliveries)} deliveries) to {out_name}")

def main():
    print("Starting Cricsheet JSON -> Parquet conversion...")
    
    global_mapping = load_people_mapping()
    print(f"Loaded {len(global_mapping)} player mappings.")
    
    convert_zips_to_parquet(global_mapping)
    print("Done!")

if __name__ == "__main__":
    main()