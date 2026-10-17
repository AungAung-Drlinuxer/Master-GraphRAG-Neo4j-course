# Walkthrough 02 — k-hop Subgraph Retrieval (Exercise 2)

> ဤဖိုင်သည် Module 07 ၏ `solution.md` ထဲက Exercise 2 ကို **Python အခြေခံမှ စ၍**
> အပိုင်းလိုက် ရှင်းပြသည့် walkthrough ဖြစ်သည်။ Format သည် Module 01 ၏
> `walkthroughs/01_regex_ner.md` နှင့် `walkthroughs/03_gazetteer_lookup.md` နှင့်
> တူညီသည်။

---

## 0. ဤ Exercise က ဘာကို ဖြေရှင်းပေးသလဲ။

Exercise 1 က anchor node များကို ရှာပေးသည် (`["co:neo4j", "prod:aura", "tech:vectorindex"]`)။
သို့သော် anchor များတည်းကို prompt ထဲ ထည့်လျှင် မလုံလောက်ပါ — multi-hop question
ဖြေရန် anchor များကို ဆက်စပ်သည့် triple များလည် လိုသည်။ ဤအလုပ်ကို **subgraph
retrieval** ဟု ခေါ်သည်။

```text
anchor: co:neo4j
   hop 0        co:neo4j                       (1 node)
   hop 1        + org:neo4jeng, prod:aura,
                  tech:cypher, tech:graphrag   (5 nodes)
   hop 2        + tech:vectorindex             (6 nodes, saturated)
   hop 3        ဘာမှ မတိုး (expansion ရပ်သည်)
```

Hop အရေအတွက်ကို **hop budget** ဟု ခေါ်သည်။ Hop တစ်ခု တိုးတိုင်း ပါဝင်သည့် node
အရေအတွက်သည် တိုးနိုင်သည်၊ ထို့ကြောင့် prompt context အရွယ်အစား တိုးသည်။ Graph
degree distribution သည် heavy-tail ဖြစ်တတ်သဖြင့် hub node တစ်ခုမှ edge ထောင်ချီ
ပြန်လာနိုင်သည် — ထို့ကြောင့် **hop budget ကို တိတိကျကျ ထိန်းခြင်း** သည် ဤ exercise
၏ အဓိက ရည်မှန်းချက် ဖြစ်သည်။

ဤ code မှာ လေ့လာရမည့် Python concepts များမှာ —

- Tuple of tuples ဖြင့် edge list ကို ကိုယ်စားပြုခြင်း
- `dict` + `set` ဖြင့် **adjacency list** တည်ဆောက်ခြင်း
- `dict.setdefault()` နှင့် set ပေါ်ရှိ `.add()`
- Tuple unpacking in `for` loop (`for _src, _rel, _dst, _chunk in EDGES`)
- `_` ဖြင့် အသုံးမလိုသည့် variable ကို ညွှန်းခြင်း
- `collections.deque` နှင့် `.popleft()` (BFS)
- `while` loop နှင့် level-by-level processing
- `in` operator (set membership)
- `enumerate()` နှင့် `range()`
- `set` ၏ သတိထားရမည့် order သဘောတရား

---

## 1. `EDGES` — Edge List

```python
# (src, rel, dst, provenance chunk id of the passage it was extracted from)
EDGES = (
    ("co:neo4j", "DEVELOPS", "prod:aura", "c1"),
    ("co:neo4j", "CREATES", "tech:cypher", "c2"),
    ("co:neo4j", "EMPLOYS", "org:neo4jeng", "c2"),
    ("prod:aura", "USES", "tech:vectorindex", "c1"),
    ("tech:cypher", "MAINTAINED_BY", "org:neo4jeng", "c2"),
    ("tech:graphrag", "USES", "tech:cypher", "c3"),
    ("co:neo4j", "PUBLISHES", "tech:graphrag", "c3"),
    ("tech:graphrag", "RUNS_ON", "prod:aura", "c3"),
    ("person:eifrem", "AFFILIATED_WITH", "org:cnrs", "c4"),
    ("person:eifrem", "PROPOSED", "tech:louvain", "c4"),
    ("org:cnrs", "PUBLISHES", "tech:louvain", "c4"),
    ("tech:louvain", "DOCUMENTED_IN", "paper:louvain", "c4"),
)
```

`EDGES` သည် **tuple of tuples** ဖြစ်သည်။ Element တိုင်းသည် 4-tuple ဖြစ်ပြီး
`(source, relationship type, destination, provenance chunk)` ဖြစ်သည်။ ဤကဲ့သို့
tuple ထဲတွင် element အရေအတွက် အတိအကျသတ်မှတ်ထားခြင်းကို **fixed-width record**
ဟု ခေါ်သည်။ Tuple သည် **immutable** ဖြစ်သဖြင့် `EDGES[0][1] = "X"` လို့ ပြင်လို့
မရပါ — fixture ကို မတော်တဆ ပြင်မိခြင်းမှ ကာကွယ်သည်။

Edge အညွှန်း (index) သည် အရေးကြီးသည် — Exercise 4 တွင် `graph:0` လို့ ရေးသည့်အခါ
`EDGES[0]` ကို ဆိုလိုသည်။ Edge တစ်ခုစီကို **index** ဖြင့် ကိုယ်စားပြုခြင်းက
retrieval result ကို id တစ်ခုတည်းဖြင့် ခြေရာခံနိုင်စေသည်။

---

