# Walkthrough 06 — Community Detection (Exercise 6)

> ဤဖိုင်သည် Module 07 ၏ `solution.md` ထဲက Exercise 6 ကို **Python အခြေခံမှ စ၍**
> အပိုင်းလိုက် ရှင်းပြသည့် walkthrough ဖြစ်သည်။ Format သည် Module 01 ၏
> `walkthroughs/01_regex_ner.md` နှင့် `walkthroughs/03_gazetteer_lookup.md` နှင့်
> တူညီသည်။

---

## 0. ဤ Exercise က ဘာကို ဖြေရှင်းပေးသလဲ။

Exercise 1-5 သည် **local** retrieval ဖြစ်သည် — query ထဲက anchor မှ စသည်။ သို့သော်
"corpus တစ်ခုလုံးအကြောင်း ဘာပြောနိုင်သနည်း" ကဲ့သို့ **global question** တွင်
anchor မရှိပါ။ ဤအခါ **community detection** လိုအပ်သည် — graph ကို အုပ်စု
(community) များအဖြစ် ခွဲပြီး အုပ်စုတိုင်းအတွက် summary ထုတ်သည်။

```text
property graph (10 nodes, 12 edges)
        |
        |  connected_components()      <- level 1
        v
2 communities
  community 0: co:neo4j, org:neo4jeng, prod:aura,
               tech:cypher, tech:graphrag, tech:vectorindex
  community 1: org:cnrs, paper:louvain, person:eifrem, tech:louvain
        |
        |  greedy_modularity_partition()   <- level 2
        v
level 2: Q မြင့်သည့် partition (refinement)
        |
        |  community_summaries()
        v
"Community 0 covers: AuraDB, Cypher, GraphRAG, Neo4j, ..."   <- global question ၏ retrieval unit
```

ဤ exercise တွင် hierarchy **၃ ဆင့်** ကို တည်ဆောက်ပြီး ဆင့်တိုင်းအတွက်
**modularity `Q`** ကို တွက်သည်။

| ဆင့် | အမည် | ရှင်းလင်းချက် |
| --- | --- | --- |
| level 0 | singletons | node တိုင်း သီးခြား community — trivial |
| level 1 | connected components | ဆက်စပ်မှု ရှိသည့် node အားလုံး အုပ်စုတစ်ခု |
| level 2 | modularity refinement | `Q` တက်သည့် ရွှေ့မှုကိုသာ လက်ခံသည့် Louvain-style refinement |

ဤ code မှာ လေ့လာရမည့် Python concepts များမှာ —

- `dict` comprehension (`{node: node for node in ADJ}`)
- Set union (`|=`၊ `|`)
- `deque` နှင့် `popleft()` (BFS — Exercise 2 နှင့် တူညီ)
- `collections.defaultdict(int)`
- `round(x, 10)` နှင့် float နှိုင်းယှဉ်မှု
- `while improved:` flag loop
- `dict(labels)` ဖြင့် copy (mutate မလုပ်ရန်)
- `1e-12` (scientific notation literal)
- `dict.setdefault()` ဖြင့် label numbering
- `sorted(..., key=...)` နှင့် tuple return
- `str.join()` ဖြင့် summary စာသား တည်ဆောက်ခြင်း
- `try/except` (boundary case အတွက်)

---

## 1. `connected_components()` — Level 1 Partition

```python
def connected_components(adj):
    """Level-1 partition: cheap, deterministic, no resolution parameter."""
    labels, seen = {}, set()
    for start in sorted(adj):
        if start in seen:
            continue
        comp = {start}
        queue = deque([start])
        while queue:
            for nb in sorted(adj[queue.popleft()]):
                if nb not in comp:
                    comp.add(nb)
                    queue.append(nb)
        seen |= comp
        for node in comp:
            labels[node] = start
    return labels
```

### 1.1 `labels, seen = {}, set()`

`labels` သည် node → community label mapping ဖြစ်သည်။ `seen` သည် စစ်ပြီးသား node
များ ဖြစ်သည်။ **`seen` ရှိခြင်းသည် ဤ function ၏ အဓိကအချက်** ဖြစ်သည် — မရှိလျှင်
တူညီသည့် component ကို **အကြိမ်များစွာ** ပြန်လုပ်မည်။

### 1.2 `for start in sorted(adj)` နှင့် `continue`

`sorted(adj)` သည် node id များကို အက္ခရာအစီအစဉ်ဖြင့် လှမ်းသည် — deterministic
label assignment အတွက် လိုသည်။ `if start in seen: continue` သည် **skip** လုပ်သည် —
`continue` သည် လက်ရှိ iteration ကို ရပ်ပြီး နောက်တစ်ခုသို့ သွားသည်။

### 1.3 BFS — `comp` နှင့် `queue`

```python
comp = {start}
queue = deque([start])
while queue:
    for nb in sorted(adj[queue.popleft()]):
        if nb not in comp:
            comp.add(nb)
            queue.append(nb)
```

ဤအပိုင်းသည် Exercise 2 ၏ BFS နှင့် သဘောတရား တူညီသည် — `queue.popleft()` ဖြင့်
level အလိုက် လှမ်းသည်။ သို့သော် hop budget မရှိပါ — component **ကုန်ဆုံးသည်အထိ**
လှမ်းသည်။ `comp` သည် set ဖြစ်သဖြင့် membership စစ်ခြင်း `O(1)` ဖြစ်ပြီး duplicate
ကို ဖယ်သည်။

### 1.4 `seen |= comp` — Set union update

```python
seen |= comp
for node in comp:
    labels[node] = start
```

