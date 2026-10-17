# Walkthrough 01 — Triple → Cypher batch generator (`UNWIND`) (Exercise 1)

> ဤဖိုင်သည် Module 06 ၏ `solution.md` ထဲက Exercise 1 ကို **Python အခြေခံမှ စ၍**
> အပိုင်းလိုက် ရှင်းပြသည့် walkthrough ဖြစ်သည်။ Code နှင့် output များသည်
> `modules/06_storing_entities_relationships_neo4j/lab.py` ကို run ၍ ရရှိသည့်
> အမှန်တကယ် ရလဒ်များ ဖြစ်သည်။

---

## 0. ဤ Exercise က ဘာကို ဖြေရှင်းပေးသလဲ။

LLM က text ထဲမှ triple ၆ ခုကို ဆွဲထုတ်ပြီးရင် ထို triple များကို Neo4j ထဲ ရေးသွင်းရသည်။
အရိုးရှင်းဆုံး နည်းလမ်းမှာ triple တစ်ခုလျှင် Cypher statement တစ်ခု ပို့ခြင်းဖြစ်သည် —
triple ၆ ခုအတွက် round-trip ၆ ကြိမ်။ Triple ၁ သန်းဆိုလျှင် round-trip ၁ သန်း ဖြစ်သည်။

```text
triple c01  (Ada, WORKED_AT, Project)     -> network round-trip 1 -> 1 transaction
triple c01  (Ada, USES, Engine)           -> network round-trip 2 -> 1 transaction
triple c02  (Babbage, FOUNDED, Project)   -> network round-trip 3 -> 1 transaction
triple c03  (Project, LOCATED_IN, London) -> network round-trip 4 -> 1 transaction
...
```

ဤ Exercise က triple များကို **(head label, relationship type, tail label)** အလိုက် group ဖွဲ့ပြီး
group တိုင်းအတွက် `UNWIND $rows AS row` batch statement **တစ်ခုတည်း** ဖန်တီးပေးသည့်
`build_batch_statements()` ကို တည်ဆောက်သည်။ Tuple တူသော triple များကို row အဖြစ်
စုစည်းလိုက်ခြင်းဖြင့် round-trip အရေအတွက်သည် **triple အရေအတွက်မှ distinct group
အရေအတွက်သို့** ကျဆင်းသည်။

Code block တစ်ခုတည်းထဲ label နှင့် relationship type ကို `str.format` ဖြင့် ထည့်ရသည်မှာ
အရေးကြီးသည် — Cypher သည် label နှင့် relationship type အတွက် parameter substitution ကို
မထောက်ပံ့ပါ။ ထို့ကြောင့် ၎င်းတို့ကို **allowlist mapping** မှသာ interpolate လုပ်သည်; value
အားလုံး (name၊ id၊ chunk_id၊ confidence) မှာ `$rows` parameter ဖြင့် သွားသည်။

ဤ code တွင် လေ့လာရမည့် Python concepts များမှာ —

- `str.join()` နှင့် conditional expression (`x if cond else y`)
- Generator expression နှင့် list comprehension
- Dictionary နှင့် tuple key
- `collections.OrderedDict` နှင့် `dict.setdefault()`
- Nested tuple unpacking — `for (a, b, c), items in groups.items():`
- `str.format()` နှင့် `{{` `}}` escape

---
## 1. `slug()` — Node id ကို canonical ဖြစ်စေခြင်း
Graph ထဲမှာ entity တစ်ခုကို **တစ်ကြိမ်တည်း** ရေးရန် identity key တစ်ခု လိုသည်။
ဤ Exercise က entity အမည်ကို lowercase ပြောင်းပြီး စာလုံး/ဂဏန်း မဟုတ်သော စာလုံးများကို
`_` ဖြင့် အစားထိုးသည့် `slug()` ကို သုံးသည်။ ဤနည်းဖြင့် `Ada Lovelace` သည်
`ada_lovelace` ဖြစ်သွားပြီး အမည်တွင် space၊ case ကွာခြားခြင်းကြောင့် node နှစ်ခု
ဖြစ်ပေါ်ခြင်းကို ကာကွယ်သည်။

