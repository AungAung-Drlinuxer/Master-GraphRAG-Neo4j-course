# M08 — Conclusion — လေ့ကျင့်ခန်းများ

Exercise တိုင်းကို `lab.py` အတွင်းတွင် `exercise_N()` function အဖြစ် ရေးပြီး run ရမည်။
Python standard library သာ သုံးရမည်၊ `random` နှင့် network access မသုံးရ။

---

## Exercise 1 — Full pipeline recap (stage ordering)

M00–M07 ၏ stage များကို prerequisite စာရင်းဖြင့် ဖော်ပြပြီး၊ dependency အားလုံး ပြီးသွားသော stage
ကို အရင်ရွေးသည့် topological order ကို ထုတ်ပေးသည့် function ရေးပါ။ Order တွင် prerequisite
တိုင်းသည် dependent stage အရင် နေရာရကြောင်း စစ်ဆေးပါ။

**Hints:** Stage list ကို `OrderedDict` ဖြင့် ထားပါ။ Loop တစ်ခုအတွင်း ရွေးနိုင်သော stage မရှိတော့ပါက
cycle ရှိသည်ဟု ယူဆ၍ exception ပစ်ပါ။ `position = {name: i for i, name in enumerate(order)}`
ဖြင့် `position[dep] < position[name]` ကို assert လုပ်ပါ။

**Expected behavior:** Order သည် `ingest` မှ စပြီး `generate` ဖြင့် ဆုံးသည်။ Module map သည်
M00–M08 အတိအကျ ကိုးခု ရှိပြီး M04 သည် project module ဖြစ်ကြောင်း ဖော်ပြသည်။

---

## Exercise 2 — Cost / latency model

Ingestion Cost နှင့် Latency ကို formula ဖြင့် တွက်သည့် `cost_latency_model()` ရေးပါ။ ထို့နောက်
corpus size နှစ်ဆ ဖြစ်ပါက Cost နှစ်ဆ ဖြစ်ကြောင်း၊ parallel worker တိုးပါက parallel latency
ကျကြောင်း စစ်ဆေးပါ။ Query-side latency ကို `retrieval_latency_ms()` ဖြင့် သီးခြား တွက်ပါ။

**Hints:** `CHARS_PER_TOKEN = 4.0` ကို constant အဖြစ် သုံးပါ။ `math.ceil` ဖြင့် chunk count ကို
ကိန်းပြည့်ဖြစ်စေပါ။ Parallel latency ကို `math.ceil(chunks / workers) * per_chunk_seconds` ဖြင့်
တွက်ပါ။

**Expected behavior:** 48000 chars၊ `chunk_chars=2000` ဖြင့် chunk 24 ခု၊ Cost `$18.24`၊
sequential latency `211.600 s`၊ worker 4 ဖြင့် `52.900 s` ထွက်သည်။ Query traversal သည် millisecond
scale ဖြစ်ပြီး generation က လွှမ်းမိုးသည်။

---

## Exercise 3 — Build-vs-buy decision scorer

Criteria ငါးခုအတွက် weight သတ်မှတ်ပြီး၊ "build in-house" နှင့် "managed service (buy)" အတွက်
score များ ပေး၍ weighted total ကို နှိုင်းယှဉ်ပါ။ Weight ပြောင်းလိုက်ပါက ဆုံးဖြတ်ချက်
ပြောင်းနိုင်ကြောင်း သက်သေပြပါ။

**Hints:** Weight များ၏ ပေါင်းလဒ်သည် 1.0 ဖြစ်ကြောင်း `assert` ဖြင့် စစ်ပါ။ Score ကို 0–5 scale
ဖြင့် ထားပါ။ ဆုံးဖြတ်ချက်ကို `"build" if score_build > score_buy else "buy"` ဖြင့် ပြန်ပါ။

**Expected behavior:** Default weight (`time_to_first_value=0.25`) ဖြင့် build `3.450` > buy `3.350`
ဖြစ်၍ build ရွေးသည်။ `time_to_first_value` ကို `0.40` သို့ တင်ပါက buy `3.800` > build `3.050`
ဖြစ်၍ buy ရွေးသည်။

---

## Exercise 4 — Incremental update planner