`seen |= comp` သည် `seen = seen | comp` နှင့် တူညီသည် — **in-place union update**။
ထို့နောက် `comp` ထဲက node တိုင်းကို ထို component ၏ **ပထမဆုံး node** (အက္ခရာအစီအစဉ်
အငယ်ဆုံး) ဖြင့် label ပေးသည်။ ထို့ကြောင့် label သည် **node id တစ်ခု** ဖြစ်သည်
(ဂဏန်း မဟုတ်)။

```python
comp = {1, 2}
seen = {0}
seen |= comp
print(sorted(seen))
print(sorted(seen | {3}))
```

Output —

```text
[0, 1, 2]
[0, 1, 2, 3]
```

`|` သည် **union** ဖြစ်သည် — set အသစ်တစ်ခု ပြန်သည်။ `|=` သည် မူလ set ကို
in-place ပြင်သည်။ ဤနှစ်ခုကို ခွဲခြားသိရန် လိုသည်: `seen | {3}` သည် `seen` ကို
**မပြင်ပါ**၊ `seen |= {3}` သည် ပြင်သည်။

### 1.5 `connected_components(ADJ)` ၏ ရလဒ်

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
from collections import deque


def connected_components(adj):
    labels, seen = {}, set()
    for start in sorted(adj):
        if start in seen:
            continue
        comp = {start}
        queue = deque([start])
        while queue:
            for nb in sorted(adj[queue.popleft()]):
                if nb not in comp:
                    comp.add(nb)
                    queue.append(nb)
        seen |= comp
        for node in comp:
            labels[node] = start
    return labels


cc = connected_components(ADJ)
for node in sorted(cc):
    print("%-18s -> %s" % (node, cc[node]))
print(len(set(cc.values())), "communities")
```

Output —

```text
co:neo4j           -> co:neo4j
org:cnrs           -> org:cnrs
org:neo4jeng       -> co:neo4j
paper:louvain      -> org:cnrs
person:eifrem      -> org:cnrs
prod:aura          -> co:neo4j
tech:cypher        -> co:neo4j
tech:graphrag      -> co:neo4j
tech:louvain       -> org:cnrs
tech:vectorindex   -> co:neo4j
2 communities
```

`org:cnrs` နှင့် `co:neo4j` သည် မိမိတို့ component ၏ အငယ်ဆုံး node ဖြစ်သဖြင့်
**မိမိကိုယ်ကို label** ဖြစ်သည်။ `len(set(cc.values()))` သည် community အရေအတွက်
ဖြစ်သည် — `set()` ဖြင့် label ထပ်နေမှုကို ဖယ်သည်။

**သတိထားရန်** — `labels` dict ကို တိုက်ရိုက် `print(cc)` လုပ်လျှင် **dict
insertion order** ကို ပြမည်ဖြစ်ပြီး `comp` သည် set ဖြစ်သဖြင့် ထို order သည်
run တစ်ခုနှင့်တစ်ခု ကွဲနိုင်သည်။ ထို့ကြောင့် ဤနေရာတွင် `for node in sorted(cc)`
ဖြင့် စီပြီးမှ print လုပ်သည်။

---

## 2. `modularity()` — Newman Modularity `Q`

```python
def modularity(partition, adj):
    """Newman modularity Q = sum_c [ L_c/m - (k_c / 2m)^2 ]."""
    m = len(EDGES)
    internal, degree = defaultdict(int), defaultdict(int)
    for node in adj:
        degree[partition[node]] += len(adj[node])
    for src, _rel, dst, _chunk in EDGES:
        if partition[src] == partition[dst]:
            internal[partition[src]] += 1
    return round(sum(internal[lab] / m - (degree[lab] / (2 * m)) ** 2 for lab in degree), 10)
```

### 2.1 Formula ကို ဖတ်ခြင်း

```text
Q = Σ_c [ L_c / m  −  (k_c / 2m)² ]
```

| Symbol | အဓိပ္ပာယ် |
| --- | --- |
| `m` | edge စုစုပေါင်း |
| `L_c` | community `c` **အတွင်း**ရှိ edge အရေအတွက် |
| `k_c` | community `c` ထဲက node များ၏ degree ပေါင်း |

`Q` သည် **community အတွင်း edge များလား၊ random graph က မျှော်လင့်မည့်ထက်
ပိုလား** ကို တိုင်းသည်။ `Q` မြင့်လျှင် partition ကောင်း; `Q` အနုတ်လျှင် random
ထက်တောင် ဆိုးသည်။

### 2.2 `defaultdict(int)` နှင့် `len(adj[node])`

`degree[partition[node]] += len(adj[node])` သည် node ၏ adjacency set size ကို
ထို node ၏ community degree ထဲ ထည့်သည်။ `adj[node]` သည် **undirected** adjacency
set ဖြစ်သဖြင့် `len()` သည် degree အစစ် ဖြစ်သည် — ဤအချက်သည် အရေးကြီးသည်။
`adj` ကို **undirected** အနေအထား ကိုယ်စားပြုရမည် (Exercise 2 တွင် နှစ်ဖက်လုံး
ထည့်ထားသည်)။

**ကန့်သတ်ချက်** — `partition` သည် `adj` ထဲက node **အားလုံး** ကို ဖုံးရမည်။
မဖုံးလျှင် `partition[node]` က `KeyError` ဖြစ်သည်။

```python
from collections import defaultdict

EDGES = (("co:neo4j", "DEVELOPS", "prod:aura", "c1"),)
ADJ = {"co:neo4j": {"prod:aura"}, "prod:aura": {"co:neo4j"}}
partition = {"co:neo4j": 0, "prod:aura": 0}
degree = defaultdict(int)
for node in ADJ:
    degree[partition[node]] += len(ADJ[node])
