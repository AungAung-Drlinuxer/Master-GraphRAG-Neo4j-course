# Walkthrough 04 — Hybrid Retrieval Fusion (Exercise 4)

> ဤဖိုင်သည် Module 07 ၏ `solution.md` ထဲက Exercise 4 ကို **Python အခြေခံမှ စ၍**
> အပိုင်းလိုက် ရှင်းပြသည့် walkthrough ဖြစ်သည်။ Format သည် Module 01 ၏
> `walkthroughs/01_regex_ner.md` နှင့် `walkthroughs/03_gazetteer_lookup.md` နှင့်
> တူညီသည်။

---

## 0. ဤ Exercise က ဘာကို ဖြေရှင်းပေးသလဲ။

Exercise 2-3 သည် **graph** ဘက်မှ ရလဒ် ပေးသည်။ သို့သော် vector search ကလည်
သက်ဆိုင်သည့် chunk များကို ပေးနိုင်သည်။ နှစ်ခုလုံးကို ပေါင်းလျှင် အကောင်းဆုံး
ရလဒ် ရနိုင်သည် — ဤအလုပ်ကို **hybrid retrieval** ဟု ခေါ်သည်။ ပြဿနာမှာ
ranking နှစ်ခုကို **ဘယ်လို ပေါင်းမလဲ** ဆိုသည့် အချက် ဖြစ်သည်။

```text
vector ranking      graph ranking
  1. vec:c1            1. graph:0
  2. vec:c4            2. graph:4
  3. vec:c2            3. graph:6
        |                    |
        +----- RRF fuse ------+
                 |
     fused: graph:0, vec:c1, graph:4, vec:c4, graph:6, vec:c2
                 |
     provenance dedup (chunk တူညီသည့် item ဖယ်)
                 |
     final: graph:0, graph:4, vec:c4, graph:6
```

**Reciprocal Rank Fusion (RRF)** သည် ဤပြဿနာအတွက် အသုံးအများဆုံး နည်းလမ်း
ဖြစ်သည်။ Score တန်ဖိုး နှစ်ခုကို **normalize မလုပ်ဘဲ** rank ကိုသာ ယုံသည် —

```text
score(item) = Σ_lists  1 / (k + rank)      (rank သည် 1 မှ စသည်၊ k = 60)
```

ဤအချက်သည် အဘယ်ကြောင့် အရေးကြီးသနည်း — vector search ၏ cosine similarity သည်
`0.0 – 1.0` အတွင်း ဖြစ်ပြီး graph relevance score သည် မတူညီသည့် scale ဖြစ်နိုင်သည်။
RRF သည် rank ကိုသာ သုံးသဖြင့် scale ကွာခြားမှုကို လုံးဝ ကျော်လွှားသည်။

ဤ exercise တွင် **vector ranking နှင့် graph ranking နှစ်ခုလုံးသည် scripted
fixture ဖြစ်သည်** — တကယ့် embedding search နှင့် တကယ့် graph score မဟုတ်ပါ။
ဤ module ၏ lab သည် retrieval ကို in-memory ဖြင့် simulate လုပ်သည်။ Fusion
algorithm နှင့် dedup logic မှာမူ တကယ့် production code နှင့် တူညီသည်။

ဤ code မှာ လေ့လာရမည့် Python concepts များမှာ —

- `enumerate(iterable, start=1)`
- `dict.values()` ဖြင့် လှမ်းခြင်း
- `collections.defaultdict(float)`
- `+=` ဖြင့် dict value စုခြင်း
- `sorted(..., key=lambda kv: (-kv[1], kv[0]))` — descending + tie-break
- String slicing (`item[4:]`) နှင့် `str.startswith()`
- `int(str)` ဖြင့် စာသား → ဂဏန်း
- Tuple ကို `(item, score)` အဖြစ် သိမ်းခြင်း
- Guideline ကဲ့သို့ `prev is None or ...` chain (short-circuit)

---

## 1. `rankings` — Ranking နှစ်ခု

