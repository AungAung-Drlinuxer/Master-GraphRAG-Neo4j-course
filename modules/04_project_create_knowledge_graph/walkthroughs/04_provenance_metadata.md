# Walkthrough 04 — Provenance Metadata (Exercise 4)

> ဤဖိုင်သည် Module 04 ၏ `solution.md` ထဲက Exercise 4 ကို **Python အခြေခံမှ စ၍**
> အပိုင်းလိုက် ရှင်းပြသည့် walkthrough ဖြစ်သည်။

---

## 0. ဤ Exercise က ဘာကို ဖြေရှင်းပေးသလဲ။

Triple တစ်ခုသည် corpus ၏ မည်သည့်နေရာမှ လာသည်ကို မမှတ်ထားလျှင် —
ရလဒ်ကို **စစ်ဆေး (audit) လုပ်၍ မရ**၊ confidence ကို ခန့်မှန်း၍ မရပါ။

```text
extract stage က triple များ ထုတ်သည် —
  GraphRAG -[BUILT_ON]-> Knowledge Graph   (doc-001:c00 မှ)
  GraphRAG -[BUILT_ON]-> Knowledge Graph   (doc-002:c00 မှ)   <- same key

merge stage တွင် ရွေးချယ်စရာ နှစ်မျိုး —
  (က) duplicate ကို ဖျက်ပစ်    -> source တစ်ခု ဆုံးရှုံး
  (ခ) provenance list ကို union -> source နှစ်ခုလုံး ကျန်၊ support count 2

support count သည် confidence ကို ခိုင်မာစေသည် —
  source ၂ ခု ထောက်ခံသော triple သည် source ၁ ခုထက် ယုံကြည်ရသည်

audit လုပ်ရန် —
  triple -> chunk_id -> မူရင်း sentence အထိ ပြန်လိုက်နိုင်သည်
```

ဤ Exercise သည် `Provenance` dataclass ဖြင့် **source chunk id၊ confidence၊ method**
သုံးခုကို triple တိုင်းတွင် မှတ်ပြီး၊ duplicate များကို **ဖျက်မပစ်ဘဲ ပေါင်း** သည်။

ဤ code တွင် လေ့လာရမည့် Python concepts များမှာ —

- `@dataclass` နှင့် nested dataclass (`list` field ထဲ `Provenance`)
- `field(default_factory=list)` — mutable default ၏ အန္တရာယ်
- `@property` decorator — computed attribute
- Generator expression ကို `max()` သို့ ပို့ခြင်း
- Empty iterable နှင့် `ValueError`
- `collections.OrderedDict` နှင့် `in` operator
- `list()` copy နှင့် `extend()`
- `sorted(set(...))` ဖြင့် အစီအစဉ် တည်ငြိမ်စေခြင်း
- `json.dumps(sort_keys=True)`
- `try`/`except ValueError`

---

## 1. `Provenance` — triple တစ်ခု၏ မူရင်း အထောက်အထား

```python
from dataclasses import dataclass


@dataclass
class Provenance:
    chunk_id: str
    confidence: float
    method: str


prov = Provenance("doc-001:c00", 0.95, "pattern:uses")
print(prov)
print(prov.chunk_id, prov.confidence, prov.method)
```

Output —

```text
Provenance(chunk_id='doc-001:c00', confidence=0.95, method='pattern:uses')
doc-001:c00 0.95 pattern:uses
```

Field သုံးခုသည် တာဝန် သုံးမျိုးကို ကိုယ်စားပြုသည်။

| Field | အဓိပ္ပာယ် | ဥပမာ |
| --- | --- | --- |
| `chunk_id` | triple ကို ရှာတွေ့သည့် chunk | `doc-001:c00` |
| `confidence` | ထို chunk တွင် ဤ triple မှန်ကြောင်း ယုံကြည်မှု | `0.95` |
| `method` | extraction နည်းလမ်း | `pattern:uses`၊ `cooccurrence` |

`method` သည် **နည်းလမ်းအလိုက် စစ်ထုတ်ရန်** အရေးကြီးသည် — ဥပမာ
`cooccurrence` method ၏ triple များကို သီးခြား စစ်လိုပါက `method` ဖြင့်
ခွဲနိုင်သည်။ ထို့ကြောင့် `pattern:uses` ကဲ့သို့ prefix ကို ထည့်ထားခြင်း ဖြစ်သည် — predicate
အမည်ကို နောက်တွင် ကပ်ထားသဖြင့် `startswith("pattern:")` ဖြင့် pattern-based
triple အားလုံးကို တစ်ချက် ဆွဲထုတ်နိုင်သည်။

