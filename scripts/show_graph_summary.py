import sys
import os

if sys.stdout.encoding != "utf-8":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from backend.app.graph.neo4j import neo4j_manager

if not neo4j_manager.connect():
    print("Could not connect to Neo4j.")
    sys.exit(1)

labels = neo4j_manager.execute_query("MATCH (n) RETURN labels(n)[0] AS label, count(n) AS cnt ORDER BY cnt DESC")
print("=" * 60)
print("📊 CURRENT NODES IN YOUR NEO4J DATABASE BY TYPE:")
print("=" * 60)
for row in labels:
    print(f"  • {row['label']:<18} : {row['cnt']} nodes")

print("\n" + "=" * 60)
print("🕵️ REAL THREAT ACTORS CURRENTLY IN YOUR DATABASE:")
print("=" * 60)
actors = neo4j_manager.execute_query("MATCH (a:ThreatActor) RETURN a.name AS name, a.aliases AS aliases")
for row in actors:
    aliases = ", ".join(row['aliases']) if row.get('aliases') else "None"
    print(f"  • Actor: {row['name']} (Aliases: {aliases})")

print("\n" + "=" * 60)
print("🔗 REAL RELATIONSHIPS CONNECTING ACTORS TO MALWARE & TOOLS:")
print("=" * 60)
rels = neo4j_manager.execute_query("""
    MATCH (a:ThreatActor)-[r:USES]->(tool)
    RETURN a.name AS actor, type(r) AS rel, labels(tool)[0] AS target_type, tool.name AS target_name
    LIMIT 10
""")
for row in rels:
    print(f"  • {row['actor']} --[{row['rel']}]--> {row['target_name']} ({row['target_type']})")

print("\n" + "=" * 60)
print("🌐 MALICIOUS INFRASTRUCTURE (IPs / Domains) IN DATABASE:")
print("=" * 60)
infra = neo4j_manager.execute_query("""
    MATCH (m:Malware)-[r:CONTACTS]->(target)
    RETURN m.name AS malware, labels(target)[0] AS infra_type, target.value AS value
    LIMIT 6
""")
for row in infra:
    print(f"  • Malware '{row['malware']}' CONTACTS {row['infra_type']}: {row['value']}")

print("=" * 60)
