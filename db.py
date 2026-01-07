import psycopg
from psycopg.rows import dict_row
from settings import DATABASE_URL

if not DATABASE_URL:
    raise RuntimeError("DATABASE_URL is missing. Put it in .env")

def get_conn():
    return psycopg.connect(DATABASE_URL, row_factory=dict_row)