print(sorted(degree.items()))
```

Output —

```text
[(0, 2)]
```

Node နှစ်ခုလုံးသည် community `0` ဖြစ်ပြီး တစ်ခုစီ၏ degree သည် `1` ဖြစ်သဖြင့်
`degree[0] = 1 + 1 = 2` ဖြစ်သည်။ `sorted(degree.items())` ဖြင့် print လုပ်ခြင်းသည်
`defaultdict` ကို အစီအစဉ်တကျ ပြသည်။ ဤအချက်က **edge တစ်ခုသည် degree နှစ်ခု
(undirected) ဖြစ်သည်** ဆိုသည့် အချက်ကို ပြသည် — ထို့ကြောင့် `k_c` သည်
`2 * internal` ဖြစ်နိုင်သည် (Section 2.3 တွင် community 0 အတွက် `k_c=16` နှင့်
`L_c=8` ဖြစ်သည်ကို တွေ့မည်)။

**ကန့်သတ်ချက်** — `partition` သည် `adj` ထဲက node **အားလုံး** ကို ဖုံးရမည်။
မဖုံးလျှင် `partition[node]` က `KeyError` ဖြစ်သည်။

```python
from collections import defaultdict

EDGES = (("co:neo4j", "DEVELOPS", "prod:aura", "c1"),)
adj = {"co:neo4j": {"prod:aura"}, "prod:aura": {"co:neo4j"}, "org:neo4jeng": {"co:neo4j"}}


def modularity(partition, adj):
    m = len(EDGES)
    internal, degree = defaultdict(int), defaultdict(int)
    for node in sorted(adj):
        degree[partition[node]] += len(adj[node])
    return sorted(degree)


try:
    modularity({"co:neo4j": 0, "prod:aura": 0}, adj)
except KeyError as exc:
    print("KeyError:", exc)
```

Output —

```text
KeyError: 'org:neo4jeng'
```

`sorted(adj)` ဖြင့် လှမ်းသဖြင့် `org:neo4jeng` ကို ကြိုတင်သိနိုင် (ပထမ
အက္ခရာအစီအစဉ်) သည် — `co:neo4j`၊ `org:neo4jeng`၊ `prod:aura` အစီအစဉ်ဖြင့်
လာပြီး ဒုတိယတွင် KeyError ဖြစ်သည်။ `try/except` ဖြင့် exception ကို
ဖမ်းပြီး စာသားအဖြစ် ပြသည်။ `as exc` သည် exception object ကို variable ထဲ
ထည့်သည်။

### 2.3 တကယ့် `Q` တန်ဖိုး ကို တစ်ဆင့်ချင်း ဆွဲထုတ်ခြင်း

```python
from collections import defaultdict

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

level1 = {
    "co:neo4j": "co:neo4j", "org:neo4jeng": "co:neo4j", "prod:aura": "co:neo4j",
    "tech:cypher": "co:neo4j", "tech:graphrag": "co:neo4j", "tech:vectorindex": "co:neo4j",
    "org:cnrs": "org:cnrs", "paper:louvain": "org:cnrs", "person:eifrem": "org:cnrs",
    "tech:louvain": "org:cnrs",
}
m = len(EDGES)
internal, degree = defaultdict(int), defaultdict(int)
for node in ADJ:
    degree[level1[node]] += len(ADJ[node])
for src, _rel, dst, _chunk in EDGES:
    if level1[src] == level1[dst]:
        internal[level1[src]] += 1
print("m =", m, " 2m =", 2 * m)
for label in sorted(degree):
    term = internal[label] / m - (degree[label] / (2 * m)) ** 2
    print("community %s: L_c=%d k_c=%d term=%.10f" % (label, internal[label], degree[label], term))
```

Output —

```text
m = 12  2m = 24
community co:neo4j: L_c=8 k_c=16 term=0.2222222222
community org:cnrs: L_c=4 k_c=8 term=0.2222222222
```

| Community (level-1 label) | `L_c` (internal edge) | `k_c` (degree ပေါင်း) | `L_c/m` | `(k_c/2m)²` | term |
| --- | --- | --- | --- | --- | --- |
| `co:neo4j` | 8 | 16 | 0.6667 | 0.4444 | 0.2222 |
| `org:cnrs` | 4 | 8 | 0.3333 | 0.1111 | 0.2222 |

Label များသည် **node id** ဖြစ်ကြသည် (`co:neo4j`၊ `org:cnrs`) — `canonicalize()`
(Section 4) မလုပ်ရသေးသဖြင့် ဂဏန်း မဟုတ်ပါ။ `Q = 0.2222 + 0.2222 = 0.4444`။
`co:neo4j` community သည် node ၆ ခုနှင့် internal edge ၈ ခု ရှိပြီး `org:cnrs`
community သည် node ၄ ခုနှင့် internal edge ၄ ခု ရှိသည်။ **term နှစ်ခု တူညီသည်ကို**
သတိထားပါ — `co:neo4j` community ကြီးသော်လည်း သူ့ `k_c/2m` လည် ကြီးသဖြင့်
ချေဖျက်သည်။ ဤအချက်က `Q` သည် **edge ရေတွက်ချက် နှင့် expected edge ရေတွက်ချက်
နှစ်ခုလုံး** ကို စဉ်းစားသည့် သဘောကို ပြသည်။

### 2.4 Level 0 (singletons) ၏ `Q` သည် အနုတ် ဖြစ်သည်

Level 0 (`{node: node for node in ADJ}`) တွင် node တိုင်း သီးခြား community ဖြစ်သဖြင့်
`L_c = 0` အမြဲ ဖြစ်သည် (community အတွင်း edge မရှိ)။ ထို့ကြောင့်
`Q = −Σ_c (k_c/2m)²` ဖြစ်ပြီး အနုတ်သာ ဖြစ်သည်။

```python
degrees = sorted(len(ADJ[node]) for node in ADJ)
print(degrees)
print("sum k^2 =", sum(d * d for d in degrees), "  4m^2 =", 4 * len(EDGES) ** 2)
print("level 0 Q =", modularity({node: node for node in ADJ}, ADJ))
```

Output —

```text
[1, 1, 2, 2, 2, 3, 3, 3, 3, 4]
sum k^2 = 66   4m^2 = 576
level 0 Q = -0.1145833333
```

`Σ k² = 66`၊ `(2m)² = 24² = 576` ဖြစ်သဖြင့် `Q = −66/576 = −0.114583…`။
**Community အရေအတွက် ၁၀ ခု ရှိသည်မှာ level 0** ဖြစ်ပြီး `Q` မှာ အနုတ် ဖြစ်သည် —
ဤအချက်သည် "community အရေအတွက် များလျှင် ကောင်းသည်" ဆိုသည့် အမှားကို
ဖော်ပြသည်။

---

## 3. `greedy_modularity_partition()` — Level 2 Refinement

```python
def greedy_modularity_partition(adj, init_labels):
    """Louvain-style single-level refinement: accept only improving moves."""
    labels = dict(init_labels)
    improved = True
    while improved:
        improved = False
        for node in sorted(adj):
            base = modularity(labels, adj)
            best_label, best_gain = labels[node], 1e-12
            for cand in sorted({labels[nb] for nb in adj[node]} - {labels[node]}):
                trial = dict(labels)
                trial[node] = cand
                gain = modularity(trial, adj) - base
                if gain > best_gain:
                    best_gain, best_label = gain, cand
            if best_label != labels[node]:
                labels[node] = best_label
                improved = True
    return labels
