# Walkthrough 06 — Driver call sequence simulation (Exercise 6)

> ဤဖိုင်သည် Module 06 ၏ `solution.md` ထဲက Exercise 6 ကို **Python အခြေခံမှ စ၍**
> အပိုင်းလိုက် ရှင်းပြသည့် walkthrough ဖြစ်သည်။ `FakeDriver` / `FakeSession` /
> `FakeResult` သုံးခုသည် real `neo4j` driver ၏ **call sequence** ကို server မလိုဘဲ
> simulate လုပ်သည်။ `neo4j` package ကို lab ထဲ မသုံးရသဖြင့် ဤနည်းကို သုံးသည်။

---

## 0. ဤ Exercise က ဘာကို ဖြေရှင်းပေးသလဲ။

Write path တစ်ခုလုံး၏ နောက်ဆုံးအဆင့်မှာ Python process မှ Neo4j server သို့ ခေါ်သည့်
**call sequence** ဖြစ်သည်။ ဤ sequence မှားလျှင် (session မပိတ်ခြင်း၊ database မှားခြင်း၊
parameter အမည် မှားခြင်း) data မှားသည် သို့မဟုတ် connection pool ကုန်သည်။

```text
GraphDatabase.driver(uri, auth)      ← driver တစ်ခု (application lifecycle တစ်ခုလုံး)
  .verify_connectivity()             ← ချိတ်ဆက်မှု စစ် (တစ်ကြိမ်)
  .session(database="neo4j")         ← session တစ်ခု (context manager)
      .run(query, rows=[...])        ← batch statement တိုင်းအတွက် တစ်ကြိမ် (၅ ကြိမ်)
  (session ပိတ် — __exit__)
  .close()                           ← driver ပိတ်
```

ဤ Exercise က ထို sequence ကို Fake class များဖြင့် အတုလုပ်ပြီး —

- မည်သည့် call မည်မျှ ဖြစ်သည်ကို **မှတ်တမ်းတင်သည်** (`calls` list)
- parameter အမည်များ (`["rows"]`) နှင့် query ၏ ပထမလိုင်းကို စစ်သည်
- batch နည်းလမ်းနှင့် per-triple နည်းလမ်း၏ run call အရေအတွက်ကို နှိုင်းယှဉ်သည်

ဤ code တွင် လေ့လာရမည့် Python concepts များမှာ —

- Class နှစ်ခု ဆက်သွယ်ခြင်း (driver → session → result)
- `**params` (arbitrary keyword arguments) နှင့် `params.get("rows", [])`
- `sorted(dict.keys())` ဖြင့် log ကို deterministic ဖြစ်စေခြင်း
- `str.splitlines()`၊ `str.split(sep, maxsplit)` နှင့် `str.startswith()`
- `__enter__` / `__exit__` — **context manager** protocol
- `enumerate(list, 1)` ဖြင့် စာရင်းရေးခြင်း
- `all(...)` နှင့် generator expression

> **မှတ်ချက်** — ဤအပိုင်းမှ စ၍ snippet များသည် ဤနေရာတွင် သတ်မှတ်သည့် class များနှင့်
> `InMemoryGraph` (Walkthrough 02)၊ `TRIPLES`၊ `build_batch_statements()` (Walkthrough 01)
> တို့ကို သုံးသည်။ Snippet တစ်ခုချင်း run လိုလျှင် Section 8 ရှိ runnable script
> နှင့် ပေါင်းထည့်ရသည်။

---

## 1. `FakeResult` — Server ၏ summary ကို ကိုယ်စားပြုခြင်း
```python
class FakeResult:
    def __init__(self, counters):
        self._counters = counters

    def consume(self):
        return {"counters": self._counters}

    def data(self):
        return []


r = FakeResult({"nodes_created": 5, "relationships_created": 6})
print(r.consume())
print(r.data())
print(r._counters["nodes_created"])
```

Output —
```text
{'counters': {'nodes_created': 5, 'relationships_created': 6}}
[]
5
```

Real driver တွင် `session.run()` သည် **Result** object ကို ပြန်သည်; server ထံမှ
ရလာသည့် summary (created/matched counter များ၊ query plan၊ timing) ကို
`.consume()` ဖြင့် ရသည်။ `.data()` သည် row များကို ပြန်သည် (write query အတွက် အလွတ်)။

Counter ကို `self._counters` ဟု `_` ဖြင့် စထားခြင်းသည် "class အတွင်းသုံး" ဟု ဆိုလိုသည် —
Python တွင် ဤအရာကို private မဖြစ်စေပါ၊ သို့သော် naming convention အရ အပြင်မှ
မထိရန် အချက်ပြသည်။ ဤ walkthrough က `r._counters["nodes_created"]` ကို ဖတ်ပြသည်မှာ
ထို convention ကို ချိုးဖောက်လို့ မဟုတ်ဘဲ အတွင်းတန်ဖိုးကို ပြရန် ဖြစ်သည်။

---
## 2. `FakeSession` — `__init__` နှင့် `run(query, **params)`
```python
class FakeSession:
    def __init__(self, graph, calls, database="neo4j", fetch_size=1000):
        self.graph, self.calls = graph, calls
        self.database, self.fetch_size = database, fetch_size
        self.closed = False

    def run(self, query, **params):
        self.calls.append({"query_head": query.splitlines()[0],
                           "param_keys": sorted(params.keys()),
                           "row_count": len(params.get("rows", []))})
        self._execute(query, params)
        return FakeResult({"nodes_created": 0,
                           "relationships_created": len(params.get("rows", []))})
```
ဖတ်ရန်အပိုင်းများ —