## 2. `ADJ` — Adjacency List တည်ဆောက်ခြင်း

```python
ADJ = {}
for _src, _rel, _dst, _chunk in EDGES:
    ADJ.setdefault(_src, set()).add(_dst)
    ADJ.setdefault(_dst, set()).add(_src)
ADJ = {node: set(sorted(nb)) for node, nb in ADJ.items()}
```

### 2.1 `for _src, _rel, _dst, _chunk in EDGES` — Tuple unpacking

Loop တစ်ခုစီတွင် 4-tuple တစ်ခု ရသည်။ `_src, _rel, _dst, _chunk = ("co:neo4j", "DEVELOPS",
"prod:aura", "c1")` လို element ၄ ခုကို variable ၄ ခုအဖြစ် ခွဲယူသည်။ `_` ဖြင့်
စသည့် အမည်များသည် "ဤ variable ကို မသုံးပါ" ဟု ဖတ်သူအား ပြသည့် convention ဖြစ်သည်။

### 2.2 `setdefault()` — key မရှိလျှင် default ထည့်ပြီး ရှိလျှင် ရှိသည့်အတိုင်း ပြန်ပေးခြင်း

`ADJ.setdefault(_src, set())` သည် — `_src` key ရှိပြီးသားဖြစ်လျှင် ထို value ကို
ပြန်ပေးသည်; မရှိသေးလျှင် `set()` ကို ထည့်ပြီး ထို set အသစ်ကို ပြန်ပေးသည်။ ထို
set ပေါ်တွင် `.add(_dst)` ခေါ်သဖြင့် destination ကို ထည့်သည်။

```python
adj = {}
adj.setdefault("a", set()).add("b")
adj.setdefault("b", set()).add("a")
adj.setdefault("a", set()).add("c")
print(adj["a"] == {"b", "c"}, sorted(adj["a"]))
print(adj["b"] == {"a"}, sorted(adj["b"]))
```

Output —

```text
True ['b', 'c']
True ['a']
```

`adj["a"]` သည် `{"b", "c"}` နှင့် **တူညီသည်** (set ဖြစ်သဖြင့် အစီအစဉ် အရေးမကြီး)။
ဒုတိယ `setdefault("a", ...)` က **ရှိပြီးသား** set ကို ပြန်ပေးသဖြင့် `b` မပျောက်ပါ။

### 2.3 Undirected graph ဖြစ်စေရန် နှစ်ဖက်လုံး ထည့်ခြင်း

`ADJ.setdefault(_dst, set()).add(_src)` လိုင်းသည် **မဖြစ်မနေ လိုသည်**။ Cypher ၏
`MATCH (a)-[r]-(b)` pattern သည် direction မစစ်ပါ — k-hop traversal ကိုလည်း
undirected အဖြစ် လုပ်လိုသည်။ ထို့ကြောင့် edge တိုင်းကို နှစ်ဖက်လုံးမှ ထည့်သည်။

### 2.4 `{node: set(sorted(nb)) for node, nb in ADJ.items()}` — Dict comprehension

`ADJ.items()` သည် `(key, value)` tuple များကို ပေးသည်။ Dict comprehension သည်
key တိုင်းအတွက် value အသစ် တည်ဆောက်ပြီး dict အသစ် တစ်ခု ပြန်သည်။ ဤနေရာတွင်
value ကို `set(sorted(nb))` ဖြင့် ပြန်တည်ဆောက်သည် — ရည်ရွယ်ချက်မှာ adjacency
set များကို **တူညီသည့် iteration order** ဖြင့် ဖန်တီးရန် ဖြစ်သည်။

ဤအချက်ကို ရှင်းရှင်းလင်းလင်း သိထားရန် လိုသည် — Python ၏ `set` သည် **ပြသအစီအစဉ်
ကို အာမမခံပါ**။ ထို့ကြောင့် set ကို for loop ဖြင့် လှမ်းသည့်အခါ `sorted()` ဖြင့်
အမြဲ စီရသည်။

```python
ADJ = {
    "co:neo4j": set(["org:neo4jeng", "prod:aura", "tech:cypher", "tech:graphrag"]),
    "org:cnrs": set(["person:eifrem", "tech:louvain"]),
    "org:neo4jeng": set(["co:neo4j", "tech:cypher"]),
    "paper:louvain": set(["tech:louvain"]),
    "person:eifrem": set(["org:cnrs", "tech:louvain"]),
    "prod:aura": set(["co:neo4j", "tech:graphrag", "tech:vectorindex"]),
    "tech:cypher": set(["co:neo4j", "org:neo4jeng", "tech:graphrag"]),
    "tech:graphrag": set(["co:neo4j", "prod:aura", "tech:cypher"]),
    "tech:louvain": set(["org:cnrs", "paper:louvain", "person:eifrem"]),
    "tech:vectorindex": set(["prod:aura"]),
}
for node in sorted(ADJ):
    print("%-18s -> %s" % (node, sorted(ADJ[node])))
```

Output —

```text
co:neo4j           -> ['org:neo4jeng', 'prod:aura', 'tech:cypher', 'tech:graphrag']
org:cnrs           -> ['person:eifrem', 'tech:louvain']
org:neo4jeng       -> ['co:neo4j', 'tech:cypher']
paper:louvain      -> ['tech:louvain']
person:eifrem      -> ['org:cnrs', 'tech:louvain']
prod:aura          -> ['co:neo4j', 'tech:graphrag', 'tech:vectorindex']
tech:cypher        -> ['co:neo4j', 'org:neo4jeng', 'tech:graphrag']
tech:graphrag      -> ['co:neo4j', 'prod:aura', 'tech:cypher']
tech:louvain       -> ['org:cnrs', 'paper:louvain', 'person:eifrem']
tech:vectorindex   -> ['prod:aura']
```

