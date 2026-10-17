# M06 — Explanation: LLM-extracted Entities နှင့် Relationships ကို Neo4j ထဲ ရေးသွင်းခြင်း

ဤ explanation သည် LLM extraction output (Triple list) မှစပြီး Neo4j ထဲတွင် တည်ငြိမ်သော
Knowledge Graph အဖြစ် ရောက်ရှိသည်အထိ write path ကို subtopic ၆ ခုအဖြစ် ဖြေရှင်းသည်။
subtopic တိုင်းတွင် ချဉ်းကပ်နည်း၏ engineering rationale နှင့် မည်သည့်အခြေအနေတွင်
မသုံးသင့်သည့် trade-off ကို ဖော်ပြသည်။

---

## ၁။ Triple မှ graph write အထိ — batch `MERGE` နှင့် `UNWIND` bulk insert

Extraction output သည် ပုံမှန်အားဖြင့် ဤပုံစံ JSON list ဖြစ်သည် —

```json
[
  {"head": "Ada Lovelace", "head_type": "PERSON",
   "rel": "WORKED_AT", "tail": "Analytical Engine Project",
   "tail_type": "ORGANIZATION", "chunk_id": "c01", "confidence": 0.93}
]
```

နုံသော ချဉ်းကပ်နည်းမှာ triple တစ်ခုလျှင် Cypher statement တစ်ခု ပို့ခြင်းဖြစ်သည်။
N triple အတွက် round-trip N ကြိမ် လိုသည်။ ထို့ကြောင့် triple အားလုံးကို parameter list
တစ်ခုအဖြစ် စုပြီး **statement တစ်ခုတည်း** ဖြင့် ပို့သည့် `UNWIND` pattern ကို သုံးသည်။
`UNWIND` သည် list ကို row အဖြစ် ဖြန့်ခွဲပေးသဖြင့် row တိုင်းအတွက် `MERGE` ကို တစ်ကြိမ်
run ပေးသည်၊ သို့သော် network round-trip မှာ တစ်ကြိမ်သာ ဖြစ်သည်။

```cypher
UNWIND $rows AS row
MERGE (h:Person {id: row.head_id})
  ON CREATE SET h.name = row.head_name
MERGE (t:Organization {id: row.tail_id})
  ON CREATE SET t.name = row.tail_name
MERGE (h)-[r:WORKED_AT {chunk_id: row.chunk_id}]->(t)
  ON CREATE SET r.confidence = row.confidence
  ON MATCH SET r.confidence = row.confidence
```

Label နှင့် relationship type ကို `$param` အဖြစ် မပို့နိုင်သည် (Cypher သည် label/type
အတွက် parameter substitution ကို မထောက်ပံ့သည်)။ ထို့ကြောင့် triple များကို
`(head label, relationship type, tail label)` အလိုက် **group ဖွဲ့ပြီး** group တိုင်းအတွက်
statement တစ်ခု ထုတ်သည်။ Interpolation လုပ်သည့် label/type များသည် **allowlist mapping**
မှသာ လာရမည် — LLM output မှ ရလာသော string ကို တိုက်ရိုက် interpolate လုပ်ခြင်းသည်
Cypher injection ဖြစ်စေသည်။ Values အားလုံး `$rows` ထဲမှ ကြွလာသည်။

Group ဖွဲ့ခြင်း၏ ဘေးထွက်အကျိုးကျေးဇူးမှာ statement အရေအတွက် ကျဆင်းခြင်းဖြစ်သည် —
triple ၆ ခုတွင် group ၅ ခုသာ ရှိသဖြင့် round-trip ၆ ကြိမ်မှ ၅ ကြိမ်သို့ ကျသည်။
Triple ၁၀,၀၀၀ နှင့် distinct group ၄၀ ရှိပါက round-trip သည် ၄၀ ကြိမ်သာ ဖြစ်သည်။

**မသုံးသင့်သည့်အခါ** — row အရေအတွက် အလွန်များသော (သန်းချီ) batch တစ်ခုအတွက်
`UNWIND` တစ်ကြိမ်တည်းသည် transaction memory ကို ဖိစီးသည်။ ထိုအခါ `CALL { ... }
IN TRANSACTIONS OF 1000 ROWS` ဖြင့် batch ကို အလိုအလျောက် ခွဲပေးရသည်။

---

## ၂။ Idempotent graph write — `MERGE` နှင့် `CREATE` ၏ ကွာခြားချက်

