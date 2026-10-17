# Walkthrough 06 — Index-free adjacency traversal (Exercise 6)

> ဤဖိုင်သည် Module 05 ၏ `solution.md` ထဲက Exercise 6 ကို **Python အခြေခံမှ စ၍**
> အပိုင်းလိုက် ရှင်းပြသည့် walkthrough ဖြစ်သည်။ `collections.deque`၊ `while` loop၊
> set တိုးခြင်း၊ dict ၏ level map၊ BFS၊ `math.log()`/`math.ceil()` စသည့် Python
> concept များကို ဤနေရာတွင် ရှင်းပြသည်။

---

## 0. ဤ Exercise က ဘာကို ဖြေရှင်းပေးသလဲ။

GraphRAG retrieval တွင် entity တစ်ခုမှ စပြီး multi-hop traversal လုပ်သည်။ Neo4j ကို
ဤအလုပ်အတွက် ရွေးရသည့် အဓိက အကြောင်းရင်းမှာ **index-free adjacency** ဖြစ်သည် —
relationship တစ်ခုကို ဖြတ်သည့် cost သည် graph အရွယ်အစား (N) ပေါ်တွင် မမှီခိုပါ။
ဤ Exercise က ထိုအချက်ကို simulate လုပ်ပြီး သက်သေပြသည်။

```text
traverse(g, "p1", 2)                     index-based engine (နှိုင်းယှဉ်ရန်)
   p1 --KNOWS--> p2      (hop 1)              hop တိုင်းအတွက် index lookup တစ်ခု
   p1 --WORKS_AT--> c1   (hop 1)              cost = visited × ceil(log2 N)
   p1 --USES--> t1       (hop 1)
        |  edge traverse ၅ ခု (node အသစ် ဖြစ်/မဖြစ် မခွဲ)
        v
   visited = {p1, p2, c1, t1}
```

ဤ code မှာ လေ့လာရမည့် Python concepts — `deque` နှင့် `popleft()`၊ `while queue:` ၏
truthiness၊ set ၏ `add()`/`in`၊ dict ဖြင့် level/`prev` မှတ်ခြင်း၊ `for ... in` loop ၏
tuple unpacking၊ `list(reversed(...))`၊ `math.log()` နှင့် `math.ceil()` ။

> ဤဖိုင်တွင် Section 2 က graph နှင့် `traverse()` ကို အပြည့်အစုံ သတ်မှတ်သည်။
> နောက် Section များသည် ထို definition များကို ဆက်သုံးသည် (lab.py တွင် ထို
> တူညီသော definition များ ပါသဖြင့် snippet တိုင်း သီးခြားစီ run နိုင်သည်)။

---

## 1. `collections.deque` — အရှေ့မှ ဆွဲထုတ်နိုင်သော queue

BFS (Breadth-First Search) အတွက် queue လိုသည်။ `deque` ၏ `popleft()` သည် အရှေ့ဆုံး
element ကို O(1) ဖြင့် ဆွဲထုတ်သည် (list ၏ `pop(0)` သည် O(n) ဖြစ်သည်)။

```python
from collections import deque

dq = deque([1, 2, 3])
print(list(dq), len(dq))
print(dq.popleft(), dq.popleft(), list(dq))
dq.append(9)
print(list(dq))
```

Output —

```text
[1, 2, 3] 3
1 2 [3]
[3, 9]
```

`deque([1, 2, 3])` က deque ဖန်တီးသည်။ `list(dq)` က ပြန်ဖြန့်ပြသည်။ `popleft()` က
အရှေ့ဆုံး (`1`) ကို ဆွဲထုတ်သည် — ခေါ်တိုင်း deque က တိုလာသည်။ `append(9)` က
အဆုံးတွင် ထည့်သည်။ ဤ "အရှေ့မှ ဆွဲ၊ အနောက်တွင် ထည့်" အပြုအမူသည် queue (FIFO) ဖြစ်သည် —
BFS ၏ အခြေခံ ဖြစ်သည်။

---

## 2. `traverse()` — Directed BFS

Function သည် `(visited, levels, traversals)` ဆိုသော tuple သုံးခု ပြန်သည်။ အောက်ပါ
code သည် graph နှင့် `traverse()` ကို အပြည့်အစုံ သတ်မှတ်ပြီး run သည်။