`tech:vectorindex` သည် degree 1 သာရှိပြီး `co:neo4j` သည် degree 4 ရှိသည်ကို
တွေ့နိုင်သည်။ graph သေးသော်လည်း degree မညီမျှခြင်း (heavy tail) ၏ သဘောကို
ဤနေရာတွင် မြင်နိုင်သည်။

---

## 3. `deque` — Frontier အတွက် Data Structure

```python
from collections import deque
```

`deque` သည် "double-ended queue" ဖြစ်သည် — ရှေ့နှင့် နောက် နှစ်ဖက်လုံးမှ `O(1)`
ဖြင့် ထည့်/ထုတ် လုပ်နိုင်သည်။ သာမန် `list` တွင်လည်း `pop(0)` ဖြင့် ရှေ့မှ
ထုတ်နိုင်သော်လည်း `list.pop(0)` သည် element အားလုံးကို နေရာရွှေ့ရသဖြင့် `O(n)`
ဖြစ်သည်။ BFS တွင် node သောင်းချီ လှမ်းရနိုင်သဖြင့် `deque` ကို သုံးသည်။

```python
from collections import deque

frontier = deque(["co:neo4j", "prod:aura"])
print(list(frontier))
print(frontier.popleft())
print(list(frontier))
```

Output —

```text
['co:neo4j', 'prod:aura']
co:neo4j
['prod:aura']
```

`list(frontier)` သည် deque ကို list အဖြစ် ပြောင်းပြီး ပြသသည်။ `.popleft()` သည်
**ရှေ့ဆုံး** element ကို ဖယ်ထုတ်ပြီး ပြန်ပေးသည် — ဤအချက်သည် BFS (breadth-first)
ဖြစ်စေသည့် အဓိကအချက် ဖြစ်သည်။ `.pop()` (right) ကို သုံးလျှင် DFS ဖြစ်သွားသည်။

---

## 4. `k_hop_subgraph()` — Function တစ်ခုလုံး

```python
from collections import deque


def k_hop_subgraph(anchor_ids, k, adj=None):
    """Breadth-first expansion up to k hops. Returns (node_ids, edge_indexes)."""
    adj = ADJ if adj is None else adj
    reached = set(anchor_ids)
    frontier = deque(sorted(anchor_ids))
    for _ in range(k):
        nxt = deque()
        while frontier:
            for nb in sorted(adj.get(frontier.popleft(), ())):
                if nb not in reached:
                    reached.add(nb)
                    nxt.append(nb)
        frontier = nxt
        if not frontier:
            break
    idx = [i for i, e in enumerate(EDGES) if e[0] in reached and e[2] in reached]
    return sorted(reached), idx
```

### 4.1 Signature — `anchor_ids, k, adj=None`

- `anchor_ids` — node id များ၏ list (Exercise 1 ၏ ရလဒ်)။
- `k` — hop budget။
- `adj` — optional။ `None` ဖြစ်လျှင် module-level `ADJ` ကို သုံးသည်။

`adj` ကို ထည့်ထားခြင်းသည် **dependency injection** ဖြစ်သည် — test တွင် graph အသေးစားတစ်ခု
ထည့်ပြီး function ကို တိုက်ရိုက် စစ်နိုင်သည်။ `adj = ADJ if adj is None
else adj` ဖြစ်သည်ကို သတိထားပါ။ `if not adj` လို့ ရေးလျှင် caller က အလွတ်
graph `{}` ကို ရည်ရွယ်ချက်ရှိရှိ ပေးလာလျှင် `ADJ` ကို ပြန်သုံးမိမည်။ ထို့ကြောင့်
**`is None` ၏ identity check** ကို သုံးရသည်။

### 4.2 `set` နှင့် `deque` ကို ပြင်ဆင်ခြင်း

```python
reached = set(anchor_ids)
frontier = deque(sorted(anchor_ids))
```

- `reached` — ရောက်ရှိပြီးသား node များ။ **set** ဖြစ်သဖြင့် membership စစ်ခြင်း
  (`nb not in reached`) သည် `O(1)` ဖြစ်သည်။
- `frontier` — လက်ရှိ hop ၏ အလုပ်လုပ်စရာ node များ။ **deque** ဖြစ်သဖြင့်
  ဘယ်ဘက်မှ ထုတ်၊ ညာဘက်မှ ထည့်နိုင်သည်။

`anchor_ids` ကို `set()` နှင့် `deque(sorted(...))` နှစ်မျိုးလုံးတွင် သုံးသည်။
`set(anchor_ids)` ဖြင့် anchor ထပ်နေလျှင် တစ်ခုတည်း ဖြစ်သွားသည်။

### 4.3 Outer loop — `for _ in range(k)`

`range(k)` သည် `0, 1, ..., k-1` ကို ပေးသည်။ `_` ဖြင့် လက်ခံသဖြင့် "hop အရေအတွက်
ကိုသာ ရေတွက်သည်၊ loop variable ကို မသုံးပါ" ဆိုသည့် အဓိပ္ပာယ်ကို ပြသည်။ Hop
တစ်ခုစီသည် outer iteration တစ်ခု ဖြစ်သည်။

