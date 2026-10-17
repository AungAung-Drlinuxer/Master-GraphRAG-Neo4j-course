# Walkthrough 01 — Full pipeline recap (Exercise 1)

> ဤဖိုင်သည် Module 08 ၏ `solution.md` ထဲက Exercise 1 ကို **Python အခြေခံမှ စ၍**
> အပိုင်းလိုက် ရှင်းပြသည့် walkthrough ဖြစ်သည်။ Format သည် Module 01 ၏
> `walkthroughs/01_regex_ner.md` နှင့် `walkthroughs/03_gazetteer_lookup.md` နှင့်
> တူညီသည်။

---

## 0. ဤ Exercise က ဘာကို ဖြေရှင်းပေးသလဲ။

Course တစ်ခုလုံးတွင် M00 မှ M08 အထိ stage အများအပြား ရှိသည်။ Stage တိုင်းက သူ့အလုပ်
ပြီးမှ နောက် stage ကို စရသည်။ ဤအစီအစဉ်ကို မှန်ကန်စွာ သတ်မှတ်ရန် လိုအပ်သည် —
မဟုတ်လျှင် stage တစ်ခုက သူ့ input မရှိသေးဘဲ run မိပါမည်။

```text
ingest -> normalize -> chunk -> extract -> resolve -> merge_dedup -> graph_write
                                                                       |
                                              entity_link ----------> retrieve
                                                                       |
                                                serialize -> generate <-
```

Ingestion-side (document → graph) နှင့် retrieval-side (question → answer) ကို ချိတ်ဆက်သော
နေရာက `retrieve` ဖြစ်သည်။ ဤ Exercise က stage များကို **DAG** (Directed Acyclic Graph)
အဖြစ် ဖော်ပြပြီး **topological order** — prerequisite အားလုံး ပြီးသွားသော stage ကို အရင်
ရွေးသော အစီအစဉ် — ကို ထုတ်ပေးသည်။

ဤ code တွင် လေ့လာရမည့် Python concepts များမှာ —

- `from collections import OrderedDict` နှင့် ordered key-value ဖွဲ့စည်းပုံ
- List နှင့် `list(dict.keys())`
- `all()` နှင့် **generator expression**၊ vacuous truth (အလွတ် iterable က `True`)
- `while` loop နှင့် list ကို loop အတွင်း ပြင်ခြင်း (`list(...)` copy လုပ်ရသည့် အကြောင်းရင်း)
- `try/except` နှင့် `raise ValueError`
- Dict comprehension နှင့် `enumerate()`
- Tuple unpacking နှင့် list of tuples
- f-string alignment spec (`:<42`)
- `" -> ".join(...)`

---

## 1. `STAGE_DEPS` — Stage များ၏ မှီခိုမှု စာရင်း

```python
from collections import OrderedDict

STAGE_DEPS = OrderedDict([
    ("ingest", []),
    ("normalize", ["ingest"]),
    ("chunk", ["normalize"]),
    ("extract", ["chunk"]),
    ("resolve", ["extract"]),
    ("merge_dedup", ["resolve"]),
    ("graph_write", ["merge_dedup"]),
    ("entity_link", []),
    ("retrieve", ["entity_link", "graph_write"]),
    ("serialize", ["retrieve"]),
    ("generate", ["serialize"]),
])

print(STAGE_DEPS["retrieve"])
print(list(STAGE_DEPS))
```

Output —

```text
['entity_link', 'graph_write']
['ingest', 'normalize', 'chunk', 'extract', 'resolve', 'merge_dedup', 'graph_write', 'entity_link', 'retrieve', 'serialize', 'generate']
```

`OrderedDict([...])` ကို key-value pair များပါသော **list of tuples** ကနေ ဆောက်သည်။
`("ingest", [])` သည် `"ingest"` key နှင့် အလွတ် list `[]` value ဖြစ်သည်။

