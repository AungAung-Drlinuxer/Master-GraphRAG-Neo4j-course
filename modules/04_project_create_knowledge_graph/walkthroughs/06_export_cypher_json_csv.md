# Walkthrough 06 — Cypher / JSON / CSV Export (Exercise 6)

> ဤဖိုင်သည် Module 04 ၏ `solution.md` ထဲက Exercise 6 ကို **Python အခြေခံမှ စ၍**
> အပိုင်းလိုက် ရှင်းပြသည့် walkthrough ဖြစ်သည်။

---

## 0. ဤ Exercise က ဘာကို ဖြေရှင်းပေးသလဲ။

Validated graph ကို Neo4j သို့ ရောက်စေရန် **format သုံးမျိုး** ထုတ်သည်။
format တိုင်းတွင် ရည်ရွယ်ချက် မတူညီပါ။

```text
validated graph (entities 7 + accepted triples 5)
  |
  +-- Cypher statements  -> Neo4j driver ဖြင့် တိုက်ရိုက် run (incremental update)
  |     MERGE (n:Entity {id: $id}) SET n.name = $name, n.type = $type
  |     MATCH ... MERGE (a)-[r:<TYPE> {id: $rel_id}]->(b) SET ... = $param
  |
  +-- JSON               -> API / downstream service / diff-able artifact
  |     {"nodes": [...], "relationships": [...]}
  |
  +-- CSV                -> Neo4j Admin Import (bulk load၊ offline)
        nodes.csv        header: entity_id:ID, name, type, :LABEL
        relationships.csv header: :START_ID, :END_ID, :TYPE, rel_id, ...

format တိုင်း၏ အခြေခံစည်းမျဉ်း —
  * Cypher သည် parameter ($param) သာ သုံးရမည် — string interpolation မဟုတ်
  * JSON သည် sort_keys=True ဖြင့် run တိုင်း တူညီရမည်
  * CSV သည် comma ပါသော value များကို မှန်ကန်စွာ quote လုပ်ရမည်
```

ဤ code တွင် လေ့လာရမည့် Python concepts များမှာ —

- Module-level constant (`NODE_MERGE`) နှင့် multi-line string
- List comprehension ဖြင့် statement စာရင်း ဖန်တီးခြင်း
- `%` ဖြင့် query template ထဲ type ထည့်ခြင်း (နှင့် ၎င်း၏ အန္တရာယ်)
- `json.dumps(..., indent=2, sort_keys=True, ensure_ascii=False)`
- `json.loads()` round-trip
- `io.StringIO` နှင့် `csv.writer()`၊ `lineterminator`
- `";".join(sorted(set(...)))`
- `*` unpacking မဟုတ်ဘဲ **frozenset/set** ဖြင့် dedupe
- `all(...)` ဖြင့် security assertion
- `tuple` comprehension နှင့် generator (`set` အတွင်း)

---

## 1. `NODE_MERGE` — parameterized query template

```python
import csv
import io
import json
import re
from collections import OrderedDict
from dataclasses import dataclass, field

ALLOWED_PREDICATES = ("IS_A", "USES", "BUILT_ON", "DEVELOPED_BY", "INCLUDES", "RELATED_TO")
NODE_MERGE = "MERGE (n:Entity {id: $id})\nSET n.name = $name, n.type = $type"


def slug(text):
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")


def rel_id(subject_id, predicate, object_id):
    return "rel:" + slug("%s-%s-%s" % (subject_id, predicate, object_id))


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


@dataclass
class Entity:
    entity_id: str
    name: str
    type: str
    aliases: list = field(default_factory=list)


ENTITIES = OrderedDict()
for _name, _type in [("Neo4j", "Technology"), ("Cypher", "Technology"), ("GraphRAG", "Technology"),
                     ("Knowledge Graph", "Concept"), ("Entity Resolution", "Concept"),
                     ("LLM", "Technology"), ("Transformer", "Technology")]:
    _eid = "ent:" + slug(_name)
    ENTITIES[_eid] = Entity(_eid, _name, _type)
NEO4J, CYPHER, GRAPHRAG = "ent:neo4j", "ent:cypher", "ent:graphrag"
KG, ER, LLM, TRF = "ent:knowledge-graph", "ent:entity-resolution", "ent:llm", "ent:transformer"
ACCEPTED = [
    Triple(NEO4J, "USES", CYPHER, [Provenance("doc-001:c00", 0.95, "pattern:uses")]),
    Triple(GRAPHRAG, "BUILT_ON", KG, [Provenance("doc-001:c00", 0.95, "pattern:built_on"),
                                      Provenance("doc-002:c00", 0.95, "pattern:built_on")]),
    Triple(GRAPHRAG, "BUILT_ON", NEO4J, [Provenance("doc-002:c00", 0.80, "pattern:built_on")]),
    Triple(GRAPHRAG, "USES", ER, [Provenance("doc-003:c00", 0.95, "pattern:uses")]),
    Triple(LLM, "IS_A", TRF, [Provenance("doc-003:c00", 0.95, "pattern:is_a")]),
]

print(NODE_MERGE)
print()
print(repr(NODE_MERGE))
```

Output —

```text
MERGE (n:Entity {id: $id})
SET n.name = $name, n.type = $type

'MERGE (n:Entity {id: $id})\nSET n.name = $name, n.type = $type'
```

### `.` `\n` နှင့် `$param`

| အပိုင်း | အဓိပ္ပာယ် |
| --- | --- |
| `MERGE (n:Entity {id: $id})` | id တူလျှင် ရှိသည့် node ကို ယူ၊ မရှိလျှင် ဖန်တီး |
| `\n` | Cypher statement ခွဲခြားသည့် newline (လူဖတ်ရန်) |
| `$id`၊ `$name`၊ `$type` | **parameter** — တန်ဖိုးကို query string ထဲ မထည့် |

`repr()` သည် `\n` ကို **escape** ဖြင့် ပြသည် — string ထဲ တကယ် ပါသည့် character
သည် newline ဖြစ်ပြီး `\n` နှစ်လုံး မဟုတ်ပါ။ Debugging တွင် ဤအချက်သည်
အရေးကြီးသည် — `print` သည် newline ကို ဖျက်ပြပြီး `repr` သည် ထိန်းပြသည်။

