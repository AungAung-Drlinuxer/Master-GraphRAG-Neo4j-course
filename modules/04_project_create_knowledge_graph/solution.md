# M04 — Reference Solution

Exercise တိုင်းအတွက် reference implementation ဖြစ်သည်။ Code များသည် `lab.py` နှင့် algorithm အရ တူညီပြီး
(`lab.py` တွင် `print` နှင့် `assert` ပိုပါသည်)။

## Exercise 1: Corpus Normalization

```python
# re, unicodedata, dataclass — standard library import (lab.py ရှု)
UNICODE_FOLD = {"\u2018": "'", "\u2019": "'", "\u201c": '"', "\u201d": '"',
                "\u2013": "-", "\u2014": "-", "\u2026": "...", "\u00a0": " "}


@dataclass
class Document:
    doc_id: str
    text: str
    char_count: int


def ingest_corpus(corpus):
    return [Document(d["doc_id"], d["raw_text"], len(d["raw_text"])) for d in corpus]


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
```

```
# Expected output:
#   doc-001 | raw_chars=144 | normalized_chars=143   (doc-002/003 အတွက် script ရလဒ်ကြည့်ပါ)
# dirty   : '  Neo4j\xa0 is  a graph–database.\n\n  “GraphRAG”  …  '
# cleaned : 'Neo4j is a graph-database. "GraphRAG" ...'
```

**အဓိကအယူအဆ** — newline ကို ဖျက်ပစ်လျှင် `database.Neo4j` ကဲ့သို့ စာလုံးနှစ်လုံး ကပ်သွားပြီး sentence splitting ပျက်သည်။
ထို့ကြောင့် newline/tab ကို space အဖြစ် **အရင်** ပြောင်းပြီး ကျန်သည့် control character များကို **နောက်မှ** ဖယ်သည်။
NFC normalize မလုပ်ပါက byte level တွင် မတူညီသည့် entity အမည် နှစ်ခုသည် duplicate node ဖြစ်လာသည်။

## Exercise 2: End-to-End Pipeline Run

```python
def split_sentences(text):
    return [s.strip() for s in re.split(r"(?<=[.!?])\s+", text) if s.strip()]


def chunk_document(doc):
    chunks, buf, ordinal = [], "", 0
    for sentence in split_sentences(doc.text):  # sentence-aligned: relationship မပြတ်ရန်
        candidate = (buf + " " + sentence).strip() if buf else sentence
        if buf and len(candidate) > CHUNK_SIZE:
            chunks.append(Chunk("%s:c%02d" % (doc.doc_id, ordinal), doc.doc_id, ordinal, buf))
            ordinal, buf = ordinal + 1, sentence
        else:
            buf = candidate
    if buf:
        chunks.append(Chunk("%s:c%02d" % (doc.doc_id, ordinal), doc.doc_id, ordinal, buf))
    return chunks


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
                triples.append(Triple(entity_id(a_entry["canonical"]), predicate,
                                      entity_id(b_entry["canonical"]),
                                      [Provenance(chunk.chunk_id, round(min(a_conf, b_conf), 2),
                                                  "pattern:" + predicate.lower())]))
        if not matched:  # co-occurrence fallback: လျှော့ချ confidence၊ gate တွင် ဖယ်ရှားခံရသည်
            resolved = [e for e in (resolve_surface(m)[0] for m in find_mentions(sentence)) if e is not None]
            for left, right in zip(resolved, resolved[1:]):
                if left["canonical"] != right["canonical"]:
                    triples.append(Triple(entity_id(left["canonical"]), "RELATED_TO",
                                          entity_id(right["canonical"]),
                                          [Provenance(chunk.chunk_id, COOCCURRENCE_CONFIDENCE, "cooccurrence")]))
    return triples


def run_pipeline(corpus):
    documents = [normalize_document(doc) for doc in ingest_corpus(corpus)]
    chunks = [c for doc in documents for c in chunk_document(doc)]
    raw_triples = [t for chunk in chunks for t in extract_from_chunk(chunk)]
    entities, merged = resolve_entities(raw_triples), merge_triples(raw_triples)
    gate = quality_gate(merged, entities)
    accepted = gate["accepted"]
    return {"documents": documents, "chunks": chunks, "raw_triples": raw_triples, "entities": entities,
            "merged": merged, "accepted": accepted, "rejected": gate["rejected"],
            "cypher": export_cypher(entities, accepted), "json": export_json(entities, accepted),
            "csv": export_csv(entities, accepted)}
```

