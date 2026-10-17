# Walkthrough 02 — Idempotent merge simulator (`MERGE` vs `CREATE`) (Exercise 2)

> ဤဖိုင်သည် Module 06 ၏ `solution.md` ထဲက Exercise 2 ကို **Python အခြေခံမှ စ၍**
> အပိုင်းလိုက် ရှင်းပြသည့် walkthrough ဖြစ်သည်။ `InMemoryGraph` သည် Neo4j server
> မလိုဘဲ write path ကို simulate လုပ်သည့် class ဖြစ်သည်။ Output တိုင်းသည် ဤစာတွင်
> ပြထားသည့် code ကို run ၍ ရရှိသည့် အမှန်တကယ် ရလဒ် ဖြစ်သည်။

---

## 0. ဤ Exercise က ဘာကို ဖြေရှင်းပေးသလဲ။

Ingestion pipeline သည် corpus ပြောင်းလဲသည့်အခါ၊ job ပျက်သွားသည့်အခါ၊ retry ဖြစ်သည့်အခါ
တူညီသော triple များကို **ထပ်ခါတလဲလဲ** ရေးရသည်။ Write path က idempotent မဖြစ်လျှင် —

```text
pass 1 : MERGE/CREATE → node 5  edge 6
pass 2 : ထို input အတိအကျကိုပင် ပြန်ရေး
         MERGE  : node 5  edge 6   (မပြောင်း — idempotent)
         CREATE : node 12 edge 6   (ပွားလာ — idempotent မဟုတ်)
```

ဤ Exercise က ထို semantics ကွာခြားချက်ကို **server မလိုဘဲ** တိုင်းတာနိုင်ရန်
`InMemoryGraph` ကို ရေးသည်။ Idempotency ဆိုသည်မှာ operation တစ်ခုကို အကြိမ်များစွာ
apply လုပ်လျှင် ရလဒ် မပြောင်းခြင်း ဖြစ်သည် — `f(f(x)) == f(x)`။

ဤ code တွင် လေ့လာရမည့် Python concepts များမှာ —

- Class၊ `self` နှင့် instance attribute
- Tuple key ဖြင့် **identity** သတ်မှတ်ခြင်း
- `key in dict` (membership test) နှင့် `dict.get()`
- `dict.setdefault()` နှင့် `dict[key] = value` ၏ ကွာခြားချက်
- Early `return` ဖြင့် branch ကို ရပ်ခြင်း
- List `append()` နှင့် dict ထဲ counter တိုးခြင်း (`x[k] += 1`)
- Nested `for` loop

---

## 1. Identity key — Tuple ဖြင့် "တူညီခြင်း" ကို သတ်မှတ်ခြင်း

Node တစ်ခု ရှိပြီးသား ဟုတ်မဟုတ် ဆုံးဖြတ်ရန် **key** တစ်ခု လိုသည်။ ဤ Exercise က
`(label, id)` tuple ကို key အဖြစ် သုံးသည်။ `in` operator က dict ၏ key များထဲ
ပါမပါ စစ်သည်။
```python
nodes = {("Person", "ada_lovelace"): {"name": "Ada Lovelace"}}
print(("Person", "ada_lovelace") in nodes)
print(("Person", "ada_lovelace_2") in nodes)
print(("person", "ada_lovelace") in nodes)
```

Output —
```text
True
False
False
```

တတိယလိုင်းက အရေးကြီးသည် — `("person", ...)` နှင့် `("Person", ...)` သည် **မတူညီပါ**။
Tuple တူညီမှုသည် အဖွဲ့ဝင်တိုင်း အတိအကျ တူရသည်၊ string comparison သည် case-sensitive
ဖြစ်သည်။ ထို့ကြောင့် label ကို allowlist မှ တိတိကျကျ ရယူရသည် — `Person` နှင့် `person`
ကို label နှစ်ခုအဖြစ် Neo4j က သိသည်။

---
## 2. `InMemoryGraph.__init__` — Class နှင့် instance state
Class တစ်ခုဖန်တီးသည့်အခါ `__init__` က အလိုအလျောက် run သည်။ `self` သည်
ဖန်တီးလိုက်သည့် object ကိုယ်တိုင် ဖြစ်သည်။