```python
from collections import deque
from dataclasses import dataclass, field
from typing import Dict, Tuple


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
        self.nodes = {}
        self.relationships = []
        self.out_adj = {}
        self.in_adj = {}

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


def traverse(graph, start_id, max_depth):
    visited = {start_id}
    levels = {start_id: 0}
    traversals = 0
    queue = deque([start_id])
    while queue:
        cur = queue.popleft()
        depth = levels[cur]
        if depth == max_depth:
            continue
        for _rtype, nxt in graph.out_edges(cur):
            traversals += 1
            if nxt not in visited:
                visited.add(nxt)
                levels[nxt] = depth + 1
                queue.append(nxt)
    return visited, levels, traversals


g = build_sample_graph()
visited, levels, traversals = traverse(g, "p1", 2)
print("visited    :", sorted(visited))
print("levels     :", {k: levels[k] for k in sorted(levels)})
print("traversals :", traversals)
```

Output —

```text
visited    : ['c1', 'p1', 'p2', 't1']
levels     : {'c1': 1, 'p1': 0, 'p2': 1, 't1': 1}
traversals : 5
```

### Data structure သုံးခု

- `visited` — set။ node တစ်ခု ရောက်ပြီး/မရောက်ပြီ မှတ်သည်။ `in` စစ်ခြင်းသည်
  O(1) ဖြစ်သည်။
- `levels` — dict။ node → start မှ အကွာအဝေး (hop အရေအတွက်)။ start သည် `0`။
- `traversals` — int။ ဖြတ်လိုက်သော **directed edge** တိုင်းကို ရေတွက်သည်။

### Loop ကို အပိုင်းလိုက် ဖတ်ခြင်း

```python
while queue:
    cur = queue.popleft()
    depth = levels[cur]
    if depth == max_depth:
        continue
    for _rtype, nxt in graph.out_edges(cur):
        traversals += 1
        if nxt not in visited:
            visited.add(nxt)
            levels[nxt] = depth + 1
            queue.append(nxt)
```

`while queue:` သည် queue အလွတ်မဖြစ်သရွေ့ လုပ်သည် (empty deque သည် `False`)။
`cur = queue.popleft()` က အရှေ့ဆုံး node ကို ယူသည်။ `depth = levels[cur]` က ထို node
၏ hop အရေအတွက်။ `if depth == max_depth: continue` က depth limit တွင် ရပ်သည်
(Section 3)။

`for _rtype, nxt in graph.out_edges(cur):` သည် outgoing edge တိုင်းကို ဖြတ်သည် —
`out_edges` သည် `(rel_type, target_id)` tuple များ ပြန်သဖြင့် tuple unpacking
လုပ်သည်။ `_rtype` တွင် underscore ရှေ့ဆက်ထားသည်က "ဤ variable ကို မသုံးပါ" ဆိုသည့်
အမှတ်အသား ဖြစ်သည်။

`if nxt not in visited:` သည် node အသစ်ဖြစ်မှသာ ထည့်သည် — duplicate ဖြတ်ခြင်းကို
ရှောင်သည်။ `levels[nxt] = depth + 1` က hop တစ်ခု တိုးသည်။

---

## 3. Depth limit — `if depth == max_depth: continue`

`traverse` သည် start node ကို depth 0 သတ်မှတ်ပြီး `max_depth` အထိသာ ဆင်းသည်။

```python
g = build_sample_graph()
for d in (0, 1, 2, 3):
    v, l, t = traverse(g, "p1", d)
    print("max_depth=%d -> visited=%-28s traversals=%d" % (d, sorted(v), t))
```

Output —

```text
max_depth=0 -> visited=['p1']                       traversals=0
max_depth=1 -> visited=['c1', 'p1', 'p2', 't1']     traversals=3
max_depth=2 -> visited=['c1', 'p1', 'p2', 't1']     traversals=5
max_depth=3 -> visited=['c1', 'p1', 'p2', 't1']     traversals=5
```

`max_depth=0` တွင် start node သာ ရောက်သည် — `p1` ၏ depth သည် `0` ဖြစ်ပြီး
`if depth == max_depth` က `continue` လုပ်သဖြင့် edge မဖြတ်ပါ, traversals `0`။

