# Walkthrough 03 — Subgraph → Prompt Context Serialization (Exercise 3)

> ဤဖိုင်သည် Module 07 ၏ `solution.md` ထဲက Exercise 3 ကို **Python အခြေခံမှ စ၍**
> အပိုင်းလိုက် ရှင်းပြသည့် walkthrough ဖြစ်သည်။ Format သည် Module 01 ၏
> `walkthroughs/01_regex_ner.md` နှင့် `walkthroughs/03_gazetteer_lookup.md` နှင့်
> တူညီသည်။

---

## 0. ဤ Exercise က ဘာကို ဖြေရှင်းပေးသလဲ။

Exercise 2 က `(node_ids, edge_indexes)` ကို ပြန်ပေးသည် — Python data structure
ဖြစ်သည်။ သို့သော် **LLM သည် Python data structure ကို မဖတ်နိုင်ပါ**၊ စာသားကို
သာ ဖတ်နိုင်သည်။ ဤကွက်လပ်ကို ဖြည့်သည့် အလုပ်သည် **serialization** ဖြစ်သည် —
subgraph ကို prompt context စာသားအဖြစ် ပြောင်းခြင်း ဖြစ်သည်။

```text
subgraph (Exercise 2)
  nodes: co:neo4j, org:neo4jeng, prod:aura, tech:cypher,
         tech:graphrag, tech:vectorindex
  edges: 8 triple (index 0..7)
        |
        |  serialize_subgraph()
        v
prompt context (စာသား 14 လိုင်း၊ ~256 token)
  [ENTITY]   id=co:neo4j | label=Company | name=Neo4j | summary=...
  ...
  [RELATION] co:neo4j -[CREATES]-> tech:cypher
  ...
```

Format ကို **တိတိကျကျ သတ်မှတ်**ထားခြင်း၏ အကျိုးနှစ်ခု ရှိသည် —

1. **LLM အတွက် ဖတ်ရလွယ်ခြင်း** — entity နှင့် relation ကို marker (`[ENTITY]`၊
   `[RELATION]`) ဖြင့် ခွဲထားသဖြင့် "ဤ node များ တည်ရှိသည်" နှင့် "ဤ node များ
   ဆက်စပ်သည်" ဆိုသည့် အချက်နှစ်ခုကို ခွဲခြားဖတ်နိုင်သည်။
2. **Prompt caching** — sort order ကို သတ်မှတ်ထားသဖြင့် subgraph တူညီလျှင်
   prefix လည် တူညီသည်။ Prompt caching သည် prefix တူညီမှသာ cache hit ဖြစ်သည်။

ဤ code မှာ လေ့လာရမည့် Python concepts များမှာ —

- **f-string** (`f"[ENTITY] id={node_id} | ..."`)
- Tuple unpacking တွင် `_` prefix convention
- `"\n".join(list)` (list → စာသားတစ်ခု)
- `itertools.groupby()` — **sorted လုပ်ပြီးမှသာ သုံးနိုင်သည်**
- `sorted(..., key=lambda e: (e[0], e[1], e[2]))` — tuple sort key
- List `+=` (extend) နှင့် list comprehension
- Integer division `//`
- Conditional expression (`X if cond else Y`)

---

## 1. `[ENTITY]` Line — f-string ဖြင့် တည်ဆောက်ခြင်း

```python
NODES = {
    "co:neo4j": ("Company", "Neo4j", ("Neo4j Inc", "Neo4j, Inc."), "Graph database vendor."),
}
node_id = "co:neo4j"
label, name, _aliases, summary = NODES[node_id]
print(f"[ENTITY] id={node_id} | label={label} | name={name} | summary={summary}")
```

Output —

```text
[ENTITY] id=co:neo4j | label=Company | name=Neo4j | summary=Graph database vendor.
```

### 1.1 f-string ဆိုတာ ဘာလဲ

`f"..."` ဖြင့် စသည့် string တွင် `{variable}` ရေးလျှင် ထို variable ၏ တန်ဖိုး
အစားထိုး ခံရသည်။ `f"[ENTITY] id={node_id}"` သည် `node_id` ၏ တန်ဖိုး `co:neo4j`
ကို ထည့်သည်။ Braces အပြင်ဘက် စာသား (`[ENTITY] id=`, ` | label=`) သည်
**literal** အတိုင်း ကျန်သည်။

`|` (pipe) သည် ဒီနေရာတွင် **ကြားခံလက္ခဏာ** သာဖြစ်သည် — regex မဟုတ်၊ table
syntax မဟုတ်ပါ။ LLM အတွက် field များကို ခွဲပေးသည့် separator အဖြစ် သုံးသည်။