```python
rankings = {"vector": ["vec:c1", "vec:c4", "vec:c2"],
            "graph": ["graph:0", "graph:4", "graph:6"]}
```

`rankings` သည် dict ဖြစ်သည် — key သည် modality အမည် (`"vector"`၊ `"graph"`)၊
value သည် **item id များ၏ list** (ranking) ဖြစ်သည်။ List ၏ အစီအစဉ်သည်
အရေးကြီးသည် — index 0 သည် အကောင်းဆုံး၊ နောက်ဆုံး index သည် အနိမ့်ဆုံး။

Item id ၏ format ကို သတိထားပါ —

| Prefix | ဥပမာ | အဓိပ္ပာယ် |
| --- | --- | --- |
| `vec:` | `vec:c1` | chunk id `c1` မှ ရလာသည့် vector hit |
| `graph:` | `graph:0` | `EDGES[0]` မှ ရလာသည့် graph triple |

Prefix မတူသဖြင့် item နှစ်ခုကို တစ်ခုတည်းအဖြစ် အမှားမှတ်မိခြင်းမှ ကာကွယ်သည် —
သို့သော် **provenance chunk** ကမူ တူနိုင်သည် (Section 3)။

`enumerate(items, start=1)` ကို တကယ် ကြည့်ပါ။

```python
rankings = {"vector": ["vec:c1", "vec:c4", "vec:c2"],
            "graph": ["graph:0", "graph:4", "graph:6"]}
for items in rankings.values():
    for rank, item in enumerate(items, start=1):
        print(rank, item)
```

Output —

```text
1 vec:c1
2 vec:c4
3 vec:c2
1 graph:0
2 graph:4
3 graph:6
```

### 1.1 `rankings.values()`

`dict.values()` သည် value များကို ပေးသည် — ဤနေရာတွင် list နှစ်ခု။ Key များ
(`"vector"`၊ `"graph"`) ကို မလိုသဖြင့် `.values()` ကို သုံးသည်။ Key များကို
မလိုဘဲ iterate လုပ်လျှင် `.items()` ကို သုံးရမည်။

### 1.2 `enumerate(items, start=1)`

`enumerate(items)` သည် `(0, item)`၊ `(1, item)` စသည် ပေးသည်။ `start=1` ထည့်လျှင်
`1` မှ စသည်။ **rank သည် 1 မှ စရမည်** — အကြောင်းရင်းမှာ formula `1 / (k + rank)`
တွင် `rank = 0` ဖြစ်လျှင် denominator သည် `k` သာဖြစ်ပြီး ပထမ item က ပိုများသည့်
score ရမည်; တကယ့် RRF သတ်မှတ်ချက်တွင် rank သည် 1-based ဖြစ်သည်။

---

## 2. `reciprocal_rank_fusion()` — Score စုခြင်း

```python
from collections import defaultdict


def reciprocal_rank_fusion(rankings, k=60):
    """RRF: score(item) = sum over lists of 1 / (k + rank). Tie-break by id asc."""
    scores = defaultdict(float)
    for items in rankings.values():
        for rank, item in enumerate(items, start=1):
            scores[item] += 1.0 / (k + rank)
    return sorted(scores.items(), key=lambda kv: (-kv[1], kv[0]))
```

### 2.1 `collections.defaultdict(float)`

`defaultdict(float)` သည် dict တစ်ခုဖြစ်ပြီး key **မရှိသေးလျှင်** default
တန်ဖိုးကို **အလိုအလျောက်** ဖန်တီးပေးသည်။ `float()` ကို ခေါ်လျှင် `0.0` ရသည်။
ထို့ကြောင့် `scores["graph:0"] += 1.0 / 61` ရေးလို့ရသည် — သာမန် dict ဆိုလျှင်
`KeyError` ဖြစ်မည်။

```python
from collections import defaultdict

scores = defaultdict(float)
print(scores["graph:0"])
scores["graph:0"] += 1 / 61
print(scores["graph:0"])
```

Output —

```text
0.0
0.01639344262295082
```

