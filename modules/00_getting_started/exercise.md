# M00 — Exercise: Getting Started

လေ့ကျင့်ခန်း ၆ ခုသည် `explanation.md` ၏ သဘောတရားများကို run နိုင်သော code အဖြစ် ပြောင်းစေသည်။
Exercise တိုင်းကို `modules/00_getting_started/lab.py` ထဲတွင် implement လုပ်ပြီး
`python3 modules/00_getting_started/lab.py` ဖြင့် စစ်ဆေးပါ။ `solution.md` ကို ကိုယ်တိုင် မရေးမီ မဖတ်ရန်။

## Exercise 1 — RAG Pipeline Stage Ordering

Stage စာရင်း (ရောနှောထားသည်) နှင့် dependency map ကို input အဖြစ် ယူပြီး
`ingest → chunk → embed → index → retrieve → generate` အစီအစဉ်ကို တွက်ထုတ်ပါ။

**Hints:** Topological sort ကို ကိုယ်တိုင် ရေးပါ — dependency အားလုံး ပြည့်သော stage များထဲမှ
တစ်ခုကို ရွေးထုတ်သည်။ Tie-break အတွက် `sorted()` သုံးပါက output သည် deterministic ဖြစ်သည်။
Cycle ရှိပါက `assert` ဖြင့် ကျရှုံးစေပါ။

**Expected behavior:** Order သည် `['ingest', 'chunk', 'embed', 'index', 'retrieve', 'generate']` ဖြစ်ရမည်။
Stage တိုင်းအတွက် dependency တိုင်းသည် ၎င်းအရှေ့တွင် ရှိကြောင်း စစ်ရမည်။

## Exercise 2 — Cosine Similarity Ranking

Query vector `[0.90, 0.10, 0.00, 0.20]` နှင့် chunk vector ၄ ခုအတွက် cosine similarity ကို
တွက်ပြီး score အမြင့်ဆုံးမှ အနိမ့်ဆုံးသို့ စီပါ။

**Hints:** `math.sqrt` သာ သုံးပါ။ Zero vector (norm = 0) အတွက် similarity ကို `0.0` ပြန်ပါ။
`key=lambda item: (-score, chunk_id)` ဖြင့် စီပါက score တူပါက အမည်အလိုက် တည်ငြိမ်သည်။

**Expected behavior:** Ranking အတိအကျ — `chunk-01 (0.991173)`, `chunk-04 (0.767112)`, `chunk-02 (0.202864)`,
`chunk-03 (0.084898)`။ Vector တူညီခြင်း၏ similarity သည် `1.0`၊ orthogonal vector များအတွက် `0.0`။

## Exercise 3 — Retrieval Modality Selection

Query feature dict တစ်ခုကို ယူပြီး retrieval modality ရွေးပေးသော function ရေးပါ။
Feature များ — `hop_count`, `spans_documents`, `needs_corpus_wide_summary`, `needs_structured_filter`။

**Hints:** Rule စဉ်လိုက်မှုသည် အရေးကြီးသည် — ကျဉ်းသော (specific) rule ကို အရင်စစ်ပါ။
`hop_count >= 2` နှင့် `spans_documents` နှစ်ခုလုံး မှန်မှ entity-anchored subgraph retrieval ဖြစ်သည်။
ရိုးရှင်းသော case အားလုံးကို `Vector Search - plain RAG` သို့ ပြန်ပါ။

**Expected behavior:** Q1 → `Vector Search - plain RAG`၊ Q2 → `GraphRAG - entity-anchored subgraph retrieval`၊
Q3 → `GraphRAG - community summary retrieval`၊ Q4 → `Text-to-Cypher`။

## Exercise 4 — RAG Failure Mode Classification

Scenario ၅ ခုကို failure mode သို့ map လုပ်သော classifier ရေးပါ။ Label များ —
`ingestion_gap`, `global_summarization_failure`, `multi_hop_failure`, `chunk_isolation`, `no_failure`။

**Hints:** Rule ကို tuple list အဖြစ် ရေးပြီး စဉ်လိုက် စစ်ပါ (`(label, predicate)`)။
`ingestion_gap` သည် အခြား label အားလုံးကို ကျော်လွှားသည် — entity သည် Index ထဲ မရှိပါက
အခြား ဘယ် technique မျှ ဖြေနိုင်မည် မဟုတ်။

**Expected behavior:** S1 → `no_failure`၊ S2 → `ingestion_gap`၊ S3 → `multi_hop_failure`၊
S4 → `global_summarization_failure`၊ S5 → `chunk_isolation`။ Label ၅ ခုလုံး တစ်ကြိမ်စီ ပေါ်ရမည်။

## Exercise 5 — Triple (SPO) Parsing

`subject|predicate|object|source_chunk` format လိုင်းများကို parse လုပ်ပြီး မမှန်သော လိုင်းများကို
ခွဲထုတ်ပါ။ Predicate ကို စာလုံးအသေးသို့ ပြောင်းပြီး space များကို `_` ဖြင့် အစားထိုးပါ။
Input တွင် whitespace မတူညီသော duplicate လိုင်း၊ field မပြည့်သော လိုင်း၊ subject ဟင်းလင်းသော လိုင်း ပါဝင်သည်။

**Hints:** `re.compile(r"^(?P<s>[^|]+)\|(?P<p>[^|]+)\|(?P<o>[^|]+)\|(?P<c>[^|]+)$")` ဖြင့် field ၄ ခု
တိတိကျကျ စစ်ပါ။ `re.sub(r"\s+", " ", text).strip()` ဖြင့် normalize လုပ်ပါက
`" Acme Corp "` နှင့် `"Acme Corp"` သည် triple တူညီသည် ဖြစ်လာသည်။ `frozen=True` dataclass ဖြင့်
triple ကို hashable ဖြစ်စေပါက `set()` ဖြင့် dedupe လုပ်နိုင်သည်။

**Expected behavior:** Triple ၄ ခု ထုတ်ရမည်၊ လိုင်း ၂ ခု reject ဖြစ်ရမည်၊ unique triple ၃ ခု၊
duplicate ၁ ခု။ `(Acme Corp)-[founded_in]->(Cupertino)` သည် `source_chunk = "chunk-01"` ဖြစ်ရမည်။

## Exercise 6 — GraphRAG Readiness Check

Corpus metric profile ကို ယူပြီး `READY` / `NOT_READY` verdict နှင့် မအောင်မြင်သော check စာရင်း
ပြန်ပေးသော function ရေးပါ။ Threshold များ — `entity_coverage >= 0.85`၊
`relationship_density >= 1.50`၊ `duplicate_entity_rate <= 0.05`၊ `avg_chunk_tokens <= 512.0`၊
boolean flag များ — `uniqueness_constraint`, `fulltext_index`, `community_summary`။

**Hints:** Numeric check နှင့် boolean check ကို tuple နှစ်ခုအဖြစ် ခွဲထားခြင်းသည် threshold အသစ်
ထည့်ရာတွင် လွယ်သည်။ `failed` list ကို check စဉ်လိုက် (declaration order) ထိန်းပါ။

**Expected behavior:** `READY_PROFILE` → verdict `READY`၊ `failed = []`။ `BLOCKED_PROFILE` → verdict
`NOT_READY`၊ `failed` သည် check ၆ ခုလုံး (`entity_coverage`, `relationship_density`, `duplicate_entity_rate`,
`avg_chunk_tokens`, `fulltext_index`, `community_summary`) အစဉ်လိုက် ဖြစ်ရမည်။
