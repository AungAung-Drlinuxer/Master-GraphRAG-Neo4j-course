# Walkthrough 03 — Data Model Validation (Exercise 3)

> ဤဖိုင်သည် Module 04 ၏ `solution.md` ထဲက Exercise 3 ကို **Python အခြေခံမှ စ၍**
> အပိုင်းလိုက် ရှင်းပြသည့် walkthrough ဖြစ်သည်။

---

## 0. ဤ Exercise က ဘာကို ဖြေရှင်းပေးသလဲ။

Graph ကို Neo4j သို့ မပို့မီ **schema contract** ကို စစ်ရသည်။ Extraction output
သည် open-ended ဖြစ်သည် — pattern အသစ်၊ alias အသစ်၊ typo တစ်ခုသည် label အသစ်တစ်ခု
ဖန်တီးနိုင်သည်။

```text
extraction output (open-ended)
  ("Neo4j", "USES", "cypher")
  ("GraphRAG", "IsA", "Knowledge Graph")     <- predicate case မတူ
  ("Neo4j", "FRIENDS_WITH", "Cypher")        <- whitelist ပြင်ပ

schema contract (closed set)
  NODE_LABELS         = Document | Chunk | Entity
  ALLOWED_ENTITY_TYPES= Technology | Organization | Concept
  ALLOWED_PREDICATES  = IS_A | USES | BUILT_ON | DEVELOPED_BY | INCLUDES | RELATED_TO
  entity_id(canonical) = "ent:" + slug(canonical)     <- deterministic

စစ်ဆေးချက် မအောင်လျှင် Neo4j ထဲ —
  * label အမျိုးအစား အကန့်အသတ်မဲ့ ပေါ်လာပြီး index/constraint အားလုံး အနှောင့်အယှက်ဖြစ်သည်
  * id သည် run တိုင်း ပြောင်းလျှင် MERGE က node အသစ် ထပ်ထည့်သည်
  * query များတွင် label/type အသစ်များအတွက် သီးခြား branch ရေးရသည်
```

ဤ Exercise သည် contract ကို constant အဖြစ် သတ်မှတ်ပြီး **assertion** ဖြင့် စစ်သည်။

ဤ code တွင် လေ့လာရမည့် Python concepts များမှာ —

- Tuple constant နှင့် `in` operator
- `re.sub()` နှင့် `str.lower()`၊ `str.strip()`
- Dict comprehension (`known`)
- `collections.OrderedDict` — အစီအစဉ် ထိန်းသိမ်းသည့် dict
- `collections.defaultdict` နှင့် ၎င်း၏ trap
- `@dataclass` နှင့် `field(default_factory=list)`
- `all()`၊ set comprehension၊ `len(set(...)) == len(...)`
- `assert` နှင့် `try`/`except`
- `sorted(..., key=...)` (`sorted(items)` နှင့် ခြားနားချက်)

---

## 1. Schema contract — constant များ

```python
NODE_LABELS = ("Document", "Chunk", "Entity")
ALLOWED_ENTITY_TYPES = ("Technology", "Organization", "Concept")
ALLOWED_PREDICATES = ("IS_A", "USES", "BUILT_ON", "DEVELOPED_BY", "INCLUDES", "RELATED_TO")

print(len(NODE_LABELS), NODE_LABELS)
print("FRIENDS_WITH" in ALLOWED_PREDICATES)
print("Concept" in ALLOWED_ENTITY_TYPES)
```

Output —

```text
3 ('Document', 'Chunk', 'Entity')
False
True
```

### အဘယ်ကြောင့် tuple ဖြစ်ပြီး အဘယ်ကြောင့် set မဟုတ်သနည်း။

| အမျိုးအစား | အစီအစဉ် | ပြောင်းနိုင်မှု | ဤနေရာတွင် သင့်တော်မှု |
| --- | --- | --- | --- |
| `tuple` | ရှိသည် | မပြောင်းနိုင် | ✓ schema ကို စာရင်းအစဉ်အတိုင်း ဖော်ပြသည် |
| `set` | မရှိ | ပြောင်းနိုင် | ✗ histogram output ၏ အစီအစဉ် မတည်ငြိမ် |
| `list` | ရှိသည် | ပြောင်းနိုင် | ✗ module import အတွင်း မတော်တဆ mutate ဖြစ်နိုင် |