- `self.graph, self.calls = graph, calls` — **tuple unpacking** နှင့် attribute သတ်မှတ်ခြင်း
  တစ်လိုင်းတည်း။ `calls` သည် list ဖြစ်ပြီး **driver နှင့် session နှစ်ခုလုံး တူညီသော
  list object** ကို မျှဝေသုံးသည် (mutable object ကို reference ဖြင့် ပို့သဖြင့်
  session က append လုပ်သည်ကို driver က မြင်သည်)။
- `database="neo4j"` သည် default argument ဖြစ်သည် — parameter မပေးလျှင် ဤတန်ဖိုး ရသည်။
- `def run(self, query, **params)` — `**params` သည် keyword argument အားလုံးကို **dict**
  အဖြစ် စုသည်။ `session.run(cypher, rows=[...])` လို့ ခေါ်လျှင်
  `params == {"rows": [...]}` ဖြစ်သည်။ Parameter အမည်များကို query ထဲက `$rows` နှင့်
  တိတိကျကျ တူညီရမည် — ဤနည်းဖြင့် driver က parameter ကို bind လုပ်သည်။
- `query.splitlines()[0]` — query ၏ ပထမလိုင်း (`UNWIND $rows AS row`) ကို မှတ်သည်။
  Query တစ်ခုလုံးကို log လုပ်လျှင် log ကျယ်လွန်းသဖြင့် ပထမလိုင်း (statement အမျိုးအစား
  ကို ဖော်ပြသည့်လိုင်း) ကိုသာ သိမ်းသည်။
- `sorted(params.keys())` — dict key အစီအစဉ်သည် ထည့်သည့်အစီအစဉ်အတိုင်း ဖြစ်သဖြင့်
  log နှိုင်းယှဉ်ရာတွင် ကစဉ့်ကလျား ဖြစ်နိုင်သည်; `sorted()` က deterministic ဖြစ်စေသည်။
- `params.get("rows", [])` — `rows` မပါလျှင် `[]` ဖြင့် အစားထိုးသည် (`KeyError` မဖြစ်)။
  `len(...)` က row အရေအတွက် ဖြစ်သည်။
- Return သည် `FakeResult` object ဖြစ်သည် — real driver လိုပဲ chaining လုပ်နိုင်ရန်။

### 2.1 Session တစ်ခု ဖန်တီးကြည့်ခြင်း
```python
graph = InMemoryGraph("merge")
calls = []
session = FakeSession(graph, calls, database="neo4j")

print("class      :", session.__class__.__name__)
print("database   :", session.database)
print("fetch_size :", session.fetch_size)
print("closed     :", session.closed)
print("calls shared :", session.calls is calls)
```

Output —
```text
class      : FakeSession
database   : neo4j
fetch_size : 1000
closed     : False
calls shared : True
```

`session.calls is calls` က `True` ဖြစ်သည် — session သည် driver ၏ `calls` list ကို
**တူညီသော object** အဖြစ် သိမ်းထားသည်။ ထို့ကြောင့် session အတွင်း `run()` ခေါ်တိုင်း
driver ၏ `calls` ထဲ ရောက်သွားသည် — ဤနည်းဖြင့် ခေါ်ခဲ့သည့် call အားလုံးကို တစ်နေရာတည်းမှ
ပြန်ကြည့်နိုင်သည်။

### 2.2 `run()` က call ကို မှတ်တမ်းတင်ပြီး graph ကို ပြောင်းလဲခြင်း
```python
statements = build_batch_statements(TRIPLES)
graph = InMemoryGraph("merge")
calls = []
session = FakeSession(graph, calls)

result = session.run(statements[0]["cypher"], rows=statements[0]["rows"])
print("recorded call :", calls[0])
print("result        :", result.consume())
print("graph nodes=%d edges=%d" % (graph.node_count(), graph.edge_count()))
```

Output —
```text
recorded call : {'query_head': 'UNWIND $rows AS row', 'param_keys': ['rows'], 'row_count': 2}
result        : {'counters': {'nodes_created': 0, 'relationships_created': 2}}
graph nodes=2 edges=2
```

မှတ်တမ်းတင်ထားသည့် dict တွင် field ၃ ခု ရှိသည် — `query_head`၊ `param_keys`၊
`row_count`။ ပထမ group (`Person->WORKED_AT->Organization`) တွင် row ၂ ခု ရှိသဖြင့်
`row_count` က 2 ဖြစ်သည်။

`result.consume()` က `{"counters": {"nodes_created": 0, "relationships_created": 2}}`
ပြန်သည်ကို သတိပြုပါ — **`nodes_created` က 0 ဖြစ်သည်**။ ဤသည်မှာ simulation ၏
အတုတန်ဖိုး ဖြစ်သည် — `simulation` က node property များကို `InMemoryGraph` ထဲ
ရေးသည်သာ ဖြစ်ပြီး server counter ကို တွက်ခြင်း မရှိပါ။ ထို့ကြောင့် **counter များကို
simulation မှ မယူရ** — ဤ walkthrough တွင် အရေအတွက်များကို `graph.node_count()` /
`graph.edge_count()` နှင့် `calls` list မှ ရသည်။ Real server တွင် counter မှာ
`summary.counters.nodes_created` ဖြစ်သည် (အောက် Section 9)။

