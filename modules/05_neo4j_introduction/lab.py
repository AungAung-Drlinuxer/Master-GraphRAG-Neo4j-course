#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""M05 — Introduction to Neo4j. Lab: Property Graph model, Cypher generation/validation,
Constraint/Index DDL, parameterized Query building, index-free adjacency Traversal.
Neo4j server မလိုဘဲ run နိုင်သည်။ Stdlib သာ။ Deterministic။ Offline။"""

import math
import re
import sys
from collections import deque
from dataclasses import dataclass, field
from typing import Dict, List, Tuple

# ---- Property Graph in-memory model (adjacency maps) ----------------------

@dataclass
class Node:
    id: str
    labels: Tuple[str, ...]
    properties: Dict[str, object] = field(default_factory=dict)

@dataclass
class Relationship:
    type: str
    start: str
    end: str
    properties: Dict[str, object] = field(default_factory=dict)

class PropertyGraph:
    """Node/Relationship များကို adjacency map ဖြင့် store လုပ်သည်။"""

    def __init__(self) -> None:
        self.nodes: Dict[str, Node] = {}
        self.relationships: List[Relationship] = []
        self.out_adj: Dict[str, List[Tuple[str, str]]] = {}
        self.in_adj: Dict[str, List[Tuple[str, str]]] = {}

    def add_node(self, node_id: str, labels: Tuple[str, ...], **props: object) -> Node:
        node = Node(node_id, tuple(labels), dict(props))
        self.nodes[node_id] = node
        self.out_adj.setdefault(node_id, [])
        self.in_adj.setdefault(node_id, [])
        return node

    def add_relationship(self, rel_type: str, start: str, end: str, **props: object) -> Relationship:
        if start not in self.nodes or end not in self.nodes:
            raise ValueError("relationship endpoint မရှိသော node: " + start + " / " + end)
        rel = Relationship(rel_type, start, end, dict(props))
        self.relationships.append(rel)
        self.out_adj[start].append((rel_type, end))
        self.in_adj[end].append((rel_type, start))
        return rel

    def out_edges(self, node_id: str) -> List[Tuple[str, str]]:
        return list(self.out_adj.get(node_id, []))

    def degree(self, node_id: str) -> int:
        return len(self.out_adj.get(node_id, [])) + len(self.in_adj.get(node_id, []))

def build_sample_graph() -> PropertyGraph:
    g = PropertyGraph()
    g.add_node("p1", ("Person",), name="Aung Aung", age=34)
    g.add_node("p2", ("Person",), name="Su Su", age=29)
    g.add_node("c1", ("Company",), name="GraphRAG Labs")
    g.add_node("t1", ("Technology",), name="Neo4j")
    g.add_relationship("KNOWS", "p1", "p2", since=2019)
    g.add_relationship("WORKS_AT", "p1", "c1", role="Data Engineer")
    g.add_relationship("WORKS_AT", "p2", "c1", role="ML Engineer")
    g.add_relationship("USES", "c1", "t1", since=2021)
    g.add_relationship("USES", "p1", "t1", since=2024)
    return g

# ---- Cypher generation ---------------------------------------------------

def cypher_merge_node(node: Node) -> Tuple[str, Dict[str, object]]:
    lines = ["MERGE (n:" + node.labels[0] + " {id: $id})"]
    sets = ["n." + k + " = $" + k for k in sorted(node.properties)]
    if sets:
        lines.append("SET " + ", ".join(sets))
    lines.append("RETURN n")
    params: Dict[str, object] = {"id": node.id}
    params.update(node.properties)
    return "\n".join(lines), params

def cypher_merge_relationship(rel: Relationship, start: Node, end: Node) -> Tuple[str, Dict[str, object]]:
    lines = [
        "MATCH (a:" + start.labels[0] + " {id: $start_id})",
        "MATCH (b:" + end.labels[0] + " {id: $end_id})",
        "MERGE (a)-[r:" + rel.type + "]->(b)",
    ]
    sets = ["r." + k + " = $" + k for k in sorted(rel.properties)]
    if sets:
        lines.append("SET " + ", ".join(sets))
    lines.append("RETURN r")
    params: Dict[str, object] = {"start_id": rel.start, "end_id": rel.end}
    params.update(rel.properties)
    return "\n".join(lines), params

# ---- Cypher validation: clause order, bracket balance, parameter use ------

_CLAUSE_RE = re.compile(
    r"\b(OPTIONAL\s+MATCH|DETACH\s+DELETE|MATCH|WHERE|WITH|CREATE|MERGE|SET"
    r"|DELETE|REMOVE|ORDER\s+BY|SKIP|LIMIT|UNWIND|RETURN)\b"
)
_CLAUSE_RANK = {
    "UNWIND": 0, "OPTIONAL MATCH": 1, "MATCH": 1, "WHERE": 2, "WITH": 3,
    "CREATE": 4, "MERGE": 4, "SET": 5, "REMOVE": 5, "DETACH DELETE": 6,
    "DELETE": 6, "RETURN": 7, "ORDER BY": 8, "SKIP": 9, "LIMIT": 10,
}
_LITERAL_ID_RE = re.compile(r"\{\s*id\s*:\s*(?:'[^']*'|\"[^\"]*\"|\d+)")

def clause_sequence(statement: str) -> List[Tuple[str, int]]:
    return [(" ".join(m.group(1).split()), m.start()) for m in _CLAUSE_RE.finditer(statement)]

def validate_cypher(statement: str) -> List[str]:
    violations: List[str] = []
    if statement.count("(") != statement.count(")"):
        violations.append("unbalanced_parentheses")
    if statement.count("[") != statement.count("]"):
        violations.append("unbalanced_brackets")
    ranks = [_CLAUSE_RANK[tok] for tok, _ in clause_sequence(statement)]
    if any(ranks[i] > ranks[i + 1] for i in range(len(ranks) - 1)):
        violations.append("illegal_clause_order")
    if _LITERAL_ID_RE.search(statement):
        violations.append("literal_identity_value")
    if "$" not in statement:
        violations.append("missing_parameter")
    return violations

# ---- Constraint / Index DDL ----------------------------------------------

SCHEMA_DDL = [
    "CREATE CONSTRAINT person_id_unique IF NOT EXISTS FOR (n:Person) REQUIRE n.id IS UNIQUE",
    "CREATE INDEX person_name_range IF NOT EXISTS FOR (n:Person) ON (n.name)",
    "CREATE FULLTEXT INDEX entity_fulltext IF NOT EXISTS FOR (n:Entity) ON EACH [n.name, n.description]",
]

def classify_schema_ddl(ddl: str) -> str:
    u = " ".join(ddl.upper().split())
    if "CONSTRAINT" in u and "IS UNIQUE" in u:
        return "uniqueness_constraint"
    if "FULLTEXT INDEX" in u:
        return "fulltext_index"
    if "INDEX" in u and " ON " in u:
        return "range_index"
    return "unknown"

# ---- Parameterization ----------------------------------------------------

# clause keyword များ (MATCH/MERGE/SET) သည် legitimate template တွင် ပါနိုင်သည်။
# ဤစာရင်းသည် statement smuggling ကို ညွှန်ပြသော marker များသာ ဖြစ်သည်။
_INJECTION_MARKERS = (";", "--", "/*", "*/", "DETACH DELETE", "DROP ", "LOAD CSV")
_LABEL_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")

def detect_injection(query_text: str) -> List[str]:
    upper = query_text.upper()
    return [m for m in _INJECTION_MARKERS if m.upper() in upper]

def validate_identifier(name: str) -> bool:
    """Label/Relationship type ကို Cypher တွင် parameterize လုပ်မရ — whitelist regex လိုသည်။"""
    return bool(_LABEL_RE.match(name))

def build_parameterized_query(template: str, params: Dict[str, object]) -> Tuple[str, Dict[str, object]]:
    """Query text နှင့် value များကို သီးခြားစီ ထားရှိသည်။"""
    return template, dict(params)

# ---- Traversal: index-free adjacency simulation --------------------------

def traverse(graph: PropertyGraph, start_id: str, max_depth: int):
    """Directed BFS — (visited, levels, traversals) ပြန်ပေးသည်။"""
    visited = {start_id}
    levels = {start_id: 0}
    traversals = 0
    queue = deque([start_id])
    while queue:
        cur = queue.popleft()
        depth = levels[cur]
        if depth == max_depth:
            continue
        for _rtype, nxt in graph.out_edges(cur):
            traversals += 1
            if nxt not in visited:
                visited.add(nxt)
                levels[nxt] = depth + 1
                queue.append(nxt)
    return visited, levels, traversals

def shortest_path(graph: PropertyGraph, src: str, dst: str) -> List[str]:
    prev: Dict[str, str] = {}
    seen = {src}
    queue = deque([src])
    while queue:
        cur = queue.popleft()
        if cur == dst:
            path = [cur]
            while path[-1] != src:
                path.append(prev[path[-1]])
            return list(reversed(path))
        for _rtype, nxt in graph.out_edges(cur):
            if nxt not in seen:
                seen.add(nxt)
                prev[nxt] = cur
                queue.append(nxt)
    return []

def index_lookups(visited: int, total_nodes: int) -> int:
    """Index-based engine သည် hop တစ်ခုစီအတွက် index lookup တစ်ခု လိုသည် — O(log N)။"""
    if total_nodes <= 1:
        return visited
    return visited * max(1, int(math.ceil(math.log(total_nodes, 2))))

# ---- Exercises -----------------------------------------------------------

def exercise_1() -> bool:
    print("\n--- Exercise 1: Property Graph in-memory model ---")
    g = build_sample_graph()
    print("nodes      :", len(g.nodes), sorted(g.nodes))
    print("rels       :", len(g.relationships))
    labels = sorted({lb for n in g.nodes.values() for lb in n.labels})
    print("labels     :", labels)
    print("p1 props   :", g.nodes["p1"].properties)
    print("p1 degree  :", g.degree("p1"), "| c1 degree:", g.degree("c1"))
    assert len(g.nodes) == 4
    assert len(g.relationships) == 5
    assert labels == ["Company", "Person", "Technology"]
    assert g.nodes["p1"].properties["name"] == "Aung Aung"
    assert g.degree("p1") == 3 and g.degree("c1") == 3
    assert g.relationships[0].type == "KNOWS"
    assert (g.relationships[0].start, g.relationships[0].end) == ("p1", "p2")
    return True

def exercise_2() -> bool:
    print("\n--- Exercise 2: Cypher MERGE generation ---")
    g = build_sample_graph()
    node_stmt, node_params = cypher_merge_node(g.nodes["p1"])
    rel_stmt, rel_params = cypher_merge_relationship(g.relationships[0], g.nodes["p1"], g.nodes["p2"])
    print(node_stmt)
    print("params:", node_params)
    print("---")
    print(rel_stmt)
    print("params:", rel_params)
    assert node_stmt.splitlines()[0] == "MERGE (n:Person {id: $id})"
    assert "SET n.age = $age, n.name = $name" in node_stmt
    assert node_params == {"id": "p1", "name": "Aung Aung", "age": 34}
    assert "MERGE (a)-[r:KNOWS]->(b)" in rel_stmt
    assert rel_stmt.startswith("MATCH (a:Person {id: $start_id})")
    assert rel_params == {"start_id": "p1", "end_id": "p2", "since": 2019}
    assert "'" not in node_stmt and "'" not in rel_stmt
    return True

def exercise_3() -> bool:
    print("\n--- Exercise 3: Cypher statement parsing and validation ---")
    cases = [
        ("MATCH (a:Person {id: $id})-[:KNOWS]->(b:Person) RETURN b.name AS name", True),
        ("MERGE (n:Person {id: $id}) SET n.name = $name RETURN n", True),
        ("MATCH (a:Person {id: $id} RETURN a", False),
        ("RETURN n MATCH (n:Person {id: $id})", False),
        ("MERGE (n:Person {id: 'p1'}) RETURN n", False),
    ]
    for stmt, expected_valid in cases:
        seq = [tok for tok, _ in clause_sequence(stmt)]
        violations = validate_cypher(stmt)
        print("clauses   :", seq)
        print("violations:", violations if violations else "none")
        print("statement :", stmt)
        print("-")
        assert (len(violations) == 0) == expected_valid
    assert "unbalanced_parentheses" in validate_cypher("MATCH (a:Person {id: $id} RETURN a")
    assert "illegal_clause_order" in validate_cypher("RETURN n MATCH (n:Person {id: $id})")
    assert "literal_identity_value" in validate_cypher("MERGE (n:Person {id: 'p1'}) RETURN n")
    assert clause_sequence("MATCH (n) WHERE n.id = $id RETURN n")[0][0] == "MATCH"
    return True

def exercise_4() -> bool:
    print("\n--- Exercise 4: Constraint and Index definitions ---")
    kinds = [classify_schema_ddl(d) for d in SCHEMA_DDL]
    for kind, ddl in zip(kinds, SCHEMA_DDL):
        print(kind.ljust(22), "|", ddl)
    assert kinds == ["uniqueness_constraint", "range_index", "fulltext_index"]
    assert "IS UNIQUE" in SCHEMA_DDL[0] and "REQUIRE" in SCHEMA_DDL[0]
    assert "ON (n.name)" in SCHEMA_DDL[1]
    assert "ON EACH [n.name, n.description]" in SCHEMA_DDL[2]
    assert all("IF NOT EXISTS" in d for d in SCHEMA_DDL)
    print("Note: uniqueness constraint သည် lookup node အဖြစ် ပါ index သဘောလည်း ဆောင်သည်။")
    return True

def exercise_5() -> bool:
    print("\n--- Exercise 5: Parameterized query builder and injection defense ---")
    template = "MERGE (n:Person {id: $id}) SET n.name = $name RETURN n"
    payload_name = "Robert'); MATCH (n) DETACH DELETE n;//"
    query, params = build_parameterized_query(template, {"id": "p1", "name": payload_name})
    print("parameterized query :", query)
    print("params['name']      :", repr(params["name"]))
    print("markers in query    :", detect_injection(query))
    naive = "MERGE (n:Person {id: 'p1'}) SET n.name = '" + payload_name + "' RETURN n"
    print("naive query         :", naive)
    print("markers in naive    :", detect_injection(naive))
    assert detect_injection(query) == []
    assert params["name"] == payload_name
    assert payload_name not in query
    assert "DETACH DELETE" in detect_injection(naive) and ";" in detect_injection(naive)
    assert validate_identifier("Person") is True
    assert validate_identifier("Person`) DETACH DELETE (n") is False
    print("label whitelist     :", validate_identifier("Person"), validate_identifier("Person`) DETACH DELETE (n"))
    return True

def exercise_6() -> bool:
    print("\n--- Exercise 6: Index-free adjacency traversal ---")
    g = build_sample_graph()
    visited, levels, traversals = traverse(g, "p1", 2)
    print("visited (2-hop from p1):", sorted(visited))
    print("levels                 :", {k: levels[k] for k in sorted(levels)})
    print("edge traversals        :", traversals)
    assert visited == {"p1", "p2", "c1", "t1"}
    assert traversals == 5
    assert (levels["p1"], levels["p2"], levels["c1"], levels["t1"]) == (0, 1, 1, 1)
    path = shortest_path(g, "p2", "t1")
    print("shortest path p2 -> t1 :", " -> ".join(path), "(hops =", len(path) - 1, ")")
    assert path == ["p2", "c1", "t1"] and len(path) - 1 == 2
    # Graph ကြီးလာသော်လည်း traversal cost သည် edge count ပေါ်တွင်သာ မှီခိုသည်။
    for i in range(1000):
        g.add_node("iso_" + str(i), ("Isolated",))
    _v2, _l2, traversals_big = traverse(g, "p1", 2)
    lookups_small = index_lookups(len(visited), 4)
    lookups_big = index_lookups(len(visited), 1004)
    print("nodes              : 4 -> 1004")
    print("edge traversals    :", traversals, "->", traversals_big)
    print("index lookups      :", lookups_small, "->", lookups_big)
    assert traversals_big == traversals
    assert lookups_big >= lookups_small
    assert len(g.nodes) == 1004
    return True

def run_all() -> bool:
    exercises = [exercise_1, exercise_2, exercise_3, exercise_4, exercise_5, exercise_6]
    try:
        for fn in exercises:
            if not fn():
                return False
    except AssertionError as exc:
        print("\n[FAIL] assertion error:", exc)
        return False
    print("\n[PASS] All 6/6 exercises passed successfully.")
    return True

if __name__ == "__main__":
    sys.exit(0 if run_all() else 1)