### 1.1 `str.join()` နှင့် conditional expression
```python
print("_".join(["a", "b", "c"]))
print("".join("x" for _ in range(3)))
print("".join(ch if ch.isalnum() else "_" for ch in "Ada Lovelace"))
```

Output —
```text
a_b_c
xxx
Ada_Lovelace
```

`"_".join(list)` သည် list ထဲက စာလုံးများကို `_` ဖြင့် ဆက်ပေးသည်။ `"".join(...)` သည်
ဘယ်စာလုံးမှ မခံဘဲ ကပ်ပေးသည်။ ဒုတိယလိုင်းထဲက `"x" for _ in range(3)` သည်
**generator expression** ဖြစ်သည် — တန်ဖိုး ၃ ခုကို အလိုအလျောက် ထုတ်ပေးပြီး `join()`
က စားသည်။ `_` သည် "ဒီတန်ဖိုးကို သုံးမည် မဟုတ်" ဟု ဆိုလိုသည့် သမားရိုးကျ အမည်ဖြစ်သည်။

တတိယလိုင်းက အဓိကအပိုင်း ဖြစ်သည် —

```python
ch if ch.isalnum() else "_"
```

ဤသည်မှာ **conditional expression** ဖြစ်သည်။ `ch` သည် စာလုံး/ဂဏန်း ဖြစ်လျှင် `ch`
ကို ပြန်ပေးပြီး၊ မဟုတ်လျှင် `"_"` ကို ပြန်ပေးသည်။ `for ch in "Ada Lovelace"` က
စာလုံးတစ်လုံးချင်းဖြင့် လှည့်သည်။ ထို့ကြောင့် space သည် `_` ဖြစ်သွားသည်။

### 1.2 Function တစ်ခုလုံး
```python
def slug(text):
    """Canonical node id — deterministic, lowercase, ASCII-safe."""
    return "".join(ch if ch.isalnum() else "_" for ch in text.lower()).strip("_")

for name in ["Ada Lovelace", "Analytical Engine Project", "C++", "  London  "]:
    print("%-26s -> %s" % (name, slug(name)))
```

Output —
```text
Ada Lovelace               -> ada_lovelace
Analytical Engine Project  -> analytical_engine_project
C++                        -> c
  London                   -> london
```

`.strip("_")` သည် အစနှင့် အဆုံးမှ `_` များကို ဖယ်သည်။ `"  London  "` ကဲ့သို့ စာသားတွင်
အစ/အဆုံး space ပါလာလျှင် `__london__` ဖြစ်ပြီးနောက် `london` သို့ ရောက်သည် — node id
အစ/အဆုံးတွင် `_` မကျန်ရန် လိုအပ်သည်။

| Entity အမည် | slug |
| --- | --- |
| `Ada Lovelace` | `ada_lovelace` |
| `Analytical Engine Project` | `analytical_engine_project` |
| `C++` | `c` |
| `  London  ` | `london` |

`C++` သည် `c` သို့ ရောက်သည် — ဤနည်းသည် information ဆုံးရှုံးမှု ရှိသည်။ Entity အမည်
နှစ်ခုသည် slug တူညီသွားနိုင်သည် (ဥပမာ `C++` နှင့် `C#`)။ ထို့ကြောင့် production တွင်
slug ကို **identity key အဖြစ်သာ** သုံးပြီး၊ လူဖတ်ရန် အမည်ကို `name` property အဖြစ်
သီးသန့် သိမ်းသည် (ဤ code တွင် `head_name` / `tail_name` row field များ)။