---
## 3. `_execute()` — Query လိုင်းများကို ဖတ်ခြင်း
Simulation က query string ကို **ပြန်ဖတ်** ပြီး label/type ကို ဆွဲထုတ်သည် —
ဤအလုပ်ကို real server က parser ဖြင့် လုပ်သည်။ ဤနေရာတွင် `startswith()` နှင့်
`split(sep, 1)` ဖြင့် လုပ်သည်။
```python
line = "MERGE (h:Person {id: row.head_id})"
print(line.startswith("MERGE (h:"), "{" in line)
print(line.split("MERGE (h:", 1)[1].split()[0])

rel = "MERGE (h)-[r:WORKED_AT {chunk_id: row.chunk_id}]->(t)"
print(rel.split("MERGE (h)-[r:", 1)[1].split()[0])

print("no prefix ->", "MERGE (h:Person".split("MERGE (t:", 1))
```

Output —
```text
True True
Person
WORKED_AT
no prefix -> ['MERGE (h:Person']
```

`split("MERGE (h:", 1)` — `maxsplit=1` သည် အပိုင်း **နှစ်ခု** သာ ခွဲသည် (ပထမတွေ့သည့်
နေရာတွင်သာ)။ `[1]` က ညာဘက်အပိုင်း (`Person {id: row.head_id})`) ကို ယူသည်။
`.split()[0]` က space ဖြင့် ထပ်ခွဲပြီး ပထမစကားလုံး (`Person`) ကို ယူသည်။
`maxsplit` မပါလျှင် (သို့) `[1]` ကို မသုံးလျှင် query ထဲတွင် prefix နှစ်ကြိမ်ပါလာသည့်အခါ
အပိုင်း ၃ ခု ဖြစ်ပြီး ရလဒ် မှားနိုင်သည်။

`"MERGE (h:Person".split("MERGE (t:", 1)` က `['MERGE (h:Person']` — အပိုင်း **၁ ခု**သာ
ရသည် (separator မတွေ့လို့)။ ထို့ကြောင့် `[1]` ဖြင့် ဖတ်လျှင် error ဖြစ်သည် —
အောက်တွင် ပြထားသည်။
```python
try:
    "MERGE (a)-[:R]->(b)".split("MERGE (h:", 1)[1]
except IndexError as exc:
    print("no prefix -> %s: %s" % (type(exc).__name__, exc))

try:
    "MERGE (h:".split("MERGE (h:", 1)[1].split()[0]
except IndexError as exc:
    print("empty tail -> %s: %s" % (type(exc).__name__, exc))
```

Output —
```text
no prefix -> IndexError: list index out of range
empty tail -> IndexError: list index out of range
```

Prefix မတွေ့လျှင် `IndexError: list index out of range` ဖြစ်သည်။ ထို့ကြောင့်
`_execute()` က လိုင်းတိုင်းကို `startswith()` ဖြင့် **အရင် စစ်** ပြီးမှ `split()` လုပ်သည် —

```python
if line.startswith("MERGE (h:") and "{" in line:
    head_label = line.split("MERGE (h:", 1)[1].split()[0]
elif line.startswith("MERGE (t:") and "{" in line:
    tail_label = line.split("MERGE (t:", 1)[1].split()[0]
elif line.startswith("MERGE (h)-[r:"):
    rel_type = line.split("MERGE (h)-[r:", 1)[1].split()[0]
```

`line.startswith("MERGE (h:")` နှင့် `line.startswith("MERGE (h)-[r:")` နှစ်ခုလုံးသည်
`MERGE (h` ဖြင့် စသည်ကို သတိပြုပါ။ ပထမ branch တွင် `and "{" in line` ပါသဖြင့်
relationship လိုင်း (`MERGE (h)-[r:WORKED_AT {…}`) သည် `"{" in line` ဖြစ်သည်ဖြစ်သော်လည်း
`"MERGE (h:"` (colon ပါ) နှင့် မကိုက်ညီပါ — `MERGE (h)` ဖြစ်သည်။ ဤအချက်ကြောင့် branch
နှစ်ခု တိုက်ခြင်း မရှိပါ။ `elif` အစီအစဉ်သည် ဤနေရာတွင် အရေးကြီးသည်။

မည်သည့် branch မှ မကိုက်ညီလျှင် `head_label` သည် `None` ဖြစ်ကျန်ပြီး graph ထဲ
`None` label ရေးမည် — real Cypher တွင် label မရှိသော node ဖြစ်သည် (`MERGE (a)-[:R]->(b)`
trap နှင့် တူညီသည်)။ ထို့ကြောင့် simulation ကိုယ်တိုင် query format ကို အာမခံ
ဖို့ လိုသည် — Section 7 ၏ `assert` များ (`all(c["query_head"] == "UNWIND $rows AS row")`)
သည် ဤအာမခံချက် ဖြစ်သည်။

---
## 4. Context Manager — `__enter__` နှင့် `__exit__`
`with` statement သည် object တစ်ခုကို ဖွင့်ပြီး **မည်သို့ပဲ ဖြစ်ဖြစ်** ပိတ်စေသည် —
exception ဖြစ်လျှင်လည်း `__exit__` run သည်။ ဤသည်မှာ session/connection များ
မပိတ်ဘဲ ကျန်ခြင်းကို ကာကွယ်သည့် အခြေခံ mechanism ဖြစ်သည်။
```python
class Demo:
    def __enter__(self):
        print("  __enter__ called")
        return self

    def __exit__(self, exc_type, exc, tb):
        print("  __exit__ called, exc_type=%s" % exc_type)
        return False


with Demo() as d:
    print("  body runs, d is the object:", d.__class__.__name__)

try:
    with Demo():
        raise ValueError("boom")
except ValueError:
    print("  exception propagated (return False)")
```

