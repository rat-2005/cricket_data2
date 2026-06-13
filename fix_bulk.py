import os

with open('ingest_bulk.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Fix safe_date
bad_safe_date = """def safe_date(val):
    for fmt in ('%Y-%m-%dT%H:%M%z', '%Y-%m-%dT%H:%M:%S%z', '%Y-%m-%d %H:%M:%S'):
        try: return datetime.strptime(val.replace('Z', '+0000'), fmt)
        except ValueError: pass
    try: return datetime.fromisoformat(val.replace('Z', '+00:00'))"""

good_safe_date = """def safe_date(val):
    if not val: return None
    for fmt in ('%Y-%m-%dT%H:%M%z', '%Y-%m-%dT%H:%M:%S%z', '%Y-%m-%d %H:%M:%S'):
        try: return datetime.strptime(val.replace('Z', '+0000'), fmt)
        except ValueError: pass
    try: return datetime.fromisoformat(val.replace('Z', '+00:00'))
    except: return None"""
content = content.replace(bad_safe_date, good_safe_date)

# Fix extract_id_from_ref
bad_extract_ref = """def extract_id_from_ref(ref_dict):
    \"\"\"Extract numeric ID from {'$ref': 'http://.../12345'} dicts.\"\"\"
    url = ref_dict.get('$ref', '') if isinstance(ref_dict, dict) else str(ref_dict)
    m = re.search(r'/(\\d+)/?$', url.split('?')[0])
    if m and m.group(1) != '0':
        return m.group(1)"""

good_extract_ref = """def extract_id_from_ref(ref_dict):
    \"\"\"Extract numeric ID from {'$ref': 'http://.../12345'} dicts.\"\"\"
    if not ref_dict: return None
    url = ref_dict.get('$ref', '') if isinstance(ref_dict, dict) else str(ref_dict)
    m = re.search(r'/(\\d+)/?$', url.split('?')[0])
    if m and m.group(1) != '0':
        return m.group(1)
    return None"""
content = content.replace(bad_extract_ref, good_extract_ref)

# Fix extract_id_from_url
bad_extract_url = """def extract_id_from_url(url):
    \"\"\"Extract numeric ID from a plain URL string.\"\"\"
    m = re.search(r'/(\\d+)/?$', str(url).split('?')[0])
    if m and m.group(1) != '0':
        return m.group(1)"""

good_extract_url = """def extract_id_from_url(url):
    \"\"\"Extract numeric ID from a plain URL string.\"\"\"
    if not url: return None
    m = re.search(r'/(\\d+)/?$', str(url).split('?')[0])
    if m and m.group(1) != '0':
        return m.group(1)
    return None"""
content = content.replace(bad_extract_url, good_extract_url)

# Remove the broken lines 65-67
bad_lines = """        try:
            async with session.get(url, timeout=aiohttp.ClientTimeout(total=20)) as resp:"""
content = content.replace(bad_lines, "")

with open('ingest_bulk.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("Fixed syntax errors.")