---
## 2. `ENTITY_TYPE_TO_LABEL` — allowlist mapping
LLM က `head_type` / `tail_type` ကို string အဖြစ် ပြန်ပေးသည်။ ထို string ကို Cypher
label အဖြစ် တိုက်ရိုက် ထည့်လိုက်လျှင် — LLM output ကို ယုံကြည်လိုက်ခြင်း ဖြစ်ပြီး
injection ဖြစ်နိုင်သည်။ ထို့ကြောင့် mapping dict တစ်ခုဖြင့် allowlist လုပ်သည်။
```python
ENTITY_TYPE_TO_LABEL = {"PERSON": "Person", "ORGANIZATION": "Organization",
                        "TECHNOLOGY": "Technology", "LOCATION": "Location"}
print("entity types :", sorted(ENTITY_TYPE_TO_LABEL))
print("node labels  :", sorted(ENTITY_TYPE_TO_LABEL.values()))
print("lookup PERSON:", ENTITY_TYPE_TO_LABEL["PERSON"])

try:
    ENTITY_TYPE_TO_LABEL["COMPANY"]
except KeyError as exc:
    print("new type COMPANY ->", type(exc).__name__, exc)
```

Output —
```text
entity types : ['LOCATION', 'ORGANIZATION', 'PERSON', 'TECHNOLOGY']
node labels  : ['Location', 'Organization', 'Person', 'Technology']
lookup PERSON: Person
new type COMPANY -> KeyError 'COMPANY'
```

`sorted(dict)` သည် dictionary ၏ key များကို စီပြီး list အဖြစ် ပြန်ပေးသည်။ မသိသော type
တစ်ခု ဝင်လာလျှင် `ENTITY_TYPE_TO_LABEL["COMPANY"]` သည် `KeyError` ဖြစ်စေသည် — ဤသည်မှာ
**fail-fast** အပြုအမူ ဖြစ်သည်။ Unmapped type ကို ကျော်လွှတ်လိုက်ခြင်းထက် error ဖြစ်ခြင်းက
data loss ကို ဖော်ထုတ်ပေးသည်။ Production တွင် ဤ error ကို catch လုပ်ပြီး extraction
record ကို quarantine လုပ်ရသည်။

---
## 3. `TRIPLES` — input data (list of dict)
Input သည် list တစ်ခုဖြစ်ပြီး အဖွဲ့ဝင်တိုင်းသည် dictionary ဖြစ်သည်။ Dictionary ကို
field အမည်ဖြင့် ဖတ်သည်။ Triple တစ်ခုစီတွင် `chunk_id` (provenance) နှင့် `confidence`
ပါဝင်သည် — ဤနှစ်ခုသည် နောက်ပိုင်း relationship identity တွင် အသုံးဝင်သည်။
```python
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
print("triples :", len(TRIPLES))
for t in TRIPLES:
    print("  %-24s %-18s %-24s chunk=%s conf=%.2f"
          % (t["head"], t["rel"], t["tail"], t["chunk_id"], t["confidence"]))
```

Output —
```text
triples : 6
  Ada Lovelace             WORKED_AT          Analytical Engine Project chunk=c01 conf=0.93
  Ada Lovelace             USES               Analytical Engine        chunk=c01 conf=0.88
  Charles Babbage          FOUNDED            Analytical Engine Project chunk=c02 conf=0.91
  Analytical Engine Project LOCATED_IN         London                   chunk=c03 conf=0.76
  Ada Lovelace             COLLABORATED_WITH  Charles Babbage          chunk=c02 conf=0.84
  Ada Lovelace             WORKED_AT          Analytical Engine Project chunk=c04 conf=0.79
```

`t1` နှင့် `t6` သည် head၊ tail၊ type၊ rel အားလုံး တူညီပြီး `chunk_id` သာ ကွာသည်
(`c01` နှင့် `c04`)။ ဤနှစ်ခုသည် relationship **နှစ်ခု** ဖြစ်ရမည် — provenance သည် edge
identity ၏ အစိတ်အပိုင်း ဖြစ်သည်။ မတူညီသော chunk များမှ ထောက်ခံချက် နှစ်ခု ရှိခြင်းသည်
evidence နှစ်ခု ရှိခြင်း ဖြစ်သည်; ပေါင်းပစ်လိုက်လျှင် ဤအချက်ကို ဆုံးရှုံးမည်။

