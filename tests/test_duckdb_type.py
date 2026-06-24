import duckdb
con = duckdb.connect()
con.execute("CREATE TABLE athletes AS SELECT 253802 as id, 'Virat Kohli' as name")
print(con.execute("SELECT * FROM athletes WHERE id IN (?, ?)", ['253802', '123']).fetchall())
