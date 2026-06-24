from app import rows_from_postgres
query = """
WITH icc_balls AS (
    SELECT u.zad, u.match_date, u.over_number,
           ROW_NUMBER() OVER(PARTITION BY u.match_date, u.over_number ORDER BY u.ball_in_over) as rn
    FROM cricket.unified_deliveries u
    WHERE u.batsman_name IN ('Virat Kohli') AND u.source_database = 'ICC'
),
cric_balls AS (
    SELECT m.match_date, c.over_number, c.batsman_runs, c.ball_number,
           ROW_NUMBER() OVER(PARTITION BY m.match_date, c.over_number ORDER BY c.ball_number) as rn
    FROM cricket.cricsheet_deliveries c
    JOIN cricket.cricsheet_matches m ON m.id = c.match_id
    WHERE c.batsman_id = '253802'
)
SELECT i.zad, c.batsman_runs, i.over_number, c.ball_number as ball_in_over, i.match_date
FROM icc_balls i
LEFT JOIN cric_balls c 
  ON i.match_date = c.match_date 
 AND i.over_number = c.over_number 
 AND i.rn = c.rn
WHERE i.zad IS NOT NULL AND i.zad != ''
LIMIT 20
"""
rows = rows_from_postgres(query)
for r in rows:
    print(r)