- key = stage အမည်
- value = ထို stage မလုပ်မီ ပြီးရမည့် stage များ၏ **list** (prerequisite list)

`list(STAGE_DEPS)` က key များကို သူတို့ ထည့်ထားသော အစီအစဉ်အတိုင်း ပြန်ပေးသည်။
Python 3.7 ကတည်းက သာမန် `dict` ကလည်း insertion order ကို ထိန်းသော်လည်း၊ prerequisite
list အစီအစဉ်ကို **တိတိကျကျ** ဖော်ပြလိုသည့်အတွက် `OrderedDict` ကို သုံးထားခြင်းသည်
ရည်ရွယ်ချက် ရှိသည် — reader က \"ဤ order က ရည်ရွယ်ချက်ရှိသည်\" ဟု ဖတ်နိုင်သည်။

`entity_link` တွင် prerequisite မရှိဘဲ `[]` ရှိခြင်းကို သတိထားပါ။ Ingestion chain နှင့်
မချိတ်ဘဲ သီးခြား စနိုင်သော stage ဖြစ်သောကြောင့် ဖြစ်သည်။ `retrieve` မှာ `entity_link` နှင့်
`graph_write` **နှစ်ခုလုံး** ကို စောင့်သည်။

### OrderedDict ကို plain dict နှင့် နှိုင်းယှဉ်ခြင်း

```python
from collections import OrderedDict

plain = {"ingest": [], "normalize": ["ingest"]}
ordered = OrderedDict([("ingest", []), ("normalize", ["ingest"])])

print(list(plain))
print(list(ordered))
print(plain == ordered)
```

Output —

```text
['ingest', 'normalize']
['ingest', 'normalize']
True
```

နှစ်ခုလုံး key order တူပြီး တန်ဖိုးလည်း တူသောကြောင့် `==` က `True` ပြန်သည်။ ထို့ကြောင့်
ဤ Exercise တွင် `OrderedDict` ကို သုံးခြင်းသည် **ရည်ရွယ်ချက်ကို ရှင်းလင်းစေသည်** အပေါ်
အကျိုးသက်ရောက်မှုသာ ရှိသည်။

---

## 2. `all()` နှင့် Vacuous Truth

`all(iterable)` က iterable ထဲက item အားလုံး `True` ဖြစ်/မဖြစ် စစ်ဆေးသည်။ ဤနေရာတွင်
**generator expression** `(dep in order for dep in deps)` ကို သုံးသည်။

```python
STAGE_DEPS = {"ingest": [], "normalize": ["ingest"]}
order = []

print(all(dep in order for dep in STAGE_DEPS["ingest"]))
print(all(dep in order for dep in STAGE_DEPS["normalize"]))

order.append("ingest")
print(all(dep in order for dep in STAGE_DEPS["normalize"]))
```

Output —

```text
True
False
True
```

တစ်လိုင်းချင်း ရှင်းရအောင် —

| လိုင်း | စစ်သည့် အရာ | ရလဒ် |
| --- | --- | --- |
| ၁ | `[]` ထဲက item အားလုံး `order` ထဲ ရှိ/မရှိ | `True` |
| ၂ | `"ingest" in []` ဖြစ်/မဖြစ် | `False` |
| ၃ | `"ingest" in ["ingest"]` ဖြစ်/မဖြစ် | `True` |

ပထမလိုင်း၏ `True` က အရေးကြီးသည်။ **အလွတ် iterable အတွက် `all()` က `True`
ပြန်သည်** — ၎င်းကို *vacuous truth* ဟု ခေါ်သည်။ \"ချိုးဖောက်ထားသော item တစ်ခုမှ
မရှိ\" ဆိုသည့် အဓိပ္ပာယ်ပါ။

