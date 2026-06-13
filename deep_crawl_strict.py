import json
import urllib.request
import os
import urllib.parse
import concurrent.futures

visited = set()

def fetch_json(url):
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        return json.loads(urllib.request.urlopen(req, timeout=10).read().decode('utf-8'))
    except Exception as e:
        return None

def extract_refs(obj, in_plays=False):
    refs = []
    if isinstance(obj, dict):
        for k, v in obj.items():
            if k == '$ref':
                refs.append(v)
            else:
                refs.extend(extract_refs(v, in_plays or k == 'plays' or 'playbyplay' in k.lower()))
    elif isinstance(obj, list):
        if in_plays:
            obj = obj[:10]  # Only take first 10 items for ball-by-ball
        for item in obj:
            refs.extend(extract_refs(item, in_plays))
    return refs

def get_save_path(url):
    parsed = urllib.parse.urlparse(url)
    path = parsed.path.strip('/')
    if not path: path = "root"
    file_path = os.path.join('sample_sublinks', path)
    if not file_path.endswith('.json'):
        file_path += '.json'
    return file_path

def fetch_and_save(url):
    clean_url = url.split('?')[0]
    data = fetch_json(url)
    if not data: return []
    
    save_path = get_save_path(clean_url)
    os.makedirs(os.path.dirname(save_path), exist_ok=True)
    try:
        with open(save_path, 'w') as f:
            json.dump(data, f, indent=2)
    except:
        pass
        
    in_plays = '/plays' in clean_url or 'playbyplay' in clean_url.lower()
    refs = extract_refs(data, in_plays=in_plays)
    return [r for r in set(refs) if isinstance(r, str) and r.startswith('http')]

def main():
    os.makedirs('sample_sublinks', exist_ok=True)
    
    try:
        event_data = json.load(open('sample_event.json'))
        event_ref = event_data.get('$ref')
        event_id = event_data.get('id')
    except Exception as e:
        print("Error loading sample_event.json:", e)
        return
        
    if not event_ref or not event_id:
        print("No $ref or id found in sample_event.json")
        return
        
    print(f"Restricting crawl strictly to URLs containing event ID: {event_id}")
    current_level_urls = {event_ref}
    
    for depth in range(6): 
        print(f"--- Depth {depth} ---")
        next_level_urls = set()
        urls_to_fetch = []
        
        for u in current_level_urls:
            cu = u.split('?')[0]
            # ONLY crawl if the URL is strictly for this event ID
            if str(event_id) in cu and cu not in visited:
                visited.add(cu)
                urls_to_fetch.append(u)
                
        if not urls_to_fetch:
            print("No new event-specific URLs to fetch. Ending crawl.")
            break
            
        print(f"Fetching {len(urls_to_fetch)} URLs at depth {depth}...")
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=50) as executor:
            future_to_url = {executor.submit(fetch_and_save, url): url for url in urls_to_fetch}
            for future in concurrent.futures.as_completed(future_to_url):
                try:
                    refs = future.result()
                    for r in refs:
                        next_level_urls.add(r)
                except Exception as e:
                    pass
                    
        current_level_urls = next_level_urls
        print(f"Finished depth {depth}. Found {len(current_level_urls)} refs for next depth.")

if __name__ == '__main__':
    main()