Tuple သည် **frozen** ဖြစ်သည် — module တစ်ခုလုံးတွင် တစ်ခါ သတ်မှတ်ပြီး မည်သည့်နေရာကမှ
မပြောင်းနိုင်ပါ။ Contract တစ်ခုအတွက် ၎င်းသည် အာမခံချက် ဖြစ်သည်။

### `in` operator

`"FRIENDS_WITH" in ALLOWED_PREDICATES` သည် tuple ထဲ ပါ/မပါ စစ်သည်။ Tuple အတွက်
linear scan ဖြစ်သော်လည်း item ခြောက်ခုအတွက် လုံးဝ အရေးမကြီးပါ။ Predicate ရာနှင့်ချီ
လာလျှင် `frozenset` သို့ ပြောင်းရသည် — `in` က O(1) ဖြစ်သွားသည်။

---

## 2. `slug()` — canonical name မှ id အပိုင်း ဖန်တီးခြင်း

```python
import re


def slug(text):
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")


print(slug("Knowledge Graph"))
print(slug("Entity Resolution"))
print(slug("Neo4j"))
print(slug("LLM"))
print(slug("  Nous Research  "))
```

Output —

```text
knowledge-graph
entity-resolution
neo4j
llm
nous-research
```

### အပိုင်းလိုက် ဖတ်ခြင်း

| အပိုင်း | အဓိပ္ပာယ် |
| --- | --- |
| `text.lower()` | စာလုံးအားလုံးကို အသေးစေသည် — `Neo4j` → `neo4j` |
| `[^a-z0-9]+` | အသေးစာလုံး/ဂဏန်း **မဟုတ်သည်** အားလုံး (`[^...]` = negation) |
| `+` | ကပ်နေသည့် တစ်ခု သို့ ထို့ထက် ပို |
| `"-"` | အစားထိုးသည့် character |
| `.strip("-")` | အစ/ဆုံးတွင် ကျန်သည့် `-` ကို ဖယ်သည် |

`"  Nous Research  "` ၏ case တွင် space များသည် `-` ဖြစ်ပြီး `strip("-")` သည်
အစ/ဆုံး `-` များကို ဖယ်သည်။ ထို့ကြောင့် `nous-research` ရသည်။
`strip("-")` မထည့်လျှင် `-nous-research-` ဖြစ်မည်။

### Trap — slug သည် entity နှစ်ခုကို တစ်ခုတည်းသို့ စုစည်းနိုင်သည်

```python
import re


def slug(text):
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")


pairs = [("Knowledge Graph", "Knowledge-Graph"), ("Neo4j Inc.", "Neo4j Inc")]
for left, right in pairs:
    print("%-18s %-18s %s" % (left, right, slug(left) == slug(right)))
print(slug("Knowledge Graph"))
```

Output —

```text
Knowledge Graph    Knowledge-Graph    True
Neo4j Inc.         Neo4j Inc          True
knowledge-graph
```

`Knowledge Graph` နှင့် `Knowledge-Graph` သည် **မတူညီသည့် canonical name နှစ်ခု**
ဖြစ်သော်လည်း slug တူညီသည်။ ထို့ကြောင့် node **တစ်ခုတည်း** ဖြစ်သွားမည်။

| ဖြစ်ရပ် | ရည်ရွယ်ချက် | အမှန်တကယ် ဖြစ်သည့်အရာ |
| --- | --- | --- |
| `Knowledge Graph` / `Knowledge-Graph` | တူညီသော entity ဟု ယူဆ | ✓ ပေါင်းသွားသည် |
| `Neo4j Inc.` / `Neo4j Inc` | တူညီသော organization | ✓ ပေါင်းသွားသည် |
| `GraphRAG` / `Graph-RAG` | **မတူညီသည့်** product | ✗ မှားယွင်း ပေါင်းသွားနိုင်သည် |

