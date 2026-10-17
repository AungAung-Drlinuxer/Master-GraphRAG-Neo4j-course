# Walkthrough 01 — Property Graph in-memory model (Exercise 1)

> ဤဖိုင်သည် Module 05 ၏ `solution.md` ထဲက Exercise 1 ကို **Python အခြေခံမှ စ၍**
> အပိုင်းလိုက် ရှင်းပြသည့် walkthrough ဖြစ်သည်။ Format သည် Module 01 ၏
> `walkthroughs/01_regex_ner.md` နှင့် `03_gazetteer_lookup.md` နှင့် တူညီသည်။
> `@dataclass`၊ `field(default_factory=...)`၊ `**kwargs`၊ `setdefault()`၊ `raise`၊
> `try/except` စသည့် Python concept များကို ဤနေရာတွင် ရှင်းပြသည်။

---

## 0. ဤ Exercise က ဘာကို ဖြေရှင်းပေးသလဲ။

Neo4j သို့ မချိတ်ဆက်မီ Knowledge Graph တစ်ခုကို **memory ထဲတွင်** ကိုယ်စားပြုနိုင်ရမည်။
Graph ဆိုသည်မှာ node များနှင့် ၎င်းတို့ကို ဆက်သွယ်သော directed typed relationship များ
ဖြစ်သည်။ ဤ Exercise က Neo4j ၏ Property Graph model ကို Python ဖြင့် ပုံစံတူ တည်ဆောက်သည်။

```text
(p1:Person {name:"Aung Aung", age:34}) --KNOWS {since:2019}--> (p2:Person {name:"Su Su"})
(p1:Person) --WORKS_AT {role:"Data Engineer"}--> (c1:Company {name:"GraphRAG Labs"})
(p2:Person) --WORKS_AT {role:"ML Engineer"}-->  (c1:Company)
(c1:Company) --USES {since:2021}--> (t1:Technology {name:"Neo4j"})
(p1:Person)  --USES {since:2024}--> (t1:Technology)
```

Node ၄ ခု၊ relationship ၅ ခု ရှိသည်။ ဤဖိုင်ပြီးဆုံးလျှင် —

- `Node`/`Relationship` ကို `@dataclass` ဖြင့် ကိုယ်စားပြုပုံ
- Graph တစ်ခုကို **outgoing/incoming adjacency map** ဖြင့် store လုပ်ပုံ
- relationship သွင်းသည့်အခါ endpoint စစ်ဆေးပုံ (`raise ValueError`)
- `degree` (in + out) နှင့် `out_edges` တွက်ပုံ

ကို ရရှိမည်။ ဤ code မှာ လေ့လာရမည့် Python concepts — `@dataclass`၊
`field(default_factory=dict)`၊ type hint (`Tuple[str, ...]`, `Dict[str, object]`)၊
`**props` keyword capture၊ `dict(props)` copy၊ `tuple(labels)`၊ `setdefault()`၊
`self.` attribute၊ `raise`/`try`/`except`၊ dict comprehension ။

---

## 1. `@dataclass` — data holder class ကို အတိုချုံ့ ရေးခြင်း

Node တစ်ခုကို ကိုယ်စားပြုရန် `id`၊ `labels`၊ `properties` သုံးခု လိုသည်။ ပုံမှန် class
ရေးလျှင် `__init__`၊ `__repr__`၊ `__eq__` ကို ကိုယ်တိုင် ရေးရမည်။ `@dataclass` က
ထို boilerplate ကို field declaration မှ အလိုအလျောက် ဖန်တီးပေးသည်။

```python
from dataclasses import dataclass, field
from typing import Dict, Tuple


@dataclass
class Node:
    id: str
    labels: Tuple[str, ...]
    properties: Dict[str, object] = field(default_factory=dict)


n = Node("p1", ("Person",), {"name": "Aung Aung", "age": 34})
print(n)
print(n.id, n.labels, n.properties)
print(n.labels[0])
print(repr(n))
```

Output —

```text
Node(id='p1', labels=('Person',), properties={'name': 'Aung Aung', 'age': 34})
p1 ('Person',) {'name': 'Aung Aung', 'age': 34}
Person
Node(id='p1', labels=('Person',), properties={'name': 'Aung Aung', 'age': 34})
```

