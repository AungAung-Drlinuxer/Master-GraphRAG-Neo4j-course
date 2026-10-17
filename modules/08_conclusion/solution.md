# M08 — Conclusion — Reference Solution

Exercise တိုင်းအတွက် reference implementation ဖြစ်သည်။ Code သည် `lab.py` နှင့် algorithm အရ
တူညီသည် — `lab.py` တွင် `print` နှင့် `assert` ပိုထည့်ထားသည်။

---

## Exercise 1 — Full pipeline recap (stage ordering)

```python
import sys
import re
import json
import math
import hashlib
from collections import OrderedDict, defaultdict

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
```

`entity_link` သည် prerequisite မရှိဘဲ `retrieve` သည် `entity_link` နှင့် `graph_write` နှစ်ခုလုံးကို
စောင့်သည့် ဖွဲ့စည်းပုံက အရေးကြီးသည် — ၎င်းသည် ingestion-side နှင့် retrieval-side ကို ခွဲပေးသည့်
နေရာ ဖြစ်ပြီး incremental update ၏ အခြေခံ ဖြစ်သည်။

**အဓိကအယူအဆ** — Pipeline ကို DAG အဖြစ် ဖော်ပြခြင်းဖြင့် stage အသစ်တစ်ခု ထည့်သည့်အခါ မည်သည့်
stage များ ပြန်လည် run ရမည်ကို algorithm အရ ဆုံးဖြတ်နိုင်သည်။ Module တိုင်း၏ lab သည် ဤ DAG ၏
အစိတ်အပိုင်းတစ်ခုကို implement လုပ်ထားသည်။

---

## Exercise 2 — Cost / latency model

```python
CHARS_PER_TOKEN = 4.0


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
    return {
        "chunks": chunks,
        "input_tokens": input_tokens,
        "output_tokens": output_tokens,
        "cost_usd": cost_usd,
        "per_chunk_seconds": per_chunk_seconds,
        "sequential_latency_s": chunks * per_chunk_seconds,
        "parallel_latency_s": math.ceil(chunks / workers) * per_chunk_seconds,
    }


def retrieval_latency_ms(nodes_scanned, edges_scanned, generation_tokens,
                         generation_tokens_per_second):
    traversal_ms = 4.0 + nodes_scanned * 0.05 + edges_scanned * 0.02
    generation_ms = generation_tokens / generation_tokens_per_second * 1000.0
    return traversal_ms, generation_ms, traversal_ms + generation_ms
```

ပုံစံခွက် ဤဖြင့် တွက်သည့်အခါ —

```
corpus=48000 chars -> chunks=24
  input tokens  = 19200
  output tokens = 5760
  ingestion cost = $18.2400
  per-chunk latency = 8.817 s
  sequential latency = 211.600 s
  parallel latency   = 52.900 s
  query traversal = 4.40 ms, generation = 2000.00 ms
  query total     = 2004.40 ms
```

**အဓိကအယူအဆ** — Cost သည် corpus size နှင့် linear ဖြစ်၍ ခန့်မှန်းနိုင်သည်၊ သို့သော် query
latency ကို generation token အရေအတွက်ဖြင့် ထိန်းရမည်။ Traversal ကို optimize လုပ်ရန် ကြိုးစားခြင်းသည်
millisecond အနည်းငယ် ရရှိပြီး၊ context ကို ချုံ့ခြင်းက second များစွာ ရရှိသည်။

---

## Exercise 3 — Build-vs-buy decision scorer

```python
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
```

Default weight ဖြင့် `build=3.450`၊ `buy=3.350` — build ရွေးသည်။ `time_to_first_value` ကို 0.25 မှ
0.40 သို့ တင်ပါက `build=3.050`၊ `buy=3.800` — buy ရွေးသည်။

**အဓိကအယူအဆ** — Score သည် weight ပေါ်တွင် မှီခိုသည်၊ ထို့ကြောင့် "GraphRAG ကို build လုပ်သင့်
သည်" ဆိုသည့် ဖြေချက် မရှိ။ အဖွဲ့အစည်း၏ engineering capacity နှင့် time-to-value ဦးစားပေးမှုကို
weight အဖြစ် တိတိကျကျ ရေးပြီးမှ ဆုံးဖြတ်ရမည်။ Managed service သည် extraction quality
tooling နှင့် monitoring ကို အခမဲ့ပါလာသော်လည်း data residency ကန့်သတ်ချက် ရှိသည့် domain များတွင်
ရွေးလို့ မရနိုင်သည်။

---

## Exercise 4 — Incremental update planner

```python
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
```

`("Dave", "LEADS", "Payments Squad")` ထည့်သည့်အခါ —

```
ADD_NODE Dave
DELETE_EDGE Carol LEADS Payments Squad
ADD_EDGE Dave LEADS Payments Squad
base signature=5354f4bd285ccbb7 -> updated signature=94ac803b9cd59a9f
```