ထို့ကြောင့် slug သည် **id အတွက် ရည်ရွယ်** ထားပြီး၊ entity ပေါင်းစည်းမှု (merging)
အတွက် မဟုတ်ပါ။ Merging ကို `GAZETTEER` နှင့် `resolve_surface()` က
ထိန်းချုပ်သည် (Exercise 2)။ Id တူညီခြင်းနှင့် entity တူညီခြင်း မတူပါ။

---

## 3. `entity_id()` — deterministic id

```python
import re


def slug(text):
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")


def entity_id(canonical):
    return "ent:" + slug(canonical)


print(entity_id("Neo4j"))
print(entity_id("Knowledge Graph"))
print(entity_id("Entity Resolution"))
```

Output —

```text
ent:neo4j
ent:knowledge-graph
ent:entity-resolution
```

`ent:` prefix သည် id space ကို သတ်မှတ်သည် — document id (`doc-001`)၊ chunk id
(`doc-001:c00`)၊ relationship id (`rel:...`) နှင့် မတိုက်ပါ။

`canonical` မှ id သို့ ဆင်းသက်မှုသည် **pure function** ဖြစ်သည် — input တူလျှင်
output တူသည်။ ထို့ကြောင့် pipeline ကို မည်မျှ run လုပ်လုပ် `MERGE (n:Entity {id: $id})`
က node တစ်ခုတည်းကိုသာ ရသည် (idempotent)။

### Trap — `hash()` ကို id အဖြစ် မသုံးရ

Python ၏ `hash()` သည် **process တစ်ခုနှင့်တစ်ခု တူညီမှု မရှိ** ပါ။
`PYTHONHASHSEED` ကြောင့် run တိုင်း တန်ဖိုး ပြောင်းသည်။

```python
import subprocess
import sys

code = "print(hash('Neo4j'))"
first = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True).stdout.strip()
second = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True).stdout.strip()
print("two processes return the same hash :", first == second)
```

Output —

```text
two processes return the same hash : False
```

`hash()` ကို id အဖြစ် သုံးလျှင် process တစ်ခုစီတွင် node အသစ် ဖြစ်ပြီး graph ထဲ
duplicate ပေါ်လာမည်။ `hash()` ၏ တန်ဖိုးကိုယ်တိုင်သည်လည်း run တစ်ခုနှင့်တစ်ခု
မတူညီပါ — ထို့ကြောင့် ဤနေရာတွင် တန်ဖိုးနှစ်ခုကို မပြထားပါ။
Deterministic ဖြစ်သည့် `entity_id()` (**string operation သာ**) ကို သုံးရသည်။

---

## 4. `Entity` dataclass

```python
from dataclasses import dataclass, field


@dataclass
class Entity:
    entity_id: str
    name: str
    type: str
    aliases: list = field(default_factory=list)


entity = Entity("ent:neo4j", "Neo4j", "Technology", ["neo4j", "neo 4j", "neo4j inc"])
print(entity.entity_id, entity.name, entity.type)
print(len(entity.aliases))
print(Entity("ent:llm", "LLM", "Technology").aliases)
print(Entity("ent:llm", "LLM", "Technology"))
```

Output —

```text
ent:neo4j Neo4j Technology
3
[]
Entity(entity_id='ent:llm', name='LLM', type='Technology', aliases=[])
```

### `field(default_factory=list)` အဘယ်ကြောင့် လိုအပ်သနည်း။

`aliases: list = []` ဟု တိုက်ရိုက် ရေး၍ **မရ** ပါ — Python သည်
`ValueError: mutable default ... for field 'aliases' is not allowed` ဖြင့် ပယ်သည်။
အကြောင်းရင်းသည် default တန်ဖိုးကို **instance အားလုံး မျှဝေ** သွားစေမည် ဖြစ်သောကြောင့် ဖြစ်သည်။
`default_factory=list` သည် instance တစ်ခုစီအတွက် list အသစ် ဖန်တီးပေးသည်။

`Entity("ent:llm", "LLM", "Technology")` ဟု `aliases` မပေးဘဲ ခေါ်လျှင်
`[]` ရသည် — field အသစ်တိုင်း သီးခြား list ဖြစ်သည်ကို အာမခံသည်။

