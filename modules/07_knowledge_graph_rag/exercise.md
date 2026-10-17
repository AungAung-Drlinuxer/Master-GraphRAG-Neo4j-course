# M07 — လေ့ကျင့်ခန်း ၆ ခု

`lab.py` တွင် `exercise_1()` … `exercise_6()` ကို ဖြည့်စွက်ရမည်။ Fixture (NODES, EDGES, CHUNKS, ADJ)
ကို ပြောင်းလဲခွင့် မရှိပါ။ External package နှင့် `random` ကို မသုံးရပါ။

---

## Exercise 1 — Entity Linking

Query text မှ graph node သို့ anchor များကို ရှာပါ။ Node တိုင်း၏ `name` နှင့် `aliases` ကို
normalize လုပ်ပြီး score တွက်ရမည်။ Score ≥ 0.7 ဖြစ်သော node များကိုသာ ပြန်ပေးရမည်။
Result ကို `(-score, node_id)` ဖြင့် sort ရမည်။

**Hints:**
- Query ကို NFKD normalize → ASCII fold → casefold လုပ်ပြီး `[a-z0-9]+` ဖြင့် tokenize ပါ
- Surface သည် query ထဲ တိုက်ရိုက် substring ဖြစ်ပါက score = 1.0 ကို ဦးစားပေးပါ
- မဟုတ်ပါက token overlap ratio နှင့် `difflib.SequenceMatcher` ratio ကို ပေါင်းစပ်ပါ
- Threshold 0.7 သည် partial match (ဥပမာ "Neo4j Engineering") ကို ဖယ်ရှားရန် လုံလောက်သည်

**Expected behavior:** Query ၃ ခုအတွက် anchor list ကို print လုပ်သည်။ Query ၁ အတွက်
`["co:neo4j", "prod:aura", "tech:vectorindex"]`၊ query ၂ နှင့် ၃ အတွက် `["tech:louvain"]` သာ
ရရမည်။ `org:cnrs` နှင့် `person:eifrem` သည် ထို query များတွင် anchor အဖြစ် မပါရ။

---

## Exercise 2 — k-hop Subgraph Retrieval

Anchor node မှ စ၍ BFS ဖြင့် `k` hop အထိ expand လုပ်ပါ။ ရလဒ်သည် (node id စာရင်း, edge index
စာရင်း) ဖြစ်ရမည်။ Edge သည် ရောက်ရှိပြီးသား node နှစ်ခုလုံး ပါဝင်ပါက ထည့်ရမည်။

**Hints:**
- `deque` ကို frontier အဖြစ် သုံးပြီး hop တစ်ခုစီကို level အလိုက် ပြီးဆုံးအောင် လုပ်ပါ
- Neighbor များကို `sorted()` ဖြင့် လှမ်းပါ — မဟုတ်ပါက ရလဒ် အစီအစဉ် ပြောင်းလဲနိုင်သည်
- `k` တိုးလျှင် ရလဒ် မတိုးတော့သည့်အခါ expansion ရပ်ပါ
- Disjoint component သည် ဘယ် `k` တွင်မှ မပါဝင်ရ

**Expected behavior:** `k = 1, 2, 3` အတွက် node/edge အရေအတွက် print လုပ်သည်။ `k = 1` တွင်
node ၅ ခု၊ edge ၇ ခု၊ `k = 2` တွင် node ၆ ခု၊ edge ၈ ခု ရပြီး `k = 3` သည် `k = 2` နှင့် တူရမည်။
`person:eifrem` နှင့် `tech:louvain` သည် ရလဒ်တွင် လုံးဝ မပါရ။

---

## Exercise 3 — Subgraph → Prompt Context Serialization

Exercise 2 မှ subgraph ကို LLM prompt context အဖြစ် serialize လုပ်ပါ။ Entity line များသည်
node id အစီအစဉ်အတိုင်း၊ relation line များသည် `(src, rel, dst)` အစီအစဉ်အတိုင်း ဖြစ်ရမည်။
Entity line သည် `[ENTITY]` ဖြင့်၊ relation line သည် `[RELATION]` ဖြင့် စရမည်။

**Hints:**
- Format ကို တိကျစွာ သတ်မှတ်ပါ — `[ENTITY] id=… | label=… | name=… | summary=…`
- Relation ကို `src -[REL]-> dst` ပုံစံဖြင့် ရေးပါ (Cypher pattern နှင့် တူညီအောင်)
- `itertools.groupby` ကို အသုံးပြုလျှင် list ကို ကြိုတင် `sorted()` လုပ်ရမည်
- Token ခန့်မှန်းချက်ကို `len(text) // 4` ဖြင့် တွက်ပြီး `max_tokens` ကျော်ပါက ဖြတ်ပါ

**Expected behavior:** Entity line ၆ ခု၊ relation line ၈ ခု ရမည်။ Line ပထမဆုံးသည် `[ENTITY]` ဖြင့်
စရမည်။ `[RELATION] co:neo4j -[DEVELOPS]-> prod:aura` ပါရမည်။ Context တစ်ခုလုံးသည်
token ခန့်မှန်းချက် ~256 tokens ဖြစ်သည်။

---

## Exercise 4 — Hybrid Retrieval Fusion