`SET n.name = $name` သည် `MERGE` ပြီးနောက် property များကို **update** သည်။
`MERGE` ထဲ property ထည့်လျှင် ထို property များကို identity အဖြစ် ယူပြီး
`id` ပြောင်းသွားသည့် အခါ node အသစ် ဖန်တီးမည်။ ထို့ကြောင့် identity ကို
`id` တစ်ခုတည်း ထားပြီး ကျန်သည်ကို `SET` ဖြင့် ရေးခြင်း ဖြစ်သည်။

---

## 2. `rel_id()` — relationship အတွက် deterministic id

```python
import csv
import io
import json
import re
from collections import OrderedDict
from dataclasses import dataclass, field

ALLOWED_PREDICATES = ("IS_A", "USES", "BUILT_ON", "DEVELOPED_BY", "INCLUDES", "RELATED_TO")
NODE_MERGE = "MERGE (n:Entity {id: $id})\nSET n.name = $name, n.type = $type"


def slug(text):
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")


def rel_id(subject_id, predicate, object_id):
    return "rel:" + slug("%s-%s-%s" % (subject_id, predicate, object_id))


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


@dataclass
class Entity:
    entity_id: str
    name: str
    type: str
    aliases: list = field(default_factory=list)


ENTITIES = OrderedDict()
for _name, _type in [("Neo4j", "Technology"), ("Cypher", "Technology"), ("GraphRAG", "Technology"),
                     ("Knowledge Graph", "Concept"), ("Entity Resolution", "Concept"),
                     ("LLM", "Technology"), ("Transformer", "Technology")]:
    _eid = "ent:" + slug(_name)
    ENTITIES[_eid] = Entity(_eid, _name, _type)
NEO4J, CYPHER, GRAPHRAG = "ent:neo4j", "ent:cypher", "ent:graphrag"
KG, ER, LLM, TRF = "ent:knowledge-graph", "ent:entity-resolution", "ent:llm", "ent:transformer"
ACCEPTED = [
    Triple(NEO4J, "USES", CYPHER, [Provenance("doc-001:c00", 0.95, "pattern:uses")]),
    Triple(GRAPHRAG, "BUILT_ON", KG, [Provenance("doc-001:c00", 0.95, "pattern:built_on"),
                                      Provenance("doc-002:c00", 0.95, "pattern:built_on")]),
    Triple(GRAPHRAG, "BUILT_ON", NEO4J, [Provenance("doc-002:c00", 0.80, "pattern:built_on")]),
    Triple(GRAPHRAG, "USES", ER, [Provenance("doc-003:c00", 0.95, "pattern:uses")]),
    Triple(LLM, "IS_A", TRF, [Provenance("doc-003:c00", 0.95, "pattern:is_a")]),
]

print(rel_id("ent:graphrag", "BUILT_ON", "ent:knowledge-graph"))
print(rel_id("ent:neo4j", "USES", "ent:cypher"))
print(slug("ent:graphrag-BUILT_ON-ent:knowledge-graph"))
```

Output —

```text
rel:ent-graphrag-built-on-ent-knowledge-graph
rel:ent-neo4j-uses-ent-cypher
ent-graphrag-built-on-ent-knowledge-graph
```

### `slug("%s-%s-%s" % (...))` — အပိုင်းသုံးခုမှ id တစ်ခု

| အဆင့် | တန်ဖိုး |
| --- | --- |
| input | `"ent:graphrag"`၊ `"BUILT_ON"`၊ `"ent:knowledge-graph"` |
| `%s-%s-%s` | `"ent:graphrag-BUILT_ON-ent:knowledge-graph"` |
| `slug()` | `"ent-graphrag-built-on-ent-knowledge-graph"` |
| prefix | `"rel:ent-graphrag-built-on-ent-knowledge-graph"` |

`rel:` prefix သည် ဤ id space ကို entity (`ent:`) နှင့် ခွဲသည်။ Slug သည် `:`၊ `_`
နှင့် uppercase များကို `-`/lowercase သို့ ပြောင်းသဖြင့် id သည် Cypher property
အဖြစ်၊ file name အဖြစ် လုံခြုံသည်။

**deterministic** ဖြစ်ခြင်းသည် အဓိက ဖြစ်သည် — triple တူလျှင် `rel_id` တူသည်။ ထို့ကြောင့်
`MERGE (a)-[r:... {id: $rel_id}]->(b)` သည် duplicate edge ကို မဖန်တီးဘဲ
property များကိုသာ update လုပ်သည်။

---

## 3. `export_cypher()` — node statement + relationship statement