| Attribute | အမျိုးအစား | အလုပ် |
| --- | --- | --- |
| `semantics` | string | `"merge"` သို့မဟုတ် `"create"` |
| `node_keys` / `edge_keys` | list | ရှိပြီးသား identity key များ (အစီအစဉ် ထိန်း) |
| `node_props` / `edge_props` | dict | key → property |
| `stats` | dict | created/matched counter ၄ ခု |

`node_keys` (list) နှင့် `node_props` (dict) နှစ်ခုလုံး ထားရှိခြင်းသည် ရည်ရွယ်ချက်ရှိသည် —
dict ကို lookup အတွက်၊ list ကို **ထည့်ခဲ့သည့် အစီအစဉ်** ထိန်းသိမ်းရန် သုံးသည်။
`node_count()` သည် `len(self.node_keys)` ကို ပြန်သည် — ဤအရေအတွက်သည် *write အကြိမ်*
မဟုတ်၊ **ထူးခြားသော node အရေအတွက်** ဖြစ်သည်။
```python
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


for semantics in ("merge", "create"):
    g = InMemoryGraph(semantics)
    print("%-7s node_count=%d edge_count=%d stats=%s"
          % (semantics, g.node_count(), g.edge_count(), g.stats))
```

Output —
```text
merge   node_count=0 edge_count=0 stats={'nodes_created': 0, 'nodes_matched': 0, 'edges_created': 0, 'edges_matched': 0}
create  node_count=0 edge_count=0 stats={'nodes_created': 0, 'nodes_matched': 0, 'edges_created': 0, 'edges_matched': 0}
```

Graph အလွတ်တွင် count နှစ်ခုလုံး 0 ဖြစ်ပြီး counter ၄ ခုလုံး 0 ဖြစ်သည်။
`semantics` သည် ဖန်တီးသည့်အချိန်တွင် သတ်မှတ်ပြီး object တစ်ခုလုံး၏ အပြုအမူကို
ဆုံးဖြတ်သည် — ဤသည်မှာ **strategy** ကို constructor parameter အဖြစ် ထည့်သည့် pattern
ဖြစ်သည်။ စမ်းသပ်ရာတွင် semantics နှစ်မျိုးကို နှိုင်းယှဉ်နိုင်ရန် ဤနည်းကို သုံးသည်။

> **မှတ်ချက်** — ဤအပိုင်းမှ စ၍ အောက်ပါ snippet များသည် ဤနေရာတွင် သတ်မှတ်လိုက်သည့်
> `InMemoryGraph` နှင့် Walkthrough 01 တွင် သတ်မှတ်သည့် `ENTITY_TYPE_TO_LABEL`၊
> `TRIPLES`၊ `slug()`၊ `build_batch_statements()`၊ `apply_batch()` တို့ကို
> သုံးသည်။ Snippet တစ်ခုချင်း ကို run မည်ဆိုလျှင် Section 9 ရှိ runnable script
> နှင့်အတူ တစ်ဖိုင်တည်း ပေါင်းထည့်ပြီး run ရသည်။

---
## 3. `write_node()` — `MERGE` path နှင့် `CREATE` path
Function ၏ အဓိကလိုင်းများ —

```python
key = (label, node_id)
if self.semantics == "merge" and key in self.node_props:
    self.stats["nodes_matched"] += 1
    self.node_props[key]["name"] = name
    return
```

`and` ကွင်းဆက်သည် ဘယ်မှ ညာသို့ စစ်သည်။ `semantics == "create"` ဖြစ်လျှင် ပထမအချက်
`False` ဖြစ်သဖြင့် `key in self.node_props` ကို မစစ်တော့ပါ — ဒုတိယအချက် ဖြစ်လာသည်။
`return` သည် function ကို **ထိုနေရာတွင်** အဆုံးသတ်သည်; အောက်က ဖန်တီးသည့်လိုင်းများကို
ကျော်သွားသည်။ `CREATE` semantics အတွက် ဤ branch ကို လုံးဝ မဝင်ပါ။
```python
g = InMemoryGraph("merge")
g.write_node("Person", "ada_lovelace", "Ada Lovelace")
print("1st call :", g.node_count(), "nodes_created=%d" % g.stats["nodes_created"])
g.write_node("Person", "ada_lovelace", "Ada Lovelace")
print("2nd call :", g.node_count(), "nodes_matched=%d" % g.stats["nodes_matched"])
g.write_node("Person", "ada_lovelace", "A. Lovelace")
print("name now :", g.node_props[("Person", "ada_lovelace")]["name"])
print("node_keys:", g.node_keys)

c = InMemoryGraph("create")
c.write_node("Person", "ada_lovelace", "Ada Lovelace")
c.write_node("Person", "ada_lovelace", "Ada Lovelace")
print("create   :", c.node_count(), "nodes_created=%d" % c.stats["nodes_created"])
```

