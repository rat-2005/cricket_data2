import os
import json
import time
import pandas as pd
import time
import hmac
import hashlib
import asyncio
import argparse
from curl_cffi import requests
from dotenv import load_dotenv

load_dotenv()

KEY = "9ced54a89687e1173e91c1f225fc02abf275a119fda8a41d731d2b04dac95ff5"
BASE_URL = "https://hs-consumer-api.cricinfo.com"

# Output directories for each data layer
OUTPUT_DIR = os.path.join("data", "cricinfo_parquet")          # Ball-by-ball telemetry
METADATA_DIR = os.path.join("data", "cricinfo_metadata")       # Match info (stadium, date, result, umpires)
BATTING_DIR = os.path.join("data", "cricinfo_batting")         # Batting scorecards
BOWLING_DIR = os.path.join("data", "cricinfo_bowling")         # Bowling scorecards
PARTNERSHIPS_DIR = os.path.join("data", "cricinfo_partnerships") # Batting partnerships
FOW_DIR = os.path.join("data", "cricinfo_fow")                # Fall of wickets
INNINGS_DIR = os.path.join("data", "cricinfo_innings")         # Innings summaries

for d in [OUTPUT_DIR, METADATA_DIR, BATTING_DIR, BOWLING_DIR, PARTNERSHIPS_DIR, FOW_DIR, INNINGS_DIR]:
    os.makedirs(d, exist_ok=True)

def get_auth_token(path):
    t = f"exp={int(time.time()) + 60}~acl={path}"
    d = hmac.new(bytes.fromhex(KEY), t.encode(), hashlib.sha256).hexdigest()
    return f"{t}~hmac={d}"

def get_all_match_ids():
    """Load match IDs from events.json."""
    matches = []
    events_path = "events.json"
    if not os.path.exists(events_path):
        print("events.json not found!")
        return []
        
    with open(events_path, "r", encoding="utf-8") as f:
        urls = json.load(f)
        for url in urls:
            try:
                # URL format: http://core.espnuk.org/v2/sports/cricket/leagues/1496564/events/1496582
                parts = url.split('/')
                match_id = parts[-1]
                series_id = parts[-3] if "leagues" in url else None
                if match_id and series_id:
                    matches.append((series_id, match_id))
            except Exception:
                pass
    # Deduplicate based on match_id
    seen = set()
    unique_matches = []
    for s_id, m_id in matches:
        if m_id not in seen:
            seen.add(m_id)
            unique_matches.append((s_id, m_id))
    return unique_matches

def log_failed_match(match_id):
    with open("failed_matches.txt", "a") as f:
        f.write(f"{match_id}\n")



async def fetch_page(session, series_id, match_id, inning_number=None, from_inning_over=None, retries=3):
    if from_inning_over is None and inning_number is None:
        path = f"/v1/pages/match/commentary?lang=en&seriesId={series_id}&matchId={match_id}&sortDirection=DESC"
    else:
        path = f"/v1/pages/match/comments?lang=en&seriesId={series_id}&matchId={match_id}&inningNumber={inning_number}&commentType=ALL&sortDirection=DESC"
        if from_inning_over is not None:
            path += f"&fromInningOver={from_inning_over}"

    headers = {
        "x-hsci-auth-token": get_auth_token(path),
        "Origin": "https://www.espncricinfo.com",
        "Referer": "https://www.espncricinfo.com/",
        "Accept": "application/json",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }

    for attempt in range(retries):
        try:
            r = await session.get(f"{BASE_URL}{path}", headers=headers)
            if r.status_code == 200:
                return r.json()
            elif r.status_code == 404:
                return None # Match probably doesn't have commentary
            else:
                print(f"[{match_id}] API Error {r.status_code} on attempt {attempt+1}")
                await asyncio.sleep(2 ** attempt)
        except Exception as e:
            print(f"[{match_id}] Request failed on attempt {attempt+1}: {e}")
            await asyncio.sleep(2 ** attempt)
            
    return None

def safe_flatten(data, match_id):
    """Flatten a dict/list using json_normalize and convert complex columns to strings."""
    if isinstance(data, dict):
        data = [data]
    if not data:
        return None
    try:
        df = pd.json_normalize(data)
        for col in df.columns:
            if df[col].apply(lambda x: isinstance(x, (dict, list))).any():
                df[col] = df[col].astype(str)
        df["match_id"] = match_id
        return df
    except Exception as e:
        print(f"[{match_id}] Flatten error: {e}")
        return None

