# Walkthrough 01 — Full pipeline recap (Exercise 1)

> ဤဖိုင်သည် Module 08 ၏ `solution.md` ထဲက Exercise 1 ကို **Python အခြေခံမှ စ၍**
> အပိုင်းလိုက် ရှင်းပြသည့် walkthrough ဖြစ်သည်။ Format သည် Module 01 ၏
> `walkthroughs/01_regex_ner.md` နှင့် `walkthroughs/03_gazetteer_lookup.md` နှင့်
> တူညီသည်။

---

## 0. ဤ Exercise က ဘာကို ဖြေရှင်းပေးသလဲ။

Course တစ်ခုလုံးမှာ M00 မှ M08 အထိ stage အများအပြား ရှိပါတယ်။ Stage တိုင်းက သူ့အလုပ်
ပြီးမှ နောက် stage ကို စရပါတယ်။ ဒီအစီအစဉ်ကို မှန်ကန်စွာ သတ်မှတ်ဖို့ လိုပါတယ် —
မဟုတ်ရင် stage တစ်ခုက သူ့ input မရှိသေးဘဲ run မိပါမယ်။

```text
ingest -> normalize -> chunk -> extract -> resolve -> merge_dedup -> graph_write
                                                                       |
                                              entity_link ----------> retrieve
                                                                       |
                                                serialize -> generate <-
```

Ingestion-side (document → graph) နဲ့ retrieval-side (question → answer) ကို ချိတ်ဆက်တဲ့
နေရာက `retrieve` ဖြစ်ပါတယ်။ ဒီ Exercise က stage များကို **DAG** (Directed Acyclic Graph)
အဖြစ် ဖော်ပြပြီး **topological order** — prerequisite အားလုံး ပြီးသွားတဲ့ stage ကို အရင်
ရွေးတဲ့ အစီအစဉ် — ကို ထုတ်ပေးပါတယ်။

ဒီ code မှာ လေ့လာရမယ့် Python concepts တွေကတော့ —

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

`OrderedDict([...])` ကို key-value pair များပါတဲ့ **list of tuples** ကနေ ဆောက်ပါတယ်။
`("ingest", [])` ဆိုတာ `"ingest"` key နဲ့ အလွတ် list `[]` value ဖြစ်ပါတယ်။

- key = stage အမည်
- value = ထို stage မလုပ်မီ ပြီးရမယ့် stage များ၏ **list** (prerequisite list)

`list(STAGE_DEPS)` က key များကို သူတို့ ထည့်ထားတဲ့ အစီအစဉ်အတိုင်း ပြန်ပေးပါတယ်။
Python 3.7 ကတည်းက သာမန် `dict` ကလည်း insertion order ကို ထိန်းပေမဲ့၊ prerequisite
list အစီအစဉ်ကို **တိတိကျကျ** ဖော်ပြလိုတဲ့အတွက် `OrderedDict` ကို သုံးထားတာက
ရည်ရွယ်ချက် ရှိပါတယ် — reader က \"ဒီ order က ရည်ရွယ်ချက်ရှိသည်\" လို့ ဖတ်နိုင်ပါတယ်။

`entity_link` မှာ prerequisite မရှိဘဲ `[]` ရှိတာကို သတိထားပါ။ Ingestion chain နဲ့
မချိတ်ဘဲ သီးခြား စနိုင်တဲ့ stage ဖြစ်လို့ပါ။ `retrieve` ကတော့ `entity_link` နဲ့
`graph_write` **နှစ်ခုလုံး** ကို စောင့်ပါတယ်။

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

နှစ်ခုလုံး key order တူပြီး တန်ဖိုးလည်း တူလို့ `==` က `True` ပြန်ပါတယ်။ ဒါကြောင့်
ဒီ Exercise မှာ `OrderedDict` ကို သုံးတာက **ရည်ရွယ်ချက်ကို ရှင်းလင်းစေသည်** အပေါ်
အကျိုးသက်ရောက်မှုသာ ရှိပါတယ်။

---

## 2. `all()` နှင့် Vacuous Truth