Output —
```text
1st call : 1 nodes_created=1
2nd call : 1 nodes_matched=1
name now : A. Lovelace
node_keys: [('Person', 'ada_lovelace')]
create   : 2 nodes_created=2
```

`merge` ဖြင့် ဒုတိယအကြိမ် ရေးလျှင် `node_count()` မပြောင်း — `nodes_matched` သာ တိုးသည်။
ထို့ကြောင့် **node အရေအတွက်ကို မတိုးစေဘဲ** အချက်အလက်ကို refresh လုပ်နိုင်သည်။
တတိယ call တွင် name ကို `A. Lovelace` ဟု ပြောင်းရေးလိုက်လျှင် property update ဖြစ်သွားသည် —
နောက်ဆုံး ရေးသည့်တန်ဖိုးက အနိုင်ရသည် (last-write-wins)။

`create` ဖြင့် ထို call နှစ်ခုသည် node **နှစ်ခု** ဖြစ်လာသည် — `node_keys` ထဲ tuple တူညီသည့်
အဖွဲ့ဝင် နှစ်ခု ရှိလာသည်။ Neo4j တွင် ဤအခြေအနေကို duplicate node ဟုခေါ်ပြီး graph ၏
အဓိက ပြဿနာ ဖြစ်သည်။

### 3.1 `setdefault()` နှင့် `dict[key] = value` ၏ ကွာခြားချက်
```python
props = {}
props.setdefault(("Person", "ada"), {"name": "Ada Lovelace"})
props.setdefault(("Person", "ada"), {"name": "overwrite?"})
print(props[("Person", "ada")])

other = {}
other[("Person", "ada")] = {"name": "Ada Lovelace"}
other[("Person", "ada")] = {"name": "overwrite"}
print(other[("Person", "ada")])
```

Output —
```text
{'name': 'Ada Lovelace'}
{'name': 'overwrite'}
```

`setdefault(key, value)` သည် key **မရှိလျှင်သာ** value ကို ထည့်သည်။ `dict[key] = value` သည်
key ရှိပြီးသားဖြစ်လျှင်လည်း အပေါ်ရေးလိုက်သည်။ Code က `setdefault` ကို သုံးထားသည်မှာ
`MERGE ... ON CREATE SET` နှင့် တူညီသည့် အပြုအမူ ဖြစ်သည် — node **အသစ်** ဖြစ်မှသာ
property ကို ချမှတ်သည်။ ရှိပြီးသား node အတွက် property ပြောင်းလဲမှုကို အထက်က
`node_props[key]["name"] = name` လိုင်းက သီးသန့် လုပ်သည် (`ON MATCH SET`)။

---
## 4. `write_edge()` — Edge identity တွင် `chunk_id` ပါဝင်သည်
Edge key သည် field **၆ ခု** ပါသည် —

```python
key = (head_label, head_id, rel_type, tail_label, tail_id, chunk_id)
```