`CREATE` သည် label ကို မစစ်ဆေးဘဲ node အသစ် ဖန်တီးသည်။ T ကြိမ် run လျှင် node T ဆ
ဖြစ်လာသည်။ `MERGE` သည် pattern ကို **ရှာပြီး** မတွေ့မှ ဖန်တီးသည် — ထို့ကြောင့်
တူညီသော input ကို ထပ်ခါတလဲလဲ run လျှင် ရလဒ် မပြောင်းလဲပါ။ ဤဂုဏ်သတ္တိကို
**Idempotency** ဟုခေါ်ပြီး ingestion pipeline များအတွက် မဖြစ်မနေ လိုအပ်သည်။

`lab.py` ၏ in-memory simulation သည် ဤကွာခြားချက်ကို တိတိကျကျ ပြသည် —

| Semantics | Pass 1 (nodes, edges) | Pass 2 (nodes, edges) |
|---|---|---|
| `MERGE` | (5, 6) | (5, 6) |
| `CREATE` | (12, 6) | (24, 12) |

`MERGE` ၏ counters မှာ `nodes_created=5`, `nodes_matched=19`, `edges_created=6`,
`edges_matched=6` ဖြစ်သည် — pass ၂ တွင် node အားလုံး matched ဖြစ်သွားသည်ကို
counter ဖြင့် တိုင်းတာနိုင်သည်။ Ingestion job တစ်ခု မအောင်မြင်ဘဲ ပြန် run ချိန်တွင်
graph မပွားလာစေရန် ဤ counter များကို monitoring metric အဖြစ် သုံးရသည်။

Identity key ရွေးချယ်မှုသည် အဓိကဖြစ်သည်။ `{id: row.head_id}` ဖြစ်ပါက `id` သည်
canonical, normalized value ဖြစ်ရမည် — "Ada Lovelace" နှင့် "Ada  Lovelace" (space နှစ်ခု)
သည် id ကွဲသွားပြီး duplicate node ဖြစ်လာသည်။ ထို့ကြောင့် M02 ၏ entity resolution
အဆင့်သည် write path ၏ ရှေ့တွင် တည်ရှိရမည်။

**မသုံးသင့်သည့်အခါ** — log event သို့မဟုတ် immutable fact (စာရင်းစစ် record) များအတွက်
ထပ်တူ event များကို ရည်ရွယ်ချက်ရှိရှိ သိမ်းရန် `CREATE` က မှန်ကန်သည်။ `MERGE` သည်
unique constraint မရှိဘဲ concurrent session နှစ်ခု တစ်ပြိုင်နက် run လျှင် duplicate
ဖန်တီးနိုင်သေးသည် — ဤအချက်ကို subtopic ၃ တွင် ဖြေရှင်းသည်။

---

## ၃။ Constraint ဖြင့် entity uniqueness ထိန်းချုပ်ခြင်း — `REQUIRE n.id IS UNIQUE`

```cypher
CREATE CONSTRAINT entity_id_unique IF NOT EXISTS
FOR (n:Entity) REQUIRE n.id IS UNIQUE
```

(Neo4j 5 syntax။ Neo4j 4.x တွင် `CREATE CONSTRAINT entity_id_unique IF NOT EXISTS
ON (n:Entity) ASSERT n.id IS UNIQUE` ဖြစ်သည်။)

Constraint သည် သုံးမျိုးသော အကျိုးသက်ရောက်မှု ရှိသည် —

1. **Correctness** — duplicate `id` ရှိသော write ကို server က ငြင်းပယ်သည်။ Transaction
   တစ်ခုလုံး fail ဖြစ်သဖြင့် graph သည် တစ်ဝက်တစ်ပျက် အခြေအနေသို့ မရောက်ပါ။
2. **Concurrency** — uniqueness ကို server က အာမခံသဖြင့် session pool ထဲမှ session
   များ တစ်ပြိုင်နက် `MERGE` လုပ်လျှင်လည်း duplicate node မဖြစ်ပါ။
3. **Performance** — unique constraint သည် backing index ကို အလိုအလျောက် ဖန်တီးပေးသည်။
   `MERGE ... {id: ...}` သည် ထို index ကို သုံး၍ node ကို O(1) နှင့် ရှာသည်။ Index
   မရှိပါက `MERGE` သည် index-free adjacency ၏ အကျိုးမရရှိဘဲ label scan ပြုလုပ်သည် —
   label တွင် node သန်းချီ ရှိပါက write တစ်ကြိမ်၏ latency သည် ဆယ်ဆကျော် ကွာသည်။