---

## 2. `Triple` dataclass နှင့် `field(default_factory=list)`

```python
from dataclasses import dataclass, field


@dataclass
class Provenance:
    chunk_id: str
    confidence: float
    method: str


@dataclass
class Triple:
    subject_id: str
    predicate: str
    object_id: str
    provenance: list = field(default_factory=list)

    @property
    def key(self):
        return (self.subject_id, self.predicate, self.object_id)


triple = Triple("ent:neo4j", "USES", "ent:cypher", [Provenance("doc-001:c00", 0.95, "pattern:uses")])
print(triple.key)
print(len(triple.provenance))
print(triple)
```

Output —

```text
('ent:neo4j', 'USES', 'ent:cypher')
1
Triple(subject_id='ent:neo4j', predicate='USES', object_id='ent:cypher', provenance=[Provenance(chunk_id='doc-001:c00', confidence=0.95, method='pattern:uses')])
```

### အဘယ်ကြောင့် `provenance` သည် **list** ဖြစ်သနည်း။

Triple တစ်ခုကို source များစွာမှ တွေ့နိုင်သည်။ List ဖြစ်သောကြောင့်
`append`/`extend` ဖြင့် source အသစ် ထည့်နိုင်သည်။ `confidence` ကို **မသိမ်း**
ထားသည်ကို သတိထားပါ — `@property` ဖြင့် `provenance` မှ တွက်သည် (အပိုင်း ၄)။
Derived value ကို သိမ်းမထားခြင်းဖြင့် "source အသစ် ထည့်ပြီး confidence မပြင်မိ"
ဆိုသည့် bug ကို လုံးဝ ရှောင်နိုင်သည်။

### `field(default_factory=list)`

```python
provenance: list = field(default_factory=list)
```

`provenance: list = []` ဟု ရေးလျှင် Python သည် `ValueError` ဖြင့် ပယ်သည်။
အကြောင်းရင်းသည် `[]` ကို **တစ်ခါတည်း** ဖန်တီးပြီး instance အားလုံး မျှဝေစေမည် ဖြစ်သောကြောင့် ဖြစ်သည်။
`default_factory=list` သည် instance တစ်ခုစီအတွက် list အသစ် ဖန်တီးပေးသည်။

```python
from dataclasses import dataclass, field


@dataclass
class Bad:
    items: list = []


print("class defined")
```

ဤ snippet ကို **run လုပ်လျှင် error ဖြစ်သည်**။ တိကျသည့် error ကို ကြည့်ပါ။

```python
from dataclasses import dataclass
import traceback

source = """
from dataclasses import dataclass


@dataclass
class Bad:
    items: list = []
"""
try:
    exec(compile(source, "<bad>", "exec"), {})
except ValueError as exc:
    print("ValueError:", exc)
```

Output —

```text
ValueError: mutable default <class 'list'> for field items is not allowed: use default_factory
```

Python သည် class definition အချိန်တွင်ပင် ဖမ်းပြီး ဖြေရှင်းနည်းကို ပြောပြသည်။

### `@property key` — tuple ဖြင့် identity

```python
@property
def key(self):
    return (self.subject_id, self.predicate, self.object_id)
```

`@property` သည် method တစ်ခုကို **attribute ကဲ့သို့** ဖတ်နိုင်စေသည် — `triple.key`
ဟု ကွင်းမပါဘဲ ရေးသည်။

`provenance` ကို key ထဲ **မထည့်** ပါ — key သည် identity သာဖြစ်ပြီး
provenance သည် support ဖြစ်သည်။ ထို့ကြောင့် source နှစ်ခုမှ တွေ့သည့် triple
နှစ်ခုသည် key တူညီပြီး merge လုပ်နိုင်သည်။

`key` ကို tuple ဖြစ်စေခြင်းသည် dict key အဖြစ် သုံးနိုင်ရန် ဖြစ်သည် — Python tuple သည်
immutable ဖြစ်သောကြောင့် hashable ဖြစ်သည်။ List ဖြစ်လျှင်
`TypeError: unhashable type` ဖြစ်မည်။

