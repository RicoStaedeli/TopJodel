from SQL.Authentication.user import register_user, change_credentials, delete_user, retrieve_user
from SQL.Profil.change import change_profile
from SQL.Profil.retrieve import retrieve_profiles_by_user_id, retrieve_profile_ids, retrieve_profile_by_id
from initialize import create_tables
from SQL.Authentication.user import login_user, logout_user

if __name__ == "__main__":
    try:
        create_tables()

        #register_user("test", "test@test.ch", "Test1234", "Max", "Mustermann")

        #register_user("test1", "test1@test.ch", "Test1234", "Max", "Müller")

        session = login_user("test1@test.ch", "Test1234")

        user_id = session["user_id"]
        token = session["token"]

        # change_credentials(session["user_id"], session["token"], "test@test.ch","Test1234", "test@test.ch" ,None)

        # print(retrieve_user(user_id))

        profiles = retrieve_profiles_by_user_id(user_id)
        print(profiles)
        #print(retrieve_profile_by_id(profiles[0]["id"]))

        #query = {"username": "test", "last_name": "Müller"}
        #print(retrieve_profile_ids("OR", query))

        change_query = {"username": "test2", "last_name": "Bäcker"}
        change_profile(token, user_id, profiles[0]["id"], change_query)

        print(retrieve_profile_by_id(profiles[0]["id"]))

        # delete_user(user_id, token, "test@test.ch", "Test1234")

        logout_user(session["token"])


    except Exception as e:
        print(e)