Vector ranking နှင့် graph ranking ကို Reciprocal Rank Fusion (k = 60) ဖြင့် ပေါင်းပါ။ ထို့နောက်
source chunk တူညီသော item များကို deduplicate လုပ်ပါ။ Score တူညီပါက graph triple ကို ဦးစားပေးပါ။

**Hints:**
- `score(item) = Σ 1 / (k + rank)` ဖြင့် တွက်ပါ၊ rank သည် 1 မှ စသည်
- Sort ကို `(-score, item_id)` ဖြင့် လုပ်ပါ — tie-break မရှိပါက output မတည်ငြိမ်နိုင်သည်
- `vec:cN` ၏ provenance chunk သည် `cN` ဖြစ်သည်၊ `graph:i` ၏ provenance သည် `EDGES[i][3]` ဖြစ်သည်
- Dedup လုပ်ပြီးနောက် item တစ်ခုစီသည် chunk တစ်ခုစီကို ကိုယ်စားပြုရမည်

**Expected behavior:** Fused list သည် `graph:0, vec:c1, graph:4, vec:c4, graph:6, vec:c2` ဖြစ်ပြီး
final list သည် `graph:0, graph:4, vec:c4, graph:6` ဖြစ်သည်။ `vec:c1` နှင့် `vec:c2` သည်
collision ကြောင့် ဖယ်ရှားခံရသည် (item ၂ ခု လျော့သည်)။

---

## Exercise 5 — Text-to-Cypher Guardrail Validation

LLM generate လုပ်သော Cypher ကို execute မလုပ်မီ စစ်ဆေးသော validator တစ်ခု တည်ဆောက်ပါ။
(က) မည်သည့် destructive clause ကိုမျှ ခွင့်မပြုရ (b) query သည် read-only clause ဖြင့် စရမည်
(ဂ) `RETURN` မဖြစ်မနေ ပါရမည် (ဃ) label များသည် schema allowlist အတွင်း ဖြစ်ရမည် (င) statement
တစ်ခုတည်းသာ ခွင့်ပြုရမည်။

**Hints:**
- Comment (`//`, `/* */`) နှင့် string literal ကို ကြိုတင် ဖယ်ရှားပါ — ထို content သည် mutate မလုပ်နိုင်ပါ
- Keyword ကို word boundary ဖြင့် စစ်ပါ၊ substring ဖြင့် စစ်ပါက column name များကို မှားစစ်နိုင်သည်
- `;` သည် အဆုံးတွင်သာ ခွင့်ပြုရမည်၊ ထို့ပြင် `;` ရှိပါက multiple statement ဟု reject ရမည်
- Label များကို `[DEVELOPS]` ကဲ့သို့ relationship type နှင့် မရောပါနှင့် — relationship bracket ကို
  ကြိုတင် ဖယ်ရှားပြီးမှ node label ကို ထုတ်ပါ

**Expected behavior:** Candidate ၉ ခုအနက် ၆ ခု သည် reject ခံရသည်။ `DETACH DELETE`, `DROP`, `SET`,
`CREATE`, multiple statement, unknown label (`Secret`) များ ပါဝင်သည်။ Parameterized read-only
query ၂ ခုနှင့် trailing `//` comment ပါသော query သည် accept ခံရသည်။

---

## Exercise 6 — Community Detection

Graph ကို hierarchy ၃ ဆင့်အဖြစ် partition လုပ်ပါ — level 0 (singleton)၊ level 1 (connected
component)၊ level 2 (modularity refinement)။ ဆင့်တိုင်းအတွက် Newman modularity `Q` ကို တွက်ပြီး
community summary များကို ထုတ်ပါ။

**Hints:**
- `Q = Σ_c [ L_c/m − (k_c/2m)² ]` — `L_c` သည် community အတွင်းရှိ edge အရေအတွက်၊ `k_c` သည် degree ပေါင်း
- Refinement သည် node တစ်ခုကို အိမ်နီးချင်း community သို့ ရွှေ့ကြည့်ပြီး `Q` တက်သော ရွှေ့မှုကိုသာ လက်ခံရမည်
- Node iterating ကို `sorted()` ဖြင့် လုပ်ပါ — deterministic ဖြစ်ရမည်
- Community label များကို ပထမ ပေါ်ပေါက်သည့် node အစီအစဉ်အတိုင်း 0, 1, … သို့ canonicalize လုပ်ပါ

**Expected behavior:** Level 1 တွင် community ၂ ခု၊ `Q = 0.4444444444` (4/9) ရမည်။ Community 0 တွင်
Neo4j/AuraDB/Cypher/GraphRAG/Vector Index/Neo4j Engineering၊ community 1 တွင် CNRS/Louvain/Blondel/
paper ပါဝင်သည်။ Level 2 ၏ `Q` သည် level 1 ထက် လျော့ရ မည် မဟုတ်ပါ။

---

## Run လုပ်ပုံ

```bash
python3 modules/07_knowledge_graph_rag/lab.py
```

အောင်မြင်ပါက နောက်ဆုံးလိုင်းတွင် `[PASS] All 6/6 exercises passed successfully.` ပေါ်ပြီး
exit code သည် `0` ဖြစ်ရမည်။