Document အသစ်တစ်ခုမှ Triple များကို ရှိပြီးသား graph နှင့် နှိုင်းယှဉ်၍ operation list
(`ADD_NODE`၊ `ADD_EDGE`၊ `DELETE_EDGE`၊ `NOOP`) ထုတ်ပေးသည့် planner ရေးပါ။ Single-valued
Relationship တွင် အဟောင်း Relationship ကို ဖယ်ရှားပါ။ Document ကို နှစ်ခါ ingest လုပ်ပါက
graph content hash မပြောင်းကြောင်း စစ်ဆေးပါ။

**Hints:** `SINGLE_VALUED = {"LEADS", "MANAGES"}` ကဲ့သို့ set သတ်မှတ်ပါ။ Hash အတွက်
`hashlib.sha256` ကို `json.dumps(..., sort_keys=True)` နှင့် တွဲသုံးပါ — key order မတည်ငြိမ်ခြင်းက
hash ကို ပြောင်းစေနိုင်သည်။

**Expected behavior:** `("Dave", "LEADS", "Payments Squad")` ထည့်ပါက `ADD_NODE Dave`၊
`DELETE_EDGE Carol LEADS Payments Squad`၊ `ADD_EDGE Dave LEADS Payments Squad` ထွက်သည်။
ဒုတိယအကြိမ်တွင် `NOOP` သာ ထွက်ပြီး signature မပြောင်း။

---

## Exercise 5 — Production architecture checklist

Production architecture တစ်ခုအတွက် control များကို critical / advisory ဟူ၍ ခွဲပြီး audit လုပ်သည့်
function ရေးပါ။ Critical control တစ်ခု လွဲပါက total score မည်မျှပင် မြင့်စေကာမူ design သည်
မအောင်မြင်ရ။

**Hints:** Checklist ကို `(name, satisfied, critical)` tuple list အဖြစ် ထားပါ။
`critical_failures = [name for name, ok, critical in checklist if critical and not ok]` ဖြင့်
ရှာပါ။ `passes` ကို `not critical_failures` အဖြစ် သတ်မှတ်ပါ။

**Expected behavior:** Checklist တစ်ခုလုံး ပြည့်စုံပါက score `7/7`၊ critical failure သုည၊
`passes=True` ဖြစ်သည်။ `read_only_cypher_guardrail` ဖယ်လိုက်ပါက score မြင့်နေသော်လည်း
`passes=False` ဖြစ်သည်။

---

## Exercise 6 — End-to-end mini GraphRAG integration test

M03–M07 ကို ချိတ်ဆက်သည့် mini pipeline တစ်ခုလုံးကို run ပါ — sentence-aware chunking →
scripted deterministic extraction → entity resolution → in-memory graph → entity linking →
k-hop subgraph retrieval → prompt context serialization → rule-based generator။

**Hints:** Corpus အသေးစားကို list အဖြစ် ထားပါ။ Relation များကို `re.compile` pattern list ဖြင့်
ဖော်ပါ။ Chunk တိုင်းမှ Triple ထုတ်ပြီး `(subject, relation, object)` key ဖြင့် dedupe လုပ်ပါ၊
သို့သော် `chunks` provenance list ကို သိမ်းထားပါ။ Retrieval တွင် directed edge ကို undirected
neighbor အဖြစ် ဖြန့်ကြည့်ပြီး hop အရေအတွက်ဖြင့် ကန့်သတ်ပါ။ Generator တွင် question ၏
verb keyword မှ relation ကို map လုပ်ပြီး၊ anchor ကို object အဖြစ် ရှိသော edge ၏ subject ကို
အဖြေအဖြစ် ပြန်ပါ။

**Expected behavior:** Sentence 5 ခုမှ chunk 4 ခု (overlap sentence 1 ခု) ထွက်သည်။ Raw triple 8 ခု
မှ 5 ခု ကျန်သည် (overlap ကြောင့် ထပ်နေသော triple များ ပေါင်းသွားသည်)။ Graph တွင် node 6 ခု၊
edge 5 ခု ရှိသည်။ "Who leads the Payments Squad?" → anchor `Payments Squad`၊ 1-hop subgraph တွင်
node 4 ခု၊ edge 3 ခု (Audit Store ပါဝင်သည် မဟုတ်)၊ generator အဖြေ `Carol`။
"Who builds the Ledger service?" → အဖြေ `Payments Squad`။