ပထမ print သည် `0.0` ကို ပြသည် — ထို key ကို ရှာလိုက်ရုံဖြင့် dict ထဲ
**ထည့်လိုက်သည်** ဆိုသည့် side effect ကို သတိထားပါ။ ဤနေရာတွင် ထို side effect
သည် လိုချင်သည့် အပြုအမူ ဖြစ်သည်။

### 2.2 `scores[item] += 1.0 / (k + rank)` — Formula

`+=` သည် `scores[item] = scores[item] + 1.0 / (k + rank)` ၏ အတိုကောက် ဖြစ်သည်။
Item တစ်ခုသည် ranking တစ်ခုထက် ပိုတွင် ပါလျှင် (ဥပမာ vector ရော graph ရော)
score များ **စုပေါင်း** ခံရသည် — ဤအချက်သည် RRF ၏ အဓိကအချက် ဖြစ်သည်။

`k = 60` သည် **smoothing constant** ဖြစ်သည်။ တန်ဖိုးအတိအကျကို တွက်ကြည့်ပါ။

```python
k = 60
for rank in (1, 2, 3):
    print("rank %d -> 1/(k+rank) = 1/%d = %r" % (rank, k + rank, 1.0 / (k + rank)))
```

Output —

```text
rank 1 -> 1/(k+rank) = 1/61 = 0.01639344262295082
rank 2 -> 1/(k+rank) = 1/62 = 0.016129032258064516
rank 3 -> 1/(k+rank) = 1/63 = 0.015873015873015872
```

| Formula အပိုင်း | တန်ဖိုး | အဓိပ္ပာယ် |
| --- | --- | --- |
| `k` | 60 | smoothing — rank တစ်ခုချင်း၏ ကွာခြားမှုကို လျှော့သည် |
| `1/61` | 0.016393 | rank 1 |
| `1/62` | 0.016129 | rank 2 |
| `1/63` | 0.015873 | rank 3 |

`k` ကြီးလျှင် rank များကြား ကွာခြားမှု သေးငယ်လာသည် — ထို့ကြောင့် `k` သည်
"ranking များစွာတွင် အနိမ့် rank ပါသည့် item ကို မည်မျှ အလေးထားမလဲ" ကို
ထိန်းသည်။ `k = 60` သည် literature တွင် ပုံမှန် default ဖြစ်သည်။

### 2.3 `sorted(scores.items(), key=...)`

`scores.items()` သည် `(item, score)` tuple များကို ပေးသည်။ `sorted()` ကို
dict ပေါ် တိုက်ရိုက် ခေါ်လျှင် key များသာ ရမည် — ထို့ကြောင့် `.items()` လိုသည်။
`key=lambda kv: (-kv[1], kv[0])` သည် score ကို descending၊ tie ဖြစ်လျှင် item id
အက္ခရာအစီအစဉ် ဖြင့် ဖြတ်သည် (Exercise 1 ၏ နည်းလမ်းနှင့် တူညီသည်)။

---

## 3. `provenance_chunk()` — Item မှ Source Chunk သို့

```python
def provenance_chunk(item):
    return item[4:] if item.startswith("vec:") else EDGES[int(item[6:])][3]
```

Item id နှစ်မျိုးအတွက် provenance ကို နည်းလမ်းနှစ်မျိုးဖြင့် ရှာသည်။

| Item format | ရှာသည့်နည်း | အဓိပ္ပာယ် |
| --- | --- | --- |
| `vec:cN` | `item[4:]` | prefix ၄ လုံး (`vec:`) ဖယ်လိုက်ရုံ |
| `graph:i` | `EDGES[int(item[6:])][3]` | prefix ၆ လုံး (`graph:`) ဖယ် → index → edge ၏ element ၄ |

`item[4:]` သည် **slicing** ဖြစ်သည် — index 4 မှ အဆုံးအထိ။ `"vec:c1"[4:]` → `"c1"`။
`item.startswith("vec:")` သည် prefix ကို စစ်သည်။ Conditional expression
(`X if cond else Y`) ဖြင့် နှစ်မျိုးကို တစ်လိုင်းတည်း ခွဲသည်။