Output —
```text
  __enter__ called
  body runs, d is the object: Demo
  __exit__ called, exc_type=None
  __enter__ called
  __exit__ called, exc_type=<class 'ValueError'>
  exception propagated (return False)
```

`__enter__` သည် with body တွင် ရမည့် object ကို ပြန်သည် (`as d`); ဤနေရာတွင်
`return self` ဖြစ်သဖြင့် `d is` မူရင်း object ဖြစ်သည်။ `__exit__` သည် argument
၃ ခု (`exc_type`, `exc`, `tb`) ကို လက်ခံသည်။ `return False` သည် "exception ကို
မဖမ်းဘူး" ဟု ဆိုလိုသည် — ထို့ကြောင့် `ValueError` သည် propagate ဖြစ်ပြီး
အပြင်ဘက် `except` က ဖမ်းသည်။ `return True` ပြန်လျှင် exception ကို ဖျောက်လိုက်မည် —
ထို case ကို ဤ code တွင် မလိုချင်ပါ။

### 4.1 `FakeSession` ၏ context manager
```python
    def close(self):
        self.closed = True

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        self.close()
        return False
```

`close()` ကို `__exit__` မှ ခေါ်ခြင်းသည် **single place to close** ဖြစ်သည် —
body ထဲတွင် error ဖြစ်လျှင်လည်း `closed = True` ဖြစ်သည်။
```python
graph = InMemoryGraph("merge")
calls = []
session = FakeSession(graph, calls)

print("before with :", session.closed)
with session as s:
    print("inside with :", s.closed, "| same object:", s is session)
print("after with  :", session.closed)
```

Output —
```text
before with : False
inside with : False | same object: True
after with  : True
```

`with` ထဲဝင်လျှင် `__enter__` က `self` ကို ပြန်သဖြင့် `s is session` ဖြစ်သည်
(`True`)။ ထွက်လျှင် `session.closed` က `True` ဖြစ်သည်။

Real driver တွင် `driver.session()` ကို `with` ဖြင့် သုံးခြင်းသည် session ကို
connection pool သို့ ပြန်အပ်စေသည် — မပိတ်ဘဲ ကျန်လျှင် pool ကုန်ပြီး
`ServiceUnavailable` ဖြစ်သည်။ ထို့ကြောင့် `session.run(...)` တစ်ခုချင်း ခေါ်ပြီး
ပိတ်ခြင်းထက် **session တစ်ခုထဲတွင် statement အားလုံး ပို့ခြင်း** သည် connection
setup cost ကို လျှော့စေသည် (ဤ Exercise က ဤနည်းကို သုံးသည်)။

---
## 5. `FakeDriver` — URI၊ auth နှင့် session ဖန်တီးခြင်း
```python
class FakeDriver:
    def __init__(self, uri, auth, graph=None, calls=None):
        self.uri, self.auth, self.graph = uri, auth, graph
        self.calls = calls if calls is not None else []
        self.verified = 0
        self.closed = False

    def verify_connectivity(self):
        self.verified += 1

    def session(self, database=None, **kwargs):
        return FakeSession(self.graph, self.calls, database=database or "neo4j")

    def close(self):
        self.closed = True
```
ဖတ်ရန်အပိုင်းများ —

- `def __init__(self, uri, auth, graph=None, calls=None)` — `graph`/`calls` ကို optional
  ထားသည်; `calls if calls is not None else []` သည် "default argument ကို mutable
  object ဖြစ်စေခြင်း" ဆိုသည့် trap ကို ရှောင်သည့် ရေးထုံးဖြစ်သည်။
  (`def f(x=[])` လို့ ရေးလျှင် list တစ်ခုတည်းကို call အားလုံး မျှဝေသုံးမည် — bug
  ဖြစ်သည်။)
- `verify_connectivity()` — call အရေအတွက်ကို counter (`self.verified`) ဖြင့် မှတ်သည်။
- `session(database=None, **kwargs)` — `database or "neo4j"` သည် `None` သို့မဟုတ် `""`
  ဖြစ်လျှင် `"neo4j"` ကို ယူသည်။
```python
graph = InMemoryGraph("merge")
driver = FakeDriver("bolt://localhost:7687", ("neo4j", "graphrag123"), graph=graph)

driver.verify_connectivity()
driver.verify_connectivity()
print("verify calls :", driver.verified)

session = driver.session(database="graph")
print("session db   :", session.database)

driver.close()
print("driver closed:", driver.closed)
```

Output —
```text
verify calls : 2
session db   : graph
driver closed: True
```

`verify_connectivity()` ကို နှစ်ကြိမ် ခေါ်သဖြင့် `verified` က 2 ဖြစ်သည် — counter
သည် **ခေါ်ခဲ့သည့် အရေအတွက်** ဖြစ်သည်၊ bool မဟုတ်ပါ။ ဤအချက်သည် test ရေးရာတွင်
အသုံးဝင်သည်: "တစ်ကြိမ်သာ ခေါ်သည်" ဆိုသည့် အာမခံချက်ကို `driver.verified == 1` ဖြင့်
စစ်သည်။ Production တွင် `verify_connectivity()` ကို application startup အချိန်တွင်
**တစ်ကြိမ်** ခေါ်ရသည် — request တိုင်း ခေါ်လျှင် round-trip ပိုသည်။

