
from datetime import datetime, timezone, timedelta
import secrets
import psycopg2
from SQL.connection import connect_to_sql_database
from SQL.sql_error import TokenError

def generate_token(length=64):
    return secrets.token_hex(length)

def issue_token(user_id):

    token = generate_token()
    expires_at = datetime.now(timezone.utc) + timedelta(hours=24)

    try:
        with connect_to_sql_database() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO api_tokens (token, user_id, expires_at)
                    VALUES (%s, %s, %s)
                """, (token, user_id, expires_at))
                conn.commit()
            return token
    except psycopg2.Error as e:
        raise TokenError("Failed to issue token") from e

def validate_token(user_id, token):

    now_utc = datetime.now(timezone.utc)

    try:
        with connect_to_sql_database() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT user_id FROM api_tokens WHERE user_id = %s AND token = %s AND expires_at > %s
                """, (user_id, token, now_utc))
                row = cur.fetchone()

                if row:
                    return row[0]
                return None

    except psycopg2.Error as e:
        raise TokenError("Failed to validate token") from e

def revoke_token(token):

    try:
        with connect_to_sql_database() as conn:
            with conn.cursor() as cur:
                cur.execute("DELETE FROM api_tokens WHERE token = %s", (token,))
                deleted = cur.rowcount
                conn.commit()

                if deleted > 0:
                    return True
                else:
                    return False

    except psycopg2.Error as e:
        raise TokenError("Failed to revoke token") from e
