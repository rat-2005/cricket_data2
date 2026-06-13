import json, os

all_schemas = {}

for root, dirs, files in os.walk('sample_sublinks'):
    for file in files:
        if file.endswith('.json'):
            filepath = os.path.join(root, file)
            rel = os.path.relpath(filepath, 'sample_sublinks').replace('\\', '/')
            
            entity = 'unknown'
            for keyword in ['details', 'plays', 'playbyplay', 'roster', 'athletes', 
                           'statistics', 'status', 'officials', 'broadcasts', 'odds',
                           'venues', 'teams', 'scores', 'linescores', 'matchcards',
                           'situation', 'competitors', 'leaders', 'records', 'tickets',
                           'weather', 'notes']:
                if keyword in rel.lower():
                    entity = keyword
                    break
            
            try:
                with open(filepath, 'r') as f:
                    data = json.load(f)
                if entity not in all_schemas:
                    all_schemas[entity] = {'sample_path': filepath, 'keys': set(), 'count': 0}
                all_schemas[entity]['count'] += 1
                
                def get_keys(obj, prefix=''):
                    keys = set()
                    if isinstance(obj, dict):
                        for k, v in obj.items():
                            p = prefix + '.' + k if prefix else k
                            keys.add(p)
                            keys.update(get_keys(v, p))
                    elif isinstance(obj, list) and obj:
                        keys.update(get_keys(obj[0], prefix + '[]'))
                    return keys
                all_schemas[entity]['keys'].update(get_keys(data))
            except:
                pass

for entity in sorted(all_schemas.keys()):
    info = all_schemas[entity]
    count = info['count']
    sample = info['sample_path']
    print(f'=== {entity.upper()} ({count} files) ===')
    print(f'Sample: {sample}')
    for k in sorted(info['keys']):
        if k.count('.') < 4 and '$ref' not in k:
            print(f'  {k}')
    print()
