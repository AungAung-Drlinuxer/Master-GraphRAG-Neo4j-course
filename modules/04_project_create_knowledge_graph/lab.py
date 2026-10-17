#!/usr/bin/env python3
"""
M04 — Project: Create a Knowledge Graph from Text

End-to-end Pipeline — ingest -> normalize -> chunk -> extract -> resolve -> merge
-> quality gate -> export. The LLM extraction stage is replaced by a deterministic
scripted extractor: standard library only, offline, no random, identical every run.
"""

import csv
import io
import json
import re
import sys
import unicodedata
from collections import OrderedDict, defaultdict
from dataclasses import dataclass, field
from difflib import SequenceMatcher

# ---- Embedded sample corpus (ingest input) --------------------------------- #
SAMPLE_CORPUS = [
    {"doc_id": "doc-001", "raw_text": "Neo4j  is a graph database.\nNeo4j uses Cypher as its query language. "
                                      "GraphRAG is built on a Knowledge Graph. Nous Research develops open models."},
    {"doc_id": "doc-002", "raw_text": "Graph Rag runs on Neo4j. GraphRAG is built on a Knowledge Graph. "
                                      "Neo4j was developed by Neo4j Inc. Neo4j,  GraphRAG and Cypher are widely "
                                      "used in production."},
    {"doc_id": "doc-003", "raw_text": "Entity Resolution merges duplicate nodes. GraphRAG uses Entity Resolution. "
                                      "LLM is a Transformer based model. Entity resolution includes alias mapping."},
]

# ---- Schema contract ------------------------------------------------------- #
NODE_LABELS = ("Document", "Chunk", "Entity")
ALLOWED_ENTITY_TYPES = ("Technology", "Organization", "Concept")
ALLOWED_PREDICATES = ("IS_A", "USES", "BUILT_ON", "DEVELOPED_BY", "INCLUDES", "RELATED_TO")
MIN_CONFIDENCE, CHUNK_SIZE, FUZZY_THRESHOLD = 0.60, 140, 0.85
COOCCURRENCE_CONFIDENCE = 0.45
CONF_EXACT, CONF_ALIAS, CONF_FUZZY = 0.95, 0.80, 0.55

GAZETTEER = [
    {"canonical": "Neo4j", "type": "Technology", "aliases": ["neo4j", "neo 4j", "neo4j inc"]},
    {"canonical": "Cypher", "type": "Technology", "aliases": ["cypher"]},
    {"canonical": "GraphRAG", "type": "Technology", "aliases": ["graphrag", "graph rag"]},
    {"canonical": "Knowledge Graph", "type": "Concept", "aliases": ["knowledge graph", "knowledge graphs"]},
    {"canonical": "Entity Resolution", "type": "Concept", "aliases": ["entity resolution", "entity-resolution"]},
    {"canonical": "Nous Research", "type": "Organization", "aliases": ["nous research"]},
    {"canonical": "LLM", "type": "Technology", "aliases": ["llm", "large language model"]},
    {"canonical": "Transformer", "type": "Technology", "aliases": ["transformer"]},
]
PATTERN_RULES = [
    ("IS_A", r"(?:is|are)\s+(?:a|an)"),
    ("USES", r"(?:uses?|use)"),
    ("BUILT_ON", r"(?:is\s+built\s+on|runs?\s+on|is\s+based\s+on)"),
    ("DEVELOPED_BY", r"(?:was\s+developed\s+by|develops?)"),
    ("INCLUDES", r"(?:contains?|includes?)"),
]


def slug(text):
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")


def entity_id(canonical):
    return "ent:" + slug(canonical)


def rel_id(subject_id, predicate, object_id):
    return "rel:" + slug("%s-%s-%s" % (subject_id, predicate, object_id))


@dataclass
class Document:
    doc_id: str
    text: str
    char_count: int


@dataclass
class Chunk:
    chunk_id: str
    doc_id: str
    ordinal: int
    text: str


@dataclass
class Entity:
    entity_id: str
    name: str
    type: str
    aliases: list = field(default_factory=list)


@dataclass
class Provenance:
    chunk_id: str
    confidence: float
    method: str


