# Walkthrough 05 — Quality Gate Filtering (Exercise 5)

> ဤဖိုင်သည် Module 04 ၏ `solution.md` ထဲက Exercise 5 ကို **Python အခြေခံမှ စ၍**
> အပိုင်းလိုက် ရှင်းပြသည့် walkthrough ဖြစ်သည်။

---

## 0. ဤ Exercise က ဘာကို ဖြေရှင်းပေးသလဲ။

Extraction အဆင့်သည် **recall ကို ဦးစားပေး** သည် — pattern မကိုက်သော sentence
တွင်ပင် entity နှစ်ခုတွဲလျှင် co-occurrence triple ထုတ်သည်။ ထို့ကြောင့်
triple များထဲ ချို့ယွင်းချက် ပါလာသည်။

```text
candidates (merged triples + injected defects)
  ok      Neo4j -[USES]-> Cypher                       0.95
  defect  Neo4j -[DEVELOPED_BY]-> Neo4j                0.80   <- self-loop
  defect  Neo4j -[USES]-> <empty>                      0.95   <- empty endpoint
  defect  Neo4j -[FRIENDS_WITH]-> Cypher               0.90   <- whitelist ပြင်ပ
  defect  Cypher -[IS_A]-> GraphRAG                    0.30   <- confidence နိမ့်
  defect  Neo4j -[USES]-> Cypher (ထပ်)                 0.95   <- duplicate

quality gate (အစဉ်လိုက် ၆ ဆင့်)
  1 missing_endpoint  2 self_loop  3 unknown_predicate
  4 dangling_endpoint 5 low_confidence  6 duplicate
  -> accepted / rejected + reason တိုင်း log

accepted များသာ Neo4j သို့ ရောက်သည်
```

Gate သည် graph ၏ **အရည်အသွေး အာမခံချက်** ဖြစ်သည်။ Reason ကို log
လုပ်ခြင်းကြောင့် မည်သည့် defect အမျိုးအစား များနေသည်ကို တိုင်းတာနိုင်ပြီး
upstream (extractor၊ resolver) ကို ပြန်ပြင်နိုင်သည်။

ဤ code တွင် လေ့လာရမည့် Python concepts များမှာ —

- `elif` chain နှင့် အစဉ်လိုက် ဆုံးဖြတ်ချက်
- `set` ဖြင့် duplicate စစ်ခြင်း (membership O(1))
- `(triple, reason)` tuple စုဆောင်းခြင်း
- `defaultdict(int)` ဖြင့် reason histogram
- `dict(sorted(...))` ဖြင့် output အစီအစဉ် တည်ငြိမ်စေခြင်း
- Float comparison ၏ boundary (`<` နှင့် `<=`)
- `or` ၏ **truthiness** (empty string က falsy)
- `assert` ဖြင့် စစ်ဆေးခြင်း

---

## 1. `MIN_CONFIDENCE` နှင့် boundary comparison

```python
from collections import OrderedDict, defaultdict
from dataclasses import dataclass, field

MIN_CONFIDENCE = 0.60
ALLOWED_PREDICATES = ("IS_A", "USES", "BUILT_ON", "DEVELOPED_BY", "INCLUDES", "RELATED_TO")


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


ENTITY_IDS = {"ent:neo4j", "ent:cypher", "ent:graphrag", "ent:knowledge-graph",
              "ent:entity-resolution", "ent:llm", "ent:transformer"}
NEO4J, CYPHER, GRAPHRAG, KG, ER, LLM, TRF = ("ent:neo4j", "ent:cypher", "ent:graphrag",
                                             "ent:knowledge-graph", "ent:entity-resolution",
                                             "ent:llm", "ent:transformer")

boundary = Triple(NEO4J, "RELATED_TO", GRAPHRAG, [Provenance("doc-002:c01", 0.60, "cooccurrence")])
print("confidence  :", boundary.confidence)
print("<  MIN      :", boundary.confidence < MIN_CONFIDENCE)
print("<= MIN      :", boundary.confidence <= MIN_CONFIDENCE)
```

Output —

```text
confidence  : 0.6
<  MIN      : False
<= MIN      : True
```

| Condition | ရလဒ် | ဆိုလိုသည့် အဓိပ္ပာယ် |
| --- | --- | --- |
| `confidence < MIN_CONFIDENCE` | `False` | ဤ triple ကို **လက်ခံ** (message "≥ 0.60 မှ လက်ခံ") |
| `confidence <= MIN_CONFIDENCE` | `True` | ဤ triple ကို **ပယ်** (message "> 0.60 မှ လက်ခံ") |

