#!/usr/bin/env python3
"""M07 — Knowledge Graph-based RAG (GraphRAG): executable lab.

Standard library only, deterministic, offline: the property graph, the vector
index and the language model are simulated in memory with scripted data.
"""

import itertools
import math
import re
import sys
import unicodedata
from collections import defaultdict, deque
from difflib import SequenceMatcher

# --- Fixture: in-memory property graph + simulated vector index -------------
# node id -> (label, name, aliases, summary)
NODES = {
    "co:neo4j": ("Company", "Neo4j", ("Neo4j Inc", "Neo4j, Inc."), "Graph database vendor."),
    "prod:aura": ("Product", "AuraDB", ("Neo4j AuraDB", "Aura"), "Managed cloud graph database service."),
    "tech:cypher": ("Technology", "Cypher", ("openCypher", "Cypher Query Language"), "Declarative graph query language."),
    "tech:louvain": ("Technology", "Louvain", ("Louvain method",), "Greedy modularity optimisation for community detection."),
    "org:cnrs": ("Organization", "CNRS", (), "Research organisation of the Louvain authors."),
    "person:eifrem": ("Person", "Vincent Blondel", ("Blondel",), "Lead author of the Louvain method."),
    "tech:graphrag": ("Technology", "GraphRAG", ("Graph RAG", "Microsoft GraphRAG"), "Retrieval pattern grounded in a knowledge graph."),
    "tech:vectorindex": ("Technology", "Vector Index", ("vector search index", "HNSW index"), "Approximate nearest neighbour index over embeddings."),
    "org:neo4jeng": ("Team", "Neo4j Engineering", (), "Engineering team maintaining Cypher."),
    "paper:louvain": ("Paper", "Fast unfolding of communities in large networks", (), "The 2008 Louvain method paper."),
}
# (src, rel, dst, provenance chunk id of the passage it was extracted from)
EDGES = (
    ("co:neo4j", "DEVELOPS", "prod:aura", "c1"),
    ("co:neo4j", "CREATES", "tech:cypher", "c2"),
    ("co:neo4j", "EMPLOYS", "org:neo4jeng", "c2"),
    ("prod:aura", "USES", "tech:vectorindex", "c1"),
    ("tech:cypher", "MAINTAINED_BY", "org:neo4jeng", "c2"),
    ("tech:graphrag", "USES", "tech:cypher", "c3"),
    ("co:neo4j", "PUBLISHES", "tech:graphrag", "c3"),
    ("tech:graphrag", "RUNS_ON", "prod:aura", "c3"),
    ("person:eifrem", "AFFILIATED_WITH", "org:cnrs", "c4"),
    ("person:eifrem", "PROPOSED", "tech:louvain", "c4"),
    ("org:cnrs", "PUBLISHES", "tech:louvain", "c4"),
    ("tech:louvain", "DOCUMENTED_IN", "paper:louvain", "c4"),
)
CHUNKS = {
    "c1": "Neo4j AuraDB is a managed cloud service that uses a vector index for retrieval.",
    "c2": "Cypher is the declarative query language created by Neo4j and maintained by its team.",
    "c3": "GraphRAG grounds generation in knowledge graph triples extracted from source text.",
    "c4": "The Louvain method optimises modularity to detect communities in large networks.",
    "c5": "Vector search returns approximate nearest neighbours from an embedding index.",
}
ALLOWED_LABELS = frozenset(node[0] for node in NODES.values())
ADJ = {}
for _src, _rel, _dst, _chunk in EDGES:
    ADJ.setdefault(_src, set()).add(_dst)
    ADJ.setdefault(_dst, set()).add(_src)
ADJ = {node: set(sorted(nb)) for node, nb in ADJ.items()}

# --- Exercise 1: Entity Linking ---------------------------------------------

def _fold(text):
    return unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode().casefold()


def tokenize(text):
    return re.findall(r"[a-z0-9]+", _fold(text))