Write မတိုင်မီ client-side validation သည် defense-in-depth အဖြစ် အသုံးဝင်သည် —
`id` သည် null/empty ဖြစ်နေသော row များကို batch တစ်ခုလုံး မပို့မီ ဖယ်ထုတ်နိုင်သည်။
`lab.py` ၏ simulation သည် candidate ၅ ခုတွင် violation ၂ ခုကို ရှာတွေ့သည် —
`Person` label အတွင်း `ada_lovelace` ထပ်ခြင်း (`id_unique`) နှင့် `Location` အတွင်း
`id` အလွတ်ဖြစ်ခြင်း (`id_not_null`)။

**Security သတိပေးချက်** — `CREATE CONSTRAINT`၊ `DROP CONSTRAINT`၊ `CREATE INDEX`
ကဲ့သို့သော schema DDL များကို Text-to-Cypher လမ်းကြောင်းမှ ဖြတ်သန်းခွင့် မပြုရ။
ထို query များကို allowlist-based guardrail ဖြင့် block ပြီး read-only role ဖြင့်သာ
LLM-generated query များကို run စေရမည်။

**မသုံးသင့်သည့်အခါ** — `id` ကို application layer မှ အာမခံပြီးသား၊ node အရေအတွက်
အလွန်နည်းသော prototype တွင် constraint ထည့်ခြင်းသည် ingestion ကို မနှေးစေသော်လည်း
ကာကွယ်မှုလည်း မပေးပါ။ Multi-tenant graph တွင် uniqueness သည် `(tenant_id, id)` အတွက်
ဖြစ်ရမည် — `id` တစ်ခုတည်းအပေါ် constraint ထားပါက tenant နှစ်ခု၏ တူညီသော id များ
တိုက်မိမည်။ Neo4j 5 သည် node key constraint ဖြင့် ဤအခြေအနေကို ဖြေရှင်းသည်။

---

## ၄။ Update နှင့် delete semantics — stale relationship၊ orphan node၊ cascade delete

Re-extraction ပြီးတိုင်း graph သည် အဟောင်း triple များကို ထိန်းထားလျှင် အချိန်ကြာလာသည့်အခါ
မှားယွင်းသော retrieval ကို ပြန်ပေးသည်။ ထို့ကြောင့် **desired state** နှင့် **current state**
ကို diff လုပ်ပြီး ကွာခြားချက်ကို သုံး၍ write လုပ်ရသည် —

```cypher
-- stale relationship ဖယ်ရှားခြင်း
MATCH (h:Person {id: $head_id})-[r:USES {chunk_id: $chunk_id}]->(t:Technology {id: $tail_id})
DELETE r
```

`lab.py` တွင် current edge ၆ ခုမှ desired edge ၄ ခုသို့ ရောက်ရန် `USES` နှင့်
`COLLABORATED_WITH` edge ၂ ခုကို delete လုပ်သည်။ Relationship delete သည် node များကို
မထိခိုက်ပါ — ထို့ကြောင့် `analytical_engine` (`Technology`) node သည် degree 0 ဖြစ်လာပြီး
**orphan node** ဖြစ်လာသည်။ Orphan node များသည် node count ကို မှားယွင်းစေပြီး
node-count-based metric များကို အနှောင့်အယှက် ဖြစ်စေသည်။

```cypher
MATCH (n:Technology)
WHERE NOT (n)--()
DELETE n
```

`DELETE` နှင့် `DETACH DELETE` ကွာခြားချက်သည် အရေးကြီးသည်။ `DELETE n` သည် node တွင်
relationship ရှိနေပါက error ဖြင့် ကျရှုံးသည် — ၎င်းသည် **accidental cascade ကာကွယ်မှု**
ဖြစ်သည်။ `DETACH DELETE n` သည် relationship အားလုံးကို အရင်ဖျက်ပြီးမှ node ကို ဖျက်သည်။
Simulation တွင် `ada_lovelace` ကို `DETACH DELETE` လုပ်ချိန် edge ၄ ခုမှ ၂ ခုသို့ ကျသည် —
node တစ်ခု၏ ဖျက်လိုက်သော relationship အရေအတွက်ကို ကြိုတင် တိုင်းတာထားရမည်။

**မသုံးသင့်သည့်အခါ** — `DETACH DELETE` ကို LLM-generated query မှ တိုက်ရိုက် ခေါ်ခွင့်ပြုခြင်းသည်
destructive operation ဖြစ်သည်။ ဖျက်မည့်အရာကို ကြိုတင် count လုပ်ပြီး threshold ကျော်ပါက
approval လိုအပ်စေရမည်။ Incremental ingestion တွင် relationship ကို အမှန်တကယ် ဖျက်မည့်အစား
အဟောင်း edge ကို `valid_from`/`valid_to` property ဖြင့် invalidate လုပ်ခြင်း (temporal graph)
သည် audit လိုအပ်သော စနစ်များအတွက် ပိုသင့်လျော်သည်။