### 1.2 `label, name, _aliases, summary = NODES[node_id]`

`NODES[node_id]` သည် 4-tuple ဖြစ်သည်။ ဘယ်ဘက်တွင် variable ၄ ခု ထားသဖြင့်
တစ်ခုချင်း ခွဲယူသည်။ ဤနေရာတွင် alias ကို မလိုသဖြင့် `_aliases` လို့ နာမည်ပေးသည် —
`_` prefix သည် "ဖတ်သူအား ဤ variable ကို ရည်ရွယ်ချက်ရှိရှိ မသုံးပါ" ဟု ပြသည့်
convention ဖြစ်သည်။ **`_aliases` ကို ဖယ်လို့မရပါ** — tuple တွင် element ၄ ခု
ရှိသဖြင့် variable ၄ ခု လိုသည်၊ မဟုတ်လျှင် `ValueError: too many values to
unpack` ဖြစ်သည်။

### 1.3 Entity line သည် node id အစီအစဉ်ဖြင့် လာရမည်

```python
NODES = {
    "co:neo4j": ("Company", "Neo4j", ("Neo4j Inc", "Neo4j, Inc."), "Graph database vendor."),
    "tech:vectorindex": ("Technology", "Vector Index", ("vector search index", "HNSW index"), "Approximate nearest neighbour index over embeddings."),
}
lines = []
for node_id in sorted(["tech:vectorindex", "co:neo4j"]):
    label, name, _aliases, summary = NODES[node_id]
    lines.append(f"[ENTITY] id={node_id} | label={label} | name={name} | summary={summary}")
print("\n".join(lines))
```

Output —

```text
[ENTITY] id=co:neo4j | label=Company | name=Neo4j | summary=Graph database vendor.
[ENTITY] id=tech:vectorindex | label=Technology | name=Vector Index | summary=Approximate nearest neighbour index over embeddings.
```

`"\n".join(list)` သည် list ထဲက စာသားများကို newline ဖြင့်
ပြန်ဆက်ပြီး စာသားတစ်ခုတည်း ပြန်ပေးသည်။ `sorted([...])` က `co:neo4j` ကို
`tech:vectorindex` ထက် အရင်ထားသဖြင့် input order ကို ပြောင်းလိုက်သည်ကို
တွေ့နိုင်သည် — ဤအချက်သည် deterministic prefix ဖြစ်စေသည်။

---

## 2. `[RELATION]` Line — Cypher pattern နှင့် တူညီအောင်

```python
print(f"{e[0]} -[{e[1]}]-> {e[2]}")
```

Relation line သည် Cypher ၏ pattern syntax နှင့် **တူညီအောင်** ရေးထားသည် —
`(a)-[:REL]->(b)` ၏ core shape ဖြစ်သည့် `a -[REL]-> b` ကို ယူထားသည်။
အကျိုးမှာ LLM သည် training data တွင် မြင်ဖူးသည့် shape ဖြစ်သဖြင့် relation
တစ်ခုစီကို graph triple အဖြစ် အလွယ်တကူ ဖတ်နိုင်သည်။

`e` သည် 4-tuple `(src, rel, dst, chunk)` ဖြစ်သည်။ `e[0]` = source၊ `e[1]` =
relationship type၊ `e[2]` = destination။ Index `3` (provenance chunk) ကို relation
line တွင် **မထည့်ပါ** — chunk ကို LLM မလိုပါ; citation အတွက် နောက်ပိုင်း retrieval
layer တွင် သုံးသည်။

---

## 3. `itertools.groupby()` — Sorted လုပ်ပြီးမှသာ သုံးရမည်

```python
import itertools

edges = [
    ("tech:graphrag", "USES", "tech:cypher"),
    ("co:neo4j", "DEVELOPS", "prod:aura"),
    ("co:neo4j", "CREATES", "tech:cypher"),
    ("prod:aura", "USES", "tech:vectorindex"),
]
grouped = sorted(edges, key=lambda e: (e[0], e[1], e[2]))
for src, group in itertools.groupby(grouped, key=lambda e: e[0]):
    print(src, "->", [e[2] for e in group])
```

Output —

```text
co:neo4j -> ['tech:cypher', 'prod:aura']
prod:aura -> ['tech:vectorindex']
tech:graphrag -> ['tech:cypher']
```

`groupby(iterable, key=...)` သည် **ကပ်လျက်** တူညီသည့် key ရှိသည့် element များကို
`(key, group_iterator)` tuple အဖြစ် စုပေးသည်။ `key=lambda e: e[0]` သည် source
node အမည်ကို group key အဖြစ် သုံးသည်။