Exercise ၏ requirement က **"confidence ≥ 0.60 ဖြစ်ရမည်"** ဖြစ်သဖြင့် `<`
ကို သုံးရသည်။ `<=` သုံးလျှင် **တိကျ 0.60** ဖြစ်သည့် valid triple များ ပယ်ခံရမည် —
threshold တစ်ခုတည်းတွင် မျဉ်းကြောင်း တစ်လုံးကို ရှေ့/နောက် ရွှေ့လိုက်ခြင်းနှင့် တူသည်။

Threshold တစ်ခုတည်းတွင် တန်ဖိုးတူ triple များ ရှိလာလျှင် ဤကဲ့သို့ boundary ကို
test တစ်ခုဖြင့် ပိတ်ထားရသည်။

---

## 2. `quality_gate()` — ဆုံးဖြတ်ချက် ၆ ဆင့်

```python
from collections import OrderedDict, defaultdict
from dataclasses import dataclass, field

MIN_CONFIDENCE = 0.60
ALLOWED_PREDICATES = ("IS_A", "USES", "BUILT_ON", "DEVELOPED_BY", "INCLUDES", "RELATED_TO")


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


def quality_gate(triples, entities):
    accepted, rejected, seen = [], [], set()
    for triple in triples:
        if not triple.subject_id or not triple.object_id:
            rejected.append((triple, "missing_endpoint"))
        elif triple.subject_id == triple.object_id:
            rejected.append((triple, "self_loop"))
        elif triple.predicate not in ALLOWED_PREDICATES:
            rejected.append((triple, "unknown_predicate"))
        elif triple.subject_id not in entities or triple.object_id not in entities:
            rejected.append((triple, "dangling_endpoint"))
        elif triple.confidence < MIN_CONFIDENCE:
            rejected.append((triple, "low_confidence"))
        elif triple.key in seen:
            rejected.append((triple, "duplicate"))
        else:
            seen.add(triple.key)
            accepted.append(triple)
    return {"accepted": accepted, "rejected": rejected}
```

### ဆုံးဖြတ်ချက် ဇယား

| # | Condition | Reason | ဤစစ်ဆေးမှုက ဖော်ထုတ်သည့် အန္တရာယ် |
| --- | --- | --- | --- |
| 1 | `not subject_id or not object_id` | `missing_endpoint` | empty id — Cypher `MATCH` လုံးဝ မကိုက် |
| 2 | `subject_id == object_id` | `self_loop` | coreference မှားခြင်း၏ လက္ခဏာ |
| 3 | `predicate not in ALLOWED_PREDICATES` | `unknown_predicate` | relationship type အသစ် — index/query ပျက် |
| 4 | endpoint များ entities ထဲ မရှိ | `dangling_endpoint` | graph အပြင်ဘက် ညွှန်နေသည့် edge |
| 5 | `confidence < MIN_CONFIDENCE` | `low_confidence` | မှန်းဆချက် (co-occurrence) ရလဒ် |
| 6 | `key in seen` | `duplicate` | exact ထပ် — `MERGE` ကို မလိုအပ်ဘဲ ဖိစီးစေ |
| — | အားလုံး ဖြတ် | (accept) | `seen.add(key)` + `accepted.append(triple)` |

### အဘယ်ကြောင့် `elif` ဖြစ်ပြီး `if` မဟုတ်သနည်း။

Reason တစ်ခုတည်း **အတိအကျ** log လုပ်ရန် `elif` လိုသည်။ ရှေးဆင့်တစ်ခုက
မှန်သွားလျှင် ကျန်သည်များကို မစစ်တော့ပါ — ထို့ကြောင့် histogram သည်
"triple အရေအတွက် = rejection အရေအတွက်" ဖြစ်သည်။

### "Empty string သည် falsy ဖြစ်သည်" — `not subject_id`

`not triple.subject_id` သည် `subject_id == ""` နှင့် **တူညီမှု မရှိ** ပါ —
`not` သည် **truthiness** ကို စစ်သည်။ `""`၊ `0`၊ `[]`၊ `None` အားလုံး falsy ဖြစ်သည်။

```python
for value in ["", "ent:neo4j", None, 0]:
    print("%-12r truthy=%s" % (value, bool(value)))
```

Output —

```text
''           truthy=False
'ent:neo4j'  truthy=True
None         truthy=False
0            truthy=False
```