```python
EDGES = (
    ("co:neo4j", "DEVELOPS", "prod:aura", "c1"),
    ("prod:aura", "USES", "tech:vectorindex", "c1"),
)
print("vec:c1"[4:])
print(int("graph:0"[6:]))
print(EDGES[int("graph:1"[6:])])
print(EDGES[int("graph:1"[6:])][3])
```

Output —

```text
c1
0
('prod:aura', 'USES', 'tech:vectorindex', 'c1')
c1
```

`int("0")` သည် စာသားကို ဂဏန်းအဖြစ် ပြောင်းသည်။ `EDGES[0]` သည် tuple ဖြစ်ပြီး
`[3]` ဖြင့် provenance chunk ကို ယူသည်။ **`graph:i` ၏ provenance သည်
`EDGES[i][3]` ဖြစ်သည်** — ဤအချက်သည် exercise hint တွင် တိကျစွာ ဖော်ပြထားသည်။

---

## 4. `dedupe_by_provenance()` — Chunk တစ်ခုလျှင် Item တစ်ခု

```python
def dedupe_by_provenance(fused):
    """Keep one item per source chunk; on an equal score the graph triple wins."""
    best = {}
    for item, score in fused:
        chunk = provenance_chunk(item)
        prev = best.get(chunk)
        if prev is None or score > prev[1] or (score == prev[1] and item.startswith("graph:")):
            best[chunk] = (item, score)
    keep = {v[0] for v in best.values()}
    return [item for item, _ in fused if item in keep]
```

### 4.1 `best` — chunk → (item, score)

`best` သည် dict ဖြစ်ပြီး key သည် chunk id၊ value သည် ထို chunk ကို ကိုယ်စားပြု
မည့် `(item, score)` tuple ဖြစ်သည်။ `fused` သည် score မြင့်သည့်အစီအစဉ်
ဖြစ်သဖြင့် **ပထမဆုံး တွေ့သည့် item** သည် ထို chunk ၏ score မြင့်ဆုံး item ဖြစ်သည်။

### 4.2 Condition သုံးပိုင်း (short-circuit)

```python
if prev is None or score > prev[1] or (score == prev[1] and item.startswith("graph:")):
```

| အစဉ် | Condition | အဓိပ္ပာယ် |
| --- | --- | --- |
| 1 | `prev is None` | ဤ chunk ကို ပထမဆုံး တွေ့သည် |
| 2 | `score > prev[1]` | ယခု item ၏ score ပိုမြင့်သည် |
| 3 | `score == prev[1] and item.startswith("graph:")` | score တူညီပြီး ယခု item က graph triple |

Python သည် `or` ကွင်းဆက်တွင် condition တစ်ခု `True` ဖြစ်လျှင် ကျန်တာကို
မစစ်တော့ပါ — **short-circuit evaluation**။ Condition ၃ တွင် `score == prev[1]`
ကို အရင်စစ်ထားသဖြင့် `item.startswith("graph:")` ကို လိုအပ်မှသာ စစ်သည်။

**Score တူညီလျှင် graph triple ကို ဦးစားပေးခြင်း၏ အကြောင်းရင်း** — vector hit
သည် chunk စာသားအပြည့် (ဥပမာ ၄၄ လုံးဆ) ကို ကိုယ်စားပြုပြီး graph triple သည်
normalized triple တစ်ခု (`prod:aura -[USES]-> tech:vectorindex`) ဖြစ်သည်။
Triple သည် တိုတောင်းပြီး structured ဖြစ်သဖြင့် context window ကို သက်သာစွာ
သုံးနိုင်သည်။

### 4.3 `keep` set နှင့် final list

```python
keep = {v[0] for v in best.values()}
return [item for item, _ in fused if item in keep]
```

