# M04 — Project: Create a Knowledge Graph from Text — ရှင်းလင်းချက်

ဤ module သည် Knowledge Graph တည်ဆောက်သည့် Pipeline တစ်ခုလုံးကို end-to-end အဖြစ် ဖော်ပြသည်။
M01–M03 သည် အဆင့်တစ်ခုချင်းစီကို သီးခြားစီ ရှင်းပြခဲ့သည် — ဤနေရာတွင် ထို algorithm များကို
ချိတ်ဆက်ပြီး deliverable တစ်ခုတည်းအဖြစ် ထုတ်လုပ်သည်။ LLM extraction အဆင့်ကို **deterministic
scripted extractor** ဖြင့် အစားထိုးထားသည်မှာ Pipeline တစ်ခုလုံးကို offline၊ script တစ်ခုတည်းဖြင့်
ပြန်လည် run နိုင်ရန်နှင့် output တိုင်း တူညီရန် ဖြစ်သည်။

---

## ၁။ Project scope နှင့် deliverable

Project ၏ input သည် `{"doc_id": str, "raw_text": str}` ပုံစံ document စာရင်းဖြစ်ပြီး output သည်
**validated Knowledge Graph** ဖြစ်သည်။ "validated" ဆိုသည်မှာ triple တိုင်းသည် schema contract
(ခွင့်ပြုထားသော Node label၊ Relationship type၊ property) ကို ဖြေဆိုပြီး Quality Gate အားလုံးကို
ဖြတ်သန်းပြီးသား ဖြစ်သည်။

Deliverable ကို format သုံးမျိုးဖြင့် တစ်ပြိုင်နက် ထုတ်သည် —

| Deliverable | ရည်ရွယ်ချက် |
|---|---|
| Cypher `MERGE` statements | Neo4j သို့ parameterized၊ idempotent ဖြင့် စာရင်းသွင်းရန် |
| JSON triple list | အခြား service သို့ ပေးပို့ရန်၊ review လုပ်ရန် |
| CSV (`nodes.csv`, `relationships.csv`) | Neo4j Admin Import ဖြင့် bulk load ရန် |

Pipeline သည် **recall-oriented extraction** နှင့် **precision-oriented validation** ကို ခွဲခြားထားသည်။
Extractor ကို ကျယ်ကျယ် extract စေ၍ မှားယွင်းသည့် triple များကို gate အဆင့်တွင် ဖယ်ရှားသည်။
ဤဒီဇိုင်း၏ အကြောင်းရင်းမှာ extraction အဆင့်တွင် ဖယ်ရှားလွန်းပါက ပြန်လည် ရှာမတွေ့နိုင်တော့ဘဲ
gate တွင် ဖယ်ရှားပါက rejection reason ကို log ဖြင့် တိုင်းတာနိုင်ခြင်း ဖြစ်သည်။

```python
SAMPLE_CORPUS = [
    {"doc_id": "doc-001", "raw_text": "Neo4j  is a graph database.\nNeo4j uses Cypher as its query language. "
                                      "GraphRAG is built on a Knowledge Graph. Nous Research develops open models."},
    ...
]
# Expected output (exercise_1):
#   doc-001 | raw_chars=144 | normalized_chars=143
#   doc-002 | raw_chars=157 | normalized_chars=156
#   doc-003 | raw_chars=150 | normalized_chars=150
```

## ၂။ Pipeline အဆင့်ဆင့်

| အဆင့် | Input → Output | Failure mode | ကိုင်တွယ်ပုံ |
|---|---|---|---|
| ingest | corpus → `Document` list | encoding မမှန် | NFC normalize ဖြင့် ပြုပြင် |
| normalize | raw text → clean text | control char၊ double space | whitespace collapse၊ Unicode fold |
| chunk | document → `Chunk` list | sentence ပြတ်တောက် | sentence-aligned chunking + `chunk_id` |
| extract | chunk → raw triples | pattern မကိုက် | co-occurrence fallback (confidence နိမ့်) |
| resolve | surface form → canonical id | alias မသိ | gazetteer → alias → fuzzy fallback |
| merge | triples → unique triples | duplicate triple | key အလိုက် provenance union |
| validate | unique triples → accepted/rejected | self-loop၊ endpoint ပျောက် | Quality Gate |
| export | accepted → Cypher/JSON/CSV | literal injection | parameterized query သာ |

Chunking သည် **sentence-aligned** ဖြစ်သည် — sentence ကို ဖြတ်တောက်လျှင် Entity pair တစ်ခုလုံး
chunk နှစ်ခုအဖြစ် ကွဲသွားပြီး relationship ပြတ်တောက်သည်။ ထို့ကြောင့် `CHUNK_SIZE` (char) ကို
sentence boundary တွင်သာ ချိုးသည်။

