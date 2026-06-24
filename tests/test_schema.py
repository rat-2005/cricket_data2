from app import rows_from_postgres
query = """
SELECT column_name, data_type 
FROM information_schema.columns 
WHERE table_schema = 'cricket' AND table_name = 'unified_deliveries';
"""
rows = rows_from_postgres(query)
for r in rows:
    print(r['column_name'], r['data_type'])