ဤအချက်က `topological_order` အတွက် **မရှိမဖြစ်** လိုအပ်သည်။ `ingest` နှင့်
`entity_link` က prerequisite `[]` ရှိသောကြောင့် သူတို့ကို **ပထမဆုံး** ရွေးနိုင်သည်။
`all()` က အလွတ် list အတွက် `False` ပြန်ခဲ့လျှင် ဘယ် stage မှ စ၍ မရဘဲ loop က
ပိတ်မိသွားပါမည်။

### Generator expression ဆိုသည်မှာ အဘယ်နည်း

`all(...)` ထဲတွင် ကွင်း `()` နှင့် ရေးထားသော `dep in order for dep in deps` က
generator expression ဖြစ်သည်။ List comprehension နှင့် တူသော်လည်း item များကို
**တစ်လုံးချင်း လိုအပ်သည့်အခါမှ** ထုတ်ပေးသည်။

```python
deps = ["ingest", "chunk"]
order = ["ingest"]

print([dep in order for dep in deps])
print(list(dep in order for dep in deps))
print(all(dep in order for dep in deps))
```

Output —

```text
[True, False]
[True, False]
False
```

ပထမလိုင်းက list comprehension (list ပြန်သည်)၊ ဒုတိယလိုင်းက generator expression ကို
`list()` ဖြင့် ပြောင်းထားခြင်း ဖြစ်သည်။ ရလဒ် တူညီသည်။

---

## 3. `topological_order()` — အစီအစဉ် ဆုံးဖြတ်ခြင်း

```python
def topological_order(stage_deps):
    """Prerequisite အားလုံး ပြီးသွားသော stage ကို အရင် ရွေးချယ်သည်။"""
    remaining = list(stage_deps.keys())
    order = []
    while remaining:
        progressed = False
        for name in list(remaining):
            if all(dep in order for dep in stage_deps[name]):
                order.append(name)
                remaining.remove(name)
                progressed = True
        if not progressed:
            raise ValueError("cycle detected in stage dependencies")
    return order
```

### 3.1 `remaining = list(stage_deps.keys())` — ကျန်ရှိသေး queue

`stage_deps.keys()` က အားလုံး key ကို ပြန်ပေးသည်။ `list(...)` ဖြင့် list အဖြစ်
ပြောင်းထားခြင်းသည် **နောက်ပိုင်း `remaining.remove(name)` လုပ်နိုင်ရန်** ဖြစ်သည်။

```python
STAGE_DEPS = {"ingest": [], "normalize": ["ingest"]}
remaining = list(STAGE_DEPS.keys())
print(remaining)
remaining.remove("ingest")
print(remaining)
```

Output —

```text
['ingest', 'normalize']
['normalize']
```

`remove(value)` က list ထဲက **တန်ဖိုးနှင့် ကိုက်သည့် ပထမဆုံး item** ကို ဖယ်သည်။

### 3.2 `while remaining:` — အဘယ်ကြောင့် `while` နည်း

`remaining` list ထဲ stage ကျန်နေသရွေ့ loop ဆက်လုပ်သည်။ `while` သုံးခြင်းသည်
loop အတွင်းတွင်သာ `remaining` ကို item ဖယ်ပြီး **အတိုချုံ့** သွားသောကြောင့် ဖြစ်သည်။
`for` loop နှင့်ဆို item တစ်ခုချင်း တိုးပြီး ဤသို့ ပြင်ခြင်း အဆင်မပြေပါ။

`while remaining:` သည် `while len(remaining) > 0:` နှင့် အလုပ်တူသည် — မလွတ် list
က `True`၊ လွတ်သွားလျှင် `False` ဖြစ်သည်။

```python
counter = []
while counter:
    print("never runs")
counter.append("ingest")
while counter:
    print("runs once, remaining =", len(counter))
    counter.remove("ingest")
```

Output —

```text
runs once, remaining = 1
```

### 3.3 `for name in list(remaining):` — copy လုပ်ရသည့် အကြောင်းရင်း

