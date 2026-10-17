# M00 — Solution: Getting Started

Reference implementation များသည် `lab.py` နှင့် algorithm အရ တူညီသည် —
`lab.py` တွင် `print` နှင့် `assert` ပိုထည့်ထားသည်။

---

## Exercise 1 — RAG Pipeline Stage Ordering

```python
PIPELINE_DEPENDENCIES = {
    "ingest": (),
    "chunk": ("ingest",),
    "embed": ("chunk",),
    "index": ("embed",),
    "retrieve": ("index",),
    "generate": ("retrieve",),
}
UNORDERED_STAGES = ["generate", "retrieve", "index", "embed", "ingest", "chunk"]
def topological_order(stages, dependencies):
    """Return a deterministic order in which every stage follows its dependencies."""
    ordered = []
    remaining = sorted(set(stages))
    while remaining:
        ready = [s for s in remaining if all(d in ordered for d in dependencies[s])]
        assert ready, "dependency cycle detected"
        chosen = ready[0]
        ordered.append(chosen)
        remaining.remove(chosen)
    return ordered
order = topological_order(UNORDERED_STAGES, PIPELINE_DEPENDENCIES)
print(order)
# Expected output:
# ['ingest', 'chunk', 'embed', 'index', 'retrieve', 'generate']
```

**အဓိကအယူအဆ** — Pipeline အဆင့်များသည် set တစ်ခု မဟုတ်၊ partial order တစ်ခု ဖြစ်သည်။
`ready` list သည် dependency အားလုံး ပြည့်ပြီးသော stage များသာ ပါသောကြောင့်
`ordered` list သည် အမြဲတမ်း valid order ဖြစ်သည်။ `sorted(set(stages))` ကို tie-break
အဖြစ် သုံးခြင်းသည် run တိုင်း result တူညီစေသည် — dict သို့မဟုတ် set ၏ iteration order
အပေါ် မမှီခိုရခြင်းသည် deterministic lab ၏ အခြေခံ လိုအပ်ချက် ဖြစ်သည်။
Cycle ရှိပါက `ready` list ဟင်းလင်းဖြစ်လာပြီး `assert` က ချက်ချင်း ကျရှုံးစေသည် —
infinite loop ဖြစ်ခြင်းကို ကာကွယ်သည်။

---

## Exercise 2 — Cosine Similarity Ranking

```python
import math
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
    scored = [(chunk_id, cosine_similarity(query, vector)) for chunk_id, vector in chunks.items()]
    scored.sort(key=lambda item: (-item[1], item[0]))
    return scored
for rank, (chunk_id, score) in enumerate(rank_chunks(QUERY_VECTOR, CHUNK_VECTORS), start=1):
    print("%d. %s similarity=%.6f" % (rank, chunk_id, score))
# Expected output:
# 1. chunk-01 similarity=0.991173
# 2. chunk-04 similarity=0.767112
# 3. chunk-02 similarity=0.202864
# 4. chunk-03 similarity=0.084898
```

**အဓိကအယူအဆ** — Cosine similarity သည် magnitude (vector length) ကို ပယ်ဖျက်ပြီး
ဦးတည်ချက်သာ တိုင်းသည် — ထို့ကြောင့် chunk အရှည် မတူသည့်အခါ ဖြစ်ပေါ်သော bias ကို ဖယ်ရှားသည်။
`norm == 0.0` ဖြစ်သည့် zero vector အတွက် `0.0` ပြန်ရသည့် branch သည် လိုအပ်သည် —
မဟုတ်ပါက `ZeroDivisionError` ဖြစ်သည်။ `(-score, chunk_id)` key သည် score တူပါက
chunk id အလိုက် တည်ငြိမ်စွာ စီစေသည် — float rounding ကြောင့် tie ဖြစ်နိုင်သော
production တွင် ဤ tie-break သည် pagination ၏ ညီညွတ်မှုကို ထိန်းသည်။

---

## Exercise 3 — Retrieval Modality Selection

```python
def select_modality(features):
    """Choose the cheapest retrieval modality that satisfies the query features."""
    if features["hop_count"] >= 2 and features["spans_documents"]:
        return "GraphRAG - entity-anchored subgraph retrieval"
    if features["needs_corpus_wide_summary"]:
        return "GraphRAG - community summary retrieval"
    if features["needs_structured_filter"]:
        return "Text-to-Cypher"
    return "Vector Search - plain RAG"
QUERIES = [
    ("Q1", {"hop_count": 0, "spans_documents": False, "needs_corpus_wide_summary": False,
            "needs_structured_filter": False}),
    ("Q2", {"hop_count": 3, "spans_documents": True, "needs_corpus_wide_summary": False,
            "needs_structured_filter": False}),
    ("Q3", {"hop_count": 1, "spans_documents": False, "needs_corpus_wide_summary": True,
            "needs_structured_filter": False}),
    ("Q4", {"hop_count": 0, "spans_documents": False, "needs_corpus_wide_summary": False,
            "needs_structured_filter": True}),
]
for query_id, features in QUERIES:
    print("%s -> %s" % (query_id, select_modality(features)))
# Expected output:
# Q1 -> Vector Search - plain RAG
# Q2 -> GraphRAG - entity-anchored subgraph retrieval
# Q3 -> GraphRAG - community summary retrieval
# Q4 -> Text-to-Cypher
```

