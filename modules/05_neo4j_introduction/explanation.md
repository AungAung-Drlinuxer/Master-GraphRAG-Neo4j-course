# M05 — Introduction to Neo4j: အဓိက သဘောတရားများ

ဤဖိုင်သည် Neo4j ၏ data model၊ storage architecture၊ Cypher ၏ အခြေခံ clause များ၊ Constraint/Index
များ၊ parameterization နှင့် graph database ရွေးချယ်မှုဆိုင်ရာ ဆုံးဖြတ်ချက်များကို ရှင်းလင်းသည်။
Subtopic တိုင်းတွင် ဘာကြောင့် ဤနည်းလမ်း ဖြစ်သနည်း (rationale) နှင့် ဘယ်အချိန်တွင် မသုံးသင့်သနည်း
(trade-off) ကို တွဲဖက် ဖော်ပြသည်။

---

## ၁။ Property Graph Model

Neo4j ၏ data model သည် **Property Graph** ဖြစ်သည်။ အစိတ်အပိုင်း ၄ မျိုး ရှိသည်။

- **Node** — graph ၏ entity တစ်ခု။ Node သည် identity (internal id) နှင့် property အစုတစ်ခု ပိုင်ဆိုင်သည်။
- **Label** — Node ကို အမျိုးအစားခွဲသည့် tag။ Node တစ်ခုတွင် Label များစွာ တွဲနိုင်သည် (`:Person:Employee`)။
  Label သည် schema အဆင့်တွင် ရှိပြီး query ကို ကျဉ်းမြောင်းစေသည်။
- **Relationship** — Node နှစ်ခုကို ချိတ်ဆက်သည့် **directed, typed** edge။ Direction သည် အဓိပ္ပာယ် သယ်သည်
  (`(a)-[:WORKS_AT]->(b)` သည် `(b)-[:WORKS_AT]->(a)` နှင့် မတူ)။ Type မရှိသော relationship မရှိရ။
- **Property** — Node နှင့် Relationship နှစ်မျိုးလုံးတွင် ရှိနိုင်သည့် key–value pair။
  Relationship ပေါ်ရှိ property သည် relationship အရည်အသွေး (ဥပမာ `since`၊ `confidence`၊ `source_chunk`)
  ကို သယ်ဆောင်သည်။

Relationship ကို property ဖြင့် ကိုယ်စားပြုခြင်းထက် edge အဖြစ် တိုက်ရိုက် ထားခြင်းသည် traversal
ကို အဓိကအားဖြင့် ပိုမြန်စေသည် — relationship type နှင့် direction ကို engine က ကြိုတင် သိထားသည်။

Knowledge Graph context တွင် Triple (`subject – predicate – object`) သည် Property Graph သို့ ညီမျှစွာ
map ဖြစ်သည် — subject/object သည် Node၊ predicate သည် Relationship type ဖြစ်သည်။

```cypher
MERGE (s:Entity {id: $subject_id})
  ON CREATE SET s.name = $subject_name
MERGE (o:Entity {id: $object_id})
  ON CREATE SET o.name = $object_name
MERGE (s)-[r:MENTIONS]->(o)
  ON CREATE SET r.source_chunk = $chunk_id, r.confidence = $confidence
```

**Trade-off** — Property Graph သည် schema ပြောင်းလဲမှုကို ခံနိုင်သည် (schema-flexible)။ သို့သော်
property type ကို database က အတင်းအကြပ် မစစ်ဆေးသောကြောင့် data quality ကို application အဆင့်တွင်
ကိုယ်တိုင် စစ်ရသည်။ Formal ontology validation (RDF/OWL reasoning) လိုအပ်သော အခြေအနေတွင်
Property Graph သည် မလုံလောက်နိုင်။

---

## ၂။ Neo4j Architecture — index-free adjacency၊ storage၊ Bolt၊ Browser

**Index-free adjacency** သည် Neo4j ၏ အဓိကစွမ်းဆောင်ရည် ဆိုင်ရာ ဆုံးဖြတ်ချက် ဖြစ်သည်။ Node တိုင်းသည်
၎င်း၏ relationship များသို့ တိုက်ရိုက် pointer (physical reference) ကို ကိုင်ထားသည်။ ထို့ကြောင့်
neighbor တစ်ခုသို့ ရောက်ရန် global index lookup မလိုအပ် — pointer ကို dereference လုပ်ရုံသာ။