```python
import csv
import io
import json
import re
from collections import OrderedDict
from dataclasses import dataclass, field

ALLOWED_PREDICATES = ("IS_A", "USES", "BUILT_ON", "DEVELOPED_BY", "INCLUDES", "RELATED_TO")
NODE_MERGE = "MERGE (n:Entity {id: $id})\nSET n.name = $name, n.type = $type"


def slug(text):
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")


def rel_id(subject_id, predicate, object_id):
    return "rel:" + slug("%s-%s-%s" % (subject_id, predicate, object_id))


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


@dataclass
class Entity:
    entity_id: str
    name: str
    type: str
    aliases: list = field(default_factory=list)


ENTITIES = OrderedDict()
for _name, _type in [("Neo4j", "Technology"), ("Cypher", "Technology"), ("GraphRAG", "Technology"),
                     ("Knowledge Graph", "Concept"), ("Entity Resolution", "Concept"),
                     ("LLM", "Technology"), ("Transformer", "Technology")]:
    _eid = "ent:" + slug(_name)
    ENTITIES[_eid] = Entity(_eid, _name, _type)
NEO4J, CYPHER, GRAPHRAG = "ent:neo4j", "ent:cypher", "ent:graphrag"
KG, ER, LLM, TRF = "ent:knowledge-graph", "ent:entity-resolution", "ent:llm", "ent:transformer"
ACCEPTED = [
    Triple(NEO4J, "USES", CYPHER, [Provenance("doc-001:c00", 0.95, "pattern:uses")]),
    Triple(GRAPHRAG, "BUILT_ON", KG, [Provenance("doc-001:c00", 0.95, "pattern:built_on"),
                                      Provenance("doc-002:c00", 0.95, "pattern:built_on")]),
    Triple(GRAPHRAG, "BUILT_ON", NEO4J, [Provenance("doc-002:c00", 0.80, "pattern:built_on")]),
    Triple(GRAPHRAG, "USES", ER, [Provenance("doc-003:c00", 0.95, "pattern:uses")]),
    Triple(LLM, "IS_A", TRF, [Provenance("doc-003:c00", 0.95, "pattern:is_a")]),
]


def export_cypher(entities, triples):
    statements = [{"query": NODE_MERGE, "params": {"id": e.entity_id, "name": e.name, "type": e.type}}
                  for e in entities.values()]
    for t in triples:
        statements.append({"query": "MATCH (a:Entity {id: $subject_id}), (b:Entity {id: $object_id})\n"
                                    "MERGE (a)-[r:%s {id: $rel_id}]->(b)\n"
                                    "SET r.confidence = $confidence, r.chunk_ids = $chunk_ids, "
                                    "r.methods = $methods" % t.predicate,
                           "params": {"subject_id": t.subject_id, "object_id": t.object_id,
                                      "rel_id": rel_id(t.subject_id, t.predicate, t.object_id),
                                      "confidence": t.confidence,
                                      "chunk_ids": [p.chunk_id for p in t.provenance],
                                      "methods": sorted({p.method for p in t.provenance})}})
    return statements


statements = export_cypher(ENTITIES, ACCEPTED)
node_stmts = [s for s in statements if s["query"].startswith("MERGE (n:Entity")]
rel_stmts = [s for s in statements if s["query"].startswith("MATCH (a:Entity")]
print("cypher statements : %d (node=%d, rel=%d)" % (len(statements), len(node_stmts), len(rel_stmts)))
print("\nexample node statement:\n%s\nparams: %s" % (node_stmts[0]["query"],
                                                       json.dumps(node_stmts[0]["params"], sort_keys=True)))
example = [s for s in rel_stmts if s["params"]["object_id"] == "ent:knowledge-graph"][0]
print("\nexample rel statement:\n%s\nparams: %s" % (example["query"],
                                                       json.dumps(example["params"], sort_keys=True)))
```

Output —

```text
cypher statements : 12 (node=7, rel=5)

example node statement:
MERGE (n:Entity {id: $id})
SET n.name = $name, n.type = $type
params: {"id": "ent:neo4j", "name": "Neo4j", "type": "Technology"}

example rel statement:
MATCH (a:Entity {id: $subject_id}), (b:Entity {id: $object_id})
MERGE (a)-[r:BUILT_ON {id: $rel_id}]->(b)
SET r.confidence = $confidence, r.chunk_ids = $chunk_ids, r.methods = $methods
params: {"chunk_ids": ["doc-001:c00", "doc-002:c00"], "confidence": 0.95, "methods": ["pattern:built_on"], "object_id": "ent:knowledge-graph", "rel_id": "rel:ent-graphrag-built-on-ent-knowledge-graph", "subject_id": "ent:graphrag"}
```

### Statement ပုံစံ

```python
{"query": "<Cypher text>", "params": {<parameter dict>}}
```

Statement တိုင်းတွင် `query` နှင့် `params` နှစ်ခု **ခွဲထား** ထားသည်။ Driver သည်
`session.run(query, **params)` ဖြင့် run သည် — query string သည် run တိုင်း
တူညီပြီး parameter များသာ ပြောင်းသဖြင့် **query plan cache** ကို ပြန်သုံးနိုင်သည်။

### List comprehension နှင့် loop ရောစပ်ခြင်း

```python
statements = [{...} for e in entities.values()]        # node statement အားလုံး
for t in triples:                                       # relationship တစ်ခုချင်း
    statements.append({...})
```

Node statement များသည် ပုံစံတူ (template တူ) ဖြစ်သဖြင့် comprehension ဖြင့်
ရေးသည်။ Relationship statement များသည် template ထဲ type ထည့်ရသဖြင့်
loop ဖြင့် ရေးသည်။ **နှစ်နည်းလုံးကို ရောစပ်ခြင်း** သည် ဖတ်ရလွယ်သည့်
အပိုင်းတိုင်းအတွက် သင့်တော်သည့် ပုံစံကို ရွေးနိုင်သည်။

### `[p.chunk_id for p in t.provenance]` နှင့် `sorted({p.method for p in t.provenance})`

| Expression | အမျိုးအစား | ရလဒ် |
| --- | --- | --- |
| `[p.chunk_id for p in t.provenance]` | list | source အစဉ်အတိုင်း — `["doc-001:c00", "doc-002:c00"]` |
| `{p.method for p in t.provenance}` | **set** | ထပ်နေမှု ဖယ်သည် |
| `sorted({...})` | list | အက္ခရာအစဉ် — `["pattern:built_on"]` |

`chunk_ids` ကို list အဖြစ် ထားခြင်းသည် source အစဉ် (provenance အစဉ်) ကို
ထိန်းသိမ်းရန် ဖြစ်သည် — `MERGE` ပြီးနောက် `r.chunk_ids` သည် array အဖြစ် ရှိမည်။
`methods` ကို set ဖြင့် dedupe လုပ်ပြီး `sorted()` ဖြင့် အစီအစဉ်
တည်ငြိမ်စေသည်။

### `all("$" in ... and "'" not in ...)` — security assertion

`lab.py` တွင် —
`assert all("$" in s["query"] and "'" not in s["query"] for s in statements)`။
Query string ထဲ quote (`'`) **မပါရ** ခြင်းသည် တန်ဖိုးများ query ထဲ string literal
အဖြစ် မထည့်ထားကြောင်း စစ်သည်။ တန်ဖိုးအားလုံးသည် `$param` ဖြင့်သာ
ရောက်သည်။

