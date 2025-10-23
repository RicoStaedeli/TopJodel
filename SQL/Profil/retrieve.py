import psycopg2

from SQL.sql_error import ProfileError
from SQL.connection import connect_to_sql_database
from SQL.utils import clean_input

def retrieve_profile_by_id(profile_id):

    profile_id = clean_input(profile_id)

    try:
        with connect_to_sql_database() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT * FROM profile WHERE id = %s;", (profile_id,))

                profile = cur.fetchone()

                if not profile:
                    print(f"⚠️ Profile not found for profile_id {profile_id}")
                    return None

                return output_profile(profile)
    except psycopg2.Error as e:
        raise ProfileError(f"Database error occurred: {e.pgerror}") from e
    except Exception as e:
        raise ProfileError(f"An unexpected error occurred: {e}") from e

def retrieve_profiles_by_user_id(user_id):

    user_id = clean_input(user_id)

    try:
        with connect_to_sql_database() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT * FROM profile WHERE user_id = %s;", (user_id,))

                profiles = cur.fetchall()

                if not profiles:
                    print(f"⚠️ Profile not found for profile_id {user_id}")
                    return None

                return [output_profile(profile) for profile in profiles]
    except psycopg2.Error as e:
        raise ProfileError(f"Database error occurred: {e.pgerror}") from e
    except Exception as e:
        raise ProfileError(f"An unexpected error occurred: {e}") from e

def retrieve_profile_by_username(username):

    username = clean_input(username)

    try:
        with connect_to_sql_database() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT * FROM profile WHERE username = %s;", (username,))

                profile = cur.fetchone()

                if not profile:
                    print(f"⚠️ Profile not found for username {username}")
                    return None

                return output_profile(profile)
    except psycopg2.Error as e:
        raise ProfileError(f"Database error occurred: {e.pgerror}") from e
    except Exception as e:
        raise ProfileError(f"An unexpected error occurred: {e}") from e

def retrieve_profile_ids(operation, query_criteria):
    try:
        with connect_to_sql_database() as conn:
            with conn.cursor() as cur:
                base_query = "SELECT id FROM profile"
                conditions = []
                values = []

                for key, value in query_criteria.items():
                    conditions.append(f"{key} = %s")
                    values.append(clean_input(value))

                if conditions:
                    where_clause = " WHERE " + f" {operation} ".join(conditions)
                    final_query = base_query + where_clause
                else:
                    final_query = base_query

                cur.execute(final_query, tuple(values))

                profile_ids = cur.fetchall()

                if not profile_ids:
                    print("⚠️ No profiles found matching the criteria")
                    return []

                return profile_ids
    except psycopg2.Error as e:
        raise ProfileError(f"Database error occurred: {e.pgerror}") from e
    except Exception as e:
        raise ProfileError(f"An unexpected error occurred: {e}") from e

def output_profile(profile):
    return {
        "id": profile[0],
        "user_id": profile[1],
        "username": profile[2],
        "first_name": profile[3],
        "last_name": profile[4],
        "updated_at": profile[5]
    }
