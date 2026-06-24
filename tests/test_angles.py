from app import rows_from_postgres

query = """
SELECT shot_type, 
       MIN(CAST(split_part(u.zad, ',', 2) as INTEGER)) as min_a, 
       MAX(CAST(split_part(u.zad, ',', 2) as INTEGER)) as max_a, 
       ROUND(AVG(CAST(split_part(u.zad, ',', 2) as INTEGER)), 1) as avg_a,
       COUNT(*) as cnt
FROM cricket.unified_deliveries u
WHERE u.batsman_name IN ('Virat Kohli') AND u.source_database = 'ICC' AND u.zad IS NOT NULL AND u.zad != ''
  AND shot_type IS NOT NULL AND shot_type != ''
GROUP BY shot_type
HAVING COUNT(*) > 10
ORDER BY avg_a
"""
rows = rows_from_postgres(query)
print(f"{'Shot Type':<25} | {'Min A':<5} | {'Max A':<5} | {'Avg A':<6} | {'Count'}")
print("-" * 60)
for r in rows:
    print(f"{r['shot_type']:<25} | {r['min_a']:<5} | {r['max_a']:<5} | {r['avg_a']:<6} | {r['cnt']}")