---

## 4. Trap — Relationship type ကို parameter လုပ်၍ မရ

Cypher တွင် label နှင့် relationship type ကို `$param` ဖြင့် ပေး၍ **မရပါ** —
ထို့ကြောင့် `%` ဖြင့် query string ထဲ ထည့်ရသည်။ ဤနေရာတွင် whitelist
မစစ်လျှင် **Cypher injection** ဖြစ်နိုင်သည်။

```python
import csv
import io
import json
import re
from collections import OrderedDict
from dataclasses import dataclass, field

ALLOWED_PREDICATES = ("IS_A", "USES", "BUILT_ON", "DEVELOPED_BY", "INCLUDES", "RELATED_TO")
NODE_MERGE = "MERGE (n:Entity {id: $id})\nSET n.name = $name, n.type = $type"


def slug(text):
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")


def rel_id(subject_id, predicate, object_id):
    return "rel:" + slug("%s-%s-%s" % (subject_id, predicate, object_id))


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


@dataclass
class Entity:
    entity_id: str
    name: str
    type: str
    aliases: list = field(default_factory=list)


ENTITIES = OrderedDict()
for _name, _type in [("Neo4j", "Technology"), ("Cypher", "Technology"), ("GraphRAG", "Technology"),
                     ("Knowledge Graph", "Concept"), ("Entity Resolution", "Concept"),
                     ("LLM", "Technology"), ("Transformer", "Technology")]:
    _eid = "ent:" + slug(_name)
    ENTITIES[_eid] = Entity(_eid, _name, _type)
NEO4J, CYPHER, GRAPHRAG = "ent:neo4j", "ent:cypher", "ent:graphrag"
KG, ER, LLM, TRF = "ent:knowledge-graph", "ent:entity-resolution", "ent:llm", "ent:transformer"
ACCEPTED = [
    Triple(NEO4J, "USES", CYPHER, [Provenance("doc-001:c00", 0.95, "pattern:uses")]),
    Triple(GRAPHRAG, "BUILT_ON", KG, [Provenance("doc-001:c00", 0.95, "pattern:built_on"),
                                      Provenance("doc-002:c00", 0.95, "pattern:built_on")]),
    Triple(GRAPHRAG, "BUILT_ON", NEO4J, [Provenance("doc-002:c00", 0.80, "pattern:built_on")]),
    Triple(GRAPHRAG, "USES", ER, [Provenance("doc-003:c00", 0.95, "pattern:uses")]),
    Triple(LLM, "IS_A", TRF, [Provenance("doc-003:c00", 0.95, "pattern:is_a")]),
]


def build_rel_query(predicate):
    return ("MATCH (a:Entity {id: $subject_id}), (b:Entity {id: $object_id})\n"
            "MERGE (a)-[r:%s {id: $rel_id}]->(b)" % predicate)


for predicate in ["BUILT_ON", "FRIENDS_WITH", "X]->() DETACH DELETE a //"]:
    query = build_rel_query(predicate)
    line = [l for l in query.split("\n") if l.startswith("MERGE")][0]
    print("%-26s %s" % (predicate, line))
    print("%-26s allowed=%s" % ("", predicate in ALLOWED_PREDICATES))
```

Output —

```text
BUILT_ON                   MERGE (a)-[r:BUILT_ON {id: $rel_id}]->(b)
                           allowed=True
FRIENDS_WITH               MERGE (a)-[r:FRIENDS_WITH {id: $rel_id}]->(b)
                           allowed=False
X]->() DETACH DELETE a //  MERGE (a)-[r:X]->() DETACH DELETE a // {id: $rel_id}]->(b)
                           allowed=False
```

### Injection မည်သို့ ဖြစ်သွားသနည်း။

တတိယ case တွင် predicate ကို `FRIENDS_WITH` အစား
`X]->() DETACH DELETE a //` ဖြင့် ပေးလိုက်သည်။ `%` သည် ၎င်းကို query string ထဲ
**တိုက်ရိုက်** ထည့်လိုက်သဖြင့် `r:X]->()` ဖြင့် relationship ပိတ်ပြီး
`DETACH DELETE a` ကို ဆက်လုပ်သည် — `//` သည် ကျန်သည်ကို comment လုပ်သည်။

| Predicate | `in ALLOWED_PREDICATES` |
| --- | --- |
| `BUILT_ON` | `True` — whitelist အတွင်း |
| `FRIENDS_WITH` | `False` — whitelist ပြင်ပ |
| `X]->() DETACH DELETE a //` | `False` — whitelist ပြင်ပ၊ injection ဖြစ်နိုင် |

### ကာကွယ်မှု — whitelist ကို query မဖန်တီးမီ apply လုပ်ပါ

Exercise 5 ၏ `quality_gate` သည် `predicate not in ALLOWED_PREDICATES` ဖြစ်သည့်
triple ကို `unknown_predicate` အဖြစ် ဖယ်လိုက်သည်။ ထို့ကြောင့်
`export_cypher()` သို့ ရောက်သည့် triple တိုင်း၏ predicate သည် whitelist အတွင်း
ဖြစ်ပြီးသား ဖြစ်သည်။

| အတားအဆီး | အလုပ် |
| --- | --- |
| Quality gate (Exercise 5) | whitelist ပြင်ပ predicate များကို triple အဆင့်တွင် ဖယ် |
| `ALLOWED_PREDICATES` constant | whitelist ကို တစ်နေရာတည်း သတ်မှတ် |
| Parameter (`$param`) | တန်ဖိုးများ (id၊ name၊ confidence) အားလုံး query နှင့် ခွဲ |
| `assert "'" not in query` | query ထဲ string literal မပါကြောင်း run အချိန်တွင် စစ် |

**သတိပေးချက်** — Text-to-Cypher သို့မဟုတ် LLM-generated predicate ကို
လက်ခံသည့် စနစ်တွင် whitelist သည် **မဖြစ်မနေ** လိုအပ်သည်။ `MATCH`၊ `DELETE`၊
`DETACH DELETE`၊ `DROP` ကဲ့သို့ destructive clause များကို query မဖန်တီးမီ
block လုပ်ရသည်။ Read-only user နှင့် separate database သုံးခြင်းသည်လည်း
အတားအဆီး တစ်ခု ဖြစ်သည်။