Node key တွင် field ၂ ခုသာ ရှိသည်နှင့် နှိုင်းယှဉ်ပါ။ Edge တွင် endpoint နှစ်ခု၏ identity
နှင့် provenance (`chunk_id`) ပါဝင်သည်။ ဤကြောင့် triple `t1` (`c01`) နှင့် `t6` (`c04`) သည်
head/tail/rel တူညီသော်လည်း edge **နှစ်ခု** ဖြစ်လာသည်။
```python
g = InMemoryGraph("merge")
g.write_node("Person", "ada_lovelace", "Ada Lovelace")
g.write_node("Organization", "analytical_engine_project", "Analytical Engine Project")
g.write_edge("Person", "ada_lovelace", "WORKED_AT", "Organization",
             "analytical_engine_project", "c01", 0.93)
g.write_edge("Person", "ada_lovelace", "WORKED_AT", "Organization",
             "analytical_engine_project", "c01", 0.90)
print("same chunk_id twice : edges=%d edges_matched=%d"
      % (g.edge_count(), g.stats["edges_matched"]))
print("confidence now      :", g.edge_props[("Person", "ada_lovelace", "WORKED_AT",
                                             "Organization",
                                             "analytical_engine_project", "c01")])
g.write_edge("Person", "ada_lovelace", "WORKED_AT", "Organization",
             "analytical_engine_project", "c04", 0.79)
print("other chunk_id      : edges=%d" % g.edge_count())
```

Output —
```text
same chunk_id twice : edges=1 edges_matched=1
confidence now      : 0.9
other chunk_id      : edges=2
```

ပထမ နှစ်ကြိမ်သည် key တူညီသဖြင့် edge တစ်ခုတည်း ဖြစ်ပြီး confidence ကို update လုပ်သည်
(`edges_matched=1`)။ `chunk_id` ကွာသည့် တတိယ call သည် edge အသစ် ဖြစ်လာသည်။

`chunk_id` ကို edge identity ထဲ ထည့်ခြင်း၏ trade-off —

- **အားသာချက်** — evidence များစွာ (chunk များစွာ) က triple တစ်ခုကို ထောက်ခံသည့်အခါ
  ထောက်ခံချက် တစ်ခုစီကို ခွဲထားနိုင်ပြီး တစ်ခု ပြောင်းလဲသည့်အခါ ကျန်တာကို မထိခိုက်ပါ။
- **အားနည်းချက်** — `MATCH (h)-[r:WORKED_AT]->(t)` သည် edge များစွာ ပြန်ပေးနိုင်သဖြင့်
  query ရေးသည့်အခါ aggregation (`max(r.confidence)` ကဲ့သို့) လိုအပ်လာသည်။

---
## 5. `apply_batch()` — Nested loop ဖြင့် batch တစ်ခုလုံး ရေးခြင်း
```python
for st in statements:            # batch တစ်ခုချင်း
    head_label, rel_type, tail_label = st["group"]   # tuple unpacking
    for row in st["rows"]:       # row တစ်ခုချင်း
        ...
```

`head_label, rel_type, tail_label = st["group"]` သည် tuple ၃ ခုကို variable ၃ ခုအဖြစ်
ခွဲယူသည်။ Row တိုင်းအတွက် **node နှစ်ခု → edge တစ်ခု** အစီအစဉ်ဖြင့် ရေးသည်။
ဤအစီအစဉ်သည် အရေးကြီးသည် — endpoint node များ မရှိသေးဘဲ edge ရေးလျှင် orphan
ဖြစ်သည် (Section 8 တွင် ပြထားသည်)။
```python
graph = InMemoryGraph("merge")
statements = build_batch_statements(TRIPLES)
apply_batch(graph, statements)
print("statements=%d  nodes=%d  edges=%d"
      % (len(statements), graph.node_count(), graph.edge_count()))
print("node_keys:", sorted(graph.node_keys))
```

Output —
```text
statements=5  nodes=5  edges=6
node_keys: [('Location', 'london'), ('Organization', 'analytical_engine_project'), ('Person', 'ada_lovelace'), ('Person', 'charles_babbage'), ('Technology', 'analytical_engine')]
```

Node စုစုပေါင်း ၅ ခု ရသည် — `ada_lovelace`၊ `analytical_engine_project`၊
`analytical_engine`၊ `charles_babbage`၊ `london`။ Triple ၆ ခုရှိသော်လည်း node ၅ ခုသာ
ဖြစ်သည်မှာ entity တစ်ခုကို multiple triple များက ရည်ညွှန်းသောကြောင့် ဖြစ်သည် —
`Ada Lovelace` သည် triple ၄ ခုတွင် ပါသည်။ `merge` semantics ကြောင့်သာ ဤအခြေအနေ
ဖြစ်နိုင်သည်။ Edge ၆ ခုမှာ triple ၆ ခုနှင့် တူညီသည် — `t1` နှင့် `t6` သည်
`chunk_id` ကွာသဖြင့် မပေါင်းပါ။