ထို့ကြောင့် `not triple.object_id` သည် `object_id` သည် `""` ဖြစ်စေ၊ `None`
ဖြစ်စေ ဖမ်းမိသည်။ Id တစ်ခုက `"0"` (string) ဖြစ်နေလျှင်တော့ non-empty string
ဖြစ်သဖြင့် truthy ဖြစ်သည် — ထို့ကြောင့် ဤစစ်ဆေးချက်သည် လုံခြုံသည်။

### `seen` — `set` ဖြင့် duplicate စစ်ခြင်း

```python
seen = set()
...
elif triple.key in seen:
    rejected.append((triple, "duplicate"))
else:
    seen.add(triple.key)
    accepted.append(triple)
```

`seen.add()` ကို **accept branch ထဲတွင်သာ** ခေါ်သည်။ ထို့ကြောင့် ဖယ်ခံရသည့်
triple များသည် `seen` ကို မထိပါ။ `triple.key` သည် `tuple` ဖြစ်သဖြင့်
hashable ဖြစ်ပြီး `in` က O(1) ဖြစ်သည်။ List ဖြင့် စစ်လျှင် O(n²) ဖြစ်မည်။

---

## 3. ရလဒ် — candidate ၁၃ မှ accepted ၅

```python
from collections import OrderedDict, defaultdict
from dataclasses import dataclass, field

MIN_CONFIDENCE = 0.60
ALLOWED_PREDICATES = ("IS_A", "USES", "BUILT_ON", "DEVELOPED_BY", "INCLUDES", "RELATED_TO")


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


ENTITY_IDS = {"ent:neo4j", "ent:cypher", "ent:graphrag", "ent:knowledge-graph",
              "ent:entity-resolution", "ent:llm", "ent:transformer"}
NEO4J, CYPHER, GRAPHRAG, KG, ER, LLM, TRF = ("ent:neo4j", "ent:cypher", "ent:graphrag",
                                             "ent:knowledge-graph", "ent:entity-resolution",
                                             "ent:llm", "ent:transformer")
MERGED = [
    Triple(NEO4J, "USES", CYPHER, [Provenance("doc-001:c00", 0.95, "pattern:uses")]),
    Triple(GRAPHRAG, "BUILT_ON", KG, [Provenance("doc-001:c00", 0.95, "pattern:built_on"),
                                      Provenance("doc-002:c00", 0.95, "pattern:built_on")]),
    Triple(GRAPHRAG, "BUILT_ON", NEO4J, [Provenance("doc-002:c00", 0.80, "pattern:built_on")]),
    Triple(NEO4J, "DEVELOPED_BY", NEO4J, [Provenance("doc-002:c00", 0.80, "pattern:developed_by")]),
    Triple(NEO4J, "RELATED_TO", GRAPHRAG, [Provenance("doc-002:c01", 0.45, "cooccurrence")]),
    Triple(GRAPHRAG, "RELATED_TO", CYPHER, [Provenance("doc-002:c01", 0.45, "cooccurrence")]),
    Triple(GRAPHRAG, "USES", ER, [Provenance("doc-003:c00", 0.95, "pattern:uses")]),
    Triple(LLM, "IS_A", TRF, [Provenance("doc-003:c00", 0.95, "pattern:is_a")]),
]
CANDIDATES = MERGED + [
    Triple(NEO4J, "USES", "", [Provenance("doc-001:c00", 0.95, "pattern:uses")]),
    Triple(CYPHER, "USES", CYPHER, [Provenance("doc-003:c00", 0.95, "pattern:uses")]),
    Triple(NEO4J, "FRIENDS_WITH", CYPHER, [Provenance("doc-003:c00", 0.90, "pattern:friends_with")]),
    Triple(CYPHER, "IS_A", GRAPHRAG, [Provenance("doc-003:c00", 0.30, "pattern:is_a")]),
    Triple(NEO4J, "USES", CYPHER, [Provenance("doc-002:c00", 0.95, "pattern:uses")]),
]


def quality_gate(triples, entities):
    accepted, rejected, seen = [], [], set()
    for triple in triples:
        if not triple.subject_id or not triple.object_id:
            rejected.append((triple, "missing_endpoint"))
        elif triple.subject_id == triple.object_id:
            rejected.append((triple, "self_loop"))
        elif triple.predicate not in ALLOWED_PREDICATES:
            rejected.append((triple, "unknown_predicate"))
        elif triple.subject_id not in entities or triple.object_id not in entities:
            rejected.append((triple, "dangling_endpoint"))
        elif triple.confidence < MIN_CONFIDENCE:
            rejected.append((triple, "low_confidence"))
        elif triple.key in seen:
            rejected.append((triple, "duplicate"))
        else:
            seen.add(triple.key)
            accepted.append(triple)
    return {"accepted": accepted, "rejected": rejected}


gate = quality_gate(CANDIDATES, ENTITY_IDS)
reasons = defaultdict(int)
for triple, reason in gate["rejected"]:
    reasons[reason] += 1
    print("  REJECT %-17s %s -[%s]-> %s" % (reason, triple.subject_id, triple.predicate,
                                            triple.object_id or "<empty>"))
print("candidates : %d (merged triples + 5 injected defects)" % len(CANDIDATES))
print("accepted   : %d" % len(gate["accepted"]))
print("rejected   : %s" % dict(sorted(reasons.items())))
```