Loop အတွင်းတွင် `remaining.remove(name)` ကို ခေါ်သည်။ ထို့ကြောင့် `for` က
`list(remaining)` — **copy တစ်ခု** အပေါ်တွင် loop လုပ်ရသည်။ `remaining` ကိုယ်တိုင်
အပေါ်တွင် loop လုပ်လျှင် iteration အတွင်း list ကို ပြင်နေခြင်းကြောင့် item ကျော်သွားနိုင်သည်။

```python
items = ["a", "b", "c"]
for x in list(items):
    items.remove(x)
    print("removed", x, "-> remaining", items)
```

Output —

```text
removed a -> remaining ['b', 'c']
removed b -> remaining ['c']
removed c -> remaining []
```

### 3.4 `all(...)` + `append` + `remove` — stage တစ်ခု ရွေးခြင်း

`if all(dep in order for dep in stage_deps[name]):` သည် true ဖြစ်လျှင် — ထို stage ၏
prerequisite အားလုံး `order` ထဲ ရှိပြီးသား — ထိုအခါ `order` ထဲ ထည့်ပြီး `remaining`
ကနေ ဖယ်သည်။

`progressed = True` က \"ဤ round တွင် အနည်းဆုံး stage တစ်ခု ရွေးနိုင်ခဲ့သည်\" ကို
မှတ်ထားခြင်း ဖြစ်သည်။

---

## 4. Cycle Detection — `progressed` နှင့် `raise ValueError`

```python
remaining = ["a", "b"]
order = []
progressed = False
for name in list(remaining):
    deps = {"a": ["b"], "b": ["a"]}[name]
    if all(dep in order for dep in deps):
        order.append(name)
        remaining.remove(name)
        progressed = True
print("progressed =", progressed)
print("would raise:", not progressed)
```

Output —

```text
progressed = False
would raise: True
```

`if not progressed:` က round တစ်ခုလုံးတွင် ဘယ် stage မှ မရွေးနိုင်လျှင် `raise` လုပ်သည်။
`raise ValueError("...")` က exception ကို **ဖန်တီးပစ်** သည်။ ၎င်းသည် infinite loop ကို
တားဆီးသည် — cycle ရှိလျှင် `remaining` မည်သည့်အခါမျှ လွတ်မည် မဟုတ်သောကြောင့် loop က
ထာဝရ လည်နေမည် ဖြစ်သည်။

`try/except` ဖြင့် ဖမ်းကြည့်ရအောင် —

```python
def topological_order(stage_deps):
    remaining = list(stage_deps.keys())
    order = []
    while remaining:
        progressed = False
        for name in list(remaining):
            if all(dep in order for dep in stage_deps[name]):
                order.append(name)
                remaining.remove(name)
                progressed = True
        if not progressed:
            raise ValueError("cycle detected in stage dependencies")
    return order


CYCLIC = {"a": ["b"], "b": ["a"]}
try:
    order = topological_order(CYCLIC)
    print("order =", order)
except ValueError as exc:
    print("caught ->", type(exc).__name__ + ":", exc)
```

Output —

```text
caught -> ValueError: cycle detected in stage dependencies
```

`raise ValueError("...")` သည် exception object တစ်ခု ဖန်တီးပြီး လက်ရှိ call stack ကို
ရပ်တန့်သည်။ `try:` block အတွင်း ခေါ်ထားသောကြောင့် `except ValueError as exc:` က ဖမ်းပြီး
`exc` ထဲ ထည့်သည်။ `type(exc).__name__` က class အမည် `ValueError` ကို ပြန်သည်။

---

## 5. Function တစ်ခုလုံး Run ခြင်း — အစီအစဉ် ရလဒ်