---
## 4. `OrderedDict` နှင့် `setdefault()` ဖြင့် group ဖွဲ့ခြင်း
Group ဖွဲ့သည့် pattern သည် "dict ထဲတွင် list စုခြင်း" ဖြစ်သည်။ `setdefault(key, [])`
သည် key မရှိလျှင် `[]` ထည့်ပြီး၊ ထို list ကို ပြန်ပေးသည်; key ရှိပြီးသားဖြစ်လျှင် ရှိပြီးသား
list ကို ပြန်ပေးသည်။ ထို့နောက် `.append()` လုပ်သည်။
```python
from collections import OrderedDict

groups = OrderedDict()
for word in ["apple", "avocado", "banana", "blueberry"]:
    groups.setdefault(word[0], []).append(word)

print(groups)
print(dict(groups))
print(sorted(groups))
```

Output —
```text
OrderedDict({'a': ['apple', 'avocado'], 'b': ['banana', 'blueberry']})
{'a': ['apple', 'avocado'], 'b': ['banana', 'blueberry']}
['a', 'b']
```

`OrderedDict` နှင့် သာမန် `dict` နှစ်ခုလုံး ထည့်သည့် အစီအစဉ်ကို ထိန်းသည် (CPython 3.7
နောက်ပိုင်း)။ `OrderedDict` ကို သုံးထားသည်မှာ **စာဖတ်သူအတွက် ရည်ရွယ်ချက် အတိအလင်း**
ဖြစ်သည် — group အစီအစဉ်သည် deterministic ဖြစ်ရမည်၊ မဟုတ်လျှင် output သည် run တစ်ခုနှင့်
တစ်ခု မတူပါ။

### 4.1 Triple များကို group ဖွဲ့ခြင်း
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

groups = OrderedDict()
for t in TRIPLES:
    key = (ENTITY_TYPE_TO_LABEL[t["head_type"]], t["rel"],
           ENTITY_TYPE_TO_LABEL[t["tail_type"]])
    groups.setdefault(key, []).append(t)

print("distinct groups :", len(groups))
for key, items in groups.items():
    print("  %-42s rows=%d" % ("->".join(key), len(items)))
print("row total       :", sum(len(v) for v in groups.values()))
```

Output —
```text
distinct groups : 5
  Person->WORKED_AT->Organization            rows=2
  Person->USES->Technology                   rows=1
  Person->FOUNDED->Organization              rows=1
  Organization->LOCATED_IN->Location         rows=1
  Person->COLLABORATED_WITH->Person          rows=1
row total       : 6
```

Key သည် **tuple** ဖြစ်သည် — `("Person", "WORKED_AT", "Organization")`။ Tuple သည်
immutable ဖြစ်သဖြင့် dict key အဖြစ် သုံးနိုင်သည် (list ကို key အဖြစ် သုံးလျှင်
`TypeError: unhashable type: 'list'` ဖြစ်သည်)။ `"->".join(key)` သည် tuple ၏
အဖွဲ့ဝင် string သုံးခုကို `->` ဖြင့် ဆက်ပေးသည်။

Group အရေအတွက်သည် **၅** ဖြစ်ပြီး row စုစုပေါင်းသည် **၆** ဖြစ်သည်။ နောက်ဆုံးလိုင်းက
ဤအချက်ကို စစ်ပေးသည် — group ဖွဲ့ခြင်းသည် triple တစ်ခုကိုမှ မပျောက်စေရပါ။

---
## 5. `rows` — List comprehension ဖြင့် `$rows` payload ဖန်တီးခြင်း
Cypher ထဲ `$rows` အဖြစ် ပို့မည့် payload သည် **list of dict** ဖြစ်ရသည်။ Dictionary
တစ်ခုစီသည် `UNWIND` လုပ်ပြီးနောက် row တစ်ခု ဖြစ်လာသည်။ List comprehension ဖြင့်
triple တစ်ခုချင်းစီကို row အဖြစ် ပြောင်းသည်။
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

groups = OrderedDict()
for t in TRIPLES:
    key = (ENTITY_TYPE_TO_LABEL[t["head_type"]], t["rel"],
           ENTITY_TYPE_TO_LABEL[t["tail_type"]])
    groups.setdefault(key, []).append(t)

key, items = next(iter(groups.items()))
print("first group :", "->".join(key))
rows = [OrderedDict([("head_id", slug(t["head"])),
                     ("head_name", t["head"]),
                     ("tail_id", slug(t["tail"])),
                     ("tail_name", t["tail"]),
                     ("chunk_id", t["chunk_id"]),
                     ("confidence", t["confidence"])]) for t in items]
print("row count   :", len(rows))
print(rows[0])
for row in rows:
    print("  head_id=%-18s tail_id=%-26s chunk=%s conf=%.2f"
          % (row["head_id"], row["tail_id"], row["chunk_id"], row["confidence"]))
```

