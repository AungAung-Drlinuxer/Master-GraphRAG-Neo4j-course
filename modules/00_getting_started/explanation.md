# M00 — Getting Started: အခြေခံသဘောတရားများ

ဤ module သည် GraphRAG ကို မတည်ဆောက်မီ လိုအပ်သော မူလအခြေခံကို တင်ပေးသည် — RAG pipeline ၏
အဆင့်များ၊ Vector Search ၏ ကန့်သတ်ချက်များ၊ Knowledge Graph ၏ အစိတ်အပိုင်းများ။
ဖော်ပြချက်တိုင်းတွင် **ဘာကြောင့် ဤနည်းလမ်း ဖြစ်သည်** နှင့် **ဘယ်အချိန်တွင် မသုံးသင့်** ကို တွဲဖက်ဖော်ပြသည်။
---

## ၁။ Course architecture နှင့် lab များ run ပုံ

Course ကို module ၉ ခုအဖြစ် ခွဲထားပြီး module တိုင်းတွင် file ၅ ခု တူညီစွာ ရှိသည် —
`README.md` (scope)၊ `explanation.md` (သဘောတရား)၊ `exercise.md` (လေ့ကျင့်ခန်း)၊
`solution.md` (reference)၊ `lab.py` (executable)။

Module များ၏ ချိတ်ဆက်မှုသည် တစ်လမ်းညွှန်ဖြစ်သည် —

```text
M01–M03  Knowledge Graph ဖော်ဆောင်ခြင်း →  M04  Project: Create a Knowledge Graph from Text
                                                      │
M05–M06  Neo4j storage                                │
        │                                             │
        └── M07 Knowledge Graph-based RAG  ───  M08 Conclusion
```

Lab တိုင်းသည် Neo4j server မလိုဘဲ run နိုင်ရမည် — graph traversal၊ Cypher statement generation နှင့်
query validation များကို Python ဖြင့် simulate လုပ်သည်။ ဤဒီဇိုင်းသည် graded check ကို
deterministic ဖြစ်စေသည် — server state ပြောင်းလဲမှုကြောင့် result မကွဲပြားနိုင်။

```bash
python3 modules/00_getting_started/lab.py
```

`lab.py` သည် `assert` ဖြင့် စစ်ဆေးပြီး အောင်မြင်ပါက `exit 0`၊ ကျရှုံးပါက `exit 1` ပြန်သည်။

**Rationale** — assertion-based lab သည် output ကို လူမဖတ်လည်း CI ဖြင့် စစ်နိုင်သည်။
**Trade-off** — assertion သည် ရလဒ်တစ်ခုတည်းကို စစ်သည်။ algorithm ၏ reasoning ကို စစ်လိုပါက
`print` လုပ်ထားသော intermediate value များကို ဖတ်ရမည်။

---

## ၂။ RAG ၏ အခြေခံ pipeline

RAG သည် (က) retrieval နှင့် (ခ) generation ကို ပေါင်းစပ်သည်။ အဆင့်များသည်
partial order တစ်ခု ဖြစ်သည် — အဆင့်တိုင်း၏ output သည် နောက်အဆင့်၏ input ဖြစ်သည်။

```text
ingest → chunk → embed → index → retrieve → generate
```

- **ingest** — raw document များကို စုစည်းခြင်း၊ format normalization
- **chunk** — text ကို Token budget အလိုက် ဖြတ်ခြင်း
- **embed** — Chunk တိုင်းကို Embedding model ဖြင့် vector အဖြစ် ပြောင်းခြင်း
- **index** — vector များကို ရှာဖွေနိုင်သော Index ထဲ ထည့်ခြင်း (ANN index)
- **retrieve** — Query vector နှင့် အနီးစပ်ဆုံး chunk k ခု ဆွဲထုတ်ခြင်း
- **generate** — ဆွဲထုတ်ထားသော chunk များကို context အဖြစ် LLM ထဲ ထည့်၍ အဖြေထုတ်ခြင်း