```python
from collections import OrderedDict


def topological_order(stage_deps):
    remaining = list(stage_deps.keys())
    order = []
    while remaining:
        progressed = False
        for name in list(remaining):
            if all(dep in order for dep in stage_deps[name]):
                order.append(name)
                remaining.remove(name)
                progressed = True
        if not progressed:
            raise ValueError("cycle detected in stage dependencies")
    return order


STAGE_DEPS = OrderedDict([
    ("ingest", []),
    ("normalize", ["ingest"]),
    ("chunk", ["normalize"]),
    ("extract", ["chunk"]),
    ("resolve", ["extract"]),
    ("merge_dedup", ["resolve"]),
    ("graph_write", ["merge_dedup"]),
    ("entity_link", []),
    ("retrieve", ["entity_link", "graph_write"]),
    ("serialize", ["retrieve"]),
    ("generate", ["serialize"]),
])

order = topological_order(STAGE_DEPS)
print(order)
```

Output —

```text
['ingest', 'normalize', 'chunk', 'extract', 'resolve', 'merge_dedup', 'graph_write', 'entity_link', 'retrieve', 'serialize', 'generate']
```

Round တစ်ခုစီတွင် မည်သည့် stage ကို ရွေးနိုင်ခဲ့သည်ကို ပြန်ကြည့်ရအောင်။ `for name in list(remaining)` က
`remaining` အစီအစဉ်အတိုင်း စစ်သည်။

| Round | အစပိုင်း `remaining` | ရွေးနိုင်သည့် stage | ရွေးပြီး `order` |
| --- | --- | --- | --- |
| 1 | ingest, normalize, chunk…, entity_link | `ingest`၊ `entity_link` | `[ingest, entity_link]` |
| 2 | normalize, chunk…, retrieve | `normalize` | `[ingest, entity_link, normalize]` |
| 3 | chunk, extract…, retrieve | `chunk` | `…, chunk` |
| နောက်ဆုံး | `generate` သာ ကျန် | `generate` | `generate` ဖြင့် ဆုံး |

Order ၏ **ဖော်ပြအစီအစဉ်** က round အတွင်း `remaining` အစီအစဉ်အပေါ် မူတည်သည်
(ဥပမာ `ingest` နှင့် `entity_link` နှစ်ခုလုံး round 1 တွင် ရွေးခံရသည်)။ သို့သော်
**prerequisite စည်းမျဉ်း** (dependent အရင် ရှိရမည်) ကို ချိုးဖောက်ခြင်း မရှိပါ။

---

## 6. `position` — Dict Comprehension နှင့် `enumerate()`

Order ရလာပြီးလျှင် stage တိုင်း၏ **နေရာ (index)** ကို မှတ်ထားရန် လိုအပ်သည်။

```python
order = ["ingest", "normalize", "chunk", "extract"]
position = {name: index for index, name in enumerate(order)}
print(position)
```

Output —

```text
{'ingest': 0, 'normalize': 1, 'chunk': 2, 'extract': 3}
```

`enumerate(order)` က `(index, value)` tuple များကို ပြန်သည်။

```python
for index, name in enumerate(["a", "b", "c"]):
    print(index, name)
```

Output —

```text
0 a
1 b
2 c
```

`{name: index for index, name in enumerate(order)}` သည် **dict comprehension** ဖြစ်သည်။
`enumerate` က `(0, "ingest")` လို tuple ပေးသည့်အခါ `index, name` ဟူ၍ **tuple unpacking**
နှင့် ခွဲယူသည်။ List comprehension ကဲ့သို့ပင် ၎င်းသည် for loop တစ်ခုကို တစ်လိုင်းတည်း
ရေးခြင်း ဖြစ်သည်။

Dictionary ကို index အဖြင့် ပြန်ဖတ်လျှင် prerequisite check က **အလွန်လွယ်** သည် —

```python
order = ["ingest", "normalize", "chunk", "extract"]
position = {name: index for index, name in enumerate(order)}
STAGE_DEPS = {"ingest": [], "normalize": ["ingest"], "extract": ["chunk"]}

for name, deps in STAGE_DEPS.items():
    for dep in deps:
        print(dep, position[dep], "<", name, position[name], "=", position[dep] < position[name])
```

