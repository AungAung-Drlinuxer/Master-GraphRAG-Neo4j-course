# Walkthrough 04 — Relationship update/delete diff နှင့် orphan cleanup (Exercise 4)

> ဤဖိုင်သည် Module 06 ၏ `solution.md` ထဲက Exercise 4 ကို **Python အခြေခံမှ စ၍**
> အပိုင်းလိုက် ရှင်းပြသည့် walkthrough ဖြစ်သည်။ Diff နှင့် orphan တွက်ချက်မှုအားလုံးသည်
> in-memory simulation မှ ရသည်; Cypher အပိုင်းများမှာ Neo4j ၏ documented semantics ဖြစ်သည်။

---

## 0. ဤ Exercise က ဘာကို ဖြေရှင်းပေးသလဲ။

Corpus ပြောင်းလဲသည့်အခါ LLM ၏ extraction ရလဒ်လည်း ပြောင်းသည်။ Chunk တစ်ခုကို ဖျက်လိုက်
ခြင်း၊ prompt ပြောင်းခြင်း၊ model version တိုးခြင်းကြောင့် **အရင် ထုတ်ခဲ့သည့်
relationship တစ်ခုသည် ယခု မထောက်ပံ့တော့ခြင်း** ဖြစ်နိုင်သည်။ Graph ကို current state
အဖြစ် ထားရှိရန် desired state နှင့် နှိုင်းယှဉ်ပြီး ဖျက်ရမည့်အရာကို ရှာရသည်။

```text
current edge set (graph ထဲ ရှိပြီးသား)   ─┐
                                         ├─ diff ─ → to_add     (ရေးရန်)
desired edge set (ယခု extraction ရလဒ်)  ─┘        → to_delete  (ဖျက်ရန်)
                                                   ↓
                                     relationship ဖျက်ပြီးနောက် degree 0 ဖြစ်သည့် node
                                     = orphan → cleanup လုပ်ရန်
```

ဤ Exercise က `edge_set()`၊ `diff_relationships()`၊ `node_degree()` နှင့်
`orphan_nodes()` ၄ ခုကို တည်ဆောက်ပြီး `DELETE` နှင့် `DETACH DELETE` ၏
ဘေးထွက်သက်ရောက်မှုကို တိုင်းတာသည်။

ဤ code တွင် လေ့လာရမည့် Python concepts များမှာ —

- Set comprehension နှင့် set ၏ hashable လိုအပ်ချက်
- Set difference operator (`-`) နှင့် ၎င်း၏ ဦးတည်ချက်
- Tuple unpacking (အသုံးမလိုသည့် variable အတွက် `_` အမည်)
- `dict.get(key, default)` ဖြင့် counter pattern
- Set union (`|`) နှင့် generator expression
- `sorted()` ဖြင့် ရလဒ်ကို deterministic ဖြစ်စေခြင်း

---
## 1. Set — Edge အစုအဝေးကို ကိုယ်စားပြုခြင်း
`{...}` syntax သည် **set** သို့မဟုတ် **dict** ဖြစ်နိုင်သည်။ `{"a", "b"}` တွင် `:` မပါလျှင်
set ဖြစ်သည်; `{"a": 1}` တွင် key-value ရှိလျှင် dict ဖြစ်သည်။ Set သည် အဖွဲ့ဝင် ထပ်ခြင်းကို
အလိုအလျောက် ဖယ်ပြီး အဖွဲ့ဝင်ရှိမရှိ စစ်ခြင်းကို မြန်စေသည်။
```python
print(type({"a", "b"}))
print(type({"a": 1}))

edges = {("Person", "ada_lovelace", "WORKED_AT", "Organization",
          "analytical_engine_project", "c01"),
         ("Person", "ada_lovelace", "WORKED_AT", "Organization",
          "analytical_engine_project", "c04")}
print(len(edges))
print(("Person", "ada_lovelace", "WORKED_AT", "Organization",
       "analytical_engine_project", "c01") in edges)

try:
    {["Person", "ada_lovelace"]}
except TypeError as exc:
    print("list key ->", type(exc).__name__, exc)
```

Output —
```text
<class 'set'>
<class 'dict'>
2
True
list key -> TypeError cannot use 'list' as a set element (unhashable type: 'list')
```

