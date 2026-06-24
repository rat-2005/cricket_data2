from app import rows_from_postgres

query = """
SELECT format, COUNT(*) as cnt
FROM cricket.unified_deliveries
GROUP BY format
"""
for r in rows_from_postgres(query):
    print(r)