`all(iterable)` က iterable ထဲက item အားလုံး `True` လား စစ်ပါတယ်။ ဒီနေရာမှာ
**generator expression** `(dep in order for dep in deps)` ကို သုံးပါတယ်။

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
| ၁ | `[]` ထဲက item အားလုံး `order` ထဲ ရှိလား | `True` |
| ၂ | `"ingest" in []` ဖြစ်လား | `False` |
| ၃ | `"ingest" in ["ingest"]` ဖြစ်လား | `True` |

ပထမလိုင်း၏ `True` က အရေးကြီးပါတယ်။ **အလွတ် iterable အတွက် `all()` က `True`
ပြန်တယ်** — ဒါကို *vacuous truth* လို့ ခေါ်ပါတယ်။ \"ချိုးဖောက်ထားတဲ့ item တစ်ခုမှ
မရှိ\" ဆိုတဲ့ အဓိပ္ပာယ်ပါ။

ဒီအချက်က `topological_order` အတွက် **မရှိမဖြစ်** လိုအပ်ပါတယ်။ `ingest` နဲ့
`entity_link` က prerequisite `[]` ရှိလို့ သူတို့ကို **ပထမဆုံး** ရွေးနိုင်ပါတယ်။
`all()` က အလွတ် list အတွက် `False` ပြန်ခဲ့ရင် ဘယ် stage မှ စလို့မရဘဲ loop က
ပိတ်မိသွားပါမယ်။

### Generator expression ဆိုတာ ဘာလဲ

`all(...)` ထဲမှာ ကွင်း `()` နဲ့ ရေးထားတဲ့ `dep in order for dep in deps` က
generator expression ဖြစ်ပါတယ်။ List comprehension နဲ့ တူပေမဲ့ item များကို
**တစ်လုံးချင်း လိုအပ်တဲ့အခါမှ** ထုတ်ပေးပါတယ်။

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
`list()` နဲ့ ပြောင်းထားတာ။ ရလဒ် တူပါတယ်။

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

`stage_deps.keys()` က အားလုံး key ကို ပြန်ပေးပါတယ်။ `list(...)` ဖြင့် list အဖြစ်
ပြောင်းထားတာက **နောက်ပိုင်း `remaining.remove(name)` လုပ်နိုင်ရန်** ဖြစ်ပါတယ်။

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

`remove(value)` က list ထဲက **တန်ဖိုးနှင့် ကိုက်သည့် ပထမဆုံး item** ကို ဖယ်ပါတယ်။

### 3.2 `while remaining:` — ဘာကြောင့် `while` လဲ

`remaining` list ထဲ stage ကျန်နေသရွေ့ loop ဆက်လုပ်ပါတယ်။ `while` သုံးတာက
loop အတွင်းမှာပဲ `remaining` ကို item ဖယ်ပြီး **အတိုချုံ့** သွားလို့ပါ။
`for` loop နဲ့ဆို item တစ်ခုချင်း တိုးပြီး ဒီလို ပြင်လို့ အဆင်မပြေပါ။

`while remaining:` သည် `while len(remaining) > 0:` နဲ့ အလုပ်တူပါတယ် — မလွတ် list
က `True`၊ လွတ်သွားရင် `False` ဖြစ်ပါတယ်။

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

Loop အတွင်းမှာ `remaining.remove(name)` ကို ခေါ်ပါတယ်။ ဒါကြောင့် `for` က
`list(remaining)` — **copy တစ်ခု** အပေါ်မှာ loop လုပ်ရပါတယ်။ `remaining` ကိုယ်တိုင်
အပေါ်မှာ loop လုပ်ရင် iteration အတွင်း list ကို ပြင်နေတာမို့ item ကျော်သွားနိုင်ပါတယ်။

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

`if all(dep in order for dep in stage_deps[name]):` သည် true ဖြစ်ရင် — ထို stage ၏
prerequisite အားလုံး `order` ထဲ ရှိပြီးသား — ဒါဆို `order` ထဲ ထည့်ပြီး `remaining`
ကနေ ဖယ်ပါတယ်။

