#!/usr/bin/env python3
"""M06 lab — Storing LLM-extracted Entities and Relationships in Neo4j.

Offline: Python standard library only. No `neo4j` driver, no network, no random.
The write path (batch MERGE, UNWIND bulk insert, idempotency, constraint,
update/delete diff, transaction sizing, driver call sequence) is simulated in
memory while the generated Cypher stays valid for a real Neo4j 5 server.
"""
import sys
from collections import OrderedDict

# Labels resolve from an allowlist — never from raw LLM output.
ENTITY_TYPE_TO_LABEL = {"PERSON": "Person", "ORGANIZATION": "Organization",
                        "TECHNOLOGY": "Technology", "LOCATION": "Location"}

# Deterministic sample: LLM-extracted triples with chunk provenance.
# t1 and t6 share head/tail/type but differ by chunk_id, so they must produce
# two distinct relationships (provenance is part of edge identity).
TRIPLES = [
    {"head": "Ada Lovelace", "head_type": "PERSON", "rel": "WORKED_AT",
     "tail": "Analytical Engine Project", "tail_type": "ORGANIZATION",
     "chunk_id": "c01", "confidence": 0.93},
    {"head": "Ada Lovelace", "head_type": "PERSON", "rel": "USES",
     "tail": "Analytical Engine", "tail_type": "TECHNOLOGY",
     "chunk_id": "c01", "confidence": 0.88},
    {"head": "Charles Babbage", "head_type": "PERSON", "rel": "FOUNDED",
     "tail": "Analytical Engine Project", "tail_type": "ORGANIZATION",
     "chunk_id": "c02", "confidence": 0.91},
    {"head": "Analytical Engine Project", "head_type": "ORGANIZATION",
     "rel": "LOCATED_IN", "tail": "London", "tail_type": "LOCATION",
     "chunk_id": "c03", "confidence": 0.76},
    {"head": "Ada Lovelace", "head_type": "PERSON", "rel": "COLLABORATED_WITH",
     "tail": "Charles Babbage", "tail_type": "PERSON",
     "chunk_id": "c02", "confidence": 0.84},
    {"head": "Ada Lovelace", "head_type": "PERSON", "rel": "WORKED_AT",
     "tail": "Analytical Engine Project", "tail_type": "ORGANIZATION",
     "chunk_id": "c04", "confidence": 0.79},
]


def slug(text):
    """Canonical node id — deterministic, lowercase, ASCII-safe."""
    return "".join(ch if ch.isalnum() else "_" for ch in text.lower()).strip("_")


# --------------------------------------------------------------------------
# Exercise 1 — Triple -> Cypher batch generator (UNWIND)
# --------------------------------------------------------------------------
def build_batch_statements(triples):
    """Group triples by (head label, rel type, tail label): one UNWIND batch each.

    Labels and relationship types are interpolated from the allowlist mapping;
    every value travels as the `$rows` parameter.
    """
    groups = OrderedDict()
    for t in triples:
        key = (ENTITY_TYPE_TO_LABEL[t["head_type"]], t["rel"],
               ENTITY_TYPE_TO_LABEL[t["tail_type"]])
        groups.setdefault(key, []).append(t)
    statements = []
    for (head_label, rel_type, tail_label), items in groups.items():
        rows = [OrderedDict([("head_id", slug(t["head"])),
                             ("head_name", t["head"]),
                             ("tail_id", slug(t["tail"])),
                             ("tail_name", t["tail"]),
                             ("chunk_id", t["chunk_id"]),
                             ("confidence", t["confidence"])]) for t in items]
        cypher = (
            "UNWIND $rows AS row\n"
            "MERGE (h:{hl} {{id: row.head_id}})\n"
            "  ON CREATE SET h.name = row.head_name\n"
            "MERGE (t:{tl} {{id: row.tail_id}})\n"
            "  ON CREATE SET t.name = row.tail_name\n"
            "MERGE (h)-[r:{rel} {{chunk_id: row.chunk_id}}]->(t)\n"
            "  ON CREATE SET r.confidence = row.confidence\n"
            "  ON MATCH SET r.confidence = row.confidence"
        ).format(hl=head_label, tl=tail_label, rel=rel_type)
        statements.append({"group": (head_label, rel_type, tail_label),
                           "cypher": cypher, "rows": rows})
    return statements