### 4.4 Inner loop — level တစ်ခုလုံး ပြီးဆုံးအောင် စားသုံးခြင်း

```python
while frontier:
    for nb in sorted(adj.get(frontier.popleft(), ())):
```

ဤအပိုင်းသည် ဤ function ၏ **အဓိကအချက်** ဖြစ်သည်။ `while frontier:` သည် frontier
ကို **အလွတ်ဖြစ်သည်အထိ** လုပ်သည် — ထို့ကြောင့် hop တစ်ခု၏ node များ အားလုံး
ကုန်ဆုံးသည်အထိ ရပ်မည် မဟုတ်ပါ။ `nxt` ထဲ ရောက်သမျှ node များသည် **နောက် hop**
အတွက်သာ ဖြစ်သည် — လက်ရှိ hop တွင် သူတို့ကို မလှမ်းပါ။ ဤအချက်သည် hop တစ်ခုထက်
မကျော်စေရန် အာမခံသည်။

`adj.get(frontier.popleft(), ())` — `dict.get(key, default)` သည် key မရှိလျှင်
`()` (empty tuple) ကို ပြန်ပေးသည်။ **isolated node** တစ်ခု ပါလာလျှင် `KeyError`
မဖြစ်စေရန် ကာကွယ်ခြင်း ဖြစ်သည်။

`frontier.popleft()` ကို `for` loop ၏ expression ထဲတွင် တိုက်ရိုက် ခေါ်ထားသဖြင့်
loop iteration အတိုင်း ရှေ့ node တစ်ခုစီ ထုတ်သည်။

### 4.5 `nb not in reached`

```python
if nb not in reached:
    reached.add(nb)
    nxt.append(nb)
```

- `in` သည် set membership စစ်သည်။
- Neighbor ကို **reached ထဲ ရှိပြီးသား** ဖြစ်လျှင် ကျော်လိုက်သည် — cycle ရှိသည့်
  graph တွင် infinite loop ဖြစ်ခြင်းကို ကာကွယ်သည်၊ duplicate ကိုလည် ဖယ်သည်။
- `reached.add()` နှင့် `nxt.append()` ကို **တွဲလုပ်သည်** — node တစ်ခုကို နှစ်ကြိမ်
  `nxt` ထဲ မထည့်စေရန် ဖြစ်သည်။

### 4.6 `frontier = nxt` နှင့် `break`

```python
frontier = nxt
if not frontier:
    break
```

`frontier` ကို `nxt` ဖြင့် **အစားထိုး** လိုက်သည်ကို သတိထားပါ — delegate မဟုတ်၊
reference assignment ဖြစ်သည်။ နောက် iteration သည် `nxt` ကို စားသုံးမည်။
`frontier` အလွတ်ဖြစ်လျှင် နောက် hop တွင်လည် ဘာမှ ရှာမည် မဟုတ်သဖြင့်
`break` ဖြင့် ရပ်သည် — ဤအချက်သည် `k` ထက် ပိုမလုပ်စေရန် လိုအပ်သည်။

---

## 5. Frontier Trace — တကယ့် BFS အလုပ်လုပ်ပုံ

```python
from collections import deque

ADJ = {
    "co:neo4j": set(["org:neo4jeng", "prod:aura", "tech:cypher", "tech:graphrag"]),
    "org:cnrs": set(["person:eifrem", "tech:louvain"]),
    "org:neo4jeng": set(["co:neo4j", "tech:cypher"]),
    "paper:louvain": set(["tech:louvain"]),
    "person:eifrem": set(["org:cnrs", "tech:louvain"]),
    "prod:aura": set(["co:neo4j", "tech:graphrag", "tech:vectorindex"]),
    "tech:cypher": set(["co:neo4j", "org:neo4jeng", "tech:graphrag"]),
    "tech:graphrag": set(["co:neo4j", "prod:aura", "tech:cypher"]),
    "tech:louvain": set(["org:cnrs", "paper:louvain", "person:eifrem"]),
    "tech:vectorindex": set(["prod:aura"]),
}
frontier = deque(sorted(["co:neo4j"]))
reached = set(["co:neo4j"])
print("hop 0  frontier=%s" % list(frontier))
hop = 0
while frontier:
    hop += 1
    nxt = deque()
    popped = []
    while frontier:
        node = frontier.popleft()
        popped.append(node)
        for nb in sorted(ADJ.get(node, ())):
            if nb not in reached:
                reached.add(nb)
                nxt.append(nb)
    print("hop %d  popped=%s" % (hop, popped))
    print("       new frontier=%s" % list(nxt))
    print("       reached=%s" % sorted(reached))
    frontier = nxt
    if not frontier:
        print("       frontier empty -> break at hop %d" % hop)
        break
```

Output —

```text
hop 0  frontier=['co:neo4j']
hop 1  popped=['co:neo4j']
       new frontier=['org:neo4jeng', 'prod:aura', 'tech:cypher', 'tech:graphrag']
       reached=['co:neo4j', 'org:neo4jeng', 'prod:aura', 'tech:cypher', 'tech:graphrag']
hop 2  popped=['org:neo4jeng', 'prod:aura', 'tech:cypher', 'tech:graphrag']
       new frontier=['tech:vectorindex']
       reached=['co:neo4j', 'org:neo4jeng', 'prod:aura', 'tech:cypher', 'tech:graphrag', 'tech:vectorindex']
hop 3  popped=['tech:vectorindex']
       new frontier=[]
       reached=['co:neo4j', 'org:neo4jeng', 'prod:aura', 'tech:cypher', 'tech:graphrag', 'tech:vectorindex']
       frontier empty -> break at hop 3
```