```python
key = ("ent:neo4j", "USES", "ent:cypher")
store = {key: "found"}
print(store[("ent:neo4j", "USES", "ent:cypher")])
try:
    store[["ent:neo4j", "USES", "ent:cypher"]] = "x"
except TypeError as exc:
    print("TypeError:", exc)
```

Output —

```text
found
TypeError: cannot use 'list' as a dict key (unhashable type: 'list')
```

---

## 3. `@property confidence` — provenance မှ တွက်ချက်ခြင်း

```python
from dataclasses import dataclass, field


@dataclass
class Provenance:
    chunk_id: str
    confidence: float
    method: str


@dataclass
class Triple:
    subject_id: str
    predicate: str
    object_id: str
    provenance: list = field(default_factory=list)

    @property
    def confidence(self):
        return max(p.confidence for p in self.provenance)


support = Triple("ent:graphrag", "BUILT_ON", "ent:knowledge-graph",
                 [Provenance("doc-001:c00", 0.95, "pattern:built_on"),
                  Provenance("doc-002:c00", 0.80, "pattern:built_on")])
print(support.confidence)
print(max([0.95, 0.80]))
empty = Triple("ent:neo4j", "USES", "ent:cypher")
try:
    print(empty.confidence)
except ValueError as exc:
    print("ValueError:", exc)
```

Output —

```text
0.95
0.95
ValueError: max() iterable argument is empty
```

### `max(generator)` — အကြီးဆုံးကို ယူသည်

`max(p.confidence for p in self.provenance)` သည် generator expression မှ
အကြီးဆုံး confidence ကို ပြန်သည်။ `[0.95, 0.80]` အတွက် `0.95` ရသည်။

| Provenance | confidence |
| --- | --- |
| `doc-001:c00` | 0.95 |
| `doc-002:c00` | 0.80 |
| **`max`** | **0.95** |

### အဘယ်ကြောင့် `max` ဖြစ်ပြီး `min` မဟုတ်သနည်း။

Extraction တစ်ခုချင်းစီမှ confidence သည် အဆိုပါ chunk အတွက်သာ ဖြစ်သည်။
`min` ယူလျှင် source အသစ် ထည့်တိုင်း confidence **ကျ** မည် — ၎င်းသည်
"အထောက်အထား များလာသည်နှင့် ယုံကြည်မှု ကျသည်" ဆိုသည့် ဆန့်ကျင်ဘက်
အပြုအမူ ဖြစ်သည်။ `max` ယူခြင်းကြောင့် source အများအပြား ထောက်ခံသည့် triple သည်
quality gate (Exercise 5) ကို ဖြတ်နိုင်သည်။

### Trap — provenance မရှိသော triple

```python
from dataclasses import dataclass, field


@dataclass
class Provenance:
    chunk_id: str
    confidence: float
    method: str


@dataclass
class Triple:
    subject_id: str
    predicate: str
    object_id: str
    provenance: list = field(default_factory=list)

    @property
    def confidence(self):
        return max(p.confidence for p in self.provenance)


empty = Triple("ent:neo4j", "USES", "ent:cypher")
try:
    print(empty.confidence)
except ValueError as exc:
    print("ValueError:", exc)
```

Output —

```text
ValueError: max() iterable argument is empty
```

Provenance list ဗလာဖြစ်လျှင် `max()` သည် `ValueError` ဖြင့် ကျရှုံးသည်။ ထို့ကြောင့်
`merge_triples` နှင့် `quality_gate` များတွင်
`assert triple.provenance` ဖြင့် စစ်ရသည် — provenance မရှိသည့် triple
တစ်ခု ရှိလျှင် **pipeline တစ်ခုလုံး ရပ်သွား** နိုင်သည်။

---

## 4. `merge_triples()` — duplicate များကို ပေါင်းခြင်း