ဆိုလိုသည်မှာ traversal cost သည် **graph စုစုပေါင်း အရွယ်အစား (N) ပေါ်တွင် မမှီခို**၊ သွားလာသည့်
relationship အရေအတွက် (degree) ပေါ်တွင်သာ မှီခိုသည်။ Relational store တွင် hop တစ်ခုစီအတွက် join
သို့မဟုတ် index lookup `O(log N)` လိုသည်။ Neo4j တွင် hop တစ်ခုစီသည် `O(degree)` ဖြစ်သည်။

```
index-based engine : hop 1 လျှင် O(log N) lookup တစ်ခု
index-free adjacency : hop 1 လျှင် pointer dereference တစ်ခု (N နှင့် မသက်ဆိုင်)
```

**Storage** — Neo4j သည် fixed-size record store ကို သုံးသည်။ Node record၊ relationship record၊
property record များ သီးခြားစီ ရှိသည်။ Relationship record သည် doubly-linked list အဖြစ်
ဆက်စပ်ထားသောကြောင့် node တစ်ခု၏ relationship စာရင်းကို ဖြတ်သန်းရန် လွယ်ကူသည်။

**Bolt protocol** — application (Driver) နှင့် database အကြား binary, stateful protocol။ Bolt သည်
session/transaction semantics ကို သယ်ဆောင်ပြီး HTTP ထက် overhead နည်းသည်။ Python application မှ
`neo4j` driver ဖြင့် `bolt://localhost:7687` သို့ ချိတ်ဆက်သည်။

**Neo4j Browser** — web-based query interface (default port `7474`)။ Cypher ရေးပြီး result ကို
graph visualization အဖြစ် ကြည့်ရန် သုံးသည်။ Production တွင် ad-hoc inspection အတွက်သာ သုံးသင့်သည် —
programmatic access အတွက် Driver သို့မဟုတ် Cypher Shell ကို သုံးရသည်။

**Trade-off** — index-free adjacency သည် deep/large traversal ကို ကြီးမားစွာ အမြန်ဆုံး ဖြစ်စေသော်လည်း
dense node (relationship သိန်းချီ ရှိသော super-node) ရှိပါက traversal သည် degree နှင့်အညီ ကြီးထွားသည်။
Super-node ရှိသော graph တွင် traversal ကို depth နှင့် relationship type ဖြင့် ကန့်သတ်ရမည်။
ထို့အပြင် Neo4j ကို sharding လုပ်ရာတွင် traversal အများစုသည် single instance ပေါ် ကျရောက်ရန်
data model ကို ဒီဇိုင်းလုပ်ရသည် — general-purpose horizontal sharding သည် relational store ထက် ခက်ခဲသည်။

---

## ၃။ Cypher အခြေခံ — `MATCH`၊ `CREATE`၊ `MERGE`၊ `WHERE`၊ `RETURN`၊ `SET`၊ `DELETE`

Cypher သည် declarative၊ ASCII-art pattern ကို အသုံးပြုသည်။ Clause တိုင်းသည် pipe အဖြစ်
အစဉ်လိုက် အလုပ်လုပ်သည်။

| Clause | တာဝန် |
|---|---|
| `MATCH` | ရှိပြီးသား pattern ကို ရှာသည် (read) |
| `WHERE` | `MATCH`/`WITH` ၏ ရလဒ်ကို စစ်ထုတ်သည် |
| `RETURN` | ရလဒ် projection နှင့် output |
| `CREATE` | pattern အသစ်ကို အမြဲ ထည့်သည် (duplicate ဖြစ်စေနိုင်) |
| `MERGE` | pattern ရှိလျှင် match၊ မရှိလျှင် create (idempotent write) |
| `SET` | property နှင့် label ကို update လုပ်သည် |
| `DELETE` | node/relationship ကို ဖျက်သည် |

```cypher
// Read — entity ကို id ဖြင့် ရှာပြီး 2-hop subgraph ကို ဆွဲထုတ်ခြင်း
MATCH (e:Entity {id: $id})
OPTIONAL MATCH path = (e)-[:REL*1..2]->(n)
RETURN e, collect(n) AS neighbours
```

```cypher
// Idempotent write — MERGE ဖြင့် duplicate မဖြစ်စေဘဲ update လုပ်ခြင်း
MERGE (n:Entity {id: $id})
  ON CREATE SET n.created_at = $ts
SET n.name = $name, n.updated_at = $ts
RETURN n
```