`print(n)` က `n.__repr__()` ကို ခေါ်သည်။ Dataclass က `__repr__` ကို အလိုအလျောက်
ထောက်ပံ့သဖြင့် `Node(id=..., labels=..., properties=...)` ပုံစံ ရသည်။ Debug လုပ်ရာတွင်
ဤ repr သည် field တစ်ခုချင်းစီကို ပြသသဖြင့် အသုံးဝင်သည်။

`Dict[str, object]` အစရှိသည့် type hint များသည် **documentation** သာဖြစ်သည် —
Python က runtime တွင် မစစ်ဆေးပါ။ သို့သော် reader နှင့် editor အတွက် intent ကို
ရှင်းစေသဖြင့် course တစ်ခုလုံးတွင် တူညီစွာ သုံးသည်။

### `==` နှင့် `is` — `@dataclass` က `__eq__` ကို ပေးသည်

Dataclass က `__eq__` ကို field များ တူ/မတူ နှိုင်းယှဉ်ရန် အလိုအလျောက် ဖန်တီးပေးသည်။

```python
from dataclasses import dataclass, field
from typing import Dict, Tuple


@dataclass
class Node:
    id: str
    labels: Tuple[str, ...]
    properties: Dict[str, object] = field(default_factory=dict)


a = Node("p1", ("Person",))
b = Node("p1", ("Person",))
c = Node("p1", ("Person",), {"age": 34})
print("a == b :", a == b)
print("a is b :", a is b)
print("a == c :", a == c)
```

Output —

```text
a == b : True
a is b : False
a == c : False
```

`a == b` က `True` ဖြစ်သည် — field တန်ဖိုးများ တူညီသည်။ `a is b` က `False` ဖြစ်သည် —
object နှစ်ခုက memory တွင် မတူညီသော instance များ ဖြစ်သည်။ `a == c` က `False` ဖြစ်သည် —
`properties` မတူပါ။ ဤခွဲခြားမှုသည် assertion တွင်အရေးပါသည် — `assert a == b` က
တန်ဖိုး နှိုင်းယှဉ်သည်၊ identity နှိုင်းယှဉ်သည်မဟုတ်။

---

## 2. `field(default_factory=dict)` — mutable default ကို ရှောင်ခြင်း

`properties` တွင် default လိုသည်။ သို့သော် dict ကို တိုက်ရိုက် default အဖြစ် ပေးခြင်းသည်
အန္တရာယ်ရှိသည် — အားလုံးသော instance များ **dict တစ်ခုတည်း**ကို share လုပ်သွားမည်။
`@dataclass` က ဤအမှားကို class ဖန်တီးချိန်တွင်ပင် ငြင်းပယ်သည်။

```python
from dataclasses import dataclass, field

try:
    @dataclass
    class Bad:
        props: dict = {}
    print("no error:", Bad().props)
except ValueError as exc:
    print("ValueError:", exc)


@dataclass
class Good:
    props: dict = field(default_factory=dict)


ga, gb = Good(), Good()
ga.props["k"] = 1
print("good a :", ga.props)
print("good b :", gb.props)
```

Output —

```text
ValueError: mutable default <class 'dict'> for field props is not allowed: use default_factory
good a : {'k': 1}
good b : {}
```

Error က **class definition ဖတ်သည့်အခါ** (instance မဖန်တီးမီ) ပေါ်လာသည် — runtime အထိ
မစောင့်ပါ။ ဒါကြောင့် ဤအန္တရာယ်ကို မတော်တဆ ကျော်လွန်၍ မရနိုင်ပါ။

`field(default_factory=dict)` က instance တစ်ခုစီအတွက် **dict အသစ်** ကို ဖန်တီးပေးသည်။
`ga` ကို ပြင်လိုက်သော်လည်း `gb` မပြောင်းသည်ကို output တွင် တွေ့ရသည်။ Property Graph
member တိုင်းတွင် ကိုယ်ပိုင် `properties` dict ရှိရမည်ဖြစ်သဖြင့် ဤနည်းသည် မဖြစ်မနေ လိုသည်။

---

## 3. `**props` နှင့် `dict(props)` — keyword argument များကို ဖမ်းခြင်း

Caller က `add_node("p1", ("Person",), name="Aung Aung", age=34)` လို့ ခေါ်နိုင်ရမည်။
Property အရေအတွက် ကြိုမသိသဖြင့် `**props` ဖြင့် keyword argument အားလုံးကို dict
အဖြစ် ဖမ်းသည်။

```python
def add_node(node_id, labels, **props):
    print("props dict  :", props)
    return node_id, tuple(labels), dict(props)


print(add_node("p1", ("Person",), name="Aung Aung", age=34))
print(add_node("t1", ("Technology",)))
```