Output —

```text
  REJECT self_loop         ent:neo4j -[DEVELOPED_BY]-> ent:neo4j
  REJECT low_confidence    ent:neo4j -[RELATED_TO]-> ent:graphrag
  REJECT low_confidence    ent:graphrag -[RELATED_TO]-> ent:cypher
  REJECT missing_endpoint  ent:neo4j -[USES]-> <empty>
  REJECT self_loop         ent:cypher -[USES]-> ent:cypher
  REJECT unknown_predicate ent:neo4j -[FRIENDS_WITH]-> ent:cypher
  REJECT low_confidence    ent:cypher -[IS_A]-> ent:graphrag
  REJECT duplicate         ent:neo4j -[USES]-> ent:cypher
candidates : 13 (merged triples + 5 injected defects)
accepted   : 5
rejected   : {'duplicate': 1, 'low_confidence': 3, 'missing_endpoint': 1, 'self_loop': 2, 'unknown_predicate': 1}
```

### Log အစီအစဉ်သည် candidate အစီအစဉ်အတိုင်း ဖြစ်သည်

Rejection များကို reason အလိုက် မစီပါ — `for triple in triples` ၏
အစီအစဉ်အတိုင်း ထွက်သည်။ ထို့ကြောင့် log သည် "မည်သည့် defect က မည်သည့်နေရာတွင်
ပထမ တွေ့ခဲ့သည်ကို" ပြသည် — debugging အတွက် histogram ထက် အသုံးဝင်သည်။

| Reason | အရေအတွက် | မည်သည့် candidate |
| --- | --- | --- |
| `self_loop` | 2 | `Neo4j -[DEVELOPED_BY]-> Neo4j`၊ `Cypher -[USES]-> Cypher` |
| `low_confidence` | 3 | `RELATED_TO` နှစ်ခု (0.45)၊ `IS_A` (0.30) |
| `missing_endpoint` | 1 | object က `""` ဖြစ်သော `USES` |
| `unknown_predicate` | 1 | `FRIENDS_WITH` |
| `duplicate` | 1 | `Neo4j -[USES]-> Cypher` (ဒုတိယမြောက်) |
| **စုစုပေါင်း** | **8** | candidates 13 − accepted 5 |

`dict(sorted(reasons.items()))` သည် output ကို reason အက္ခရာအစဉ် (`duplicate`၊
`low_confidence`၊ `missing_endpoint`၊ `self_loop`၊ `unknown_predicate`) ဖြင့်
တည်ငြိမ်စေသည်။ Defaultdict ကို တိုက်ရိုက် print လျှင် insertion order ဖြစ်ပြီး
reason တွေ့သည့် အစီအစဉ် ပြောင်းလဲနိုင်သည်။

---

## 4. Trap — `if` chain အစား သီးခြား `if` များ

`elif` များကို သီးခြား `if` များအဖြစ် ပြောင်းကြည့်ပါ။

