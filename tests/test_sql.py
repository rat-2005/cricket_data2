import psycopg2
from dotenv import load_dotenv
import os
load_dotenv()
conn = psycopg2.connect(os.getenv('DATABASE_URL'))
cur = conn.cursor()
cur.execute("SELECT DISTINCT tournament FROM cricket.unified_deliveries WHERE tournament ILIKE '%asia cup%'")
print('unified_deliveries:')
for row in cur.fetchall(): print(row[0])

cur.execute("SELECT DISTINCT name FROM cricket.leagues WHERE name ILIKE '%asia cup%'")
print('leagues:')
for row in cur.fetchall(): print(row[0])