ပြဿနာမှာ — `groupby` သည် **sort လုပ်ပေးသည့် function မဟုတ်ပါ**၊ ကပ်လျက်
ရှိပြီးသား element များကိုသာ စုသည်။ Sort မလုပ်ရင် ဘာဖြစ်လဲ။

```python
import itertools

unsorted_edges = [("co:neo4j", "DEVELOPS"), ("prod:aura", "USES"), ("co:neo4j", "CREATES")]
for src, group in itertools.groupby(unsorted_edges, key=lambda e: e[0]):
    print(src, "->", [e[1] for e in group])
```

Output —

```text
co:neo4j -> ['DEVELOPS']
prod:aura -> ['USES']
co:neo4j -> ['CREATES']
```

`co:neo4j` သည် **နှစ်ကြိမ်** ပေါ်လာသည် — သူ့ element နှစ်ခုသည် ကပ်လျက် မရှိလို့ပါ။
ဤအချက်က ဤ exercise ၏ exercise hint တွင် "`itertools.groupby` ကို အသုံးပြုလျှင်
list ကို ကြိုတင် `sorted()` လုပ်ရမည်" လို့ ရေးထားရသည့် အကြောင်းရင်း ဖြစ်သည်။
Output သည် graph ကဲ့သို့ **ပုံပေါ်ရုံသာ** ဖြစ်ပြီး အမှန်တကယ် မှားနေသည် — ဤကဲ့သို့
bug ကို ရှာရ အခက်သည်၊ ထို့ကြောင့် `sorted()` ကို groupby မတိုင်မီ အမြဲ ထားရမည်။

---

## 4. `serialize_subgraph()` — Function တစ်ခုလုံး

```python
import itertools


def serialize_subgraph(node_ids, edge_indexes, max_tokens=4096):
    """Deterministic text block: entity lines first, then relation lines."""
    lines = []
    for node_id in sorted(node_ids):
        label, name, _aliases, summary = NODES[node_id]
        lines.append(f"[ENTITY] id={node_id} | label={label} | name={name} | summary={summary}")
    grouped = sorted((EDGES[i] for i in edge_indexes), key=lambda e: (e[0], e[1], e[2]))
    for src, group in itertools.groupby(grouped, key=lambda e: e[0]):
        lines += [f"[RELATION] {e[0]} -[{e[1]}]-> {e[2]}" for e in group]
    text = "\n".join(lines)
    return text if len(text) // 4 <= max_tokens else text[: max_tokens * 4]
```

### 4.1 Parameter များ

- `node_ids` — Exercise 2 ၏ `sorted(reached)` (node id များ၏ list)။
- `edge_indexes` — Exercise 2 ၏ `idx` (edge index များ၏ list)။
- `max_tokens` — ခန့်မှန်း token အများဆုံး။ Default `4096`။

### 4.2 Entity loop — အပိုင်း ၁

```python
lines = []
for node_id in sorted(node_ids):
    label, name, _aliases, summary = NODES[node_id]
    lines.append(f"[ENTITY] id={node_id} | ...")
```

`lines` သည် စာသားလိုင်းများ စုထားသည့် list ဖြစ်သည်။ စာသားကို `+=` ဖြင့်
တိုက်ရိုက် ဆက်မထားဘဲ list ထဲ ထည့်ပြီး **အဆုံးတွင် တစ်ကြိမ်တည်း join**
လုပ်ခြင်းသည် performance အရ ပိုကောင်းသည် — string သည် immutable ဖြစ်သဖြင့်
`text += line` က iteration တိုင်း စာသားအသစ် ဖန်တီးသည်။

### 4.3 Relation အပိုင်း — generator expression + tuple sort key

```python
grouped = sorted((EDGES[i] for i in edge_indexes), key=lambda e: (e[0], e[1], e[2]))
```

`(EDGES[i] for i in edge_indexes)` သည် **generator expression** ဖြစ်သည် — list
comprehension နှင့် shape တူသော်လည်း `[...]` မဟုတ်ဘဲ `(...)` ဖြစ်သည်။ List
တစ်ခုလုံး memory ထဲ မဖန်တီးဘဲ တန်ဖိုးများကို တစ်ခုချင်း ပေးသည်။ `sorted()`
သည် ထို generator ကို စားသုံးပြီး list အဖြစ် ပြန်ပေးသည်။