Node တူညီသော Relationship နှစ်ခု ဆက်ရှိနေပါက "ဘယ်သူက Leads" ဆိုသည့် question သည်
အဖြေနှစ်ခု ရနိုင်ပြီး generator သည် မှားနိုင်သည်။ ထို့ကြောင့် single-valued Relationship ကို
အဟောင်း ဖယ်ရှားရမည်။

**အဓိကအယူအဆ** — Idempotency သည် `MERGE` ကို သုံးခြင်းဖြင့် အလိုအလျောက် မရနိုင်ဘဲ၊ operation
တိုင်းကို diff အဖြစ် ဖော်ခြင်းဖြင့် ရသည်။ Signature-based verification သည် re-ingestion ကြောင့်
graph မပြောင်းကြောင်း test အတွက် တိကျသော အထောက်အထား ဖြစ်သည်။

---

## Exercise 5 — Production architecture checklist

```python
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
```

ပြည့်စုံသော design — `score=7/7`၊ `critical_failures=[]`၊ `passes=True`။
`read_only_cypher_guardrail` ဖယ်လိုက်ပါက `critical_failures=['read_only_cypher_guardrail']`၊
`passes=False`။

**အဓိကအယူအဆ** — Text-to-Cypher ကဲ့သို့ LLM က graph ကို တိုက်ရိုက်ရေးနိုင်သော pattern တွင်
read-only guardrail သည် အဓိက control ဖြစ်သည်။ `DELETE`၊ `DETACH DELETE`၊ `DROP` clause များကို
block မလုပ်ပါက prompt injection တစ်ခုတည်းဖြင့် graph တစ်ခုလုံး ပျက်စီးနိုင်သည်။
Critical control ကို total score နှင့် မပေါင်းရ — score မြင့်နေခြင်းသည် လုံခြုံမှုကို မဆိုလိုသည်။

---

## Exercise 6 — End-to-end mini GraphRAG integration test

### ၆.၁ Chunking နှင့် scripted extraction

```python
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


def clean_surface(text):
    surface = re.sub(r"^(the|a|an)\s+", "", text.strip(), flags=re.IGNORECASE)
    return surface.strip(" .,;:")


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
```

`max_chars=90`၊ `overlap=1` ဖြင့် sentence 5 ခုမှ chunk 4 ခု ထွက်သည် —

```
chunk 0: 2 sentences
chunk 1: 2 sentences
chunk 2: 2 sentences
chunk 3: 2 sentences
```

### ၆.၂ Entity resolution နှင့် graph တည်ဆောက်ခြင်း

```python
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


def resolve_entity(surface):
    key = re.sub(r"\s+", " ", clean_surface(surface).lower())
    key = ENTITY_ALIASES.get(key, key)
    return ENTITY_CANONICAL.get(key, clean_surface(surface))


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
```

Overlap ကြောင့် triple များ ထပ်ထွက်သည့်အတွက် `raw=8` မှ `after dedup=5` ဖြစ်သည်။
Graph တွင် `nodes=6`၊ `edges=5`။ `resolve_entity("Payments team")` သည် `"Payments Squad"` ပြန်သည် —
"Carol leads the Payments team." မှ triple သည် "Payments squad builds ..." မှ triple နှင့်
အလိုအလျောက် ချိတ်ဆက်သည်။ Entity resolution မရှိပါက graph တွင် `Payments Squad` နှင့်
`Payments team` ဟူ၍ node နှစ်ခု ကွဲနေပြီး "ဘယ်သူက Payments squad ကို leads" ဆိုသည့် question ကို
ဖြေနိုင်တော့မည် မဟုတ်။

### ၆.၃ Entity linking၊ k-hop retrieval၊ serialization၊ generation

```python
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
```

"Who leads the Payments Squad?" အတွက် output —

```
question: Who leads the Payments Squad?
  entity linking -> anchors=['Payments Squad']
  1-hop subgraph -> nodes=['Alice', 'Carol', 'Ledger Service', 'Payments Squad']
  retained edges = 3, hops bound excluded Audit Store
  serialized prompt context:
    Knowledge Graph triples:
    Alice --MANAGES--> Payments Squad
    Carol --LEADS--> Payments Squad
    Payments Squad --BUILDS--> Ledger Service
  generator answer -> Carol
```

"Who builds the Ledger service?" → anchor `Ledger Service`၊ အဖြေ `Payments Squad`။

**အဓိကအယူအဆ** — `Audit Store` သည် hop ကန့်သတ်ချက်ကြောင့် context မှ ထွက်သွားသည် — ဤသို့
hop bound ကို တိတိကျကျ သတ်မှတ်ခြင်းဖြင့် context token၊ Cost နှင့် latency ကို ထိန်းနိုင်သည်။
Generator ကို rule-based ဖြင့် အစားထိုးထားခြင်းသည် LLM မလိုဘဲ pipeline တစ်ခုလုံး၏
correctness (chunk → graph → retrieval → answer) ကို test လုပ်နိုင်ရန် ဖြစ်သည်။ Lab ဤခုသည်
M08 ၏ exercise ခြောက်ခုလုံးကို `[PASS] All 6/6 exercises passed successfully.` ဖြင့် ပိတ်သည်။
