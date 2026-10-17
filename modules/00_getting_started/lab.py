#!/usr/bin/env python3
"""M00 lab: pipeline order, cosine similarity, routing, failure modes, Triple (SPO) parsing."""

import math
import re
import sys
from collections import Counter
from dataclasses import dataclass

# --- Exercise 1: RAG pipeline stage ordering --------------------------------
PIPELINE_DEPENDENCIES = {
    "ingest": (), "chunk": ("ingest",), "embed": ("chunk",),
    "index": ("embed",), "retrieve": ("index",), "generate": ("retrieve",),
}

UNORDERED_STAGES = ["generate", "retrieve", "index", "embed", "ingest", "chunk"]

def topological_order(stages, dependencies):
    """Return a deterministic order in which every stage follows its dependencies."""
    ordered, remaining = [], sorted(set(stages))
    while remaining:
        ready = [s for s in remaining if all(d in ordered for d in dependencies[s])]
        assert ready, "dependency cycle detected"
        ordered.append(ready[0])
        remaining.remove(ready[0])
    return ordered

def exercise_1() -> bool:
    print("\n--- Exercise 1: RAG Pipeline Stage Ordering ---")
    order = topological_order(UNORDERED_STAGES, PIPELINE_DEPENDENCIES)
    print("input stages   :", UNORDERED_STAGES)
    print("computed order :", order)
    assert order == ["ingest", "chunk", "embed", "index", "retrieve", "generate"]
    position_of = {stage: i for i, stage in enumerate(order)}
    for stage, deps in PIPELINE_DEPENDENCIES.items():
        for dep in deps:
            assert position_of[dep] < position_of[stage], "%s must precede %s" % (dep, stage)
    print("dependency invariant holds for %d stages" % len(PIPELINE_DEPENDENCIES))
    return True

# --- Exercise 2: Cosine similarity over Embedding vectors -------------------
def cosine_similarity(left, right):
    if len(left) != len(right):
        raise ValueError("dimension mismatch")
    dot = sum(a * b for a, b in zip(left, right))
    norm_left = math.sqrt(sum(a * a for a in left))
    norm_right = math.sqrt(sum(b * b for b in right))
    if norm_left == 0.0 or norm_right == 0.0:
        return 0.0
    return dot / (norm_left * norm_right)

QUERY_VECTOR = [0.90, 0.10, 0.00, 0.20]

CHUNK_VECTORS = {
    "chunk-01": [0.85, 0.15, 0.05, 0.10],
    "chunk-02": [0.10, 0.80, 0.60, 0.10],
    "chunk-03": [0.00, 0.20, 0.95, 0.30],
    "chunk-04": [0.70, 0.05, 0.10, 0.90],
}

def rank_chunks(query, chunks):
    scored = [(cid, cosine_similarity(query, vec)) for cid, vec in chunks.items()]
    scored.sort(key=lambda item: (-item[1], item[0]))
    return scored

def exercise_2() -> bool:
    print("\n--- Exercise 2: Cosine Similarity Ranking ---")
    ranking = rank_chunks(QUERY_VECTOR, CHUNK_VECTORS)
    for rank, (chunk_id, score) in enumerate(ranking, start=1):
        print("  %d. %s similarity=%.6f" % (rank, chunk_id, score))
    print("  self-similarity = %.6f" % cosine_similarity(QUERY_VECTOR, list(QUERY_VECTOR)))
    print("  orthogonal      = %.6f" % cosine_similarity([1.0, 0.0], [0.0, 2.0]))
    assert abs(cosine_similarity(QUERY_VECTOR, list(QUERY_VECTOR)) - 1.0) < 1e-9
    assert abs(cosine_similarity([1.0, 0.0], [0.0, 2.0])) < 1e-9
    assert cosine_similarity([0.0, 0.0], [1.0, 1.0]) == 0.0
    assert ranking[0][0] == "chunk-01" and ranking[-1][0] == "chunk-03"
    print("top-1 chunk =", ranking[0][0])
    return True

# --- Exercise 3: Retrieval modality selection -------------------------------
def select_modality(features):
    """Choose the cheapest retrieval modality that satisfies the query features."""
    if features["hop_count"] >= 2 and features["spans_documents"]:
        return "GraphRAG - entity-anchored subgraph retrieval"
    if features["needs_corpus_wide_summary"]:
        return "GraphRAG - community summary retrieval"
    if features["needs_structured_filter"]:
        return "Text-to-Cypher"
    return "Vector Search - plain RAG"

