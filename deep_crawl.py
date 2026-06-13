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

def extract_refs(obj):
    refs = []
    if isinstance(obj, dict):
        for k, v in obj.items():
            if k == '$ref':
                refs.append(v)
            else:
                refs.extend(extract_refs(v))
    elif isinstance(obj, list):
        for item in obj:
            refs.extend(extract_refs(item))
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
        
    refs = extract_refs(data)
    return [r for r in set(refs) if isinstance(r, str) and r.startswith('http')]

def main():
    os.makedirs('sample_sublinks', exist_ok=True)
    
    try:
        event_data = json.load(open('sample_event.json'))
        event_ref = event_data.get('$ref')
    except Exception as e:
        print("Error loading sample_event.json:", e)
        return
        
    if not event_ref:
        print("No $ref found in sample_event.json")
        return
        
    current_level_urls = {event_ref}
    
    # User asked for up to 5 layers deep (0, 1, 2, 3, 4, 5)
    for depth in range(6): 
        print(f"--- Depth {depth} ---")
        next_level_urls = set()
        
        urls_to_fetch = []
        for u in current_level_urls:
            cu = u.split('?')[0]
            if cu not in visited:
                visited.add(cu)
                urls_to_fetch.append(u)
                
        if not urls_to_fetch:
            print("No new URLs to fetch. Ending crawl.")
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