```python
def normalize_text(raw):
    text = unicodedata.normalize("NFC", raw)
    for src, dst in UNICODE_FOLD.items():
        text = text.replace(src, dst)
    text = re.sub(r"[\r\n\t\f\v]+", " ", text)
    text = "".join(ch for ch in text if unicodedata.category(ch)[0] != "C")
    return re.sub(r"\s+", " ", text).strip()

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
# Expected output (exercise_2):
# chunk      : 6 chunks -> ['doc-001:c00', 'doc-001:c01', 'doc-002:c00',
#                           'doc-002:c01', 'doc-003:c00', 'doc-003:c01']
# extract    : 9 raw triples (scripted extractor)
```

Newline ကို ဖျက်မပစ်ဘဲ space အဖြစ် ပြောင်းသည်မှာ `database.\nNeo4j` ကဲ့သို့ စာလုံးနှစ်လုံး
ကပ်သွားခြင်းကို ကာကွယ်ရန် ဖြစ်သည် — ကပ်သွားပါက sentence splitting နှင့် token boundary နှစ်ခုလုံး
ပျက်ပြီး extraction recall ကျသည်။

## ၃။ Data model ဒီဇိုင်း

Data model ကို **code ထဲတွင် contract အဖြစ်** သတ်မှတ်သည် — extractor၊ gate နှင့် exporter
အားလုံး တူညီသော constant များကို ဖတ်သည်။ ဤနည်းဖြင့် schema ပြောင်းလဲမှုကို နေရာတစ်ခုတည်းတွင် ပြင်နိုင်သည်။

- **Node label** — `Document`၊ `Chunk`၊ `Entity`
- **Entity type (property)** — `Technology`၊ `Organization`၊ `Concept`
- **Relationship type** — `IS_A`၊ `USES`၊ `BUILT_ON`၊ `DEVELOPED_BY`၊ `INCLUDES`၊ `RELATED_TO`
- **Property (relationship)** — `confidence`၊ `chunk_ids`၊ `methods`၊ `rel_id`

Canonical id ကို entity အမည်မှ deterministic ဖြင့် ထုတ်သည် (`ent:` + slug)။ Idempotency အတွက်
id သည် run တိုင်း တူညီရမည် — hash ကို clock/random နှင့် မရောနှောရ။

```python
NODE_LABELS = ("Document", "Chunk", "Entity")
ALLOWED_ENTITY_TYPES = ("Technology", "Organization", "Concept")
ALLOWED_PREDICATES = ("IS_A", "USES", "BUILT_ON", "DEVELOPED_BY", "INCLUDES", "RELATED_TO")

def slug(text):
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")

def entity_id(canonical):
    return "ent:" + slug(canonical)
# Expected output (exercise_3):
#   ent:neo4j              Neo4j              Technology
#   ent:cypher             Cypher             Technology
#   ent:graphrag           GraphRAG           Technology
#   ent:knowledge-graph    Knowledge Graph    Concept
#   ent:entity-resolution  Entity Resolution  Concept
#   ent:llm                LLM                Technology
#   ent:transformer        Transformer        Technology
```

Neo4j ဘက်တွင် id ကို uniqueness constraint ဖြင့် ကာကွယ်ရမည် — constraint မရှိပါက `MERGE` သည်
duplicate node ဖန်တီးနိုင်သည် (concurrent write အောက်တွင် အထူးသဖြင့်)။

```cypher
CREATE CONSTRAINT entity_id_unique IF NOT EXISTS
FOR (n:Entity) REQUIRE n.id IS UNIQUE
```

## ၄။ Provenance tracking

Triple တိုင်းတွင် provenance record စာရင်းကို သိမ်းသည်။ Record တစ်ခုစီသည် —

- `chunk_id` — ထို triple ထွက်လာသည့် source `Chunk` (စာသားအထိ ပြန်လိုက်နိုင်)
- `confidence` — extraction ယုံကြည်စိတ်ချမှု (exact canonical = 0.95၊ alias = 0.80၊ fuzzy = 0.55၊ co-occurrence = 0.45)
- `method` — extraction နည်းလမ်း (`pattern:uses`၊ `pattern:built_on`၊ `cooccurrence`)

