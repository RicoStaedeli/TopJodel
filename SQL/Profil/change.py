import psycopg2

from SQL.Authentication.api_token import validate_token
from SQL.sql_error import ProfileError
from SQL.connection import connect_to_sql_database
from SQL.utils import clean_input
from datetime import datetime, UTC

def change_profile(token, user_id, id, new_profile_data):

    if len(new_profile_data) == 0:
        print("⚠️ Nothing to update.")
        return False

    user_id = clean_input(user_id)
    token = clean_input(token)

    validate_token(user_id, token)

    try:
        with connect_to_sql_database() as conn:
            with conn.cursor() as cur:
                base_query = "UPDATE profile"
                conditions = []
                values = []

                for key, value in new_profile_data.items():
                    if key == "id" or key == "user_id" or key == "updated_at":
                        continue
                    conditions.append(f"{key} = %s")
                    values.append(clean_input(value))

                conditions.append(f"updated_at = %s")
                values.append(datetime.now(UTC))

                where_clause = " WHERE id = %s"
                values.append(clean_input(id))

                if conditions:
                    set_clause = " SET " + f", ".join(conditions)
                    final_query = base_query + set_clause + where_clause

                cur.execute(final_query, tuple(values))
                conn.commit()
                print(f"✅ Profile successfully changed (id={id})")

        return True
    except psycopg2.Error as e:
        raise ProfileError(f"Database error occurred: {e.pgerror}") from e
    except Exception as e:
        raise ProfileError(f" Failed to change profile: {e}") from e