Output —
```text
first group : Person->WORKED_AT->Organization
row count   : 2
OrderedDict({'head_id': 'ada_lovelace', 'head_name': 'Ada Lovelace', 'tail_id': 'analytical_engine_project', 'tail_name': 'Analytical Engine Project', 'chunk_id': 'c01', 'confidence': 0.93})
  head_id=ada_lovelace       tail_id=analytical_engine_project  chunk=c01 conf=0.93
  head_id=ada_lovelace       tail_id=analytical_engine_project  chunk=c04 conf=0.79
```

ဖတ်ရန် အပိုင်းများ —

- `OrderedDict([("head_id", slug(t["head"])), ...])` — `OrderedDict` ကို `(key, value)`
  tuple များ၏ list ဖြင့် တည်ဆောက်သည်။ Row field အစီအစဉ်သည် deterministic ဖြစ်သည်။
- `[ ... for t in items]` — **list comprehension**။ `items` ထဲက triple တိုင်းအတွက်
  စာလုံးတစ်လုံး ထုတ်ပေးသည်။ ပုံမှန် loop ဖြင့် ရေးလျှင် —

```python
rows = []
for t in items:
    rows.append(OrderedDict([("head_id", slug(t["head"])), ("head_name", t["head"]),
                             ("tail_id", slug(t["tail"])), ("tail_name", t["tail"]),
                             ("chunk_id", t["chunk_id"]),
                             ("confidence", t["confidence"])]))
```

ရည်ရွယ်ချက် တူညီသည်။

`head_id` သည် ရှာဖွေရန်/merge လုပ်ရန် key ဖြစ်ပြီး `head_name` သည် လူဖတ်ရန် အမည်
ဖြစ်သည်။ နှစ်ခုကို ခွဲထားခြင်းသည် identity နှင့် display ကို ကွဲကွဲစွာ ထားရှိစေသည်။

---
## 6. Cypher ကို `str.format` ဖြင့် တည်ဆောက်ခြင်း — `{{` `}}` escape
Statement ထဲတွင် အစားထိုးလိုသည့် အပိုင်း ၃ ခုသာ ရှိသည် — `{hl}`, `{tl}`, `{rel}`။
Cypher syntax ၏ `{id: row.head_id}` ကဲ့သို့ curly brace များကို `str.format` က
placeholder အဖြစ် ဖတ်သည်။ ထို့ကြောင့် ၎င်းတို့ကို `{{` `}}` ဖြင့် escape လုပ်ရသည်။
```python
template = "MERGE (h:{hl} {{id: row.head_id}}) ON CREATE SET h.name = row.head_name"
print(template.format(hl="Person"))
print("%s" % template)

try:
    print("MERGE (h:{hl} {id: row.head_id})".format(hl="Person"))
except Exception as exc:
    print("unescaped braces -> %s: %s" % (type(exc).__name__, exc))
```

Output —
```text
MERGE (h:Person {id: row.head_id}) ON CREATE SET h.name = row.head_name
MERGE (h:{hl} {{id: row.head_id}}) ON CREATE SET h.name = row.head_name
unescaped braces -> KeyError: 'id'
```

