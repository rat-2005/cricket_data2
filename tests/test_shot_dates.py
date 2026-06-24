from app import rows_from_postgres

query = """
SELECT EXTRACT(YEAR FROM match_date) as yr, COUNT(*) as total, SUM(CASE WHEN shot_type != '' THEN 1 ELSE 0 END) as with_shot
FROM cricket.unified_deliveries u
WHERE u.batsman_name IN ('Virat Kohli') AND u.source_database = 'ICC'
GROUP BY yr
ORDER BY yr
"""
for r in rows_from_postgres(query):
    print(r)