def fuzzy_score(surface, query):
    """Surface-form match score in [0, 1] between a node name/alias and a query."""
    s, q = " ".join(tokenize(surface)), " ".join(tokenize(query))
    if not s:
        return 0.0
    if s in q:
        return 1.0
    words = set(tokenize(surface))
    if not words:
        return 0.0
    overlap = len(words & set(tokenize(query))) / len(words)
    return round(max(overlap * 0.95, SequenceMatcher(None, s, q).ratio() * 0.6), 4)


def link_query(query, threshold=0.7):
    """Return [(node_id, score, matched_surface)] sorted by score desc, id asc."""
    hits = []
    for node_id in sorted(NODES):
        label, name, aliases, summary = NODES[node_id]
        scored = [(fuzzy_score(s, query), s) for s in (name,) + tuple(aliases)]
        best_score, best_surface = max(scored)
        if best_score >= threshold:
            hits.append((node_id, best_score, best_surface))
    return sorted(hits, key=lambda h: (-h[1], h[0]))


def exercise_1() -> bool:
    print("\n--- Exercise 1: Entity Linking ---")
    queries = (
        "How does Neo4j AuraDB use a vector index for retrieval?",
        "Which algorithm does the Louvain method use to detect communities?",
        "Who proposed the Louvain method?",
    )
    linked = {}
    for query in queries:
        hits = link_query(query)
        linked[query] = [h[0] for h in hits]
        print(f"query: {query}")
        for node_id, score, surface in hits:
            print(f"  -> {node_id:<18} score={score:<6} surface={surface!r}")

    assert linked[queries[0]] == ["co:neo4j", "prod:aura", "tech:vectorindex"], linked[queries[0]]
    assert linked[queries[1]] == ["tech:louvain"], linked[queries[1]]
    assert linked[queries[2]] == ["tech:louvain"], linked[queries[2]]
    assert "org:cnrs" not in linked[queries[0]]
    assert "person:eifrem" not in linked[queries[2]]
    print("[ok] query -> node anchors resolved without false positives")
    return True

# --- Exercise 2: k-hop subgraph retrieval from anchors ----------------------

def k_hop_subgraph(anchor_ids, k, adj=None):
    """Breadth-first expansion up to k hops. Returns (node_ids, edge_indexes)."""
    adj = ADJ if adj is None else adj
    reached = set(anchor_ids)
    frontier = deque(sorted(anchor_ids))
    for _ in range(k):
        nxt = deque()
        while frontier:
            for nb in sorted(adj.get(frontier.popleft(), ())):
                if nb not in reached:
                    reached.add(nb)
                    nxt.append(nb)
        frontier = nxt
        if not frontier:
            break
    idx = [i for i, e in enumerate(EDGES) if e[0] in reached and e[2] in reached]
    return sorted(reached), idx


def exercise_2() -> bool:
    print("\n--- Exercise 2: k-hop Subgraph Retrieval ---")
    hops = {k: k_hop_subgraph(["co:neo4j"], k) for k in (1, 2, 3)}
    for k, (nodes, edges) in hops.items():
        print(f"k={k}: {len(nodes)} nodes, {len(edges)} edges  nodes={nodes}")
    n1, e1 = hops[1]
    n2, e2 = hops[2]
    n3, e3 = hops[3]

    assert n1 == ["co:neo4j", "org:neo4jeng", "prod:aura", "tech:cypher", "tech:graphrag"], n1
    assert e1 == [0, 1, 2, 4, 5, 6, 7], e1
    assert set(n2) - set(n1) == {"tech:vectorindex"}, set(n2) - set(n1)
    assert n2 == n3 and e2 == e3, "expansion must saturate inside the component"
    assert "person:eifrem" not in n3 and "tech:louvain" not in n3
    assert len(e2) == 8, len(e2)
    print("[ok] hop budget controls context size; disjoint component stays out")
    return True

# --- Exercise 3: subgraph -> prompt context serialization -------------------

def serialize_subgraph(node_ids, edge_indexes, max_tokens=4096):
    """Deterministic text block: entity lines first, then relation lines."""
    lines = []
    for node_id in sorted(node_ids):
        label, name, _aliases, summary = NODES[node_id]
        lines.append(f"[ENTITY] id={node_id} | label={label} | name={name} | summary={summary}")
    grouped = sorted((EDGES[i] for i in edge_indexes), key=lambda e: (e[0], e[1], e[2]))
    for src, group in itertools.groupby(grouped, key=lambda e: e[0]):
        lines += [f"[RELATION] {e[0]} -[{e[1]}]-> {e[2]}" for e in group]
    text = "\n".join(lines)
    return text if len(text) // 4 <= max_tokens else text[: max_tokens * 4]


