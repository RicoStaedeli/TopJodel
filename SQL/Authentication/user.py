from SQL.connection import connect_to_sql_database
import psycopg2
import bcrypt
from SQL.Authentication.api_token import issue_token, revoke_token, validate_token
from SQL.sql_error import AuthenticationError, RegistrationError, UserError, TokenError
from SQL.utils import clean_input, validate_username, validate_email, validate_password, validate_first_name, validate_last_name
from datetime import datetime, UTC


def register_user(username, email, password, first_name, last_name):

    username = clean_input(username)
    email = clean_input(email)
    password = clean_input(password)
    first_name = clean_input(first_name)
    last_name = clean_input(last_name)

    try:
        validate_username(username)
        validate_email(email)
        validate_password(password)
        validate_first_name(first_name)
        validate_last_name(last_name)

        with connect_to_sql_database() as conn:
            with conn.cursor() as cur:

                password_hash = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt())
                password_hash_str = password_hash.decode("utf-8")

                cur.execute("""
                            INSERT INTO users (email, password_hash)
                            VALUES (%s, %s) RETURNING id;
                            """, (email, password_hash_str))
                user_id = cur.fetchone()[0]

                cur.execute("""
                            INSERT INTO profile (user_id, username, first_name, last_name)
                            VALUES (%s, %s, %s, %s);
                            """, (user_id, username, first_name, last_name))

                conn.commit()
                print(f"✅ User successfully registered (id={user_id})")
                return user_id
    except psycopg2.Error as e:
            raise RegistrationError(f"Database error: {e}") from e
    except ValueError as e:
        raise RegistrationError(e) from e
    except Exception as e:
        print(f"❌ Registration failed: {e}")
        raise

def check_password(email, password):

    try:
        with connect_to_sql_database() as conn:
            with conn.cursor() as cur:

                cur.execute("""
                    SELECT * FROM users WHERE email = %s;
                """, (email,))

                user = cur.fetchone()

                if user is None:
                    raise AuthenticationError(f"User with email '{email}' does not exist.")

                stored_hash_str = user[2]
                stored_hash_bytes = stored_hash_str.encode("utf-8")

                if not bcrypt.checkpw(password.encode("utf-8"), stored_hash_bytes):
                    raise AuthenticationError("Incorrect password.")

                return user[0]

    except psycopg2.Error as e:
        raise AuthenticationError("Database error") from e
    except AuthenticationError as e:
        raise e
    except Exception as e:
        print(f"❌ Password validation failed: {e}")
        raise

def login_user(email, password):

    email = clean_input(email)
    password = clean_input(password)

    user_id = check_password(email, password)

    try:
        with connect_to_sql_database() as conn:
            with conn.cursor() as cur:
                token = issue_token(user_id)
                print(f"✅ User logged in successfully (user_id={user_id})")
                return {"user_id": user_id, "token": token}

    except psycopg2.Error as e:
        raise AuthenticationError("Database error") from e
    except AuthenticationError as e:
        raise e
    except Exception as e:
        print(f"❌ Login failed: {e}")
        raise

def logout_user(token):

    token = clean_input(token)

    try:
        revoked = revoke_token(token)
        if revoked:
            print(f"✅ User logged out successfully")
        else:
            print("⚠️ No active session found for this token.")
    except TokenError as e:
        raise AuthenticationError("Failed to logout user") from e

def retrieve_user(user_id):

    user_id = clean_input(user_id)

    try:
        with connect_to_sql_database() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT id, email, created_at, updated_at FROM users WHERE id = %s;", (user_id,))

                user = cur.fetchone()

                if not user:
                    raise UserError(f"❌ User with user_id '{user_id}' does not exist.")

                user_data = {
                    "id": user[0],
                    "email": user[1],
                    "created_at": user[2],
                    "updated_at": user[3]
                }

                return user_data

    except psycopg2.Error as e:
        raise UserError("❌ Failed to fetch user: Database error") from e

def change_credentials(user_id, token, old_email, old_password, new_email=None, new_password=None):

    user_id = clean_input(user_id)
    old_email = clean_input(old_email)
    old_password = clean_input(old_password)
    token = clean_input(token)

    user_id = validate_token(user_id, token)

    user_id_password = check_password(old_email, old_password)

    if user_id is None or user_id != user_id_password:
        raise UserError("❌ Failed to change credentials: Invalid token or old credentials")

    try:
        fields = []
        values = []

        if new_password:
            new_password = clean_input(new_password)
            validate_password(new_password)
            password_hash = bcrypt.hashpw(new_password.encode("utf-8"), bcrypt.gensalt())
            password_hash_str = password_hash.decode("utf-8")
            fields.append("password_hash = %s")
            values.append(password_hash_str)

        if new_email:
            new_email = clean_input(new_email)
            validate_email(new_email)
            fields.append("email = %s")
            values.append(new_email)

        date = datetime.now(UTC)
        fields.append("updated_at = %s")
        values.append(date)

        values.append(user_id)

        if len(fields) == 1:
            print("⚠️ Nothing to update.")
            return False

        query = f" UPDATE users SET {', '.join(fields)} WHERE id = %s;"

        with connect_to_sql_database() as conn:
            with conn.cursor() as cur:
                cur.execute(query, tuple(values))
                conn.commit()
                print(f"✅ User credentials successfully changed (id={user_id})")

        return True
    except psycopg2.Error as e:
        raise UserError("❌ Failed to change credentials: Database error") from e
    except TokenError as e:
        raise UserError(f"❌ Failed to change credentials: {e}") from e

def delete_user(user_id, token, email, password):
    user_id = clean_input(user_id)
    token = clean_input(token)
    email = clean_input(email)
    password = clean_input(password)

    try:

        user_id = validate_token(user_id, token)
        check_password(email, password)

        with connect_to_sql_database() as conn:
            with conn.cursor() as cur:
                cur.execute("DELETE FROM users WHERE id = %s;", (user_id,))
                conn.commit()
                print(f"✅ User successfully deleted (id={user_id})")
                return True

    except psycopg2.Error as e:
        raise UserError("❌ Failed to delete user: Database error") from e
    except TokenError as e:
        raise UserError(f"❌ Failed to delete user: {e}") from e