def exercise_1() -> bool:
    print("\n--- Exercise 1: Triple -> Cypher batch generator (UNWIND) ---")
    statements = build_batch_statements(TRIPLES)
    print("triples=%d  batch statements=%d" % (len(TRIPLES), len(statements)))
    for st in statements:
        print("  group=%-42s rows=%d" % ("->".join(st["group"]), len(st["rows"])))
    print("first statement:\n" + statements[0]["cypher"])
    assert sum(len(st["rows"]) for st in statements) == len(TRIPLES)
    assert len(statements) == 5, len(statements)
    for st in statements:
        assert st["cypher"].startswith("UNWIND $rows AS row"), st["cypher"]
        assert "MERGE (h:" in st["cypher"] and "MERGE (t:" in st["cypher"]
        assert "-[r:" in st["cypher"] and "$rows" in st["cypher"]
        head_label, rel_type, tail_label = st["group"]
        assert head_label in ENTITY_TYPE_TO_LABEL.values()
        assert tail_label in ENTITY_TYPE_TO_LABEL.values()
        assert " " not in rel_type
    print("[ok] every group produced one parameterized UNWIND batch statement")
    return True


# --------------------------------------------------------------------------
# Exercise 2 — Idempotent merge simulator (MERGE vs CREATE)
# --------------------------------------------------------------------------
class InMemoryGraph:
    """semantics='merge' dedupes by identity key (MERGE); 'create' appends blindly."""

    def __init__(self, semantics="merge"):
        self.semantics = semantics
        self.node_keys, self.edge_keys = [], []
        self.node_props, self.edge_props = {}, {}
        self.stats = {"nodes_created": 0, "nodes_matched": 0,
                      "edges_created": 0, "edges_matched": 0}

    def write_node(self, label, node_id, name):
        key = (label, node_id)
        if self.semantics == "merge" and key in self.node_props:
            self.stats["nodes_matched"] += 1
            self.node_props[key]["name"] = name
            return
        self.stats["nodes_created"] += 1
        self.node_keys.append(key)
        self.node_props.setdefault(key, {"label": label, "id": node_id, "name": name})

    def write_edge(self, head_label, head_id, rel_type, tail_label, tail_id,
                   chunk_id, confidence):
        key = (head_label, head_id, rel_type, tail_label, tail_id, chunk_id)
        if self.semantics == "merge" and key in self.edge_props:
            self.stats["edges_matched"] += 1
            self.edge_props[key] = confidence
            return
        self.stats["edges_created"] += 1
        self.edge_keys.append(key)
        self.edge_props[key] = confidence

    def node_count(self):
        return len(self.node_keys)

    def edge_count(self):
        return len(self.edge_keys)


def apply_batch(graph, statements):
    """Execute the generated statements against the simulated graph."""
    for st in statements:
        head_label, rel_type, tail_label = st["group"]
        for row in st["rows"]:
            graph.write_node(head_label, row["head_id"], row["head_name"])
            graph.write_node(tail_label, row["tail_id"], row["tail_name"])
            graph.write_edge(head_label, row["head_id"], rel_type, tail_label,
                             row["tail_id"], row["chunk_id"], row["confidence"])


def exercise_2() -> bool:
    print("\n--- Exercise 2: Idempotent merge simulator (MERGE vs CREATE) ---")
    statements = build_batch_statements(TRIPLES)
    merged = InMemoryGraph("merge")
    apply_batch(merged, statements)
    first_pass = (merged.node_count(), merged.edge_count())
    apply_batch(merged, statements)
    second_pass = (merged.node_count(), merged.edge_count())
    created = InMemoryGraph("create")
    apply_batch(created, statements)
    create_first = (created.node_count(), created.edge_count())
    apply_batch(created, statements)
    create_second = (created.node_count(), created.edge_count())
    print("MERGE  pass1 nodes/edges=%s  pass2=%s" % (first_pass, second_pass))
    print("CREATE pass1 nodes/edges=%s  pass2=%s" % (create_first, create_second))
    print("MERGE counters: %s" % merged.stats)
    assert first_pass == (5, 6), first_pass
    assert second_pass == (5, 6), second_pass
    assert merged.stats["nodes_matched"] > 0 and merged.stats["edges_matched"] > 0
    assert create_first == (12, 6), create_first
    assert create_second == (24, 12), create_second
    print("[ok] MERGE is idempotent on re-run; CREATE doubles the graph")
    return True


# --------------------------------------------------------------------------
# Exercise 3 — Uniqueness constraint validation
# --------------------------------------------------------------------------
def expected_constraint_ddl():
    return ("CREATE CONSTRAINT entity_id_unique IF NOT EXISTS\n"
            "FOR (n:Entity) REQUIRE n.id IS UNIQUE")


def validate_uniqueness_constraint(candidates):
    """Simulate `REQUIRE n.id IS UNIQUE` over the incoming write set."""
    violations, seen = [], {}
    for cand in candidates:
        label, node_id = cand["label"], cand["id"]
        if not node_id:
            violations.append({"label": label, "id": node_id, "rule": "id_not_null"})
            continue
        key = (label, node_id)
        if key in seen:
            violations.append({"label": label, "id": node_id,
                               "rule": "id_unique", "first_seen": seen[key]})
        else:
            seen[key] = cand["name"]
    return violations