---

## 5. `export_json()` — round-trip စစ်နိုင်သော artifact

```python
import csv
import io
import json
import re
from collections import OrderedDict
from dataclasses import dataclass, field

ALLOWED_PREDICATES = ("IS_A", "USES", "BUILT_ON", "DEVELOPED_BY", "INCLUDES", "RELATED_TO")
NODE_MERGE = "MERGE (n:Entity {id: $id})\nSET n.name = $name, n.type = $type"


def slug(text):
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")


def rel_id(subject_id, predicate, object_id):
    return "rel:" + slug("%s-%s-%s" % (subject_id, predicate, object_id))


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


@dataclass
class Entity:
    entity_id: str
    name: str
    type: str
    aliases: list = field(default_factory=list)


ENTITIES = OrderedDict()
for _name, _type in [("Neo4j", "Technology"), ("Cypher", "Technology"), ("GraphRAG", "Technology"),
                     ("Knowledge Graph", "Concept"), ("Entity Resolution", "Concept"),
                     ("LLM", "Technology"), ("Transformer", "Technology")]:
    _eid = "ent:" + slug(_name)
    ENTITIES[_eid] = Entity(_eid, _name, _type)
NEO4J, CYPHER, GRAPHRAG = "ent:neo4j", "ent:cypher", "ent:graphrag"
KG, ER, LLM, TRF = "ent:knowledge-graph", "ent:entity-resolution", "ent:llm", "ent:transformer"
ACCEPTED = [
    Triple(NEO4J, "USES", CYPHER, [Provenance("doc-001:c00", 0.95, "pattern:uses")]),
    Triple(GRAPHRAG, "BUILT_ON", KG, [Provenance("doc-001:c00", 0.95, "pattern:built_on"),
                                      Provenance("doc-002:c00", 0.95, "pattern:built_on")]),
    Triple(GRAPHRAG, "BUILT_ON", NEO4J, [Provenance("doc-002:c00", 0.80, "pattern:built_on")]),
    Triple(GRAPHRAG, "USES", ER, [Provenance("doc-003:c00", 0.95, "pattern:uses")]),
    Triple(LLM, "IS_A", TRF, [Provenance("doc-003:c00", 0.95, "pattern:is_a")]),
]


def export_json(entities, triples):
    names = {eid: e.name for eid, e in entities.items()}
    return json.dumps({"nodes": [{"id": e.entity_id, "name": e.name, "type": e.type, "aliases": e.aliases}
                                 for e in entities.values()],
                       "relationships": [t.to_dict(names) for t in triples]},
                      indent=2, sort_keys=True, ensure_ascii=False)


payload = json.loads(export_json(ENTITIES, ACCEPTED))
print("json export       : nodes=%d relationships=%d" % (len(payload["nodes"]), len(payload["relationships"])))
print(json.dumps(payload["relationships"][1], sort_keys=True, indent=2))
print(sorted(payload["relationships"][1]))
```

Output —

```text
json export       : nodes=7 relationships=5
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
['confidence', 'object', 'object_id', 'predicate', 'provenance', 'subject', 'subject_id']
```

### `json.dumps()` argument သုံးခု

| Argument | ရည်ရွယ်ချက် |
| --- | --- |
| `indent=2` | လူဖတ်ရလွယ်သော multi-line output (diff တွင် ဖတ်နိုင်) |
| `sort_keys=True` | key များကို အက္ခရာအစဉ် — run တိုင်း တူညီသော byte |
| `ensure_ascii=False` | non-ASCII (ဥပမာ မြန်မာ) ကို escape မလုပ်ဘဲ မူရင်းအတိုင်း |

`json.loads()` round-trip သည် **assertion အဖြစ် အသုံးဝင်သည်** — output ကို
ပြန်ဖတ်၍ မရလျှင် serialization ပျက်နေပါပြီ။ `lab.py` တွင်
`payload["relationships"] == [t.to_dict(names) for t in accepted]` ဖြင့်
round-trip ကို တိုက်ရိုက် စစ်သည်။

Relationship dict တွင် key ခုနစ်ခု ရှိသည် — `subject`၊ `predicate`၊ `object`၊
`subject_id`၊ `object_id`၊ `confidence`၊ `provenance`။ နောက်ဆုံး print သည်
ထို key များကို အက္ခရာအစဉ်ဖြင့် ပြသည်။

---

## 6. `export_csv()` — Neo4j Admin Import အတွက်

