# M06 — Exercises

`lab.py` ထဲတွင် function ၆ ခုကို implement လုပ်ပြီး `python3 modules/06_storing_entities_relationships_neo4j/lab.py`
ဖြင့် run စစ်ရမည်။ Neo4j server မလိုအပ်၊ external package မသုံးရ၊ `random` မသုံးရ။ Input triple ၆ ခု
(deterministic sample) ကို အခြေခံရမည် — `t1` နှင့် `t6` သည် head/tail/type တူပြီး `chunk_id` ကွာသဖြင့်
relationship ၂ ခု သီးသန့် ဖြစ်ရမည်။

## Exercise 1 — Triple → Cypher batch generator (`UNWIND`)

**လုပ်ငန်း:** Triple များကို `(head label, relationship type, tail label)` အလိုက် group ဖွဲ့ပြီး group တိုင်းအတွက်
`UNWIND $rows AS row` batch statement တစ်ခုနှင့် `$rows` payload ကို ထုတ်ပေးပါ။ Node အတွက်
`MERGE (h:<Label> {id: row.head_id})`၊ relationship အတွက် `MERGE (h)-[r:<TYPE> {chunk_id: row.chunk_id}]->(t)`၊
`ON CREATE SET` နှင့် `ON MATCH SET` နှစ်မျိုးလုံး ပါရမည်။ Label/type ကို allowlist mapping မှသာ ယူရမည်။

**Hints:** group အစီအစဉ် deterministic ဖြစ်စေရန် `collections.OrderedDict` သုံးပါ · node `id` အတွက် name ကို
lowercase + non-alphanumeric → `_` ဖြင့် slug လုပ်ပါ · `str.format` ဖြင့် Cypher ရေးပါက `{id: ...}` အတွက်
`{{` `}}` ဖြင့် escape လုပ်ရသည်

**Expected behavior:** triple ၆ ခုမှ statement ၅ ခု (`Person->WORKED_AT->Organization` row ၂ ခု၊ ကျန် ၄ ခု row
၁ ခုစီ)။ Statement တိုင်းသည် `UNWIND $rows AS row` ဖြင့် စပြီး `$rows` ကို parameter အဖြစ် သုံးသည်။ Row
စုစုပေါင်းသည် triple အရေအတွက်နှင့် တူရမည်။

## Exercise 2 — Idempotent merge simulator (`MERGE` vs `CREATE`)

**လုပ်ငန်း:** `InMemoryGraph` class ရေးပါ။ `semantics="merge"` ဖြစ်ပါက identity key (node: `(label, id)`၊ edge:
`(head_label, head_id, rel, tail_label, tail_id, chunk_id)`) ဖြင့် dedupe လုပ်ရမည်၊ `"create"` ဖြစ်ပါက blind
append လုပ်ရမည်။ `nodes_created`၊ `nodes_matched`၊ `edges_created`၊ `edges_matched` counters ထိန်းပြီး
batch ကို နှစ်ကြိမ် apply ၍ နှိုင်းယှဉ်ပါ။

**Hints:** `node_count()`/`edge_count()` သည် သိမ်းထားသော key အရေအတွက် ဖြစ်ရမည် (write အရေအတွက် မဟုတ်) ·
`MERGE` တွင် တွေ့ပါက `nodes_matched` တိုးသည်၊ `CREATE` တွင် မတိုးပါ · pass ၂ တွင် `nodes_matched` သည်
0 ထက် ကြီးရမည်

**Expected behavior:** `MERGE` graph သည် pass ၁ နှင့် ၂ စလုံးတွင် (nodes, edges) = (5, 6) — idempotent။
`CREATE` graph သည် pass ၁ တွင် (12, 6)၊ pass ၂ တွင် (24, 12) — ပွားလာသည်။

## Exercise 3 — Uniqueness constraint validation

**လုပ်ငန်း:** `REQUIRE n.id IS UNIQUE` ၏ အပြုအမူကို client-side တွင် simulate လုပ်ပါ။ Candidate node list မှ
violation list ကို ပြန်ပေးရမည် — `id` အလွတ်/null ဖြစ်ပါက `id_not_null`၊ label တစ်ခုတည်းအတွင်း `id` ထပ်ပါက
`id_unique` ဖြစ်ပြီး ပထမဆုံး တွေ့ခဲ့သော name ကို `first_seen` အဖြစ် ပူးတွဲပြရမည်။ Constraint DDL ကို
print လုပ်ပါ။

**Hints:** `seen` dict ကို `(label, id)` key ဖြင့် သုံးပါ · null/empty `id` ကို duplicate မစစ်မီ အရင်စစ်ပါ ·
Neo4j 5 နှင့် 4.x DDL syntax ကွာခြားချက်ကို comment တွင် ဖော်ပြပါ