---

## 5. `resolve_entities()` — canonical entity များ ရွေးထုတ်ခြင်း

```python
import re
from collections import OrderedDict
from dataclasses import dataclass, field


def slug(text):
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")


def entity_id(canonical):
    return "ent:" + slug(canonical)


GAZETTEER = [
    {"canonical": "Neo4j", "type": "Technology", "aliases": ["neo4j", "neo 4j", "neo4j inc"]},
    {"canonical": "Cypher", "type": "Technology", "aliases": ["cypher"]},
    {"canonical": "GraphRAG", "type": "Technology", "aliases": ["graphrag", "graph rag"]},
    {"canonical": "Knowledge Graph", "type": "Concept", "aliases": ["knowledge graph", "knowledge graphs"]},
    {"canonical": "Entity Resolution", "type": "Concept", "aliases": ["entity resolution", "entity-resolution"]},
    {"canonical": "Nous Research", "type": "Organization", "aliases": ["nous research"]},
    {"canonical": "LLM", "type": "Technology", "aliases": ["llm", "large language model"]},
    {"canonical": "Transformer", "type": "Technology", "aliases": ["transformer"]},
]


@dataclass
class Entity:
    entity_id: str
    name: str
    type: str
    aliases: list = field(default_factory=list)


def resolve_entities(triples):
    known = {entity_id(e["canonical"]): Entity(entity_id(e["canonical"]), e["canonical"],
                                               e["type"], list(e["aliases"])) for e in GAZETTEER}
    used = OrderedDict()
    for triple in triples:
        for eid in (triple[0], triple[2]):
            if eid in known:
                used[eid] = known[eid]
    return used


TRIPLES = [
    ("ent:neo4j", "USES", "ent:cypher"),
    ("ent:graphrag", "BUILT_ON", "ent:knowledge-graph"),
    ("ent:neo4j", "USES", "ent:neo-4j-servers"),
    ("ent:llm", "IS_A", "ent:transformer"),
]
entities = resolve_entities(TRIPLES)
for entity in entities.values():
    print("%-22s %-18s %s" % (entity.entity_id, entity.name, entity.type))
print("entities: %d" % len(entities))
```

Output —

```text
ent:neo4j              Neo4j              Technology
ent:cypher             Cypher             Technology
ent:graphrag           GraphRAG           Technology
ent:knowledge-graph    Knowledge Graph    Concept
ent:llm                LLM                Technology
ent:transformer        Transformer        Technology
entities: 6
```

### Dict comprehension ဖြင့် `known` ဖန်တီးခြင်း

```python
known = {entity_id(e["canonical"]): Entity(entity_id(e["canonical"]), e["canonical"],
                                           e["type"], list(e["aliases"])) for e in GAZETTEER}
```

Key သည် `entity_id(canonical)`၊ value သည် `Entity` object ဖြစ်သည်။ ထို့ကြောင့် id ဖြင့်
O(1) ရှာနိုင်သည်။

`list(e["aliases"])` သည် **copy** ဖြစ်သည်။ မလုပ်လျှင် `Entity.aliases` သည်
`GAZETTEER` dict ၏ list ကို **မျှဝေ** သွားပြီး Entity တစ်ခုတွင် append လုပ်လိုက်လျှင်
GAZETTEER ပါ ပြောင်းသွားမည် — ခက်ခဲသည့် alias bug ဖြစ်သည်။

### `OrderedDict` ကို သုံးရသည့် အကြောင်းရင်း

`used = OrderedDict()` သည်
**တွေ့ရှိသည့် အစဉ်အတိုင်း** key များကို ထိန်းသိမ်းသည်။
Python 3.7+ တွင် သာမန် `dict` သည်လည်း insertion order ကို ထိန်းသိမ်းသည်၊
သို့သော် `OrderedDict` သည် ရည်ရွယ်ချက်ကို ဖော်ပြပြီး (`move_to_end`၊
order-sensitive `==` စသည့် အပိုလုပ်ဆောင်ချက် ပါသည်) pipeline output ကို
run တိုင်း **တူညီသည့် အစီအစဉ်** ဖြစ်စေသည်။

