import json
import re
from collections import Counter

def analyze_events_json():
    filename = 'events.json'
    try:
        with open(filename, 'r') as f:
            urls = json.load(f)
    except FileNotFoundError:
        print(f"Error: Could not find '{filename}'")
        return
    except json.JSONDecodeError:
        print(f"Error: '{filename}' is not valid JSON")
        return

    # 1. Total URLs in the file
    total_urls = len(urls)
    
    # 2. Total unique URLs (ignoring exact duplicates)
    unique_urls = len(set(urls))
    
    # 3. Total unique Event IDs (extracted from the URL)
    # The URL pattern looks like: .../events/1103267
    event_ids = []
    for url in urls:
        match = re.search(r'/events/(\d+)', url)
        if match:
            event_ids.append(match.group(1))
            
    unique_ids = len(set(event_ids))
    
    print("-" * 50)
    print("ANALYSIS OF EVENTS.JSON")
    print("-" * 50)
    print(f"Total URLs in file:       {total_urls:,}")
    print(f"Unique URLs:              {unique_urls:,}")
    print(f"Unique Event IDs:         {unique_ids:,}")
    print("-" * 50)
    print(f"This means there are {total_urls - unique_ids:,} duplicate endpoints")
    print("pointing to the same matches.")
    
    # Find a quick example of a duplicate to show the user
    counts = Counter(event_ids)
    duplicates = [(eid, count) for eid, count in counts.items() if count > 1]
    
    if duplicates:
        sample_id = duplicates[0][0]
        sample_urls = [u for u in urls if f"/events/{sample_id}" in u]
        print("\nExample of a duplicate event ID:")
        print(f"Event ID {sample_id} appears {duplicates[0][1]} times:")
        for u in sample_urls:
            print(f" -> {u}")

if __name__ == "__main__":
    analyze_events_json()