Output —

```text
props dict  : {'name': 'Aung Aung', 'age': 34}
('p1', ('Person',), {'name': 'Aung Aung', 'age': 34})
props dict  : {}
('t1', ('Technology',), {})
```

`**props` သည် function parameter တွင် **dict** ဖြစ်ပြီး၊ function ကို ခေါ်သည့်အခါ
`key=value` အတွဲများအဖြစ် ဖြန့်သည်။ Property မပေးလျှင် `props` က empty dict `{}` ဖြစ်သည် —
error မဖြစ်ပါ။

`dict(props)` သည် **copy** ဖန်တီးသည်။ ဒါက အရေးကြီးသည် — `props` ကို တိုက်ရိုက်
သိမ်းလျှင် caller ဖြတ်သွားသော object နှင့် share ဖြစ်နိုင်သည်။ `dict(...)` သည် မိမိ
ကိုယ်ပိုင် copy ဖြစ်စေသည်။

---

## 4. `tuple(labels)` — label list ကို မပြောင်းနိုင်စေခြင်း

Node တစ်ခုတွင် label တစ်ခုထက် ပိုရှိနိုင်သည် (ဥပမာ `Person` နှင့် `Employee`)။
`labels` ကို `Tuple[str, ...]` အဖြစ် သိမ်းသည်။

```python
labels_list = ["Person"]
labels_tuple = tuple(labels_list)
print(labels_list, type(labels_list).__name__)
print(labels_tuple, type(labels_tuple).__name__)
labels_list.append("Employee")
print("after list append :", labels_list)
print("tuple unchanged   :", labels_tuple)
```

Output —

```text
['Person'] list
('Person',) tuple
after list append : ['Person', 'Employee']
tuple unchanged   : ('Person',)
```

`tuple(labels)` သည် list မှ tuple အသစ် **copy** ဖန်တီးသည်။ ပြီးနောက် list ကို ပြင်လျှင်
tuple မပြောင်းသည်ကို output တွင် တွေ့ရသည်။ Label သည် node ၏ identity ကို ဆုံးဖြတ်သော
အချက်ဖြစ်သဖြင့် နောက်ပိုင်း မတော်တဆ ပြောင်းမသွားစေရန် immutable tuple ဖြင့် ထားသည်။

`(<element>,)` ပုံစံတွင် **comma** လိုသည် — `("Person")` က string သာဖြစ်သည်၊
`("Person",)` ကသာ tuple ဖြစ်သည်။

---

## 5. `setdefault()` — adjacency list ကို လုံခြုံစွာ တည်ဆောက်ခြင်း

`PropertyGraph` က node များကို `out_adj` နှင့် `in_adj` ဆိုသော dict နှစ်ခုတွင် ထားသည်။
`out_adj[node_id]` က ထို node မှ ထွက်သော `(rel_type, target_id)` tuple စာရင်းဖြစ်သည်။
`setdefault(key, default)` က key မရှိလျှင် default ကို ထည့်ပြီး ပြန်ပေးသည်။

```python
out_adj = {}
out_adj.setdefault("p1", []).append(("KNOWS", "p2"))
out_adj.setdefault("p1", []).append(("USES", "t1"))
out_adj.setdefault("t1", [])
print(out_adj)
print("len:", len(out_adj))
```

Output —

```text
{'p1': [('KNOWS', 'p2'), ('USES', 't1')], 't1': []}
len: 2
```

ပထမ `setdefault("p1", [])` က list အသစ် ဖန်တီးပြီး ထည့်သည်။ ဒုတိယအကြိမ် ခေါ်သည့်အခါ
`p1` ရှိပြီးဖြစ်သဖြင့် **ရှိပြီးသား list** ကို ပြန်ပေးသည် — ထပ်မဖန်တီးပါ။ ဒါကြောင့်
`append` နှစ်ခုလုံး list တစ်ခုတည်းထဲ ရောက်သည်။ `if key not in out_adj: out_adj[key] = []`
လို့ နှစ်လိုင်းရေးရသည်ကို `setdefault` က တစ်လိုင်းတည်း ဖြစ်စေသည်။

`in_adj` က လားရာ (direction) ကို ထိန်းထားရန် လိုသည် — မဟုတ်ပါက `(a)<-[:R]-(b)` လို
ပြောင်းပြန် pattern ကို ရှာရန် graph တစ်ခုလုံး scan ရမည်။ ဤအချက်သည် Neo4j ၏
doubly-linked relationship record ကို ပုံစံတူ ကိုယ်စားပြုသည်။

