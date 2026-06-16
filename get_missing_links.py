import json
import os
import psycopg2
from dotenv import load_dotenv

load_dotenv()

def get_missing_links():
    print("Loading events.json...")
    with open("events.json", "r", encoding="utf-8") as f:
        urls = json.load(f)
        
    # Map event ID to the original core API URL
    event_map = {}
    for url in urls:
        event_id = url.rstrip("/").split("/")[-1]
        event_map[event_id] = url

    print("Connecting to database...")
    conn = psycopg2.connect(os.environ.get("DATABASE_URL"))
    cur = conn.cursor()
    
    print("Fetching delivery coverage...")
    cur.execute("SELECT DISTINCT competition_id FROM cricket.deliveries")
    comp_ids_with_deliveries = set(row[0] for row in cur.fetchall())
    
    print("Fetching competition formats...")
    cur.execute("SELECT event_id, id, class_name FROM cricket.competitions")
    db_events = {}
    for row in cur.fetchall():
        db_events[str(row[0])] = {'comp_id': row[1], 'class': row[2]}
        
    t20i_urls = []
    test_urls = []
    odi_urls = []
    other_urls = []
    
    print("Categorizing missing URLs...")
    for event_id, url in event_map.items():
        if event_id in db_events:
            comp_id = db_events[event_id]['comp_id']
            # If the competition exists but has NO deliveries, it's a missing URL
            if comp_id not in comp_ids_with_deliveries:
                cls = db_events[event_id]['class']
                if cls == 'T20I':
                    t20i_urls.append(url)
                elif cls == 'Test':
                    test_urls.append(url)
                elif cls == 'ODI':
                    odi_urls.append(url)
                else:
                    other_urls.append(url)
        else:
            # If the event isn't even in the competitions table, it's completely missing
            other_urls.append(url)
            
    print(f"Missing T20I: {len(t20i_urls)}")
    print(f"Missing Test: {len(test_urls)}")
    print(f"Missing ODI: {len(odi_urls)}")
    print(f"Missing Other: {len(other_urls)}")
    print(f"Total Missing: {len(t20i_urls) + len(test_urls) + len(odi_urls) + len(other_urls)}")
    
    print("Writing to missing_urls_lists.py...")
    with open("missing_urls_lists.py", "w", encoding="utf-8") as f:
        f.write(f"t20i_urls = {t20i_urls}\n\n")
        f.write(f"test_urls = {test_urls}\n\n")
        f.write(f"odi_urls = {odi_urls}\n\n")
        f.write(f"other_urls = {other_urls}\n\n")
    
    print("Done! Open missing_urls_lists.py to see the lists.")

if __name__ == "__main__":
    get_missing_links()