```cypher
// Delete — relationship ကို အရင် ဖျက်ပြီး node ကို ဖျက်ခြင်း
MATCH (a:Entity {id: $id})-[r]->(b)
DELETE r
WITH a
MATCH (a)
DETACH DELETE a
```

**`CREATE` နှင့် `MERGE` ကွာခြားချက်** — `CREATE` သည် run တိုင်း element အသစ် ဖန်တီးသည်။ `MERGE`
သည် pattern လုံးကို အရင် match လုပ်ပြီး မတွေ့မှ create လုပ်သည်။ Graph ingestion တွင် idempotency
လိုသောကြောင့် `MERGE` ကို သုံးရသည်။

**Trade-off** — `MERGE` သည် `CREATE` ထက် စျေးကြီးသည် — pattern lookup တစ်ခု အပိုလိုသည်။
ထို့ကြောင့် bulk ingest တွင် constraint/index မရှိဘဲ `MERGE` သုံးပါက per-row scan ဖြစ်ပြီး
linear scale ကျသည်။ ဖြေရှင်းနည်းမှာ identity property ပေါ်တွင် uniqueness constraint ထားခြင်း
(အပိုင်း ၄ ကို ကြည့်ပါ) နှင့် `UNWIND $rows AS row` ဖြင့် batch လုပ်ခြင်း ဖြစ်သည်။

**Ordering** — Cypher တွင် clause အစဉ်သည် တင်းကျပ် (strict) ဖြစ်သည်။ `MATCH` သည် `WHERE` အရ ရှိရမည်၊
`RETURN` သည် နောက်ဆုံး လုပ်ငန်းခွဲ ဖြစ်ရမည်။ `RETURN` ပြီးနောက် `MATCH` ထည့်ပါက syntax error ဖြစ်သည်။
ဤစည်းမျဉ်းကို static validator တွင် clause rank အဖြစ် ကိုယ်စားပြုနိုင်သည်။

---

## ၄။ Constraints နှင့် Indexes

**Uniqueness constraint** သည် property တစ်ခုပေါ်တွင် value ထပ်ခြင်းကို database အဆင့်တွင် တားဆီးသည်။
Neo4j 5 တွင် syntax သည် `FOR ... REQUIRE ...` ဖြစ်သည်။

```cypher
CREATE CONSTRAINT entity_id_unique IF NOT EXISTS
FOR (n:Entity) REQUIRE n.id IS UNIQUE
```

Uniqueness constraint သည် uniqueness ကို အာမခံရုံမက **backing index** တစ်ခုကိုပါ ဖန်တီးပေးသည်။
ထို့ကြောင့် `MERGE (n:Entity {id: $id})` သည် index lookup `O(log N)` ဖြင့် အလုပ်လုပ်သည် — full scan
မဖြစ်။ Constraint သည် entity resolution ၏ duplicate ဖြစ်မှုကို database အဆင့်တွင် ကာကွယ်သောကြောင့်
LLM extraction ၏ မမှန်ကန်သော duplicate များကို နောက်ဆုံး အဆင့်တွင် ဖမ်းမိသည်။

**Range index** သည် equality နှင့် range (`>`, `<`, `STARTS WITH`) lookup အတွက် ဖြစ်သည်။

```cypher
CREATE INDEX entity_name_range IF NOT EXISTS
FOR (n:Entity) ON (n.name)
```

**Full-text index** သည် tokenize လုပ်ပြီး Lucene-based similarity ရှာဖွေမှုအတွက် ဖြစ်သည်။
Range index သည် exact/prefix match သာ လုပ်နိုင်သည်၊ substring သို့မဟုတ် fuzzy search မလုပ်နိုင်။

```cypher
CREATE FULLTEXT INDEX entity_fulltext IF NOT EXISTS
FOR (n:Entity) ON EACH [n.name, n.description]
```

Query —

```cypher
CALL db.index.fulltext.queryNodes('entity_fulltext', $search_term)
YIELD node, score
RETURN node.id AS id, score
ORDER BY score DESC
LIMIT 10
```

**Query plan သက်ရောက်မှု** — Index/constraint မရှိပါက `MATCH (n:Entity {id: $id})` သည်
`NodeByLabelScan` + filter ဖြစ်ပြီး complexity `O(N)` ဖြစ်သည်။ Index ရှိပါက `NodeIndexSeek`
ဖြစ်ပြီး `O(log N)` ဖြစ်သည်။ `EXPLAIN`/`PROFILE` ဖြင့် စစ်ဆေးနိုင်သည်။