def exercise_3() -> bool:
    print("\n--- Exercise 3: Subgraph Serialization ---")
    nodes, edges = k_hop_subgraph(["co:neo4j"], 2)
    context = serialize_subgraph(nodes, edges)
    print(context)

    lines = context.splitlines()
    entity_lines = [ln for ln in lines if ln.startswith("[ENTITY]")]
    relation_lines = [ln for ln in lines if ln.startswith("[RELATION]")]

    assert len(entity_lines) == len(nodes) == 6, len(entity_lines)
    assert len(relation_lines) == len(edges) == 8, len(relation_lines)
    assert entity_lines == sorted(entity_lines), "entity lines must be id-ordered"
    assert lines[0].startswith("[ENTITY]") and "[RELATION]" not in lines[0]
    assert "[RELATION] co:neo4j -[DEVELOPS]-> prod:aura" in lines
    print(f"[ok] serialized {len(entity_lines)} entities + {len(relation_lines)} relations, "
          f"~{len(context) // 4} tokens")
    return True

# --- Exercise 4: hybrid retrieval fusion (vector chunks + graph triples) ----

def reciprocal_rank_fusion(rankings, k=60):
    """RRF: score(item) = sum over lists of 1 / (k + rank). Tie-break by id asc."""
    scores = defaultdict(float)
    for items in rankings.values():
        for rank, item in enumerate(items, start=1):
            scores[item] += 1.0 / (k + rank)
    return sorted(scores.items(), key=lambda kv: (-kv[1], kv[0]))


def provenance_chunk(item):
    return item[4:] if item.startswith("vec:") else EDGES[int(item[6:])][3]


def dedupe_by_provenance(fused):
    """Keep one item per source chunk; on an equal score the graph triple wins."""
    best = {}
    for item, score in fused:
        chunk = provenance_chunk(item)
        prev = best.get(chunk)
        if prev is None or score > prev[1] or (score == prev[1] and item.startswith("graph:")):
            best[chunk] = (item, score)
    keep = {v[0] for v in best.values()}
    return [item for item, _ in fused if item in keep]


def exercise_4() -> bool:
    print("\n--- Exercise 4: Hybrid Retrieval Fusion ---")
    fused = reciprocal_rank_fusion({"vector": ["vec:c1", "vec:c4", "vec:c2"],
                                    "graph": ["graph:0", "graph:4", "graph:6"]})
    for item, score in fused:
        chunk = provenance_chunk(item)
        print(f"  {item:<10} rrf={score:.6f}  chunk={chunk}  {CHUNKS[chunk][:44]}")
    final = dedupe_by_provenance(fused)
    print(f"fused={[i for i, _ in fused]}")
    print(f"final={final}")

    assert [i for i, _ in fused] == ["graph:0", "vec:c1", "graph:4", "vec:c4", "graph:6", "vec:c2"]
    assert final == ["graph:0", "graph:4", "vec:c4", "graph:6"], final
    assert len(final) == len(fused) - 2, "two colliding vector chunks removed"
    assert final[0] == "graph:0", "top item ranked first in both modalities wins"
    assert len({provenance_chunk(i) for i in final}) == len(final), "one item per chunk"
    print("[ok] RRF merged both rankings, deduplicated by provenance chunk")
    return True

# --- Exercise 5: Text-to-Cypher guardrail validation ------------------------

BLOCK_COMMENT_RE = re.compile(r"/\*.*?\*/", re.DOTALL)
LINE_COMMENT_RE = re.compile(r"//[^\n]*")
STRING_LITERAL_RE = re.compile(r"'(?:[^'\\]|\\.)*'|\"(?:[^\"\\]|\\.)*\"")
REL_DETAIL_RE = re.compile(r"\[[^\]]*\]")
NODE_BLOCK_RE = re.compile(r"\(([^()]*)\)")
LABEL_RE = re.compile(r":\s*([A-Za-z_][A-Za-z0-9_]*)")