def extract_batting_scorecard(innings_list, match_id):
    """Extract batting stats from all innings into a single Parquet file."""
    all_rows = []
    for inning in innings_list:
        inning_num = inning.get("inningNumber", 0)
        team_name = inning.get("team", {}).get("longName", "Unknown")
        team_id = inning.get("team", {}).get("id", None)
        
        for b in inning.get("inningBatsmen", []):
            row = {
                "match_id": match_id,
                "inningNumber": inning_num,
                "teamName": team_name,
                "teamId": team_id,
                "playerId": b.get("player", {}).get("id"),
                "playerName": b.get("player", {}).get("longName"),
                "playerRole": b.get("playerRoleType"),
                "battingStyle": ", ".join(b.get("player", {}).get("longBattingStyles", [])),
                "battedType": b.get("battedType"),
                "runs": b.get("runs"),
                "balls": b.get("balls"),
                "minutes": b.get("minutes"),
                "fours": b.get("fours"),
                "sixes": b.get("sixes"),
                "strikeRate": b.get("strikerate"),
                "isOut": b.get("isOut"),
                "dismissalType": b.get("dismissalType"),
                "dismissalText": b.get("dismissalText", ""),
                "dismissalBowlerId": b.get("dismissalBowler", {}).get("id") if b.get("dismissalBowler") else None,
                "dismissalBowlerName": b.get("dismissalBowler", {}).get("longName") if b.get("dismissalBowler") else None,
                "fowOrder": b.get("fowOrder"),
                "fowWicketNum": b.get("fowWicketNum"),
                "fowRuns": b.get("fowRuns"),
                "fowOvers": b.get("fowOvers"),
            }
            all_rows.append(row)
    
    if all_rows:
        df = pd.DataFrame(all_rows)
        df.to_parquet(os.path.join(BATTING_DIR, f"match_{match_id}_batting.parquet"), index=False)

def extract_bowling_scorecard(innings_list, match_id):
    """Extract bowling stats from all innings into a single Parquet file."""
    all_rows = []
    for inning in innings_list:
        inning_num = inning.get("inningNumber", 0)
        team_name = inning.get("team", {}).get("longName", "Unknown")
        team_id = inning.get("team", {}).get("id", None)
        
        for bw in inning.get("inningBowlers", []):
            row = {
                "match_id": match_id,
                "inningNumber": inning_num,
                "battingTeamName": team_name,  # The team that was BATTING (bowler is from the other team)
                "battingTeamId": team_id,
                "playerId": bw.get("player", {}).get("id"),
                "playerName": bw.get("player", {}).get("longName"),
                "bowlingStyle": ", ".join(bw.get("player", {}).get("longBowlingStyles", [])),
                "bowledType": bw.get("bowledType"),
                "overs": bw.get("overs"),
                "balls": bw.get("balls"),
                "maidens": bw.get("maidens"),
                "conceded": bw.get("conceded"),
                "wickets": bw.get("wickets"),
                "economy": bw.get("economy"),
                "runsPerBall": bw.get("runsPerBall"),
                "dots": bw.get("dots"),
                "fours": bw.get("fours"),
                "sixes": bw.get("sixes"),
                "wides": bw.get("wides"),
                "noballs": bw.get("noballs"),
            }
            all_rows.append(row)
    
    if all_rows:
        df = pd.DataFrame(all_rows)
        df.to_parquet(os.path.join(BOWLING_DIR, f"match_{match_id}_bowling.parquet"), index=False)

def extract_partnerships(innings_list, match_id):
    """Extract batting partnerships from all innings."""
    all_rows = []
    for inning in innings_list:
        inning_num = inning.get("inningNumber", 0)
        team_name = inning.get("team", {}).get("longName", "Unknown")
        
        for p in inning.get("inningPartnerships", []):
            row = {
                "match_id": match_id,
                "inningNumber": inning_num,
                "teamName": team_name,
                "player1Id": p.get("player1", {}).get("id"),
                "player1Name": p.get("player1", {}).get("longName"),
                "player2Id": p.get("player2", {}).get("id"),
                "player2Name": p.get("player2", {}).get("longName"),
                "runs": p.get("runs"),
                "balls": p.get("balls"),
                "player1Runs": p.get("player1Runs"),
                "player1Balls": p.get("player1Balls"),
                "player2Runs": p.get("player2Runs"),
                "player2Balls": p.get("player2Balls"),
                "isLive": p.get("isLive"),
                "outPlayerId": p.get("outPlayer", {}).get("id") if p.get("outPlayer") else None,
            }
            all_rows.append(row)
    
    if all_rows:
        df = pd.DataFrame(all_rows)
        df.to_parquet(os.path.join(PARTNERSHIPS_DIR, f"match_{match_id}_partnerships.parquet"), index=False)