---

## 6. `add_relationship` နှင့် `raise ValueError`

Relationship သွင်းသည့်အခါ endpoint node နှစ်ခုလုံး ရှိရမည်။ မရှိလျှင် `raise` ဖြင့်
ရပ်လိုက်သည်။

```python
if start not in self.nodes or end not in self.nodes:
    raise ValueError("relationship endpoint မရှိသော node: " + start + " / " + end)
```

ဤ fragment ကို သတိထားကြည့်ပါ — `in` ဖြင့် dict ၏ **key** များထဲ ရှိမရှိ စစ်သည်။
Node id သည် `self.nodes` ၏ key ဖြစ်သည်။ `or` သည် short-circuit ဖြစ်သဖြင့်
တစ်ခုခု မရှိသည်နှင့် ရပ်သည်။

```python
g = build_sample_graph()
try:
    g.add_relationship("KNOWS", "p1", "ghost")
except ValueError as exc:
    print("ValueError :", exc)
print("relationships after failed add :", len(g.relationships))
print("out_edges(p1) :", g.out_edges("p1"))
print("out_edges(zz) :", g.out_edges("zz"))
```

Output —

```text
ValueError : relationship endpoint မရှိသော node: p1 / ghost
relationships after failed add : 5
out_edges(p1) : [('KNOWS', 'p2'), ('WORKS_AT', 'c1'), ('USES', 't1')]
out_edges(zz) : []
```

`try/except` ဖြင့် error ကို ဖမ်းပြီး program ကို ဆက်လုပ်စေသည်။ `ghost` node မရှိသဖြင့်
`raise` ဖြစ်သော်လည်း **relationship မထည့်ရသေးမီ** ရပ်လိုက်သဖြင့် `relationships` သည်
၅ ခုတွင်ပင် ရှိနေသည်။ ဤအစီအစဉ်သည် အရေးကြီးသည် — validation ကို mutation မတိုင်မီ
လုပ်ခြင်းဖြင့် မပြည့်စုံသော state ကို ရှောင်သည်။

`out_edges("zz")` က `[]` ပြန်သည် — `self.out_adj.get("zz", [])` တွင် default `[]` ပါသဖြင့်
`KeyError` မဖြစ်ပါ။ မသိသော node အတွက် crash မလုပ်ဘဲ empty list ပြန်ခြင်းသည်
traversal code အတွက် ပိုလုံခြုံသည်။

---

## 7. `build_sample_graph()` — sample graph တည်ဆောက်ခြင်း

Node ၄ ခု၊ relationship ၅ ခု ထည့်သည့် helper ဖြစ်သည်။ `add_node`/`add_relationship` ကို
အစဉ်လိုက် ခေါ်ပြီး graph တစ်ခုလုံး ဖန်တီးသည်။

```python
g = build_sample_graph()
print("nodes :", len(g.nodes), sorted(g.nodes))
print("rels  :", len(g.relationships))
print("labels:", sorted({lb for n in g.nodes.values() for lb in n.labels}))
for nid in sorted(g.nodes):
    print("%-3s out=%-45s in=%s" % (nid, g.out_adj[nid], g.in_adj[nid]))
```

Output —

```text
nodes : 4 ['c1', 'p1', 'p2', 't1']
rels  : 5
labels: ['Company', 'Person', 'Technology']
c1  out=[('USES', 't1')]                              in=[('WORKS_AT', 'p1'), ('WORKS_AT', 'p2')]
p1  out=[('KNOWS', 'p2'), ('WORKS_AT', 'c1'), ('USES', 't1')] in=[]
p2  out=[('WORKS_AT', 'c1')]                          in=[('KNOWS', 'p1')]
t1  out=[]                                            in=[('USES', 'c1'), ('USES', 'p1')]
```

`%-3s` နှင့် `%-45s` သည် column များကို တန်းညှိရန် space ဖြည့်သည်။ `p1` ၏
out list သည် စာလုံး ၄၅ ခုထက် ရှည်သဖြင့် ဖြည့်ရန် မလိုတော့ဘဲ ညာဘက် column က
တိုသွားသည်ကို တွေ့ရသည်။

`sorted({lb for n in g.nodes.values() for lb in n.labels})` ကို ခွဲဖတ်ကြည့်ရအောင်။