---
## 6. `run_write_transaction()` — Sequence တစ်ခုလုံး
```python
def run_write_transaction(driver, statements):
    """Mirrors GraphDatabase.driver -> session(database) -> run(query, **params)."""
    driver.verify_connectivity()
    with driver.session(database="neo4j") as session:
        for st in statements:
            session.run(st["cypher"], rows=st["rows"])
    driver.close()
    return driver
```
Sequence သည် real driver နှင့် လုံးဝ တူညီသည် —

1. `driver.verify_connectivity()` — အရင် စစ်သည် (fail-fast)။
2. `with driver.session(database="neo4j") as session:` — session ဖွင့်ပြီး body
   ပြီးသည်နှင့် အလိုအလျောက် ပိတ်သည်။
3. `for st in statements: session.run(st["cypher"], rows=st["rows"])` — batch တိုင်းအတွက်
   တစ်ကြိမ်။ `rows=` သည် keyword argument ဖြစ်သဖြင့် `params == {"rows": ...}` ဖြစ်ပြီး
   query ထဲက `$rows` နှင့် ကိုက်ညီသည်။
4. `driver.close()` — driver ကို ပိတ်သည်။

`session.run()` မှ ပြန်လာသည့် response object ကို ဤနေရာတွင် **မဖတ်**ပါ — write query ၏
ရလဒ်ကို မလိုအပ်လို့ဖြစ်သည်။ Real server တွင် counter လိုလျှင် `.consume()` ဖြင့်
ဖတ်ရသည်။
```python
statements = build_batch_statements(TRIPLES)
graph = InMemoryGraph("merge")
driver = FakeDriver("bolt://localhost:7687", ("neo4j", "graphrag123"), graph=graph)
run_write_transaction(driver, statements)

print("uri=%s  auth=(%s, ***)" % (driver.uri, driver.auth[0]))
print("verify_connectivity calls=%d" % driver.verified)
print("session.run calls=%d" % len(driver.calls))
for i, call in enumerate(driver.calls, 1):
    print("  %d) %s params=%s rows=%d"
          % (i, call["query_head"], call["param_keys"], call["row_count"]))
print("graph nodes=%d edges=%d" % (graph.node_count(), graph.edge_count()))
print("driver closed=%s" % driver.closed)
```

Output —
```text
uri=bolt://localhost:7687  auth=(neo4j, ***)
verify_connectivity calls=1
session.run calls=5
  1) UNWIND $rows AS row params=['rows'] rows=2
  2) UNWIND $rows AS row params=['rows'] rows=1
  3) UNWIND $rows AS row params=['rows'] rows=1
  4) UNWIND $rows AS row params=['rows'] rows=1
  5) UNWIND $rows AS row params=['rows'] rows=1
graph nodes=5 edges=6
driver closed=True
```

ရလဒ်ကို ဇယားဖြင့် (အထက်က run ၏ အမှန်တကယ် တန်ဖိုးများ) —

| အဆင့် | Call | အရေအတွက် |
| --- | --- | --- |
| 1 | `verify_connectivity()` | 1 |
| 2 | `session(database="neo4j")` | 1 |
| 3 | `session.run(query, rows=…)` | 5 (batch ၅ ခု) |
| 4 | `session.close()` | 1 (`with` မှ အလိုအလျောက်) |
| 5 | `driver.close()` | 1 |

Real driver တွင် tx ကို `session.run()` တစ်ကြိမ်လျှင် တစ်ခု ဖွင့်သည် (auto-commit)။
Statement အားလုံးကို transaction **တစ်ခုတည်း** ထဲတွင် လိုချင်လျှင်
`session.execute_write(fn)` ကို သုံးရသည် — ထို case တွင် statement တစ်ခု ပျက်လျှင်
အားလုံး rollback ဖြစ်သည်။ Trade-off ကို Exercise 5 တွင် တွက်ချက်ထားသည်။

---
## 7. Batch နှင့် Per-triple နည်းလမ်း နှိုင်းယှဉ်ခြင်း
```python
statements = build_batch_statements(TRIPLES)
graph = InMemoryGraph("merge")
driver = FakeDriver("bolt://localhost:7687", ("neo4j", "graphrag123"), graph=graph)
run_write_transaction(driver, statements)

batched_calls = len(driver.calls)
per_triple_calls = len(TRIPLES)
print("batched run calls    = %d" % batched_calls)
print("per-triple run calls = %d" % per_triple_calls)
print("reduction            = %.1fx" % (per_triple_calls / batched_calls))
print("all heads UNWIND     = %s"
      % all(c["query_head"] == "UNWIND $rows AS row" for c in driver.calls))
print("all param keys rows  = %s" % all(c["param_keys"] == ["rows"] for c in driver.calls))
```

Output —
```text
batched run calls    = 5
per-triple run calls = 6
reduction            = 1.2x
all heads UNWIND     = True
all param keys rows  = True
```

| နည်းလမ်း | run calls | ရေးသည့် row | မှတ်ချက် |
| --- | --- | --- | --- |
| batched (`UNWIND`) | 5 | 6 | group တိုင်းအတွက် တစ်ကြိမ် |
| per-triple | 6 | 6 | triple တိုင်းအတွက် တစ်ကြိမ် |