@dataclass
class Triple:
    subject_id: str
    predicate: str
    object_id: str
    provenance: list = field(default_factory=list)

    @property
    def key(self):
        return (self.subject_id, self.predicate, self.object_id)

    @property
    def confidence(self):
        return max(p.confidence for p in self.provenance)

    def to_dict(self, names):
        return {"subject": names.get(self.subject_id, self.subject_id), "predicate": self.predicate,
                "object": names.get(self.object_id, self.object_id), "subject_id": self.subject_id,
                "object_id": self.object_id, "confidence": round(self.confidence, 2),
                "provenance": [{"chunk_id": p.chunk_id, "confidence": p.confidence, "method": p.method}
                               for p in self.provenance]}


# ---- Stage 1-2: ingest + normalize ----------------------------------------- #
def ingest_corpus(corpus):
    return [Document(d["doc_id"], d["raw_text"], len(d["raw_text"])) for d in corpus]


UNICODE_FOLD = {"\u2018": "'", "\u2019": "'", "\u201c": '"', "\u201d": '"',
                "\u2013": "-", "\u2014": "-", "\u2026": "...", "\u00a0": " "}


def normalize_text(raw):
    text = unicodedata.normalize("NFC", raw)
    for src, dst in UNICODE_FOLD.items():
        text = text.replace(src, dst)
    text = re.sub(r"[\r\n\t\f\v]+", " ", text)
    text = "".join(ch for ch in text if unicodedata.category(ch)[0] != "C")
    return re.sub(r"\s+", " ", text).strip()


def normalize_document(doc):
    text = normalize_text(doc.text)
    return Document(doc.doc_id, text, len(text))


# ---- Stage 3: chunk (sentence-aligned, bounded by CHUNK_SIZE) -------------- #
def split_sentences(text):
    return [s.strip() for s in re.split(r"(?<=[.!?])\s+", text) if s.strip()]


def chunk_document(doc):
    chunks, buf, ordinal = [], "", 0
    for sentence in split_sentences(doc.text):
        candidate = (buf + " " + sentence).strip() if buf else sentence
        if buf and len(candidate) > CHUNK_SIZE:
            chunks.append(Chunk("%s:c%02d" % (doc.doc_id, ordinal), doc.doc_id, ordinal, buf))
            ordinal, buf = ordinal + 1, sentence
        else:
            buf = candidate
    if buf:
        chunks.append(Chunk("%s:c%02d" % (doc.doc_id, ordinal), doc.doc_id, ordinal, buf))
    return chunks


# ---- Stage 4: extract (deterministic scripted extractor) ------------------- #
ALIAS_INDEX, CANONICAL_INDEX = {}, {}
for _entry in GAZETTEER:
    CANONICAL_INDEX[_entry["canonical"].lower()] = _entry
    for _alias in _entry["aliases"]:
        ALIAS_INDEX[_alias.lower()] = _entry
_BOUNDED = r"(?<![\w-])(?:%s)(?![\w-])" % "|".join(
    re.escape(a) for a in sorted(ALIAS_INDEX, key=len, reverse=True))
_DETERMINER = r"(?:(?:a|an|the)\s+)?"


def resolve_surface(surface):
    """(entry, confidence, kind) — canonical hit, alias hit, fuzzy fallback, or unresolved."""
    key = surface.lower()
    if key in CANONICAL_INDEX:
        return CANONICAL_INDEX[key], CONF_EXACT, "canonical"
    if key in ALIAS_INDEX:
        return ALIAS_INDEX[key], CONF_ALIAS, "alias"
    best, best_ratio = None, 0.0
    for alias, entry in ALIAS_INDEX.items():
        ratio = SequenceMatcher(None, key, alias).ratio()
        if ratio > best_ratio:
            best, best_ratio = entry, ratio
    if best is not None and best_ratio >= FUZZY_THRESHOLD:
        return best, CONF_FUZZY, "fuzzy"
    return None, 0.0, "unresolved"


def find_mentions(sentence):
    hits = sorted(((m.start(), m.group(0)) for m in re.finditer(_BOUNDED, sentence, re.I)), key=lambda i: i[0])
    return [surface for _, surface in hits]