Output —

```text
ingest 0 < normalize 1 = True
chunk 2 < extract 3 = True
```

`position[dep] < position[name]` ကို `assert` နှင့် စစ်လိုက်လျှင် — prerequisite တိုင်းက
dependent stage အရင် နေရာရကြောင်း **တိတိကျကျ** သက်သေပြသည်။

---

## 7. `" -> ".join(order)` — အစီအစဉ်ကို တစ်လိုင်းတည်း ဖော်ပြခြင်း

```python
order = ["ingest", "normalize", "chunk"]
print("ingestion + retrieval order: " + " -> ".join(order))
```

Output —

```text
ingestion + retrieval order: ingest -> normalize -> chunk
```

`" -> ".join(order)` က list ထဲက string များကို `" -> "` separator ဖြင့်
ဆက်စပ်ပေးသည်။ `join` က **string method** ဖြစ်ပြီး list ကို argument အဖြစ်
လက်ခံသည်။

```python
print(" -> ".join(["ingest"]))
print(" -> ".join([]))
```

Output —

```text
ingest

```

item တစ်ခုတည်းလျှင် separator မပါဘဲ ထို item သာ ရသည်။ အလွတ် list အတွက်
empty string `""` ရသည် (အပေါ်က ဒုတိယလိုင်းက ဗလာလိုင်း ဖြစ်သည်)။

---

## 8. `MODULE_MAP` — List of Tuples နှင့် f-string Alignment

```python
MODULE_MAP = [
    ("M00", "Getting Started", "course architecture, RAG basics, GraphRAG path"),
    ("M07", "Knowledge Graph RAG", "entity linking, k-hop subgraph, hybrid retrieval"),
    ("M08", "Conclusion", "production deployment, decision criteria, capstone"),
]

print(MODULE_MAP[0])
module_id, title, focus = MODULE_MAP[1]
print(module_id, "|", title, "|", focus)
for module_id, title, focus in MODULE_MAP:
    print(f"  {module_id}  {title:<42} {focus}")
```

Output —

```text
('M00', 'Getting Started', 'course architecture, RAG basics, GraphRAG path')
M07 | Knowledge Graph RAG | entity linking, k-hop subgraph, hybrid retrieval
  M00  Getting Started                            course architecture, RAG basics, GraphRAG path
  M07  Knowledge Graph RAG                        entity linking, k-hop subgraph, hybrid retrieval
  M08  Conclusion                                 production deployment, decision criteria, capstone
```

`MODULE_MAP` ထဲက tuple တိုင်းတွင် `(module_id, title, focus)` သုံးခု ပါသည်။
`for a, b, c in list_of_tuples:` ဟု ရေးလျှင် tuple တိုင်းကို **unpack** လုပ်ပြီး loop
သည်။ `M04` က project module ဖြစ်ကြောင်း ဖော်ပြရန် map ထဲ အပြည့်အစုံ ကိုးခု ရှိသည်။

### `:<42` alignment spec

f-string ထဲက `{title:<42}` က `title` ကို **ဘယ်ဘက်ချိန်** ပြီး **အနည်းဆုံး 42
character ကျယ်အောင်** ဖြည့်သည်။ `<` က left-align၊ `42` က field width ပါ။

```python
print(f"[{'M01':<5}][{'Conclusion':<12}]end")
print(len(f"{'M01':<5}"))
print(f"{'Conclusion':<12}" + "|")
```

Output —

```text
[M01  ][Conclusion  ]end
5
Conclusion  |
```

`"M01"` (၃ လုံး) ကို width 5 ဖြည့်သဖြင့် `"M01  "` (၅ လုံး) ဖြစ်သည်။ `"Conclusion"`
(၁၀ လုံး) က width 12 ဖြည့်သဖြင့် နောက်တွင် space နှစ်လုံး ပါသည်။ `len(...)` က 5
ပြန်ခြင်းသည် field width ပြည့်ပြီးကြောင်း အတည်ပြုသည်။

