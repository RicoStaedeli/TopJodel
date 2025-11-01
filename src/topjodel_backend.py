# SQL
from SQL.Authentication.user import *
from SQL.Profil.retrieve import *

# MongoDB
from MongoDB.mongo_repo import MongoPostsRepository
from MongoDB.connection import get_mongo_client

# Neo4j
from NeoDB.neo4j_repo import Neo4jRepository
from NeoDB.connection import get_neo4j_driver


class TopJodelBackend():

    def __init__(self):
        client = get_mongo_client()
        self.mongo_repo = MongoPostsRepository(db=client["appdb"])

        driver = get_neo4j_driver()
        self.neo_repo = Neo4jRepository(driver)



    def get_news_feed(self, user_id: int, limit: int = 10, token: str = ""):

        client = get_mongo_client()
        db = client['appdb']
        posts_repo = MongoPostsRepository(db)

        driver = get_neo4j_driver()

        neo_repo = Neo4jRepository(driver)

        # Query the neo4j database to get the list of user IDs that the given user follows
        list_users = neo_repo.run_cypher()

        # Get the latest posts from those users


        # Fetch posts for the news feed
        posts = posts_repo.get_posts_by_user(user_id=user_id, limit=limit)

        return posts


    def follow_user(self, logged_in_user_id: int, name_to_follow: str="", last_name_to_follow:str = ""):
        """
        Follows a user by creating a FOLLOWS relationship in the Neo4j database.
        name_to_follow: First name of the user to follow
        last_name_to_follow: Last name of the user to follow
        :param logged_in_user_id:
        :param name_to_follow:
        :param last_name_to_follow:
        :return:
        """

        query = {"first_name": name_to_follow, "last_name": last_name_to_follow}
        profile_ids = retrieve_profile_ids("OR", query)
        print(f"Found profiles: {profile_ids}")

        if len(profile_ids) > 0:
            follow_profile_id = profile_ids[0][0]
            print(f"Following profile id: {follow_profile_id}")
            username_to_follow = retrieve_profile_by_id(follow_profile_id)["username"]
            username_logged_in = retrieve_profiles_by_user_id(logged_in_user_id)[0]["username"]
            print(f"Logged in: {username_logged_in}")

            query = """
        MATCH (a:User {username: $logged_in}),
              (b:User {username: $to_follow})
        MERGE (a)-[:FOLLOWS]->(b)
        """

            self.neo_repo.run_cypher(
                query,
                {
                    "logged_in": username_logged_in,
                    "to_follow": username_to_follow
                }
            )
            print(f"Successfully followed {name_to_follow} {last_name_to_follow}")
        else:
            print(f"No profile found for name: {name_to_follow} {last_name_to_follow}")
            return f"No profile found for name: {name_to_follow} {last_name_to_follow}"