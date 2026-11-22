import os, psycopg
from dotenv import load_dotenv

load_dotenv()
with psycopg.connect(os.environ["TEST_DATABASE_URL"]) as conn:
    rows = conn.execute("select table_name from information_schema.tables where table_schema = 'public' order by 1").fetchall()
print(len(rows), "tables:", [r[0] for r in rows])