`key=lambda e: (e[0], e[1], e[2])` — sort key သည် **tuple** ဖြစ်သည်။ Tuple
နှိုင်းယှဉ်မှုသည် element အစဉ်လိုက် ဖြစ်သဖြင့် source ကို အရင်နှိုင်းယှဉ်ပြီး
တူလျှင် relationship type ကို၊ ထို့နောက် destination ကို နှိုင်းယှဉ်သည်။
ထို့ကြောင့် relation line များသည် **edge index အစီအစဉ်မဟုတ်ဘဲ** `(src, rel,
dst)` အက္ခရာအစီအစဉ်ဖြင့် လာသည်။

ဤအချက်ကို တိုက်ရိုက် မြင်အောင် ကြည့်ပါ။

```python
import itertools

EDGES = (
    ("co:neo4j", "DEVELOPS", "prod:aura", "c1"),
    ("co:neo4j", "CREATES", "tech:cypher", "c2"),
    ("co:neo4j", "EMPLOYS", "org:neo4jeng", "c2"),
    ("prod:aura", "USES", "tech:vectorindex", "c1"),
    ("tech:cypher", "MAINTAINED_BY", "org:neo4jeng", "c2"),
    ("tech:graphrag", "USES", "tech:cypher", "c3"),
    ("co:neo4j", "PUBLISHES", "tech:graphrag", "c3"),
    ("tech:graphrag", "RUNS_ON", "prod:aura", "c3"),
)
edge_indexes = [0, 1, 2, 3, 4, 5, 6, 7]
grouped = sorted((EDGES[i] for i in edge_indexes), key=lambda e: (e[0], e[1], e[2]))
for src, group in itertools.groupby(grouped, key=lambda e: e[0]):
    rel_lines = [f"{e[0]} -[{e[1]}]-> {e[2]}" for e in group]
    print(src, len(rel_lines))
    for line in rel_lines:
        print("   ", line)
```

Output —

```text
co:neo4j 4
    co:neo4j -[CREATES]-> tech:cypher
    co:neo4j -[DEVELOPS]-> prod:aura
    co:neo4j -[EMPLOYS]-> org:neo4jeng
    co:neo4j -[PUBLISHES]-> tech:graphrag
prod:aura 1
    prod:aura -[USES]-> tech:vectorindex
tech:cypher 1
    tech:cypher -[MAINTAINED_BY]-> org:neo4jeng
tech:graphrag 2
    tech:graphrag -[RUNS_ON]-> prod:aura
    tech:graphrag -[USES]-> tech:cypher
```

Edge index 0 က `DEVELOPS`၊ index 1 က `CREATES` ဖြစ်သည်ကို သတိထားပါ။ Output တွင်
`CREATES` က အရင်လာသည် — အကြောင်းရင်းမှာ sort key က `(src, rel, dst)` ဖြစ်လို့ပါ။
Edge index အစီအစဉ်ကို ပြင်ခြင်းသည် output ကို မပြောင်းလဲစေပါ။

### 4.4 `lines += [...]` — extend

```python
lines += [f"[RELATION] {e[0]} -[{e[1]}]-> {e[2]}" for e in group]
```

`lines += list` သည် `lines.extend(list)` နှင့် တူညီသည် — element တိုင်းကို
အစဉ်လိုက် ထည့်သည်။ `lines = lines + list` လည် ရလဒ် တူညီသော်လည်း `+=` သည်
list တစ်ခုတည်းကို **in-place** ပြင်သဖြင့် ပိုထိရောက်သည်။

`group` သည် groupby ပေးသည့် **iterator** ဖြစ်သည်။ List comprehension နှင့်
တိုက်ရိုက် စားသုံးလိုက်သဖြင့် group တစ်ခုစီကို တစ်ကြိမ်တည်း ကုန်စေသည် —
groupby ၏ iterator များသည် **တစ်ကြိမ်တည်း သုံးရမည်** (တစ်ကြိမ်သုံးပြီးလျှင်
ကုန်သွားသည်)။

### 4.5 Token ခန့်မှန်းချက်နှင့် ဖြတ်ခြင်း

```python
text = "\n".join(lines)
return text if len(text) // 4 <= max_tokens else text[: max_tokens * 4]
```

- `len(text) // 4` — စာလုံး ၄ လုံးလျှင် token ၁ ခုဟု ခန့်မှန်းသည်။ `//` သည်
  **integer division** — ဒသမ မပါဘဲ အောက်ကို လှမ်းသည်။
