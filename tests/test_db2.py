from app import rows_from_postgres
query = """
SELECT u.match_date, u.over_number, u.ball_in_over, u.zad
FROM cricket.unified_deliveries u
WHERE u.batsman_name IN ('Virat Kohli') AND u.source_database = 'ICC' AND u.zad IS NOT NULL AND u.zad != ''
ORDER BY u.match_date, u.over_number, u.ball_in_over
LIMIT 20
"""
rows = rows_from_postgres(query)
for r in rows:
    print(r)