Tuple နှစ်ခုကို `{}` ထဲ ထည့်ပေမဲ့ `len()` က 2 ပြန်သည်မှာ ၎င်းတို့သည် `chunk_id` ကွာသဖြင့်
မတူညီလို့ဖြစ်သည်။ Set နှင့် dict နှစ်ခုလုံးသည် **hashable** အဖွဲ့ဝင်ကိုသာ လက်ခံသည် —
list ကို key အဖြစ် ထည့်လျှင် `TypeError: unhashable type: 'list'` ဖြစ်သည်။ Tuple သည်
immutable ဖြစ်သဖြင့် ရသည်။ ဤအချက်သည် edge identity ကို ၆-tuple အဖြင်း ကိုယ်စားပြုရခြင်း၏
အကြောင်းရင်း ဖြစ်သည်။

**လိုအပ်သော သတိပေးချက်** — set ၏ ပြသအစီအစဉ်သည် run တစ်ခုနှင့်တစ်ခု **ကွဲနိုင်သည်**
(hash randomisation)။ ထို့ကြောင့် ဤ walkthrough တွင် set ကို print သည့်အခါတိုင်း
`sorted()` ဖြင့် စီပြီးမှ print သည်။ ထိုသို့ မလုပ်လျှင် output သည် run တိုင်း မတူပါ။

---
## 2. `edge_set()` — Set comprehension ဖြင့် Edge စုစည်းခြင်း
```python
return {(ENTITY_TYPE_TO_LABEL[t["head_type"]], slug(t["head"]), t["rel"],
         ENTITY_TYPE_TO_LABEL[t["tail_type"]], slug(t["tail"]), t["chunk_id"])
        for t in triples}
```

ဤသည်မှာ **set comprehension** ဖြစ်သည် — list comprehension နှင့် တူညီသော်လည်း
`{}` ဖြင့် ရေးသည်။ Triple တိုင်းသည် tuple ၆ ခုပါသည့် edge identity အဖြစ် ပြောင်းသွားသည်။
```python
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

def edge_set(triples):
    return {(ENTITY_TYPE_TO_LABEL[t["head_type"]], slug(t["head"]), t["rel"],
             ENTITY_TYPE_TO_LABEL[t["tail_type"]], slug(t["tail"]), t["chunk_id"])
            for t in triples}


current = edge_set(TRIPLES)
print("edge count :", len(current))
for e in sorted(current):
    print("  %-12s %-26s %-18s %-12s %-26s %s"
          % (e[0], e[1], e[2], e[3], e[4], e[5]))
```

Output —
```text
edge count : 6
  Organization analytical_engine_project  LOCATED_IN         Location     london                     c03
  Person       ada_lovelace               COLLABORATED_WITH  Person       charles_babbage            c02
  Person       ada_lovelace               USES               Technology   analytical_engine          c01
  Person       ada_lovelace               WORKED_AT          Organization analytical_engine_project  c01
  Person       ada_lovelace               WORKED_AT          Organization analytical_engine_project  c04
  Person       charles_babbage            FOUNDED            Organization analytical_engine_project  c02
```

Triple ၆ ခုမှ edge identity ၆ ခု ရသည် (`t1` နှင့် `t6` သည် `chunk_id` ကွာသဖြင့် မပေါင်းပါ)။
Identity ထဲတွင် label များပါသဖြင့် (label, id, rel, label, id, chunk) အမည်တူ node
နှစ်ခုကို ခွဲထားနိုင်သည်။

`chunk_id` ကို identity ထဲ မထည့်လျှင် ဤ set သည် အဖွဲ့ဝင် ၅ ခုသာ ရမည် — `t1` နှင့်
`t6` ပေါင်းသွားမည်။ ထို့နောက် diff က "edge တစ်ခု ပျောက်သွားသည်" ဟု မှားယွင်းသော
ဆုံးဖြတ်ချက် ပေးနိုင်သည်။

---
## 3. Set Difference (`-`) ဖြင့် Diff တွက်ခြင်း
`A - B` သည် A ထဲ ရှိပြီး B ထဲ မရှိသည့် အဖွဲ့ဝင်များကို ပြန်သည်။ **ဦးတည်ချက်** အရေးကြီးသည် —

- `desired - current` → `to_add` (အသစ် ရေးရမည့် edge များ)
- `current - desired` → `to_delete` (ဖျက်ရမည့် edge များ)
```python
current = {("P", "a", "R", "P", "b", "c1"), ("P", "a", "R", "P", "b", "c2")}
desired = {("P", "a", "R", "P", "b", "c1"), ("P", "b", "R", "P", "c", "c3")}

print("desired - current :", sorted(desired - current))
print("current - desired :", sorted(current - desired))
print("symmetric same?   :",
      sorted(desired - current) == sorted(current - desired))
print("|A|=%d |B|=%d |A-B|=%d" % (len(current), len(desired),
                                  len(current - desired)))
```

