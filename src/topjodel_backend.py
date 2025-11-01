from MongoDB.mongo_repo import MongoPostsRepository
from MongoDB.connection import get_mongo_client
from NeoDB.neo4j_repo import Neo4jRepository
from NeoDB.connection import get_neo4j_driver


def get_news_feed(user_id: int, limit: int = 10, token):

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