from connection import connect_to_sql_database
import psycopg2

class CreationError(Exception):
    PREFIX = "❌ Creation of Table failed: "

    def __init__(self, message):
        # store the prefixed message
        super().__init__(self.PREFIX + str(message))

def create_tables():

    try:
        with connect_to_sql_database() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS users (
                        id SERIAL PRIMARY KEY,
                        email VARCHAR(100) UNIQUE NOT NULL,
                        password_hash TEXT NOT NULL,
                        created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                        updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
                    );
                 """)

                cur.execute("""
                    CREATE TABLE IF NOT EXISTS profile(
                        id SERIAL PRIMARY KEY,
                        user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                        username VARCHAR(50) UNIQUE NOT NULL,
                        first_name VARCHAR(50) NOT NULL,
                        last_name VARCHAR(50) NOT NULL,
                        updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()    
                    );
                """)

                cur.execute("""
                    CREATE TABLE IF NOT EXISTS api_tokens (
                        token TEXT PRIMARY KEY,
                        user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
                        expires_at TIMESTAMPTZ NOT NULL
                    );
                """)

                conn.commit()
                print("✅ 'users' table created successfully.")
                print("✅ 'profile' table created successfully.")
                print("✅ 'api_tokens' table created successfully.")

    except psycopg2.Error as e:
            raise CreationError("Database error") from e
    except Exception as e:
        print(f"❌ Creation of Table failed: {e}")
        raise