#!/usr/bin/env python3
"""
M08 — Conclusion: end-to-end mini GraphRAG integration lab.

chunk → scripted extraction → entity resolution → in-memory graph → entity linking →
k-hop retrieval → prompt context serialization → rule-based generation။
Python standard library သာ၊ `random` မသုံး၊ network access မရှိ၊ run တိုင်း output တူညီသည်။
"""

import re
import json
import math
import sys
import hashlib
from collections import OrderedDict, defaultdict

CHARS_PER_TOKEN = 4.0


# --- Exercise 1 — pipeline recap ---

MODULE_MAP = [
    ("M00", "Getting Started", "course architecture, RAG basics, GraphRAG path"),
    ("M01", "Traditional NER and Relation Extraction", "BIO tagging, gazetteer, P/R/F1"),
    ("M02", "LLM Entity and Relation Extraction", "extraction prompt, JSON schema, resolution"),
    ("M03", "Chunking at Scale", "chunk size, overlap, map-reduce, idempotency"),
    ("M04", "Project: Knowledge Graph from Text", "end-to-end ingestion, provenance, export"),
    ("M05", "Neo4j Introduction", "Property Graph, Cypher, constraints, indexes"),
    ("M06", "Storing Entities and Relationships", "batch MERGE, UNWIND, driver session"),
    ("M07", "Knowledge Graph RAG", "entity linking, k-hop subgraph, hybrid retrieval"),
    ("M08", "Conclusion", "production deployment, decision criteria, capstone"),
]

STAGE_DEPS = OrderedDict([
    ("ingest", []),
    ("normalize", ["ingest"]),
    ("chunk", ["normalize"]),
    ("extract", ["chunk"]),
    ("resolve", ["extract"]),
    ("merge_dedup", ["resolve"]),
    ("graph_write", ["merge_dedup"]),
    ("entity_link", []),
    ("retrieve", ["entity_link", "graph_write"]),
    ("serialize", ["retrieve"]),
    ("generate", ["serialize"]),
])


def topological_order(stage_deps):
    """Prerequisite အားလုံး ပြီးသွားသော stage ကို အရင် ရွေးချယ်သည်။"""
    remaining = list(stage_deps.keys())
    order = []
    while remaining:
        progressed = False
        for name in list(remaining):
            if all(dep in order for dep in stage_deps[name]):
                order.append(name)
                remaining.remove(name)
                progressed = True
        if not progressed:
            raise ValueError("cycle detected in stage dependencies")
    return order


def exercise_1() -> bool:
    print("\n--- Exercise 1: Full pipeline recap (stage ordering) ---")
    order = topological_order(STAGE_DEPS)
    print("ingestion + retrieval order: " + " -> ".join(order))
    for module_id, title, focus in MODULE_MAP:
        print(f"  {module_id}  {title:<42} {focus}")
    position = {name: index for index, name in enumerate(order)}
    for name, deps in STAGE_DEPS.items():
        for dep in deps:
            assert position[dep] < position[name], (name, dep)
    assert len(order) == len(STAGE_DEPS)
    assert order[0] == "ingest" and order[-1] == "generate"
    assert len(MODULE_MAP) == 9
    assert MODULE_MAP[0][0] == "M00" and MODULE_MAP[-1][0] == "M08"
    print("prerequisite check: every stage runs after all of its dependencies")
    return True


# --- Exercise 2 — cost / latency model ---