`{v[0] for v in best.values()}` သည် **set comprehension** ဖြစ်သည် — best ထဲက
item များကို set အဖြစ် စုသည်။ ထို့နောက် `fused` ၏ အစီအစဉ်အတိုင်း လှမ်းပြီး
`keep` ထဲ ပါသည့် item များကိုသာ ပြန်ပေးသည် — ထို့ကြောင့် **final ၏ အစီအစဉ်သည်
fused ၏ အစီအစဉ် ဖြစ်သည်** (`best` ထဲက အစီအစဉ် မဟုတ်)။ List comprehension
တွင် `for item, _ in fused` သည် tuple unpacking ဖြစ်သည် — score ကို မလိုသဖြင့်
`_` ဖြင့် လက်ခံသည်။

---

## 5. Run အပြည့်အစုံ

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
CHUNKS = {
    "c1": "Neo4j AuraDB is a managed cloud service that uses a vector index for retrieval.",
    "c2": "Cypher is the declarative query language created by Neo4j and maintained by its team.",
    "c3": "GraphRAG grounds generation in knowledge graph triples extracted from source text.",
    "c4": "The Louvain method optimises modularity to detect communities in large networks.",
    "c5": "Vector search returns approximate nearest neighbours from an embedding index.",
}


def reciprocal_rank_fusion(rankings, k=60):
    scores = defaultdict(float)
    for items in rankings.values():
        for rank, item in enumerate(items, start=1):
            scores[item] += 1.0 / (k + rank)
    return sorted(scores.items(), key=lambda kv: (-kv[1], kv[0]))


def provenance_chunk(item):
    return item[4:] if item.startswith("vec:") else EDGES[int(item[6:])][3]


def dedupe_by_provenance(fused):
    best = {}
    for item, score in fused:
        chunk = provenance_chunk(item)
        prev = best.get(chunk)
        if prev is None or score > prev[1] or (score == prev[1] and item.startswith("graph:")):
            best[chunk] = (item, score)
    keep = {v[0] for v in best.values()}
    return [item for item, _ in fused if item in keep]


fused = reciprocal_rank_fusion({"vector": ["vec:c1", "vec:c4", "vec:c2"],
                                "graph": ["graph:0", "graph:4", "graph:6"]})
for item, score in fused:
    chunk = provenance_chunk(item)
    print("  %-10s rrf=%.6f  chunk=%s  %s" % (item, score, chunk, CHUNKS[chunk][:44]))
final = dedupe_by_provenance(fused)
print(f"fused={[i for i, _ in fused]}")
print(f"final={final}")
```

Output —

```text
  graph:0    rrf=0.016393  chunk=c1  Neo4j AuraDB is a managed cloud service that
  vec:c1     rrf=0.016393  chunk=c1  Neo4j AuraDB is a managed cloud service that
  graph:4    rrf=0.016129  chunk=c2  Cypher is the declarative query language cre
  vec:c4     rrf=0.016129  chunk=c4  The Louvain method optimises modularity to d
  graph:6    rrf=0.015873  chunk=c3  GraphRAG grounds generation in knowledge gra
  vec:c2     rrf=0.015873  chunk=c2  Cypher is the declarative query language cre
fused=['graph:0', 'vec:c1', 'graph:4', 'vec:c4', 'graph:6', 'vec:c2']
final=['graph:0', 'graph:4', 'vec:c4', 'graph:6']
```

### 5.1 ရလဒ်ကို ဖတ်ခြင်း

- `graph:0` နှင့် `vec:c1` သည် score **တူညီသည်** (`0.016393`)။ Sort key က
  `(-score, item_id)` ဖြစ်သဖြင့် `graph:0` က အရင်လာသည် (`g < v`)။
- `graph:0` နှင့် `vec:c1` **နှစ်ခုလုံး** chunk `c1` မှ ဆင်းသက်သည် — ဤအချက်ကို
  ဇယားတွင် တွေ့နိုင်သည်။
- `final` တွင် `vec:c1` နှင့် `vec:c2` မပါတော့ပါ — ၆ ခုမှ ၄ ခုသို့ လျော့သည်။

### 5.2 Dedup ဆုံးဖြတ်ချက် ဇယား

ဤဇယားသည် `dedupe_by_provenance()` ၏ loop တစ်ခုစီကို တကယ့် run မှ
တန်ဖိုးများဖြင့် ဖော်ပြသည်။

```python
fused = [("graph:0", 0.01639344262295082), ("vec:c1", 0.01639344262295082),
         ("graph:4", 0.016129032258064516), ("vec:c4", 0.016129032258064516),
         ("graph:6", 0.015873015873015872), ("vec:c2", 0.015873015873015872)]