`max_depth=1` တွင် `p1` က ဖြတ်သည် (depth 0 ≠ 1) — outgoing edge ၃ ခု → traversals 3။
သို့သော် `p2`၊ `c1`၊ `t1` (depth 1) တို့က `continue` လုပ်သဖြင့် ၎င်းတို့၏ edge များ
မဖြတ်ပါ။ `max_depth=2` တွင် `p2`၊ `c1` တို့က ဖြတ်ပြီး edge ၂ ခု ပိုဖြတ်သည် —
traversals `5`။ `max_depth=3` တွင် ထပ်တိုးစရာ မရှိပါ (`t1` ၏ out_edges အလွတ်) ။

---

## 4. `traversals` — edge တိုင်းကို ရေတွက်ခြင်း

`traversals` သည် node အသစ် ဖြစ်/မဖြစ် မခွဲဘဲ ဖြတ်လိုက်သော edge **တိုင်း** ကို
ရေတွက်သည်။ အောက်ပါ step trace ကို `build_sample_graph()` ဖြင့် run သည်။

```python
from collections import deque

g = build_sample_graph()
q = deque(["p1"])
lv = {"p1": 0}
seen = {"p1"}
step = 0
traversals = 0
while q:
    cur = q.popleft()
    out = g.out_edges(cur)
    print("step %d: pop=%-3s depth=%d out_edges=%s" % (step, cur, lv[cur], out))
    traversals += len(out)
    step += 1
    if lv[cur] == 2:
        continue
    for _rt, nx in out:
        if nx not in seen:
            seen.add(nx)
            lv[nx] = lv[cur] + 1
            q.append(nx)
print("edge traversals counted :", traversals)
```

Output —

```text
step 0: pop=p1  depth=0 out_edges=[('KNOWS', 'p2'), ('WORKS_AT', 'c1'), ('USES', 't1')]
step 1: pop=p2  depth=1 out_edges=[('WORKS_AT', 'c1')]
step 2: pop=c1  depth=1 out_edges=[('USES', 't1')]
step 3: pop=t1  depth=1 out_edges=[]
edge traversals counted : 5
```

| step | pop | depth | out_edges | traversals (cumulative) |
| --- | --- | --- | --- | --- |
| 0 | `p1` | 0 | KNOWS→p2၊ WORKS_AT→c1၊ USES→t1 | 3 |
| 1 | `p2` | 1 | WORKS_AT→c1 | 4 |
| 2 | `c1` | 1 | USES→t1 | 5 |
| 3 | `t1` | 1 | (အလွတ်) | 5 |

`p2` ၏ `WORKS_AT→c1` သည် `c1` ကို `visited` တွင် ရှိပြီးဖြစ်သော်လည်း **ရေတွက်ခံရသည်**
(traversals 4 သို့ တက်)။ ဒါကြောင့် `traversals` သည် "node အသစ် အရေအတွက်" မဟုတ်ဘဲ
"ဖြတ်လိုက်သော edge အရေအတွက်" ဖြစ်သည်။ ၎င်းသည် index-free adjacency ၏ **စစ်မှန်သော
cost ဖြစ်သည်** — DB သည် edge record ကို pointer ဖြင့် ဖတ်ရသဖြင့် ရေတွက်ခံရသည်။

`step 3` တွင် `t1` ကို pop လုပ်သော်လည်း `out_edges` အလွတ်သဖြင့် ဘာမှ မဖြတ်ပါ။
ဤအချက်က traversal cost သည် **ဖြတ်လိုက်သော edge ပေါ်တွင်သာ** မှီခိုကြောင်း ပြသည်။

---

## 5. `shortest_path()` — `prev` map ဖြင့် လမ်းကြောင်း ပြန်လိုက်ခြင်း

BFS သည် unweighted graph တွင် shortest path ကို ပေးသည်။ `prev` dict တွင် node တိုင်း၏
ရှေ့ node ကို မှတ်ထားပြီး destination ရောက်သည့်အခါ ပြန်လိုက်သည်။

