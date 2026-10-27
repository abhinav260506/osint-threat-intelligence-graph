"""Neo4j Connectivity & Health Check Utility for ThreatGraph AI."""

import sys
import os

if sys.stdout.encoding != "utf-8":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

# Add root directory to path so backend module can be resolved
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from neo4j import GraphDatabase
from backend.app.core.config import settings


def check_neo4j():
    print("=" * 60)
    print("🛡️  ThreatGraph AI — Neo4j Connection Diagnostic Tool")
    print("=" * 60)
    print(f"Target URI      : {settings.NEO4J_URI}")
    print(f"User            : {settings.NEO4J_USER}")
    print(f"Database        : {settings.NEO4J_DATABASE}")
    print(f"Password        : {'*' * len(settings.NEO4J_PASSWORD)}")
    print("-" * 60)
    print("Attempting to connect to Neo4j...")

    try:
        driver = GraphDatabase.driver(
            settings.NEO4J_URI,
            auth=(settings.NEO4J_USER, settings.NEO4J_PASSWORD),
            connection_acquisition_timeout=5.0,
        )
        driver.verify_connectivity()
        print("✅ Connectivity verification SUCCESSFUL!\n")

        with driver.session(database=settings.NEO4J_DATABASE) as session:
            # Query server version & db stats
            version_res = session.run("CALL dbms.components() YIELD name, versions, edition RETURN name, versions[0] AS version, edition")
            for ver_record in version_res:
                print(f"• Neo4j Component : {ver_record['name']} {ver_record['edition']} (v{ver_record['version']})")
                break

            node_count = session.run("MATCH (n) RETURN count(n) AS count").single()["count"]
            rel_count = session.run("MATCH ()-[r]->() RETURN count(r) AS count").single()["count"]
            print(f"• Current Nodes : {node_count}")
            print(f"• Current Edges : {rel_count}")

            # Check constraints
            constraints_res = session.run("SHOW CONSTRAINTS YIELD name, type, entityType, properties")
            constraints = list(constraints_res)
            print(f"• Constraints   : {len(constraints)} active schema constraints")

        driver.close()
        print("\n🎉 Your Neo4j database is fully configured and ready for ThreatGraph AI!")
        return 0

    except Exception as exc:
        err_msg = str(exc)
        print(f"❌ Connection FAILED: {err_msg}\n")
        print("🔍 Diagnostic Suggestions:")

        if "refused" in err_msg.lower() or "failed to establish connection" in err_msg.lower():
            print("  1. The Neo4j service is not currently running on this port.")
            print("     -> If using Docker, run: docker compose up -d neo4j (make sure Docker Desktop is running)")
            print("     -> If using Neo4j Desktop, click 'Start' on your database project.")
            print("     -> If using Neo4j AuraDB (Cloud), verify your NEO4J_URI (e.g. neo4j+s://xxxx.databases.neo4j.io)")
        elif "authentication" in err_msg.lower() or "unauthorized" in err_msg.lower():
            print("  2. Authentication failed: incorrect username or password.")
            print("     -> Check NEO4J_USER and NEO4J_PASSWORD in your .env file.")
        elif "database does not exist" in err_msg.lower():
            print("  3. The specified database was not found.")
            print("     -> Check NEO4J_DATABASE in .env (default is usually 'neo4j').")
        else:
            print("  4. Please inspect your .env file settings and ensure the Neo4j instance is accessible.")

        print("=" * 60)
        return 1


if __name__ == "__main__":
    sys.exit(check_neo4j())