Output —
```text
desired - current : [('P', 'b', 'R', 'P', 'c', 'c3')]
current - desired : [('P', 'a', 'R', 'P', 'b', 'c2')]
symmetric same?   : False
|A|=2 |B|=2 |A-B|=1
```

`desired - current` နှင့် `current - desired` သည် **တူညီခြင်း မရှိပါ**
(`symmetric same? : False`)။ ဤအချက်သည် set difference ၏ အဓိကဂုဏ်သတ္တိ ဖြစ်သည် —
`|A|` နှင့် `|B|` တူညီသော်လည်း ဦးတည်ချက် မှားလျှင် `to_add` နှင့် `to_delete` ကို
လဲလှယ်လိုက်ခြင်း ဖြစ်သည်။ `to_delete` နှင့် `to_add` ကို လဲလှယ်လိုက်လျှင် **ဖျက်သင့်သည့်
edge များကို ရေးပြီး ရေးသင့်သည့် edge များကို ဖျက်** လိုက်မည်။

### 3.1 Function အဖြစ် ထုပ်ခြင်း
```python
def diff_relationships(current_edges, desired_edges):
    return (sorted(desired_edges - current_edges),
            sorted(current_edges - desired_edges))


current = {("P", "a", "R", "P", "b", "c1"), ("P", "a", "R", "P", "b", "c2")}
desired = {("P", "a", "R", "P", "b", "c1"), ("P", "b", "R", "P", "c", "c3")}
to_add, to_delete = diff_relationships(current, desired)
print("to_add :", to_add)
print("to_delete :", to_delete)
print(type(to_add).__name__, type(to_delete).__name__)
```

Output —
```text
to_add : [('P', 'b', 'R', 'P', 'c', 'c3')]
to_delete : [('P', 'a', 'R', 'P', 'b', 'c2')]
list list
```

`sorted()` ဖြင့် စီထားသဖြင့် ရလဒ်သည် list ဖြစ်ပြီး အစီအစဉ် deterministic ဖြစ်သည် —
set ၏ hash order ကို လုံးဝ မမှီခိုပါ။ ဤအချက်သည် log နှိုင်းယှဉ်ခြင်း၊ test ရေးခြင်းအတွက်
မဖြစ်မနေ လိုသည်။

Return အဖြစ် tuple `(to_add, to_delete)` ကို ပြန်ခြင်းသည် caller ကို
`to_add, to_delete = diff_relationships(...)` လို့ တစ်လိုင်းတည်း ခွဲယူစေသည်။

---
## 4. `node_degree()` — `dict.get()` ဖြင့် Counter pattern
```python
degree[(head_label, head_id)] = degree.get((head_label, head_id), 0) + 1
```

ဤသည်မှာ Python တွင် အဖြစ်အများဆုံး counting pattern ဖြစ်သည်။ `degree.get(key, 0)`
သည် key ရှိလျှင် တန်ဖိုးကို၊ မရှိလျှင် `0` ကို ပြန်သည်။ ထို့ကြောင့် key မရှိသေးသည့်
အခါ `KeyError` မဖြစ်ဘဲ 1 မှ စရေသည်။ (`collections.Counter` ကလည်း ဤအလုပ်ကို လုပ်သည်;
standard library ကို မပြောင်းလဲစေရန် ဤနေရာတွင် manual pattern ကို ပြထားသည်။)

Degree ကို **နှစ်ဖက်လုံး** တွက်သည်ကို သတိပြုပါ — head နှင့် tail တစ်ခုစီ။ Loop variable
`_rel` နှင့် `_chunk` သည် အသုံးမလိုသည့် field များဖြစ်သည်; `_` ဖြင့် စသည့်အမည်သည်
"သုံးမည် မဟုတ်" ဟု ဆိုလိုသည်။
```python
edges = {("Person", "ada_lovelace", "WORKED_AT", "Organization", "project", "c01"),
         ("Person", "ada_lovelace", "USES", "Technology", "engine", "c01"),
         ("Person", "ada_lovelace", "COLLABORATED_WITH", "Person", "babbage", "c02")}
degree = {}
for head_label, head_id, _rel, tail_label, tail_id, _chunk in edges:
    degree[(head_label, head_id)] = degree.get((head_label, head_id), 0) + 1
    degree[(tail_label, tail_id)] = degree.get((tail_label, tail_id), 0) + 1

for node in sorted(degree):
    print("  %-12s %-18s degree=%d" % (node[0], node[1], degree[node]))
print("nodes in dict :", len(degree))
print("get default   :", degree.get(("Person", "nobody"), 0))
```