def exercise_3() -> bool:
    print("\n--- Exercise 3: Uniqueness constraint validation ---")
    candidates = [
        {"label": "Person", "id": slug("Ada Lovelace"), "name": "Ada Lovelace"},
        {"label": "Person", "id": slug("Charles Babbage"), "name": "Charles Babbage"},
        {"label": "Person", "id": slug("Ada Lovelace"), "name": "A. Lovelace"},
        {"label": "Organization", "id": slug("Analytical Engine Project"),
         "name": "Analytical Engine Project"},
        {"label": "Location", "id": "", "name": "London"},
    ]
    violations = validate_uniqueness_constraint(candidates)
    print("constraint DDL:\n" + expected_constraint_ddl())
    print("candidates=%d  violations=%d" % (len(candidates), len(violations)))
    for v in violations:
        print("  %s  id=%r  rule=%s" % (v["label"], v["id"], v["rule"]))
    assert len(violations) == 2, violations
    assert sorted(v["rule"] for v in violations) == ["id_not_null", "id_unique"]
    assert violations[0]["first_seen"] == "Ada Lovelace"
    print("[ok] duplicate id and empty id are both rejected before the write")
    return True


# --------------------------------------------------------------------------
# Exercise 4 — Relationship update / delete diff and orphan cleanup
# --------------------------------------------------------------------------
def edge_set(triples):
    return {(ENTITY_TYPE_TO_LABEL[t["head_type"]], slug(t["head"]), t["rel"],
             ENTITY_TYPE_TO_LABEL[t["tail_type"]], slug(t["tail"]), t["chunk_id"])
            for t in triples}


def diff_relationships(current_edges, desired_edges):
    return (sorted(desired_edges - current_edges),
            sorted(current_edges - desired_edges))


def node_degree(edges):
    degree = {}
    for head_label, head_id, _rel, tail_label, tail_id, _chunk in edges:
        degree[(head_label, head_id)] = degree.get((head_label, head_id), 0) + 1
        degree[(tail_label, tail_id)] = degree.get((tail_label, tail_id), 0) + 1
    return degree


def orphan_nodes(nodes, edges):
    degree = node_degree(edges)
    return sorted(n for n in nodes if degree.get(n, 0) == 0)


def exercise_4() -> bool:
    print("\n--- Exercise 4: Relationship update/delete diff ---")
    current = edge_set(TRIPLES)
    # The re-extraction no longer supports USES and COLLABORATED_WITH here.
    desired = edge_set([t for t in TRIPLES if t["chunk_id"] not in ("c01", "c02")
                        or t["rel"] not in ("USES", "COLLABORATED_WITH")])
    to_add, to_delete = diff_relationships(current, desired)
    nodes = {(e[0], e[1]) for e in current} | {(e[3], e[4]) for e in current}
    remaining = current - set(to_delete)
    orphans = orphan_nodes(nodes, remaining)
    print("current edges=%d  desired edges=%d" % (len(current), len(desired)))
    print("to_add=%d  to_delete=%d" % (len(to_add), len(to_delete)))
    for e in to_delete:
        print("  DELETE %s(%s)-[:%s]->%s(%s)" % (e[0], e[1], e[2], e[3], e[4]))
    print("orphan nodes after delete=%s" % [n[1] for n in orphans])
    assert len(to_delete) == 2, to_delete
    assert to_add == [], to_add
    assert orphans == [("Technology", "analytical_engine")], orphans
    # DETACH DELETE removes the node and every attached relationship.
    victim = ("Person", "ada_lovelace")
    cascaded = {e for e in remaining
                if (e[0], e[1]) != victim and (e[3], e[4]) != victim}
    print("DETACH DELETE %s -> edges %d -> %d"
          % (victim[1], len(remaining), len(cascaded)))
    assert len(cascaded) == 2, cascaded
    print("[ok] stale relationships removed, orphan detected, cascade delete bounded")
    return True


# --------------------------------------------------------------------------
# Exercise 5 — Batch transaction sizing
# --------------------------------------------------------------------------
def chunk_rows(row_count, batch_size):
    return [(start, min(start + batch_size, row_count))
            for start in range(0, row_count, batch_size)]


def estimate_seconds(row_count, batch_size, tx_overhead_ms=4.0, row_ms=0.08,
                     pool_size=4):
    """T = (ceil(N / B) * t_tx + N * t_row) / pool_size"""
    batches = len(chunk_rows(row_count, batch_size))
    return (batches * tx_overhead_ms + row_count * row_ms) / 1000.0 / pool_size