---

## 9. Code တစ်ခုလုံး — Run လုပ်နိုင်သော Version

```python
from collections import OrderedDict

MODULE_MAP = [
    ("M00", "Getting Started", "course architecture, RAG basics, GraphRAG path"),
    ("M01", "Traditional NER and Relation Extraction", "BIO tagging, gazetteer, P/R/F1"),
    ("M02", "LLM Entity and Relation Extraction", "extraction prompt, JSON schema, resolution"),
    ("M03", "Chunking at Scale", "chunk size, overlap, map-reduce, idempotency"),
    ("M04", "Project: Knowledge Graph from Text", "end-to-end ingestion, provenance, export"),
    ("M05", "Neo4j Introduction", "Property Graph, Cypher, constraints, indexes"),
    ("M06", "Storing Entities and Relationships", "batch MERGE, UNWIND, driver session"),
    ("M07", "Knowledge Graph RAG", "entity linking, k-hop subgraph, hybrid retrieval"),
    ("M08", "Conclusion", "production deployment, decision criteria, capstone"),
]

STAGE_DEPS = OrderedDict([
    ("ingest", []),
    ("normalize", ["ingest"]),
    ("chunk", ["normalize"]),
    ("extract", ["chunk"]),
    ("resolve", ["extract"]),
    ("merge_dedup", ["resolve"]),
    ("graph_write", ["merge_dedup"]),
    ("entity_link", []),
    ("retrieve", ["entity_link", "graph_write"]),
    ("serialize", ["retrieve"]),
    ("generate", ["serialize"]),
])


def topological_order(stage_deps):
    remaining = list(stage_deps.keys())
    order = []
    while remaining:
        progressed = False
        for name in list(remaining):
            if all(dep in order for dep in stage_deps[name]):
                order.append(name)
                remaining.remove(name)
                progressed = True
        if not progressed:
            raise ValueError("cycle detected in stage dependencies")
    return order


order = topological_order(STAGE_DEPS)
print("ingestion + retrieval order: " + " -> ".join(order))
for module_id, title, focus in MODULE_MAP:
    print(f"  {module_id}  {title:<42} {focus}")
position = {name: index for index, name in enumerate(order)}
for name, deps in STAGE_DEPS.items():
    for dep in deps:
        assert position[dep] < position[name], (name, dep)
print("prerequisite check: every stage runs after all of its dependencies")
```

Output —

```text
ingestion + retrieval order: ingest -> normalize -> chunk -> extract -> resolve -> merge_dedup -> graph_write -> entity_link -> retrieve -> serialize -> generate
  M00  Getting Started                            course architecture, RAG basics, GraphRAG path
  M01  Traditional NER and Relation Extraction    BIO tagging, gazetteer, P/R/F1
  M02  LLM Entity and Relation Extraction         extraction prompt, JSON schema, resolution
  M03  Chunking at Scale                          chunk size, overlap, map-reduce, idempotency
  M04  Project: Knowledge Graph from Text         end-to-end ingestion, provenance, export
  M05  Neo4j Introduction                         Property Graph, Cypher, constraints, indexes
  M06  Storing Entities and Relationships         batch MERGE, UNWIND, driver session
  M07  Knowledge Graph RAG                        entity linking, k-hop subgraph, hybrid retrieval
  M08  Conclusion                                 production deployment, decision criteria, capstone
prerequisite check: every stage runs after all of its dependencies
```

---

## 10. ရလဒ်ကို ပြန်ကြည့်ခြင်း