Output —
```text
  Organization project            degree=1
  Person       ada_lovelace       degree=3
  Person       babbage            degree=1
  Technology   engine             degree=1
nodes in dict : 4
get default   : 0
```

`ada_lovelace` ၏ degree သည် 3 ဖြစ်သည် (edge ၃ ခုလုံးတွင် ပါသည်); `babbage`၊ `project`၊
`engine` တို့သည် 1 စီ။ `degree.get(("Person", "nobody"), 0)` က `0` ပြန်သည်ကို
အသုံးပြုပြီး `orphan_nodes()` က "graph ထဲ စာရင်းသွင်းထားသော်လည်း edge မရှိသည့် node"
ကို ရှာသည်။

---
## 5. Diff ကို အမှန်တကယ် Run ခြင်း
Desired state ကို ဖန်တီးသည့်နည်းကို ဖတ်ကြည့်ပါ —

```python
desired = edge_set([t for t in TRIPLES if t["chunk_id"] not in ("c01", "c02")
                    or t["rel"] not in ("USES", "COLLABORATED_WITH")])
```

Condition သည် "`chunk_id` က `c01`/`c02` မဟုတ် **သို့မဟုတ်** `rel` က `USES`/
`COLLABORATED_WITH` မဟုတ်" ဖြစ်သည်။ ဤသည်မှာ "`c01`/`c02` chunk များထဲက
`USES`/`COLLABORATED_WITH` ကို ချန်လှပ်" ဆိုသည့် အဓိပ္ပာယ်ဖြင့် တူညီသည် —
re-extraction က ထို relationship နှစ်မျိုးကို မထုတ်တော့ခြင်းကို ကိုယ်စားပြုသည်။
```python
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

def edge_set(triples):
    return {(ENTITY_TYPE_TO_LABEL[t["head_type"]], slug(t["head"]), t["rel"],
             ENTITY_TYPE_TO_LABEL[t["tail_type"]], slug(t["tail"]), t["chunk_id"])
            for t in triples}


def diff_relationships(current_edges, desired_edges):
    return (sorted(desired_edges - current_edges),
            sorted(current_edges - desired_edges))


def node_degree(edges):
    degree = {}
    for head_label, head_id, _rel, tail_label, tail_id, _chunk in edges:
        degree[(head_label, head_id)] = degree.get((head_label, head_id), 0) + 1
        degree[(tail_label, tail_id)] = degree.get((tail_label, tail_id), 0) + 1
    return degree


def orphan_nodes(nodes, edges):
    degree = node_degree(edges)
    return sorted(n for n in nodes if degree.get(n, 0) == 0)

current = edge_set(TRIPLES)
desired = edge_set([t for t in TRIPLES if t["chunk_id"] not in ("c01", "c02")
                    or t["rel"] not in ("USES", "COLLABORATED_WITH")])
to_add, to_delete = diff_relationships(current, desired)

print("current edges=%d  desired edges=%d" % (len(current), len(desired)))
print("to_add=%d  to_delete=%d" % (len(to_add), len(to_delete)))
for e in to_delete:
    print("  DELETE %s(%s)-[:%s]->%s(%s)" % (e[0], e[1], e[2], e[3], e[4]))
```

Output —
```text
current edges=6  desired edges=4
to_add=0  to_delete=2
  DELETE Person(ada_lovelace)-[:COLLABORATED_WITH]->Person(charles_babbage)
  DELETE Person(ada_lovelace)-[:USES]->Technology(analytical_engine)
```

Desired သည် 4 ဖြစ်ပြီး `to_add` 0၊ `to_delete` 2 ဖြစ်သည်။ `to_add = 0` ဖြစ်ခြင်းက
desired ၏ edge အားလုံး graph ထဲ ရှိပြီးသား ဖြစ်ကြောင်း၊ လိုအပ်သည်မှာ **ဖျက်ခြင်းသာ**
ဖြစ်ကြောင်း ပြသည်။