ပထမလိုင်းက `{{` `}}` ကို `{` `}` အဖြစ် ပြန်ထုတ်ပေးသည် — Cypher အတွက် မှန်ကန်သည်။
ဒုတိယလိုင်းက escape မလုပ်ထားသော string ကို `%s` ဖြင့် ရိုးရိုး print လုပ်ခြင်းဖြစ်သည် —
`.`format()` မခေါ်သဖြင့် error မဖြစ်ပါ။ တတိယလိုင်းက escape မလုပ်ဘဲ `.format()` ခေါ်ခြင်းဖြစ်သည် —
`{id: ...}` ကို field အမည် `id: ...` အဖြစ် ဖတ်ပြီး `KeyError` ဖြစ်သည်။

ဤအချက်သည် `str.format` နှင့် Cypher ကို တွဲသုံးသည့်အခါ အဖြစ်များသော error ဖြစ်သည်။
ဖတ်ရလွယ်စေရန် option တစ်ခုမှာ placeholder အမည်များကို format လုပ်ပြီးမှ နောက်ဆုံးအဆင့်တွင်
တစ်ခါတည်း စစ်ဆေးခြင်းဖြစ်သည် (ဤ code က `assert` များဖြင့် လုပ်သည်)။

### 6.1 Group တစ်ခုအတွက် ထွက်လာသည့် Statement
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

statements = build_batch_statements(TRIPLES)
print(statements[0]["cypher"])
```

Output —
```text
UNWIND $rows AS row
MERGE (h:Person {id: row.head_id})
  ON CREATE SET h.name = row.head_name
MERGE (t:Organization {id: row.tail_id})
  ON CREATE SET t.name = row.tail_name
MERGE (h)-[r:WORKED_AT {chunk_id: row.chunk_id}]->(t)
  ON CREATE SET r.confidence = row.confidence
  ON MATCH SET r.confidence = row.confidence
```

ထိုအပိုင်းကို Cypher အဖြစ် ဖတ်ရှုရန် —
```cypher
UNWIND $rows AS row
MERGE (h:Person {id: row.head_id})
  ON CREATE SET h.name = row.head_name
MERGE (t:Organization {id: row.tail_id})
  ON CREATE SET t.name = row.tail_name
MERGE (h)-[r:WORKED_AT {chunk_id: row.chunk_id}]->(t)
  ON CREATE SET r.confidence = row.confidence
  ON MATCH SET r.confidence = row.confidence
```

လိုင်းတိုင်း၏ အဓိပ္ပာယ် —

| လိုင်း | အဓိပ္ပာယ် |
| --- | --- |
| `UNWIND $rows AS row` | `$rows` list ကို row တစ်ခုချင်း ခွဲထုတ်သည် |
| `MERGE (h:Person {id: row.head_id})` | row ၏ head_id ဖြင့် node ရှာသည်; မရှိလျှင် ဖန်တီးသည် |
| `ON CREATE SET h.name = row.head_name` | node အသစ် ဖြစ်မှသာ `name` ထည့်သည် |
| `MERGE (t:Organization {id: row.tail_id})` | tail node အတွက် အလားတူ |
| `MERGE (h)-[r:WORKED_AT {chunk_id: row.chunk_id}]->(t)` | relationship ကို chunk_id အပါအဝင် ရှာသည်/ဖန်တီးသည် |
| `ON CREATE SET r.confidence = row.confidence` | edge အသစ်အတွက် confidence |
| `ON MATCH SET r.confidence = row.confidence` | edge ရှိပြီးသားဖြစ်လျှင် confidence ကို update |

`MERGE (h)-[r:...]->(t)` ကို `MATCH` မလုပ်ဘဲ တိုက်ရိုက် ရေးထားသည်မှာ `h` နှင့် `t` ကို
လိုင်း ၂ နှင့် ၄ က binding လုပ်ပြီးသား ဖြစ်သောကြောင့် ဖြစ်သည်။ **binding မရှိသော
variable များဖြင့် `MERGE (a)-[:R]->(b)` ရေးလျှင် Neo4j သည် label မရှိသော node အသစ်
နှစ်ခုကို အလိုအလျောက် ဖန်တီးသည်** — ဤအချက်ကို Walkthrough 02 တွင် ရှင်းလင်းစွာ ပြထားသည်။