```python
from collections import OrderedDict
from dataclasses import dataclass, field


@dataclass
class Provenance:
    chunk_id: str
    confidence: float
    method: str


@dataclass
class Triple:
    subject_id: str
    predicate: str
    object_id: str
    provenance: list = field(default_factory=list)

    @property
    def key(self):
        return (self.subject_id, self.predicate, self.object_id)


def merge_triples(triples):
    merged = OrderedDict()
    for triple in triples:
        if triple.key in merged:
            merged[triple.key].provenance.extend(triple.provenance)
        else:
            merged[triple.key] = Triple(triple.subject_id, triple.predicate, triple.object_id,
                                        list(triple.provenance))
    return list(merged.values())


def merge_last_wins(triples):
    merged = {}
    for triple in triples:
        merged[triple.key] = Triple(triple.subject_id, triple.predicate, triple.object_id,
                                    list(triple.provenance))
    return list(merged.values())


RAW = [
    Triple("ent:graphrag", "BUILT_ON", "ent:knowledge-graph",
           [Provenance("doc-001:c00", 0.95, "pattern:built_on")]),
    Triple("ent:graphrag", "BUILT_ON", "ent:knowledge-graph",
           [Provenance("doc-002:c00", 0.95, "pattern:built_on")]),
]
for label, fn in [("extend (correct)", merge_triples), ("overwrite (trap)", merge_last_wins)]:
    result = fn(RAW)
    print("%-18s triples=%d provenance=%s"
          % (label, len(result), [(p.chunk_id, p.confidence) for p in result[0].provenance]))
```

Output —

```text
extend (correct)   triples=1 provenance=[('doc-001:c00', 0.95), ('doc-002:c00', 0.95)]
overwrite (trap)   triples=1 provenance=[('doc-002:c00', 0.95)]
```

### Trap — "နောက်ဆုံးက အနိုင်" (last wins)

`merge_last_wins` သည် `merged[triple.key] = ...` ဖြင့် **အစားထိုး** လိုက်သည်။
`triples=1` ဖြစ်ခြင်းသည် triple အရေအတွက် မှန်သော်လည်း `provenance` တွင်
`doc-001:c00` **ပျောက်သွား** သည်။

| နည်းလမ်း | Triple အရေအတွက် | Provenance အရေအတွက် | Source ဆုံးရှုံးမှု |
| --- | --- | --- | --- |
| `extend` (မှန်) | 1 | 2 | မရှိ |
| overwrite (trap) | 1 | 1 | `doc-001:c00` ဆုံးရှုံး |

`extend` သည် list နှစ်ခုကို **ပေါင်း** သည် (append နှင့် ခြားနားချက် —
`extend` သည် item တစ်ခုချင်း ဖြန့်ထည့်သည်၊ `append` သည် list တစ်ခုလုံး ထည့်သည်)။

```python
first, second = ["a"], ["b", "c"]
first.extend(second)
print(first)

third, fourth = ["a"], ["b", "c"]
third.append(fourth)
print(third)
```

Output —

```text
['a', 'b', 'c']
['a', ['b', 'c']]
```

### `list(triple.provenance)` က copy ဖြစ်သည်

```python
merged[triple.key] = Triple(..., list(triple.provenance))
```

`list()` မလုပ်ဘဲ `triple.provenance` ကို တိုက်ရိုက် ထည့်လျှင် merged triple နှင့်
မူရင်း triple သည် **list တစ်ခုတည်း** ကို မျှဝေသွားသည်။ နောက်တွင်
`extend` လုပ်လိုက်လျှင် မူရင်း raw triple ပါ ပြောင်းသွားမည် — ၎င်းသည်
"raw_triples နှင့် merged ကွာခြားမှု" ကို ပျက်စေသည်။

### `OrderedDict` နှင့် `in`

`if triple.key in merged:` သည် dict membership ဖြစ်သည် — O(1)။ List ဖြင့်
`if triple.key in list_of_keys:` လုပ်လျှင် O(n) ဖြစ်သည်။ `OrderedDict` သည်
key များကို **ပထမဆုံး တွေ့သည့် အစဉ်** အတိုင်း ထိန်းသိမ်းသဖြင့် output ၏
အစီအစဉ် run တိုင်း တူညီသည်။

---

## 5. `to_dict()` — JSON export အတွက် ပြောင်းခြင်း

```python
import json
from dataclasses import dataclass, field


@dataclass
class Provenance:
    chunk_id: str
    confidence: float
    method: str


@dataclass
class Triple:
    subject_id: str
    predicate: str
    object_id: str
    provenance: list = field(default_factory=list)

    @property
    def confidence(self):
        return max(p.confidence for p in self.provenance)

    def to_dict(self, names):
        return {"subject": names.get(self.subject_id, self.subject_id), "predicate": self.predicate,
                "object": names.get(self.object_id, self.object_id), "subject_id": self.subject_id,
                "object_id": self.object_id, "confidence": round(self.confidence, 2),
                "provenance": [{"chunk_id": p.chunk_id, "confidence": p.confidence, "method": p.method}
                               for p in self.provenance]}


names = {"ent:graphrag": "GraphRAG", "ent:knowledge-graph": "Knowledge Graph"}
triple = Triple("ent:graphrag", "BUILT_ON", "ent:knowledge-graph",
                [Provenance("doc-001:c00", 0.95, "pattern:built_on"),
                 Provenance("doc-002:c00", 0.95, "pattern:built_on")])
print(json.dumps(triple.to_dict(names), sort_keys=True, indent=2))
```