**Expected behavior:** candidate ၅ ခုတွင် violation ၂ ခု — `Person` အတွင်း `ada_lovelace` ထပ်ခြင်း (`id_unique`၊
`first_seen="Ada Lovelace"`) နှင့် `Location` အတွင်း `id=""` (`id_not_null`)။ Real server တွင် ဤ violation များသည်
transaction တစ်ခုလုံးကို rollback စေသည်။

## Exercise 4 — Relationship update/delete diff နှင့် orphan cleanup

**လုပ်ငန်း:** Edge set နှစ်ခု (current နှင့် desired) ကို နှိုင်းယှဉ်ပြီး `to_add`/`to_delete` ထုတ်ပါ။ Delete ပြီးနောက်
degree 0 ဖြစ်သော orphan node များကို ရှာပါ။ `DETACH DELETE` ကို လက်တုန်းဖြင့် simulate လုပ်ပြီး node တစ်ခု
ဖျက်လိုက်ချိန် edge အရေအတွက် ပြောင်းလဲမှုကို တွက်ပါ။

**Hints:** edge identity သည် အပေါ်တွင် ဖော်ပြထားသည့် tuple ၆ ခု ဖြစ်သည် · `to_add` = desired − current၊
`to_delete` = current − desired · orphan ကို node တိုင်း၏ degree တွက်ပြီး 0 ဖြစ်သည်ကို စစ်ပါ

**Expected behavior:** current ၆ ခုမှ desired ၄ ခုသို့ ရောက်ရန် `to_delete` ၂ ခု (`USES` နှင့် `COLLABORATED_WITH`)၊
`to_add` မရှိ။ Orphan ၁ ခု — `analytical_engine` (`Technology`)။ `ada_lovelace` ကို `DETACH DELETE` လုပ်ပါက
edge ၄ ခုမှ ၂ ခုသို့ ကျသည်။

## Exercise 5 — Batch transaction sizing

**လုပ်ငန်း:** Row အရေအတွက်နှင့် batch size ကို လက်ခံပြီး batch boundary `(start, end)` များ ပြန်ပေးသည့်
function ရေးပါ။ Latency model `T ≈ (batches · t_tx + N · t_row) / pool_size` ဖြင့် batch size များစွာအတွက်
ခန့်မှန်းချိန် တွက်ပြီး transaction အရေအတွက်နှင့်အတူ print လုပ်ပါ။

**Hints:** `range(0, N, B)` ဖြင့် batch ခွဲပြီး နောက်ဆုံး batch ကို `min` ဖြင့် ဖြတ်ပါ · `t_tx = 4.0` ms၊
`t_row = 0.08` ms၊ `pool_size = 4`၊ `N = 1000` သုံးပါ · Wall-clock သည် batch size တိုးလာသည်နှင့် monotonically
ကျရမည်

**Expected behavior:** `batch_size ∈ {1, 10, 50, 200, 1000}` အတွက် transaction အရေအတွက်သည် `{1000, 100, 20, 5, 1}`
ဖြစ်ပြီး ခန့်မှန်းချိန် ကျဆင်းသည်။ Batch 1 → 1000 သည် round-trip ကို 1000 ဆ လျှော့ချသည်။

## Exercise 6 — Driver call sequence simulation

**လုပ်ငန်း:** `FakeDriver`/`FakeSession`/`FakeResult` ဖြင့် real `neo4j` driver ၏ call sequence ကို simulate လုပ်ပါ —
`verify_connectivity()` တစ်ကြိမ်၊ `session(database="neo4j")` context manager တစ်ခု၊ ထိုအတွင်း batch statement
တိုင်းအတွက် `run(query, rows=...)` တစ်ကြိမ်စီ။ ခေါ်ခဲ့သော call များကို sequence အဖြစ် မှတ်တမ်းတင်ပြီး
per-triple နည်းလမ်း (call ၆ ကြိမ်) နှင့် နှိုင်းယှဉ်ပါ။

**Hints:** `run(query, **params)` ထဲတွင် `query.splitlines()[0]` နှင့် `sorted(params.keys())` ကို မှတ်ပါ ·
`__enter__`/`__exit__` implement လုပ်ပြီး `close()` ကို `__exit__` မှ ခေါ်ပါ · Generate လုပ်ထားသော statement
များကို in-memory graph ပေါ် အမှန်တကယ် apply လုပ်ပါ

**Expected behavior:** `verify_connectivity` ၁ ကြိမ်၊ `session.run` ၅ ကြိမ် (batch ၁ ခုလျှင် တစ်ကြိမ်၊ per-triple
၆ ကြိမ်ထက် နည်း)။ Query တိုင်း၏ ပထမလိုင်းသည် `UNWIND $rows AS row`၊ parameter key သည် `["rows"]` တစ်ခုတည်း။
Graph ရလဒ်သည် node ၅၊ edge ၆။
