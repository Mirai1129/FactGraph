import os
import shutil

from dotenv import load_dotenv
from neo4j import GraphDatabase

load_dotenv()

NEO4J_URI = os.getenv("NEO4J_URI")
NEO4J_USER = os.getenv("NEO4J_USER")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD")
NEO4J_DATABASE = os.getenv("NEO4J_DATABASE", "neo4j")

WSL_EXPORT_DIR = "/mnt/c/neo4j-output"
WSL_EXPORT_FILE = f"{WSL_EXPORT_DIR}/kg-raw-graph.csv"
WIN_EXPORT_FILE = "file:C:/neo4j-output/kg-raw-graph.csv"

WSL_DEST_DIR = "/home/karca5103/dev/FactGraph/data/raw/knowledge-graph/"
WSL_DEST_FILE = f"{WSL_DEST_DIR}neo4j-kg-raw-graph.csv"

os.makedirs(WSL_EXPORT_DIR, exist_ok=True)
os.makedirs(WSL_DEST_DIR, exist_ok=True)

driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))


def export_full_graph_to_csv() -> None:
    cypher = f"""
    CALL apoc.export.csv.query(
      "MATCH (h)-[r]->(t)
       RETURN h.name  AS head,
              type(r) AS relation,
              t.name  AS tail,
              properties(h) AS head_props,
              properties(r) AS rel_props,
              properties(t) AS tail_props",
      "{WIN_EXPORT_FILE}",
      {{}})
    YIELD file, nodes, relationships, properties, time
    RETURN file, nodes, relationships, properties, time
    """
    with driver.session(database=NEO4J_DATABASE) as s:
        rec = s.run(cypher).single()
        if not rec:
            raise RuntimeError("APOC 匯出失敗")
        print(f"✅ 匯出完成：{rec['file']}")
        print(f"   節點 {rec['nodes']}、關係 {rec['relationships']}、屬性 {rec['properties']} (耗時 {rec['time']} ms)")


def move_to_wsl() -> None:
    shutil.copy2(WSL_EXPORT_FILE, WSL_DEST_FILE)
    print(f"🚚 已搬至：{WSL_DEST_FILE}")


if __name__ == "__main__":
    export_full_graph_to_csv()
    move_to_wsl()
    driver.close()
    print("🎉 全流程完成！")