def _query(hop_count, spans_documents, needs_corpus_wide_summary, needs_structured_filter):
    return {"hop_count": hop_count, "spans_documents": spans_documents,
            "needs_corpus_wide_summary": needs_corpus_wide_summary,
            "needs_structured_filter": needs_structured_filter}

QUERIES = [("Q1", _query(0, False, False, False)), ("Q2", _query(3, True, False, False)),
           ("Q3", _query(1, False, True, False)), ("Q4", _query(0, False, False, True))]

EXPECTED_MODALITY = {"Q1": "Vector Search - plain RAG", "Q4": "Text-to-Cypher",
                     "Q2": "GraphRAG - entity-anchored subgraph retrieval",
                     "Q3": "GraphRAG - community summary retrieval"}

def exercise_3() -> bool:
    print("\n--- Exercise 3: Retrieval Modality Selection ---")
    decisions = {}
    for query_id, features in QUERIES:
        decisions[query_id] = select_modality(features)
        print("  %s -> %s" % (query_id, decisions[query_id]))
    assert decisions == EXPECTED_MODALITY
    print("modality decisions =", len(decisions))
    return True

# --- Exercise 4: RAG failure mode classification ----------------------------
FAILURE_RULES = (
    ("ingestion_gap", lambda f: not f["required_entity_in_index"]),
    ("global_summarization_failure", lambda f: f["needs_corpus_wide_aggregate"]),
    ("multi_hop_failure", lambda f: f["hop_count"] >= 2),
    ("chunk_isolation", lambda f: f["facts_split_across_chunks"]),
)

def classify_failure(features):
    for label, rule in FAILURE_RULES:
        if rule(features):
            return label
    return "no_failure"

def _scenario(entity_in_index, needs_aggregate, hop_count, split_across_chunks):
    return {"required_entity_in_index": entity_in_index,
            "needs_corpus_wide_aggregate": needs_aggregate, "hop_count": hop_count,
            "facts_split_across_chunks": split_across_chunks}

FAILURE_SCENARIOS = [("S1", _scenario(True, False, 0, False)),
                     ("S2", _scenario(False, False, 0, False)),
                     ("S3", _scenario(True, False, 2, True)),
                     ("S4", _scenario(True, True, 0, False)),
                     ("S5", _scenario(True, False, 1, True))]

EXPECTED_FAILURE = {"S1": "no_failure", "S2": "ingestion_gap", "S3": "multi_hop_failure",
                    "S4": "global_summarization_failure", "S5": "chunk_isolation"}

def exercise_4() -> bool:
    print("\n--- Exercise 4: RAG Failure Mode Classification ---")
    outcomes = {}
    for scenario_id, features in FAILURE_SCENARIOS:
        outcomes[scenario_id] = classify_failure(features)
        print("  %s -> %s" % (scenario_id, outcomes[scenario_id]))
    assert outcomes == EXPECTED_FAILURE
    counts = Counter(outcomes.values())
    for label in sorted(counts):
        print("    %-30s %d" % (label, counts[label]))
    assert counts["no_failure"] == 1
    print("distinct failure modes =", len(counts))
    return True

# --- Exercise 5: Triple (SPO) parsing and validation ------------------------
TRIPLE_PATTERN = re.compile(r"^(?P<s>[^|]+)\|(?P<p>[^|]+)\|(?P<o>[^|]+)\|(?P<c>[^|]+)$")

@dataclass(frozen=True)
class Triple:
    subject: str
    predicate: str
    object: str
    source_chunk: str

    def to_spo(self):
        return "(%s)-[%s]->(%s)" % (self.subject, self.predicate, self.object)

def _normalize(text):
    return re.sub(r"\s+", " ", text).strip()

def parse_triples(lines):
    """Parse 'subject|predicate|object|source_chunk' lines into (triples, errors)."""
    triples, errors = [], []
    for line_number, raw in enumerate(lines, start=1):
        match = TRIPLE_PATTERN.match(raw.strip())
        if match is None:
            errors.append((line_number, "malformed_field_count"))
            continue
        subject = _normalize(match.group("s"))
        predicate = _normalize(match.group("p")).lower().replace(" ", "_")
        obj = _normalize(match.group("o"))
        chunk = _normalize(match.group("c"))
        if not subject or not predicate or not obj or not chunk:
            errors.append((line_number, "empty_field"))
            continue
        triples.append(Triple(subject, predicate, obj, chunk))
    return triples, errors