def cost_latency_model(corpus_chars, chunk_chars, prompt_overhead_tokens,
                       tokens_per_triple, triples_per_chunk,
                       price_in_per_1k, price_out_per_1k,
                       base_latency_s, tokens_per_second, workers):
    chunks = max(1, math.ceil(corpus_chars / chunk_chars))
    chunk_tokens = math.ceil(chunk_chars / CHARS_PER_TOKEN)
    input_tokens = chunks * (prompt_overhead_tokens + chunk_tokens)
    output_tokens = chunks * triples_per_chunk * tokens_per_triple
    cost_usd = (input_tokens / 1000.0) * price_in_per_1k + (output_tokens / 1000.0) * price_out_per_1k
    per_chunk_seconds = base_latency_s + (
        prompt_overhead_tokens + chunk_tokens + triples_per_chunk * tokens_per_triple
    ) / tokens_per_second
    sequential_latency_s = chunks * per_chunk_seconds
    parallel_latency_s = math.ceil(chunks / workers) * per_chunk_seconds
    return {
        "chunks": chunks,
        "input_tokens": input_tokens,
        "output_tokens": output_tokens,
        "cost_usd": cost_usd,
        "per_chunk_seconds": per_chunk_seconds,
        "sequential_latency_s": sequential_latency_s,
        "parallel_latency_s": parallel_latency_s,
    }


def retrieval_latency_ms(nodes_scanned, edges_scanned, generation_tokens,
                         generation_tokens_per_second):
    traversal_ms = 4.0 + nodes_scanned * 0.05 + edges_scanned * 0.02
    generation_ms = generation_tokens / generation_tokens_per_second * 1000.0
    return traversal_ms, generation_ms, traversal_ms + generation_ms


def exercise_2() -> bool:
    print("\n--- Exercise 2: Cost / latency model ---")
    config = dict(corpus_chars=48000, chunk_chars=2000, prompt_overhead_tokens=300,
                  tokens_per_triple=30, triples_per_chunk=8,
                  price_in_per_1k=0.5, price_out_per_1k=1.5,
                  base_latency_s=0.15, tokens_per_second=120.0, workers=4)
    base = cost_latency_model(**config)
    print(f"corpus={config['corpus_chars']} chars -> chunks={base['chunks']}")
    print(f"  input tokens  = {base['input_tokens']}")
    print(f"  output tokens = {base['output_tokens']}")
    print(f"  ingestion cost = ${base['cost_usd']:.4f}")
    print(f"  per-chunk latency = {base['per_chunk_seconds']:.3f} s")
    print(f"  sequential latency = {base['sequential_latency_s']:.3f} s")
    print(f"  parallel latency   = {base['parallel_latency_s']:.3f} s")

    bigger = cost_latency_model(**{**config, "corpus_chars": config["corpus_chars"] * 2})
    assert bigger["chunks"] == base["chunks"] * 2
    assert abs(bigger["cost_usd"] - 2 * base["cost_usd"]) < 1e-9
    assert base["cost_usd"] > 0 and base["parallel_latency_s"] < base["sequential_latency_s"]

    wider = cost_latency_model(**{**config, "workers": 8})
    assert abs(wider["parallel_latency_s"] - base["parallel_latency_s"] / 2) < 1e-9

    traversal_ms, generation_ms, total_ms = retrieval_latency_ms(6, 5, 80, 40.0)
    print(f"  query traversal = {traversal_ms:.2f} ms, generation = {generation_ms:.2f} ms")
    print(f"  query total     = {total_ms:.2f} ms  (ingestion is the dominant cost)")
    assert total_ms < base["sequential_latency_s"] * 1000.0
    print("cost doubles with corpus size; workers 4 -> 8 halves parallel latency: OK")
    return True


# --- Exercise 3 — build vs buy decision scorer ---

BUILD_VS_BUY_WEIGHTS = OrderedDict([
    ("time_to_first_value", 0.25),
    ("control_and_customization", 0.20),
    ("operating_cost_at_scale", 0.20),
    ("compliance_and_data_residency", 0.15),
    ("engineering_capacity", 0.20),
])

BUILD_SCORES = OrderedDict([
    ("time_to_first_value", 2.0),
    ("control_and_customization", 5.0),
    ("operating_cost_at_scale", 4.0),
    ("compliance_and_data_residency", 5.0),
    ("engineering_capacity", 2.0),
])