Triple ၏ confidence ကို provenance record များ၏ **အမြင့်ဆုံး** (max) ဖြင့် သတ်မှတ်သည်။
Merge အဆင့်တွင် key တူသည့် triple များ၏ provenance ကို union လုပ်သည် — ထို့ကြောင့် duplicate triple
တစ်ခုကို ဖျက်မပစ်ဘဲ **source အများအပြား၏ ထောက်ခံမှု** အဖြစ် ပြောင်းလဲသည်။

```python
def merge_triples(triples):
    merged = OrderedDict()
    for triple in triples:
        if triple.key in merged:
            merged[triple.key].provenance.extend(triple.provenance)
        else:
            merged[triple.key] = Triple(triple.subject_id, triple.predicate, triple.object_id,
                                        list(triple.provenance))
    return list(merged.values())

@property
def confidence(self):
    return max(p.confidence for p in self.provenance)
# Expected output (exercise_4):
#   GraphRAG -[BUILT_ON]-> Knowledge Graph conf=0.95 sources=['doc-001:c00', 'doc-002:c00']
#   LLM      -[IS_A]->     Transformer     conf=0.95 sources=['doc-003:c00']
```

Confidence ကို **max** ဖြင့် သတ်မှတ်သည်မှာ alias ဖြင့် extract လုပ်သည့် run နှင့် canonical ဖြင့်
extract လုပ်သည့် run နှစ်ခုတွင် ရလဒ် မကွဲပြားရန် ဖြစ်သည်။ သို့သော် source အရေအတွက်ကို ဦးစားပေးလိုပါက
`confidence = min(1.0, max_conf * (1 + 0.05 * (sources - 1)))` ကဲ့သို့ adjustment ထည့်နိုင်သည်။

## ၅။ Quality gates

Quality Gate သည် triple တစ်ခုကို အောက်ပါ order ဖြင့် စစ်သည်။ Order သည် အရေးကြီးသည် —
အရင်စစ်သည့် rule ၏ rejection reason သာ log တွင် ကျန်မည် ဖြစ်၍ structure ချို့ယွင်းမှုကို အရင်ဖမ်းသည်။

| Gate | စစ်သည့်အရာ | တားဆီးသည့် ပြဿနာ |
|---|---|---|
| 1 | endpoint ဗလာ/မရှိ | malformed extraction output |
| 2 | self-loop (`subject == object`) | pronoun/coreference မှားယွင်းမှု |
| 3 | predicate ခွင့်ပြုစာရင်းတွင် ပါ/မပါ | hallucinated Relationship type |
| 4 | endpoint သည် node set တွင် ရှိ/မရှိ | dangling reference |
| 5 | `confidence >= MIN_CONFIDENCE` (0.60) | အားနည်းသည့် co-occurrence triple |
| 6 | key ထပ်နေခြင်း | pipeline ပြန် run သည့်အခါ duplicate write |

```python
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
# Expected output (exercise_5):
# candidates : 13 (merged triples + 5 injected defects)
# accepted   : 5
# rejected   : {'duplicate': 1, 'low_confidence': 3, 'missing_endpoint': 1,
#               'self_loop': 2, 'unknown_predicate': 1}
```

`MIN_CONFIDENCE` ကို နိမ့်လွန်းသတ်မှတ်ပါက noise triple များ graph ထဲ ဝင်လာပြီး Retrieval အချိန်တွင်
LLM ကို လမ်းလွဲစေသည်။ မြင့်လွန်းသတ်မှတ်ပါက recall ကျသည်။ ထို့ကြောင့် threshold ကို **rejected
reason histogram** နှင့်အတူ တိုင်းတာပြီး ချိန်ရသည် — ဤ lab တွင် co-occurrence (0.45) ကို အလိုအလျောက်
ဖယ်ရှားပြီး alias-based triple (0.80) ကို ချန်ထားသည်။

## ၆။ Export format

**Cypher `MERGE` statements** ကို parameter အဖြစ်သာ ထုတ်သည်။ Query string ထဲတွင် literal မထည့်ရ —
အကြောင်းရင်းနှစ်ခုရှိသည်။ (က) Cypher injection ကို ကာကွယ်ခြင်း၊ (ခ) plan cache ကို ပြန်သုံးနိုင်ခြင်း။

```cypher
MERGE (n:Entity {id: $id})
SET n.name = $name, n.type = $type;

MATCH (a:Entity {id: $subject_id}), (b:Entity {id: $object_id})
MERGE (a)-[r:BUILT_ON {id: $rel_id}]->(b)
SET r.confidence = $confidence, r.chunk_ids = $chunk_ids, r.methods = $methods;
```

```json
{"chunk_ids": ["doc-001:c00", "doc-002:c00"], "confidence": 0.95,
 "methods": ["pattern:built_on"], "object_id": "ent:knowledge-graph",
 "rel_id": "rel:ent-graphrag-built-on-ent-knowledge-graph", "subject_id": "ent:graphrag"}
```