TRIPLE_LINES = [
    "  Acme Corp | founded_in | Cupertino | chunk-01 ",
    "Acme Corp|founded_in|Cupertino|chunk-01",
    "Alice Chen|works_at|Acme Corp|chunk-02",
    "Alice Chen | reports_to | Bob Ray | chunk-02",
    "Broken|line",
    "|empty_subject|Acme Corp|chunk-03",
]

def exercise_5() -> bool:
    print("\n--- Exercise 5: Triple (SPO) Parsing ---")
    triples, errors = parse_triples(TRIPLE_LINES)
    for triple in triples:
        print("  %-40s [%s]" % (triple.to_spo(), triple.source_chunk))
    for line_number, reason in errors:
        print("  rejected line %d: %s" % (line_number, reason))
    unique = sorted(set(triples), key=lambda t: (t.subject, t.predicate, t.object, t.source_chunk))
    duplicates = len(triples) - len(unique)
    assert len(triples) == 4
    assert len(errors) == 2
    assert duplicates == 1 and len(unique) == 3
    first = unique[0]
    assert (first.subject, first.predicate, first.object, first.source_chunk) == (
        "Acme Corp", "founded_in", "Cupertino", "chunk-01")
    assert first.to_spo() == "(Acme Corp)-[founded_in]->(Cupertino)"
    assert sorted({t.predicate for t in triples}) == ["founded_in", "reports_to", "works_at"]
    print("unique triples = %d, duplicates = %d" % (len(unique), duplicates))
    return True

# --- Exercise 6: GraphRAG readiness check -----------------------------------
NUMERIC_CHECKS = (
    ("entity_coverage", ">=", 0.85),
    ("relationship_density", ">=", 1.50),
    ("duplicate_entity_rate", "<=", 0.05),
    ("avg_chunk_tokens", "<=", 512.0),
)

BOOLEAN_CHECKS = ("uniqueness_constraint", "fulltext_index", "community_summary")

def _numeric_pass(value, operator, threshold):
    return value >= threshold if operator == ">=" else value <= threshold

def readiness_report(metrics):
    failed = [name for name, operator, threshold in NUMERIC_CHECKS
              if not _numeric_pass(metrics[name], operator, threshold)]
    failed += [name for name in BOOLEAN_CHECKS if not metrics[name]]
    return {"verdict": "READY" if not failed else "NOT_READY", "failed": failed}

READY_PROFILE = {"entity_coverage": 0.93, "relationship_density": 2.40,
                 "duplicate_entity_rate": 0.02, "avg_chunk_tokens": 384.0,
                 "uniqueness_constraint": True, "fulltext_index": True, "community_summary": True}

BLOCKED_PROFILE = {"entity_coverage": 0.71, "relationship_density": 1.10,
                   "duplicate_entity_rate": 0.12, "avg_chunk_tokens": 640.0,
                   "uniqueness_constraint": True, "fulltext_index": False, "community_summary": False}

def exercise_6() -> bool:
    print("\n--- Exercise 6: GraphRAG Readiness Check ---")
    for name, profile in (("ready-profile", READY_PROFILE), ("blocked-profile", BLOCKED_PROFILE)):
        report = readiness_report(profile)
        print("  %-16s verdict=%s failed=%s" % (name, report["verdict"], report["failed"]))
    assert readiness_report(READY_PROFILE) == {"verdict": "READY", "failed": []}
    blocked = readiness_report(BLOCKED_PROFILE)
    assert blocked["verdict"] == "NOT_READY"
    assert blocked["failed"] == ["entity_coverage", "relationship_density",
                                 "duplicate_entity_rate", "avg_chunk_tokens",
                                 "fulltext_index", "community_summary"]
    print("checks evaluated =", len(NUMERIC_CHECKS) + len(BOOLEAN_CHECKS))
    return True

# --- Runner -----------------------------------------------------------------
def run_all() -> bool:
    exercises = [
        ("Exercise 1", exercise_1), ("Exercise 2", exercise_2), ("Exercise 3", exercise_3),
        ("Exercise 4", exercise_4), ("Exercise 5", exercise_5), ("Exercise 6", exercise_6),
    ]
    passed = 0
    for label, exercise in exercises:
        try:
            if exercise():
                passed += 1
        except AssertionError as error:
            print("[FAIL] %s: %s" % (label, error))
    total = len(exercises)
    print("\n[RESULT] %d/%d exercises passed." % (passed, total))
    if passed == total:
        print("[PASS] All 6/6 exercises passed successfully.")
        return True
    return False

if __name__ == "__main__":
    sys.exit(0 if run_all() else 1)