| စစ်ဆေးချက် | Code | ရလဒ် |
| --- | --- | --- |
| Order သည် `ingest` မှ စသည် | `order[0] == "ingest"` | `True` |
| Order သည် `generate` ဖြင့် ဆုံး | `order[-1] == "generate"` | `True` |
| Stage အားလုံး ပါဝင် | `len(order) == len(STAGE_DEPS)` | `11 == 11` |
| Prerequisite အရင် ရှိသည် | `position[dep] < position[name]` | `assert` အောင်သည် |
| Module map အရေအတွက် | `len(MODULE_MAP) == 9` | `True` |

`entity_link` က prerequisite `[]` ရှိသောကြောင့် `ingest` နှင့်တွဲပြီး အစောပိုင်းတွင် ရွေးခံရသည်။
၎င်းသည် ingestion-side နှင့် retrieval-side **သီးခြား စနိုင်သည်** ဆိုသည်ကို ပြသည်။
Incremental update တွင် ဤအချက်က အရေးကြီးသည် — graph_write မပြန်လုပ်ဘဲ
retrieval-side ကို re-run နိုင်သည်။

---

## 11. ကိုယ်တိုင်လေ့ကျင့်ကြည့်ပါ

**မေးခွန်း** — အောက်ပါ code က ဘယ်ရလဒ် ပြန်ပေးမလဲ။

```python
def topological_order(stage_deps):
    remaining = list(stage_deps.keys())
    order = []
    while remaining:
        progressed = False
        for name in list(remaining):
            if all(dep in order for dep in stage_deps[name]):
                order.append(name)
                remaining.remove(name)
                progressed = True
        if not progressed:
            raise ValueError("cycle detected in stage dependencies")
    return order


DEPS = {"ingest": [], "entity_link": []}
print(topological_order(DEPS))
```

1. `['ingest']` — ပထမဆုံး prerequisite မရှိသည့် stage သာ
2. `['ingest', 'entity_link']` — prerequisite မရှိသည့် stage နှစ်ခုလုံး
3. `ValueError` — cycle ဖြစ်သည်
4. `[]` — ဘယ် stage မှ ရွေး၍ မရ

<details>
<summary>အဖြေ ကြည့်ရန်</summary>

**အဖြေ — 2. `['ingest', 'entity_link']`**

အကြောင်းရင်း — `ingest` နှင့် `entity_link` နှစ်ခုလုံးတွင် prerequisite list က အလွတ်
`[]` ဖြစ်သည်။ Round 1 တွင် `for name in list(remaining)` က `ingest` ကို အရင်စစ်သည် —
`all(dep in order for dep in [])` က **vacuous truth** ဖြင့် `True` ပြန်သဖြင့် `ingest`
ရွေးခံရသည်။ ဆက်ပြီး `entity_link` ကိုလည်း စစ်ရာ `[]` ဖြစ်သောကြောင့် `True` ပြန်သဖြင့်
ရွေးခံရသည်။ ထို့ကြောင့် order သည် `['ingest', 'entity_link']` ဖြစ်သည်။

`[]` အတွက် `all()` က `False` ပြန်ခဲ့လျှင် `progressed` က `False` ဖြစ်ပြီး `ValueError`
ရမည် — သို့သော် တကယ်တွင် `all()` က `True` ပြန်သဖြင့် cycle အမှား မဖြစ်ပါ။

</details>

---

**အဓိက မှတ်ထားရန်** — Pipeline ကို DAG အဖြစ် ဖော်ပြခြင်းဖြင့် stage အသစ်တစ်ခု
ထည့်သည့်အခါ မည်သည့် stage များ ပြန်လည် run ရမည်ကို algorithm အရ ဆုံးဖြတ်နိုင်သည်။
`all()` ၏ vacuous truth၊ `while` နှင့် `list(copy)` ကို မှန်ကန်စွာ သုံးနိုင်ရန်
လိုအပ်သည်။ Module တိုင်း၏ lab သည် ဤ DAG ၏ အစိတ်အပိုင်းတစ်ခုကို implement
လုပ်ထားသည်။