```python
from collections import deque


def shortest_path(graph, src, dst):
    prev = {}
    seen = {src}
    queue = deque([src])
    while queue:
        cur = queue.popleft()
        if cur == dst:
            path = [cur]
            while path[-1] != src:
                path.append(prev[path[-1]])
            return list(reversed(path))
        for _rtype, nxt in graph.out_edges(cur):
            if nxt not in seen:
                seen.add(nxt)
                prev[nxt] = cur
                queue.append(nxt)
    return []


g = build_sample_graph()
for src, dst in [("p2", "t1"), ("p1", "p1"), ("t1", "p2"), ("p1", "nope")]:
    path = shortest_path(g, src, dst)
    print("%-5s -> %-5s : %-22s hops=%s" % (src, dst, path, len(path) - 1 if path else "n/a"))
```

Output —

```text
p2    -> t1    : ['p2', 'c1', 't1']     hops=2
p1    -> p1    : ['p1']                 hops=0
t1    -> p2    : []                     hops=n/a
p1    -> nope  : []                     hops=n/a
```

### `prev` map

`prev[nxt] = cur` သည် "`nxt` သို့ `cur` မှ ရောက်သည်" ကို မှတ်သည်။ ဥပမာ `p2` မှ စလျှင်
`prev = {'c1': 'p2', 't1': 'c1'}` ဖြစ်သည်။

### လမ်းကြောင်း ပြန်လိုက်ခြင်း

```python
path = [cur]                      # destination မှ စ
while path[-1] != src:
    path.append(prev[path[-1]])   # ရှေ့ node သို့ ပြန်တက်
return list(reversed(path))
```

`path[-1]` သည် list ၏ နောက်ဆုံး element ဖြစ်သည်။ destination မှ စပြီး `prev` ဖြင့်
source အထိ ပြန်တက်သည်။ ထို့နောက် `list(reversed(path))` ဖြင့် လမ်းကြောင်းကို
source → destination အစီအစဉ် ပြောင်းသည်။ ရလဒ်မှာ `['p2', 'c1', 't1']` — hops ၂။

### အစွန်း case များ

- `p1 -> p1` — source နှင့် destination တူညီလျှင် `['p1']` ပြန်သည်, hops 0။
- `t1 -> p2` — `t1` တွင် outgoing edge မရှိသဖြင့် လမ်းကြောင်း မရှိပါ → `[]`။ ဤ graph သည်
  **directed** ဖြစ်သဖြင့် `p2 → c1 → t1` ရှိပေမဲ့ `t1 → p2` မရှိပါ။
- `p1 -> nope` — မရှိသော node အတွက် `[]` ပြန်သည်, error မဖြစ်ပါ။

`max_depth` မပါဘဲ `while queue` က graph တစ်ခုလုံး ကုန်သည်အထိ ဆင်းသည် — လမ်းကြောင်း
မရှိသည့်အခါ လုံးလုံး ပြီးဆုံးမှ `[]` ပြန်သည်။

---

## 6. `index_lookups()` — index-based engine ၏ ခန့်မှန်း cost

နှိုင်းယှဉ်ရန် — index-based engine သည် hop တိုင်းအတွက် index lookup လိုသည်ဟု
simulate လုပ်သည်။ ဤ snippet သည် graph မလိုဘဲ သီးခြား run သည်။

```python
import math


def index_lookups(visited, total_nodes):
    if total_nodes <= 1:
        return visited
    return visited * max(1, int(math.ceil(math.log(total_nodes, 2))))


print("log2(4)    =", math.log(4, 2), "ceil =", math.ceil(math.log(4, 2)))
print("log2(1004) =", math.log(1004, 2), "ceil =", math.ceil(math.log(1004, 2)))
print("index_lookups(4, 4)    :", index_lookups(4, 4))
print("index_lookups(4, 1004) :", index_lookups(4, 1004))
print("index_lookups(4, 1)    :", index_lookups(4, 1))
```

Output —

```text
log2(4)    = 2.0 ceil = 2
log2(1004) = 9.971543553950772 ceil = 10
index_lookups(4, 4)    : 8
index_lookups(4, 1004) : 40
index_lookups(4, 1)    : 4
```

`math.log(total_nodes, 2)` သည် log base 2 ဖြစ်သည် — index တစ်ခုတွင် lookup cost က
binary search လို `O(log N)` ဖြစ်သည်ဟု ကိုယ်စားပြုသည်။ `math.ceil()` က အထက်သို့
ကိန်းပြည့်ပြောင်းသည် — `log2(4) = 2.0` (ကိန်းပြည့်ဖြစ်နှင့်)၊ `log2(1004) = 9.97...`
ဖြစ်သဖြင့် `ceil` → `10`။