| လိုင်း | လုပ်ဆောင်ချက် |
| --- | --- |
| `for eid in (triple[0], triple[2]):` | subject နှင့် object ကို နှစ်ခုလုံး ယူသည် |
| `if eid in known:` | gazetteer ထဲ ရှိလျှင်သာ ထည့်သည် |
| `used[eid] = known[eid]` | key တူလျှင် **ထပ်ရေးလိုက်ရုံ** — အစီအစဉ် မပြောင်း |

`ent:neo-4j-servers` ကဲ့သို့ gazetteer ပြင်ပ id များကို **ဖယ်** လိုက်သည်ကို
သတိထားပါ — `entities: 6` ဖြစ်ရသည့် အကြောင်းရင်း ဖြစ်သည်။ ဤ endpoint နှင့် ဆက်နေသည့်
triple ကို Exercise 5 ၏ gate က `dangling_endpoint` အဖြစ် ဖယ်မည်။

---

## 6. Histogram — `defaultdict` ဖြင့် အရေအတွက် ရေတွက်ခြင်း

```python
from collections import defaultdict

type_hist = defaultdict(int)
for entity_type in ["Technology", "Technology", "Technology", "Concept", "Concept", "Technology", "Technology"]:
    type_hist[entity_type] += 1
print(len(type_hist))
print(type_hist["Missing"])
print(len(type_hist))
print("Missing" in type_hist)
print(dict(sorted(type_hist.items())))
```

Output —

```text
2
0
3
True
{'Concept': 2, 'Missing': 0, 'Technology': 5}
```

### `defaultdict(int)` က ဘာလုပ်ပေးသလဲ။

`type_hist[entity_type] += 1` ကို သာမန် dict ဖြင့် ရေးလျှင် key မရှိသေးသည့် အခါ
`KeyError` ဖြစ်သည်။ `defaultdict(int)` သည် key မရှိလျှင် `int()` (ဆိုလိုသည်မှာ `0`)
ကို အလိုအလျောက် ဖန်တီးပေးသည်။ ထို့ကြောင့် `+= 1` သည် `0 + 1` အဖြစ်
အလုပ်လုပ်သည်။

### Trap — ဖတ်လိုက်ခြင်းဖြင့် key အသစ် ထည့်သွားသည်

ဤ output ကို အနီးကပ် ကြည့်ပါ —

| လိုင်း | `len(type_hist)` | အဓိပ္ပာယ် |
| --- | --- | --- |
| ရေတွက်ပြီးချင်း | 2 | `Concept`၊ `Technology` |
| `type_hist["Missing"]` ပြီးနောက် | **3** | `Missing` **ထည့်သွား** ပြီ (တန်ဖိုး 0) |
| `"Missing" in type_hist` | — | `True` |

`type_hist["Missing"]` သည် **ရိုးရိုးဖတ်ခြင်း မဟုတ်** — `defaultdict` အတွက်
"ရှာပြီး မရှိလျှင် default ဖန်တီး" ဖြစ်သည်။ ထို့ကြောင့် histogram ကို
ရေတွက်ပြီးနောက် `len()` ဖြင့် စစ်ခြင်းမျိုး၊ `in` ဖြင့် စစ်ခြင်းမျိုးကို **ရေတွက်မှု မလုပ်မီ**
သို့မဟုတ် `.get()` ဖြင့် လုပ်ရသည်။ ဤအချက်သည် နောက်ပိုင်း `assert` များကို
တိတ်တဆိတ် ပျက်စေနိုင်သည်။

`dict(sorted(type_hist.items()))` သည် key များကို အက္ခရာအစဉ်အလိုက် စီပြီး
သာမန် dict အဖြစ် ပြောင်းသည် — output ကို run တိုင်း တူညီစေသည်။
`sorted(type_hist)` ဟု ရေးလျှင် key များ၏ **စာရင်း** ကို ပြန်သည် — dict မဟုတ်ပါ။
နှစ်ခုကို ခွဲခြားထားရသည်။