**အဓိကအယူအဆ** — Rule များကို **အကျဉ်းဆုံးမှ အကျယ်ဆုံးသို့** စီထားရသည်။
`hop_count >= 2` စစ်ချက်သည် `spans_documents` နှင့် `and` ဖြင့် တွဲထားသည် —
document တစ်ခုတည်းအတွင်း hop ၂ ခုရှိပါက graph က အကျိုးရှိသော်လည်း corpus အတွင်း
မဖြန့်ပါက subgraph retrieval သည် overhead ဖြစ်သည်။ နောက်ဆုံး `return` သည်
"default = cheapest modality" ဆိုသည့် မူဝါဒကို ကိုယ်စားပြုသည် — graph ကို
မလိုအပ်သည့် query များကို graph သို့ မလွှဲခြင်းသည် cost ကို ထိန်းသည်။

---

## Exercise 4 — RAG Failure Mode Classification

```python
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
FAILURE_SCENARIOS = [
    ("S1", {"required_entity_in_index": True, "needs_corpus_wide_aggregate": False,
            "hop_count": 0, "facts_split_across_chunks": False}),
    ("S2", {"required_entity_in_index": False, "needs_corpus_wide_aggregate": False,
            "hop_count": 0, "facts_split_across_chunks": False}),
    ("S3", {"required_entity_in_index": True, "needs_corpus_wide_aggregate": False,
            "hop_count": 2, "facts_split_across_chunks": True}),
    ("S4", {"required_entity_in_index": True, "needs_corpus_wide_aggregate": True,
            "hop_count": 0, "facts_split_across_chunks": False}),
    ("S5", {"required_entity_in_index": True, "needs_corpus_wide_aggregate": False,
            "hop_count": 1, "facts_split_across_chunks": True}),
]
from collections import Counter
outcomes = {sid: classify_failure(features) for sid, features in FAILURE_SCENARIOS}
print(outcomes)
print(Counter(outcomes.values()))
# Expected output:
# {'S1': 'no_failure', 'S2': 'ingestion_gap', 'S3': 'multi_hop_failure',
#  'S4': 'global_summarization_failure', 'S5': 'chunk_isolation'}
# Counter({'no_failure': 1, 'ingestion_gap': 1, 'multi_hop_failure': 1,
#          'global_summarization_failure': 1, 'chunk_isolation': 1})
```

**အဓိကအယူအဆ** — Rule list ကို tuple အစဉ်လိုက် စစ်ခြင်းသည် priority ကို
code ဖွဲ့စည်းပုံအတွင်းတင် ဖော်ပြသည် — သီးခြား priority field မလိုအပ်။
S3 တွင် `hop_count >= 2` နှင့် `facts_split_across_chunks` နှစ်ခုလုံး မှန်သော်လည်း
`multi_hop_failure` သာ ပြန်သည် — multi-hop မအောင်မြင်ခြင်းသည် chunk isolation ၏
ပိုမိုပြင်းထန်သော ပုံစံ ဖြစ်သောကြောင့် သီးခြား label ထားခြင်းသည် evaluation တွင်
root cause ကို ရှာရလွယ်စေသည်။ `ingestion_gap` ကို ထိပ်ဆုံးထားရသည့် အကြောင်းရင်းမှာ
entity သည် Index ထဲ မရှိပါက retrieval technique မည်သည့်ဟာမှ မကယ်နိုင်သောကြောင့် ဖြစ်သည်။

---

## Exercise 5 — Triple (SPO) Parsing

```python
import re
from dataclasses import dataclass
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
    triples = []
    errors = []
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
triples, errors = parse_triples(TRIPLE_LINES)
unique = sorted(set(triples), key=lambda t: (t.subject, t.predicate, t.object, t.source_chunk))
print(len(triples), len(errors), len(triples) - len(unique))
# Expected output:
# 4 2 1
```