```python
import csv
import io
import json
import re
from collections import OrderedDict
from dataclasses import dataclass, field

ALLOWED_PREDICATES = ("IS_A", "USES", "BUILT_ON", "DEVELOPED_BY", "INCLUDES", "RELATED_TO")
NODE_MERGE = "MERGE (n:Entity {id: $id})\nSET n.name = $name, n.type = $type"


def slug(text):
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")


def rel_id(subject_id, predicate, object_id):
    return "rel:" + slug("%s-%s-%s" % (subject_id, predicate, object_id))


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


@dataclass
class Entity:
    entity_id: str
    name: str
    type: str
    aliases: list = field(default_factory=list)


ENTITIES = OrderedDict()
for _name, _type in [("Neo4j", "Technology"), ("Cypher", "Technology"), ("GraphRAG", "Technology"),
                     ("Knowledge Graph", "Concept"), ("Entity Resolution", "Concept"),
                     ("LLM", "Technology"), ("Transformer", "Technology")]:
    _eid = "ent:" + slug(_name)
    ENTITIES[_eid] = Entity(_eid, _name, _type)
NEO4J, CYPHER, GRAPHRAG = "ent:neo4j", "ent:cypher", "ent:graphrag"
KG, ER, LLM, TRF = "ent:knowledge-graph", "ent:entity-resolution", "ent:llm", "ent:transformer"
ACCEPTED = [
    Triple(NEO4J, "USES", CYPHER, [Provenance("doc-001:c00", 0.95, "pattern:uses")]),
    Triple(GRAPHRAG, "BUILT_ON", KG, [Provenance("doc-001:c00", 0.95, "pattern:built_on"),
                                      Provenance("doc-002:c00", 0.95, "pattern:built_on")]),
    Triple(GRAPHRAG, "BUILT_ON", NEO4J, [Provenance("doc-002:c00", 0.80, "pattern:built_on")]),
    Triple(GRAPHRAG, "USES", ER, [Provenance("doc-003:c00", 0.95, "pattern:uses")]),
    Triple(LLM, "IS_A", TRF, [Provenance("doc-003:c00", 0.95, "pattern:is_a")]),
]


def export_csv(entities, triples):
    node_buf, rel_buf = io.StringIO(), io.StringIO()
    node_writer, rel_writer = csv.writer(node_buf, lineterminator="\n"), csv.writer(rel_buf, lineterminator="\n")
    node_writer.writerow(["entity_id:ID", "name", "type", ":LABEL"])
    for e in entities.values():
        node_writer.writerow([e.entity_id, e.name, e.type, "Entity"])
    rel_writer.writerow([":START_ID", ":END_ID", ":TYPE", "rel_id", "confidence", "chunk_ids"])
    for t in triples:
        rel_writer.writerow([t.subject_id, t.object_id, t.predicate,
                             rel_id(t.subject_id, t.predicate, t.object_id), round(t.confidence, 2),
                             ";".join(sorted({p.chunk_id for p in t.provenance}))])
    return {"nodes.csv": node_buf.getvalue(), "relationships.csv": rel_buf.getvalue()}


csv_files = export_csv(ENTITIES, ACCEPTED)
node_rows = list(csv.reader(io.StringIO(csv_files["nodes.csv"])))
rel_rows = list(csv.reader(io.StringIO(csv_files["relationships.csv"])))
print("nodes.csv header : %s" % node_rows[0])
print("nodes.csv rows   : %d" % (len(node_rows) - 1))
print()
print(csv_files["relationships.csv"])
print("relationships rows : %d" % (len(rel_rows) - 1))
```

Output —

```text
nodes.csv header : ['entity_id:ID', 'name', 'type', ':LABEL']
nodes.csv rows   : 7

:START_ID,:END_ID,:TYPE,rel_id,confidence,chunk_ids
ent:neo4j,ent:cypher,USES,rel:ent-neo4j-uses-ent-cypher,0.95,doc-001:c00
ent:graphrag,ent:knowledge-graph,BUILT_ON,rel:ent-graphrag-built-on-ent-knowledge-graph,0.95,doc-001:c00;doc-002:c00
ent:graphrag,ent:neo4j,BUILT_ON,rel:ent-graphrag-built-on-ent-neo4j,0.8,doc-002:c00
ent:graphrag,ent:entity-resolution,USES,rel:ent-graphrag-uses-ent-entity-resolution,0.95,doc-003:c00
ent:llm,ent:transformer,IS_A,rel:ent-llm-is-a-ent-transformer,0.95,doc-003:c00

relationships rows : 5
```

### `io.StringIO` — memory ထဲ file ကဲ့သို့

`csv.writer()` သည် file-like object ကို လိုသည်။ `io.StringIO()` သည် memory ထဲ
file တစ်ခုကို တုပပေးသည် — disk မထိဘဲ string အဖြစ် ထုတ်နိုင်သည်။
`getvalue()` သည် စုစည်းထားသည့် string ကို ပြန်ပေးသည်။

### `lineterminator="\n"`

`csv.writer` ၏ default line terminator သည် `"\r\n"` ဖြစ်သည်။ Linux တွင်
`\r` မလိုသဖြင့် `\n` သတ်မှတ်သည် — ထို့ကြောင့် output သည် byte-stable ဖြစ်ပြီး
version control တွင် diff သန့်ရှင်းသည်။

### `";".join(sorted({...}))` — array property ကို scalar အဖြစ်

CSV တွင် array type မရှိပါ။ `chunk_ids` ကို `;` ဖြင့် ဆက်ပြီး scalar တစ်ခု
ဖြစ်စေသည်။ `set` ဖြင့် ထပ်နေမှု ဖယ်ပြီး `sorted()` ဖြင့် အစီအစဉ်
တည်ငြိမ်စေသည် — `doc-001:c00;doc-002:c00`။

Neo4j Admin Import တွင် header များ၏ prefix သည် အဓိပ္ပာယ် သတ်မှတ်သည် —

| Header | အဓိပ္ပာယ် |
| --- | --- |
| `entity_id:ID` | node ၏ unique id (join key) |
| `:LABEL` | node label |
| `:START_ID` / `:END_ID` | relationship ၏ အစ/အဆုံး node id |
| `:TYPE` | relationship type |

### Trap — comma ပါသော value ကို ကိုယ်တိုင် join လုပ်ခြင်း

```python
import csv
import io

rows = ["Neo4j, Inc", "GraphRAG"]
buf = io.StringIO()
writer = csv.writer(buf, lineterminator="\n")
writer.writerow(rows)
print(repr(buf.getvalue()))
print(list(csv.reader(io.StringIO(buf.getvalue()))))
print(repr(",".join(rows)))
print(len(list(csv.reader(io.StringIO(",".join(rows))))[0]))
```

Output —

```text
'"Neo4j, Inc",GraphRAG\n'
[['Neo4j, Inc', 'GraphRAG']]
'Neo4j, Inc,GraphRAG'
3
```

| နည်းလမ်း | တန်ဖိုး | ပြန်ဖတ်လျှင် field အရေအတွက် |
| --- | --- | --- |
| `csv.writer` | `'"Neo4j, Inc",GraphRAG\n'` | **2** (မှန်) |
| `",".join(...)` | `'Neo4j, Inc,GraphRAG'` | **3** (မှား) |