def extract_from_chunk(chunk):
    triples = []
    for sentence in split_sentences(chunk.text):
        matched = False
        for predicate, connector in PATTERN_RULES:
            pattern = r"(?P<a>%s)\s+%s\s+%s(?P<b>%s)" % (_BOUNDED, connector, _DETERMINER, _BOUNDED)
            for match in re.finditer(pattern, sentence, re.I):
                a_entry, a_conf, _ = resolve_surface(match.group("a"))
                b_entry, b_conf, _ = resolve_surface(match.group("b"))
                if a_entry is None or b_entry is None:
                    continue
                matched = True
                triples.append(Triple(entity_id(a_entry["canonical"]), predicate, entity_id(b_entry["canonical"]),
                                      [Provenance(chunk.chunk_id, round(min(a_conf, b_conf), 2),
                                                  "pattern:" + predicate.lower())]))
        if not matched:  # co-occurrence fallback: low confidence, removed by the quality gate
            resolved = [e for e in (resolve_surface(m)[0] for m in find_mentions(sentence)) if e is not None]
            for left, right in zip(resolved, resolved[1:]):
                if left["canonical"] != right["canonical"]:
                    triples.append(Triple(entity_id(left["canonical"]), "RELATED_TO", entity_id(right["canonical"]),
                                          [Provenance(chunk.chunk_id, COOCCURRENCE_CONFIDENCE, "cooccurrence")]))
    return triples


# ---- Stage 5-6: entity resolution + merge/dedup ---------------------------- #
def resolve_entities(triples):
    known = {}
    for entry in GAZETTEER:
        known[entity_id(entry["canonical"])] = Entity(entity_id(entry["canonical"]), entry["canonical"],
                                                      entry["type"], list(entry["aliases"]))
    used = OrderedDict()
    for triple in triples:
        for eid in (triple.subject_id, triple.object_id):
            if eid in known:
                used[eid] = known[eid]
    return used


def merge_triples(triples):
    merged = OrderedDict()
    for triple in triples:
        if triple.key in merged:
            merged[triple.key].provenance.extend(triple.provenance)
        else:
            merged[triple.key] = Triple(triple.subject_id, triple.predicate, triple.object_id, list(triple.provenance))
    return list(merged.values())


# ---- Stage 7: quality gate ------------------------------------------------- #
def quality_gate(triples, entities):
    accepted, rejected, seen = [], [], set()
    for triple in triples:
        if not triple.subject_id or not triple.object_id:
            rejected.append((triple, "missing_endpoint"))
        elif triple.subject_id == triple.object_id:
            rejected.append((triple, "self_loop"))
        elif triple.predicate not in ALLOWED_PREDICATES:
            rejected.append((triple, "unknown_predicate"))
        elif triple.subject_id not in entities or triple.object_id not in entities:
            rejected.append((triple, "dangling_endpoint"))
        elif triple.confidence < MIN_CONFIDENCE:
            rejected.append((triple, "low_confidence"))
        elif triple.key in seen:
            rejected.append((triple, "duplicate"))
        else:
            seen.add(triple.key)
            accepted.append(triple)
    return {"accepted": accepted, "rejected": rejected}


# ---- Stage 8: export (Cypher / JSON / CSV) --------------------------------- #
NODE_MERGE = "MERGE (n:Entity {id: $id})\nSET n.name = $name, n.type = $type"


def export_cypher(entities, triples):
    statements = [{"query": NODE_MERGE, "params": {"id": e.entity_id, "name": e.name, "type": e.type}}
                  for e in entities.values()]
    for t in triples:
        statements.append({"query": "MATCH (a:Entity {id: $subject_id}), (b:Entity {id: $object_id})\n"
                                    "MERGE (a)-[r:%s {id: $rel_id}]->(b)\n"
                                    "SET r.confidence = $confidence, r.chunk_ids = $chunk_ids, "
                                    "r.methods = $methods" % t.predicate,
                           "params": {"subject_id": t.subject_id, "object_id": t.object_id,
                                      "rel_id": rel_id(t.subject_id, t.predicate, t.object_id),
                                      "confidence": t.confidence,
                                      "chunk_ids": [p.chunk_id for p in t.provenance],
                                      "methods": sorted({p.method for p in t.provenance})}})
    return statements


def export_json(entities, triples):
    names = {eid: e.name for eid, e in entities.items()}
    return json.dumps({"nodes": [{"id": e.entity_id, "name": e.name, "type": e.type, "aliases": e.aliases}
                                 for e in entities.values()],
                       "relationships": [t.to_dict(names) for t in triples]},
                      indent=2, sort_keys=True, ensure_ascii=False)