```

### 3.1 `labels = dict(init_labels)` — copy (mutate မလုပ်ရ)

`dict(init_labels)` သည် dict အသစ် တစ်ခု ဖန်တီးသည်။ `labels = init_labels` လို့
ရေးလျှင် caller ၏ dict ကို **တိုက်ရိုက် ပြင်မိမည်** (aliasing)။ Function သည်
input ကို မပြင်သင့်ပါ — ထို့ကြောင့် copy လုပ်သည်။

### 3.2 `while improved:` — flag loop

`improved = True` ဖြင့် စပြီး loop အတွင်းတွင် `False` လို့ ပြန်ထားသည်။
ရွှေ့မှု တစ်ခုခု ဖြစ်လျှင် `True` ပြန်ဖြစ်ပြီး outer loop က ထပ်လုပ်သည်။
ဘာမှ မရွှေ့လျှင် loop ရပ်သည်။ ဤပုံစံသည် **greedy local search** ၏
standard pattern ဖြစ်သည်။

### 3.3 `base` နှင့် `best_gain = 1e-12`

```python
base = modularity(labels, adj)
best_label, best_gain = labels[node], 1e-12
```

`base` သည် လက်ရှိ partition ၏ `Q` ဖြစ်သည် — node တိုင်းအတွက် ပြန်တွက်သည်
(`O(n)` ခေါ်မှု များသည်၊ သို့သော် ဤ graph သေးသဖြင့် အဆင်ပြေသည်)။
`1e-12` သည် **scientific notation** ဖြစ်သည် — `0.000000000001`။ ဤ threshold သည်
"အလွန်သေးငယ်သည့် တိုးတက်မှုကို လက်မခံ" ဟု ဆိုလိုသည် — float rounding
noise ကြောင့် loop မဆုံးနိုင်ခြင်းကို ကာကွယ်သည်။

### 3.4 `trial = dict(labels)` — speculative move

```python
for cand in sorted({labels[nb] for nb in adj[node]} - {labels[node]}):
    trial = dict(labels)
    trial[node] = cand
    gain = modularity(trial, adj) - base
```

`{labels[nb] for nb in adj[node]} - {labels[node]}` သည် **neighbor များ၏
community များ** မှ လက်ရှိ community ကို ဖယ်သည် — node ကို ရွှေ့နိုင်သည့်
community များ ဖြစ်သည်။ `trial = dict(labels)` သည် **မရွှေ့မီ စမ်းသပ်မှု**
ဖြစ်သည် — `trial` ကို ပြင်ပြီး `Q` ကို တွက်ကြည့်သည်။ မကောင်းလျှင် `labels`
ကို မထိပါ။ ဤ pattern ကို **trial-and-commit** ဟု ခေါ်သည်။

### 3.5 `if gain > best_gain` — တိုးတက်မှုကိုသာ လက်ခံ

`gain > best_gain` ဖြစ်သဖြင့် `Q` မတိုးသည့် ရွှေ့မှု (gain ≤ 0) ကို **လက်မခံ**။
ထို့ကြောင့် level 2 ၏ `Q` သည် level 1 ၏ `Q` ထက် **ဘယ်တော့မှ လျော့မည် မဟုတ်** —
ဤအချက်သည် `assert q2 >= q1 - 1e-12` ၏ အကြောင်းရင်း ဖြစ်သည်။

### 3.6 ဤ fixture တွင် ရွှေ့မှု တစ်ခုမှ မဖြစ်ပါ

အထက်ပါ loop ကို trace လုပ်ကြည့်ပါ။

```python
from collections import defaultdict, deque

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


def connected_components(adj):
    labels, seen = {}, set()
    for start in sorted(adj):
        if start in seen:
            continue
        comp = {start}
        queue = deque([start])
        while queue:
            for nb in sorted(adj[queue.popleft()]):
                if nb not in comp:
                    comp.add(nb)
                    queue.append(nb)
        seen |= comp
        for node in comp:
            labels[node] = start
    return labels