`visited × ceil(log2 N)` — node ၄ ခု ရောက်သည့် traversal တစ်ခုအတွက် `4 × 2 = 8`
(4-node graph)၊ `4 × 10 = 40` (1004-node graph)။ `total_nodes <= 1` ဖြစ်လျှင်
`log2(1) = 0` ဖြစ်သဖြင့် lookup `0` ဖြစ်မည် — ထို case ကို သီးခြား `return visited`
ဖြင့် ဖမ်းထားသည်။

---

## 7. Isolated node ၁၀၀၀ ထည့်ပြီး သက်သေပြခြင်း

Index-free adjacency ၏ အဓိက အချက်မှာ traversal cost သည် N ပေါ်တွင် မမှီခိုခြင်း ဖြစ်သည်။
Graph ကို ချိတ်ဆက်မှုမရှိသော node ၁၀၀၀ ဖြင့် ကြီးစေပြီး ပြန်တိုင်းတာသည်။

```python
import math


def index_lookups(visited, total_nodes):
    if total_nodes <= 1:
        return visited
    return visited * max(1, int(math.ceil(math.log(total_nodes, 2))))


g = build_sample_graph()
visited, levels, traversals = traverse(g, "p1", 2)
lookups_small = index_lookups(len(visited), 4)
for i in range(1000):
    g.add_node("iso_" + str(i), ("Isolated",))
_v2, _l2, traversals_big = traverse(g, "p1", 2)
lookups_big = index_lookups(len(visited), 1004)
print("total nodes        :", len(g.nodes))
print("edge traversals    :", traversals, "->", traversals_big)
print("index lookups      :", lookups_small, "->", lookups_big)
print("isolated out_edges :", g.out_edges("iso_0"))
```

Output —

```text
total nodes        : 1004
edge traversals    : 5 -> 5
index lookups      : 8 -> 40
isolated out_edges : []
```

Node အရေအတွက် ၄ မှ ၁၀၀၄ သို့ ၂၅၀ ဆ တက်သွားသော်လည်း `traversals` သည် **၅ တွင်
မပြောင်း** ပါ။ Isolated node များသည် reachable မဖြစ်သဖြင့် traversal သည် မထိပါ။
`index_lookups` မှာမူ `8 → 40` သို့ ကြီးလာသည် — N ပေါ်တွင် မှီခိုသည်။

| အတိုင်းအတာ | 4 nodes | 1004 nodes | ကွာခြားချက် |
| --- | --- | --- | --- |
| `total nodes` | 4 | 1004 | 251× |
| `traversals` | 5 | 5 | မပြောင်း |
| `index_lookups` | 8 | 40 | 5× တက် |
| `isolated out_edges` | — | `[]` | ချိတ်ဆက်မှု မရှိ |

ဤကွာခြားချက်သည်ပင် Neo4j ကို GraphRAG retrieval အတွက် ရွေးချယ်ရသည့် အဓိက
အကြောင်းရင်း ဖြစ်သည် — entity-anchored subgraph ကို ရှာသည့်အခါ cost သည် "ဖြတ်သည့်
edge အရေအတွက်" ပေါ်တွင်သာ မှီခိုပြီး database တစ်ခုလုံး၏ အရွယ်အစား ပေါ်တွင်
မမှီခိုပါ။

> `index_lookups` သည် **simulation** ဖြစ်သည် — Neo4j ၏ တကယ့် query plan မဟုတ်ပါ။
> Index-based engine ကို နှိုင်းယှဉ်ရန် ရိုးရှင်းသော cost model တစ်ခု ဖြစ်သည်။

---

## 8. Code တစ်ခုလုံး — Run လုပ်နိုင်သော Version