`progressed = True` က \"ဒီ round မှာ အနည်းဆုံး stage တစ်ခု ရွေးနိုင်ခဲ့သည်\" ကို
မှတ်ထားတာပါ။

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

`if not progressed:` က round တစ်ခုလုံးမှာ ဘယ် stage မှ မရွေးနိုင်ရင် `raise` လုပ်ပါတယ်။
`raise ValueError("...")` က exception ကို **ဖန်တီးပစ်** ပါတယ်။ ဒါက infinite loop ကို
တားဆီးပါတယ် — cycle ရှိရင် `remaining` ဘယ်တော့မှ လွတ်မှာ မဟုတ်လို့ loop က
ထာဝရ လည်နေမှာပါ။

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
ရပ်တန့်ပါတယ်။ `try:` block အတွင်း ခေါ်ထားလို့ `except ValueError as exc:` က ဖမ်းပြီး
`exc` ထဲ ထည့်ပါတယ်။ `type(exc).__name__` က class အမည် `ValueError` ကို ပြန်ပါတယ်။

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

Round တစ်ခုစီမှာ ဘာ ရွေးနိုင်ခဲ့လဲ ပြန်ကြည့်ရအောင်။ `for name in list(remaining)` က
`remaining` အစီအစဉ်အတိုင်း စစ်ပါတယ်။

| Round | အစပိုင်း `remaining` | ရွေးနိုင်သည့် stage | ရွေးပြီး `order` |
| --- | --- | --- | --- |
| 1 | ingest, normalize, chunk…, entity_link | `ingest`၊ `entity_link` | `[ingest, entity_link]` |
| 2 | normalize, chunk…, retrieve | `normalize` | `[ingest, entity_link, normalize]` |
| 3 | chunk, extract…, retrieve | `chunk` | `…, chunk` |
| နောက်ဆုံး | `generate` သာ ကျန် | `generate` | `generate` ဖြင့် ဆုံး |

Order ၏ **ဖော်ပြအစီအစဉ်** က round အတွင်း `remaining` အစီအစဉ်အပေါ် မူတည်ပါတယ်
(ဥပမာ `ingest` နဲ့ `entity_link` နှစ်ခုလုံး round 1 မှာ ရွေးခံရသည်)။ သို့သော်
**prerequisite စည်းမျဉ်း** (dependent အရင် ရှိရမည်) ကို ချိုးဖောက်တာ မရှိပါ။

---

## 6. `position` — Dict Comprehension နှင့် `enumerate()`

Order ရလာပြီးရင် stage တိုင်း၏ **နေရာ (index)** ကို မှတ်ထားဖို့ လိုပါတယ်။

```python
order = ["ingest", "normalize", "chunk", "extract"]
position = {name: index for index, name in enumerate(order)}
print(position)
```

Output —

```text
{'ingest': 0, 'normalize': 1, 'chunk': 2, 'extract': 3}
```

`enumerate(order)` က `(index, value)` tuple များကို ပြန်ပါတယ်။

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

`{name: index for index, name in enumerate(order)}` ဆိုတာ **dict comprehension** ဖြစ်ပါတယ်။
`enumerate` က `(0, "ingest")` လို tuple ပေးတဲ့အခါ `index, name` လို့ **tuple unpacking**
နဲ့ ခွဲယူပါတယ်။ List comprehension လိုပဲ ဒါက for loop တစ်ခုကို တစ်လိုင်းတည်း
ရေးတာပါ။

Dictionary ကို index အဖြင့် ပြန်ဖတ်ရင် prerequisite check က **အလွန်လွယ်** ပါတယ် —

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

`position[dep] < position[name]` ကို `assert` နဲ့ စစ်လိုက်ရင် — prerequisite တိုင်းက
dependent stage အရင် နေရာရကြောင်း **တိတိကျကျ** သက်သေပြပါတယ်။

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
ဆက်စပ်ပေးပါတယ်။ `join` က **string method** ဖြစ်ပြီး list ကို argument အဖြစ်
လက်ခံပါတယ်။

```python
print(" -> ".join(["ingest"]))
print(" -> ".join([]))
```

Output —

```text
ingest

```