def extract_fall_of_wickets(innings_list, match_id):
    """Extract fall of wickets timeline from all innings."""
    all_rows = []
    for inning in innings_list:
        inning_num = inning.get("inningNumber", 0)
        team_name = inning.get("team", {}).get("longName", "Unknown")
        
        for fow in inning.get("inningFallOfWickets", []):
            row = {
                "match_id": match_id,
                "inningNumber": inning_num,
                "teamName": team_name,
                "dismissedPlayerId": fow.get("dismissalBatsman", {}).get("id") if fow.get("dismissalBatsman") else None,
                "dismissedPlayerName": fow.get("dismissalBatsman", {}).get("longName") if fow.get("dismissalBatsman") else None,
                "fowType": fow.get("fowType"),
                "fowOrder": fow.get("fowOrder"),
                "fowWicketNum": fow.get("fowWicketNum"),
                "fowRuns": fow.get("fowRuns"),
                "fowOvers": fow.get("fowOvers"),
                "fowBalls": fow.get("fowBalls"),
            }
            all_rows.append(row)
    
    if all_rows:
        df = pd.DataFrame(all_rows)
        df.to_parquet(os.path.join(FOW_DIR, f"match_{match_id}_fow.parquet"), index=False)

def extract_innings_summary(innings_list, match_id):
    """Extract innings-level aggregate stats."""
    all_rows = []
    for inning in innings_list:
        row = {
            "match_id": match_id,
            "inningNumber": inning.get("inningNumber"),
            "teamId": inning.get("team", {}).get("id"),
            "teamName": inning.get("team", {}).get("longName"),
            "teamAbbreviation": inning.get("team", {}).get("abbreviation"),
            "isBatted": inning.get("isBatted"),
            "runs": inning.get("runs"),
            "wickets": inning.get("wickets"),
            "overs": inning.get("overs"),
            "balls": inning.get("balls"),
            "totalOvers": inning.get("totalOvers"),
            "totalBalls": inning.get("totalBalls"),
            "minutes": inning.get("minutes"),
            "extras": inning.get("extras"),
            "byes": inning.get("byes"),
            "legbyes": inning.get("legbyes"),
            "wides": inning.get("wides"),
            "noballs": inning.get("noballs"),
            "penalties": inning.get("penalties"),
            "fours": inning.get("fours"),
            "sixes": inning.get("sixes"),
            "target": inning.get("target"),
            "lead": inning.get("lead"),
            "runsSaved": inning.get("runsSaved"),
            "catches": inning.get("catches"),
            "catchesDropped": inning.get("catchesDropped"),
            "ballsPerOver": inning.get("ballsPerOver"),
        }
        all_rows.append(row)
    
    if all_rows:
        df = pd.DataFrame(all_rows)
        df.to_parquet(os.path.join(INNINGS_DIR, f"match_{match_id}_innings.parquet"), index=False)