---

## 7. Assertion — contract ကို စစ်ဆေးခြင်း

```python
ALLOWED_ENTITY_TYPES = ("Technology", "Organization", "Concept")
entity_types = {"ent:neo4j": "Technology", "ent:cypher": "Technology",
                "ent:knowledge-graph": "Concept", "ent:llm": "Technology"}

print(all(t in ALLOWED_ENTITY_TYPES for t in entity_types.values()))
print(all(t in ("Concept",) for t in entity_types.values()))

ids = ["ent:neo4j", "ent:cypher", "ent:neo4j"]
print(len(set(ids)), len(ids), len(set(ids)) == len(ids))

try:
    assert len(set(ids)) == len(ids), "duplicate entity_id found"
except AssertionError as exc:
    print("AssertionError:", exc)
```

Output —

```text
True
False
2 3 False
AssertionError: duplicate entity_id found
```

### `all()` သည် ဘာပြန်သနည်း။

`all(iterable)` သည် item အားလုံး truthy ဖြစ်လျှင် `True` ပြန်သည်။ Empty iterable
အတွက် `True` ပြန်သည် (vacuous truth)။ `any()` သည် တစ်ခုခု မှန်လျှင် `True` ပြန်သည်။

`all(t in ALLOWED_ENTITY_TYPES for t in entity_types.values())` သည်
**generator expression** ဖြစ်သည် — `all()` သည် ပထမ `False` တွေ့သည်နှင့်
ရပ်လိုက်သည် (short-circuit)။ ထို့ကြောင့် ကြီးမားသည့် graph ကို စစ်ရာတွင်
ထိရောက်သည်။

### `len(set(...)) == len(...)` — duplicate id စစ်ခြင်း

```python
len(set(ids)) == len(ids)
```

`ids` ထဲ duplicate ရှိလျှင် `set` က ခေါက်ပြီး လျော့သွားသောကြောင့် `len` နှစ်ခု
မတူညီပါ။ Output တွင် `2 3 False` ရသည် — id နှစ်ခုတည်း ရှိပြီး
id သုံးလိုင်း ရှိသောကြောင့် ဖြစ်သည်။ ဤနည်းသည် `entity_id` ထပ်နေသည့် node နှစ်ခု
တိုက်ဆိုင်နေခြင်း (slug collision) ကို ဖော်ထုတ်ပေးသည်။

### `assert` နှင့် `try`/`except`

`assert condition, message` သည် condition `False` ဖြစ်လျှင် `AssertionError`
(လိုအပ်လျှင် message အပါ) ဖြင့် ကျရှုံးသည်။ `try`/`except` သည် ထို error ကို
ဖမ်းပြီး pipeline တစ်ခုလုံး မပြိုလဲစေပါ။ `lab.py` တွင် `run_all()` သည်
`AssertionError` ကို ဖမ်းပြီး exercise တစ်ခုချင်း ရလဒ်ကို print သည်။

---

## 8. Code တစ်ခုလုံး — Run လုပ်နိုင်သော Version

ဤ script သည် Exercise 5 ၏ accepted triple ငါးခုကို **တိုက်ရိုက် ထည့်** ပြီး
schema contract ကို အစအဆုံး စစ်သည်။ ထို့ကြောင့် pipeline တစ်ခုလုံး မလိုဘဲ
validation အဆင့်တစ်ခုတည်းကို ခွဲထုတ် ကြည့်နိုင်သည်။