provenance = {"graph:0": "c1", "vec:c1": "c1", "graph:4": "c2", "vec:c4": "c4",
              "graph:6": "c3", "vec:c2": "c2"}
best = {}
for item, score in fused:
    chunk = provenance[item]
    prev = best.get(chunk)
    take = prev is None or score > prev[1] or (score == prev[1] and item.startswith("graph:"))
    print("item=%-10s chunk=%s prev=%-52s take=%s" % (item, chunk, prev, take))
    if take:
        best[chunk] = (item, score)
print("best =", best)
```

Output —

```text
item=graph:0    chunk=c1 prev=None                                                 take=True
item=vec:c1     chunk=c1 prev=('graph:0', 0.01639344262295082)                     take=False
item=graph:4    chunk=c2 prev=None                                                 take=True
item=vec:c4     chunk=c4 prev=None                                                 take=True
item=graph:6    chunk=c3 prev=None                                                 take=True
item=vec:c2     chunk=c2 prev=('graph:4', 0.016129032258064516)                    take=False
best = {'c1': ('graph:0', 0.01639344262295082), 'c2': ('graph:4', 0.016129032258064516), 'c4': ('vec:c4', 0.016129032258064516), 'c3': ('graph:6', 0.015873015873015872)}
```

| အစဉ် | Item | Chunk | `prev` | `take` | အကြောင်းရင်း |
| --- | --- | --- | --- | --- | --- |
| 1 | `graph:0` | `c1` | `None` | True | chunk အသစ် |
| 2 | `vec:c1` | `c1` | `('graph:0', …)` | False | score တူ (graph က ရှိပြီး) |
| 3 | `graph:4` | `c2` | `None` | True | chunk အသစ် |
| 4 | `vec:c4` | `c4` | `None` | True | chunk အသစ် |
| 5 | `graph:6` | `c3` | `None` | True | chunk အသစ် |
| 6 | `vec:c2` | `c2` | `('graph:4', …)` | False | score တူ (graph က ရှိပြီး) |

`vec:c1` နှင့် `vec:c2` သည် ဖယ်ခံရသည်ကို ဤဇယားက ရှင်းရှင်းလင်းလင်း ပြသည်။
Chunk `c1` အတွက် `graph:0` က ဦးစားပေးခံရပြီး chunk `c2` အတွက် `graph:4` က
ဦးစားပေးခံရသည် — နှစ်ခုလုံးတွင် score တူညီသည့်အတွက် graph triple က အနိုင်ရသည်။
`vec:c4` မှာမူ chunk `c4` တွင် တစ်ခုတည်း ဖြစ်သဖြင့် ကျန်သည်။

---

## 6. Tie-Break ကို တိုက်ရိုက် စမ်းခြင်း

Score တူညီသည့်အခါ graph triple က အနိုင်ရသည်ကို **graph နှင့် vector ကို
အစီအစဉ် လှန်ကြည့်**ဖြင့် စစ်နိုင်သည်။

```python
from collections import defaultdict


def reciprocal_rank_fusion(rankings, k=60):
    scores = defaultdict(float)
    for items in rankings.values():
        for rank, item in enumerate(items, start=1):
            scores[item] += 1.0 / (k + rank)
    return sorted(scores.items(), key=lambda kv: (-kv[1], kv[0]))


