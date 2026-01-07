import os
import psycopg
from psycopg.rows import dict_row

DATABASE_URL = os.environ.get("DATABASE_URL")
if not DATABASE_URL:
    raise RuntimeError("DATABASE_URL environment variable not set")

def get_conn():
    return psycopg.connect(DATABASE_URL, row_factory=dict_row)

def init_db():
    schema_path = os.path.join(os.path.dirname(__file__), "schema.sql")
    with open(schema_path, "r", encoding="utf-8") as f:
        sql = f.read()

    # Split into individual statements safely enough for our schema.sql
    statements = [s.strip() for s in sql.split(";") if s.strip()]

    with get_conn() as con:
        for stmt in statements:
            try:
                con.execute(stmt)
            except Exception as e:
                # IMPORTANT: pgcrypto may fail if Railway role lacks permission.
                # We don't want that to block table creation.
                if "CREATE EXTENSION" in stmt.upper():
                    print(f"WARNING: extension not created: {e}")
                    continue
                raise
        con.commit()
