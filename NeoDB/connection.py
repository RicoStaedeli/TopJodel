import os
from dotenv import load_dotenv
from neo4j import GraphDatabase


def get_neo4j_driver():

    # Load environment file
    load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), '..', '.env'), override=True)

    # Gather variables (no defaults)
    APP_NEO4J_URI_HTTP = os.getenv("APP_NEO4J_URI_HTTP")
    APP_NEO4J_USER = os.getenv("APP_NEO4J_USER")
    APP_NEO4J_PASSWORD = os.getenv("APP_NEO4J_PASSWORD")

    driver = GraphDatabase.driver(APP_NEO4J_URI_HTTP, auth=(APP_NEO4J_USER, APP_NEO4J_PASSWORD))

    return driver