Pipeline အဆင့်များကို order ပြန်စီခြင်းသည် dependency order ကို ဖော်ထုတ်ခြင်း ဖြစ်သည်။
ဤ lab သည် tie-break အတွက် အမည်အလိုက် (alphabetical) စီသည် — ထို့ကြောင့် run တိုင်း result တူသည်။

```python
PIPELINE_DEPENDENCIES = {
    "ingest": (), "chunk": ("ingest",), "embed": ("chunk",),
    "index": ("embed",), "retrieve": ("index",), "generate": ("retrieve",),
}

def topological_order(stages, dependencies):
    ordered, remaining = [], sorted(set(stages))
    while remaining:
        ready = [s for s in remaining if all(d in ordered for d in dependencies[s])]
        assert ready, "dependency cycle detected"
        ordered.append(ready[0])
        remaining.remove(ready[0])
    return ordered

# Expected output:
# ['ingest', 'chunk', 'embed', 'index', 'retrieve', 'generate']
```

**Rationale** — order error သည် silent failure ဖြစ်သည် — ဥပမာ `embed` မပြီးမီ `index` လုပ်ပါက
Index ထဲ chunk တစ်ချို့ လုံးဝ မရောက်ဘဲ retrieval recall ကျသည်။
**Trade-off** — strict linear order သည် pipeline ကို increment update အလိုက် partial re-run
လုပ်ရာတွင် အခက်အခဲ ဖြစ်စေသည် — ထိုအခြေအနေတွင် stage တိုင်းကို idempotent အဖြစ် ရေးရမည် (M03, M06)။

---

## ၃။ Plain Vector RAG ၏ ကန့်သတ်ချက်များ

Vector Search သည် ပြဿနာ ၃ ခုကို မဖြေနိုင်ပါ —

1. **Chunk isolation** — အဖြေသည် chunk တစ်ခုထဲ မဟုတ်ဘဲ chunk နှစ်ခုကို entity ဆက်စပ်မှုဖြင့်
   ချိတ်မှ ရနိုင်။ ဥပမာ — "Alice က ဘယ်ကုမ္ပဏီမှာ အလုပ်လုပ်သည်" ဆိုသည့် အဖြေသည်
   `Alice Chen | works_at | Acme Corp` (chunk-02) နှင့် `Acme Corp | founded_in | Cupertino` ကို
   ချိတ်မှ ပြန်ဖြေနိုင်သည်။ similarity ranking သည် ထို join ကို မလုပ်သည်။
2. **Multi-hop မဖြေနိုင်ခြင်း** — hop ၂ ခုနှင့် အထက် လိုသော query အတွက် လိုအပ်သည့် chunk အားလုံး
   top-k ထဲ မပါနိုင်ပါ။ k ကို တိုးလျှင် context window ပြည့်ပြီး noise တိုးသည်။
3. **Global summarization အားနည်းခြင်း** — "corpus တစ်ခုလုံး၏ အဓိက ခေါင်းစဉ် ၃ ခု" ကဲ့သို့
   corpus-wide aggregate မေးခွန်းများအတွက် top-k chunk သည် corpus ၏ အပိုင်းတစ်ခုသာ ကိုယ်စားပြုသည် —
   ဤသည် sampling bias ဖြစ်သည်။

Cosine similarity သည် embedding vector နှစ်ခုအကြား ထောင့်ကို တိုင်းသည် —

```text
cos(A, B) = (A · B) / (||A|| · ||B||)
```

```python
import math

def cosine_similarity(left, right):
    dot = sum(a * b for a, b in zip(left, right))
    norm_left = math.sqrt(sum(a * a for a in left))
    norm_right = math.sqrt(sum(b * b for b in right))
    if norm_left == 0.0 or norm_right == 0.0:
        return 0.0
    return dot / (norm_left * norm_right)

query = [0.90, 0.10, 0.00, 0.20]
chunks = {
    "chunk-01": [0.85, 0.15, 0.05, 0.10],
    "chunk-02": [0.10, 0.80, 0.60, 0.10],
    "chunk-03": [0.00, 0.20, 0.95, 0.30],
    "chunk-04": [0.70, 0.05, 0.10, 0.90],
}
ranking = sorted(chunks.items(), key=lambda kv: -cosine_similarity(query, kv[1]))
# Expected output:
# chunk-01 0.991173 | chunk-04 0.767112 | chunk-02 0.202864 | chunk-03 0.084898
```