```python
from collections import OrderedDict, defaultdict
from dataclasses import dataclass, field

MIN_CONFIDENCE = 0.60
ALLOWED_PREDICATES = ("IS_A", "USES", "BUILT_ON", "DEVELOPED_BY", "INCLUDES", "RELATED_TO")


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


ENTITY_IDS = {"ent:neo4j", "ent:cypher", "ent:graphrag", "ent:knowledge-graph",
              "ent:entity-resolution", "ent:llm", "ent:transformer"}
NEO4J, CYPHER, GRAPHRAG, KG, ER, LLM, TRF = ("ent:neo4j", "ent:cypher", "ent:graphrag",
                                             "ent:knowledge-graph", "ent:entity-resolution",
                                             "ent:llm", "ent:transformer")
MERGED = [
    Triple(NEO4J, "USES", CYPHER, [Provenance("doc-001:c00", 0.95, "pattern:uses")]),
    Triple(GRAPHRAG, "BUILT_ON", KG, [Provenance("doc-001:c00", 0.95, "pattern:built_on"),
                                      Provenance("doc-002:c00", 0.95, "pattern:built_on")]),
    Triple(GRAPHRAG, "BUILT_ON", NEO4J, [Provenance("doc-002:c00", 0.80, "pattern:built_on")]),
    Triple(NEO4J, "DEVELOPED_BY", NEO4J, [Provenance("doc-002:c00", 0.80, "pattern:developed_by")]),
    Triple(NEO4J, "RELATED_TO", GRAPHRAG, [Provenance("doc-002:c01", 0.45, "cooccurrence")]),
    Triple(GRAPHRAG, "RELATED_TO", CYPHER, [Provenance("doc-002:c01", 0.45, "cooccurrence")]),
    Triple(GRAPHRAG, "USES", ER, [Provenance("doc-003:c00", 0.95, "pattern:uses")]),
    Triple(LLM, "IS_A", TRF, [Provenance("doc-003:c00", 0.95, "pattern:is_a")]),
]
CANDIDATES = MERGED + [
    Triple(NEO4J, "USES", "", [Provenance("doc-001:c00", 0.95, "pattern:uses")]),
    Triple(CYPHER, "USES", CYPHER, [Provenance("doc-003:c00", 0.95, "pattern:uses")]),
    Triple(NEO4J, "FRIENDS_WITH", CYPHER, [Provenance("doc-003:c00", 0.90, "pattern:friends_with")]),
    Triple(CYPHER, "IS_A", GRAPHRAG, [Provenance("doc-003:c00", 0.30, "pattern:is_a")]),
    Triple(NEO4J, "USES", CYPHER, [Provenance("doc-002:c00", 0.95, "pattern:uses")]),
]


def gate_all_if(triples, entities):
    accepted, rejected, seen = [], [], set()
    for triple in triples:
        bad = False
        if not triple.subject_id or not triple.object_id:
            rejected.append((triple, "missing_endpoint")); bad = True
        if triple.subject_id == triple.object_id:
            rejected.append((triple, "self_loop")); bad = True
        if triple.predicate not in ALLOWED_PREDICATES:
            rejected.append((triple, "unknown_predicate")); bad = True
        if triple.subject_id not in entities or triple.object_id not in entities:
            rejected.append((triple, "dangling_endpoint")); bad = True
        if triple.confidence < MIN_CONFIDENCE:
            rejected.append((triple, "low_confidence")); bad = True
        if triple.key in seen:
            rejected.append((triple, "duplicate")); bad = True
        if not bad:
            seen.add(triple.key)
            accepted.append(triple)
    return {"accepted": accepted, "rejected": rejected}


gate = gate_all_if(CANDIDATES, ENTITY_IDS)
reasons = defaultdict(int)
for triple, reason in gate["rejected"]:
    reasons[reason] += 1
print("accepted   : %d" % len(gate["accepted"]))
print("rejected   : %s" % dict(sorted(reasons.items())))
print("rejection count : %d" % len(gate["rejected"]))
```

Output —

```text
accepted   : 5
rejected   : {'dangling_endpoint': 1, 'duplicate': 1, 'low_confidence': 3, 'missing_endpoint': 1, 'self_loop': 2, 'unknown_predicate': 1}
rejection count : 9
```

### ကွာခြားချက်

| | `elif` chain (မှန်) | သီးခြား `if` (trap) |
| --- | --- | --- |
| accepted | 5 | 5 |
| rejection records | **8** | **9** |
| `dangling_endpoint` | မပါ | **1** (မှားယွင်း) |

`dangling_endpoint` သည် မှားယွင်း ပေါ်လာသည် — empty endpoint triple ၏
`object_id` က `""` ဖြစ်ပြီး `"" not in entities` က `True` ဖြစ်သဖြင့်
ထို triple သည် reason **နှစ်ခု** ရသည်။ `elif` chain သည် ပထမ reason
(`missing_endpoint`) တွေ့သည်နှင့် ရပ်သောကြောင့် ဤအမှား မဖြစ်ပါ။

Accepted အရေအတွက် မပြောင်းခြင်းကို သတိထားပါ — အမှားသည် **reason histogram**
တွင်သာ ပေါ်ပြီး accepted set ကို မထိပါ။ ထို့ကြောင့် histogram ကို မကြည့်ဘဲ
accepted count ကိုသာ စစ်လျှင် bug ကို လွတ်သွားမည်။