fused = reciprocal_rank_fusion({"vector": ["vec:c5", "vec:c1"], "graph": ["graph:0"]})
print(fused)
```

Output —

```text
[('graph:0', 0.01639344262295082), ('vec:c5', 0.01639344262295082), ('vec:c1', 0.016129032258064516)]
```

`graph:0` နှင့် `vec:c5` သည် **နှစ်ခုလုံး rank 1** ဖြစ်သဖြင့် score တူညီသည်
(`0.016393`)။ Sort key ၏ ဒုတိယအပိုင်း (`kv[0]`) က `graph:0` ကို အရင်ထားသည်။
Dedup လုပ်လျှင် chunk နှစ်ခု ကွဲပြားသဖြင့် (`c5` နှင့် `c1`) နှစ်ခုလုံး ကျန်မည်။
ဤအချက်ကြောင့် **score တူညီသည့်အခါ graph triple ကို ဦးစားပေး** ဆိုသည့်
စည်းမျဉ်းသည် dedup stage တွင်သာ အလုပ်လုပ်သည် — fusion stage တွင် item id ၏
အက္ခရာအစီအစဉ်သာ အလုပ်လုပ်သည်။

---

## 7. Code တစ်ခုလုံး — Run လုပ်နိုင်သော Version

```python
# end-to-end: exercise_4
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
CHUNKS = {
    "c1": "Neo4j AuraDB is a managed cloud service that uses a vector index for retrieval.",
    "c2": "Cypher is the declarative query language created by Neo4j and maintained by its team.",
    "c3": "GraphRAG grounds generation in knowledge graph triples extracted from source text.",
    "c4": "The Louvain method optimises modularity to detect communities in large networks.",
    "c5": "Vector search returns approximate nearest neighbours from an embedding index.",
}


def reciprocal_rank_fusion(rankings, k=60):
    scores = defaultdict(float)
    for items in rankings.values():
        for rank, item in enumerate(items, start=1):
            scores[item] += 1.0 / (k + rank)
    return sorted(scores.items(), key=lambda kv: (-kv[1], kv[0]))


def provenance_chunk(item):
    return item[4:] if item.startswith("vec:") else EDGES[int(item[6:])][3]


def dedupe_by_provenance(fused):
    best = {}
    for item, score in fused:
        chunk = provenance_chunk(item)
        prev = best.get(chunk)
        if prev is None or score > prev[1] or (score == prev[1] and item.startswith("graph:")):
            best[chunk] = (item, score)
    keep = {v[0] for v in best.values()}
    return [item for item, _ in fused if item in keep]


fused = reciprocal_rank_fusion({"vector": ["vec:c1", "vec:c4", "vec:c2"],
                                "graph": ["graph:0", "graph:4", "graph:6"]})
for item, score in fused:
    chunk = provenance_chunk(item)
    print("  %-10s rrf=%.6f  chunk=%s  %s" % (item, score, chunk, CHUNKS[chunk][:44]))
final = dedupe_by_provenance(fused)
print(f"fused={[i for i, _ in fused]}")
print(f"final={final}")

assert [i for i, _ in fused] == ["graph:0", "vec:c1", "graph:4", "vec:c4", "graph:6", "vec:c2"]
assert final == ["graph:0", "graph:4", "vec:c4", "graph:6"]
assert len(final) == len(fused) - 2
assert final[0] == "graph:0"
assert len({provenance_chunk(i) for i in final}) == len(final)
print("[ok] RRF merged both rankings, deduplicated by provenance chunk")
```

Output —

```text
  graph:0    rrf=0.016393  chunk=c1  Neo4j AuraDB is a managed cloud service that
  vec:c1     rrf=0.016393  chunk=c1  Neo4j AuraDB is a managed cloud service that
  graph:4    rrf=0.016129  chunk=c2  Cypher is the declarative query language cre
  vec:c4     rrf=0.016129  chunk=c4  The Louvain method optimises modularity to d
  graph:6    rrf=0.015873  chunk=c3  GraphRAG grounds generation in knowledge gra
  vec:c2     rrf=0.015873  chunk=c2  Cypher is the declarative query language cre