---
## 6. `MERGE` နှင့် `CREATE` — pass နှစ်ခု နှိုင်းယှဉ်ခြင်း
ဤသည်မှာ Exercise ၏ အဓိကစမ်းသပ်ချက် ဖြစ်သည် — input အတိအကျကို **နှစ်ကြိမ်**
apply လုပ်ပြီး graph အရေအတွက် ပြောင်းမပြောင်း တိုင်းတာသည်။
```python
statements = build_batch_statements(TRIPLES)

merged = InMemoryGraph("merge")
apply_batch(merged, statements)
merge_first = (merged.node_count(), merged.edge_count())
apply_batch(merged, statements)
merge_second = (merged.node_count(), merged.edge_count())

created = InMemoryGraph("create")
apply_batch(created, statements)
create_first = (created.node_count(), created.edge_count())
apply_batch(created, statements)
create_second = (created.node_count(), created.edge_count())

print("MERGE  pass1 nodes/edges=%s  pass2=%s" % (merge_first, merge_second))
print("CREATE pass1 nodes/edges=%s  pass2=%s" % (create_first, create_second))
```

Output —
```text
MERGE  pass1 nodes/edges=(5, 6)  pass2=(5, 6)
CREATE pass1 nodes/edges=(12, 6)  pass2=(24, 12)
```

ရလဒ်ကို ဇယားဖြင့် —

| Semantics | pass 1 `(nodes, edges)` | pass 2 `(nodes, edges)` | Idempotent? |
| --- | --- | --- | --- |
| `merge` | `(5, 6)` | `(5, 6)` | ✓ ရသည် |
| `create` | `(12, 6)` | `(24, 12)` | ✗ မရပါ |

`create` ၏ pass 1 တွင် node 12 ဖြစ်ခြင်းကို ရှင်းပြရန် — row ၆ ခုရှိပြီး row တိုင်းအတွက်
node **နှစ်ခု** ရေးသဖြင့် write_node call ၁၂ ကြိမ် ဖြစ်သည်။ `create` သည် blind append
လုပ်သဖြင့် node ၁၂ ခု ဖြစ်သည် (`merge` က ၅ ခုသာ)။ Pass 2 တွင် node ၁၂ ခု ထပ်တိုးပြီး
edge ကလည်း ၆ → ၁၂ ဖြစ်လာသည် — ဤသည်မှာ idempotency မရှိသည့် write path ၏ လက္ခဏာ
ဖြစ်သည်။

`merge` ၏ pass 2 တွင် edge အရေအတွက် ၆ မှ ၁၂ မဖြစ်ရခြင်းမှာ edge key တွင် `chunk_id`
ပါဝင်ပြီး pass ၂ တွင် key တူညီသည့် edge များကို `edges_matched` သာ တိုးစေလို့ဖြစ်သည်။

---
## 7. Counter များကို ဖတ်ခြင်း — Observability
`stats` dict သည် အလုပ်လုပ်မှုကို မျက်စိဖြင့် မြင်နိုင်စေသည်။ Pass တစ်ခုချင်း ပြီးတိုင်း
counter ကို ဖတ်ကြည့်ပါ။
```python
statements = build_batch_statements(TRIPLES)

merged = InMemoryGraph("merge")
apply_batch(merged, statements)
print("MERGE after pass1 :", merged.stats)
apply_batch(merged, statements)
print("MERGE after pass2 :", merged.stats)

created = InMemoryGraph("create")
apply_batch(created, statements)
print("CREATE after pass1:", created.stats)
apply_batch(created, statements)
print("CREATE after pass2:", created.stats)
```

Output —
```text
MERGE after pass1 : {'nodes_created': 5, 'nodes_matched': 7, 'edges_created': 6, 'edges_matched': 0}
MERGE after pass2 : {'nodes_created': 5, 'nodes_matched': 19, 'edges_created': 6, 'edges_matched': 6}
CREATE after pass1: {'nodes_created': 12, 'nodes_matched': 0, 'edges_created': 6, 'edges_matched': 0}
CREATE after pass2: {'nodes_created': 24, 'nodes_matched': 0, 'edges_created': 12, 'edges_matched': 0}
```