def modularity(partition, adj):
    m = len(EDGES)
    internal, degree = defaultdict(int), defaultdict(int)
    for node in adj:
        degree[partition[node]] += len(adj[node])
    for src, _rel, dst, _chunk in EDGES:
        if partition[src] == partition[dst]:
            internal[partition[src]] += 1
    return round(sum(internal[lab] / m - (degree[lab] / (2 * m)) ** 2 for lab in degree), 10)


cc = connected_components(ADJ)
labels = dict(cc)
improved = True
rounds = 0
moves = []
while improved:
    improved = False
    rounds += 1
    for node in sorted(ADJ):
        base = modularity(labels, ADJ)
        best_label, best_gain = labels[node], 1e-12
        for cand in sorted({labels[nb] for nb in ADJ[node]} - {labels[node]}):
            trial = dict(labels)
            trial[node] = cand
            gain = modularity(trial, ADJ) - base
            if gain > best_gain:
                best_gain, best_label = gain, cand
        if best_label != labels[node]:
            labels[node] = best_label
            improved = True
            moves.append((node, best_label))
print("rounds:", rounds, "improved:", improved, "moves:", moves)
print("level 2 Q =", modularity(labels, ADJ))
```

Output —

```text
rounds: 1 improved: False moves: []
level 2 Q = 0.4444444444
```

`rounds: 1` နှင့် `moves: []` — ရွှေ့မှု **တစ်ခုမှ** မဖြစ်ပါ။ အကြောင်းရင်းမှာ
ဤ fixture တွင် component နှစ်ခုကြား **edge လုံးဝ မရှိ** သဖြင့် node တစ်ခုကို
အခြား component သို့ ရွှေ့လျှင် `Q` သည် ကျသည်သာ ဖြစ်သည်။ ထို့ကြောင့် level 2 ၏
`Q` သည် level 1 နှင့် **တူညီသည်** (`0.4444444444`)။

ဤအချက်သည် အရေးကြီးသည့် သင်ခန်းစာ ဖြစ်သည် — **refinement သည် အမြဲ တိုးတက်မှု
မပေးပါ**။ Level 1 (`connected_components`) သည် အလွန်ဈေးသက်သာပြီး parameter
မလိုသဖြင့် graph သည် component နှစ်ခုသာ ဖြစ်လျှင် level 2 က ဘာမှ မထပ်တိုးပါ။
ကြီးမားသည့် graph တွင် modularity refinement သည် component တစ်ခုအတွင်းမှ
community များကို ထပ်ခွဲပေးသည်။

---

## 4. `canonicalize()` — Label များကို 0, 1, … ပြန်နံပါတ်တပ်ခြင်း

```python
def canonicalize(labels):
    order = {}
    for node in sorted(labels):
        order.setdefault(labels[node], len(order))
    return {node: order[label] for node, label in labels.items()}
```

`connected_components()` သည် label အဖြစ် **node id** ကို ပြန်သည်
(`co:neo4j`၊ `org:cnrs`)။ `canonicalize()` သည် ထို label များကို `0`၊ `1`၊ … ဂဏန်း
အဖြစ် ပြောင်းသည် — **ပထမ ပေါ်ပေါက်သည့် node အစီအစဉ်အတိုင်း**။

`order.setdefault(labels[node], len(order))` သည် —
- label ကို မမြင်ဖူးသေးလျှင် လက်ရှိ `order` size ကို နံပါတ်အဖြစ် သတ်မှတ်သည်
  (ထို့ကြောင့် `0`၊ `1`၊ `2` … အစဉ်လိုက်)။
- မြင်ဖူးပြီးသားလျှင် မပြင်ပါ။

`for node in sorted(labels)` ဖြစ်သဖြင့် နံပါတ်တပ်ခြင်းသည် **node id အက္ခရာအစီအစဉ်**
ကို အခြေခံသည် — run တိုင်း တူညီသည်။ သို့သော် **label assignment ကိုယ်တိုင်**
(ဥပမာ Louvain တွင် မည်သည့် community က `0` ဖြစ်မည်) သည် order အပေါ် မှီခိုသည်။
ထို့ကြောင့် `canonicalize` ဖြင့် ရလဒ်ကို တည်ငြိမ်စေသည်။

```python
def canonicalize(labels):
    order = {}
    for node in sorted(labels):
        order.setdefault(labels[node], len(order))
    return {node: order[label] for node, label in labels.items()}


labels = {"b": "z", "a": "y", "c": "z"}
result = canonicalize(labels)
print(result)
print("a ->", result["a"], "| b ->", result["b"], "| c ->", result["c"])
```

Output —

```text
{'b': 1, 'a': 0, 'c': 1}
a -> 0 | b -> 1 | c -> 1
```

`sorted(labels)` သည် `['a', 'b', 'c']` ဖြစ်သဖြင့် —
`a` အတွက် `order.setdefault("y", 0)` → `y → 0` (ပထမ label);
`b` အတွက် `order.setdefault("z", 1)` → `z → 1` (ဒုတိယ label);
`c` အတွက် `order.setdefault("z", 2)` → `"z"` ရှိပြီးသားဖြစ်သဖြင့် `1` ပြန်သည်။

ထို့ကြောင့် `c → 1` ဖြစ်သည်။ **`c` နှင့် `b` သည် label တူညီသည့် community
တစ်ခုတည်း ဖြစ်သဖြင့် ဂဏန်းလည် တူရမည်** — ဤအချက်သည် `canonicalize()` ၏
မှန်ကန်မှုကို စစ်သည့် အဓိကအချက် ဖြစ်သည်။ `setdefault` ၏ ဒုတိယ argument
(`len(order)`) သည် ခေါ်တိုင်း တွက်ချက်ခံရသော်လည်း key ရှိပြီးသားလျှင်
**အသုံးမပြု**သဖြင့် ရလဒ် မပြောင်းပါ။

ပြန်လာသည့် dict ၏ **ပြသအစီအစဉ်** သည် `labels` literal ၏ key အစီအစဉ်အတိုင်း
ဖြစ်သည် (`b`၊ `a`၊ `c`) — ထို့ကြောင့် `{'b': 1, 'a': 0, 'c': 1}` ဟု ပေါ်သည်။
ဂဏန်းတန်ဖိုးများ (mapping) ကိုသာ ဖတ်ရမည်၊ အစီအစဉ်ကို အဓိပ္ပာယ် မကောက်ရပါ။
စစ်ရန် လိုလျှင် `sorted(canonicalize(labels).items())` ကို သုံးရမည်။

---

## 5. `community_summaries()` — Global Question ၏ Retrieval Unit

```python
def community_summaries(labels):
    groups = defaultdict(list)
    for node, label in sorted(labels.items()):
        groups[label].append(node)
    return [(label, members, "Community %d covers: %s" % (
        label, ", ".join(sorted(NODES[m][1] for m in members))))
        for label, members in sorted(groups.items())]