ဤ trace ကို ဇယားအဖြစ် ဖတ်လျှင် BFS ၏ hop-by-hop သဘောကို ရှင်းရှင်းလင်းလင်း
မြင်နိုင်သည်။

| Hop | Frontier (လုပ်ရမည့် node) | Pop လုပ်ပြီး ရရှိသည့် node အသစ် | Reached စုစုပေါင်း |
| --- | --- | --- | --- |
| 0 | `co:neo4j` | — (anchor) | 1 |
| 1 | `co:neo4j` | `org:neo4jeng`၊ `prod:aura`၊ `tech:cypher`၊ `tech:graphrag` | 5 |
| 2 | `org:neo4jeng`၊ `prod:aura`၊ `tech:cypher`၊ `tech:graphrag` | `tech:vectorindex` | 6 |
| 3 | `tech:vectorindex` | ဘာမှ မရ | 6 (saturated) |

အဓိက အချက် နှစ်ခု —

1. **Hop 2 ၏ frontier သည် hop 1 တွင် ရရှိသည့် node များ ဖြစ်သည်** — hop 1 တွင်
   ရရှိသည့် node များကို hop 1 အတွင်း မလှမ်းပါ။ ဤအချက်သည် hop budget ကို
   တိတိကျကျ ထိန်းသည်။
2. **Hop 3 တွင် node အသစ် လုံးဝ မရပါ** — component ကုန်ဆုံးသွားသဖြင့်
   `frontier` အလွတ်ဖြစ်ပြီး `break` ဖြစ်သည်။

---

## 6. Edge Collection — `enumerate()` နှင့် နှစ်ဖက်စစ်ခြင်း

```python
idx = [i for i, e in enumerate(EDGES) if e[0] in reached and e[2] in reached]
```

`enumerate(EDGES)` သည် `(index, value)` tuple များကို ပေးသည် — `(0, ("co:neo4j",
"DEVELOPS", "prod:aura", "c1"))`၊ `(1, ...)` စသည်။ ဤနေရာတွင် index ကို `i`၊
tuple ကို `e` အဖြစ် ခွဲယူသည်။ List comprehension ၏ condition သည် —
`e[0] in reached and e[2] in reached` — **source ရော destination ရော** ရောက်ရှိပြီး
ဖြစ်ရမည်။

`reached = {"co:neo4j", "prod:aura"}` လို့ ထားရင် ဘာဖြစ်လဲ။

```python
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
reached = {"co:neo4j", "prod:aura"}
idx = [i for i, e in enumerate(EDGES) if e[0] in reached and e[2] in reached]
print(idx)
for i in idx:
    print(i, EDGES[i])
```

Output —

```text
[0]
0 ('co:neo4j', 'DEVELOPS', 'prod:aura', 'c1')
```

Edge `7` (`tech:graphrag -[RUNS_ON]-> prod:aura`) သည် `prod:aura` ပါသော်လည်း
`tech:graphrag` မပါသဖြင့် **မပါဝင်ပါ**။ ဤအချက်သည် **dangling triple** ကို
ကာကွယ်သည် — source သို့မဟုတ် destination မပါသော triple ကို prompt ထဲ ထည့်လျှင်
LLM သည် မည်သည့် entity အကြောင်း ပြောနေသည်ကို မသိနိုင်ပါ။

`reached` အပြည့်ဖြစ်လျှင် ရလဒ်သည် ဤကဲ့သို့ ဖြစ်သည်။

```python
EDGES = (
    ("co:neo4j", "DEVELOPS", "prod:aura", "c1"),
    ("co:neo4j", "CREATES", "tech:cypher", "c2"),
    ("co:neo4j", "EMPLOYS", "org:neo4jeng", "c2"),
    ("prod:aura", "USES", "tech:vectorindex", "c1"),
    ("tech:cypher", "MAINTAINED_BY", "org:neo4jeng", "c2"),
    ("tech:graphrag", "USES", "tech:cypher", "c3"),
    ("co:neo4j", "PUBLISHES", "tech:graphrag", "c3"),
    ("tech:graphrag", "RUNS_ON", "prod:aura", "c3"),
    ("person:eifrem", "AFFILIATED_WITH", "org:cnrs", "c4"),
    ("person:eifrem", "PROPOSED", "tech:louvain", "c4"),
    ("org:cnrs", "PUBLISHES", "tech:louvain", "c4"),
    ("tech:louvain", "DOCUMENTED_IN", "paper:louvain", "c4"),
)
reached = {"co:neo4j", "org:neo4jeng", "prod:aura", "tech:cypher", "tech:graphrag"}
idx = [i for i, e in enumerate(EDGES) if e[0] in reached and e[2] in reached]
print(len(EDGES), "edges,", len(idx), "selected")
print(idx)
```

Output —

```text
12 edges, 7 selected
[0, 1, 2, 4, 5, 6, 7]
```

Edge စုစုပေါင်း 12 ခုအနက် 7 ခု ရွေးခံရသည်။ ဤ `idx` list သည် `return sorted(reached),
idx` ၏ ဒုတိယ element ဖြစ်သည်။

---

## 7. ရလဒ်ကို စစ်ဆေးခြင်း — Saturation နှင့် Disjoint Component

