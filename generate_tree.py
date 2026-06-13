import json
import urllib.request
import os

tree_lines = ["# Sub-Link Tree for The Ashes 1st Test 2023\n"]
visited = set()

def fetch_json(url):
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        return json.loads(urllib.request.urlopen(req, timeout=5).read().decode('utf-8'))
    except:
        return None

def extract_refs(obj, path='Event'):
    refs = {}
    if isinstance(obj, dict):
        for k, v in obj.items():
            if k == '$ref':
                refs[path] = v
            else:
                refs.update(extract_refs(v, f'{path}.{k}'))
    elif isinstance(obj, list):
        if len(obj) > 0:
            refs.update(extract_refs(obj[0], f'{path}[]'))
    return refs

def crawl(data, depth=0, max_depth=2, label='Event'):
    refs = extract_refs(data)
    
    for p, ref_url in refs.items():
        clean_p = p.replace('Event.', '').split('[]')[0]
        if clean_p == 'Event' or 'previous' in clean_p.lower() or 'next' in clean_p.lower():
            continue
            
        clean_url = ref_url.split('?')[0]
        
        # Format the line
        indent = "    " * depth
        tree_lines.append(f"{indent}- **{clean_p}**: [{ref_url}]({ref_url})")
        
        # Recursion
        if depth < max_depth and clean_url not in visited and 'events' in clean_url:
            visited.add(clean_url)
            sub_data = fetch_json(clean_url)
            if sub_data:
                crawl(sub_data, depth + 1, max_depth, clean_p)

if __name__ == '__main__':
    event_data = json.load(open('sample_event.json'))
    crawl(event_data, max_depth=2)
    
    with open('sublinks_tree.md', 'w') as f:
        f.write("\n".join(tree_lines))
    print('Tree generated in sublinks_tree.md')