```python
from collections import deque
from dataclasses import dataclass, field
from typing import Dict, Tuple


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
        self.nodes = {}
        self.relationships = []
        self.out_adj = {}
        self.in_adj = {}

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


def traverse(graph, start_id, max_depth):
    visited = {start_id}
    levels = {start_id: 0}
    traversals = 0
    queue = deque([start_id])
    while queue:
        cur = queue.popleft()
        depth = levels[cur]
        if depth == max_depth:
            continue
        for _rtype, nxt in graph.out_edges(cur):
            traversals += 1
            if nxt not in visited:
                visited.add(nxt)
                levels[nxt] = depth + 1
                queue.append(nxt)
    return visited, levels, traversals


def shortest_path(graph, src, dst):
    prev = {}
    seen = {src}
    queue = deque([src])
    while queue:
        cur = queue.popleft()
        if cur == dst:
            path = [cur]
            while path[-1] != src:
                path.append(prev[path[-1]])
            return list(reversed(path))
        for _rtype, nxt in graph.out_edges(cur):
            if nxt not in seen:
                seen.add(nxt)
                prev[nxt] = cur
                queue.append(nxt)
    return []


g = build_sample_graph()
visited, levels, traversals = traverse(g, "p1", 2)
print("visited (2-hop from p1):", sorted(visited))
print("levels                 :", {k: levels[k] for k in sorted(levels)})
print("edge traversals        :", traversals)
path = shortest_path(g, "p2", "t1")
print("shortest path p2 -> t1 :", " -> ".join(path), "(hops =", len(path) - 1, ")")
```

Output —

```text
visited (2-hop from p1): ['c1', 'p1', 'p2', 't1']
levels                 : {'c1': 1, 'p1': 0, 'p2': 1, 't1': 1}
edge traversals        : 5
shortest path p2 -> t1 : p2 -> c1 -> t1 (hops = 2 )
```

> `print("(hops =", len(path) - 1, ")")` သည် `(hops = 2 )` ဟု space နှစ်ခုဖြင့် ထုတ်သည် —
> `print()` က argument များကြား space ထည့်သဖြင့် ဖြစ်သည်။

---

## 9. ကိုယ်တိုင်လေ့ကျင့်ကြည့်ပါ

**မေးခွန်း** — အောက်ပါ code က ဘယ်ရလဒ် ပြန်မလဲ။

```python
import math


def index_lookups(visited, total_nodes):
    if total_nodes <= 1:
        return visited
    return visited * max(1, int(math.ceil(math.log(total_nodes, 2))))


print(index_lookups(5, 1004), index_lookups(1, 1))
```

1. `50 0`
2. `50 1`
3. `10 0`
4. `5 1`

<details>
<summary>အဖြေ ကြည့်ရန်</summary>

**အဖြေ — 2. `50 1`**

အကြောင်းရင်း — `index_lookups(5, 1004)` အတွက် `ceil(log2(1004)) = ceil(9.97...) = 10`၊
ထို့ကြောင့် `5 × 10 = 50`။ ဒုတိယ case တွင် `total_nodes = 1` ဖြစ်ပြီး `total_nodes <= 1`
ဖြစ်သဖြင့် `if` အစိတ်အပိုင်းက `return visited` → `1`။
`log2(1) = 0` ဖြစ်သဖြင့် `if` မပါလျှင် lookup `0` ဖြစ်မည် — ထို့ကြောင့်
`total_nodes <= 1` ကို သီးခြား ဖမ်းထားခြင်း ဖြစ်သည်။ ဤ code ကို run ၍
အတည်ပြုပြီးဖြစ်သည်။

</details>

---

**အဓိက မှတ်ထားရန်** — Index-free adjacency ၏ အနှစ်သာရမှာ **traversal cost သည် graph
အရွယ်အစား N ပေါ်တွင် မမှီခိုခြင်း** ဖြစ်သည်။ `traversals` သည် ဖြတ်လိုက်သော directed
edge တိုင်းကို ရေတွက်သဖြင့် isolated node ၁၀၀၀ ထည့်လည်း ၅ တွင်ပင် ရှိသည်။
`shortest_path` သည် BFS နှင့် `prev` map ဖြင့် unweighted graph ၏ shortest path ကို
ပေးသည်။ Neo4j သည် relationship များကို doubly-linked pointer အဖြစ် store လုပ်သဖြင့်
ဤအချက်သည် တကယ့် engine တွင် အလုပ်လုပ်သည် — GraphRAG retrieval တွင် multi-hop
subgraph ကို ရွေးချယ်ရသည့် အဓိက အကြောင်းရင်း ဖြစ်သည်။