---
## 7. `build_batch_statements()` — Function တစ်ခုလုံး
Function ကို အပိုင်း ၄ ပိုင်း ခွဲဖတ်ပါ —

1. `groups = OrderedDict()` — ရလဒ် သိမ်းမည့် container အလွတ်။
2. `for t in triples:` — key တည်ဆောက်ပြီး `setdefault(key, []).append(t)`။
   ဤ loop ပြီးလျှင် triple တိုင်းသည် group တစ်ခုခုထဲ ရောက်ပြီး ဖြစ်သည်။
3. `for (head_label, rel_type, tail_label), items in groups.items():` — **nested tuple
   unpacking**။ `groups.items()` က `(key, value)` ပေး; `key` ကို tuple ၃ ခုအဖြစ်
   ဆက်ခွဲသည်။ `items` က အဲဒီ group ၏ triple list ဖြစ်သည်။
4. `statements.append({...})` — statement တစ်ခုကို dict အဖြစ် သိမ်းသည် —
   `group` (tuple)၊ `cypher` (string)၊ `rows` (list of dict)။
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

statements = build_batch_statements(TRIPLES)
print("triples=%d  batch statements=%d" % (len(TRIPLES), len(statements)))
for st in statements:
    print("  group=%-42s rows=%d" % ("->".join(st["group"]), len(st["rows"])))
```

Output —
```text
triples=6  batch statements=5
  group=Person->WORKED_AT->Organization            rows=2
  group=Person->USES->Technology                   rows=1
  group=Person->FOUNDED->Organization              rows=1
  group=Organization->LOCATED_IN->Location         rows=1
  group=Person->COLLABORATED_WITH->Person          rows=1
```

Statement တစ်ခုစီသည် dict ဖြစ်သဖြင့် နောက်ပိုင်း driver call တွင်
`session.run(st["cypher"], rows=st["rows"])` လို့ တိုက်ရိုက် သုံးနိုင်သည် (Walkthrough 06)။
`group` ကို သိမ်းထားခြင်းသည် မည့်သည် batch မည်သည့် label/type အတွက် ဖြစ်သည်ကို
log တွင် ပြရန် ဖြစ်သည်။

---
## 8. ရလဒ် — Group တိုင်း၏ batch
Triple ၆ ခုမှ statement ၅ ခု ထွက်သည်။ Group တိုင်း၏ အခြေအနေကို ဇယားဖြင့် ဖော်ပြသည်
(ဤတန်ဖိုးများသည် အထက်က run ၏ အမှန်တကယ် ရလဒ် ဖြစ်သည်) —

| # | Group (head→rel→tail) | rows | ပါဝင်သော node id များ |
| --- | --- | --- | --- |
| 1 | `Person->WORKED_AT->Organization` | 2 | `ada_lovelace`, `analytical_engine_project` |
| 2 | `Person->USES->Technology` | 1 | `ada_lovelace`, `analytical_engine` |
| 3 | `Person->FOUNDED->Organization` | 1 | `analytical_engine_project`, `charles_babbage` |
| 4 | `Organization->LOCATED_IN->Location` | 1 | `analytical_engine_project`, `london` |
| 5 | `Person->COLLABORATED_WITH->Person` | 1 | `ada_lovelace`, `charles_babbage` |

`WORKED_AT` group တစ်ခုတည်းတွင် row ၂ ခု ရှိသည် — `c01` နှင့် `c04`။ ၎င်းတို့သည်
head/tail တူညီသော်လည်း `chunk_id` ကွာသဖြင့် relationship နှစ်ခု ဖြစ်လာမည်။
Statement အရေအတွက်သည် ၅ ဖြစ်ပြီး per-triple နည်းလမ်း၏ ၆ ထက် နည်းသည် — ဤ
module ၏ sample သေးငယ်သည့်အတွက် ကွာခြားချက် ၁ ခုသာ ဖြစ်သည်; triple သောင်းနှင့်ချီ
ဆိုလျှင် group အရေအတွက်သည် label-pair အရေအတွက်အထိ ကျဆင်းသည်။

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

statements = build_batch_statements(TRIPLES)
print("triples=%d  batch statements=%d" % (len(TRIPLES), len(statements)))
for st in statements:
    print("  group=%-42s rows=%d" % ("->".join(st["group"]), len(st["rows"])))
```