```python
from collections import deque

EDGES = (
    ("co:neo4j", "DEVELOPS", "prod:aura", "c1"),
    ("co:neo4j", "CREATES", "tech:cypher", "c2"),
    ("co:neo4j", "EMPLOYS", "org:neo4jeng", "c2"),
    ("prod:aura", "USES", "tech:vectorindex", "c1"),
    ("tech:cypher", "MAINTAINED_BY", "org:neo4jeng", "c2"),
    ("tech:graphrag", "USES", "tech:cypher", "c3"),
    ("co:neo4j", "PUBLISHES", "tech:graphrag", "c3"),
    ("tech:graphrag", "RUNS_ON", "prod:aura", "c3"),
    ("person:eifrem", "AFFILIATED_WITH", "org:cnrs", "c4"),
    ("person:eifrem", "PROPOSED", "tech:louvain", "c4"),
    ("org:cnrs", "PUBLISHES", "tech:louvain", "c4"),
    ("tech:louvain", "DOCUMENTED_IN", "paper:louvain", "c4"),
)
ADJ = {}
for _src, _rel, _dst, _chunk in EDGES:
    ADJ.setdefault(_src, set()).add(_dst)
    ADJ.setdefault(_dst, set()).add(_src)
ADJ = {node: set(sorted(nb)) for node, nb in ADJ.items()}


def k_hop_subgraph(anchor_ids, k, adj=None):
    adj = ADJ if adj is None else adj
    reached = set(anchor_ids)
    frontier = deque(sorted(anchor_ids))
    for _ in range(k):
        nxt = deque()
        while frontier:
            for nb in sorted(adj.get(frontier.popleft(), ())):
                if nb not in reached:
                    reached.add(nb)
                    nxt.append(nb)
        frontier = nxt
        if not frontier:
            break
    idx = [i for i, e in enumerate(EDGES) if e[0] in reached and e[2] in reached]
    return sorted(reached), idx


for k in (0, 1, 2, 3):
    nodes, edges = k_hop_subgraph(["co:neo4j"], k)
    print("k=%d: %d nodes, %d edges  nodes=%s" % (k, len(nodes), len(edges), nodes))

n1, e1 = k_hop_subgraph(["co:neo4j"], 1)
n2, e2 = k_hop_subgraph(["co:neo4j"], 2)
n3, e3 = k_hop_subgraph(["co:neo4j"], 3)
print("n2 == n3:", n2 == n3)
print("e2 == e3:", e2 == e3)
print("set(n2) - set(n1):", sorted(set(n2) - set(n1)))
print("person:eifrem in n3:", "person:eifrem" in n3)
print("tech:louvain in n3:", "tech:louvain" in n3)
```

Output —

```text
k=0: 1 nodes, 0 edges  nodes=['co:neo4j']
k=1: 5 nodes, 7 edges  nodes=['co:neo4j', 'org:neo4jeng', 'prod:aura', 'tech:cypher', 'tech:graphrag']
k=2: 6 nodes, 8 edges  nodes=['co:neo4j', 'org:neo4jeng', 'prod:aura', 'tech:cypher', 'tech:graphrag', 'tech:vectorindex']
k=3: 6 nodes, 8 edges  nodes=['co:neo4j', 'org:neo4jeng', 'prod:aura', 'tech:cypher', 'tech:graphrag', 'tech:vectorindex']
n2 == n3: True
e2 == e3: True
set(n2) - set(n1): ['tech:vectorindex']
person:eifrem in n3: False
tech:louvain in n3: False
```

| `k` | Node | Edge | မှတ်ချက် |
| --- | --- | --- | --- |
| 0 | 1 | 0 | anchor သာ — edge နှစ်ဖက်လုံး မပြည့်သဖြင့် 0 |
| 1 | 5 | 7 | ပထမ hop — hub ၏ neighbor အားလုံး |
| 2 | 6 | 8 | `tech:vectorindex` တစ်ခုသာ တိုး |
| 3 | 6 | 8 | saturation — `k=2` နှင့် လုံးဝ တူညီ |

`k=1` မှ `k=2` သို့ တိုးလျှင် node 5 → 6 (တိုး)၊ သို့သော် `k=2` မှ `k=3` သို့
တိုးလျှင် လုံးဝ မတိုးပါ။ `n2 == n3: True` ဖြစ်ခြင်းသည် ထို အချက်ကို
programmatically အတည်ပြုသည်။ Disjoint component (`person:eifrem` ဘက်) သည်
**ဘယ် `k` တွင်မှ** မပါဝင်ပါ — `False` နှစ်ခု ဖြင့် အတည်ပြုသည်။

`set(a) - set(b)` သည် **set difference** — `a` ထဲ ပါပြီး `b` ထဲ မပါသည့်
element များ။ `sorted(...)` ဖြင့် စီထားသဖြင့် အစီအစဉ် တည်ငြိမ်သည်။
`set(n2) - set(n1)` သည် `['tech:vectorindex']` — hop နှစ်ခုကြား တိုးလာသည့် node
တစ်ခုတည်း ဖြစ်သည်။

---

## 8. Neo4j ပေါ်တွင် ညီမျှသော Operation

`k_hop_subgraph()` သည် in-memory simulation ဖြစ်သည်။ Neo4j တွင် ထို operation ကို
**variable-length pattern** ဖြင့် ရေးနိုင်သည်။

```cypher
MATCH path = (a)-[r*1..2]-(b)
WHERE a.id IN $anchor_ids
UNWIND relationships(path) AS rel
RETURN DISTINCT startNode(rel).id AS src, type(rel) AS rel_type, endNode(rel).id AS dst
LIMIT $limit
```