Output —

```text
{
  "confidence": 0.95,
  "object": "Knowledge Graph",
  "object_id": "ent:knowledge-graph",
  "predicate": "BUILT_ON",
  "provenance": [
    {
      "chunk_id": "doc-001:c00",
      "confidence": 0.95,
      "method": "pattern:built_on"
    },
    {
      "chunk_id": "doc-002:c00",
      "confidence": 0.95,
      "method": "pattern:built_on"
    }
  ],
  "subject": "GraphRAG",
  "subject_id": "ent:graphrag"
}
```

### `names.get(id, id)` — fallback

`names` သည် `{entity_id: name}` mapping ဖြစ်သည်။ `names.get(self.subject_id, self.subject_id)`
သည် id ကို ရှာပြီး **မရှိလျှင် id ကိုယ်တိုင်** ပြန်သည် (`.get()` ၏ ဒုတိယ argument
သည် default)။ ထို့ကြောင့် `KeyError` မဖြစ်ဘဲ output သည် အမြဲ ပြည့်စုံသည်။

### အဘယ်ကြောင့် id နှင့် name နှစ်ခုလုံး ထည့်သနည်း။

| Field | အသုံးပြုသည့် နေရာ |
| --- | --- |
| `subject_id` / `object_id` | Neo4j `MERGE` (တိကျပြီး deterministic) |
| `subject` / `object` | လူဖတ်ရန်၊ report/UI |

Id သာ ပါလျှင် လူဖတ်ရ ခက်သည်။ Name သာ ပါလျှင် id collision ကို မဖော်နိုင်ပါ။
နှစ်ခုလုံး ထည့်ခြင်းသည် နှစ်ဖက်စလုံး အကျိုးရှိသည်။

`round(self.confidence, 2)` သည် float ၏ binary representation အမှားများ
(ဥပမာ `0.9499999`) ကို output တွင် ဖုံးကွယ်ပေးသည်။ JSON တွင်
`sort_keys=True` ထည့်ခြင်းသည် key အစီအစဉ်ကို တည်ငြိမ်စေသည် — ထို့ကြောင့်
output ကို run တိုင်း diff လုပ်နိုင်သည်။

---

## 6. ရလဒ် — merged triple ၈ ခု ၏ provenance

