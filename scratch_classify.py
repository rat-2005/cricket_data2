import json, os

# Check ALL unique classification combos across all local JSON files
files = [f for f in os.listdir('data/cricinfo_json') if f.endswith('.json')]
print(f"Scanning {len(files)} files...")

combos = {}
league_names = set()

for f in files:
    with open(f'data/cricinfo_json/{f}', 'r', encoding='utf-8') as fh:
        d = json.load(fh)
    m = d.get('match', {})
    intClass = m.get('internationalClassId')
    genClass = m.get('generalClassId')
    fmt = m.get('format')
    series = m.get('series', {}).get('longName', '')
    
    key = (intClass, genClass, fmt)
    if key not in combos:
        combos[key] = {"count": 0, "example_series": set()}
    combos[key]["count"] += 1
    combos[key]["example_series"].add(series[:80])
    league_names.add(series)

print(f"\n{'='*100}")
print(f"{'intClass':<12} {'genClass':<12} {'format':<10} {'count':<8} Example Series")
print(f"{'='*100}")

for (intClass, genClass, fmt), info in sorted(combos.items(), key=lambda x: -x[1]['count']):
    examples = list(info['example_series'])[:3]
    print(f"{str(intClass):<12} {str(genClass):<12} {str(fmt):<10} {info['count']:<8} {' | '.join(examples)}")

# Also print all unique series names that contain known T20 league keywords
print(f"\n\n{'='*60}")
print("SERIES NAMES containing T20 league keywords:")
print(f"{'='*60}")
keywords = ['IPL', 'Indian Premier', 'Big Bash', 'BBL', 'PSL', 'Pakistan Super', 
            'CPL', 'Caribbean Premier', 'SA20', 'Hundred', 'BPL', 'Bangladesh Premier',
            'Lanka Premier', 'LPL', 'Major League Cricket', 'MLC', 'ILT20', 'Super Smash',
            'Vitality Blast', 'T20 Blast']
for name in sorted(league_names):
    for kw in keywords:
        if kw.lower() in name.lower():
            print(f"  {name}")
            break