- `X if cond else Y` သည် **conditional expression** — `cond` မှန်လျှင် `X`၊
  မှားလျှင် `Y`။ ဤနေရာတွင် "ကန့်သတ်ချက်အတွင်း ဆိုလျှင် စာသားအပြည့်၊ မဟုတ်လျှင်
  ဖြတ်" ဟု ဖတ်သည်။
- `text[: max_tokens * 4]` သည် **slicing** ဖြစ်သည် — ပထမ `max_tokens * 4` လုံးကို
  ယူသည်။ အရေးကြီးသည့် အချက်မှာ ဤဖြတ်ခြင်းသည် **လိုင်းအလယ်တွင် ရပ်နိုင်သည်**။

```python
text = "abc"
print(len(text), len(text) // 4)
print(1026 // 4)
print(len("x" * 200))
```

Output —

```text
3 0
256
200
```

`"abc"` သည် လုံး ၃ လုံးရှိပြီး `3 // 4` သည် `0` ဖြစ်သည် — token ခန့်မှန်းချက်
သည် စာသားတိုအတွက် 0 ဖြစ်နိုင်သည်။ `1026 // 4 = 256` ဖြစ်သည် — ဤတန်ဖိုးသည်
Section 6 တွင် တကယ်တွက်ထားသည့် context ၏ token ခန့်မှန်းချက် ဖြစ်သည်။

`max_tokens` ထက် ကျော်လျှင် အလုပ်လုပ်သည့် ဖြတ်ခြင်း branch ကို Section 6 ၏ run
တွင် တိုက်ရိုက် တွေ့နိုင်သည် — ထို run သည် `max_tokens=50` ဖြင့် ဖြတ်ထားသည့်
ရလဒ်ကိုလည် ပြထားသည်။

---

## 5. Context အရွယ်အစားကို Hop နှင့် နှိုင်းယှဉ်ခြင်း

`serialize_subgraph()` အတွက် ထည့်လိုက်သည့် subgraph ကြီးလာလျှင် context လည်
ကြီးလာသည်။ Section 6 ၏ run သည် Exercise 2 ၏ `k=1` နှင့် `k=2` ရလဒ် နှစ်မျိုးလုံးအတွက်
context အရွယ်အစားကို တိုင်းထားသည်။