```python
from collections import OrderedDict
from dataclasses import dataclass, field


@dataclass
class Provenance:
    chunk_id: str
    confidence: float
    method: str


@dataclass
class Triple:
    subject_id: str
    predicate: str
    object_id: str
    provenance: list = field(default_factory=list)

    @property
    def key(self):
        return (self.subject_id, self.predicate, self.object_id)

    @property
    def confidence(self):
        return max(p.confidence for p in self.provenance)


def merge_triples(triples):
    merged = OrderedDict()
    for triple in triples:
        if triple.key in merged:
            merged[triple.key].provenance.extend(triple.provenance)
        else:
            merged[triple.key] = Triple(triple.subject_id, triple.predicate, triple.object_id,
                                        list(triple.provenance))
    return list(merged.values())


NEO4J, CYPHER, GRAPHRAG = "ent:neo4j", "ent:cypher", "ent:graphrag"
KG, ER, LLM, TRF = "ent:knowledge-graph", "ent:entity-resolution", "ent:llm", "ent:transformer"
RAW = [
    Triple(NEO4J, "USES", CYPHER, [Provenance("doc-001:c00", 0.95, "pattern:uses")]),
    Triple(GRAPHRAG, "BUILT_ON", KG, [Provenance("doc-001:c00", 0.95, "pattern:built_on")]),
    Triple(GRAPHRAG, "BUILT_ON", KG, [Provenance("doc-002:c00", 0.95, "pattern:built_on")]),
    Triple(GRAPHRAG, "BUILT_ON", NEO4J, [Provenance("doc-002:c00", 0.80, "pattern:built_on")]),
    Triple(NEO4J, "DEVELOPED_BY", NEO4J, [Provenance("doc-002:c00", 0.80, "pattern:developed_by")]),
    Triple(NEO4J, "RELATED_TO", GRAPHRAG, [Provenance("doc-002:c01", 0.45, "cooccurrence")]),
    Triple(GRAPHRAG, "RELATED_TO", CYPHER, [Provenance("doc-002:c01", 0.45, "cooccurrence")]),
    Triple(GRAPHRAG, "USES", ER, [Provenance("doc-003:c00", 0.95, "pattern:uses")]),
    Triple(LLM, "IS_A", TRF, [Provenance("doc-003:c00", 0.95, "pattern:is_a")]),
]
names = {"ent:neo4j": "Neo4j", "ent:cypher": "Cypher", "ent:graphrag": "GraphRAG",
         "ent:knowledge-graph": "Knowledge Graph", "ent:entity-resolution": "Entity Resolution",
         "ent:llm": "LLM", "ent:transformer": "Transformer"}

merged = merge_triples(RAW)
chunk_ids = {"doc-001:c00", "doc-001:c01", "doc-002:c00", "doc-002:c01", "doc-003:c00", "doc-003:c01"}
methods = set()
for triple in merged:
    assert triple.provenance, "triple without provenance"
    for prov in triple.provenance:
        assert prov.chunk_id in chunk_ids and 0.0 <= prov.confidence <= 1.0
        methods.add(prov.method)
    print("  %-15s -[%s]-> %-16s conf=%.2f sources=%s" % (names[triple.subject_id], triple.predicate,
                                                          names[triple.object_id], triple.confidence,
                                                          [p.chunk_id for p in triple.provenance]))
target = [t for t in merged if t.subject_id == "ent:graphrag" and t.predicate == "BUILT_ON"
          and t.object_id == "ent:knowledge-graph"]
print("raw triples : %d" % len(RAW))
print("merged      : %d" % len(merged))
print("merged triple 'GraphRAG -[BUILT_ON]-> Knowledge Graph' provenance: %s" %
      [(p.chunk_id, p.confidence) for p in target[0].provenance])
print(sorted(methods))
assert len(target) == 1 and len(target[0].provenance) == 2
assert len({p.chunk_id for p in target[0].provenance}) == 2
```

Output —

```text
  Neo4j           -[USES]-> Cypher           conf=0.95 sources=['doc-001:c00']
  GraphRAG        -[BUILT_ON]-> Knowledge Graph  conf=0.95 sources=['doc-001:c00', 'doc-002:c00']
  GraphRAG        -[BUILT_ON]-> Neo4j            conf=0.80 sources=['doc-002:c00']
  Neo4j           -[DEVELOPED_BY]-> Neo4j            conf=0.80 sources=['doc-002:c00']
  Neo4j           -[RELATED_TO]-> GraphRAG         conf=0.45 sources=['doc-002:c01']
  GraphRAG        -[RELATED_TO]-> Cypher           conf=0.45 sources=['doc-002:c01']
  GraphRAG        -[USES]-> Entity Resolution conf=0.95 sources=['doc-003:c00']
  LLM             -[IS_A]-> Transformer      conf=0.95 sources=['doc-003:c00']
raw triples : 9
merged      : 8
merged triple 'GraphRAG -[BUILT_ON]-> Knowledge Graph' provenance: [('doc-001:c00', 0.95), ('doc-002:c00', 0.95)]
['cooccurrence', 'pattern:built_on', 'pattern:developed_by', 'pattern:is_a', 'pattern:uses']
```

ဤ output သည် `lab.py` ၏ Exercise 4 နှင့် တူညီသည်။

### Merged triple ဇယား

| Subject | Predicate | Object | confidence | Sources | Gate ရလဒ် |
| --- | --- | --- | --- | --- | --- |
| Neo4j | USES | Cypher | 0.95 | `doc-001:c00` | accept |
| GraphRAG | BUILT_ON | Knowledge Graph | 0.95 | `doc-001:c00`၊ `doc-002:c00` | accept |
| GraphRAG | BUILT_ON | Neo4j | 0.80 | `doc-002:c00` | accept |
| Neo4j | DEVELOPED_BY | Neo4j | 0.80 | `doc-002:c00` | **reject** (self-loop) |
| Neo4j | RELATED_TO | GraphRAG | 0.45 | `doc-002:c01` | **reject** (low confidence) |
| GraphRAG | RELATED_TO | Cypher | 0.45 | `doc-002:c01` | **reject** (low confidence) |
| GraphRAG | USES | Entity Resolution | 0.95 | `doc-003:c00` | accept |
| LLM | IS_A | Transformer | 0.95 | `doc-003:c00` | accept |