item တစ်ခုတည်းရင် separator မပါဘဲ ထို item သာ ရပါတယ်။ အလွတ် list အတွက်
empty string `""` ရပါတယ် (အပေါ်က ဒုတိယလိုင်းက ဗလာလိုင်း ဖြစ်သည်)။

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

`MODULE_MAP` ထဲက tuple တိုင်းမှာ `(module_id, title, focus)` သုံးခု ပါပါတယ်။
`for a, b, c in list_of_tuples:` လို့ ရေးရင် tuple တိုင်းကို **unpack** လုပ်ပြီး loop
ပါတယ်။ `M04` က project module ဖြစ်ကြောင်း ဖော်ပြဖို့ map ထဲ အပြည့်အစုံ ကိုးခု ရှိပါတယ်။

### `:<42` alignment spec

f-string ထဲက `{title:<42}` က `title` ကို **ဘယ်ဘက်ချိန်** ပြီး **အနည်းဆုံး 42
character ကျယ်အောင်** ဖြည့်ပါတယ်။ `<` က left-align၊ `42` က field width ပါ။

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

`"M01"` (၃ လုံး) ကို width 5 ဖြည့်လို့ `"M01  "` (၅ လုံး) ဖြစ်ပါတယ်။ `"Conclusion"`
(၁၀ လုံး) က width 12 ဖြည့်လို့ နောက်မှာ space နှစ်လုံး ပါပါတယ်။ `len(...)` က 5
ပြန်တာက field width ပြည့်ပြီးကြောင်း အတည်ပြုပါတယ်။

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

`entity_link` က prerequisite `[]` ရှိလို့ `ingest` နဲ့တွဲပြီး အစောပိုင်းမှာ ရွေးခံရပါတယ်။
ဒါက ingestion-side နဲ့ retrieval-side သည် **သီးခြား စနိုင်သည်** ဆိုတာကို ပြပါတယ်။
Incremental update မှာ ဒီအချက်က အရေးကြီးပါတယ် — graph_write မပြန်လုပ်ဘဲ
retrieval-side ကို re-run နိုင်ပါတယ်။

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
4. `[]` — ဘယ် stage မှ ရွေးလို့မရ

<details>
<summary>အဖြေ ကြည့်ရန်</summary>

**အဖြေ — 2. `['ingest', 'entity_link']`**

အကြောင်းရင်း — `ingest` နှင့် `entity_link` နှစ်ခုလုံးတွင် prerequisite list က အလွတ်
`[]` ဖြစ်သည်။ Round 1 တွင် `for name in list(remaining)` က `ingest` ကို အရင်စစ်သည် —
`all(dep in order for dep in [])` က **vacuous truth** ဖြင့် `True` ပြန်သဖြင့် `ingest`
ရွေးခံရသည်။ ဆက်ပြီး `entity_link` ကိုလည်း စစ်ရာ `[]` မို့ `True` ပြန်သဖြင့်
ရွေးခံရသည်။ ထို့ကြောင့် order မှာ `['ingest', 'entity_link']` ဖြစ်သည်။

`[]` အတွက် `all()` က `False` ပြန်ခဲ့ရင် `progressed` က `False` ဖြစ်ပြီး `ValueError`
ရမည် — သို့သော် တကယ်တွင် `all()` က `True` ပြန်သဖြင့် cycle အမှား မဖြစ်ပါ။

</details>

---

**အဓိက မှတ်ထားရန်** — Pipeline ကို DAG အဖြစ် ဖော်ပြခြင်းဖြင့် stage အသစ်တစ်ခု
ထည့်တဲ့အခါ မည်သည့် stage များ ပြန်လည် run ရမည်ကို algorithm အရ ဆုံးဖြတ်နိုင်ပါတယ်။
`all()` ၏ vacuous truth၊ `while` နဲ့ `list(copy)` ကို မှန်ကန်စွာ သုံးနိုင်ဖို့
လိုပါတယ်။ Module တိုင်း၏ lab သည် ဤ DAG ၏ အစိတ်အပိုင်းတစ်ခုကို implement
လုပ်ထားပါတယ်။
