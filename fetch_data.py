import urllib.request
import json
import os
import sys
import threading
import concurrent.futures

def fetch_json(url):
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=10) as response:
            return json.loads(response.read().decode('utf-8'))
    except Exception as e:
        return None

def fetch_events_for_league(league_url):
    events_found = []
    seasons_url = f"{league_url}/seasons?limit=1000"
    seasons_data = fetch_json(seasons_url)
    
    if seasons_data and 'items' in seasons_data:
        for season_item in seasons_data['items']:
            season_ref = season_item.get('$ref')
            if season_ref:
                season_clean = season_ref.split('?')[0]
                events_url = f"{season_clean}/events?limit=1000"
                events_data = fetch_json(events_url)
                if events_data and 'items' in events_data:
                    for event_item in events_data['items']:
                        event_ref = event_item.get('$ref')
                        if event_ref:
                            events_found.append(event_ref.split('?')[0])
    return events_found

def main():
    log_file = open('progress.log', 'w')
    def log(msg):
        print(msg)
        log_file.write(msg + '\n')
        log_file.flush()

    # Load existing leagues
    existing_leagues_list = []
    if os.path.exists('leagues.json'):
        with open('leagues.json', 'r') as f:
            existing_leagues_list = json.load(f)
    
    existing_leagues_set = set(existing_leagues_list)
    log(f"Loaded {len(existing_leagues_list)} existing leagues from file.")

    # Always fetch leagues to check for new ones
    log("Checking for new leagues from page 1 to 7...")
    new_leagues_count = 0
    for page in range(1, 8):
        url = f"http://core.espnuk.org/v2/sports/cricket/leagues?limit=1000&page={page}"
        data = fetch_json(url)
        if data and 'items' in data:
            for item in data['items']:
                league_ref = item.get('$ref')
                if league_ref:
                    league_clean = league_ref.split('?')[0]
                    if league_clean not in existing_leagues_set:
                        existing_leagues_set.add(league_clean)
                        existing_leagues_list.append(league_clean)
                        new_leagues_count += 1
                        
    if new_leagues_count > 0:
        log(f"Found {new_leagues_count} new leagues! Saving updated leagues.json.")
        with open('leagues.json', 'w') as f:
            json.dump(existing_leagues_list, f, indent=2)
    else:
        log("No new leagues found.")

    total_leagues = len(existing_leagues_list)

    # Load existing events
    existing_events_list = []
    if os.path.exists('events.json'):
        with open('events.json', 'r') as f:
            existing_events_list = json.load(f)
            
    existing_events_set = set(existing_events_list)
    log(f"Loaded {len(existing_events_list)} existing events from file.")

    save_lock = threading.Lock()
    new_events_added_this_run = 0
    
    log("Fetching events for all leagues concurrently to find new matches...")
    with concurrent.futures.ThreadPoolExecutor(max_workers=50) as executor:
        future_to_league = {executor.submit(fetch_events_for_league, league): league for league in existing_leagues_list}
        
        completed = 0
        for future in concurrent.futures.as_completed(future_to_league):
            league = future_to_league[future]
            try:
                events = future.result()
                if events:
                    with save_lock:
                        for ev in events:
                            if ev not in existing_events_set:
                                existing_events_set.add(ev)
                                existing_events_list.append(ev)
                                new_events_added_this_run += 1
            except Exception as exc:
                log(f"League {league} generated an exception: {exc}")
            
            completed += 1
            if completed % 100 == 0:
                with save_lock:
                    total_evs = len(existing_events_list)
                    if new_events_added_this_run > 0:
                        with open('events.json', 'w') as f:
                            json.dump(existing_events_list, f, indent=2)
                log(f"Processed {completed}/{total_leagues} leagues. Total matches: {total_evs} ({new_events_added_this_run} new so far).")

    log(f"Final total events (matches) in database: {len(existing_events_list)}")
    log(f"Total NEW matches added this run: {new_events_added_this_run}")

    if new_events_added_this_run > 0:
        with open('events.json', 'w') as f:
            json.dump(existing_events_list, f, indent=2)
        log("Finished! New matches saved to events.json")
    else:
        log("Finished! No new matches were found.")
        
    log_file.close()

if __name__ == '__main__':
    main()