`csv.writer` သည် comma ပါသည့် value ကို quote (`"..."`) ဖြင့် ခြုံပေးသည်။
`",".join()` ဖြင့် ကိုယ်တိုင်စီရင် `Neo4j, Inc` သည် field **နှစ်ခု** အဖြစ်
ကွဲသွားပြီး column အားလုံး တစ်ခုစီ ရွှေ့သွားသည် — import လုပ်သည့်အခါ
error ဖြစ်စေ၊ တိတ်တဆိတ် မှားယွင်းစွာ load ဖြစ်စေ ဖြစ်နိုင်သည်။
ထို့ကြောင့် CSV ကို **`csv` module ဖြင့်သာ** ရေးရသည်။

---

## 7. Code တစ်ခုလုံး — Run လုပ်နိုင်သော Version

```python
import csv
import io
import json
import re
from collections import OrderedDict
from dataclasses import dataclass, field

ALLOWED_PREDICATES = ("IS_A", "USES", "BUILT_ON", "DEVELOPED_BY", "INCLUDES", "RELATED_TO")
NODE_MERGE = "MERGE (n:Entity {id: $id})\nSET n.name = $name, n.type = $type"


def slug(text):
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")


def rel_id(subject_id, predicate, object_id):
    return "rel:" + slug("%s-%s-%s" % (subject_id, predicate, object_id))


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


@dataclass
class Entity:
    entity_id: str
    name: str
    type: str
    aliases: list = field(default_factory=list)


ENTITIES = OrderedDict()
for _name, _type in [("Neo4j", "Technology"), ("Cypher", "Technology"), ("GraphRAG", "Technology"),
                     ("Knowledge Graph", "Concept"), ("Entity Resolution", "Concept"),
                     ("LLM", "Technology"), ("Transformer", "Technology")]:
    _eid = "ent:" + slug(_name)
    ENTITIES[_eid] = Entity(_eid, _name, _type)
NEO4J, CYPHER, GRAPHRAG = "ent:neo4j", "ent:cypher", "ent:graphrag"
KG, ER, LLM, TRF = "ent:knowledge-graph", "ent:entity-resolution", "ent:llm", "ent:transformer"
ACCEPTED = [
    Triple(NEO4J, "USES", CYPHER, [Provenance("doc-001:c00", 0.95, "pattern:uses")]),
    Triple(GRAPHRAG, "BUILT_ON", KG, [Provenance("doc-001:c00", 0.95, "pattern:built_on"),
                                      Provenance("doc-002:c00", 0.95, "pattern:built_on")]),
    Triple(GRAPHRAG, "BUILT_ON", NEO4J, [Provenance("doc-002:c00", 0.80, "pattern:built_on")]),
    Triple(GRAPHRAG, "USES", ER, [Provenance("doc-003:c00", 0.95, "pattern:uses")]),
    Triple(LLM, "IS_A", TRF, [Provenance("doc-003:c00", 0.95, "pattern:is_a")]),
]


def export_cypher(entities, triples):
    statements = [{"query": NODE_MERGE, "params": {"id": e.entity_id, "name": e.name, "type": e.type}}
                  for e in entities.values()]
    for t in triples:
        statements.append({"query": "MATCH (a:Entity {id: $subject_id}), (b:Entity {id: $object_id})\n"
                                    "MERGE (a)-[r:%s {id: $rel_id}]->(b)\n"
                                    "SET r.confidence = $confidence, r.chunk_ids = $chunk_ids, "
                                    "r.methods = $methods" % t.predicate,
                           "params": {"subject_id": t.subject_id, "object_id": t.object_id,
                                      "rel_id": rel_id(t.subject_id, t.predicate, t.object_id),
                                      "confidence": t.confidence,
                                      "chunk_ids": [p.chunk_id for p in t.provenance],
                                      "methods": sorted({p.method for p in t.provenance})}})
    return statements


def export_json(entities, triples):
    names = {eid: e.name for eid, e in entities.items()}
    return json.dumps({"nodes": [{"id": e.entity_id, "name": e.name, "type": e.type, "aliases": e.aliases}
                                 for e in entities.values()],
                       "relationships": [t.to_dict(names) for t in triples]},
                      indent=2, sort_keys=True, ensure_ascii=False)


def export_csv(entities, triples):
    node_buf, rel_buf = io.StringIO(), io.StringIO()
    node_writer, rel_writer = csv.writer(node_buf, lineterminator="\n"), csv.writer(rel_buf, lineterminator="\n")
    node_writer.writerow(["entity_id:ID", "name", "type", ":LABEL"])
    for e in entities.values():
        node_writer.writerow([e.entity_id, e.name, e.type, "Entity"])
    rel_writer.writerow([":START_ID", ":END_ID", ":TYPE", "rel_id", "confidence", "chunk_ids"])
    for t in triples:
        rel_writer.writerow([t.subject_id, t.object_id, t.predicate,
                             rel_id(t.subject_id, t.predicate, t.object_id), round(t.confidence, 2),
                             ";".join(sorted({p.chunk_id for p in t.provenance}))])
    return {"nodes.csv": node_buf.getvalue(), "relationships.csv": rel_buf.getvalue()}


statements = export_cypher(ENTITIES, ACCEPTED)
node_stmts = [s for s in statements if s["query"].startswith("MERGE (n:Entity")]
rel_stmts = [s for s in statements if s["query"].startswith("MATCH (a:Entity")]
print("cypher statements : %d (node=%d, rel=%d)" % (len(statements), len(node_stmts), len(rel_stmts)))
print("\nexample node statement:\n%s\nparams: %s" % (node_stmts[0]["query"],
                                                       json.dumps(node_stmts[0]["params"], sort_keys=True)))
example = [s for s in rel_stmts if s["params"]["object_id"] == "ent:knowledge-graph"][0]
print("\nexample rel statement:\n%s\nparams: %s" % (example["query"],
                                                       json.dumps(example["params"], sort_keys=True)))
payload = json.loads(export_json(ENTITIES, ACCEPTED))
node_rows = list(csv.reader(io.StringIO(export_csv(ENTITIES, ACCEPTED)["nodes.csv"])))
rel_rows = list(csv.reader(io.StringIO(export_csv(ENTITIES, ACCEPTED)["relationships.csv"])))
print("\njson export       : nodes=%d relationships=%d" % (len(payload["nodes"]), len(payload["relationships"])))
print("csv nodes.csv     : header=%s rows=%d" % (node_rows[0], len(node_rows) - 1))
print("csv relationships : header=%s rows=%d" % (rel_rows[0], len(rel_rows) - 1))

assert len(statements) == len(ENTITIES) + len(ACCEPTED) == 12
assert all("$" in s["query"] and "'" not in s["query"] for s in statements)
assert len(payload["nodes"]) == 7 and len(payload["relationships"]) == 5
assert node_rows[0] == ["entity_id:ID", "name", "type", ":LABEL"]
assert rel_rows[0] == [":START_ID", ":END_ID", ":TYPE", "rel_id", "confidence", "chunk_ids"]
assert len(node_rows) - 1 == 7 and len(rel_rows) - 1 == 5
```