MERGE ၏ counter များကို ခွဲဖတ်ပါ —

| Counter | pass 1 ပြီးနောက် | pass 2 ပြီးနောက် | အဓိပ္ပာယ် |
| --- | --- | --- | --- |
| `nodes_created` | 5 | 5 (မပြောင်း) | node အသစ် ၅ ခု — pass 2 တွင် အသစ် မရှိ |
| `nodes_matched` | 7 | 19 | call ၁၂ ကြိမ်အနက် pass 1 တွင် ၇ ခု match၊ pass 2 တွင် ၁၂ ခုလုံး |
| `edges_created` | 6 | 6 (မပြောင်း) | edge အသစ် ၆ ခု |
| `edges_matched` | 0 | 6 | pass 2 တွင် edge ၆ ခုလုံး ရှိပြီးသား |

ဤ counter များသည် production တွင် ရောဂါရှာဖွေရန် သုံးသည် —

- `nodes_created` ၏ **pass တစ်ခုအတွင်း တိုးလာမှု (delta) သည် 0** ဖြစ်နေလျှင် input အသစ်
  မဝင်ခြင်းကို ညွှန်းသည် (သို့မဟုတ် extraction က အလွတ် ပြန်နေခြင်း)။ Counter သည်
  cumulative ဖြစ်သဖြင့် တန်ဖိုးကိုယ်တိုင် မဟုတ်ဘဲ **အဆင့်နှစ်ခုကြား ကွာခြားချက်** ကို
  ကြည့်ရသည် — ဤ run တွင် pass 1 ပြီး 5 ဖြစ်ပြီး pass 2 ပြီးလည်း 5 ဖြစ်သည် (delta 0)။
- `nodes_matched` သည် created ထက် အဆမတန်ကြီးနေလျှင် တူညီသော input ကို
  ထပ်ခါတလဲလဲ ပို့နေခြင်း (retry storm သို့မဟုတ် scheduler နှစ်ဆ) ဖြစ်သည်။

`create` ၏ counter များတွင် `nodes_matched` နှင့် `edges_matched` သည် 0 ဖြစ်သည် —
match လုပ်ခြင်း လုံးဝ မရှိပါ။ ထို့ကြောင့် duplicate ရှိမရှိကို `create` semantics ဖြင့်
counter ဖတ်၍ မသိနိုင်ပါ — graph ကို စစ်ရမည်။

---
## 8. ရှောင်ရမည့် trap — binding မရှိသော variable ဖြင့် `MERGE (a)-[:R]->(b)`
Neo4j ၏ documented semantics အရ `MERGE` သည် **pattern တစ်ခုလုံး** မတွေ့လျှင်
pattern အပြည့်ကို ဖန်တီးသည်။ `a` နှင့် `b` ကို အထက်တွင် `MATCH` သို့မဟုတ် `MERGE`
ဖြင့် binding မလုပ်ထားလျှင် ၎င်းတို့သည် **label မရှိ၊ property မရှိသော node အသစ်**
နှစ်ခု ဖြစ်လာသည်။ ထို node များကို `MATCH (h:Person {id: $id})` ဖြင့် ဘယ်တော့မှ
ရှာမတွေ့တော့ပါ။

မှားသော form —

```cypher
// ဤ statement သည် run ဖြစ်သည်၊ သို့သော် label မရှိသော node နှစ်ခု ဖန်တီးလိုက်သည်
MERGE (a)-[:COLLABORATED_WITH {chunk_id: $chunk_id}]->(b)
```

မှန်သော form (ဤ module ထုတ်ပေးသည့် form) —

```cypher
MERGE (h:Person {id: row.head_id})
  ON CREATE SET h.name = row.head_name
MERGE (t:Person {id: row.tail_id})
  ON CREATE SET t.name = row.tail_name
MERGE (h)-[r:COLLABORATED_WITH {chunk_id: row.chunk_id}]->(t)
  ON CREATE SET r.confidence = row.confidence
  ON MATCH SET r.confidence = row.confidence
```

