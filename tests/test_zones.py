from app import rows_from_postgres

query = """
SELECT CAST(split_part(u.zad, ',', 2) as INTEGER) as angle, COUNT(*) as cnt
FROM cricket.unified_deliveries u
WHERE u.batsman_name IN ('Virat Kohli') AND u.source_database = 'ICC' AND u.zad IS NOT NULL AND u.zad != ''
  AND shot_type = 'Straight Drive'
GROUP BY angle
ORDER BY cnt DESC
"""
print("--- STRAIGHT DRIVE ANGLES ---")
for r in rows_from_postgres(query):
    print(r)