Idempotent delete စည်းမျဉ်း — ဖျက်ပြီးသား edge ကို ထပ်ဖျက်လျှင် Neo4j တွင်
`MATCH ... DELETE` သည် match မတွေ့သဖြင့် *error မဖြစ်၊ ဘာမှ မလုပ်* ပါ။ ထို့ကြောင့်
prune job ကို ထပ်ခါတလဲလဲ run နိုင်သည် — `DELETE` သည် idempotent ဖြစ်သည်။
သို့သော် `to_delete` စာရင်းကို **အရင် log** လုပ်ထားရသည်; မဟုတ်လျှင် မည်သည့်
relationship များ ပျောက်သွားသည်ကို ပြန်မသိနိုင်ပါ။

---
## 6. Orphan Node — ဖျက်ပြီးနောက် degree 0 ဖြစ်သည့် node
Relationship တစ်ခုကို ဖျက်လိုက်သည့်အခါ endpoint node တစ်ခုသည် **မည်သည့် edge နှင့်မှ
မချိတ်တော့သည့်** အခြေအနေ ဖြစ်နိုင်သည်။ ဥပမာ `(Ada)-[:USES]->(Analytical Engine)` ကို
ဖျက်လိုက်လျှင် `analytical_engine` node သည် ကျန်ခဲ့သည်။ လူမမြင်နိုင်သော်လည်း
`MATCH (n) WHERE NOT (n)--()` query အားလုံးတွင် ပါလာပြီး index နှင့် traversal ကို
ပိုလေးစေသည်။

`orphan_nodes(nodes, edges)` သည် node စာရင်းနှင့် edge set ကို လက်ခံပြီး degree 0
ဖြစ်သည့် node များကို စီပြီး ပြန်သည်။ `sorted(...)` ဖြင့် deterministic ဖြစ်စေသည်။
```python
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

def edge_set(triples):
    return {(ENTITY_TYPE_TO_LABEL[t["head_type"]], slug(t["head"]), t["rel"],
             ENTITY_TYPE_TO_LABEL[t["tail_type"]], slug(t["tail"]), t["chunk_id"])
            for t in triples}


def diff_relationships(current_edges, desired_edges):
    return (sorted(desired_edges - current_edges),
            sorted(current_edges - desired_edges))


def node_degree(edges):
    degree = {}
    for head_label, head_id, _rel, tail_label, tail_id, _chunk in edges:
        degree[(head_label, head_id)] = degree.get((head_label, head_id), 0) + 1
        degree[(tail_label, tail_id)] = degree.get((tail_label, tail_id), 0) + 1
    return degree


def orphan_nodes(nodes, edges):
    degree = node_degree(edges)
    return sorted(n for n in nodes if degree.get(n, 0) == 0)

current = edge_set(TRIPLES)
desired = edge_set([t for t in TRIPLES if t["chunk_id"] not in ("c01", "c02")
                    or t["rel"] not in ("USES", "COLLABORATED_WITH")])
to_add, to_delete = diff_relationships(current, desired)
nodes = {(e[0], e[1]) for e in current} | {(e[3], e[4]) for e in current}
remaining = current - set(to_delete)

degree_before = node_degree(current)
degree_after = node_degree(remaining)
for node in sorted(nodes):
    print("  %-12s %-26s before=%d after=%d"
          % (node[0], node[1], degree_before[node], degree_after.get(node, 0)))
print("orphans :", [n[1] for n in orphan_nodes(nodes, remaining)])
```

Output —
```text
  Location     london                     before=1 after=1
  Organization analytical_engine_project  before=4 after=4
  Person       ada_lovelace               before=4 after=2
  Person       charles_babbage            before=2 after=1
  Technology   analytical_engine          before=1 after=0
orphans : ['analytical_engine']
```

`analytical_engine` ၏ degree သည် ဖျက်ခြင်းမတိုင်မီ 1၊ ပြီးနောက် 0 ဖြစ်သွားသည်။ ကျန်
node အားလုံးတွင် edge ကျန်သည် (`after >= 1`)။

Orphan ကို ဖျက်မလား၊ ထားမလား ဆုံးဖြတ်ချက်သည် domain အပေါ် မူတည်သည် —

- **ဖျက်သင့်သည်** — node သည် ယခု corpus မှ လုံးဝ ပျောက်သွားလျှင်။
- **မဖျက်သင့်ပါ** — node သည် entity အမှန်တကယ် ဖြစ်ပြီး relationship များသာ မဖန်တီးရသေးလျှင်
  (incremental ingestion တွင် chunk က relationship မပါဘဲ ဝင်လာနိုင်သည်)။ ထို node ကို
  ဖျက်လိုက်လျှင် နောက်တစ်ကြိမ် ရေးသည့်အခါ identity အသစ် ဖြစ်သွားနိုင်သည်။