```

`groups` သည် `defaultdict(list)` ဖြစ်သည် — label → member node များ။ `for node,
label in sorted(labels.items())` သည် **item** များကို sort လုပ်သည် (tuple
နှိုင်းယှဉ်မှုဖြစ်သဖြင့် node id ဖြင့် စီသည်)။ ထို့ကြောင့် `members` list သည်
node id အစီအစဉ်ဖြင့် လာသည်။

Summary စာသားတွင် node ၏ **name** (`NODES[m][1]`) ကို သုံးသည်၊ id မဟုတ်ပါ — LLM
အတွက် name က ဖတ်ရလွယ်သည်။ `sorted(...)` ဖြင့် အက္ခရာအစီအစဉ် ပြန်စီသည်။
`", ".join(...)` သည် list ကို `", "` ဖြင့် ဆက်သည်။ Return သည် **tuple** ၏ list
ဖြစ်သည် — `(label, members, summary)`။

```python
labels = {"co:neo4j": 0, "org:neo4jeng": 0, "prod:aura": 0, "tech:cypher": 0,
          "tech:graphrag": 0, "tech:vectorindex": 0,
          "org:cnrs": 1, "paper:louvain": 1, "person:eifrem": 1, "tech:louvain": 1}
NODES = {
    "co:neo4j": ("Company", "Neo4j", (), "Graph database vendor."),
    "org:neo4jeng": ("Team", "Neo4j Engineering", (), "Engineering team."),
    "prod:aura": ("Product", "AuraDB", (), "Managed cloud service."),
    "tech:cypher": ("Technology", "Cypher", (), "Declarative graph query language."),
    "tech:graphrag": ("Technology", "GraphRAG", (), "Retrieval pattern."),
    "tech:vectorindex": ("Technology", "Vector Index", (), "Approximate index."),
    "org:cnrs": ("Organization", "CNRS", (), "Research organisation."),
    "paper:louvain": ("Paper", "Fast unfolding of communities in large networks", (), "The 2008 paper."),
    "person:eifrem": ("Person", "Vincent Blondel", (), "Lead author."),
    "tech:louvain": ("Technology", "Louvain", (), "Greedy modularity."),
}
from collections import defaultdict


def community_summaries(labels):
    groups = defaultdict(list)
    for node, label in sorted(labels.items()):
        groups[label].append(node)
    return [(label, members, "Community %d covers: %s" % (
        label, ", ".join(sorted(NODES[m][1] for m in members))))
        for label, members in sorted(groups.items())]


for label, members, summary in community_summaries(labels):
    print("  %s" % summary)
    print("    members=%s" % members)
```

Output —

```text
  Community 0 covers: AuraDB, Cypher, GraphRAG, Neo4j, Neo4j Engineering, Vector Index
    members=['co:neo4j', 'org:neo4jeng', 'prod:aura', 'tech:cypher', 'tech:graphrag', 'tech:vectorindex']
  Community 1 covers: CNRS, Fast unfolding of communities in large networks, Louvain, Vincent Blondel
    members=['org:cnrs', 'paper:louvain', 'person:eifrem', 'tech:louvain']
```

Summary တိုင်းသည် **global question အတွက် retrieval unit** ဖြစ်လာသည်။ "corpus
တစ်ခုလုံးအကြောင်း ဘာပြောနိုင်သနည်း" မေးလျှင် summary နှစ်ခုလုံးကို ပေးရမည်;
"Neo4j ecosystem အကြောင်း" မေးလျှင် community 0 ၏ summary ကို ပေးရမည်။

---

## 6. Level သုံးဆင့်ကို တစ်ကြိမ်တည်း run ခြင်း

```python
import math
from collections import defaultdict, deque

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


def connected_components(adj):
    labels, seen = {}, set()
    for start in sorted(adj):
        if start in seen:
            continue
        comp = {start}
        queue = deque([start])
        while queue:
            for nb in sorted(adj[queue.popleft()]):
                if nb not in comp:
                    comp.add(nb)
                    queue.append(nb)
        seen |= comp
        for node in comp:
            labels[node] = start
    return labels


def modularity(partition, adj):
    m = len(EDGES)
    internal, degree = defaultdict(int), defaultdict(int)
    for node in adj:
        degree[partition[node]] += len(adj[node])
    for src, _rel, dst, _chunk in EDGES:
        if partition[src] == partition[dst]:
            internal[partition[src]] += 1
    return round(sum(internal[lab] / m - (degree[lab] / (2 * m)) ** 2 for lab in degree), 10)


def canonicalize(labels):
    order = {}
    for node in sorted(labels):
        order.setdefault(labels[node], len(order))
    return {node: order[label] for node, label in labels.items()}