---

## 5. Trap — စစ်ဆေးမှု အစဉ် (ပြောင်းလိုက်လျှင် reason ပြောင်းသည်)

Structure ချို့ယွင်းမှုနှင့် confidence နိမ့်မှု **တစ်ခါတည်း** ဖြစ်နေသည့် triple
တစ်ခုကို စမ်းကြည့်ပါ။

```python
from collections import OrderedDict, defaultdict
from dataclasses import dataclass, field

MIN_CONFIDENCE = 0.60
ALLOWED_PREDICATES = ("IS_A", "USES", "BUILT_ON", "DEVELOPED_BY", "INCLUDES", "RELATED_TO")


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


ENTITY_IDS = {"ent:neo4j", "ent:cypher", "ent:graphrag", "ent:knowledge-graph",
              "ent:entity-resolution", "ent:llm", "ent:transformer"}
NEO4J = "ent:neo4j"


def gate_structure_first(triples, entities):
    for triple in triples:
        if not triple.subject_id or not triple.object_id:
            return "missing_endpoint"
        elif triple.subject_id == triple.object_id:
            return "self_loop"
        elif triple.predicate not in ALLOWED_PREDICATES:
            return "unknown_predicate"
        elif triple.subject_id not in entities or triple.object_id not in entities:
            return "dangling_endpoint"
        elif triple.confidence < MIN_CONFIDENCE:
            return "low_confidence"
    return "accept"


def gate_confidence_first(triples, entities):
    for triple in triples:
        if triple.confidence < MIN_CONFIDENCE:
            return "low_confidence"
        elif triple.subject_id == triple.object_id:
            return "self_loop"
        elif not triple.subject_id or not triple.object_id:
            return "missing_endpoint"
        elif triple.predicate not in ALLOWED_PREDICATES:
            return "unknown_predicate"
        elif triple.subject_id not in entities or triple.object_id not in entities:
            return "dangling_endpoint"
    return "accept"


self_loop_low_conf = Triple(NEO4J, "DEVELOPED_BY", NEO4J,
                            [Provenance("doc-003:c01", 0.30, "cooccurrence")])
print("confidence       :", self_loop_low_conf.confidence)
print("structure first  :", gate_structure_first([self_loop_low_conf], ENTITY_IDS))
print("confidence first :", gate_confidence_first([self_loop_low_conf], ENTITY_IDS))
```

Output —

```text
confidence       : 0.3
structure first  : self_loop
confidence first : low_confidence
```

| အစဉ် | Reason | ဆိုလိုသည့် အချက် |
| --- | --- | --- |
| structure အရင် (မှန်) | `self_loop` | coreference မှားယွင်းမှု — upstream extractor ပြင်ရမည် |
| confidence အရင် (trap) | `low_confidence` | structure ချို့ယွင်းမှု **ဖုံးကွယ်** သွားသည် |

`low_confidence` သည် ကျယ်ပြန့်သည့် blanket reason ဖြစ်သည် — ထို့ကြောင့်
confidence ကို အရင်စစ်လျှင် self-loop ဖြစ်နေသည်ကို မသိတော့ဘဲ pipeline ကို
"threshold နိမ့်သောကြောင့် ဖယ်လိုက်ခြင်း" ဟု မှားယူဆမည်။ Structure ကို အရင်
စစ်ခြင်းဖြင့် **တိကျသည့် signal** ကို ထိန်းသိမ်းသည်။

### အဘယ်ကြောင့် self-loop သည် အရေးကြီးသည့် signal ဖြစ်သနည်း။

Coreference resolution မှားယွင်းသည့်အခါ entity တစ်ခုက မိမိကိုယ်ကို
ဆက်သွားသည့် edge ဖြစ်လာသည် (`Neo4j -[DEVELOPED_BY]-> Neo4j`)။
ဤအချက်သည် upstream bug ၏ လက္ခဏာ ဖြစ်သည် — ဖယ်လိုက်ရုံဖြင့် မလုံလောက်ပါ။
Reason ကို log ထားခြင်းဖြင့် alias mapping သို့မဟုတ် coreference model ကို
ပြန်ပြင်နိုင်သည်။

---

## 6. Code တစ်ခုလုံး — Run လုပ်နိုင်သော Version

