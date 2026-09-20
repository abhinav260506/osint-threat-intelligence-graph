"""Neo4j Driver Connection Manager and Cypher Execution Layer."""

from typing import Any, Dict, List, Optional
import neo4j
from neo4j import GraphDatabase, Driver
from backend.app.core.config import settings
from backend.app.core.logging import logger


class Neo4jConnectionManager:
    """Manages Neo4j Bolt driver lifecycle and session pools."""

    def __init__(self):
        self._driver: Optional[Driver] = None
        self._is_available: bool = False

    def connect(self) -> bool:
        """Initializes connection to Neo4j."""
        try:
            self._driver = GraphDatabase.driver(
                settings.NEO4J_URI,
                auth=(settings.NEO4J_USER, settings.NEO4J_PASSWORD),
                max_connection_lifetime=30 * 60,
                max_connection_pool_size=50,
                connection_acquisition_timeout=5.0,
            )
            self._driver.verify_connectivity()
            self._is_available = True
            logger.info("Successfully connected to Neo4j Threat Knowledge Graph.")
            self._initialize_schema_constraints()
            return True
        except Exception as e:
            self._is_available = False
            logger.warning(f"Neo4j is currently unreachable ({e}). In-memory graph engine will be active.")
            return False

    def _initialize_schema_constraints(self):
        """Applies uniqueness constraints and performance indexes."""
        if not self._driver or not self._is_available:
            return

        constraint_queries = [
            "CREATE CONSTRAINT threat_actor_id_unique IF NOT EXISTS FOR (n:ThreatActor) REQUIRE n.id IS UNIQUE",
            "CREATE CONSTRAINT campaign_id_unique IF NOT EXISTS FOR (n:Campaign) REQUIRE n.id IS UNIQUE",
            "CREATE CONSTRAINT malware_id_unique IF NOT EXISTS FOR (n:Malware) REQUIRE n.id IS UNIQUE",
            "CREATE CONSTRAINT technique_id_unique IF NOT EXISTS FOR (n:AttackTechnique) REQUIRE n.id IS UNIQUE",
            "CREATE CONSTRAINT domain_val_unique IF NOT EXISTS FOR (n:Domain) REQUIRE n.value IS UNIQUE",
            "CREATE CONSTRAINT ip_val_unique IF NOT EXISTS FOR (n:IP) REQUIRE n.value IS UNIQUE",
            "CREATE CONSTRAINT hash_val_unique IF NOT EXISTS FOR (n:Hash) REQUIRE n.value IS UNIQUE",
            "CREATE CONSTRAINT cve_id_unique IF NOT EXISTS FOR (n:CVE) REQUIRE n.id IS UNIQUE",
            "CREATE CONSTRAINT report_id_unique IF NOT EXISTS FOR (n:Report) REQUIRE n.id IS UNIQUE",
        ]
        with self._driver.session(database=settings.NEO4J_DATABASE) as session:
            for q in constraint_queries:
                try:
                    session.run(q)
                except Exception as ex:
                    logger.debug(f"Schema constraint notice: {ex}")

    def execute_query(self, query: str, parameters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """Executes read/write Cypher query with parameterized protection against Cypher injection."""
        if not self._driver or not self._is_available:
            return []

        parameters = parameters or {}
        try:
            with self._driver.session(database=settings.NEO4J_DATABASE) as session:
                result = session.run(query, parameters)
                return [record.data() for record in result]
        except Exception as e:
            logger.error(f"Error executing Cypher query: {e}")
            return []

    def close(self):
        """Closes the driver connection."""
        if self._driver:
            self._driver.close()
            self._is_available = False

    @property
    def is_available(self) -> bool:
        return self._is_available


neo4j_manager = Neo4jConnectionManager()