level0 = {node: node for node in ADJ}
level1 = canonicalize(connected_components(ADJ))
q0, q1 = modularity(level0, ADJ), modularity(level1, ADJ)
print("level 0 (singletons)  communities=%d Q=%s" % (len(set(level0.values())), q0))
print("level 1 (components)  communities=%d Q=%s" % (len(set(level1.values())), q1))
print("q1 == 4/9 :", math.isclose(q1, 4 / 9, abs_tol=1e-9))
```

Output —

```text
level 0 (singletons)  communities=10 Q=-0.1145833333
level 1 (components)  communities=2 Q=0.4444444444
q1 == 4/9 : True
```

`math.isclose(q1, 4 / 9, abs_tol=1e-9)` သည် float နှိုင်းယှဉ်မှုအတွက်
မှန်ကန်သည့် နည်းလမ်းဖြစ်သည် — `q1 == 4/9` သည် `round(..., 10)` ကြောင့်
false ဖြစ်နိုင်သော်လည်း `isclose` က tolerance ဖြင့် စစ်သည်။

| ဆင့် | Community | `Q` | Retrieval granularity |
| --- | --- | --- | --- |
| level 0 | 10 (singleton) | −0.1145833333 | အသုံးမဝင်ပါ (trivial) |
| level 1 | 2 (components) | 0.4444444444 (= 4/9) | entity-specific global question |
| level 2 | 2 (refinement) | 0.4444444444 | ဤ fixture တွင် level 1 နှင့် တူ |

---

## 7. Code တစ်ခုလုံး — Run လုပ်နိုင်သော Version

```python
# end-to-end: exercise_6
import math
from collections import defaultdict, deque