BUY_SCORES = OrderedDict([
    ("time_to_first_value", 5.0),
    ("control_and_customization", 2.0),
    ("operating_cost_at_scale", 2.0),
    ("compliance_and_data_residency", 2.0),
    ("engineering_capacity", 5.0),
])


def weighted_score(scores, weights):
    assert abs(sum(weights.values()) - 1.0) < 1e-9, "weights must sum to 1.0"
    return sum(scores[key] * weight for key, weight in weights.items())


def build_vs_buy(weights, build_scores=BUILD_SCORES, buy_scores=BUY_SCORES):
    score_build = weighted_score(build_scores, weights)
    score_buy = weighted_score(buy_scores, weights)
    decision = "build" if score_build > score_buy else "buy"
    return decision, score_build, score_buy


def exercise_3() -> bool:
    print("\n--- Exercise 3: Build-vs-buy decision scorer ---")
    decision, score_build, score_buy = build_vs_buy(BUILD_VS_BUY_WEIGHTS)
    for key, weight in BUILD_VS_BUY_WEIGHTS.items():
        print(f"  {key:<32} weight={weight:.2f}  build={BUILD_SCORES[key]:.1f}  buy={BUY_SCORES[key]:.1f}")
    print(f"  weighted: build={score_build:.3f}  buy={score_buy:.3f}  -> decision={decision}")
    assert decision == "build"
    assert abs(score_build - 3.45) < 1e-9 and abs(score_buy - 3.35) < 1e-9

    time_first = OrderedDict([
        ("time_to_first_value", 0.40),
        ("control_and_customization", 0.15),
        ("operating_cost_at_scale", 0.15),
        ("compliance_and_data_residency", 0.10),
        ("engineering_capacity", 0.20),
    ])
    decision2, score_build2, score_buy2 = build_vs_buy(time_first)
    print(f"  time-to-value weighted up: build={score_build2:.3f} buy={score_buy2:.3f} -> {decision2}")
    assert decision2 == "buy" and abs(score_build2 - 3.05) < 1e-9 and abs(score_buy2 - 3.80) < 1e-9
    print("decision is weight-sensitive: no single architecture wins under every weighting")
    return True


# --- Exercise 4 — incremental update planner ---

SINGLE_VALUED = {"LEADS", "MANAGES"}


def graph_signature(edges, nodes):
    payload = json.dumps({"nodes": sorted(nodes), "edges": sorted(edges)}, sort_keys=True)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()[:16]


def plan_incremental_update(current_edges, current_nodes, new_triples):
    edges = list(current_edges)
    nodes = set(current_nodes)
    ops = []
    for subject, relation, obj in new_triples:
        for endpoint in (subject, obj):
            if endpoint not in nodes:
                nodes.add(endpoint)
                ops.append(("ADD_NODE", endpoint))
        new_edge = (subject, relation, obj)
        if new_edge in edges:
            ops.append(("NOOP", subject, relation, obj))
            continue
        if relation in SINGLE_VALUED:
            stale = [e for e in edges if e[1] == relation and e[2] == obj]
            for old_edge in stale:
                edges.remove(old_edge)
                ops.append(("DELETE_EDGE",) + old_edge)
        edges.append(new_edge)
        ops.append(("ADD_EDGE", subject, relation, obj))
    return ops, edges, nodes


def exercise_4() -> bool:
    print("\n--- Exercise 4: Incremental update planner ---")
    graph = build_knowledge_graph()
    base_edges = graph.edges()
    base_nodes = set(graph.nodes)
    before = graph_signature(base_edges, base_nodes)

    new_triples = [("Dave", "LEADS", "Payments Squad")]
    ops, edges, nodes = plan_incremental_update(base_edges, base_nodes, new_triples)
    for op in ops:
        print("  " + " ".join(str(part) for part in op))
    assert ("DELETE_EDGE", "Carol", "LEADS", "Payments Squad") in ops
    assert ("ADD_EDGE", "Dave", "LEADS", "Payments Squad") in ops
    assert ("Carol", "LEADS", "Payments Squad") not in edges
    assert ("Dave", "LEADS", "Payments Squad") in edges
    assert "Dave" in nodes and len(nodes) == len(base_nodes) + 1

    ops_again, edges_again, nodes_again = plan_incremental_update(edges, nodes, new_triples)
    assert [op[0] for op in ops_again] == ["NOOP"]
    after = graph_signature(edges, nodes)
    assert graph_signature(edges_again, nodes_again) == after
    assert after != before
    print(f"base signature={before} -> updated signature={after}")
    print("re-applying the same document is idempotent: plan contains NOOP only")
    return True