**အဓိကအယူအဆ** — Normalization သည် dedupe ၏ ရှေ့ဆက် အခြေခံဖြစ်သည် —
`"  Acme Corp "` နှင့် `"Acme Corp"` သည် triple တူညီသည်ဟု သတ်မှတ်နိုင်မှသာ
duplicate ၁ ခု ဖြစ်ကြောင်း တွေ့သည်။ `frozen=True` dataclass ကို သုံးခြင်းသည် triple ကို
hashable ဖြစ်စေပြီး `set()` ဖြင့် O(n) dedupe လုပ်နိုင်သည် — tuple အဖြစ် ပြောင်းရန်
မလိုအပ်။ Predicate ကို lowercase + space → `_` ပြောင်းခြင်းသည် Relationship type ကို
Cypher identifier အဖြစ် သုံးရန် ပြင်ဆင်ခြင်း ဖြစ်သည် (`-[:WORKS_AT]->`)။
မမှန်သော လိုင်းကို လွှင့်ပစ်မည့်အစား line number နှင့် တွဲဖက် မှတ်ထားခြင်းသည်
ingestion ပျက်ပါက မည်သည့်လိုင်းကို ပြန်ပြင်ရမည် ကို ရှာနိုင်စေသည်။

---

## Exercise 6 — GraphRAG Readiness Check

```python
NUMERIC_CHECKS = (
    ("entity_coverage", ">=", 0.85),
    ("relationship_density", ">=", 1.50),
    ("duplicate_entity_rate", "<=", 0.05),
    ("avg_chunk_tokens", "<=", 512.0),
)
BOOLEAN_CHECKS = (
    "uniqueness_constraint",
    "fulltext_index",
    "community_summary",
)
def _numeric_pass(value, operator, threshold):
    if operator == ">=":
        return value >= threshold
    return value <= threshold
def readiness_report(metrics):
    failed = []
    for name, operator, threshold in NUMERIC_CHECKS:
        if not _numeric_pass(metrics[name], operator, threshold):
            failed.append(name)
    for name in BOOLEAN_CHECKS:
        if not metrics[name]:
            failed.append(name)
    return {"verdict": "READY" if not failed else "NOT_READY", "failed": failed}
READY_PROFILE = {"entity_coverage": 0.93, "relationship_density": 2.40,
                 "duplicate_entity_rate": 0.02, "avg_chunk_tokens": 384.0,
                 "uniqueness_constraint": True, "fulltext_index": True,
                 "community_summary": True}
BLOCKED_PROFILE = {"entity_coverage": 0.71, "relationship_density": 1.10,
                   "duplicate_entity_rate": 0.12, "avg_chunk_tokens": 640.0,
                   "uniqueness_constraint": True, "fulltext_index": False,
                   "community_summary": False}
print(readiness_report(READY_PROFILE))
print(readiness_report(BLOCKED_PROFILE))
# Expected output:
# {'verdict': 'READY', 'failed': []}
# {'verdict': 'NOT_READY',
#  'failed': ['entity_coverage', 'relationship_density', 'duplicate_entity_rate',
#             'avg_chunk_tokens', 'fulltext_index', 'community_summary']}
```

**အဓိကအယူအဆ** — Readiness check သည် **failed list ကို ပြန်ပေးသည်၊ boolean တစ်ခု
တည်း မပြန်ပါ**။ အကြောင်းရင်းမှာ operator ၏ ရှုံးသွားသော check များသည် fix လုပ်ရမည့်
task list ဖြစ်လာသောကြောင့် ဖြစ်သည် — `NOT_READY` တစ်ခုတည်း ပြန်ပါက engineer သည်
ဘာကို ရှေးဦး ပြင်ရမည် ကို မသိနိုင်။ Numeric check နှင့် boolean check ကို tuple
နှစ်ခုအဖြစ် ခွဲထားခြင်းသည် threshold နှင့် flag အသစ် ထည့်ရာတွင် logic ကို
မထိတော့ဘဲ data သာ ထည့်ရုံ ဖြစ်စေသည်။ `<=` အတွက် `duplicate_entity_rate` နှင့်
`avg_chunk_tokens` သည် **ငယ်လေ ကောင်းလေ** ဖြစ်သည် — ဤ direction ကို check
declaration တွင်တင် သတ်မှတ်ထားခြင်းသည် "အဆိုးဆုံး threshold" ဆိုသည့် ခန့်မှန်းမှုကို
ဖယ်ရှားသည်။

---

## နိဂုံးချုပ်

Exercise ၆ ခုသည် M00 ၏ သဘောတရားများကို run နိုင်သော artifact အဖြစ် ပြောင်းပြခဲ့သည် —
pipeline ordering (Exercise 1)၊ Vector Search ၏ အခြေခံသင်္ချာ (2)၊ routing ဆုံးဖြတ်ချက် (3)၊
Vector RAG ၏ ကန့်သတ်ချက် (4)၊ Triple structure (5)၊ နှင့် GraphRAG readiness gate (6)။
ဤ pattern သည် M01–M08 တွင် ထပ်တူ ပြန်ပေါ်သည် — သဘောတရား → တိုင်းတာနိုင်သော check →
deterministic lab။