ထို့ကြောင့် orphan cleanup ကို **အလိုအလျောက် default မလုပ်ရ** — orphan စာရင်းကို
dry-run အဖြစ် log လုပ်ပြီး၊ threshold (`> 5% of nodes` ကဲ့သို့) ကျော်လျှင် alert ပေးမှ
ဖျက်သင့်သည်။

---
## 7. `DETACH DELETE` — Cascade ၏ ဘေးထွက်သက်ရောက်မှု
Neo4j တွင် relationship ရှိသေးသည့် node ကို `DELETE n` ဖြင့် ဖျက်လျှင် **error** ဖြစ်သည်
(`Cannot delete node<…>, because it still has relationships`).Node နှင့် သူ့
relationship အားလုံးကို ဖျက်ရန် `DETACH DELETE n` ကို သုံးရသည်။

```cypher
// node တစ်ခုတည်း ဖျက်ခြင်း — relationship ရှိသေးလျှင် error
MATCH (n:Person {id: $id})
DELETE n

// node နှင့် သူ့ relationship အားလုံး — cascade
MATCH (n:Person {id: $id})
DETACH DELETE n
```

အောက်က code သည် `ada_lovelace` ကို `DETACH DELETE` လုပ်လျှင် edge ဘယ်နှစ်ခု
ပျောက်မည်ကို simulate လုပ်သည်။
```python
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

def edge_set(triples):
    return {(ENTITY_TYPE_TO_LABEL[t["head_type"]], slug(t["head"]), t["rel"],
             ENTITY_TYPE_TO_LABEL[t["tail_type"]], slug(t["tail"]), t["chunk_id"])
            for t in triples}


def diff_relationships(current_edges, desired_edges):
    return (sorted(desired_edges - current_edges),
            sorted(current_edges - desired_edges))


def node_degree(edges):
    degree = {}
    for head_label, head_id, _rel, tail_label, tail_id, _chunk in edges:
        degree[(head_label, head_id)] = degree.get((head_label, head_id), 0) + 1
        degree[(tail_label, tail_id)] = degree.get((tail_label, tail_id), 0) + 1
    return degree


def orphan_nodes(nodes, edges):
    degree = node_degree(edges)
    return sorted(n for n in nodes if degree.get(n, 0) == 0)

current = edge_set(TRIPLES)
desired = edge_set([t for t in TRIPLES if t["chunk_id"] not in ("c01", "c02")
                    or t["rel"] not in ("USES", "COLLABORATED_WITH")])
to_add, to_delete = diff_relationships(current, desired)
remaining = current - set(to_delete)

victim = ("Person", "ada_lovelace")
cascaded = {e for e in remaining
            if (e[0], e[1]) != victim and (e[3], e[4]) != victim}
print("victim          :", victim[1])
print("edges before    :", len(remaining))
print("edges to cascade:", len(remaining) - len(cascaded))
print("edges after     :", len(cascaded))
for e in sorted(cascaded):
    print("  kept %s(%s)-[:%s]->%s(%s)" % (e[0], e[1], e[2], e[3], e[4]))
```

Output —
```text
victim          : ada_lovelace
edges before    : 4
edges to cascade: 2
edges after     : 2
  kept Organization(analytical_engine_project)-[:LOCATED_IN]->Location(london)
  kept Person(charles_babbage)-[:FOUNDED]->Organization(analytical_engine_project)
```

Edge 4 ခုမှ 2 ခုသို့ ကျသည် — `ada_lovelace` နှင့် ဆက်နေသည့် edge 2 ခု ပျောက်သွားသည်။
ဤသည်မှာ cascade delete ၏ အန္တရာယ် ဖြစ်သည်: node တစ်ခုဖျက်ရန် ရည်ရွယ်ချက်ဖြင့်
relationship အရေအတွက် မသိဘဲ run လျှင် Babbage နှင့် Project တို့၏ edge များလည်း
ပျောက်သွားနိုင်သည်။

ထို့ကြောင့် cascade delete မတိုင်မီ **count ကို အရင်တွက်ရ** သည် —

