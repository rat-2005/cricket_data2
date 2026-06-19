import os

with open("d:/cricket/fresh_data/app.py", "r", encoding="utf-8") as f:
    content = f.read()

# Add connection pool imports
old_imports = "from contextlib import closing"
new_imports = "from contextlib import closing, contextmanager\nfrom psycopg2 import pool"
content = content.replace(old_imports, new_imports)

# Add connection pool definition
pool_def = """
# Global connection pool
db_pool = psycopg2.pool.SimpleConnectionPool(1, 20, DB_URL)

@contextmanager
def get_db_connection():
    conn = db_pool.getconn()
    try:
        yield conn
    finally:
        db_pool.putconn(conn)
"""
content = content.replace("app = Flask(__name__)", f"app = Flask(__name__)\n{pool_def}")

# Replace all connections
content = content.replace("with closing(psycopg2.connect(DB_URL)) as conn:", "with get_db_connection() as conn:")

with open("d:/cricket/fresh_data/app.py", "w", encoding="utf-8") as f:
    f.write(content)

print("Replaced all connections with connection pool")