# --- Exercise 5 — production architecture checklist ---

CHECKLIST = [
    ("entity_uniqueness_constraint", True, True),
    ("ingestion_idempotent_upsert", True, True),
    ("provenance_on_every_triple", True, True),
    ("k_hop_bounded_retrieval", True, True),
    ("read_only_cypher_guardrail", True, True),
    ("retrieval_quality_eval_vs_baseline", True, False),
    ("latency_and_cost_monitoring", True, False),
]


def audit_architecture(checklist):
    total = len(checklist)
    satisfied = sum(1 for _, ok, _ in checklist if ok)
    critical_failures = [name for name, ok, critical in checklist if critical and not ok]
    return {
        "satisfied": satisfied,
        "total": total,
        "score": satisfied / total,
        "critical_failures": critical_failures,
        "passes": not critical_failures,
    }


def exercise_5() -> bool:
    print("\n--- Exercise 5: Production architecture checklist ---")
    report = audit_architecture(CHECKLIST)
    for name, ok, critical in CHECKLIST:
        tag = "critical" if critical else "advisory"
        print(f"  [{'x' if ok else ' '}] {name:<36} ({tag})")
    print(f"  score={report['satisfied']}/{report['total']} critical_failures={report['critical_failures']}")
    assert report["passes"] is True and report["score"] == 1.0

    broken = [(name, ok and name != "read_only_cypher_guardrail", critical)
              for name, ok, critical in CHECKLIST]
    broken_report = audit_architecture(broken)
    print(f"  guardrail removed -> critical_failures={broken_report['critical_failures']}")
    assert broken_report["passes"] is False
    assert broken_report["critical_failures"] == ["read_only_cypher_guardrail"]
    print("a single missing critical control blocks the design regardless of total score")
    return True


# --- End-to-end mini GraphRAG pipeline (shared by Exercise 4 and 6) ---

CORPUS_SENTENCES = [
    "Alice manages the Payments squad.",
    "Payments squad builds the Ledger service.",
    "Bob supports the Ledger service.",
    "Ledger service stores data in the Audit Store.",
    "Carol leads the Payments team.",
]

RELATION_PATTERNS = [
    ("MANAGES", re.compile(r"\bmanages\b")),
    ("BUILDS", re.compile(r"\bbuilds\b")),
    ("SUPPORTS", re.compile(r"\bsupports\b")),
    ("LEADS", re.compile(r"\bleads\b")),
    ("STORES_DATA_IN", re.compile(r"\bstores data in\b")),
]

ENTITY_CANONICAL = {
    "alice": "Alice",
    "bob": "Bob",
    "carol": "Carol",
    "dave": "Dave",
    "payments squad": "Payments Squad",
    "ledger service": "Ledger Service",
    "audit store": "Audit Store",
}

ENTITY_ALIASES = {
    "payments team": "payments squad",
}

ALIASES_BY_NODE = defaultdict(list)
for _alias, _canonical_key in ENTITY_ALIASES.items():
    ALIASES_BY_NODE[ENTITY_CANONICAL[_canonical_key]].append(_alias)

RELATION_KEYWORDS = [
    ("leads", "LEADS"),
    ("manages", "MANAGES"),
    ("builds", "BUILDS"),
    ("supports", "SUPPORTS"),
    ("stores", "STORES_DATA_IN"),
]