def export_csv(entities, triples):
    node_buf, rel_buf = io.StringIO(), io.StringIO()
    node_writer, rel_writer = csv.writer(node_buf, lineterminator="\n"), csv.writer(rel_buf, lineterminator="\n")
    node_writer.writerow(["entity_id:ID", "name", "type", ":LABEL"])
    for e in entities.values():
        node_writer.writerow([e.entity_id, e.name, e.type, "Entity"])
    rel_writer.writerow([":START_ID", ":END_ID", ":TYPE", "rel_id", "confidence", "chunk_ids"])
    for t in triples:
        rel_writer.writerow([t.subject_id, t.object_id, t.predicate,
                             rel_id(t.subject_id, t.predicate, t.object_id), round(t.confidence, 2),
                             ";".join(sorted({p.chunk_id for p in t.provenance}))])
    return {"nodes.csv": node_buf.getvalue(), "relationships.csv": rel_buf.getvalue()}


def run_pipeline(corpus):
    documents = [normalize_document(doc) for doc in ingest_corpus(corpus)]
    chunks = [c for doc in documents for c in chunk_document(doc)]
    raw_triples = [t for chunk in chunks for t in extract_from_chunk(chunk)]
    entities = resolve_entities(raw_triples)
    merged = merge_triples(raw_triples)
    gate = quality_gate(merged, entities)
    accepted = gate["accepted"]
    return {"documents": documents, "chunks": chunks, "raw_triples": raw_triples, "entities": entities,
            "merged": merged, "accepted": accepted, "rejected": gate["rejected"],
            "cypher": export_cypher(entities, accepted), "json": export_json(entities, accepted),
            "csv": export_csv(entities, accepted)}


# ---- Exercises ------------------------------------------------------------- #
def exercise_1() -> bool:
    print("\n--- Exercise 1: Corpus Normalization ---")
    documents = [normalize_document(doc) for doc in ingest_corpus(SAMPLE_CORPUS)]
    for doc in documents:
        raw = [d for d in SAMPLE_CORPUS if d["doc_id"] == doc.doc_id][0]["raw_text"]
        print("  %s | raw_chars=%3d | normalized_chars=%3d | %s" % (doc.doc_id, len(raw), doc.char_count, doc.text[:56]))
    dirty = "  Neo4j\u00a0 is  a graph\u2013database.\n\n  \u201cGraphRAG\u201d  \u2026  "
    print("dirty   : %r\ncleaned : %r" % (dirty, normalize_text(dirty)))
    assert len(documents) == 3
    assert normalize_text(dirty) == 'Neo4j is a graph-database. "GraphRAG" ...'
    assert all(unicodedata.normalize("NFC", d.text) == d.text and d.text == d.text.strip() for d in documents)
    assert all("\n" not in d.text and "  " not in d.text for d in documents)
    return True


def exercise_2() -> bool:
    print("\n--- Exercise 2: End-to-End Pipeline Run ---")
    result = run_pipeline(SAMPLE_CORPUS)
    print("ingest     : %d documents" % len(result["documents"]))
    print("chunk      : %d chunks -> %s" % (len(result["chunks"]), [c.chunk_id for c in result["chunks"]]))
    print("extract    : %d raw triples (scripted extractor)" % len(result["raw_triples"]))
    print("resolve    : %d canonical entities" % len(result["entities"]))
    print("merge      : %d unique triples" % len(result["merged"]))
    print("gate       : %d accepted / %d rejected" % (len(result["accepted"]), len(result["rejected"])))
    entry, conf, kind = resolve_surface("Graph Rag")
    fuzzy_entry, fuzzy_conf, fuzzy_kind = resolve_surface("Knowledg Graph")
    print("resolution : 'Graph Rag' -> %s (conf=%.2f, kind=%s)" % (entry["canonical"], conf, kind))
    print("resolution : 'Knowledg Graph' -> %s (conf=%.2f, kind=%s)" % (fuzzy_entry["canonical"], fuzzy_conf,
                                                                        fuzzy_kind))
    assert entry["canonical"] == "GraphRAG" and conf == 0.80 and kind == "alias"
    assert fuzzy_entry["canonical"] == "Knowledge Graph" and fuzzy_kind == "fuzzy" and fuzzy_conf < MIN_CONFIDENCE
    assert [len(result[k]) for k in ("documents", "chunks", "raw_triples", "entities", "merged", "accepted")] == \
           [3, 6, 9, 7, 8, 5]
    return True