**Rationale** — cosine သည် vector length ကို ပယ်ဖျက်သောကြောင့် document အရှည် မတူသည့်
chunk များကို တိုက်ရိုက် နှိုင်းယှဉ်နိုင်သည်။
**Trade-off** — cosine သည် lexical overlap မကြည့်၊ semantic neighborhood အပေါ်သာ မူတည်သည် —
rare identifier (ဥပမာ product code) အတွက် exact match ထက် အလွယ်တကူ အမှားမှားသည်။
ထို့ကြောင့် production တွင် BM25 ကဲ့သို့ keyword scoring ကို ပေါင်းထည့်လေ့ရှိသည် (hybrid search)။

---

## ၄။ Graph RAG သို့ ရောက်ရှိသည့် လမ်းကြောင်း

Retrieval သည် အဆင့်လိုက် တိုးတက်သည် — အဆင့်တိုင်းသည် ရှေ့အဆင့်၏ ကန့်သတ်ချက်ကို ဖြေသည် —

- **Vector RAG** — semantic recall ကောင်းသည်၊ entity identity မသိပါ
- **Hybrid Search** — vector + BM25 fusion၊ rare term precision တိုးသည်၊ join မလုပ်နိုင်ဆဲ
- **Knowledge Graph** — entity များကို Node အဖြစ်၊ fact များကို Relationship အဖြစ် သိုလှောင်သည်။
  ဤအဆင့်တွင် multi-hop traversal ဖြစ်နိုင်သည်
- **GraphRAG** — graph structure ကို retrieval signal အဖြစ် သုံးသည် —
  entity-anchored subgraph၊ Text-to-Cypher၊ community summary (M07)

Modality ရွေးချယ်မှုကို query feature အပေါ် မူတည်၍ ဆုံးဖြတ်သည် —

```python
def select_modality(features):
    if features["hop_count"] >= 2 and features["spans_documents"]:
        return "GraphRAG - entity-anchored subgraph retrieval"
    if features["needs_corpus_wide_summary"]:
        return "GraphRAG - community summary retrieval"
    if features["needs_structured_filter"]:
        return "Text-to-Cypher"
    return "Vector Search - plain RAG"

# Expected output:
# Q1 -> Vector Search - plain RAG
# Q2 -> GraphRAG - entity-anchored subgraph retrieval
# Q3 -> GraphRAG - community summary retrieval
# Q4 -> Text-to-Cypher
```

**Rationale** — routing သည် cost ကို လျှော့ချသည် — local fact query အားလုံးကို graph traversal
ဖြင့် ဖြေပါက latency မြင့်ပြီး အကျိုးမရှိ။
**Trade-off** — routing classifier မှားပါက ပိုဆိုးသည် — multi-hop query ကို vector သို့ လွှဲပါက
silent wrong answer ဖြစ်သည်။ ထို့ကြောင့် router ၏ recall ကို separate အနေဖြင့် တိုင်းရမည်။

Failure mode များကို တိုင်းတာနိုင်သော label အဖြစ် ခွဲထုတ်ခြင်းသည် အရေးကြီးသည် —
`ingestion_gap` (entity သည် Index ထဲ မရှိ)၊ `global_summarization_failure`၊
`multi_hop_failure`၊ `chunk_isolation`၊ `no_failure`။ ဤ label များသည် M07 ၏ evaluation
baseline ဖြစ်လာသည်။

---

## ၅။ Knowledge Graph ၏ အစိတ်အပိုင်းများနှင့် Triple