```cypher
EXPLAIN MATCH (n:Entity {id: $id}) RETURN n
PROFILE MATCH (n:Entity {id: $id}) RETURN n
```

**Security ဆိုင်ရာ သတိပေးချက်** — Text-to-Cypher pipeline တွင် LLM က `DELETE`၊ `DETACH DELETE`၊
`DROP` ကဲ့သို့ destructive clause များကို generate လုပ်နိုင်သည်။ Query ကို read-only user
(သို့မဟုတ် read transaction) ဖြင့် run ရမည်။ Clause whitelist စစ်ဆေးခြင်း၊ `EXPLAIN` ဖြင့်
plan ကို execute မလုပ်မီ စစ်ဆေးခြင်း၊ statement အရေအတွက် ၁ ခုသာ ခွင့်ပြုခြင်း (semicolon
smuggling ကာကွယ်ရန်) များ လိုသည်။

**Trade-off** — Index တိုင်းသည် write throughput ကို လျော့စေသည် (insert တိုင်း index update
လိုသည်) နှင့် storage ကို ပိုသုံးသည်။ ၂ hop အထိ သေးငယ်သော graph တွင် index များ၏ အကျိုး
နည်းသည်။ ထို့ကြောင့် query pattern အပေါ် အခြေခံ၍ index ကို ရည်ရွယ်ချက်ရှိရှိ ထည့်ရသည်၊
default အဖြစ် property တိုင်းကို index မလုပ်ရ။

---

## ၅။ Parameterization — `$param` ဖြင့် Cypher Injection ကာကွယ်ခြင်း

Cypher injection သည် user input ကို query string အဖြစ် string concatenation ဖြင့် ပေါင်းထည့်သောအခါ
ဖြစ်သည်။ Parameter ကို သုံးပါက value သည် query ၏ syntax tree အပြင်ဘက်တွင် သီးခြားစီ သယ်ဆောင်သည် —
value ထဲရှိ quote၊ semicolon၊ clause keyword များသည် syntax အဖြစ် အဓိပ္ပာယ် မဖွင့်တော့ပါ။

```cypher
// Parameterized — လုံခြုံသည်
MERGE (n:Entity {id: $id})
SET n.name = $name
RETURN n
```

```python
# Driver ဘက်တွင် parameter ကို dict အဖြစ် သီးခြားစီ ပေးသည်
params = {"id": "e1", "name": "Robert'); MATCH (n) DETACH DELETE n;//"}
query = "MERGE (n:Entity {id: $id}) SET n.name = $name RETURN n"
# query text ထဲတွင် payload မပါဝင်ပါ — value သည် parameter အဖြစ်သာ သွားသည်
```

**Parameter လုပ်မရသော အစိတ်အပိုင်းများ** — Label၊ Relationship type၊ property key၊ နှင့်
`LIMIT` ပမာဏ (Neo4j 5 အဆင့်တွင် `LIMIT $n` ကို ခွင့်ပြုချိန်တွင် ကိန်းလုံးအဖြစ်သာ) တို့ကို
parameterize လုပ်မရပါ။ ထို dynamic အစိတ်အပိုင်းများအတွက် whitelist regex
(`^[A-Za-z_][A-Za-z0-9_]*$`) ဖြင့် စစ်ဆေးရမည်။