```python
import re
from collections import OrderedDict, defaultdict
from dataclasses import dataclass, field

NODE_LABELS = ("Document", "Chunk", "Entity")
ALLOWED_ENTITY_TYPES = ("Technology", "Organization", "Concept")
ALLOWED_PREDICATES = ("IS_A", "USES", "BUILT_ON", "DEVELOPED_BY", "INCLUDES", "RELATED_TO")
GAZETTEER = [
    {"canonical": "Neo4j", "type": "Technology", "aliases": ["neo4j", "neo 4j", "neo4j inc"]},
    {"canonical": "Cypher", "type": "Technology", "aliases": ["cypher"]},
    {"canonical": "GraphRAG", "type": "Technology", "aliases": ["graphrag", "graph rag"]},
    {"canonical": "Knowledge Graph", "type": "Concept", "aliases": ["knowledge graph", "knowledge graphs"]},
    {"canonical": "Entity Resolution", "type": "Concept", "aliases": ["entity resolution", "entity-resolution"]},
    {"canonical": "Nous Research", "type": "Organization", "aliases": ["nous research"]},
    {"canonical": "LLM", "type": "Technology", "aliases": ["llm", "large language model"]},
    {"canonical": "Transformer", "type": "Technology", "aliases": ["transformer"]},
]
ACCEPTED = [("Neo4j", "USES", "Cypher"),
            ("GraphRAG", "BUILT_ON", "Knowledge Graph"),
            ("GraphRAG", "BUILT_ON", "Neo4j"),
            ("GraphRAG", "USES", "Entity Resolution"),
            ("LLM", "IS_A", "Transformer")]


def slug(text):
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")


def entity_id(canonical):
    return "ent:" + slug(canonical)


@dataclass
class Entity:
    entity_id: str
    name: str
    type: str
    aliases: list = field(default_factory=list)


def resolve_entities(triples):
    known = {entity_id(e["canonical"]): Entity(entity_id(e["canonical"]), e["canonical"],
                                               e["type"], list(e["aliases"])) for e in GAZETTEER}
    used = OrderedDict()
    for triple in triples:
        for eid in (triple[0], triple[2]):
            if eid in known:
                used[eid] = known[eid]
    return used


triples = [(entity_id(a), p, entity_id(b)) for a, p, b in ACCEPTED]
entities = resolve_entities(triples)
type_hist, pred_hist = defaultdict(int), defaultdict(int)
for entity in entities.values():
    type_hist[entity.type] += 1
for subject, predicate, obj in triples:
    pred_hist[predicate] += 1

print("node labels    : %s" % list(NODE_LABELS))
print("entity types   : %s" % dict(sorted(type_hist.items())))
print("predicate hist : %s" % dict(sorted(pred_hist.items())))
for entity in entities.values():
    print("  %-22s %-18s %s" % (entity.entity_id, entity.name, entity.type))

assert all(e.type in ALLOWED_ENTITY_TYPES for e in entities.values())
assert all(e.entity_id == entity_id(e.name) and e.name == e.name.strip() for e in entities.values())
assert len({e.entity_id for e in entities.values()}) == len(entities)
assert all(p in ALLOWED_PREDICATES for _, p, _ in triples)
assert all(s in entities and o in entities and s != o for s, _, o in triples)
assert set(pred_hist) == {"BUILT_ON", "IS_A", "USES"} and sum(pred_hist.values()) == 5
print("entities: %d" % len(entities))
```

Output —

```text
node labels    : ['Document', 'Chunk', 'Entity']
entity types   : {'Concept': 2, 'Technology': 5}
predicate hist : {'BUILT_ON': 2, 'IS_A': 1, 'USES': 2}
  ent:neo4j              Neo4j              Technology
  ent:cypher             Cypher             Technology
  ent:graphrag           GraphRAG           Technology
  ent:knowledge-graph    Knowledge Graph    Concept
  ent:entity-resolution  Entity Resolution  Concept
  ent:llm                LLM                Technology
  ent:transformer        Transformer        Technology
entities: 7
```

ရလဒ်သည် `lab.py` ၏ Exercise 3 နှင့် တူညီသည် — entity ၇ ခု၊
`{'Concept': 2, 'Technology': 5}` နှင့် `{'BUILT_ON': 2, 'IS_A': 1, 'USES': 2}`။

### စစ်ဆေးချက် ဇယား