Property Graph model တွင် အစိတ်အပိုင်း ၄ ခု ရှိသည် —

| အစိတ်အပိုင်း | ဖော်ပြချက် |
|---|---|
| **Node** | Entity တစ်ခု (ဥပမာ `(p:Person {id: "alice"})`) |
| **Label** | Node ၏ အမျိုးအစား (`:Person`, `:Company`) |
| **Relationship** | ဦးတည်ချက်ရှိ၊ အမျိုးအစားရှိ ဆက်စပ်မှု (`-[:WORKS_AT]->`) |
| **Property** | Node သို့မဟုတ် Relationship ပေါ်ရှိ key-value (`name`, `confidence`) |

**Triple** သည် (Subject, Predicate, Object) သုံးခုတည်း ဖြင့် fact တစ်ခုကို ကိုယ်စားပြုသည် —
graph ထဲတွင် Subject နှင့် Object သည် Node၊ Predicate သည် Relationship type ဖြစ်သည်။
ထို့ကြောင့် Triple list သည် Graph သို့ ရောက်သည့် ကြားခံ format ဖြစ်သည်။

```text
(Acme Corp)-[founded_in]->(Cupertino)    [chunk-01]
(Alice Chen)-[works_at]->(Acme Corp)     [chunk-02]
```

Triple တိုင်းတွင် provenance (source chunk id) ကို ချိတ်ထားရမည် — မဟုတ်ပါက LLM ထုတ်ပေးသော
fact ကို source text အထိ ပြန်စစ် (audit) လုပ်နိုင်မည် မဟုတ်။

```cypher
// Triple list ကို idempotent ဖြစ်စေသော write pattern
UNWIND $triples AS row
MERGE (s:Entity {id: row.subject_id})
MERGE (o:Entity {id: row.object_id})
MERGE (s)-[r:REL {type: row.predicate}]->(o)
SET r.source_chunk = row.source_chunk
```

`MERGE` ကို ရွေးရသည့် အကြောင်းရင်းမှာ အလားတူ ingestion ကို နှစ်ကြိမ် run လုပ်ပါက
duplicate node မဖြစ်စေရန် ဖြစ်သည်။ **Trade-off** — `MERGE` သည် `CREATE` ထက် နှေးသည်။
ထို့ကြောင့် bulk load အတွက် uniqueness constraint နှင့် `UNWIND` batch ကို တွဲသုံးရမည် (M06)။

**သတိပေးချက်** — Text-to-Cypher ကို production တွင် ချိတ်ဆက်ပါက `DELETE`၊ `DETACH DELETE`၊
`SET` ကဲ့သို့ write clause များကို allowlist ဖြင့် block ရမည်။ ဤ module ၏ lab သည် query ကို
parse/validate သာ လုပ်သည်၊ server သို့ မပို့ပါ။

---

## ၆။ Toolchain နှင့် environment

| အစိတ်အပိုင်း | အသုံးပြုပုံ | လိုအပ်သည့် module |
|---|---|---|
| Python standard library | lab အားလုံး၏ algorithm၊ Cypher string ဖော်ဆောင်ခြင်း | M00 — M08 |
| Neo4j (Docker) | Property Graph သိုလှောင်ခြင်း၊ Cypher run ခြင်း | M05 — M07 |
| Cypher | graph read/write၊ traversal | M05 — M07 |
| Python driver (`neo4j`) | application မှ Neo4j သို့ ချိတ်ဆက်ခြင်း | M06 |

Lab များသည် standard library သာ သုံးသောကြောင့် network မရှိသော environment တွင်လည်း run နိုင်သည်၊
result သည် run တိုင်း တူသည် — `random` module ကို မသုံးရ၊ system clock ကို မမှီခိုရ။
Randomness လိုအပ်ပါက fixed-seed LCG ကို ကိုယ်တိုင် implement လုပ်ရမည်။

Neo4j ကို local တွင် မြှောက်လိုပါက —