```python
from collections import OrderedDict, defaultdict
from dataclasses import dataclass, field

MIN_CONFIDENCE = 0.60
ALLOWED_PREDICATES = ("IS_A", "USES", "BUILT_ON", "DEVELOPED_BY", "INCLUDES", "RELATED_TO")


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


ENTITY_IDS = {"ent:neo4j", "ent:cypher", "ent:graphrag", "ent:knowledge-graph",
              "ent:entity-resolution", "ent:llm", "ent:transformer"}
NEO4J, CYPHER, GRAPHRAG, KG, ER, LLM, TRF = ("ent:neo4j", "ent:cypher", "ent:graphrag",
                                             "ent:knowledge-graph", "ent:entity-resolution",
                                             "ent:llm", "ent:transformer")
MERGED = [
    Triple(NEO4J, "USES", CYPHER, [Provenance("doc-001:c00", 0.95, "pattern:uses")]),
    Triple(GRAPHRAG, "BUILT_ON", KG, [Provenance("doc-001:c00", 0.95, "pattern:built_on"),
                                      Provenance("doc-002:c00", 0.95, "pattern:built_on")]),
    Triple(GRAPHRAG, "BUILT_ON", NEO4J, [Provenance("doc-002:c00", 0.80, "pattern:built_on")]),
    Triple(NEO4J, "DEVELOPED_BY", NEO4J, [Provenance("doc-002:c00", 0.80, "pattern:developed_by")]),
    Triple(NEO4J, "RELATED_TO", GRAPHRAG, [Provenance("doc-002:c01", 0.45, "cooccurrence")]),
    Triple(GRAPHRAG, "RELATED_TO", CYPHER, [Provenance("doc-002:c01", 0.45, "cooccurrence")]),
    Triple(GRAPHRAG, "USES", ER, [Provenance("doc-003:c00", 0.95, "pattern:uses")]),
    Triple(LLM, "IS_A", TRF, [Provenance("doc-003:c00", 0.95, "pattern:is_a")]),
]
CANDIDATES = MERGED + [
    Triple(NEO4J, "USES", "", [Provenance("doc-001:c00", 0.95, "pattern:uses")]),
    Triple(CYPHER, "USES", CYPHER, [Provenance("doc-003:c00", 0.95, "pattern:uses")]),
    Triple(NEO4J, "FRIENDS_WITH", CYPHER, [Provenance("doc-003:c00", 0.90, "pattern:friends_with")]),
    Triple(CYPHER, "IS_A", GRAPHRAG, [Provenance("doc-003:c00", 0.30, "pattern:is_a")]),
    Triple(NEO4J, "USES", CYPHER, [Provenance("doc-002:c00", 0.95, "pattern:uses")]),
]


def quality_gate(triples, entities):
    accepted, rejected, seen = [], [], set()
    for triple in triples:
        if not triple.subject_id or not triple.object_id:
            rejected.append((triple, "missing_endpoint"))
        elif triple.subject_id == triple.object_id:
            rejected.append((triple, "self_loop"))
        elif triple.predicate not in ALLOWED_PREDICATES:
            rejected.append((triple, "unknown_predicate"))
        elif triple.subject_id not in entities or triple.object_id not in entities:
            rejected.append((triple, "dangling_endpoint"))
        elif triple.confidence < MIN_CONFIDENCE:
            rejected.append((triple, "low_confidence"))
        elif triple.key in seen:
            rejected.append((triple, "duplicate"))
        else:
            seen.add(triple.key)
            accepted.append(triple)
    return {"accepted": accepted, "rejected": rejected}


gate = quality_gate(CANDIDATES, ENTITY_IDS)
reasons = defaultdict(int)
for triple, reason in gate["rejected"]:
    reasons[reason] += 1
    print("  REJECT %-17s %s -[%s]-> %s" % (reason, triple.subject_id, triple.predicate,
                                            triple.object_id or "<empty>"))
print("candidates : %d (merged triples + 5 injected defects)" % len(CANDIDATES))
print("accepted   : %d" % len(gate["accepted"]))
print("rejected   : %s" % dict(sorted(reasons.items())))

assert len(gate["accepted"]) == 5 and len(CANDIDATES) == 13
assert dict(reasons) == {"self_loop": 2, "low_confidence": 3, "missing_endpoint": 1,
                         "unknown_predicate": 1, "duplicate": 1}
```

Output —