---

## ၅။ Batch performance — transaction batching၊ session pool၊ index အရေးပါမှု

Write လုပ်ငန်းတိုင်းတွင် **transaction overhead** နှင့် **per-row cost** နှစ်မျိုး ပေါင်းထည့်သည်။
Batch size ကို B၊ row အရေအတွက်ကို N၊ transaction overhead ကို `t_tx`၊ row တစ်ခုချင်း
ကုန်ကျမှုကို `t_row`၊ concurrent session အရေအတွက်ကို P သတ်မှတ်ပါက wall-clock ခန့်မှန်းချက်မှာ —

```
T ≈ ( ceil(N / B) · t_tx + N · t_row ) / P
```

`lab.py` တွင် `t_tx = 4 ms`၊ `t_row = 0.08 ms`၊ `P = 4`၊ `N = 1000` ဖြင့် တွက်ချက်သည် —

| batch_size | transactions | estimated wall-clock |
|---|---|---|
| 1 | 1000 | 1.0200 s |
| 10 | 100 | 0.1200 s |
| 50 | 20 | 0.0400 s |
| 200 | 5 | 0.0250 s |
| 1000 | 1 | 0.0210 s |

Batch size 1 မှ 1000 သို့ တိုးခြင်းသည် round-trip အရေအတွက်ကို **1000 ဆ** လျှော့ချပေးသည်။
သို့သော် ပုံသေ `N · t_row` term ကြောင့် အကျိုးအမြတ်သည် တစ်နေရာတွင် ပြန်၍ ပြားသွားသည် —
batch size ကို ထိုထက်ကျော် တိုးခြင်းသည် latency မကျစေတော့ဘဲ transaction memory ကိုသာ
တိုးစေသည်။ Batch size သည် database ၏ heap ထဲ transaction state အားလုံး ဝင်နိုင်သည့်
အရွယ်ထက် မကျော်ရ။

Session pool သည် `T` ကို P ဖြင့် စားသည်။ `GraphDatabase.driver` သည် default pool size
(`max_connection_pool_size`) ဖြင့် session များကို ပြန်သုံးသည် — session တစ်ခုချင်း
ဖန်တီး/ပိတ်ခြင်းသည် connection handshake ကုန်ကျမှုကို ပြန်ထည့်စေသဖြင့် batch loop ကို
session တစ်ခုတည်းအတွင်း run ရသည်။ Pool size ကို CPU core နှင့် server heap အပေါ်
မူတည်ပြီး သတ်မှတ်ရသည်၊ ကျော်လွန်ပါက lock contention နှင့် page cache thrashing ဖြစ်သည်။

Index အရေးပါမှုသည် subtopic ၃ တွင် ဖော်ပြခဲ့သည့်အတိုင်း `MERGE` ၏ lookup cost ကို
ဆုံးဖြတ်သည်။ Index မရှိသော ရေးသွင်းမှုတွင် B ကို မည်မျှချိန်လည်း O(N) scan ကြောင့်
per-row cost တိုးနေသဖြင့် batch tuning သည် အကျိုးမထူးပါ။

**မသုံးသင့်သည့်အခါ** — Batch size ကို အလွန်ကြီးစေခြင်း (ဥပမာ row ၁၀၀,၀၀၀ တစ်
transaction) သည် failure recovery ကို ခက်ခဲစေသည် — transaction တစ်ခု fail ဖြစ်ပါက
row အားလုံး ပြန် retry ရသည်။ ထိုအခါ `IN TRANSACTIONS OF` ဖြင့် chunk ခွဲပြီး တစ်စိတ်တစ်ပိုင်း
success ကို ထိန်းထားရသည်။

---

## ၆။ Python driver အခြေခံ — offline simulation နှင့် live driver call ဆက်စပ်မှု

Live write path သည် ဤ driver call အစီအစဉ် အတိအကျ ဖြစ်သည် (ဤ code ကို `lab.py` ထဲ
မထည့်ရ — `neo4j` package လိုအပ်သဖြင့် server မရှိဘဲ run မရပါ) —

```python
from neo4j import GraphDatabase

driver = GraphDatabase.driver(
    "bolt://localhost:7687", auth=("neo4j", "graphrag123")
)
driver.verify_connectivity()

with driver.session(database="neo4j") as session:
    for statement in statements:
        summary = session.run(statement["cypher"], rows=statement["rows"]).consume()
        counters = summary.counters
        print(counters.nodes_created, counters.relationships_created)

driver.close()
```