def clean_surface(text):
    surface = re.sub(r"^(the|a|an)\s+", "", text.strip(), flags=re.IGNORECASE)
    return surface.strip(" .,;:")


def resolve_entity(surface):
    key = re.sub(r"\s+", " ", clean_surface(surface).lower())
    key = ENTITY_ALIASES.get(key, key)
    return ENTITY_CANONICAL.get(key, clean_surface(surface))


def chunk_sentences(sentences, max_chars, overlap):
    """Sentence boundary ကို မချိုးဘဲ char budget အတွင်း ထည့်နိုင်သမျှ ထည့်သည်။"""
    chunks = []
    index = 0
    while index < len(sentences):
        current, size, cursor = [], 0, index
        while cursor < len(sentences):
            sentence = sentences[cursor]
            addition = len(sentence) + (1 if current else 0)
            if current and size + addition > max_chars:
                break
            current.append(sentence)
            size += addition
            cursor += 1
        chunks.append(current)
        if cursor >= len(sentences):
            break
        index = max(index + 1, cursor - overlap)
    return chunks


def extract_chunk_triples(chunk, chunk_id):
    """Scripted extraction — LLM output ကို deterministic pattern ဖြင့် အစားထိုးသည်။"""
    records = []
    for sentence in chunk:
        for relation, pattern in RELATION_PATTERNS:
            match = pattern.search(sentence)
            if not match:
                continue
            subject = clean_surface(sentence[:match.start()])
            obj = clean_surface(sentence[match.end():])
            if not subject or not obj:
                continue
            records.append((chunk_id, resolve_entity(subject), relation, resolve_entity(obj)))
    return records


def dedupe_triples(records):
    merged = OrderedDict()
    for chunk_id, subject, relation, obj in records:
        key = (subject, relation, obj)
        if key not in merged:
            merged[key] = {"subject": subject, "relation": relation, "object": obj, "chunks": [chunk_id]}
        elif chunk_id not in merged[key]["chunks"]:
            merged[key]["chunks"].append(chunk_id)
    return list(merged.values())


class Graph:
    def __init__(self):
        self.nodes = set()
        self.out = defaultdict(list)
        self.inn = defaultdict(list)

    def add_triple(self, subject, relation, obj):
        self.nodes.add(subject)
        self.nodes.add(obj)
        if (relation, obj) not in self.out[subject]:
            self.out[subject].append((relation, obj))
        if (relation, subject) not in self.inn[obj]:
            self.inn[obj].append((relation, subject))

    def edges(self):
        return sorted((s, r, o) for s in self.out for (r, o) in self.out[s])

    def neighbors(self, node):
        found = {obj for _, obj in self.out[node]}
        found |= {subject for _, subject in self.inn[node]}
        return found


def build_knowledge_graph(max_chars=90, overlap=1):
    chunks = chunk_sentences(CORPUS_SENTENCES, max_chars, overlap)
    raw = []
    for chunk_id, chunk in enumerate(chunks):
        raw.extend(extract_chunk_triples(chunk, chunk_id))
    triples = dedupe_triples(raw)
    graph = Graph()
    for triple in triples:
        graph.add_triple(triple["subject"], triple["relation"], triple["object"])
    return graph


def k_hop_subgraph(graph, anchors, hops):
    visited = set(anchors)
    frontier = set(anchors)
    for _ in range(hops):
        nxt = set()
        for node in frontier:
            nxt |= graph.neighbors(node)
        nxt -= visited
        visited |= nxt
        frontier = nxt
    edges = [edge for edge in graph.edges() if edge[0] in visited and edge[2] in visited]
    return visited, edges


def entity_link(graph, question):
    lowered = question.lower()
    anchors = []
    for node in sorted(graph.nodes):
        surfaces = [node.lower()] + ALIASES_BY_NODE.get(node, [])
        if any(surface in lowered for surface in surfaces):
            anchors.append(node)
    return anchors


