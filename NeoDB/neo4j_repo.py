from neo4j import Driver


class Neo4jRepository:
    def __init__(self, driver: Driver):
        self.driver = driver

    def run_cypher(self, query, params=None):
        """
        Execute a Cypher query against the Neo4j database.
        :param query:
        :param params:
        :return: results of the query
        """
        with self.driver.session() as session:
            return list(session.run(query, params or {}))