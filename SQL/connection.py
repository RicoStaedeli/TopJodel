import os
from dotenv import load_dotenv
import psycopg2

def connect_to_sql_database():
    # Load environment file
    load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), '..', '.env'), override=True)

    # Gather variables (no defaults)
    PGHOST = os.getenv("PGHOST")
    PGPORT = os.getenv("PGPORT")
    PGUSER = os.getenv("POSTGRES_USER")
    PGPASSWORD = os.getenv("POSTGRES_PASSWORD")
    PGDATABASE = os.getenv("POSTGRES_DB")


    # Collect into a dict for nice reporting
    env_vars = {
        "PGHOST": PGHOST,
        "PGPORT": PGPORT,
        "POSTGRES_USER": PGUSER,
        "POSTGRES_PASSWORD": PGPASSWORD,
        "POSTGRES_DB": PGDATABASE,
    }

    conn = psycopg2.connect(host="localhost", port=PGPORT, user=PGUSER, password=PGPASSWORD, dbname=PGDATABASE)
    return conn