ရလဒ် —

- raw triple **၉** ခုမှ merged **၈** ခု ဖြစ်သည် — `GraphRAG -[BUILT_ON]-> Knowledge Graph`
  သည် source နှစ်ခုမှ လာသဖြင့် ပေါင်းသွားသည်။
- ပေါင်းသွားသည့် triple ၏ `provenance` တွင် record **၂** ခု ရှိပြီး
  chunk_id နှစ်ခု **ကွဲပြား** သည် — ၎င်းကို assertion က စစ်သည်။
- `methods` စုစုပေါင်း ငါးမျိုး — pattern ၄ မျိုးနှင့် `cooccurrence` တစ်မျိုး။

Output တွင် `%-16s` format ကြောင့် column အလျားမညီသည်ကို တွေ့နိုင်သည်
(`Knowledge Graph` သည် ၁၅ လုံးထက် ရှည်သဖြင့် padding မထည့်နိုင်)။ ၎င်းသည်
formatting အပိုင်းသာ ဖြစ်ပြီး အချက်အလက် မှန်ကန်မှုကို မထိပါ။

---

## 7. ကိုယ်တိုင်လေ့ကျင့်ကြည့်ပါ

**မေးခွန်း** — အောက်ပါ code သည် မည်သည့်ရလဒ် ပြန်ပေးမည်နည်း။

```python
from dataclasses import dataclass, field


@dataclass
class Provenance:
    chunk_id: str
    confidence: float
    method: str


@dataclass
class Triple:
    subject_id: str
    predicate: str
    object_id: str
    provenance: list = field(default_factory=list)

    @property
    def confidence(self):
        return max(p.confidence for p in self.provenance)


triple = Triple("ent:llm", "IS_A", "ent:transformer",
                [Provenance("doc-003:c00", 0.55, "pattern:is_a"),
                 Provenance("doc-003:c01", 0.30, "pattern:is_a")])
print(triple.confidence)
```

1. `0.30` — အနည်းဆုံး confidence (`min`)
2. `0.55` — အမြင့်ဆုံး confidence (`max`)
3. `0.43` — ပျမ်းမျှ (`(0.55 + 0.30) / 2`)

<details>
<summary>အဖြေ ကြည့်ရန်</summary>

**အဖြေ — 2. `0.55`**

အကြောင်းရင်း — `confidence` သည် `max(p.confidence for p in self.provenance)`
ဖြစ်သဖြင့် `[0.55, 0.30]` ထဲမှ `0.55` ရသည်။ Float ပြတ်သားမှုအတွက်
`0.55` သည် `0.5500000000000000444` ဖြစ်နိုင်သော်လည်း `print()` သည် `0.55` ဖြင့်
ပြသည်။

`max` ဖြစ်ရသည့် အကြောင်းရင်း — source အသစ် ထည့်တိုင်း confidence ကျသွားလျှင်
(=`min` ဖြစ်လျှင်) support များသည့် triple များသည် gate ကို ပို၍ ခက်ခဲစွာ ဖြတ်ရမည်။
`max` ဖြင့် source အသစ်သည် confidence ကို မညံ့စေပါ။

</details>

---

**အဓိက မှတ်ထားရန်** — Provenance သည် pipeline ၏ **audit trail** ဖြစ်သည်။
`chunk_id` ကြောင့် triple တိုင်းကို မူရင်း sentence အထိ ပြန်လိုက်နိုင်ပြီး
`method` ကြောင့် pattern-based နှင့် co-occurrence ရလဒ်များကို ခွဲခြားနိုင်သည်။
Duplicate triple များကို ဖျက်မပစ်ဘဲ `extend()` ဖြင့် **union** လုပ်ခြင်းကြောင့်
support count ကျန်ပြီး၊ `Triple.confidence` ကို provenance မှ **တွက်ချက်** ခြင်းကြောင့်
source အသစ် ထည့်ပြီး confidence ပြင်ရန် မေ့ခြင်း မဖြစ်နိုင်ပါ။ `list()` copy နှင့်
`field(default_factory=list)` နှစ်ခုသည် "list တစ်ခုတည်း မျှဝေ" bug ကို တားသည်။