- `g.nodes.values()` — Node object များ၏ value list။
- `for n in ...` — Node တစ်ခုချင်းစီ။
- `for lb in n.labels` — ထို node ၏ label တစ်ခုချင်းစီ။
- `{...}` — **set comprehension** — ထပ်နေသော label များကို ဖျောက်သည်။
- `sorted(...)` — set ကို စီထားသော list အဖြစ် ပြောင်းသည်။

`labels` ကို `sorted()` ဖြင့် ထုတ်သည်ကို သတိထားပါ။ Python ၏ `set` သည် element များကို
**hash-randomised order** ဖြင့် iterate လုပ်သဖြင့် `sorted()` မလုပ်လျှင် run တစ်ခုနှင့်
တစ်ခု ပြသအစီအစဉ် ကွဲနိုင်သည်။ determinism အတွက် ဤနေရာတွင် `sorted()` မဖြစ်မနေ လိုသည်။

---

## 8. `degree` နှင့် `out_edges`

`degree(node_id)` က outgoing နှင့် incoming အရေအတွက် ပေါင်းကို ပြန်သည်။

```python
g = build_sample_graph()
for nid in sorted(g.nodes):
    print("%-3s out=%d in=%d degree=%d"
          % (nid, len(g.out_adj[nid]), len(g.in_adj[nid]), g.degree(nid)))
```

Output —

```text
c1  out=1 in=2 degree=3
p1  out=3 in=0 degree=3
p2  out=1 in=1 degree=2
t1  out=0 in=2 degree=2
```

`degree` က `len(self.out_adj.get(node_id, [])) + len(self.in_adj.get(node_id, []))` ဖြစ်သည်။
`p1` သည် outgoing ၃ ခု (KNOWS၊ WORKS_AT၊ USES)၊ incoming ၀ ခု — စုစုပေါင်း ၃။ `c1` သည်
outgoing ၁ ခု၊ incoming ၂ ခု — စုစုပေါင်း ၃။ Degree တူပေမဲ့ ဖွဲ့စည်းပုံ မတူပါ။
GraphRAG တွင် degree မြင့်သော node များသည် super-node ဖြစ်တတ်ပြီး traversal
latency ကို မြင့်စေသည် — ဤကွာခြားချက်ကို သိရန် in/out ကို သီးခြား ကြည့်ရသည်။

---

## 9. ရလဒ်ကို ဇယားဖြင့် ပြန်ကြည့်ခြင်း

Graph တစ်ခုလုံး၏ adjacency ကို ဇယားဖြင့် ပြသည် (အထက်ပါ run မှ တိုက်ရိုက် ကူးချသည်)။

| Node | Label | Outgoing | Incoming | degree |
| --- | --- | --- | --- | --- |
| `p1` | `Person` | ၃ — KNOWS→p2၊ WORKS_AT→c1၊ USES→t1 | ၀ | ၃ |
| `p2` | `Person` | ၁ — WORKS_AT→c1 | ၁ — KNOWS မှ p1 | ၂ |
| `c1` | `Company` | ၁ — USES→t1 | ၂ — WORKS_AT မှ p1၊ p2 | ၃ |
| `t1` | `Technology` | ၀ | ၂ — USES မှ c1၊ p1 | ၂ |

Relationship ၅ ခု အားလုံး ဤဇယားတွင် ပေါ်သည် — `KNOWS`၊ `WORKS_AT` ၂ ခု၊ `USES` ၂ ခု။
`t1` သည် outgoing မရှိသဖြင့် traversal သည် `t1` တွင် ဆုံးသည်။

---

## 10. Code တစ်ခုလုံး — Run လုပ်နိုင်သော Version