| Hop budget | Entity line | Relation line | လိုင်းစုစုပေါင်း | Token ခန့်မှန်း (chars // 4) |
| --- | --- | --- | --- | --- |
| `k=1` | 5 | 7 | 12 | 211 |
| `k=2` (saturation) | 6 | 8 | 14 | 256 |

Anchor `co:neo4j` တစ်ခုတည်းအတွက် `k=2` သည် 256 token သာ ဖြစ်သည် — အလွန်
သေးငယ်သည်။ သို့သော် degree မြင့်သည့် hub များရှိသည့် graph အစစ်တွင် hop
တစ်ခု တိုးတိုင်း ရာဂဏန်းဆ token ဖြစ်နိုင်သည်။ ဤဇယားက **hop budget နှင့် context
size တိုက်ရိုက် အချိုးကျသည်** ဆိုသည့် အချက်ကို တိုင်းတာနိုင်စေသည်။

---

## 6. Serialization ရလဒ် အပြည့်အစုံ

```python
import itertools

NODES = {
    "co:neo4j": ("Company", "Neo4j", ("Neo4j Inc", "Neo4j, Inc."), "Graph database vendor."),
    "org:neo4jeng": ("Team", "Neo4j Engineering", (), "Engineering team maintaining Cypher."),
    "prod:aura": ("Product", "AuraDB", ("Neo4j AuraDB", "Aura"), "Managed cloud graph database service."),
    "tech:cypher": ("Technology", "Cypher", ("openCypher", "Cypher Query Language"), "Declarative graph query language."),
    "tech:graphrag": ("Technology", "GraphRAG", ("Graph RAG", "Microsoft GraphRAG"), "Retrieval pattern grounded in a knowledge graph."),
    "tech:vectorindex": ("Technology", "Vector Index", ("vector search index", "HNSW index"), "Approximate nearest neighbour index over embeddings."),
}
EDGES = (
    ("co:neo4j", "DEVELOPS", "prod:aura", "c1"),
    ("co:neo4j", "CREATES", "tech:cypher", "c2"),
    ("co:neo4j", "EMPLOYS", "org:neo4jeng", "c2"),
    ("prod:aura", "USES", "tech:vectorindex", "c1"),
    ("tech:cypher", "MAINTAINED_BY", "org:neo4jeng", "c2"),
    ("tech:graphrag", "USES", "tech:cypher", "c3"),
    ("co:neo4j", "PUBLISHES", "tech:graphrag", "c3"),
    ("tech:graphrag", "RUNS_ON", "prod:aura", "c3"),
)


def serialize_subgraph(node_ids, edge_indexes, max_tokens=4096):
    lines = []
    for node_id in sorted(node_ids):
        label, name, _aliases, summary = NODES[node_id]
        lines.append(f"[ENTITY] id={node_id} | label={label} | name={name} | summary={summary}")
    grouped = sorted((EDGES[i] for i in edge_indexes), key=lambda e: (e[0], e[1], e[2]))
    for src, group in itertools.groupby(grouped, key=lambda e: e[0]):
        lines += [f"[RELATION] {e[0]} -[{e[1]}]-> {e[2]}" for e in group]
    text = "\n".join(lines)
    return text if len(text) // 4 <= max_tokens else text[: max_tokens * 4]


n2 = ["co:neo4j", "org:neo4jeng", "prod:aura", "tech:cypher", "tech:graphrag", "tech:vectorindex"]
e2 = [0, 1, 2, 3, 4, 5, 6, 7]
context = serialize_subgraph(n2, e2)
print(context)
lines = context.splitlines()
entity_lines = [ln for ln in lines if ln.startswith("[ENTITY]")]
relation_lines = [ln for ln in lines if ln.startswith("[RELATION]")]

n1 = ["co:neo4j", "org:neo4jeng", "prod:aura", "tech:cypher", "tech:graphrag"]
e1 = [0, 1, 2, 4, 5, 6, 7]
print("k=1 tokens:", len(serialize_subgraph(n1, e1)) // 4)
print("k=2 tokens:", len(context) // 4)
truncated = serialize_subgraph(n2, e2, max_tokens=50)
print("full length :", len(context))
print("max_tokens=50 -> length :", len(truncated))
print("tail        :", repr(truncated[-16:]))
print(f"[ok] serialized {len(entity_lines)} entities + {len(relation_lines)} relations, "
      f"~{len(context) // 4} tokens")
```

Output —

```text
[ENTITY] id=co:neo4j | label=Company | name=Neo4j | summary=Graph database vendor.
[ENTITY] id=org:neo4jeng | label=Team | name=Neo4j Engineering | summary=Engineering team maintaining Cypher.
[ENTITY] id=prod:aura | label=Product | name=AuraDB | summary=Managed cloud graph database service.
[ENTITY] id=tech:cypher | label=Technology | name=Cypher | summary=Declarative graph query language.
[ENTITY] id=tech:graphrag | label=Technology | name=GraphRAG | summary=Retrieval pattern grounded in a knowledge graph.
[ENTITY] id=tech:vectorindex | label=Technology | name=Vector Index | summary=Approximate nearest neighbour index over embeddings.
[RELATION] co:neo4j -[CREATES]-> tech:cypher
[RELATION] co:neo4j -[DEVELOPS]-> prod:aura
[RELATION] co:neo4j -[EMPLOYS]-> org:neo4jeng
[RELATION] co:neo4j -[PUBLISHES]-> tech:graphrag
[RELATION] prod:aura -[USES]-> tech:vectorindex
[RELATION] tech:cypher -[MAINTAINED_BY]-> org:neo4jeng
[RELATION] tech:graphrag -[RUNS_ON]-> prod:aura
[RELATION] tech:graphrag -[USES]-> tech:cypher
k=1 tokens: 211
k=2 tokens: 256
full length : 1026
max_tokens=50 -> length : 200
tail        : ' Cypher.\n[ENTITY'
[ok] serialized 6 entities + 8 relations, ~256 tokens
```

`tail` လိုင်းသည် ဖြတ်ခြင်း branch ၏ ရလဒ်ကို ပြသည် — `max_tokens=50` ဖြင့်
စာသားသည် ၂၀၀ လုံးသို့ ဖြတ်ခံရပြီး အဆုံးသတ်စာသားမှာ `' Cypher.\n[ENTITY'`
ဖြစ်သည် — `[ENTITY` သည် **လိုင်းအလယ်တွင်** ရပ်နေသည်ကို တွေ့နိုင်သည်။ ဤအချက်က
ဤ truncation နည်းလမ်းသည် လိုင်းအလိုက် ဖြတ်ခြင်း မဟုတ်ပါ — deterministic
upper bound အတွက် ရိုးရှင်းစွာ ဖြတ်ခြင်းသာ ဖြစ်သည်။ Production တွင် line-aware
truncation (သို့) tokenizer အစစ်ဖြင့် ရေတွက်ခြင်း လိုအပ်သည်။

`lines[0]` သည် `[ENTITY]` ဖြင့် စပြီး `lines[6]` မှ စ၍ `[RELATION]` ဖြစ်သည် —
entity အပိုင်း ပြီးဆုံးမှ relation အပိုင်း စသည်ကို ဤအချက်က အတည်ပြုသည်။
Entity line ၆ ခုနှင့် relation line ၈ ခု — Exercise 2 ၏ `k=2` ရလဒ် (node 6၊ edge 8)
နှင့် **လုံးဝ ကိုက်ညီသည်**။

---

## 7. Code တစ်ခုလုံး — Run လုပ်နိုင်သော Version

```python
# end-to-end: exercise_3
import itertools

NODES = {
    "co:neo4j": ("Company", "Neo4j", ("Neo4j Inc", "Neo4j, Inc."), "Graph database vendor."),
    "org:neo4jeng": ("Team", "Neo4j Engineering", (), "Engineering team maintaining Cypher."),
    "prod:aura": ("Product", "AuraDB", ("Neo4j AuraDB", "Aura"), "Managed cloud graph database service."),
    "tech:cypher": ("Technology", "Cypher", ("openCypher", "Cypher Query Language"), "Declarative graph query language."),
    "tech:graphrag": ("Technology", "GraphRAG", ("Graph RAG", "Microsoft GraphRAG"), "Retrieval pattern grounded in a knowledge graph."),
    "tech:vectorindex": ("Technology", "Vector Index", ("vector search index", "HNSW index"), "Approximate nearest neighbour index over embeddings."),
}
EDGES = (
    ("co:neo4j", "DEVELOPS", "prod:aura", "c1"),
    ("co:neo4j", "CREATES", "tech:cypher", "c2"),
    ("co:neo4j", "EMPLOYS", "org:neo4jeng", "c2"),
    ("prod:aura", "USES", "tech:vectorindex", "c1"),
    ("tech:cypher", "MAINTAINED_BY", "org:neo4jeng", "c2"),
    ("tech:graphrag", "USES", "tech:cypher", "c3"),
    ("co:neo4j", "PUBLISHES", "tech:graphrag", "c3"),
    ("tech:graphrag", "RUNS_ON", "prod:aura", "c3"),
)


def serialize_subgraph(node_ids, edge_indexes, max_tokens=4096):
    lines = []
    for node_id in sorted(node_ids):
        label, name, _aliases, summary = NODES[node_id]
        lines.append(f"[ENTITY] id={node_id} | label={label} | name={name} | summary={summary}")
    grouped = sorted((EDGES[i] for i in edge_indexes), key=lambda e: (e[0], e[1], e[2]))
    for src, group in itertools.groupby(grouped, key=lambda e: e[0]):
        lines += [f"[RELATION] {e[0]} -[{e[1]}]-> {e[2]}" for e in group]
    text = "\n".join(lines)
    return text if len(text) // 4 <= max_tokens else text[: max_tokens * 4]


n2 = ["co:neo4j", "org:neo4jeng", "prod:aura", "tech:cypher", "tech:graphrag", "tech:vectorindex"]
e2 = [0, 1, 2, 3, 4, 5, 6, 7]
context = serialize_subgraph(n2, e2)
print(context)

lines = context.splitlines()
entity_lines = [ln for ln in lines if ln.startswith("[ENTITY]")]
relation_lines = [ln for ln in lines if ln.startswith("[RELATION]")]

assert len(entity_lines) == len(n2) == 6
assert len(relation_lines) == len(e2) == 8
assert entity_lines == sorted(entity_lines)
assert lines[0].startswith("[ENTITY]") and "[RELATION]" not in lines[0]
assert "[RELATION] co:neo4j -[DEVELOPS]-> prod:aura" in lines
print(f"[ok] serialized {len(entity_lines)} entities + {len(relation_lines)} relations, "
      f"~{len(context) // 4} tokens")
```

Output —

```text
[ENTITY] id=co:neo4j | label=Company | name=Neo4j | summary=Graph database vendor.
[ENTITY] id=org:neo4jeng | label=Team | name=Neo4j Engineering | summary=Engineering team maintaining Cypher.
[ENTITY] id=prod:aura | label=Product | name=AuraDB | summary=Managed cloud graph database service.
[ENTITY] id=tech:cypher | label=Technology | name=Cypher | summary=Declarative graph query language.
[ENTITY] id=tech:graphrag | label=Technology | name=GraphRAG | summary=Retrieval pattern grounded in a knowledge graph.
[ENTITY] id=tech:vectorindex | label=Technology | name=Vector Index | summary=Approximate nearest neighbour index over embeddings.
[RELATION] co:neo4j -[CREATES]-> tech:cypher
[RELATION] co:neo4j -[DEVELOPS]-> prod:aura
[RELATION] co:neo4j -[EMPLOYS]-> org:neo4jeng
[RELATION] co:neo4j -[PUBLISHES]-> tech:graphrag
[RELATION] prod:aura -[USES]-> tech:vectorindex
[RELATION] tech:cypher -[MAINTAINED_BY]-> org:neo4jeng
[RELATION] tech:graphrag -[RUNS_ON]-> prod:aura
[RELATION] tech:graphrag -[USES]-> tech:cypher
[ok] serialized 6 entities + 8 relations, ~256 tokens
```

`assert lines[0].startswith("[ENTITY]") and "[RELATION]" not in lines[0]` သည်
"entity အပိုင်းသည် အမြဲ အရင် လာရမည်" ဆိုသည့် contract ကို စစ်သည်။
`assert "[RELATION] co:neo4j -[DEVELOPS]-> prod:aura" in lines` သည် relation line
၏ format ကို စစ်သည် — `in` သည် list ထဲ element ရှိမရှိ စစ်ခြင်း ဖြစ်သည်။

---

## 8. ကိုယ်တိုင်လေ့ကျင့်ကြည့်ပါ

**မေးခွန်း** — `itertools.groupby` ကို အောက်ပါ code လို **sort မလုပ်ဘဲ** သုံးလျှင်
ဘယ် output ရမလဲ။

```python
import itertools

edges = [("b", "X"), ("a", "Y"), ("b", "Z")]
for src, group in itertools.groupby(edges, key=lambda e: e[0]):
    print(src, "->", [e[1] for e in group])
```

1. `b -> ['X', 'Z']`, `a -> ['Y']`
2. `a -> ['Y']`, `b -> ['X', 'Z']`
3. `b -> ['X']`, `a -> ['Y']`, `b -> ['Z']`
4. ဘာမှ မပြပါ

<details>
<summary>အဖြေ ကြည့်ရန်</summary>

**အဖြေ — 3. `b -> ['X']`, `a -> ['Y']`, `b -> ['Z']`**

အကြောင်းရင်း — `groupby` သည် **input အစီအစဉ်အတိုင်း** ကပ်လျက် တူညီသည့် key
များကိုသာ စုသည်။ ဤ list တွင် `b`၊ `a`၊ `b` လို့ လာသည် — `b` နှစ်ခုသည် ကပ်လျက်
မရှိသဖြင့် **group နှစ်ခု** ဖြစ်သွားသည်။ Output တွင် `b` သည် နှစ်ကြိမ် ပေါ်သည်။
Sort လုပ်ထားလျှင် (`sorted(edges, key=lambda e: e[0])`) output သည် ရွေးချယ်စရာ 1
ဖြစ်လာမည်။ ဤအချက်ကြောင့် `serialize_subgraph()` သည် groupby မတိုင်မီ
`sorted(...)` ကို အမြဲ ခေါ်ရသည်။

</details>

---

**အဓိက မှတ်ထားရန်** — Serialization သည် subgraph ကို LLM ဖတ်နိုင်သည့်
စာသားအဖြစ် ပြောင်းသည်။ Entity နှင့် relation ကို **နှစ်ပိုင်း ခွဲထားခြင်း**ဖြင့်
LLM သည် "ဤ node များ တည်ရှိသည်" နှင့် "ဤ node များ ဆက်စပ်သည်" ဆိုသည့်
အချက်နှစ်ခုကို ခွဲခြားဖတ်နိုင်သည်။ `itertools.groupby()` သည် **sorted လုပ်ပြီးမှသာ**
အလုပ်လုပ်သည် — မလုပ်လျှင် group များ ထပ်နေပြီး bug ကို ရှာရ ခက်သည်။
Sort order ကို သတ်မှတ်ထားခြင်းသည် deterministic prefix ဖြစ်စေပြီး prompt
caching အတွက် အကျိုးရှိသည်။ Token ခန့်မှန်းချက်ကို `len(text) // 4` ဖြင့်
တွက်ခြင်းသည် ရိုးရှင်းသော်လည်း **ခန့်မှန်းချက်သာ** ဖြစ်သည် — tokenizer အစစ်
(သို့) server-side token count နှင့် ကွာနိုင်သည်။ ဖြတ်ခြင်းသည် လိုင်းအလယ်တွင်
ရပ်နိုင်သဖြင့် production တွင် line-aware truncation ကို သုံးရမည်။