| # | Assertion | စစ်သည့် အရာ |
| --- | --- | --- |
| 1 | `all(e.type in ALLOWED_ENTITY_TYPES ...)` | type သည် closed set အတွင်း |
| 2 | `e.entity_id == entity_id(e.name)` | id သည် name မှ deterministic |
| 3 | `e.name == e.name.strip()` | name တွင် ကွက်လပ် မပိုပါ |
| 4 | `len({e.entity_id ...}) == len(entities)` | id ထပ်နေမှု မရှိ |
| 5 | `all(p in ALLOWED_PREDICATES ...)` | predicate အားလုံး whitelist အတွင်း |
| 6 | `all(s in entities and o in entities ...)` | dangling endpoint မရှိ |
| 7 | `s != o` | self-loop မရှိ |
| 8 | `set(pred_hist) == {...}` | predicate အမျိုးအစား တိကျ |

Assertion တစ်ခုချင်းစီသည် **တိကျသည့် failure mode တစ်ခု** ကို ကိုယ်စားပြုသည်။
ထို့ကြောင့် ကျရှုံးသည့် assertion နံပါတ်ကို ကြည့်လျှင် ပြဿနာ၏ အရင်းအမြစ်ကို
ချက်ချင်း သိသည်။

---

## 9. ကိုယ်တိုင်လေ့ကျင့်ကြည့်ပါ

**မေးခွန်း** — အောက်ပါ code သည် မည်သည့်ရလဒ် ပြန်ပေးမည်နည်း။

```python
import re
from collections import defaultdict


def slug(text):
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")


def entity_id(canonical):
    return "ent:" + slug(canonical)


hist = defaultdict(int)
for name in ["Neo4j", "neo4j", "Neo4j"]:
    hist[entity_id(name)] += 1
print(dict(sorted(hist.items())))
```

1. `{'ent:neo4j': 3}` — slug က case အားလုံးကို စုစည်းလိုက်သည်
2. `{'ent:neo4j': 1, 'ent:neo4j': 2}` — duplicate key နှစ်ခု
3. `{'ent:Neo4j': 3}` — slug မလုပ်ပါ

<details>
<summary>အဖြေ ကြည့်ရန်</summary>

**အဖြေ — 1. `{'ent:neo4j': 3}`**

အကြောင်းရင်း — `slug()` သည် `text.lower()` ကို အရင် လုပ်သဖြင့် `Neo4j`၊
`neo4j` နှစ်ခုလုံး `neo4j` ဖြစ်သည်။ `entity_id()` သည် `ent:neo4j` တူညီသော key
သုံးကြိမ် ရသဖြင့် `hist` သည် ၃ အထိ တက်သည်။ Dict တွင် key ထပ်နိုင်သောကြောင့်
option 2 မဖြစ်နိုင်ပါ။

ဤဥပမာသည် case-insensitive id ၏ **ကောင်းသော** အကျိုးကို ပြသည် —
`Neo4j`/`neo4j` သည် node တစ်ခုတည်း ဖြစ်သည်။ သို့သော် အလားတူ အကြောင်းရင်းဖြင့်ပင်
`Knowledge Graph`/`Knowledge-Graph` ကဲ့သို့ **မတူညီသည့်** အမည်နှစ်ခုကို
ပေါင်းစည်းနိုင်သည် — ထို့ကြောင့် slug collision ကို validation အဆင့်တွင်
သတိထားရသည်။

</details>

---

**အဓိက မှတ်ထားရန်** — Data model validation သည် graph ကို Neo4j မရောက်မီ
နောက်ဆုံး အတားအဆီး ဖြစ်သည်။ Contract ကို `tuple` constant အဖြစ်
တစ်နေရာတည်း သတ်မှတ်ထားခြင်းဖြင့် label အသစ်များ ဝင်မလာနိုင်ပါ။ Node id သည်
`entity_id()` — `hash()` မဟုတ် — မှ ဆင်းသက်သဖြင့် run တိုင်း တူညီသော id
ရပြီး `MERGE` သည် idempotent ဖြစ်သည်။ `defaultdict` ၏ "ဖတ်လိုက်ခြင်းဖြင့် key ထည့်"
အပြုအမူကို သတိထားပါ — histogram ကို ရေတွက်ပြီးနောက် စစ်ဆေးချက်များ
မလုပ်မီ `.get()` သို့မဟုတ် `dict()` ပြောင်းပြီးမှ လုပ်ပါ။