FORBIDDEN_KEYWORDS = ("CREATE", "MERGE", "DELETE", "DETACH", "SET", "REMOVE", "DROP",
                      "FOREACH", "LOAD", "CALL", "GRANT", "DENY", "REVOKE", "ALTER", "RENAME")
READ_ONLY_START = ("MATCH", "OPTIONAL MATCH", "WITH", "UNWIND")
MAX_LENGTH = 2000


def _strip_inert(query):
    """Remove comments and string literals: their content cannot mutate anything."""
    query = BLOCK_COMMENT_RE.sub(" ", query)
    return STRING_LITERAL_RE.sub(" '?' ", LINE_COMMENT_RE.sub(" ", query))


def node_labels(query):
    """Extract node labels only — relationship types are stripped first."""
    body = REL_DETAIL_RE.sub(" ", _strip_inert(query))
    return sorted({lab for block in NODE_BLOCK_RE.findall(body)
                   for lab in LABEL_RE.findall(block)})


def validate_cypher(query, allowed_labels=None, max_length=MAX_LENGTH):
    """Return (ok, reason). Read-only enforcement for LLM generated Cypher."""
    if not query or not query.strip():
        return False, "empty query"
    if len(query) > max_length:
        return False, f"query exceeds {max_length} characters"
    body = _strip_inert(query).strip()
    if body.endswith(";"):
        body = body[:-1].strip()
    if ";" in body:
        return False, "multiple statements are not allowed"
    words = set(re.findall(r"[A-Z_]+", body.upper()))
    hit = sorted(kw for kw in FORBIDDEN_KEYWORDS if kw in words)
    if hit:
        return False, f"destructive clause rejected: {', '.join(hit)}"
    first = body.split()[0].upper()
    if first not in READ_ONLY_START:
        return False, f"query must start with a read-only clause, got {first!r}"
    if "RETURN" not in words:
        return False, "query must project results with RETURN"
    if allowed_labels is not None:
        unknown = [lab for lab in node_labels(query) if lab not in allowed_labels]
        if unknown:
            return False, f"labels outside the schema allowlist: {', '.join(unknown)}"
    return True, "read-only query accepted"


def exercise_5() -> bool:
    print("\n--- Exercise 5: Text-to-Cypher Guardrails ---")
    candidates = (
        ("MATCH (p:Product {id: $id}) RETURN p.name AS name, p.summary AS summary", True),
        ("MATCH (c:Company)-[:DEVELOPS]->(p:Product) WHERE c.name = $name "
         "RETURN p.name AS product ORDER BY product LIMIT 10", True),
        ("MATCH (p:Product) DETACH DELETE p", False),
        ("MATCH (n) DROP INDEX n", False),
        ("MATCH (n) SET n.owner = $owner RETURN n", False),
        ("CREATE (n:Product {id: $id}) RETURN n", False),
        ("MATCH (n) RETURN n; MATCH (m) DELETE m", False),
        ("MATCH (n:Product) RETURN n // harmless trailing note", True),
        ("MATCH (x:Secret) RETURN x", False),
    )
    for query, expected_ok in candidates:
        ok, reason = validate_cypher(query, allowed_labels=ALLOWED_LABELS)
        print(f"  ok={str(ok):<5} expected={str(expected_ok):<5} {reason:<45}| {query[:56]}")
        assert ok is expected_ok, f"guardrail mismatch for: {query}"

    rejected = sum(1 for q, _ in candidates if not validate_cypher(q, ALLOWED_LABELS)[0])
    assert rejected == 6, rejected
    print(f"[ok] {rejected}/{len(candidates)} candidates blocked before execution")
    return True

# --- Exercise 6: community detection and hierarchical summarization ---------

def connected_components(adj):
    """Level-1 partition: cheap, deterministic, no resolution parameter."""
    labels, seen = {}, set()
    for start in sorted(adj):
        if start in seen:
            continue
        comp = {start}
        queue = deque([start])
        while queue:
            for nb in sorted(adj[queue.popleft()]):
                if nb not in comp:
                    comp.add(nb)
                    queue.append(nb)
        seen |= comp
        for node in comp:
            labels[node] = start
    return labels