```python
# Label ကို parameter မလုပ်နိုင်သောကြောင့် whitelist စစ်ဆေးရသည်
import re
LABEL_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")
assert LABEL_RE.match("Entity")
assert not LABEL_RE.match("Entity`) DETACH DELETE (n")
```

**Version မှတ်ချက်** — Neo4j 4.x နှင့် 5.x တွင် parameter syntax သည် `$param` ဖြစ်သည်။
Neo4j 3.x နှင့် အစောပိုင်း version များတွင် `{param}` ကို သုံးခဲ့သည်။ ဤ course တစ်လျှောက်
`$param` (Neo4j 5) ကို သုံးသည်။

**Security ဆိုင်ရာ မူဝါဒ** — parameterization သည် injection ကို ကာကွယ်သော်လည်း authorization ကို
အစားထိုးမပေးပါ။ database role များကို least-privilege အဖြစ် သတ်မှတ်ရမည် (read-only user
သည် write မလုပ်နိုင်)။ Application အဆင့်တွင် user ကို အခြား tenant ၏ node သို့ ရောက်စေသော
IDOR အတွက် tenant filter ကို query ထဲတွင် အတင်းအကြပ် ထည့်ရသည်။

---

## ၆။ Neo4j နှင့် အခြား Graph Database နှိုင်းယှဉ်ချက်

| System | Model | Query | အားသာချက် | အားနည်းချက် |
|---|---|---|---|---|
| Neo4j | Property Graph (native) | Cypher | mature traversal engine၊ index-free adjacency၊ tooling | sharding ခက်ခဲ၊ single-writer scaling |
| ArangoDB | Document + Graph | AQL | multi-model | graph traversal သည် Neo4j ထက် နှေး |
| Amazon Neptune | Property Graph + RDF | Gremlin / SPARQL | managed၊ RDF support | vendor lock-in |
| JanusGraph | Property Graph | Gremlin | horizontal scale (Cassandra backend) | operational complexity ကြီး |
| TigerGraph | Property Graph | GSQL | parallel traversal | deployment overhead ကြီးသည် |
| RDF store (Blazegraph, Oxigraph) | RDF Triple | SPARQL | formal ontology၊ reasoning | property/edge property ကန့်သတ် |

**Neo4j သင့်တော်သည့် အခြေအနေများ**

- Query သည် multi-hop traversal ကို အဓိက မှီခိုသည် (GraphRAG ၏ subgraph retrieval)
- Graph သည် single-instance memory အရွယ်အစား အတွင်း ရှိသည် (သို့) read replica ဖြင့် scale လုပ်နိုင်သည်
- Cypher ecosystem နှင့် tooling (Bloom၊ APOC/GDS၊ Browser) ကို အလိုရှိသည်
- Constraint အဆင့်။ entity uniqueness အာမခံချက် လိုအပ်သည်

**Neo4j မသင့်တော်သည့် အခြေအနေများ**

- Petabyte-scale၊ heavy write concurrency လိုအပ်သော workload (ဥပမာ clickstream) — multi-writer
  system က ပိုသင့်တော်သည်
- Formal OWL reasoning သည် core requirement ဖြစ်သည် — RDF/SPARQL stack က ပိုသင့်တော်သည်
- Query သည် analytical aggregation အဓိက ဖြစ်သည် (column store က ပိုသင့်တော်သည်)
- Edge property များစွာကို ပြောင်းလဲသော write-heavy graph

**Decision rule** — Relationship ကို first-class အဖြစ် traverse လုပ်သည့် query အချိုးသည် များပြီး
graph အရွယ်အစားသည် single instance အတွင်း ရှိပါက Neo4j သည် သင့်တော်သည်။ Aggregation အဓိကဖြစ်ပါက
relational/column store ကို ရွေးရသည်။

---

## Summary Checklist

- [ ] Property Graph ၏ အစိတ်အပိုင်း ၄ မျိုး (Node၊ Label၊ Relationship၊ Property) ကို ရှင်းပြနိုင်သည်
- [ ] Relationship သည် directed နှင့် typed ဖြစ်ရမည် — direction သည် အဓိပ္ပာယ် သယ်သည်
- [ ] index-free adjacency ကြောင့် traversal cost သည် N ပေါ်တွင် မမှီခိုဘဲ degree ပေါ်တွင် မှီခိုသည်
- [ ] Bolt (`bolt://localhost:7687`) နှင့် Neo4j Browser (`7474`) ၏ တာဝန်ကို ခွဲခြားနိုင်သည်
- [ ] `CREATE` နှင့် `MERGE` ၏ idempotency ကွာခြားချက်ကို ရှင်းပြနိုင်သည်
- [ ] Cypher clause အစဉ်သည် strict ဖြစ်သည် — `RETURN` ပြီးနောက် `MATCH` မရ
- [ ] Uniqueness constraint သည် backing index ဖြင့် `MERGE` ကို `NodeIndexSeek` သို့ ရောက်စေသည်
- [ ] Range index နှင့် full-text index ၏ အသုံးပြုပုံ မတူညီသည်
- [ ] `$param` ဖြင့် injection ကာကွယ်သည်; Label/type အတွက် whitelist regex လိုသည်
- [ ] Text-to-Cypher တွင် destructive clause ကို block လုပ်သည် (read-only transaction)
- [ ] Neo4j သင့်/မသင့် ဆုံးဖြတ်ရန် decision criteria ကို ဖော်ပြနိုင်သည်