```
# Expected output:
# chunk : 6 -> ['doc-001:c00', 'doc-001:c01', 'doc-002:c00', 'doc-002:c01', 'doc-003:c00', 'doc-003:c01']
# extract : 9 raw triples   resolve : 7 entities   merge : 8 triples   gate : 5 accepted / 3 rejected
# resolution : 'Graph Rag' -> GraphRAG (0.80, alias) | 'Knowledg Graph' -> Knowledge Graph (0.55, fuzzy)
# စစ်ဆေးပုံ: python3 modules/04_project_create_knowledge_graph/lab.py  ->  exit 0
```

**အဓိကအယူအဆ** — Extractor သည် recall ဦးစားပေးသည်; pattern မကိုက်သည့် sentence တွင်ပင် entity နှစ်ခုတွဲလျှင် co-occurrence
triple (0.45) ထုတ်ပြီး gate တွင် ဖယ်ရှားသည်။ `_DETERMINER` ကဲ့သို့ optional article pattern မထည့်ပါက `is built on
a Knowledge Graph` ကဲ့သို့ sentence မှ triple တစ်ခုလုံး လျော့ကျသည်။

## Exercise 3: Data Model Validation

```python
ALLOWED_ENTITY_TYPES = ("Technology", "Organization", "Concept")
ALLOWED_PREDICATES = ("IS_A", "USES", "BUILT_ON", "DEVELOPED_BY", "INCLUDES", "RELATED_TO")


def slug(text):
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")


def entity_id(canonical):
    return "ent:" + slug(canonical)


def resolve_entities(triples):
    known = {entity_id(e["canonical"]): Entity(entity_id(e["canonical"]), e["canonical"],
                                               e["type"], list(e["aliases"])) for e in GAZETTEER}
    used = OrderedDict()
    for triple in triples:
        for eid in (triple.subject_id, triple.object_id):
            if eid in known:
                used[eid] = known[eid]
    return used
```

```
# Expected output (ကောက်နုတ်ချက် — entity ၇ ခုလုံးကို print ပြသည်):
# node labels : ['Document', 'Chunk', 'Entity']   entity types : {'Concept': 2, 'Technology': 5}
# predicate hist : {'BUILT_ON': 2, 'IS_A': 1, 'USES': 2}   (ent:neo4j / ent:knowledge-graph / ...)
```

**အဓိကအယူအဆ** — Node id သည် canonical name မှ deterministic ဖြင့် ဆင်းသက်သည်။ `hash()` သို့မဟုတ် random မသုံးရ —
id သည် run နှစ်ခုတွင် မတူညီပါက `MERGE` က duplicate node ဖန်တီးသည်။ Entity type ကို closed set အဖြစ်
သတ်မှတ်ထားခြင်းကြောင့် extraction output မှ schema ပြင်ပ type များ ဝင်မလာနိုင်သည်။

## Exercise 4: Provenance Metadata

```python
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


def merge_triples(triples):
    merged = OrderedDict()
    for triple in triples:
        if triple.key in merged:
            merged[triple.key].provenance.extend(triple.provenance)
        else:
            merged[triple.key] = Triple(triple.subject_id, triple.predicate, triple.object_id,
                                        list(triple.provenance))
    return list(merged.values())
```

```
# Expected output (ကောက်နုတ်ချက် — merged triple ၈ ခုလုံးကို print ပြသည်):
#   Neo4j    -[USES]-> Cypher              conf=0.95 sources=['doc-001:c00']
#   GraphRAG -[BUILT_ON]-> Knowledge Graph conf=0.95 sources=['doc-001:c00', 'doc-002:c00']
#   merged triple provenance: [('doc-001:c00', 0.95), ('doc-002:c00', 0.95)]
```