Endpoint node များကို **အရင်** MERGE လုပ်ပြီးမှ relationship ကို MERGE လုပ်ခြင်းဖြင့်
`h` နှင့် `t` သည် binding ရပြီးသား ဖြစ်နေသည်။ အောက်က code သည် ဤကွာခြားချက်ကို
simulator ပေါ်တွင် တိုင်းတာသည် — `naive` လိုင်းက `write_edge()` ကိုသာ ခေါ်သည်
(real Cypher တွင် `MERGE (a)-[:R]->(b)` ၏ equivalent)၊ `correct` လိုင်းက node နှစ်ခုကို
label နှင့်တကွ အရင် ရေးသည်။
```python
# မှားသော form — MERGE (a)-[:R]->(b) တွင် a, b ကို binding မလုပ်ထားပါ
g = InMemoryGraph("merge")
g.write_edge(None, "ada_lovelace", "COLLABORATED_WITH", None, "charles_babbage",
             "c02", 0.84)
print("naive  : nodes=%d edges=%d node_keys=%s"
      % (g.node_count(), g.edge_count(), g.node_keys))

# မှန်သော form — node နှစ်ခုကို label နှင့်တကွ အရင် MERGE လုပ်သည်
h = InMemoryGraph("merge")
h.write_node("Person", "ada_lovelace", "Ada Lovelace")
h.write_node("Person", "charles_babbage", "Charles Babbage")
h.write_edge("Person", "ada_lovelace", "COLLABORATED_WITH", "Person",
             "charles_babbage", "c02", 0.84)
print("correct: nodes=%d edges=%d node_keys=%s"
      % (h.node_count(), h.edge_count(), h.node_keys))
```

Output —
```text
naive  : nodes=0 edges=1 node_keys=[]
correct: nodes=2 edges=1 node_keys=[('Person', 'ada_lovelace'), ('Person', 'charles_babbage')]
```

| လမ်းကြောင်း | nodes | edges | node_keys | `MATCH (:Person {id:…})` ဖြင့် ရှာတွေ့မလား |
| --- | --- | --- | --- | --- |
| `naive` (`MERGE (a)-[:R]->(b)`) | 0 | 1 | `[]` | မတွေ့ပါ — label မရှိသော node များသာ ရှိသည် |
| `correct` (node အရင်) | 2 | 1 | `('Person','ada_lovelace')`, `('Person','charles_babbage')` | တွေ့သည် |

Simulation က node မှတ်တမ်း လုံးဝ မရှိဘဲ edge တစ်ခုသာ ရှိသည်ကို ပြသည်။ ဤသည်မှာ
server ပေါ်တွင် "label မရှိသော node နှစ်ခု + edge တစ်ခု" ဖြစ်ခြင်း၏ equivalent ဖြစ်သည် —
ပြဿနာမှာ error မဖြစ်ခြင်း ဖြစ်သည်။ Statement သည် အောင်မြင်စွာ run ပြီး graph ထဲ
ရှာမတွေ့နိုင်သော node များ ကျန်ခဲ့သည်။ ထို့ကြောင့် **table prefix** နှင့် **relationship
type** ကို မည်သည့်အခါမျှ LLM output မှ တိုက်ရိုက် မထည့်ရ** — allowlist mapping
(Walkthrough 01 Section 2) မှသာ ထည့်ရသည်။

---
## 9. Code တစ်ခုလုံး — Run လုပ်နိုင်သော Version
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


statements = build_batch_statements(TRIPLES)
merged = InMemoryGraph("merge")
apply_batch(merged, statements)
first_pass = (merged.node_count(), merged.edge_count())
apply_batch(merged, statements)
second_pass = (merged.node_count(), merged.edge_count())

created = InMemoryGraph("create")
apply_batch(created, statements)
create_first = (created.node_count(), created.edge_count())
apply_batch(created, statements)
create_second = (created.node_count(), created.edge_count())