```python
count = len(remaining) - len(cascaded)
if count > MAX_CASCADE:
    raise RuntimeError("cascade လုပ်မည့် relationship %d ခု — threshold ကျော်သည်" % count)
```

Production စည်းကမ်း —

1. Cascade မတိုင်မီ count ကို log လုပ်ပြီး threshold သတ်မှတ်ရသည်။
2. `DETACH DELETE` ကို transaction တစ်ခုတည်းထဲတွင် node အရေအတွက် အနည်းငယ်သာ
   ထည့်ရသည် — node အများကြီး ဖျက်လျှင် transaction ပျက်သည့်အခါ ပြန်လုပ်ရ ခက်သည်။
3. Text-to-Cypher လမ်းကြောင်းတွင် `DETACH DELETE` ကို allowlist မှ ဖယ်ရသည် —
   user prompt တစ်ခုက graph ကို အစိတ်စိတ် ဖျက်နိုင်သည်။

---
## 8. ရလဒ်ကို ဇယားဖြင့် ကြည့်ခြင်း
Current edge တိုင်း၏ ဆုံးဖြတ်ချက် (အထက်က run ၏ အမှန်တကယ် တန်ဖိုးများ) —

| Edge identity | chunk | to_delete? |
| --- | --- | --- |
| `Organization(analytical_engine_project)-[:LOCATED_IN]->Location(london)` | `c03` | keep |
| `Person(ada_lovelace)-[:COLLABORATED_WITH]->Person(charles_babbage)` | `c02` | **DELETE** |
| `Person(ada_lovelace)-[:USES]->Technology(analytical_engine)` | `c01` | **DELETE** |
| `Person(ada_lovelace)-[:WORKED_AT]->Organization(analytical_engine_project)` | `c01` | keep |
| `Person(ada_lovelace)-[:WORKED_AT]->Organization(analytical_engine_project)` | `c04` | keep |
| `Person(charles_babbage)-[:FOUNDED]->Organization(analytical_engine_project)` | `c02` | keep |

Orphan နှင့် cascade ရလဒ်များ —

| အချက် | တန်ဖိုး |
| --- | --- |
| current edges | 6 |
| desired edges | 4 |
| to_add | 0 |
| to_delete | 2 (`USES`၊ `COLLABORATED_WITH`) |
| orphan after delete | 1 (`analytical_engine`) |
| `DETACH DELETE ada_lovelace` | edges 4 → 2 |

ဇယားက အရေးကြီးသောအချက်ကို ပြသည် — ဖျက်မည့် edge ၂ ခုအနက် တစ်ခုက `USES`
(Technology ဆီ သွားသည်) ဖြစ်သဖြင့် `analytical_engine` orphan ဖြစ်သည်။
`COLLABORATED_WITH` ဖျက်ခြင်းကမူ orphan မဖြစ်စေပါ — Babbage နှင့် Ada နှစ်ဦးလုံးတွင်
ကျန် edge ရှိသည်။ **Diff သည် orphan ကို တိုက်ရိုက် ညွှန်းခြင်း မရှိ** — ၎င်းကို အပိုဆောင်း
တွက်ချက်မှုဖြင့် ရှာရသည်။

---
## 9. Code တစ်ခုလုံး — Run လုပ်နိုင်သော Version
```python
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

def edge_set(triples):
    return {(ENTITY_TYPE_TO_LABEL[t["head_type"]], slug(t["head"]), t["rel"],
             ENTITY_TYPE_TO_LABEL[t["tail_type"]], slug(t["tail"]), t["chunk_id"])
            for t in triples}


def diff_relationships(current_edges, desired_edges):
    return (sorted(desired_edges - current_edges),
            sorted(current_edges - desired_edges))


def node_degree(edges):
    degree = {}
    for head_label, head_id, _rel, tail_label, tail_id, _chunk in edges:
        degree[(head_label, head_id)] = degree.get((head_label, head_id), 0) + 1
        degree[(tail_label, tail_id)] = degree.get((tail_label, tail_id), 0) + 1
    return degree


def orphan_nodes(nodes, edges):
    degree = node_degree(edges)
    return sorted(n for n in nodes if degree.get(n, 0) == 0)

current = edge_set(TRIPLES)
# re-extraction သည် USES နှင့် COLLABORATED_WITH ကို မထောက်ပံ့တော့ပါ
desired = edge_set([t for t in TRIPLES if t["chunk_id"] not in ("c01", "c02")
                    or t["rel"] not in ("USES", "COLLABORATED_WITH")])
to_add, to_delete = diff_relationships(current, desired)
nodes = {(e[0], e[1]) for e in current} | {(e[3], e[4]) for e in current}
remaining = current - set(to_delete)
orphans = orphan_nodes(nodes, remaining)
print("current edges=%d  desired edges=%d" % (len(current), len(desired)))
print("to_add=%d  to_delete=%d" % (len(to_add), len(to_delete)))
for e in to_delete:
    print("  DELETE %s(%s)-[:%s]->%s(%s)" % (e[0], e[1], e[2], e[3], e[4]))
print("orphan nodes after delete=%s" % [n[1] for n in orphans])
victim = ("Person", "ada_lovelace")
cascaded = {e for e in remaining
            if (e[0], e[1]) != victim and (e[3], e[4]) != victim}
print("DETACH DELETE %s -> edges %d -> %d"
      % (victim[1], len(remaining), len(cascaded)))
```