Output —

```text
cypher statements : 12 (node=7, rel=5)

example node statement:
MERGE (n:Entity {id: $id})
SET n.name = $name, n.type = $type
params: {"id": "ent:neo4j", "name": "Neo4j", "type": "Technology"}

example rel statement:
MATCH (a:Entity {id: $subject_id}), (b:Entity {id: $object_id})
MERGE (a)-[r:BUILT_ON {id: $rel_id}]->(b)
SET r.confidence = $confidence, r.chunk_ids = $chunk_ids, r.methods = $methods
params: {"chunk_ids": ["doc-001:c00", "doc-002:c00"], "confidence": 0.95, "methods": ["pattern:built_on"], "object_id": "ent:knowledge-graph", "rel_id": "rel:ent-graphrag-built-on-ent-knowledge-graph", "subject_id": "ent:graphrag"}

json export       : nodes=7 relationships=5
csv nodes.csv     : header=['entity_id:ID', 'name', 'type', ':LABEL'] rows=7
csv relationships : header=[':START_ID', ':END_ID', ':TYPE', 'rel_id', 'confidence', 'chunk_ids'] rows=5
```

ဤ output သည် `lab.py` ၏ Exercise 6 နှင့် တူညီသည်။

### Export format ဇယား

| Format | Output အရေအတွက် | Parameterize | Determinism | အသုံးပြုသည့် နေရာ |
| --- | --- | --- | --- | --- |
| Cypher | statement 12 (node 7 + rel 5) | `$param` အားလုံး | `rel_id` deterministic | Incremental update၊ driver |
| JSON | nodes 7 + relationships 5 | — | `sort_keys=True` | API၊ diff artifact၊ audit |
| CSV | rows 7 + 5 | — | `lineterminator="\n"` | Bulk import (Admin Import) |

---

## 8. ကိုယ်တိုင်လေ့ကျင့်ကြည့်ပါ

**မေးခွန်း** — အောက်ပါ code သည် မည်သည့်ရလဒ် ပြန်ပေးမည်နည်း။

```python
import csv
import io

buf = io.StringIO()
writer = csv.writer(buf, lineterminator="\n")
writer.writerow(["doc-001:c00", "Neo4j uses Cypher, a query language", 0.95])
print(repr(buf.getvalue()))
```

1. `'"doc-001:c00","Neo4j uses Cypher, a query language",0.95\n'` — value အားလုံး quote ဖြစ်သည်
2. `'doc-001:c00,"Neo4j uses Cypher, a query language",0.95\n'` — comma ပါသော field တစ်ခုတည်း quote ဖြစ်သည်
3. `'doc-001:c00,Neo4j uses Cypher, a query language,0.95\n'` — quote မဖြစ်ပါ
4. `'doc-001:c00,Neo4j uses Cypher; a query language,0.95\n'` — comma ကို `;` ဖြင့် အစားထိုးသည်

<details>
<summary>အဖြေ ကြည့်ရန်</summary>

**အဖြေ — 2. `'doc-001:c00,"Neo4j uses Cypher, a query language",0.95\n'`**

အကြောင်းရင်း — `csv.writer` သည် **comma (သို့) quote (သို့) newline** ပါသည့်
field များကိုသာ quote လုပ်သည်။ `doc-001:c00` တွင် ထို character များ မပါသဖြင့်
quote မလုပ်ပါ။ `0.95` သည်လည်း ထို့အတူ ဖြစ်သည်။ ဒုတိယ field တစ်ခုတည်းသာ quote
ဖြစ်သည်။ ဤအပြုအမူသည် `csv.reader` ဖြင့် ပြန်ဖတ်လျှင် field သုံးခု
ရရှိစေသည် — `["doc-001:c00", "Neo4j uses Cypher, a query language", "0.95"]`။
Option 3 က ဖြစ်ခဲ့လျှင် field ၄ ခု ဖြစ်သွားပြီး column များ ရွှေ့သွားမည်။

</details>

---

**အဓိက မှတ်ထားရန်** — Export အဆင့်သည် pipeline ၏ **အထွက် အာမခံချက်** ဖြစ်သည်။
Cypher တွင် တန်ဖိုးအားလုံးကို `$param` ဖြင့်သာ ပို့ပြီး relationship type ကို
parameter မလုပ်နိုင်သဖြင့် whitelist ဖြင့် စစ်ပြီးမှ query ထဲ ထည့်သည် —
၎င်းသည် Cypher injection ကာကွယ်မှု၏ အရေးကြီးဆုံး အစိတ်အပိုင်း ဖြစ်သည်။ JSON ကို
`sort_keys=True` ဖြင့်၊ CSV ကို `csv.writer` ဖြင့်သာ ထုတ်ခြင်းသည် run တိုင်း
တူညီပြီး ပြန်ဖတ်နိုင်သည့် artifact ဖြစ်စေသည်။ `MERGE` ကို deterministic
id (`entity_id`၊ `rel_id`) နှင့် တွဲသုံးခြင်းကြောင့် pipeline ကို မည်မျှ
run လုပ်လုပ် node/relationship အသစ် မဖြစ်ဘဲ property များသာ update ဖြစ်သည်။