**အဓိကအယူအဆ** — duplicate triple ကို ဖျက်ပစ်ခြင်းအစား provenance list ကို union လုပ်ခြင်းသည် အချက်အလက်
ဆုံးရှုံးမှုကို ရှောင်ပြီး support count ကို ထိန်းသိမ်းသည်။ Triple ၏ confidence ကို max ဖြင့် သတ်မှတ်သည်မှာ
source အများအပြား ထောက်ခံသည့် triple သည် gate ကို ဖြတ်နိုင်ရန် ဖြစ်သည်။

## Exercise 5: Quality Gate Filtering

```python
MIN_CONFIDENCE = 0.60


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
```

```
# Expected output:
#   REJECT self_loop         ent:neo4j -[DEVELOPED_BY]-> ent:neo4j
#   REJECT missing_endpoint  ent:neo4j -[USES]-> <empty>
#   REJECT unknown_predicate ent:neo4j -[FRIENDS_WITH]-> ent:cypher
#   REJECT duplicate         ent:neo4j -[USES]-> ent:cypher
#   REJECT low_confidence    ent:neo4j -[RELATED_TO]-> ent:graphrag  (+ injected 0.45 / 0.30 triples)
# candidates : 13    accepted : 5    rejected : {'duplicate': 1, 'low_confidence': 3, 'missing_endpoint': 1,
#   'self_loop': 2, 'unknown_predicate': 1}
```

**အဓိကအယူအဆ** — Gate ကို `elif` chain အဖြစ် ရေးခြင်းသည် reason တစ်ခုတည်းကို log လုပ်စေပြီး histogram ကို တိကျစေသည်။
Structure gate (endpoint၊ self-loop၊ predicate) ကို confidence gate အရင်စစ်ခြင်းသည် structure ချို့ယွင်းမှုကို
low-confidence ဟူသော blanket reason အောက်တွင် ဖုံးကွယ်မသွားစေရန် ဖြစ်သည်။ Self-loop သည် coreference
မှားယွင်းမှု၏ လက္ခဏာဖြစ်၍ upstream extractor ကို ပြင်ရန် signal ရသည်။

## Exercise 6: Cypher / JSON / CSV Export

```python
NODE_MERGE = "MERGE (n:Entity {id: $id})\nSET n.name = $name, n.type = $type"


def rel_id(subject_id, predicate, object_id):
    return "rel:" + slug("%s-%s-%s" % (subject_id, predicate, object_id))


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
```

```
# Expected output:
# cypher statements : 12 (node=7, rel=5)
# MATCH (a:Entity {id: $subject_id}), (b:Entity {id: $object_id})
# MERGE (a)-[r:BUILT_ON {id: $rel_id}]->(b)
# SET r.confidence = $confidence, r.chunk_ids = $chunk_ids, r.methods = $methods
# params: {"chunk_ids": ["doc-001:c00", "doc-002:c00"], "confidence": 0.95, "methods": ["pattern:built_on"],
#   "object_id": "ent:knowledge-graph", "subject_id": "ent:graphrag"}   json: nodes=7 relationships=5
# csv nodes.csv : header=['entity_id:ID', 'name', 'type', ':LABEL'] rows=7   relationships.csv rows=5
```

**အဓိကအယူအဆ** — `r:BUILT_ON` ကဲ့သို့ Relationship type ကို parameter မလုပ်နိုင်သဖြင့် whitelist (`ALLOWED_PREDICATES`)
ဖြင့် စစ်ပြီးမှသာ query string ထဲ ထည့်သည် — ဤအချက်သည် Cypher injection ကာကွယ်မှု၏ တစ်စိတ်တစ်ပိုင်းဖြစ်သည်။
`MERGE` ကို constraint နှင့် တွဲသုံးခြင်းဖြင့် pipeline ပြန် run တိုင်း duplicate မဖြစ်ဘဲ property များသာ update ဖြစ်သည်။