Output —
```text
current edges=6  desired edges=4
to_add=0  to_delete=2
  DELETE Person(ada_lovelace)-[:COLLABORATED_WITH]->Person(charles_babbage)
  DELETE Person(ada_lovelace)-[:USES]->Technology(analytical_engine)
orphan nodes after delete=['analytical_engine']
DETACH DELETE ada_lovelace -> edges 4 -> 2
```

---
## 10. ကိုယ်တိုင်လေ့ကျင့်ကြည့်ပါ

**မေးခွန်း** — `current` တွင် edge ၁ ခု၊ `desired` တွင် edge **၂** ခု ရှိပြီး current ၏
edge သည် desired ထဲ ပါဝင်လျှင် `to_add` နှင့် `to_delete` က ဘာဖြစ်မလဲ။
```python
current = {("P", "a", "R", "P", "b", "c1")}
desired = {("P", "a", "R", "P", "b", "c1"), ("P", "a", "R", "P", "b", "c2")}


def diff_relationships(current_edges, desired_edges):
    return (sorted(desired_edges - current_edges),
            sorted(current_edges - desired_edges))


to_add, to_delete = diff_relationships(current, desired)
print("to_add =", to_add)
print("to_delete =", to_delete)
```

1. `to_add` ၁ ခု၊ `to_delete` ၀
2. `to_add` ၀၊ `to_delete` ၁ ခု
3. `to_add` ၂ ခု၊ `to_delete` ၁ ခု
4. နှစ်ခုလုံး ၀ — set အရေအတွက် မတူလို့ error ဖြစ်သည်

<details>
<summary>အဖြေ ကြည့်ရန်</summary>

**အဖြေ — 1. `to_add` ၁ ခု၊ `to_delete` ၀**

အကြောင်းရင်း — `to_add = desired - current` ဖြစ်သည်။ Desired ထဲက `c1` edge သည်
current ထဲ ပါသဖြင့် ကျန် `c2` edge တစ်ခုသာ ကျန်သည်။ `to_delete = current - desired`
ဖြစ်ပြီး current ၏ edge တစ်ခုလုံး desired ထဲ ပါသဖြင့် အလွတ် ဖြစ်သည်။
အထက်က run ၏ output က အတည်ပြုသည် — `to_add = [('P', 'a', 'R', 'P', 'b', 'c2')]`၊
`to_delete = []`။

Set အရေအတွက် မတူခြင်းသည် error မဖြစ်စေပါ — set operation သည် အရေအတွက်ကို
ဂရုမစိုက်ဘဲ အဖွဲ့ဝင်အလိုက် အလုပ်လုပ်သည်။

</details>

---

**အဓိက မှတ်ထားရန်** — Desired-state diff သည် graph ကို corpus နှင့် တစ်သမတ်တည်း
ထားရှိရန် လိုအပ်သည်; `to_add` က `desired - current`၊ `to_delete` က
`current - desired` ဖြစ်ပြီး ဦးတည်ချက် လဲလျှင် ဖျက်ရမည့်အရာကို ရေးမိမည်။ Orphan ကို
diff က ညွှန်းမပေးသဖြင့် degree ကို သီးသန့် တွက်ရသည်။ `DELETE` (relationship ရှိလျှင်
error) နှင့် `DETACH DELETE` (cascade) ကို ကွဲပြားစွာ သုံးခြင်းသည် accidental cascade
ကို ကာကွယ်သည် — cascade မတိုင်မီ count ကို တွက်ပြီး threshold သတ်မှတ်ရသည်။