NODES = {
    "co:neo4j": ("Company", "Neo4j", ("Neo4j Inc", "Neo4j, Inc."), "Graph database vendor."),
    "prod:aura": ("Product", "AuraDB", ("Neo4j AuraDB", "Aura"), "Managed cloud graph database service."),
    "tech:cypher": ("Technology", "Cypher", ("openCypher", "Cypher Query Language"), "Declarative graph query language."),
    "tech:louvain": ("Technology", "Louvain", ("Louvain method",), "Greedy modularity optimisation for community detection."),
    "org:cnrs": ("Organization", "CNRS", (), "Research organisation of the Louvain authors."),
    "person:eifrem": ("Person", "Vincent Blondel", ("Blondel",), "Lead author of the Louvain method."),
    "tech:graphrag": ("Technology", "GraphRAG", ("Graph RAG", "Microsoft GraphRAG"), "Retrieval pattern grounded in a knowledge graph."),
    "tech:vectorindex": ("Technology", "Vector Index", ("vector search index", "HNSW index"), "Approximate nearest neighbour index over embeddings."),
    "org:neo4jeng": ("Team", "Neo4j Engineering", (), "Engineering team maintaining Cypher."),
    "paper:louvain": ("Paper", "Fast unfolding of communities in large networks", (), "The 2008 Louvain method paper."),
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


def connected_components(adj):
    labels, seen = {}, set()
    for start in sorted(adj):
        if start in seen:
            continue
        comp = {start}
        queue = deque([start])
        while queue:
            for nb in sorted(adj[queue.popleft()]):
                if nb not in comp:
                    comp.add(nb)
                    queue.append(nb)
        seen |= comp
        for node in comp:
            labels[node] = start
    return labels


def modularity(partition, adj):
    m = len(EDGES)
    internal, degree = defaultdict(int), defaultdict(int)
    for node in adj:
        degree[partition[node]] += len(adj[node])
    for src, _rel, dst, _chunk in EDGES:
        if partition[src] == partition[dst]:
            internal[partition[src]] += 1
    return round(sum(internal[lab] / m - (degree[lab] / (2 * m)) ** 2 for lab in degree), 10)


def greedy_modularity_partition(adj, init_labels):
    labels = dict(init_labels)
    improved = True
    while improved:
        improved = False
        for node in sorted(adj):
            base = modularity(labels, adj)
            best_label, best_gain = labels[node], 1e-12
            for cand in sorted({labels[nb] for nb in adj[node]} - {labels[node]}):
                trial = dict(labels)
                trial[node] = cand
                gain = modularity(trial, adj) - base
                if gain > best_gain:
                    best_gain, best_label = gain, cand
            if best_label != labels[node]:
                labels[node] = best_label
                improved = True
    return labels


def canonicalize(labels):
    order = {}
    for node in sorted(labels):
        order.setdefault(labels[node], len(order))
    return {node: order[label] for node, label in labels.items()}


def community_summaries(labels):
    groups = defaultdict(list)
    for node, label in sorted(labels.items()):
        groups[label].append(node)
    return [(label, members, "Community %d covers: %s" % (
        label, ", ".join(sorted(NODES[m][1] for m in members))))
        for label, members in sorted(groups.items())]


level0 = {node: node for node in ADJ}
level1 = canonicalize(connected_components(ADJ))
level2 = canonicalize(greedy_modularity_partition(ADJ, connected_components(ADJ)))
q0, q1, q2 = (modularity(p, ADJ) for p in (level0, level1, level2))
print(f"level 0 (singletons)  communities={len(set(level0.values()))} Q={q0}")
print(f"level 1 (components)  communities={len(set(level1.values()))} Q={q1}")
print(f"level 2 (refinement)  communities={len(set(level2.values()))} Q={q2}")
for _label, members, summary in community_summaries(level2):
    print(f"  {summary}\n    members={members}")

assert set(level1.values()) == {0, 1}
group_a = {n for n, c in level1.items() if c == 0}
assert group_a == {"co:neo4j", "prod:aura", "tech:cypher", "org:neo4jeng",
                   "tech:graphrag", "tech:vectorindex"}
assert math.isclose(q1, 4 / 9, abs_tol=1e-9)
assert q2 >= q1 - 1e-12
print("[ok] hierarchical partition built; refinement never lowers modularity")
```

Output —

```text
level 0 (singletons)  communities=10 Q=-0.1145833333
level 1 (components)  communities=2 Q=0.4444444444
level 2 (refinement)  communities=2 Q=0.4444444444
  Community 0 covers: AuraDB, Cypher, GraphRAG, Neo4j, Neo4j Engineering, Vector Index
    members=['co:neo4j', 'org:neo4jeng', 'prod:aura', 'tech:cypher', 'tech:graphrag', 'tech:vectorindex']
  Community 1 covers: CNRS, Fast unfolding of communities in large networks, Louvain, Vincent Blondel
    members=['org:cnrs', 'paper:louvain', 'person:eifrem', 'tech:louvain']
[ok] hierarchical partition built; refinement never lowers modularity
```

`{n for n, c in level1.items() if c == 0}` သည် **set comprehension** ဖြစ်သည် —
community 0 ထဲက node များ။ `assert group_a == {…}` သည် set နှိုင်းယှဉ်မှု ဖြစ်သဖြင့်
အစီအစဉ် အရေးမကြီးပါ။

---

## 8. ကိုယ်တိုင်လေ့ကျင့်ကြည့်ပါ

**မေးခွန်း** — အောက်ပါ code က ဘယ်ရလဒ် ပြန်ပေးမလဲ။

```python
def canonicalize(labels):
    order = {}
    for node in sorted(labels):
        order.setdefault(labels[node], len(order))
    return {node: order[label] for node, label in labels.items()}


labels = {"b": "z", "a": "y", "c": "z"}
print(sorted(canonicalize(labels).items()))
```

1. `[('a', 0), ('b', 1), ('c', 0)]`
2. `[('a', 0), ('b', 1), ('c', 1)]`
3. `[('a', 1), ('b', 0), ('c', 0)]`
4. `[('a', 0), ('b', 1), ('c', 2)]`

<details>
<summary>အဖြေ ကြည့်ရန်</summary>

**အဖြေ — 2. `[('a', 0), ('b', 1), ('c', 1)]`**

အကြောင်းရင်း — `sorted(labels)` သည် `['a', 'b', 'c']` ဖြစ်သည်။
- `a` အတွက် `order.setdefault("y", 0)` → `y → 0`
- `b` အတွက် `order.setdefault("z", 1)` → `z → 1` (`len(order)` သည် အခု `1` ဖြစ်သည်)
- `c` အတွက် `order.setdefault("z", 2)` → `"z"` **ရှိပြီးသား** ဖြစ်သဖြင့် `1` ပြန်သည်

ထို့ကြောင့် `c → 1` ဖြစ်သည် (`c` နှင့် `b` သည် label `z` တူညီသည် —
တူညီသည့် community ဖြစ်သဖြင့် ဂဏန်းလည် တူရမည်)။ ရွေးချယ်စရာ 1 (`'c': 0`)
သည် မှားသည် — `c` ၏ label `z` သည် `y` နှင့် မတူသဖြင့် `0` မဖြစ်နိုင်ပါ။
ရွေးချယ်စရာ 3 သည် နံပါတ်တပ်ခြင်းအစဉ်ကို မှားထားသည် (`sorted(labels)` ကို
သုံးသဖြင့် `a` က အရင် `0` ရသည်)။ ရွေးချယ်စရာ 4 သည် `c` ကို label အသစ်
လိုသဘောထားသည် — `"z"` ရှိပြီးသားဖြစ်သဖြင့် မဖြစ်နိုင်ပါ။
`print(sorted(...items()))` ကို သုံးခြင်းသည် dict ၏ ပြသအစီအစဉ်ကို ဖယ်ရှားသဖြင့်
ရလဒ်ကို run တိုင်း တူညီစွာ နှိုင်းယှဉ်နိုင်သည်။

</details>

---

**အဓိက မှတ်ထားရန်** — Hierarchy ၃ ဆင့်သည် retrieval granularity ၃ မျိုးကို
ပေးသည်။ Level 0 (`Q` အနုတ်၊ `−0.1145833333`) သည် trivial ဖြစ်ပြီး တန်ဖိုး
မရှိပါ — **community အရေအတွက် များလျှင် ကောင်းသည်ဟု မဆိုနိုင်ပါ**။ Level 1
(`Q = 4/9 = 0.4444444444`) သည် parameter မလိုသော ဈေးသက်သာ partition ဖြစ်သည်။
Level 2 ၏ greedy refinement သည် ရွှေ့မှု တိုင်းကို `Q` တက်မှသာ လက်ခံသောကြောင့်
level 1 ထက် `Q` လျော့နိုင်မည် မဟုတ်ပါ — ဤ fixture တွင် edge နှစ်ခုကြား လုံးဝ
မရှိသဖြင့် ရွှေ့မှု မရှိဘဲ `Q` တူညီကျန်သည်။ Modularity တွက်ချက်မှုတွင် degree
ကို `len(adj[node])` ဖြင့် ရယူသည်၊ ထို့ကြောင့် `adj` သည် **undirected** graph
ကို ကိုယ်စားပြုရမည်၊ ထို့အပြင် `partition` သည် node အားလုံးကို ဖုံးရမည် —
မဖုံးလျှင် `KeyError` ဖြစ်သည်။ Community label တပ်ခြင်းသည် iteration order ပေါ်
မှီခိုသဖြင့် `canonicalize()` ဖြင့် output ကို တည်ငြိမ်စေရမည်။ Community
summary တိုင်းသည် global question အတွက် retrieval unit ဖြစ်လာသည်။