Per-triple ၏ run call အရေအတွက်သည် triple အရေအတွက် (`len(TRIPLES)`) နှင့် တူညီသည် —
triple တိုင်းအတွက် statement တစ်ခု ပို့သဖြင့် ဖြစ်သည်။ ဤ module ၏ sample သေးငယ်သဖြင့်
5 နှင့် 6 သာ ကွာသည်; triplet သောင်းနှင့်ချီ ဖြစ်လျှင် batched နည်းလမ်းသည်
label-pair × relationship type အရေအတွက်ခန့်သာ call ဖြစ်သည် — အရေအတွက် ကွာခြားချက်သည်
အရေအတွက် အစီအစဉ် (order of magnitude) ဖြစ်လာသည်။

`all(...)` နှစ်လိုင်းသည် ခေါ်ခဲ့သည့် query အားလုံး မှန်ကန်ကြောင်း အာမခံသည် —
ပထမလိုင်းသည် query တိုင်း `UNWIND $rows AS row` ဖြင့် စသည်ကို၊ ဒုတိယသည် parameter
key သည် `["rows"]` တစ်ခုတည်း ဖြစ်သည်ကို စစ်သည်။ Parameter အမည် တစ်လုံး မှားလျှင်
real server သည် `ParameterMissing` ဖြင့် ကျရှုံးသည် — ထို error ကို server မလိုဘဲ
client-side တွင် ဖမ်းလိုက်ခြင်း ဖြစ်သည်။

