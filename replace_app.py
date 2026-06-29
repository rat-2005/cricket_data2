import os
with open('data_service.py', 'r', encoding='utf-8') as f:
    text = f.read()

text = text.replace("WHEN format = 'IT20' THEN 'T20'", "WHEN format IN ('T20', 'T20I', 'IT20') AND internationalClassId = 3 THEN 'T20I'\n                WHEN format = 'IT20' AND internationalClassId IS NULL THEN 'T20I'\n                WHEN format IN ('T20', 'T20I', 'IT20') THEN 'T20_DOMESTIC'")

bat_t = '    batting_stats = {}\\n    for row in batting_raw:\\n        fmt = _normalize_format(row["matched_format"] or "Unknown")\\n        runs  = row["total_runs"] or 0'.replace('\\n', '\n')
bat_r = '    allowed_formats = ["Test", "ODI", "T20I"]\\n\\n    batting_stats = {}\\n    for row in batting_raw:\\n        fmt = _normalize_format(row["matched_format"] or "Unknown")\\n        if fmt == "T20i":\\n            fmt = "T20I"\\n        if fmt not in allowed_formats:\\n            continue\\n\\n        runs  = row["total_runs"] or 0'.replace('\\n', '\n')

text = text.replace(bat_t, bat_r)

bowl_t = '    bowling_stats = {}\\n    for row in bowling_raw:\\n        fmt = _normalize_format(row["matched_format"] or "Unknown")\\n        w  = row["total_wickets"] or 0'.replace('\\n', '\n')
bowl_r = '    bowling_stats = {}\\n    for row in bowling_raw:\\n        fmt = _normalize_format(row["matched_format"] or "Unknown")\\n        if fmt == "T20i":\\n            fmt = "T20I"\\n        if fmt not in allowed_formats:\\n            continue\\n\\n        w  = row["total_wickets"] or 0'.replace('\\n', '\n')

text = text.replace(bowl_t, bowl_r)

with open('data_service.py', 'w', encoding='utf-8') as f:
    f.write(text)

print('Done')