def modularity(partition, adj):
    """Newman modularity Q = sum_c [ L_c/m - (k_c / 2m)^2 ]."""
    m = len(EDGES)
    internal, degree = defaultdict(int), defaultdict(int)
    for node in adj:
        degree[partition[node]] += len(adj[node])
    for src, _rel, dst, _chunk in EDGES:
        if partition[src] == partition[dst]:
            internal[partition[src]] += 1
    return round(sum(internal[lab] / m - (degree[lab] / (2 * m)) ** 2 for lab in degree), 10)


def greedy_modularity_partition(adj, init_labels):
    """Louvain-style single-level refinement: accept only improving moves."""
    labels = dict(init_labels)
    improved = True
    while improved:
        improved = False
        for node in sorted(adj):
            base = modularity(labels, adj)
            best_label, best_gain = labels[node], 1e-12
            for cand in sorted({labels[nb] for nb in adj[node]} - {labels[node]}):
                trial = dict(labels)
                trial[node] = cand
                gain = modularity(trial, adj) - base
                if gain > best_gain:
                    best_gain, best_label = gain, cand
            if best_label != labels[node]:
                labels[node] = best_label
                improved = True
    return labels


def canonicalize(labels):
    order = {}
    for node in sorted(labels):
        order.setdefault(labels[node], len(order))
    return {node: order[label] for node, label in labels.items()}


def community_summaries(labels):
    groups = defaultdict(list)
    for node, label in sorted(labels.items()):
        groups[label].append(node)
    return [(label, members, "Community %d covers: %s" % (
        label, ", ".join(sorted(NODES[m][1] for m in members))))
        for label, members in sorted(groups.items())]


def exercise_6() -> bool:
    print("\n--- Exercise 6: Community Detection ---")
    level0 = {node: node for node in ADJ}
    level1 = canonicalize(connected_components(ADJ))
    level2 = canonicalize(greedy_modularity_partition(ADJ, connected_components(ADJ)))
    q0, q1, q2 = (modularity(p, ADJ) for p in (level0, level1, level2))
    print(f"level 0 (singletons)  communities={len(set(level0.values()))} Q={q0}")
    print(f"level 1 (components)  communities={len(set(level1.values()))} Q={q1}")
    print(f"level 2 (refinement)  communities={len(set(level2.values()))} Q={q2}")
    for _label, members, summary in community_summaries(level2):
        print(f"  {summary}\n    members={members}")

    assert set(level1.values()) == {0, 1}, sorted(set(level1.values()))
    group_a = {n for n, c in level1.items() if c == 0}
    assert group_a == {"co:neo4j", "prod:aura", "tech:cypher", "org:neo4jeng",
                       "tech:graphrag", "tech:vectorindex"}, sorted(group_a)
    assert math.isclose(q1, 4 / 9, abs_tol=1e-9), q1
    assert q2 >= q1 - 1e-12, (q2, q1)
    summaries = community_summaries(level2)
    assert len(summaries) == 2 and all(s.startswith("Community ") for _, _, s in summaries)
    print("[ok] hierarchical partition built; refinement never lowers modularity")
    return True

# --- Runner -----------------------------------------------------------------

def run_all() -> bool:
    exercises = (
        ("Entity Linking", exercise_1),
        ("k-hop Subgraph Retrieval", exercise_2),
        ("Subgraph Serialization", exercise_3),
        ("Hybrid Retrieval Fusion", exercise_4),
        ("Text-to-Cypher Guardrails", exercise_5),
        ("Community Detection", exercise_6),
    )
    passed = 0
    for title, fn in exercises:
        if fn() is True:
            passed += 1
        else:
            print(f"[FAIL] {title}")
    if passed == len(exercises):
        print("\n[PASS] All 6/6 exercises passed successfully.")
        return True
    print(f"\n[FAIL] {passed}/{len(exercises)} exercises passed.")
    return False


if __name__ == "__main__":
    sys.exit(0 if run_all() else 1)
