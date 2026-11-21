import os
import psycopg
from dotenv import load_dotenv

load_dotenv()
for name in ["DATABASE_URL", "TEST_DATABASE_URL"]:
    with psycopg.connect(os.environ[name]) as conn:
        db = conn.execute("select current_database()").fetchone()[0]
        enc = conn.execute("show server_encoding").fetchone()[0]
        tz = conn.execute("show timezone").fetchone()[0]
        ext = [r[0] for r in conn.execute("select extname from pg_extension")]
        print(f"{name}: db={db} encoding={enc} timezone={tz} extensions={ext}")