fused=['graph:0', 'vec:c1', 'graph:4', 'vec:c4', 'graph:6', 'vec:c2']
final=['graph:0', 'graph:4', 'vec:c4', 'graph:6']
[ok] RRF merged both rankings, deduplicated by provenance chunk
```

`assert len({provenance_chunk(i) for i in final}) == len(final)` သည် "chunk တစ်ခုလျှင်
item တစ်ခု" ဆိုသည့် contract ကို စစ်သည် — set ၏ size နှင့် list ၏ size တူညီရမည်။

---

## 8. ကိုယ်တိုင်လေ့ကျင့်ကြည့်ပါ

**မေးခွန်း** — `provenance_chunk("graph:3")` က ဘယ်တန်ဖိုး ပြန်ပေးမလဲ။

```python
EDGES = (
    ("co:neo4j", "DEVELOPS", "prod:aura", "c1"),
    ("co:neo4j", "CREATES", "tech:cypher", "c2"),
    ("co:neo4j", "EMPLOYS", "org:neo4jeng", "c2"),
    ("prod:aura", "USES", "tech:vectorindex", "c1"),
    ("tech:cypher", "MAINTAINED_BY", "org:neo4jeng", "c2"),
)


def provenance_chunk(item):
    return item[4:] if item.startswith("vec:") else EDGES[int(item[6:])][3]


print(provenance_chunk("graph:3"))
```

1. `"c3"`
2. `"c1"`
3. `"g"`
4. `IndexError` ဖြစ်သည်

<details>
<summary>အဖြေ ကြည့်ရန်</summary>

**အဖြေ — 2. `"c1"`**

အကြောင်းရင်း — `"graph:3"` သည် `"vec:"` ဖြင့် မစသဖြင့် `else` branch ဖြစ်သည်။
`int("graph:3"[6:])` = `int("3")` = `3`။ `EDGES[3]` = `("prod:aura", "USES",
"tech:vectorindex", "c1")`။ `[3]` သည် tuple ၏ **စတုတ္ထ** element ဖြစ်သည့် `"c1"`
ကို ယူသည်။

Index သည် edge အညွှန်း ဖြစ်သည်၊ chunk အမည် မဟုတ်ပါ — ထို့ကြောင့် `graph:3` ၏
provenance သည် `c3` မဟုတ်ဘဲ `c1` ဖြစ်နိုင်သည်။ ဤအချက်က **item id ၏ ဂဏန်းနှင့်
chunk အမည် မတူနိုင်ခြင်း** ကို ပြသည် — dedup ကို chunk ဖြင့် လုပ်ရခြင်း၏
အကြောင်းရင်းလည် ဖြစ်သည်။

</details>

---

**အဓိက မှတ်ထားရန်** — RRF သည် score scale မလိုဘဲ rank ကိုသာ ယုံသည်၊ ထို့ကြောင့်
cosine similarity နှင့် graph relevance score ကို normalize လုပ်စရာ မလိုပါ။
`k = 60` သည် smoothing constant ဖြစ်ပြီး rank များကြား ကွာခြားမှုကို ထိန်းသည်။
`graph:0` နှင့် `vec:c1` သည် chunk `c1` **တစ်ခုတည်း**မှ ဆင်းသက်သည် — တူညီသည့်
အချက်အလက်ကို နှစ်ကြိမ် ပေးပို့ခြင်းသည် context window ကို ဖြုန်းတီးသည်၊
ထို့ကြောင့် **provenance deduplication မဖြစ်မနေ လိုသည်**။ Score တူညီသောအခါ
graph triple ကို ဦးစားပေးသည် — triple သည် normalized ဖြစ်ပြီး chunk ထက်
တိုတောင်းသဖြင့် context ကို သက်သာစွာ သုံးသည်။ `dedupe_by_provenance()` ၏
ရလဒ် အစီအစဉ်သည် `fused` ၏ အစီအစဉ်ကို ထိန်းထားသည်ကို သတိထားပါ။