def serialize_context(edges):
    lines = [f"{s} --{r}--> {o}" for (s, r, o) in sorted(edges)]
    return "Knowledge Graph triples:\n" + "\n".join(lines)


def generate_answer(question, edges, anchors):
    """Rule-based generator — retrieval context ပေါ်မှ ဆုံးဖြတ်ချက်ကို pattern ဖြင့် ဆွဲထုတ်သည်။"""
    words = [re.sub(r"[^a-z]", "", token) for token in question.lower().split()]
    targets = []
    for keyword, relation in RELATION_KEYWORDS:
        if keyword in words:
            targets.append(relation)
    for relation in targets:
        for subject, edge_relation, obj in sorted(edges):
            if edge_relation == relation and obj in anchors:
                return subject
    return "Unknown"


def exercise_6() -> bool:
    print("\n--- Exercise 6: End-to-end mini GraphRAG integration test ---")
    chunks = chunk_sentences(CORPUS_SENTENCES, max_chars=90, overlap=1)
    print(f"corpus sentences={len(CORPUS_SENTENCES)} -> chunks={len(chunks)} (overlap=1 sentence)")
    for chunk_id, chunk in enumerate(chunks):
        print(f"  chunk {chunk_id}: {len(chunk)} sentences")

    raw = []
    for chunk_id, chunk in enumerate(chunks):
        raw.extend(extract_chunk_triples(chunk, chunk_id))
    triples = dedupe_triples(raw)
    print(f"extracted triples: raw={len(raw)} after dedup={len(triples)}")
    assert len(raw) == 8 and len(triples) == 5
    assert all(t["chunks"] for t in triples)

    graph = build_knowledge_graph()
    print(f"in-memory graph: nodes={len(graph.nodes)} edges={len(graph.edges())}")
    assert len(graph.nodes) == 6 and len(graph.edges()) == 5
    assert resolve_entity("Payments team") == "Payments Squad"

    question = "Who leads the Payments Squad?"
    anchors = entity_link(graph, question)
    assert anchors == ["Payments Squad"], anchors
    nodes, edges = k_hop_subgraph(graph, anchors, hops=1)
    print(f"question: {question}")
    print(f"  entity linking -> anchors={anchors}")
    print(f"  1-hop subgraph -> nodes={sorted(nodes)}")
    print(f"  retained edges = {len(edges)}, hops bound excluded Audit Store")
    assert len(nodes) == 4 and len(edges) == 3
    assert "Ledger Service" in nodes and "Audit Store" not in nodes

    context = serialize_context(edges)
    payload = json.dumps({"question": question, "context": context.splitlines()[1:]})
    print("  serialized prompt context:")
    for line in context.splitlines():
        print(f"    {line}")
    assert len(payload) > 0

    answer = generate_answer(question, edges, anchors)
    print(f"  generator answer -> {answer}")
    assert answer == "Carol"

    question2 = "Who builds the Ledger service?"
    anchors2 = entity_link(graph, question2)
    nodes2, edges2 = k_hop_subgraph(graph, anchors2, hops=1)
    answer2 = generate_answer(question2, edges2, anchors2)
    print(f"question: {question2} -> anchors={anchors2} answer={answer2}")
    assert anchors2 == ["Ledger Service"] and answer2 == "Payments Squad"
    print("full pipeline ingest -> retrieve -> serialize -> generate: OK")
    return True


# --- Runner ---

def run_all():
    exercises = (exercise_1, exercise_2, exercise_3, exercise_4, exercise_5, exercise_6)
    results = []
    for exercise in exercises:
        try:
            results.append(bool(exercise()))
        except AssertionError as error:
            print(f"[FAIL] {exercise.__name__}: {error}")
            results.append(False)
    passed = sum(1 for ok in results if ok)
    print(f"\n{passed}/{len(exercises)} exercises passed.")
    if passed == len(exercises):
        print("[PASS] All 6/6 exercises passed successfully.")
        return True
    return False


if __name__ == "__main__":
    sys.exit(0 if run_all() else 1)