`MERGE` သည် constraint နှင့် တွဲသုံးမှသာ duplicate relationship ကို ကာကွယ်နိုင်သည်။ `CREATE`
ဖြင့် ရေးပါက pipeline ကို ပြန် run တိုင်း relationship အသစ် ထပ်တိုးသည် — ဤအချက်သည် Idempotency
လိုအပ်ချက်၏ အခြေခံဖြစ်သည်။

**JSON triple list** သည် node နှင့် relationship နှစ်ပိုင်း ပါပြီး relationship တိုင်းတွင် `subject_id`၊
`object_id`၊ `confidence` နှင့် `provenance` array ပါသည် — review tool နှင့် evaluation harness အတွက်
တိုက်ရိုက် အသုံးပြုနိုင်သည်။

**CSV** ကို Neo4j Admin Import header convention ဖြင့် ထုတ်သည် — `:ID`၊ `:START_ID`၊ `:END_ID`၊
`:TYPE`၊ `:LABEL`။

```csv
entity_id:ID,name,type,:LABEL
ent:neo4j,Neo4j,Technology,Entity
ent:knowledge-graph,Knowledge Graph,Concept,Entity

:START_ID,:END_ID,:TYPE,rel_id,confidence,chunk_ids
ent:graphrag,ent:knowledge-graph,BUILT_ON,rel:ent-graphrag-built-on-ent-knowledge-graph,0.95,doc-001:c00;doc-002:c00
```

Neo4j Admin Import သည် CSV ကို server offline ဖြစ်စဉ် load လုပ်သည် — import မလုပ်မီ `rel_id` နှင့်
`:START_ID`/`:END_ID` အားလုံး resolve ဖြစ်ကြောင်း စစ်ရမည်; မဖြစ်ပါက row ကို ကျော်ပြီး relationship
ပျောက်ဆုံးသည်။

## Production Considerations

- **Idempotency** — canonical id + `MERGE` ကြောင့် pipeline ကို ပြန် run နိုင်သည်; `chunk_ids` ကို
  append (set union) လုပ်ပြီး overwrite မလုပ်ရ။
- **Batch write** — statement တစ်ခုချင်း run လုပ်ခြင်းအစား `UNWIND $rows AS row` ဖြင့် batch
  တစ်ခုလျှင် 1,000–10,000 row ပို့ခြင်းသည် round trip ကို သိသိသာသာ လျှော့ချသည်။
- **Incremental update** — document အသစ် တိုးလာသည့်အခါ doc_id အလိုက် chunk ကို ပြန်ထုတ်ပြီး
  ထို chunk မှ ထွက်သည့် provenance record ကို အရင်ဖျက်ကာ အသစ်ထည့်သည် (delete-then-insert)။
- **Monitoring** — rejected reason histogram၊ confidence distribution၊ chunk တစ်ခုလျှင် triple အရေအတွက်
  သုံးခုကို metric အဖြစ် မှတ်သည်။
- **Cost** — LLM extraction ကို အစားထိုးထားသည့် scripted extractor သည် token cost သုည ဖြစ်သော်လည်း
  real-world တွင် chunk အရေအတွက်သည် token cost ကို တိုက်ရိုက် သတ်မှတ်သည်။
- **Security** — Cypher ကို parameter ဖြင့်သာ ရေးရမည်။ `apoc.periodic.iterate` ကဲ့သို့ bulk procedure
  သုံးပါက caller ၏ permission ကို ကန့်သတ်ရမည်။

## Summary Checklist

- [ ] Pipeline အဆင့် ၈ ခုလုံး တစ်ခုချင်း function အဖြစ် ခွဲထားပြီး output အဆင့်ဆင့် စစ်နိုင်သည်
- [ ] Node label၊ Entity type၊ predicate အားလုံး ခွင့်ပြုစာရင်းထဲတွင်သာ ရှိသည်
- [ ] Triple တိုင်းတွင် `chunk_id`၊ `confidence`၊ `method` ပါသည်
- [ ] Duplicate triple ကို ဖျက်မပစ်ဘဲ provenance union ဖြင့် merge လုပ်သည်
- [ ] Quality Gate ၏ rejection reason များကို histogram ဖြင့် ကြည့်နိုင်သည်
- [ ] Cypher ထုတ်လုပ်မှုတွင် literal မပါဘဲ parameter သာ ပါသည်
- [ ] `python3 modules/04_project_create_knowledge_graph/lab.py` → exit 0
