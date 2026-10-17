# M04 — လေ့ကျင့်ခန်းများ (Exercise)

အောက်ပါ လေ့ကျင့်ခန်း ၆ ခုကို `lab.py` ထဲတွင် အဆင့်ဆင့် implement လုပ်ပါ။ Exercise တိုင်းတွင်
`assert` ဖြင့် စစ်ဆေးပြီး အောင်မြင်ပါက `True` return ပြန်ရမည်။ Reference implementation ကို
`solution.md` တွင် ဖော်ပြထားသည်။ Standard library သာ သုံးရမည် — `random`၊ network call၊ external
package မသုံးရ။

## Exercise 1 — Corpus Normalization

Document များကို Pipeline အဆင့်အားလုံး မှီခိုနိုင်သည့် clean text အဖြစ် ပြောင်းပါ — Unicode NFC၊
smart quote/dash fold၊ control character ဖယ်ရှားခြင်း (newline ကို space အဖြစ် ပြောင်းရမည်)၊
whitespace collapse နှင့် strip။

**Hints:** `unicodedata.normalize("NFC", text)` ဖြင့် စပါ။ `unicodedata.category(ch)[0] == "C"` ဖြစ်သည့် character များကို
ဖယ်ပါ။ `re.sub(r"[\r\n\t\f\v]+", " ", text)` ကို control char ဖယ်မီ run ပါ။

**Expected behavior:** `'  Neo4j\u00a0 is  a graph\u2013database.\n\n  \u201cGraphRAG\u201d  \u2026  '` →
`'Neo4j is a graph-database. "GraphRAG" ...'`။ doc-001 ၏ normalized length သည် raw length ထက် ၁ လုံး လျော့သည်။

## Exercise 2 — End-to-End Pipeline Run

`run_pipeline(corpus)` တည်ဆောက်ပြီး အဆင့် ၈ ခုလုံး ချိတ်ဆက်ပါ — ingest → normalize → chunk →
extract → resolve → merge → quality gate → export။ အဆင့်တိုင်း၏ အရေအတွက်ကို print ပြပါ။

**Hints:** Chunk id ပုံစံ — `f"{doc_id}:c{ordinal:02d}"`။ Pattern မကိုက်သည့် sentence အတွက်
co-occurrence fallback (`RELATED_TO`, 0.45) ထည့်ပါ။ `resolve_surface()` သည် `(entry, confidence,
kind)` ပြန်ရမည်; `kind` သည် `canonical`၊ `alias`၊ `fuzzy`၊ `unresolved`။

**Expected behavior:** corpus ၃ → chunks ၆ → raw triples ၉ → entities ၇ → merged ၈ → accepted ၅ /
rejected ၃။ `'Graph Rag'` → `GraphRAG` (conf=0.80, kind=alias); `'Knowledg Graph'` →
`Knowledge Graph` (conf=0.55, kind=fuzzy)။

## Exercise 3 — Data Model Validation

Graph ကို Neo4j သို့ မပို့မီ schema contract စစ်ပါ — Node label၊ Entity type၊ predicate နှင့် id ပုံစံ။

**Hints:** `NODE_LABELS`၊ `ALLOWED_ENTITY_TYPES`၊ `ALLOWED_PREDICATES` ကို constant အဖြစ် သတ်မှတ်ပါ။
`entity_id(name) == slug(name)` ဖြစ်ကြောင်း စစ်ပါ။ Type နှင့် predicate အတွက် histogram ထုတ်ပါ။

**Expected behavior:** entity type histogram — `{'Concept': 2, 'Technology': 5}`။ predicate histogram —
`{'BUILT_ON': 2, 'IS_A': 1, 'USES': 2}`။ Accepted triple တိုင်း၏ endpoint သည် entity set ထဲတွင် ရှိပြီး
`subject != object` ဖြစ်သည်။

## Exercise 4 — Provenance Metadata

Triple တိုင်းတွင် `chunk_id`၊ `confidence`၊ `method` ပါသည့် provenance record ရှိကြောင်း စစ်ပြီး
duplicate triple ၏ provenance ကို union လုပ်ပါ။

**Hints:** `Provenance` ကို dataclass (`chunk_id`, `confidence`, `method`) အဖြစ် သတ်မှတ်ပါ။
`Triple.confidence` ကို provenance confidence များ၏ `max()` အဖြစ် သတ်မှတ်ပါ။ Merge တွင် key တူပါက
`extend()` လုပ်ပါ — overwrite မလုပ်ရ။

**Expected behavior:** `GraphRAG -[BUILT_ON]-> Knowledge Graph` တွင် provenance record ၂ ခု (`doc-001:c00`,
`doc-002:c00`) ရှိသည်။ Accepted triple ၏ method — `{'pattern:built_on', 'pattern:is_a', 'pattern:uses'}`။

## Exercise 5 — Quality Gate Filtering

Gate ၆ ခုကို order အလိုက် စစ်ပါ — missing endpoint → self-loop → unknown predicate → dangling
endpoint → low confidence → duplicate။ Rejection reason တိုင်းကို log လုပ်ပါ။

**Hints:** Reason များကို `(triple, reason)` tuple အဖြစ် ပြန်ပါ။ Order အရေးကြီးသည် — `elif` ကို
အစဉ်လိုက် စီပါ။ Test set အတွက် defect ၅ မျိုး (empty endpoint၊ self-loop၊ `FRIENDS_WITH`၊ 0.30
confidence၊ duplicate) ကို ကိုယ်တိုင် ထည့်ပါ။

**Expected behavior:** candidate ၁၃ → accepted ၅ / rejected ၈။ Reason histogram —
`{'duplicate': 1, 'low_confidence': 3, 'missing_endpoint': 1, 'self_loop': 2, 'unknown_predicate': 1}`။

## Exercise 6 — Cypher / JSON / CSV Export

Accepted graph ကို format သုံးမျိုးဖြင့် export လုပ်ပါ။ Cypher သည် parameter သာ သုံးရမည်။

**Hints:** Node statement — `MERGE (n:Entity {id: $id}) SET n.name = $name, n.type = $type`။ Relationship
statement — `MATCH ... MERGE (a)-[r:<TYPE> {id: $rel_id}]->(b) SET ...`။ `rel_id` ကို
subject/predicate/object မှ deterministic ဖြင့် ထုတ်ပါ။ CSV header ကို Neo4j Admin Import convention
(`:ID`၊ `:START_ID`၊ `:END_ID`၊ `:TYPE`၊ `:LABEL`) သုံးပါ။ JSON ကို `sort_keys=True` ဖြင့် ထုတ်ပြီး round-trip စစ်ပါ။

**Expected behavior:** Cypher statement ၁၂ ခု (node ၇ + rel ၅)၊ statement တိုင်းတွင် `$` ပါပြီး `'` မပါ။
JSON — nodes ၇၊ relationships ၅; CSV — row ၇ နှင့် ၅။ CSV relationship တိုင်း၏ `:START_ID`/`:END_ID`
သည် node CSV ထဲတွင် ရှိသည်။