```bash
docker run --name graphrag-neo4j \
  -p 7474:7474 -p 7687:7687 \
  -e NEO4J_AUTH=neo4j/password \
  neo4j:5
```

ဤ command သည် Browser UI (port 7474) နှင့် Bolt protocol (port 7687) ကို ဖွင့်သည်။
**သတိပေးချက်** — `NEO4J_AUTH` ထဲတွင် ကိုယ်ပိုင် production password ကို မထည့်ရ၊
`.env` ဖိုင်ကို version control သို့ မတင်ရ။

**Rationale** — stdlib-only lab သည် grader နှင့် learner အကြား dependency drift ကို ဖယ်ရှားသည် —
environment တူညီမှုသည် result တူညီမှုကို အာမခံသည်။
**Trade-off** — stdlib simulation သည် Neo4j ၏ actual query planner၊ index behavior နှင့်
transaction semantics ကို မဖမ်းနိုင်ပါ။ ထို့ကြောင့် M05 မှစ၍ live test ကို သီးခြား run ရမည်။

---

## Production Considerations

- **Baseline ကို ဦးစွာ တိုင်းပါ** — GraphRAG ကို မတည်ဆောက်မီ Plain Vector RAG ၏ recall
  ကို dataset တူညီစွာ ဖြင့် တိုင်းထားရမည်။ မဟုတ်ပါက graph build cost ကို အကျိုးအမြတ်နှင့်
  နှိုင်းယှဉ်နိုင်မည် မဟုတ်။
- **Idempotency** — ingestion ကို နှစ်ကြိမ် run လုပ်နိုင်ရမည်။ `MERGE` + uniqueness constraint သည်
  duplicate entity ကို တားသည်။
- **Cost vs fidelity** — multi-hop ဖြေနိုင်ခြင်းသည် ingestion cost နှင့် graph maintenance
  overhead ကို တိုးစေသည်။ hop depth ၂–၃ ထက် ကျော်လွန်သော traversal သည် latency ကို
  exponentially မြှင့်စေသည် — query တိုင်း၏ hop budget ကို ကန့်သတ်ရမည်။
- **Provenance** — triple တိုင်းတွင် source chunk id၊ extraction method၊ confidence ကို မှတ်ရမည်။
  မဟုတ်ပါက hallucinated fact ကို production တွင် ရှာမတွေ့နိုင်ပါ။
- **Guardrails** — Text-to-Cypher နှင့် ဆိုင်သော module များတွင် write clause များကို
  allowlist/denylist ဖြင့် ပိတ်ရမည်၊ read-only role ကို သီးခြား သတ်မှတ်ရမည်။
- **Monitoring** — entity coverage၊ duplicate entity rate၊ retrieval hit rate သုံးခုကို
  time series အဖြစ် မှတ်ထားပါက corpus drift ကို စောစီးစွာ တွေ့နိုင်သည်။

---

## Summary Checklist

- [ ] RAG pipeline အဆင့် ၆ ခုကို dependency order ဖြင့် စီနိုင်သည်
- [ ] Cosine similarity ကို လက်ဖြင့် တွက်နိုင်ပြီး chunk ranking ကို ရှင်းပြနိုင်သည်
- [ ] Query feature အလိုက် retrieval modality ရွေးချယ်နိုင်သည်
- [ ] Plain Vector RAG ၏ failure mode ၄ ခုကို ခွဲခြားနိုင်သည် (ingestion gap၊ chunk isolation၊ multi-hop၊ global summary)
- [ ] Triple (SPO) structure နှင့် Node/Relationship သို့ ပြောင်းပုံကို ရှင်းပြနိုင်သည်
- [ ] Lab ကို `python3 modules/00_getting_started/lab.py` ဖြင့် run ၍ `exit 0` ရရှိကြောင်း စစ်ပြီးသည်
- [ ] ဤ module ၏ toolchain (stdlib၊ Docker၊ Neo4j၊ Cypher) ဘယ်အချိန်တွင် လိုအပ်သည်ကို သိသည်