def extract_match_metadata(match_metadata, match_id):
    """Extract match-level metadata: stadium, teams, result, umpires, toss, dates."""
    metadata_file = os.path.join(METADATA_DIR, f"match_{match_id}_metadata.parquet")
    if not match_metadata:
        return
    try:
        # Extract key fields into a clean, flat row
        ground = match_metadata.get("ground") or {}
        series = match_metadata.get("series") or {}
        teams_raw = match_metadata.get("teams") or []
        
        # Build team info
        team1 = teams_raw[0] if len(teams_raw) > 0 else {}
        team2 = teams_raw[1] if len(teams_raw) > 1 else {}
        
        # Extract umpires
        umpires = match_metadata.get("umpires") or []
        tv_umpires = match_metadata.get("tvUmpires") or []
        match_referees = match_metadata.get("matchReferees") or []
        
        row = {
            "match_id": match_id,
            # Match basics
            "title": match_metadata.get("title"),
            "slug": match_metadata.get("slug"),
            "state": match_metadata.get("state"),
            "stage": match_metadata.get("stage"),
            "season": match_metadata.get("season"),
            "format": match_metadata.get("format"),
            "statusText": match_metadata.get("statusText"),
            "floodlit": match_metadata.get("floodlit"),
            "ballsPerOver": match_metadata.get("ballsPerOver"),
            # Dates
            "startDate": match_metadata.get("startDate"),
            "endDate": match_metadata.get("endDate"),
            "startTime": match_metadata.get("startTime"),
            # Stadium / Ground
            "groundId": ground.get("id"),
            "groundName": ground.get("longName") or ground.get("name"),
            "groundCity": ground.get("town", {}).get("name") if isinstance(ground.get("town"), dict) else None,
            "groundCountry": ground.get("country", {}).get("name") if isinstance(ground.get("country"), dict) else None,
            # Series
            "seriesId": series.get("id"),
            "seriesName": series.get("longName") or series.get("name"),
            # Teams
            "team1Id": team1.get("team", {}).get("id"),
            "team1Name": team1.get("team", {}).get("longName"),
            "team1Abbreviation": team1.get("team", {}).get("abbreviation"),
            "team1IsHome": team1.get("isHome"),
            "team2Id": team2.get("team", {}).get("id"),
            "team2Name": team2.get("team", {}).get("longName"),
            "team2Abbreviation": team2.get("team", {}).get("abbreviation"),
            "team2IsHome": team2.get("isHome"),
            # Result
            "winnerTeamId": match_metadata.get("winnerTeamId"),
            "resultStatus": match_metadata.get("resultStatus"),
            # Toss
            "tossWinnerTeamId": match_metadata.get("tossWinnerTeamId"),
            "tossWinnerChoice": match_metadata.get("tossWinnerChoice"),
            # Classification
            "internationalClassId": match_metadata.get("internationalClassId"),
            "generalClassId": match_metadata.get("generalClassId"),
            "internationalNumber": match_metadata.get("internationalNumber"),
            # Umpires
            "umpire1Id": umpires[0].get("id") if len(umpires) > 0 else None,
            "umpire1Name": umpires[0].get("longName") if len(umpires) > 0 else None,
            "umpire2Id": umpires[1].get("id") if len(umpires) > 1 else None,
            "umpire2Name": umpires[1].get("longName") if len(umpires) > 1 else None,
            "tvUmpireId": tv_umpires[0].get("id") if len(tv_umpires) > 0 else None,
            "tvUmpireName": tv_umpires[0].get("longName") if len(tv_umpires) > 0 else None,
            "matchRefereeId": match_referees[0].get("id") if len(match_referees) > 0 else None,
            "matchRefereeName": match_referees[0].get("longName") if len(match_referees) > 0 else None,
        }
        
        df = pd.DataFrame([row])
        df.to_parquet(metadata_file, index=False)
    except Exception as e:
        print(f"[{match_id}] Failed to save metadata: {e}")