def exercise_3() -> bool:
    print("\n--- Exercise 3: Data Model Validation ---")
    result = run_pipeline(SAMPLE_CORPUS)
    entities, triples = result["entities"], result["accepted"]
    type_hist, pred_hist = defaultdict(int), defaultdict(int)
    for entity in entities.values():
        type_hist[entity.type] += 1
    for triple in triples:
        pred_hist[triple.predicate] += 1
    print("node labels    : %s" % list(NODE_LABELS))
    print("entity types   : %s" % dict(sorted(type_hist.items())))
    print("predicate hist : %s" % dict(sorted(pred_hist.items())))
    for entity in entities.values():
        print("  %-22s %-18s %s" % (entity.entity_id, entity.name, entity.type))
    assert all(e.type in ALLOWED_ENTITY_TYPES for e in entities.values())
    assert all(e.entity_id == entity_id(e.name) and e.name == e.name.strip() for e in entities.values())
    assert len({e.entity_id for e in entities.values()}) == len(entities)
    assert all(t.predicate in ALLOWED_PREDICATES for t in triples)
    assert all(t.subject_id in entities and t.object_id in entities and t.subject_id != t.object_id for t in triples)
    assert set(pred_hist) == {"BUILT_ON", "IS_A", "USES"} and sum(pred_hist.values()) == 5
    return True


def exercise_4() -> bool:
    print("\n--- Exercise 4: Provenance Metadata ---")
    result = run_pipeline(SAMPLE_CORPUS)
    chunk_ids = {c.chunk_id for c in result["chunks"]}
    names = {eid: e.name for eid, e in result["entities"].items()}
    methods = set()
    accepted_methods = set()
    for triple in result["merged"]:
        assert triple.provenance, "triple without provenance"
        for prov in triple.provenance:
            assert prov.chunk_id in chunk_ids and 0.0 <= prov.confidence <= 1.0
            methods.add(prov.method)
        print("  %-15s -[%s]-> %-16s conf=%.2f sources=%s" % (names[triple.subject_id], triple.predicate,
                                                              names[triple.object_id], triple.confidence,
                                                              [p.chunk_id for p in triple.provenance]))
    for triple in result["accepted"]:
        accepted_methods |= {p.method for p in triple.provenance}
    target = [t for t in result["merged"] if t.subject_id == entity_id("GraphRAG") and t.predicate == "BUILT_ON"
              and t.object_id == entity_id("Knowledge Graph")]
    assert len(target) == 1, "duplicate triple was not merged"
    print("merged triple 'GraphRAG -[BUILT_ON]-> Knowledge Graph' provenance: %s" %
          [(p.chunk_id, p.confidence) for p in target[0].provenance])
    assert len(target[0].provenance) == 2 and len({p.chunk_id for p in target[0].provenance}) == 2
    assert target[0].confidence == 0.95
    assert methods == {"pattern:uses", "pattern:built_on", "pattern:is_a", "pattern:developed_by", "cooccurrence"}
    assert accepted_methods == {"pattern:uses", "pattern:built_on", "pattern:is_a"}
    return True


def exercise_5() -> bool:
    print("\n--- Exercise 5: Quality Gate Filtering ---")
    result = run_pipeline(SAMPLE_CORPUS)
    neo4j, cypher, graphrag = entity_id("Neo4j"), entity_id("Cypher"), entity_id("GraphRAG")
    candidates = list(result["merged"]) + [
        Triple(neo4j, "USES", "", [Provenance("doc-001:c00", 0.95, "pattern:uses")]),
        Triple(cypher, "USES", cypher, [Provenance("doc-003:c00", 0.95, "pattern:uses")]),
        Triple(neo4j, "FRIENDS_WITH", cypher, [Provenance("doc-003:c00", 0.90, "pattern:friends_with")]),
        Triple(cypher, "IS_A", graphrag, [Provenance("doc-003:c00", 0.30, "pattern:is_a")]),
        Triple(neo4j, "USES", cypher, [Provenance("doc-002:c00", 0.95, "pattern:uses")]),
    ]
    gate = quality_gate(candidates, result["entities"])
    reasons = defaultdict(int)
    for triple, reason in gate["rejected"]:
        reasons[reason] += 1
        print("  REJECT %-17s %s -[%s]-> %s" % (reason, triple.subject_id, triple.predicate,
                                                triple.object_id or "<empty>"))
    print("candidates : %d (merged triples + 5 injected defects)" % len(candidates))
    print("accepted   : %d" % len(gate["accepted"]))
    print("rejected   : %s" % dict(sorted(reasons.items())))
    assert len(gate["accepted"]) == 5 and len(candidates) == 13
    assert dict(reasons) == {"self_loop": 2, "low_confidence": 3, "missing_endpoint": 1,
                             "unknown_predicate": 1, "duplicate": 1}
    assert len(result["merged"]) - len(result["accepted"]) == len(result["rejected"]) == 3
    return True