Output —
```text
triples=6  batch statements=5
  group=Person->WORKED_AT->Organization            rows=2
  group=Person->USES->Technology                   rows=1
  group=Person->FOUNDED->Organization              rows=1
  group=Organization->LOCATED_IN->Location         rows=1
  group=Person->COLLABORATED_WITH->Person          rows=1
```

---
## 10. ကိုယ်တိုင်လေ့ကျင့်ကြည့်ပါ

**မေးခွန်း** — အောက်ပါ triple နှစ်ခုသည် head type၊ rel၊ tail type အားလုံး တူညီသည်
(`chunk_id` သာ ကွာသည်)။ `build_batch_statements()` က statement မည်မျှ ပြန်ပေးမည်၊
ထို statement ထဲတွင် row မည်မျှ ပါမည်နည်း။
```python
from collections import OrderedDict

ENTITY_TYPE_TO_LABEL = {"PERSON": "Person", "ORGANIZATION": "Organization",
                        "TECHNOLOGY": "Technology", "LOCATION": "Location"}

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

two_triples = [
    {"head": "Ada Lovelace", "head_type": "PERSON", "rel": "WORKED_AT",
     "tail": "Analytical Engine Project", "tail_type": "ORGANIZATION",
     "chunk_id": "c01", "confidence": 0.93},
    {"head": "Charles Babbage", "head_type": "PERSON", "rel": "WORKED_AT",
     "tail": "Analytical Engine Project", "tail_type": "ORGANIZATION",
     "chunk_id": "c02", "confidence": 0.91},
]
statements = build_batch_statements(two_triples)
print("statements =", len(statements))
print("rows in the single statement =", len(statements[0]["rows"]))
```

1. statement ၂ ခု၊ တစ်ခုစီတွင် row ၁ ခု
2. statement ၁ ခု၊ row ၂ ခု
3. statement ၁ ခု၊ row ၁ ခု — `chunk_id` မတူသော row များကို dedupe လုပ်သည်
4. `KeyError` ဖြစ်သည်

<details>
<summary>အဖြေ ကြည့်ရန်</summary>

**အဖြေ — 2. statement ၁ ခု၊ row ၂ ခု**

အကြောင်းရင်း — grouping key သည် `(head label, rel type, tail label)` သာ ဖြစ်သည်;
`chunk_id` သည် key ထဲ မပါပါ။ Triple နှစ်ခုစလုံး key `("Person", "WORKED_AT",
"Organization")` ဆီ ရောက်သဖြင့် list တစ်ခုတည်းထဲ စုပြီး၊ ထို list က row ၂ ခု ဖြစ်လာသည်။
အထက်က run ၏ output က ဤအချက်ကို အတည်ပြုသည် — `statements = 1`၊
`rows in the single statement = 2`။

`chunk_id` သည် relationship identity ၏ အစိတ်အပိုင်း ဖြစ်သည်မှန်သော်လည်း **batch
grouping** ၏ အစိတ်အပိုင်း မဟုတ်ပါ — ၎င်းသည် row field တစ်ခုအဖြစ်သာ ပါဝင်သည်။

</details>

---

**အဓိက မှတ်ထားရန်** — `UNWIND $rows AS row` သည် round-trip အရေအတွက်ကို triple
အရေအတွက်မှ distinct group အရေအတွက်သို့ လျှော့ချသည်။ Label နှင့် relationship type ကို
Cypher parameter အဖြစ် ပို့လို့မရသဖြင့် allowlist mapping မှသာ interpolate လုပ်ရသည်; value
အားလုံးမှာ `$rows` ဖြင့် သွားရသည်။ Batch တစ်ခုတည်းတွင် row အလွန်များလျှင် transaction
memory နှင့် failure recovery cost တိုးလာသည် — ထိုအပိုင်းကို Walkthrough 05 တွင်
တွက်ချက်ထားသည်။