def exercise_5() -> bool:
    print("\n--- Exercise 5: Batch transaction sizing ---")
    row_count = 1000
    rows = []
    for size in (1, 10, 50, 200, 1000):
        batches = len(chunk_rows(row_count, size))
        seconds = estimate_seconds(row_count, size)
        rows.append((size, batches, seconds))
        print("  batch_size=%-5d transactions=%-6d est_wall=%.4fs"
              % (size, batches, seconds))
    counts = [r[1] for r in rows]
    times = [r[2] for r in rows]
    assert counts == [1000, 100, 20, 5, 1], counts
    assert all(times[i] > times[i + 1] for i in range(len(times) - 1)), times
    print("transaction reduction at batch_size=1000: %.0fx"
          % (rows[0][1] / rows[-1][1]))
    print("[ok] batching cuts round-trips; wall-clock decreases monotonically")
    return True


# --------------------------------------------------------------------------
# Exercise 6 — Driver call sequence simulation
# --------------------------------------------------------------------------
class FakeResult:
    def __init__(self, counters):
        self._counters = counters

    def consume(self):
        return {"counters": self._counters}

    def data(self):
        return []


class FakeSession:
    def __init__(self, graph, calls, database="neo4j", fetch_size=1000):
        self.graph, self.calls = graph, calls
        self.database, self.fetch_size = database, fetch_size
        self.closed = False

    def run(self, query, **params):
        self.calls.append({"query_head": query.splitlines()[0],
                           "param_keys": sorted(params.keys()),
                           "row_count": len(params.get("rows", []))})
        self._execute(query, params)
        return FakeResult({"nodes_created": 0,
                           "relationships_created": len(params.get("rows", []))})

    def _execute(self, query, params):
        head_label = tail_label = rel_type = None
        for line in query.splitlines():
            if line.startswith("MERGE (h:") and "{" in line:
                head_label = line.split("MERGE (h:", 1)[1].split()[0]
            elif line.startswith("MERGE (t:") and "{" in line:
                tail_label = line.split("MERGE (t:", 1)[1].split()[0]
            elif line.startswith("MERGE (h)-[r:"):
                rel_type = line.split("MERGE (h)-[r:", 1)[1].split()[0]
        for row in params.get("rows", []):
            self.graph.write_node(head_label, row["head_id"], row["head_name"])
            self.graph.write_node(tail_label, row["tail_id"], row["tail_name"])
            self.graph.write_edge(head_label, row["head_id"], rel_type, tail_label,
                                  row["tail_id"], row["chunk_id"], row["confidence"])

    def close(self):
        self.closed = True

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        self.close()
        return False


class FakeDriver:
    def __init__(self, uri, auth, graph=None, calls=None):
        self.uri, self.auth, self.graph = uri, auth, graph
        self.calls = calls if calls is not None else []
        self.verified = 0
        self.closed = False

    def verify_connectivity(self):
        self.verified += 1

    def session(self, database=None, **kwargs):
        return FakeSession(self.graph, self.calls, database=database or "neo4j")

    def close(self):
        self.closed = True


def run_write_transaction(driver, statements):
    """Mirrors GraphDatabase.driver -> session(database) -> run(query, **params)."""
    driver.verify_connectivity()
    with driver.session(database="neo4j") as session:
        for st in statements:
            session.run(st["cypher"], rows=st["rows"])
    driver.close()
    return driver


def exercise_6() -> bool:
    print("\n--- Exercise 6: Driver call sequence simulation ---")
    statements = build_batch_statements(TRIPLES)
    graph = InMemoryGraph("merge")
    driver = FakeDriver("bolt://localhost:7687", ("neo4j", "graphrag123"), graph=graph)
    run_write_transaction(driver, statements)
    print("uri=%s  auth=(%s, ***)" % (driver.uri, driver.auth[0]))
    print("verify_connectivity calls=%d" % driver.verified)
    print("session.run calls=%d" % len(driver.calls))
    for i, call in enumerate(driver.calls, 1):
        print("  %d) %s params=%s rows=%d"
              % (i, call["query_head"], call["param_keys"], call["row_count"]))
    naive_calls = len(TRIPLES)
    assert driver.verified == 1
    assert len(driver.calls) == len(statements) == 5
    assert all(c["query_head"] == "UNWIND $rows AS row" for c in driver.calls)
    assert all(c["param_keys"] == ["rows"] for c in driver.calls)
    assert len(driver.calls) < naive_calls
    assert graph.node_count() == 5 and graph.edge_count() == 6
    print("batched run calls=%d vs per-triple run calls=%d"
          % (len(driver.calls), naive_calls))
    print("[ok] one session.run per UNWIND batch; parameters travel as $rows")
    return True


def run_all() -> bool:
    results = [exercise_1(), exercise_2(), exercise_3(),
               exercise_4(), exercise_5(), exercise_6()]
    if all(results):
        print("\n[PASS] All 6/6 exercises passed successfully.")
        return True
    print("\n[FAIL] %d/6 exercises passed." % sum(1 for r in results if r))
    return False


if __name__ == "__main__":
    sys.exit(0 if run_all() else 1)