| အပိုင်း | အဓိပ္ပာယ် |
| --- | --- |
| `(a)-[r*1..2]-(b)` | `a` မှ `b` သို့ 1 မှ 2 hop အတွင်း — direction မစစ် |
| `WHERE a.id IN $anchor_ids` | anchor list — parameter ဖြင့် ပေးသည် |
| `UNWIND relationships(path)` | path ထဲက relationship အားလုံးကို row တစ်ခုစီ ခွဲထုတ် |
| `LIMIT $limit` | ရလဒ် အရေအတွက် ကန့်သတ် |

`$limit` ကို **မဖြစ်မနေ ထည့်ရမည်**။ `*1..2` သည် fan-out မြင့်သည့် hub node
တစ်ခုတွင် edge ထောင်ချီ ပြန်နိုင်သည် — ထိုအခါ query သည် memory ကို ဖြုန်းတီးသည်။
`*1..2` ကဲ့သို့ variable-length pattern တွင် upper bound ကို အမြဲ သတ်မှတ်ရမည်။

Python simulation က hop ကို level အလိုက် စားသုံးသလို Cypher ကလည်း path length
ကို ကန့်သတ်သည် — သဘောတရား တူညီသည်။

---

## 9. Anchor များစွာ ဖြင့် လုပ်ခြင်း

Anchor နှစ်ခုကို ပေးလျှင် ဤ function သည် set နှစ်ခုလုံးမှ စတင် expand လုပ်သည်။

```python
for anchor in (["tech:louvain"], ["co:neo4j", "org:cnrs"]):
    for k in (1, 2):
        nodes, edges = k_hop_subgraph(anchor, k)
        print("anchor=%-24s k=%d -> %d nodes, %d edges" % (anchor, k, len(nodes), len(edges)))
```

Output —

```text
anchor=['tech:louvain']         k=1 -> 4 nodes, 4 edges
anchor=['tech:louvain']         k=2 -> 4 nodes, 4 edges
anchor=['co:neo4j', 'org:cnrs'] k=1 -> 8 nodes, 10 edges
anchor=['co:neo4j', 'org:cnrs'] k=2 -> 10 nodes, 12 edges
```

`anchor=['co:neo4j', 'org:cnrs']` ပေးလိုက်လျှင် component နှစ်ခုလုံး ပါလာသည် —
`k=2` တွင် node 10/10၊ edge 12/12 ဖြစ်လာသည်။ ဤအချက်က **anchor ရွေးချယ်မှုသည်
context အရွယ်အစားကို တိုက်ရိုက် ဆုံးဖြတ်သည်** ဆိုသည့် အချက်ကို ပြသည်။
Anchor တစ်ခုလျှင် 4-6 node၊ anchor နှစ်ခုလျှင် 10 node ဖြစ်လာသည်။

`['tech:louvain']` အတွက် `k=1` နှင့် `k=2` သည် တူညီသည် — ထို component သည်
အလွန် သေးငယ်သဖြင့် hop 1 တွင်ပင် saturated ဖြစ်သည်။

---

## 10. Code တစ်ခုလုံး — Run လုပ်နိုင်သော Version

```python
# end-to-end: exercise_2
from collections import deque

EDGES = (
    ("co:neo4j", "DEVELOPS", "prod:aura", "c1"),
    ("co:neo4j", "CREATES", "tech:cypher", "c2"),
    ("co:neo4j", "EMPLOYS", "org:neo4jeng", "c2"),
    ("prod:aura", "USES", "tech:vectorindex", "c1"),
    ("tech:cypher", "MAINTAINED_BY", "org:neo4jeng", "c2"),
    ("tech:graphrag", "USES", "tech:cypher", "c3"),
    ("co:neo4j", "PUBLISHES", "tech:graphrag", "c3"),
    ("tech:graphrag", "RUNS_ON", "prod:aura", "c3"),
    ("person:eifrem", "AFFILIATED_WITH", "org:cnrs", "c4"),
    ("person:eifrem", "PROPOSED", "tech:louvain", "c4"),
    ("org:cnrs", "PUBLISHES", "tech:louvain", "c4"),
    ("tech:louvain", "DOCUMENTED_IN", "paper:louvain", "c4"),
)
ADJ = {}
for _src, _rel, _dst, _chunk in EDGES:
    ADJ.setdefault(_src, set()).add(_dst)
    ADJ.setdefault(_dst, set()).add(_src)
ADJ = {node: set(sorted(nb)) for node, nb in ADJ.items()}


def k_hop_subgraph(anchor_ids, k, adj=None):
    adj = ADJ if adj is None else adj
    reached = set(anchor_ids)
    frontier = deque(sorted(anchor_ids))
    for _ in range(k):
        nxt = deque()
        while frontier:
            for nb in sorted(adj.get(frontier.popleft(), ())):
                if nb not in reached:
                    reached.add(nb)
                    nxt.append(nb)
        frontier = nxt
        if not frontier:
            break
    idx = [i for i, e in enumerate(EDGES) if e[0] in reached and e[2] in reached]
    return sorted(reached), idx


hops = {k: k_hop_subgraph(["co:neo4j"], k) for k in (1, 2, 3)}
for k, (nodes, edges) in hops.items():
    print(f"k={k}: {len(nodes)} nodes, {len(edges)} edges  nodes={nodes}")
n1, e1 = hops[1]
n2, e2 = hops[2]
n3, e3 = hops[3]

assert n1 == ["co:neo4j", "org:neo4jeng", "prod:aura", "tech:cypher", "tech:graphrag"]
assert e1 == [0, 1, 2, 4, 5, 6, 7]
assert set(n2) - set(n1) == {"tech:vectorindex"}
assert n2 == n3 and e2 == e3
assert "person:eifrem" not in n3 and "tech:louvain" not in n3
assert len(e2) == 8
print("[ok] hop budget controls context size; disjoint component stays out")
```