async def process_match(session, series_id, match_id):
    final_file = os.path.join(OUTPUT_DIR, f"match_{match_id}_complete.parquet")
    if os.path.exists(final_file):
        return True # Skip
        
    first_data = await fetch_page(session, series_id, match_id)
    if not first_data:
        print(f"[{match_id}] No initial commentary data found.")
        return False
        
    match_metadata = first_data.get("match", {})
    
    # Fast filtering for incomplete matches
    state = match_metadata.get("state")
    stage = match_metadata.get("stage")
    if state != "POST" and stage != "FINISHED":
        print(f"[{match_id}] Match not completed yet (state: {state}, stage: {stage}). Skipping safely.")
        return True # Safe skip, don't mark as failed
        
    # === NEW FILTER: Only keep Internationals & Major T20 Leagues ===
    int_class = match_metadata.get("internationalClassId")
    series_name = str(match_metadata.get("series", {}).get("longName", "")).lower()
    
    # If intClass has a value, it's an International (Men/Women/U19)
    is_international = int_class is not None
    
    major_t20_leagues = [
        "indian premier league", "ipl", "big bash", "bbl", "pakistan super", "psl",
        "caribbean premier", "cpl", "sa20", "bangladesh premier", "bpl",
        "lanka premier", "lpl", "major league cricket", "mlc", "the hundred",
        "vitality blast", "t20 blast", "super smash", "ilt20", "super league"
    ]
    is_major_league = any(league in series_name for league in major_t20_leagues)
    
    if not is_international and not is_major_league:
        print(f"[{match_id}] Minor match ({series_name[:30]}...). Skipping.")
        # Create a tiny marker file so we don't try to fetch this again
        df = pd.DataFrame([{"match_id": match_id, "skipped": True, "reason": "minor_match"}])
        df.to_parquet(final_file, index=False)
        return True
    # ================================================================

    content_info = first_data.get("content", {})
    innings_list = content_info.get("innings", [])
    
    if not innings_list:
        print(f"[{match_id}] No innings list. Saving metadata only.")
        # Create an empty dataframe with match_id just to mark as done
        df = pd.DataFrame([{"match_id": match_id, "empty": True}])
        df.to_parquet(final_file, index=False)
        extract_match_metadata(match_metadata, match_id)
        return True
    
    # ====== EXTRACT ALL DATA LAYERS ======
    
    # 1. Match Metadata (Stadium, Teams, Toss, Date, Umpires, Result)
    extract_match_metadata(match_metadata, match_id)
    
    # 2. Batting Scorecards
    try:
        extract_batting_scorecard(innings_list, match_id)
    except Exception as e:
        print(f"[{match_id}] Batting extraction error: {e}")
    
    # 3. Bowling Scorecards
    try:
        extract_bowling_scorecard(innings_list, match_id)
    except Exception as e:
        print(f"[{match_id}] Bowling extraction error: {e}")
    
    # 4. Partnerships
    try:
        extract_partnerships(innings_list, match_id)
    except Exception as e:
        print(f"[{match_id}] Partnership extraction error: {e}")
    
    # 5. Fall of Wickets
    try:
        extract_fall_of_wickets(innings_list, match_id)
    except Exception as e:
        print(f"[{match_id}] FOW extraction error: {e}")
    
    # 6. Innings Summaries
    try:
        extract_innings_summary(innings_list, match_id)
    except Exception as e:
        print(f"[{match_id}] Innings summary extraction error: {e}")
    
    # ====== EXTRACT BALL-BY-BALL TELEMETRY ======
    
    all_comments = []
    
    for inning_num in range(1, len(innings_list) + 1):
        next_over = None
        while True:
            data = await fetch_page(session, series_id, match_id, inning_number=inning_num, from_inning_over=next_over)
            if not data:
                break
                
            if 'comments' in data:
                comments = data['comments']
                next_over_val = data.get('nextInningOver')
            else:
                content = data.get("content", {})
                comments = content.get("comments", [])
                next_over_val = content.get("nextInningOver")
                
            if not comments:
                break
                
            all_comments.extend(comments)
            if next_over_val is None:
                break
                
            next_over = next_over_val
            await asyncio.sleep(0.05) # Rate limit per match thread
            
    # Convert to Parquet
    if all_comments:
        df = pd.DataFrame(all_comments)
        df["match_id"] = match_id
        
        # We need to drop complex nested dict/list columns or cast them to string so Parquet can handle them
        for col in df.columns:
            if df[col].apply(lambda x: isinstance(x, (dict, list))).any():
                df[col] = df[col].astype(str)
                
        df.to_parquet(final_file, index=False)
    else:
        df = pd.DataFrame([{"match_id": match_id, "empty": True}])
        df.to_parquet(final_file, index=False)
        
    print(f"[{match_id}] Scraped successfully ({len(all_comments)} comments).")
    return True

async def worker(name, queue, session):
    while True:
        series_id, match_id = await queue.get()
        try:
            success = await process_match(session, series_id, match_id)
            if not success:
                log_failed_match(match_id)
        except Exception as e:
            print(f"Worker {name} failed on {match_id}: {e}")
            log_failed_match(match_id)
        finally:
            queue.task_done()
            await asyncio.sleep(0.1) # Base delay between matches

async def main(limit=None):
    matches = get_all_match_ids()
    print(f"Found {len(matches)} total matches from events.json.")
    
    # Filter out already downloaded
    existing = set([f.split('_')[1] for f in os.listdir(OUTPUT_DIR) if f.endswith('.parquet')])
    
    # Load previously failed matches if they exist to force retry them
    failed_matches = set()
    if os.path.exists("failed_matches.txt"):
        with open("failed_matches.txt", "r") as f:
            failed_matches = set(line.strip() for line in f if line.strip())
            
    # Remove existing files unless they failed previously
    pending = [(s_id, m_id) for s_id, m_id in matches if str(m_id) not in existing or str(m_id) in failed_matches]
    
    # Clear the failed_matches file since we are retrying them now
    if os.path.exists("failed_matches.txt"):
        os.remove("failed_matches.txt")
        
    print(f"{len(existing)} already downloaded. {len(pending)} remaining (including retries).")
    
    if limit:
        pending = pending[:limit]
        print(f"Limiting to {limit} matches for this run.")
        
    queue = asyncio.Queue()
    for s_id, m_id in pending:
        queue.put_nowait((s_id, m_id))
        
    # Start workers
    num_workers = 600 # Reduced to 100 to prevent Akamai 403 on AWS IPs
    async with requests.AsyncSession(impersonate="chrome") as session:
        workers = []
        for i in range(num_workers):
            task = asyncio.create_task(worker(f"W{i}", queue, session))
            workers.append(task)
            
        await queue.join()
        
        for w in workers:
            w.cancel()

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--limit", type=int, help="Limit number of matches to process")
    args = parser.parse_args()
    
    asyncio.run(main(limit=args.limit))