```text
  REJECT self_loop         ent:neo4j -[DEVELOPED_BY]-> ent:neo4j
  REJECT low_confidence    ent:neo4j -[RELATED_TO]-> ent:graphrag
  REJECT low_confidence    ent:graphrag -[RELATED_TO]-> ent:cypher
  REJECT missing_endpoint  ent:neo4j -[USES]-> <empty>
  REJECT self_loop         ent:cypher -[USES]-> ent:cypher
  REJECT unknown_predicate ent:neo4j -[FRIENDS_WITH]-> ent:cypher
  REJECT low_confidence    ent:cypher -[IS_A]-> ent:graphrag
  REJECT duplicate         ent:neo4j -[USES]-> ent:cypher
candidates : 13 (merged triples + 5 injected defects)
accepted   : 5
rejected   : {'duplicate': 1, 'low_confidence': 3, 'missing_endpoint': 1, 'self_loop': 2, 'unknown_predicate': 1}
```

ဤ output သည် `lab.py` ၏ Exercise 5 နှင့် တူညီသည်။

---

## 7. ကိုယ်တိုင်လေ့ကျင့်ကြည့်ပါ

**မေးခွန်း** — အောက်ပါ gate သည် `triple` ကို မည်သည့် reason ဖြင့် ပယ်မည်နည်း။

```python
ALLOWED_PREDICATES = ("IS_A", "USES", "BUILT_ON", "DEVELOPED_BY", "INCLUDES", "RELATED_TO")
entities = {"ent:neo4j", "ent:cypher"}
MIN_CONFIDENCE = 0.60

triple = {"subject_id": "ent:neo4j", "predicate": "USES", "object_id": "ent:mysql",
          "confidence": 0.95}

if not triple["subject_id"] or not triple["object_id"]:
    reason = "missing_endpoint"
elif triple["subject_id"] == triple["object_id"]:
    reason = "self_loop"
elif triple["predicate"] not in ALLOWED_PREDICATES:
    reason = "unknown_predicate"
elif triple["subject_id"] not in entities or triple["object_id"] not in entities:
    reason = "dangling_endpoint"
elif triple["confidence"] < MIN_CONFIDENCE:
    reason = "low_confidence"
else:
    reason = "accept"
print(reason)
```

1. `accept` — endpoint နှစ်ခုလုံး ရှိပြီး confidence မြင့်သည်
2. `dangling_endpoint` — `ent:mysql` သည် entities ထဲ မရှိ
3. `unknown_predicate` — `USES` သည် whitelist ပြင်ပ
4. `low_confidence` — 0.95 < 0.60

<details>
<summary>အဖြေ ကြည့်ရန်</summary>

**အဖြေ — 2. `dangling_endpoint`**

အကြောင်းရင်း — `ent:mysql` သည် `entities = {"ent:neo4j", "ent:cypher"}` ထဲ
မပါပါ။ စစ်ဆေးမှု အစဉ်အရ ပထမသုံးခု မမှန်သဖြင့် စတုတ္ထစစ်ဆေးချက်
(`... or triple["object_id"] not in entities`) သို့ ရောက်ပြီး `True` ဖြစ်သည်။
ထို့ကြောင့် `dangling_endpoint` ရသည်။ Confidence 0.95 သည် threshold ကို
ဖြတ်သော်လည်း **အရင် အဆင့်တွင် ပယ်ခံရသဖြင့်** ထို အဆင့်သို့ မရောက်ပါ။ ဤအချက်သည်
"structure gate သည် confidence gate အရင်" ဆိုသည့် စည်းမျဉ်း၏ လက်တွေ့
သက်ရောက်မှုကို ပြသည်။

</details>

---

**အဓိက မှတ်ထားရန်** — Quality gate သည် extraction ၏ open-ended output ကို
Neo4j အတွက် လုံခြုံသည့် input ဖြစ်စေသည်။ `elif` chain သည် triple တစ်ခုစီအတွက်
reason **တစ်ခုတည်း** ပေးသဖြင့် histogram တိကျသည် — သီးခြား `if` များဖြင့်
ရေးလျှင် reason များ ပွားလာပြီး ရေတွက်မှု မှားသည်။ အစဉ်သည်လည်း အရေးကြီးသည် —
structure ကို confidence အရင်စစ်ခြင်းဖြင့် self-loop၊ empty endpoint နှင့်
whitelist ပြင်ပ predicate များကို `low_confidence` ဆိုသည့် blanket reason
အောက်တွင် ဖုံးကွယ်မသွားစေပါ။ Threshold ကို `<` (≥ မှ accept) ဖြင့် သတ်မှတ်ခြင်းသည်
boundary ဆုံးရှုံးမှုကို တားသည်။