```python
from dataclasses import dataclass, field
from typing import Dict, List, Tuple


@dataclass
class Node:
    id: str
    labels: Tuple[str, ...]
    properties: Dict[str, object] = field(default_factory=dict)


@dataclass
class Relationship:
    type: str
    start: str
    end: str
    properties: Dict[str, object] = field(default_factory=dict)


class PropertyGraph:
    def __init__(self):
        self.nodes: Dict[str, Node] = {}
        self.relationships: List[Relationship] = []
        self.out_adj: Dict[str, List[Tuple[str, str]]] = {}
        self.in_adj: Dict[str, List[Tuple[str, str]]] = {}

    def add_node(self, node_id, labels, **props):
        node = Node(node_id, tuple(labels), dict(props))
        self.nodes[node_id] = node
        self.out_adj.setdefault(node_id, [])
        self.in_adj.setdefault(node_id, [])
        return node

    def add_relationship(self, rel_type, start, end, **props):
        if start not in self.nodes or end not in self.nodes:
            raise ValueError("relationship endpoint မရှိသော node: " + start + " / " + end)
        rel = Relationship(rel_type, start, end, dict(props))
        self.relationships.append(rel)
        self.out_adj[start].append((rel_type, end))
        self.in_adj[end].append((rel_type, start))
        return rel

    def out_edges(self, node_id):
        return list(self.out_adj.get(node_id, []))

    def degree(self, node_id):
        return len(self.out_adj.get(node_id, [])) + len(self.in_adj.get(node_id, []))


def build_sample_graph():
    g = PropertyGraph()
    g.add_node("p1", ("Person",), name="Aung Aung", age=34)
    g.add_node("p2", ("Person",), name="Su Su", age=29)
    g.add_node("c1", ("Company",), name="GraphRAG Labs")
    g.add_node("t1", ("Technology",), name="Neo4j")
    g.add_relationship("KNOWS", "p1", "p2", since=2019)
    g.add_relationship("WORKS_AT", "p1", "c1", role="Data Engineer")
    g.add_relationship("WORKS_AT", "p2", "c1", role="ML Engineer")
    g.add_relationship("USES", "c1", "t1", since=2021)
    g.add_relationship("USES", "p1", "t1", since=2024)
    return g


g = build_sample_graph()
print("nodes      :", len(g.nodes), sorted(g.nodes))
print("rels       :", len(g.relationships))
print("labels     :", sorted({lb for n in g.nodes.values() for lb in n.labels}))
print("p1 props   :", g.nodes["p1"].properties)
print("p1 degree  :", g.degree("p1"), "| c1 degree:", g.degree("c1"))
```

Output —

```text
nodes      : 4 ['c1', 'p1', 'p2', 't1']
rels       : 5
labels     : ['Company', 'Person', 'Technology']
p1 props   : {'name': 'Aung Aung', 'age': 34}
p1 degree  : 3 | c1 degree: 3
```

---

## 11. ကိုယ်တိုင်လေ့ကျင့်ကြည့်ပါ

**မေးခွန်း** — အောက်ပါ code က ဘယ်အရာကို print လုပ်မလဲ။

```python
from dataclasses import dataclass, field
from typing import Dict, Tuple


@dataclass
class Node:
    id: str
    labels: Tuple[str, ...]
    properties: Dict[str, object] = field(default_factory=dict)


n1 = Node("a", ("Person",))
n2 = Node("a", ("Person",))
n2.properties["age"] = 30
print(n1.properties, n2.properties, n1 == n2)
```

1. `{} {'age': 30} True`
2. `{} {'age': 30} False`
3. `{'age': 30} {'age': 30} True`
4. `{} {} False`

<details>
<summary>အဖြေ ကြည့်ရန်</summary>

**အဖြေ — 2. `{} {'age': 30} False`**

အကြောင်းရင်း — `field(default_factory=dict)` က instance တိုင်းအတွက် dict **သီးခြား**
ဖန်တီးသည်။ ထို့ကြောင့် `n2.properties` ကို ပြင်လိုက်သော်လည်း `n1.properties` သည်
`{}` တွင်ပင် ရှိသည်။ ပြီးနောက် `n1 == n2` သည် `properties` မတူ (`{}` vs `{'age': 30}`)
သဖြင့် `False` ဖြစ်သည်။ ဤ code ကို run ၍ အတည်ပြုပြီးဖြစ်သည်။

</details>

---

**အဓိက မှတ်ထားရန်** — Property Graph ၏ အနှစ်သာရမှာ **adjacency** ဖြစ်သည်။ Node များကို
dict ဖြင့် သိမ်းပြီး relationship များကို outgoing/incoming directory နှစ်ခုအဖြစ် ထားခြင်းသည်
Neo4j ၏ index-free adjacency ကို ပုံစံတူ အခြေခံသည်။ `@dataclass` က data holder ကို အတိုချုံ့
ရေးစေပြီး `field(default_factory=...)` က instance တိုင်း ကိုယ်ပိုင် `properties` ရှိစေသည်။
Endpoint validation ကို mutation မတိုင်မီ လုပ်ခြင်းဖြင့် graph ၏ integrity ကို ထိန်းသည်။
နောက် walkthrough (Exercise 2) တွင် ဤ graph ကို Cypher `MERGE` statement အဖြစ်
မည်သို့ ပြောင်းမည်ကို လေ့လာမည်။