---
## 8. Code တစ်ခုလုံး — Run လုပ်နိုင်သော Version
```python
from collections import OrderedDict

ENTITY_TYPE_TO_LABEL = {"PERSON": "Person", "ORGANIZATION": "Organization",
                        "TECHNOLOGY": "Technology", "LOCATION": "Location"}

TRIPLES = [
    {"head": "Ada Lovelace", "head_type": "PERSON", "rel": "WORKED_AT",
     "tail": "Analytical Engine Project", "tail_type": "ORGANIZATION",
     "chunk_id": "c01", "confidence": 0.93},
    {"head": "Ada Lovelace", "head_type": "PERSON", "rel": "USES",
     "tail": "Analytical Engine", "tail_type": "TECHNOLOGY",
     "chunk_id": "c01", "confidence": 0.88},
    {"head": "Charles Babbage", "head_type": "PERSON", "rel": "FOUNDED",
     "tail": "Analytical Engine Project", "tail_type": "ORGANIZATION",
     "chunk_id": "c02", "confidence": 0.91},
    {"head": "Analytical Engine Project", "head_type": "ORGANIZATION",
     "rel": "LOCATED_IN", "tail": "London", "tail_type": "LOCATION",
     "chunk_id": "c03", "confidence": 0.76},
    {"head": "Ada Lovelace", "head_type": "PERSON", "rel": "COLLABORATED_WITH",
     "tail": "Charles Babbage", "tail_type": "PERSON",
     "chunk_id": "c02", "confidence": 0.84},
    {"head": "Ada Lovelace", "head_type": "PERSON", "rel": "WORKED_AT",
     "tail": "Analytical Engine Project", "tail_type": "ORGANIZATION",
     "chunk_id": "c04", "confidence": 0.79},
]

def slug(text):
    """Canonical node id — deterministic, lowercase, ASCII-safe."""
    return "".join(ch if ch.isalnum() else "_" for ch in text.lower()).strip("_")

def build_batch_statements(triples):
    """Group triples by (head label, rel type, tail label): one UNWIND batch each."""
    groups = OrderedDict()
    for t in triples:
        key = (ENTITY_TYPE_TO_LABEL[t["head_type"]], t["rel"],
               ENTITY_TYPE_TO_LABEL[t["tail_type"]])
        groups.setdefault(key, []).append(t)
    statements = []
    for (head_label, rel_type, tail_label), items in groups.items():
        rows = [OrderedDict([("head_id", slug(t["head"])),
                             ("head_name", t["head"]),
                             ("tail_id", slug(t["tail"])),
                             ("tail_name", t["tail"]),
                             ("chunk_id", t["chunk_id"]),
                             ("confidence", t["confidence"])]) for t in items]
        cypher = (
            "UNWIND $rows AS row\n"
            "MERGE (h:{hl} {{id: row.head_id}})\n"
            "  ON CREATE SET h.name = row.head_name\n"
            "MERGE (t:{tl} {{id: row.tail_id}})\n"
            "  ON CREATE SET t.name = row.tail_name\n"
            "MERGE (h)-[r:{rel} {{chunk_id: row.chunk_id}}]->(t)\n"
            "  ON CREATE SET r.confidence = row.confidence\n"
            "  ON MATCH SET r.confidence = row.confidence"
        ).format(hl=head_label, tl=tail_label, rel=rel_type)
        statements.append({"group": (head_label, rel_type, tail_label),
                           "cypher": cypher, "rows": rows})
    return statements

class InMemoryGraph:
    """semantics='merge' dedupes by identity key (MERGE); 'create' appends blindly."""

    def __init__(self, semantics="merge"):
        self.semantics = semantics
        self.node_keys, self.edge_keys = [], []
        self.node_props, self.edge_props = {}, {}
        self.stats = {"nodes_created": 0, "nodes_matched": 0,
                      "edges_created": 0, "edges_matched": 0}

    def write_node(self, label, node_id, name):
        key = (label, node_id)
        if self.semantics == "merge" and key in self.node_props:
            self.stats["nodes_matched"] += 1
            self.node_props[key]["name"] = name
            return
        self.stats["nodes_created"] += 1
        self.node_keys.append(key)
        self.node_props.setdefault(key, {"label": label, "id": node_id, "name": name})

    def write_edge(self, head_label, head_id, rel_type, tail_label, tail_id,
                   chunk_id, confidence):
        key = (head_label, head_id, rel_type, tail_label, tail_id, chunk_id)
        if self.semantics == "merge" and key in self.edge_props:
            self.stats["edges_matched"] += 1
            self.edge_props[key] = confidence
            return
        self.stats["edges_created"] += 1
        self.edge_keys.append(key)
        self.edge_props[key] = confidence

    def node_count(self):
        return len(self.node_keys)

    def edge_count(self):
        return len(self.edge_keys)


def apply_batch(graph, statements):
    for st in statements:
        head_label, rel_type, tail_label = st["group"]
        for row in st["rows"]:
            graph.write_node(head_label, row["head_id"], row["head_name"])
            graph.write_node(tail_label, row["tail_id"], row["tail_name"])
            graph.write_edge(head_label, row["head_id"], rel_type, tail_label,
                             row["tail_id"], row["chunk_id"], row["confidence"])

class FakeResult:
    def __init__(self, counters):
        self._counters = counters

    def consume(self):
        return {"counters": self._counters}

    def data(self):
        return []

class FakeSession:
    def __init__(self, graph, calls, database="neo4j", fetch_size=1000):
        self.graph, self.calls = graph, calls
        self.database, self.fetch_size = database, fetch_size
        self.closed = False

    def run(self, query, **params):
        self.calls.append({"query_head": query.splitlines()[0],
                           "param_keys": sorted(params.keys()),
                           "row_count": len(params.get("rows", []))})
        self._execute(query, params)
        return FakeResult({"nodes_created": 0,
                           "relationships_created": len(params.get("rows", []))})

    def _execute(self, query, params):
        head_label = tail_label = rel_type = None
        for line in query.splitlines():
            if line.startswith("MERGE (h:") and "{" in line:
                head_label = line.split("MERGE (h:", 1)[1].split()[0]
            elif line.startswith("MERGE (t:") and "{" in line:
                tail_label = line.split("MERGE (t:", 1)[1].split()[0]
            elif line.startswith("MERGE (h)-[r:"):
                rel_type = line.split("MERGE (h)-[r:", 1)[1].split()[0]
        for row in params.get("rows", []):
            self.graph.write_node(head_label, row["head_id"], row["head_name"])
            self.graph.write_node(tail_label, row["tail_id"], row["tail_name"])
            self.graph.write_edge(head_label, row["head_id"], rel_type, tail_label,
                                  row["tail_id"], row["chunk_id"], row["confidence"])

    def close(self):
        self.closed = True

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        self.close()
        return False

class FakeDriver:
    def __init__(self, uri, auth, graph=None, calls=None):
        self.uri, self.auth, self.graph = uri, auth, graph
        self.calls = calls if calls is not None else []
        self.verified = 0
        self.closed = False

    def verify_connectivity(self):
        self.verified += 1

    def session(self, database=None, **kwargs):
        return FakeSession(self.graph, self.calls, database=database or "neo4j")

    def close(self):
        self.closed = True

def run_write_transaction(driver, statements):
    """Mirrors GraphDatabase.driver -> session(database) -> run(query, **params)."""
    driver.verify_connectivity()
    with driver.session(database="neo4j") as session:
        for st in statements:
            session.run(st["cypher"], rows=st["rows"])
    driver.close()
    return driver

statements = build_batch_statements(TRIPLES)
graph = InMemoryGraph("merge")
driver = FakeDriver("bolt://localhost:7687", ("neo4j", "graphrag123"), graph=graph)
run_write_transaction(driver, statements)

print("uri=%s  auth=(%s, ***)" % (driver.uri, driver.auth[0]))
print("verify_connectivity calls=%d" % driver.verified)
print("session.run calls=%d" % len(driver.calls))
for i, call in enumerate(driver.calls, 1):
    print("  %d) %s params=%s rows=%d"
          % (i, call["query_head"], call["param_keys"], call["row_count"]))
naive_calls = len(TRIPLES)
print("batched run calls=%d vs per-triple run calls=%d"
      % (len(driver.calls), naive_calls))
```

Output —
```text
uri=bolt://localhost:7687  auth=(neo4j, ***)
verify_connectivity calls=1
session.run calls=5
  1) UNWIND $rows AS row params=['rows'] rows=2
  2) UNWIND $rows AS row params=['rows'] rows=1
  3) UNWIND $rows AS row params=['rows'] rows=1
  4) UNWIND $rows AS row params=['rows'] rows=1
  5) UNWIND $rows AS row params=['rows'] rows=1
batched run calls=5 vs per-triple run calls=6
```

---
## 9. Live driver — Simulation နှင့် ကွာခြားချက်

အောက်က code သည် real `neo4j` Python driver ကို သုံးသည်။ **ဤ code ကို ဤ walkthrough
တွင် run မထားပါ** (`neo4j` package လိုအပ်သဖြင့် lab ထဲ မထည့်ရ — WRITING_RULES §၃.၅)။
Repo ၏ `docker-compose.yml` ဖြင့် Neo4j 5 Community (Bolt `7687`၊ Browser `7474`၊
`neo4j` / `graphrag123`) တင်ပြီးမှ run နိုင်သည်။
```python
from neo4j import GraphDatabase

driver = GraphDatabase.driver("bolt://localhost:7687", auth=("neo4j", "graphrag123"))
driver.verify_connectivity()

with driver.session(database="neo4j") as session:
    for statement in statements:
        summary = session.run(statement["cypher"], rows=statement["rows"]).consume()
        print(summary.counters.nodes_created, summary.counters.relationships_created)

driver.close()
```
Simulation က အာမခံသည့်အရာ —