print("MERGE  pass1 nodes/edges=%s  pass2=%s" % (first_pass, second_pass))
print("CREATE pass1 nodes/edges=%s  pass2=%s" % (create_first, create_second))
print("MERGE counters: %s" % merged.stats)
```

Output —
```text
MERGE  pass1 nodes/edges=(5, 6)  pass2=(5, 6)
CREATE pass1 nodes/edges=(12, 6)  pass2=(24, 12)
MERGE counters: {'nodes_created': 5, 'nodes_matched': 19, 'edges_created': 6, 'edges_matched': 6}
```

---
## 10. ကိုယ်တိုင်လေ့ကျင့်ကြည့်ပါ

**မေးခွန်း** — `semantics="create"` ဖြင့် triple **တစ်ခု**ကို (node နှစ်ခု + edge တစ်ခု)
နှစ်ကြိမ် ရေးလျှင် `node_count()` နှင့် `edge_count()` က ဘာဖြစ်မလဲ။
```python
# semantics="create" — triple တစ်ခုတည်းကို နှစ်ကြိမ် ရေးသည်
g = InMemoryGraph("create")
for _ in range(2):
    g.write_node("Person", "ada_lovelace", "Ada Lovelace")
    g.write_node("Organization", "analytical_engine_project",
                 "Analytical Engine Project")
    g.write_edge("Person", "ada_lovelace", "WORKED_AT", "Organization",
                 "analytical_engine_project", "c01", 0.93)
print("nodes =", g.node_count())
print("edges =", g.edge_count())
```

1. `nodes = 2`၊ `edges = 1`
2. `nodes = 4`၊ `edges = 2`
3. `nodes = 2`၊ `edges = 2`
4. `nodes = 4`၊ `edges = 1`

<details>
<summary>အဖြေ ကြည့်ရန်</summary>

**အဖြေ — 2. `nodes = 4`၊ `edges = 2`**

အကြောင်းရင်း — `create` semantics တွင် `key in self.node_props` branch ကို လုံးဝ
မဝင်သဖြင့် `write_node()` call တိုင်း `nodes_created` ကို တိုးပြီး `node_keys` ထဲ
အဖွဲ့ဝင် အသစ် ထည့်သည်။ Field ၂ ခုပါ key တူညီသည့် အဖွဲ့ဝင် နှစ်ခု ရှိလာသည်။
Loop နှစ်ကြိမ်အတွက် node ၂×၂ = ၄ ခု၊ edge ၁×၂ = ၂ ခု ဖြစ်သည်။ အထက်က run ၏
output က ဤအချက်ကို အတည်ပြုသည် — `nodes = 4`၊ `edges = 2`။

`edges = 1` ဖြစ်သည်ဟု ထင်ရလျှင် ထို *edge နှစ်ခုသည် key တူညီသည်* ဆိုသည်မှာ
မှန်သည် — သို့သော် `node_keys`/`edge_keys` list သည် key များကို **ထပ်ခါတလဲလဲ**
သိမ်းနိုင်သည်; dedupe လုပ်ခြင်းသည် `merge` semantics ၏ တာဝန်သာ ဖြစ်သည်။

</details>

---

**အဓိက မှတ်ထားရန်** — `MERGE` သည် idempotent write path ၏ အခြေခံ ဖြစ်သည်: identity key
တူညီလျှင် ရှိပြီးသား node/edge ကို match လုပ်ပြီး property ကိုသာ update လုပ်သည်။
`CREATE` သည် blind append ဖြစ်သဖြင့် re-run တိုင်း graph ပွားလာသည်။ Idempotency ကို
counter (`nodes_created`၊ `nodes_matched`) ဖြင့် တိုင်းတာရသည် — pass ၂ တွင်
`nodes_created` ၏ **delta = 0** ဖြစ်ခြင်းသည် "အသစ် မရှိ" ဟု ဆိုလိုသည် (counter သည်
cumulative ဖြစ်သဖြင့် တန်ဖိုးကိုယ်တိုင် 0 မဟုတ်ဘဲ တိုးလာမှု 0 ဖြစ်သည်)။
Idempotency ရရှိရန်
endpoint node များကို relationship မတိုင်မီ binding လုပ်ရသည်; binding မရှိသော
`MERGE (a)-[:R]->(b)` သည် error မပေးဘဲ label မရှိသော node များ ဖန်တီးသည်။