def exercise_6() -> bool:
    print("\n--- Exercise 6: Cypher / JSON / CSV Export ---")
    result = run_pipeline(SAMPLE_CORPUS)
    statements = result["cypher"]
    node_stmts = [s for s in statements if s["query"].startswith("MERGE (n:Entity")]
    rel_stmts = [s for s in statements if s["query"].startswith("MATCH (a:Entity")]
    print("cypher statements : %d (node=%d, rel=%d)" % (len(statements), len(node_stmts), len(rel_stmts)))
    print("\nexample node statement:\n%s\nparams: %s" % (node_stmts[0]["query"],
                                                        json.dumps(node_stmts[0]["params"], sort_keys=True)))
    example = [s for s in rel_stmts if s["params"]["object_id"] == entity_id("Knowledge Graph")][0]
    print("\nexample rel statement:\n%s\nparams: %s" % (example["query"], json.dumps(example["params"],
                                                                                    sort_keys=True)))
    payload = json.loads(result["json"])
    node_rows = list(csv.reader(io.StringIO(result["csv"]["nodes.csv"])))
    rel_rows = list(csv.reader(io.StringIO(result["csv"]["relationships.csv"])))
    print("\njson export       : nodes=%d relationships=%d" % (len(payload["nodes"]), len(payload["relationships"])))
    print("csv nodes.csv     : header=%s rows=%d" % (node_rows[0], len(node_rows) - 1))
    print("csv relationships : header=%s rows=%d" % (rel_rows[0], len(rel_rows) - 1))
    assert any("MERGE (n:Entity {id: $id})" in s["query"] for s in statements)
    assert all("$" in s["query"] and "'" not in s["query"] for s in statements), "parameterization broken"
    assert len(statements) == len(result["entities"]) + len(result["accepted"]) == 12
    assert len(payload["nodes"]) == 7 and len(payload["relationships"]) == 5
    assert all(set(r) == {"subject", "predicate", "object", "subject_id", "object_id", "confidence", "provenance"}
               for r in payload["relationships"])
    names = {eid: e.name for eid, e in result["entities"].items()}
    assert payload["relationships"] == [t.to_dict(names) for t in result["accepted"]]
    assert node_rows[0] == ["entity_id:ID", "name", "type", ":LABEL"]
    assert rel_rows[0] == [":START_ID", ":END_ID", ":TYPE", "rel_id", "confidence", "chunk_ids"]
    assert len(node_rows) - 1 == 7 and len(rel_rows) - 1 == 5
    node_id_set = {row[0] for row in node_rows[1:]}
    assert all(row[0] in node_id_set and row[1] in node_id_set for row in rel_rows[1:])
    assert all(row[2] in ALLOWED_PREDICATES for row in rel_rows[1:])
    return True


def run_all() -> bool:
    exercises = [exercise_1, exercise_2, exercise_3, exercise_4, exercise_5, exercise_6]
    passed = 0
    for exercise in exercises:
        try:
            passed += 1 if exercise() else 0
        except AssertionError as exc:
            print("[FAIL] %s -> %s" % (exercise.__name__, exc))
    if passed == len(exercises):
        print("\n[PASS] All 6/6 exercises passed successfully.")
        return True
    print("\n[FAIL] %d/%d exercises passed." % (passed, len(exercises)))
    return False


if __name__ == "__main__":
    sys.exit(0 if run_all() else 1)