- call sequence (`verify_connectivity` → session → run → close)
- parameter အမည် (`$rows` ↔ `rows=`)
- generate လုပ်ထားသည့် Cypher ၏ ပုံစံ

Simulation က **မအာမခံနိုင်သည့်အရာ** —

- Cypher syntax မှန်မမှန် (server parser သာ အာမခံသည်)
- constraint enforcement နှင့် index query plan
- transaction isolation နှင့် concurrent write အပြုအမူ
- `summary.counters` ၏ တကယ့်တန်ဖိုး (simulation က `nodes_created` ကို 0 ဟု အတုပြန်သည်)

Production စည်းကမ်း —

1. Credential ကို environment variable မှ ဖတ်ရသည် (`os.environ["NEO4J_PASSWORD"`) —
   code ထဲ တိုက်ရိုက် မရေးရ။
2. Driver ကို application lifecycle တစ်ခုလုံးအတွက် **တစ်ခုတည်း** ထားရှိပြီး
   process ပိတ်သည့်အခါ `close()` ခေါ်ရသည်။ Request တိုင်း driver အသစ် ဖန်တီးလျှင်
   connection setup cost ကို ထပ်ခါတလဲလဲ ပေးရသည်။
3. `retry` လိုအပ်သည့် write အတွက် `session.execute_write(fn)` ကို သုံးရသည် —
   transient error တွင် driver က အလိုအလျောက် ပြန်ကြိုးစားပေးသည်။

---
## 10. ကိုယ်တိုင်လေ့ကျင့်ကြည့်ပါ

**မေးခွန်း** — statement ၃ ခု (`statements[:3]` — WORKED_AT row ၂၊ USES row ၁၊ FOUNDED
row ၁) ကို `run_write_transaction()` ဖြင့် ပို့လျှင် `session.run` မည်မျှ ခေါ်မည်၊
parameter key များက ဘာဖြစ်မည်၊ graph ထဲ node ဘယ်နှစ်ခု ရောက်မည်။
```python
statements = build_batch_statements(TRIPLES)[:3]
graph = InMemoryGraph("merge")
driver = FakeDriver("bolt://localhost:7687", ("neo4j", "graphrag123"), graph=graph)
run_write_transaction(driver, statements)

print("run calls  =", len(driver.calls))
print("param keys =", driver.calls[0]["param_keys"])
print("query head =", driver.calls[0]["query_head"])
print("nodes=%d edges=%d" % (graph.node_count(), graph.edge_count()))
```

1. run call ၁၊ key `["rows", "cypher"]`၊ node ၄
2. run call ၃၊ key `["rows"]`၊ node ၄
3. run call ၆၊ key `["rows"]`၊ node ၅
4. run call ၃၊ key `["rows"]`၊ node ၅

<details>
<summary>အဖြေ ကြည့်ရန်</summary>

**အဖြေ — 2. run call ၃၊ key `["rows"]`၊ node ၄**

အကြောင်းရင်း —

- `run_write_transaction()` သည် statement တိုင်းအတွက် `session.run()` တစ်ကြိမ် ခေါ်သဖြင့်
  statement ၃ ခုအတွက် run call 3 ကြိမ် (per-triple မဟုတ်ပါ)။
- `session.run(st["cypher"], rows=st["rows"])` လို့ ခေါ်သဖြင့် `**params` ထဲ ပါဝင်သည့်
  key သည် `rows` တစ်ခုတည်း။
- Statement ၃ ခုက row ၂ + ၁ + ၁ = 4 ခု ကို write လုပ်သည်။ Row များမှ ရသည့် node များမှာ
  `ada_lovelace`၊ `analytical_engine_project`၊ `analytical_engine`၊ `charles_babbage` —
  ထူးခြား node ၄ ခု (`London` သည် `LOCATED_IN` group ထဲမှာသာ ပါသဖြင့် မပါဝင်ပါ)။

အထက်က run ၏ output က `run calls = 3`၊ `param keys = ['rows']`၊ `nodes=4 edges=4`
ဖြစ်ကြောင်း အတည်ပြုသည်။

</details>

---

**အဓိက မှတ်ထားရန်** — Offline simulation သည် **call sequence**၊ parameter အမည် နှင့်
Cypher generation ကို အာမခံသည်; server-side behaviour (syntax validation၊ constraint
enforcement၊ index query plan၊ transaction isolation) ကို မအာမခံနိုင်ပါ။ Driver ကို
application lifecycle တစ်ခုလုံးအတွက် တစ်ခုတည်း ထားရှိပြီး session ကို `with` ဖြင့်
ပိတ်ရသည် — session တစ်ခုတည်းထဲ statement အားလုံး ပို့ခြင်းသည် connection setup cost ကို
လျှော့စေသည်။ Credential ကို environment variable မှ ဖတ်ရပြီး server behaviour ကို
အာမခံလိုသည့်အခါတိုင်း Neo4j instance ပေါ်တွင် integration test ဖြင့် စစ်ရမည်။