Offline `lab.py` သည် ဤအစီအစဉ်ကို `FakeDriver`/`FakeSession` ဖြင့် တူညီစွာ ဖော်ဆောင်သည် —

| Real driver | lab.py simulation |
|---|---|
| `GraphDatabase.driver(uri, auth=...)` | `FakeDriver("bolt://localhost:7687", ("neo4j", "graphrag123"))` |
| `driver.verify_connectivity()` | `FakeDriver.verify_connectivity()` (call တစ်ကြိမ် ရေတွက်) |
| `driver.session(database="neo4j")` | `FakeDriver.session(database="neo4j")` |
| `session.run(cypher, rows=rows)` | `FakeSession.run(query, **params)` — call များကို sequence အဖြစ် မှတ်တမ်းတင် |
| `result.consume().counters` | `FakeResult.consume()["counters"]` |
| `session.close()` / context manager | `__enter__`/`__exit__` ဖြင့် `closed` flag |

`session.run(query, **params)` တွင် `rows=...` သည် keyword argument အဖြစ် ရောက်ပြီး
Cypher ထဲရှိ `$rows` parameter နှင့် name အလိုက် တွဲသည်။ `**params` ပုံစံသည်
`session.run(q, rows=rows)` နှင့် `session.run(q, **{"rows": rows})` ကို တူညီစေသည်။
`result` ကို ချက်ချင်း iterate မလုပ်ဘဲ `consume()` ခေါ်ခြင်းသည် write query အတွက်
record buffer ကို ရှင်းပေးပြီး counters ကို ရရှိစေသည်။

Offline simulation သည် **Cypher generation၊ batch grouping နှင့် call sequence** ကို
အာမခံသည်။ အာမခံ **မပေး** သည့်အချက်များမှာ — Cypher syntax မှန်ကန်မှု၊ constraint
enforcement၊ index query plan နှင့် transaction isolation ဖြစ်သည်။ ထို့ကြောင့် lab
အောင်မြင်ပြီးနောက် repo ၏ `docker-compose.yml` (Neo4j 5 Community၊ Bolt `7687`၊
Browser `7474`၊ `neo4j` / `graphrag123`) ဖြင့် server တင်ပြီး live driver ဖြင့်
တစ်ကြိမ် run ရမည်။ Simulation တွင် PASS ဖြစ်ပြီး live တွင် fail ဖြစ်သော အဖြစ်များဆုံး
အကြောင်းရင်းမှာ label/relationship type interpolation နှင့် parameter name မကိုက်ခြင်း
ဖြစ်သည်။

**Security သတိပေးချက်** — credential ကို code ထဲ hardcode မလုပ်ရ၊ environment variable
မှ ဖတ်ရမည်။ Driver instance သည် application lifecycle တစ်ခုလုံးအတွက် တစ်ခုတည်း ဖြစ်ရမည် —
request တိုင်း driver အသစ် ဖန်တီးခြင်းသည် pool ကို အသုံးမဝင်စေဘဲ connection leak ဖြစ်စေသည်။

---

## Summary Checklist

- [ ] Triple များကို `(head label, rel type, tail label)` အလိုက် group ဖွဲ့ပြီး statement တိုင်းတွင် `UNWIND $rows AS row` သုံးသည်
- [ ] Values အားလုံး `$param` ဖြင့် ပို့သည်၊ label/type များသာ allowlist မှ interpolate လုပ်သည်
- [ ] Node write တိုင်းတွင် `MERGE` သုံးပြီး input ကို ထပ်ခါတလဲလဲ run လျှင် node/edge count မပြောင်းလဲခြင်းကို စမ်းသပ်ပြီး
- [ ] `REQUIRE n.id IS UNIQUE` constraint ကို write မတိုင်မီ တင်ထားပြီး၊ client-side null/duplicate validation လည်း ရှိသည်
- [ ] Desired state vs current state diff ဖြင့် stale relationship များ ဖျက်ပြီး orphan node များကို ရှာဖွေဖယ်ရှားသည်
- [ ] `CREATE`၊ `DELETE`၊ `DETACH DELETE` ကဲ့သို့သော destructive clause များကို Text-to-Cypher မှ block လုပ်သည်
- [ ] Batch size ကို transaction memory နှင့် failure recovery cost အပေါ် မူတည်ပြီး ရွေးသည်၊ session pool ကို ပြန်သုံးသည်
- [ ] `python3 modules/06_storing_entities_relationships_neo4j/lab.py` → `exit 0` ဖြစ်ကြောင်း အတည်ပြုသည်