Output —

```text
k=1: 5 nodes, 7 edges  nodes=['co:neo4j', 'org:neo4jeng', 'prod:aura', 'tech:cypher', 'tech:graphrag']
k=2: 6 nodes, 8 edges  nodes=['co:neo4j', 'org:neo4jeng', 'prod:aura', 'tech:cypher', 'tech:graphrag', 'tech:vectorindex']
k=3: 6 nodes, 8 edges  nodes=['co:neo4j', 'org:neo4jeng', 'prod:aura', 'tech:cypher', 'tech:graphrag', 'tech:vectorindex']
[ok] hop budget controls context size; disjoint component stays out
```

`hops = {k: k_hop_subgraph(["co:neo4j"], k) for k in (1, 2, 3)}` သည် **dict
comprehension** ဖြစ်သည် — `k` ကို key အဖြစ်၊ `(nodes, edges)` tuple ကို value
အဖြစ် သိမ်းသည်။ ထို့နောက် `n1, e1 = hops[1]` ဖြင့် tuple ကို element နှစ်ခုအဖြစ်
ခွဲယူသည်။

---

## 11. ကိုယ်တိုင်လေ့ကျင့်ကြည့်ပါ

**မေးခွန်း** — `k=1` တွင် edge ရလဒ်သည် `[0, 1, 2, 4, 5, 6, 7]` ဖြစ်သည်။ ဤ list
ထဲတွင် index `3` မပါရသည့် အကြောင်းရင်းက ဘာလဲ။

```python
EDGES = (
    ("co:neo4j", "DEVELOPS", "prod:aura", "c1"),
    ("co:neo4j", "CREATES", "tech:cypher", "c2"),
    ("co:neo4j", "EMPLOYS", "org:neo4jeng", "c2"),
    ("prod:aura", "USES", "tech:vectorindex", "c1"),
)
reached = {"co:neo4j", "org:neo4jeng", "prod:aura", "tech:cypher", "tech:graphrag"}
idx = [i for i, e in enumerate(EDGES) if e[0] in reached and e[2] in reached]
print(idx)
```

1. `EDGES[3]` သည် relationship type မမှန်လို့
2. `EDGES[3]` ၏ destination (`tech:vectorindex`) သည် `reached` ထဲ မပါလို့
3. `EDGES[3]` ၏ source (`prod:aura`) သည် `reached` ထဲ မပါလို့
4. Index `3` သည် loop ၏ `range` အပြင်ဖြစ်လို့

<details>
<summary>အဖြေ ကြည့်ရန်</summary>

**အဖြေ — 2. `EDGES[3]` ၏ destination သည် `reached` ထဲ မပါလို့**

အကြောင်းရင်း — `EDGES[3]` သည် `("prod:aura", "USES", "tech:vectorindex", "c1")` ဖြစ်သည်။
Source `prod:aura` သည် `reached` ထဲ ပါသည်; destination `tech:vectorindex` သည်
`reached` ထဲ **မပါပါ** — `tech:vectorindex` ကို hop 2 မှသာ ရရှိသည်။ `k=1`
တွင် `reached` သည် `{co:neo4j, org:neo4jeng, prod:aura, tech:cypher, tech:graphrag}`
ဖြစ်သဖြင့် index 3 သည် ကျသည်။ ဤအချက်က အဆင့် 6 တွင် ရှင်းပြထားသည့်
**dangling triple ကာကွယ်ခြင်း** ၏ တိုက်ရိုက် ရလဒ် ဖြစ်သည်။

`print(idx)` ၏ အဖြေသည် `[0, 1, 2]` ဖြစ်သည် — `EDGES[3]` မပါပါ။

</details>

---

**အဓိက မှတ်ထားရန်** — Level-by-level BFS သည် hop budget ကို တိတိကျကျ ထိန်းသည် —
frontier ကို hop တစ်ခုစီ ပြီးဆုံးအောင် စားသုံးခြင်းဖြင့် hop တစ်ခုထက် မကျော်ပါ။
Edge စုဆောင်းသည့်အခါ **node နှစ်ခုလုံး ရောက်ရှိပြီးသား ဖြစ်ရမည်** — မဟုတ်ပါက
dangling triple ဖြစ်သည်။ `set` ကို iterate လုပ်သည့်အခါ အမြဲ `sorted()`
ဖြင့် စီရမည်၊ မဟုတ်ပါက run တစ်ခုနှင့်တစ်ခ် ရလဒ် အစီအစဉ် ကွဲနိုင်သည်။ Hop
budget ပို တိုးလျှင် recall တက်နိုင်သော်လည်း context token cost လည်း
မြင့်လာသည် — နှစ်ခုကို ချိန်ညှိရမည်။ Neo4j ပေါ်တွင် `*1..2` လို variable-length
pattern ကို အသုံးပြုသည့်အခါ `LIMIT` ကို **မဖြစ်မနေ** ထည့်ရမည်။
