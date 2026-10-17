# Walkthrough 02 — End-to-End Pipeline Run (Exercise 2)

> ဤဖိုင်သည် Module 04 ၏ `solution.md` ထဲက Exercise 2 ကို **Python အခြေခံမှ စ၍**
> အပိုင်းလိုက် ရှင်းပြသည့် walkthrough ဖြစ်သည်။

---

## 0. ဤ Exercise က ဘာကို ဖြေရှင်းပေးသလဲ။

Exercise 1 က text ကို သန့်ရှင်းစေသည်။ Exercise 2 က ထို text ကို **Knowledge Graph
အထိ** ခေါ်သွားသည့် အဆင့်ရှစ်ခုကို ချိတ်ဆက်သည်။

```text
corpus (dict list)
  -> ingest      : Document object များ
  -> normalize   : clean text          (Exercise 1)
  -> chunk       : Chunk object များ (sentence-aligned၊ CHUNK_SIZE ဖြင့် ကန့်သတ်)
  -> extract     : Triple များ (pattern rule + co-occurrence fallback)
  -> resolve     : canonical Entity များ (Exercise 3)
  -> merge       : duplicate triple များ ပေါင်းခြင်း (Exercise 4)
  -> quality gate: ချို့ယွင်းသော triple များ ဖယ်ခြင်း (Exercise 5)
  -> export      : Cypher / JSON / CSV (Exercise 6)

run_pipeline(corpus) -> dict { documents, chunks, raw_triples, entities,
                              merged, accepted, rejected, cypher, json, csv }
```

ဤ Exercise ၏ အဓိကအချက်မှာ အဆင့်တိုင်းသည် **list comprehension နှင့် function
တစ်ခုတည်း** အဖြစ် အလွှာလိုက် စုစည်းထားတာပါ။ ဒါကြောင့် stage အသစ်တစ်ခု
ထည့်တဲ့အခါ ကျန်အဆင့်များကို မထိဘဲ ပြင်နိုင်ပါတယ်။

ဒီ code မှာ လေ့ရှာရမယ့် Python concepts တွေကတော့ —

- Regex **lookbehind** `(?<=...)` နှင့် lookahead `(?!...)`
- Named group `(?P<name>...)`
- `re.split()` နှင့် `re.finditer(match_object)`
- List comprehension ထဲ `if` ချက်
- `enumerate()`၊ `zip()`၊ `sorted(key=...)`
- Buffer pattern (`buf`) ဖြင့် အစဉ်လိုက် စုစည်းခြင်း
- Dictionary အပေါ် linear search (fuzzy fallback)
- Function တစ်ခုမှ တစ်ခုသို့ data ပို့ခြင်း (pipeline composition)
- `assert` ဖြင့် အဆင့်တိုင်း၏ အရေအတွက် စစ်ခြင်း

---

## 1. `split_sentences()` — sentence ခွဲခြင်း

```python
import re
from difflib import SequenceMatcher

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
CONF_EXACT, CONF_ALIAS, CONF_FUZZY, FUZZY_THRESHOLD = 0.95, 0.80, 0.55, 0.85
ALIAS_INDEX, CANONICAL_INDEX = {}, {}
for _entry in GAZETTEER:
    CANONICAL_INDEX[_entry["canonical"].lower()] = _entry
    for _alias in _entry["aliases"]:
        ALIAS_INDEX[_alias.lower()] = _entry
_BOUNDED = r"(?<![\w-])(?:%s)(?![\w-])" % "|".join(
    re.escape(a) for a in sorted(ALIAS_INDEX, key=len, reverse=True))
_DETERMINER = r"(?:(?:a|an|the)\s+)?"
PATTERN_RULES = [
    ("IS_A", r"(?:is|are)\s+(?:a|an)"),
    ("USES", r"(?:uses?|use)"),
    ("BUILT_ON", r"(?:is\s+built\s+on|runs?\s+on|is\s+based\s+on)"),
    ("DEVELOPED_BY", r"(?:was\s+developed\s+by|develops?)"),
    ("INCLUDES", r"(?:contains?|includes?)"),
]
COOCCURRENCE_CONFIDENCE = 0.45


def split_sentences(text):
    return [s.strip() for s in re.split(r"(?<=[.!?])\s+", text) if s.strip()]


text = "Neo4j uses Cypher. GraphRAG is built on a Knowledge Graph."
for sentence in split_sentences(text):
    print(repr(sentence))
```

Output —

```text
'Neo4j uses Cypher.'
'GraphRAG is built on a Knowledge Graph.'
```

### `re.split()` က delimiter ကို ဖျက်ပစ်သည်

`re.split(pattern, text)` က pattern ကို **delimiter** အဖြစ် ယူပြီး text ကို
အပိုင်းများ ခွဲပါတယ်။ delimiter ကိုယ်တိုင် ရလဒ်ထဲ မပါဝင်တော့ပါ။ ဒါကြောင့် `.`
ကို delimiter လုပ်ရင် sentence ၏ အဆုံးက `.` ပျောက်သွားပါတယ်။

### `(?<=...)` သည် zero-width ဖြစ်သည်

`(?<=[.!?])` က **lookbehind** ဖြစ်ပါတယ်။ "ရှေ့မှာ `.`/`!`/`?` ရှိရမည်" လို့
စစ်ပေမဲ့ **character ကို မစားပါ** (zero-width)။ ဒါကြောင့် delimiter က
ကွက်လပ် `\s+` သာ ဖြစ်ပြီး `.` က match မဖြစ်ဘဲ sentence ထဲ ကျန်နေပါတယ်။

### Trap — lookbehind မပါသော split

```python
import re

text = "Neo4j uses Cypher. GraphRAG is built on a Knowledge Graph."
print("lookbehind :", re.split(r"(?<=[.!?])\s+", text))
print("plain      :", re.split(r"[.!?]\s+", text))
```

Output —

```text
lookbehind : ['Neo4j uses Cypher.', 'GraphRAG is built on a Knowledge Graph.']
plain      : ['Neo4j uses Cypher', 'GraphRAG is built on a Knowledge Graph.']
```

`plain` ဗားရှင်းတွင် ပထမ sentence က `'Neo4j uses Cypher'` ဖြစ်ပြီး `.` ပျောက်နေပါတယ်။
ဒါပေမဲ့ ဒုတိယ sentence က `.` နဲ့ ဆုံးတဲ့အတွက် **မပျောက်ပါ** — delimiter က
`". "` ဖြစ်ပြီး နောက်ဆုံး `.` က delimiter မဟုတ်လို့ပါ။ ဒါကြောင့် ဤအမှားက
**တသမတ်တည်း မဖြစ်** ဘဲ ရံဖန်ရံခါသာ ဖြစ်တဲ့ bug အဖြစ် ကျန်နိုင်ပါတယ်။

### `(?<=...)` နှင့် `(...)` နှိုင်းယှဉ်ခြင်း

```python
import re

print(re.findall(r"(?<=:)\s*\w+", "id: neo4j"))
print(re.findall(r":\s*\w+", "id: neo4j"))
```

Output —

```text
[' neo4j']
[': neo4j']
```

ပထမတစ်ခုက `:` ကို မဖမ်းဘဲ နောက်က စာလုံးကိုသာ ပြန်ပေးတာကို တွေ့နိုင်ပါတယ်။

---

## 2. `chunk_document()` — sentence-aligned chunking

```python
import re
from difflib import SequenceMatcher

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
CONF_EXACT, CONF_ALIAS, CONF_FUZZY, FUZZY_THRESHOLD = 0.95, 0.80, 0.55, 0.85
ALIAS_INDEX, CANONICAL_INDEX = {}, {}
for _entry in GAZETTEER:
    CANONICAL_INDEX[_entry["canonical"].lower()] = _entry
    for _alias in _entry["aliases"]:
        ALIAS_INDEX[_alias.lower()] = _entry
_BOUNDED = r"(?<![\w-])(?:%s)(?![\w-])" % "|".join(
    re.escape(a) for a in sorted(ALIAS_INDEX, key=len, reverse=True))
_DETERMINER = r"(?:(?:a|an|the)\s+)?"
PATTERN_RULES = [
    ("IS_A", r"(?:is|are)\s+(?:a|an)"),
    ("USES", r"(?:uses?|use)"),
    ("BUILT_ON", r"(?:is\s+built\s+on|runs?\s+on|is\s+based\s+on)"),
    ("DEVELOPED_BY", r"(?:was\s+developed\s+by|develops?)"),
    ("INCLUDES", r"(?:contains?|includes?)"),
]
COOCCURRENCE_CONFIDENCE = 0.45

CHUNK_SIZE = 140


def split_sentences(text):
    return [s.strip() for s in re.split(r"(?<=[.!?])\s+", text) if s.strip()]


def chunk_document_text(doc_id, text):
    chunks, buf, ordinal = [], "", 0
    for sentence in split_sentences(text):
        candidate = (buf + " " + sentence).strip() if buf else sentence
        if buf and len(candidate) > CHUNK_SIZE:
            chunks.append(("%s:c%02d" % (doc_id, ordinal), buf))
            ordinal, buf = ordinal + 1, sentence
        else:
            buf = candidate
    if buf:
        chunks.append(("%s:c%02d" % (doc_id, ordinal), buf))
    return chunks


TEXT = ("Neo4j  is a graph database. Neo4j uses Cypher as its query language. "
        "GraphRAG is built on a Knowledge Graph. Nous Research develops open models.")
for chunk_id, body in chunk_document_text("doc-001", TEXT):
    print("%s (%3d) %s" % (chunk_id, len(body), body))
```

Output —

```text
doc-001:c00 (108) Neo4j  is a graph database. Neo4j uses Cypher as its query language. GraphRAG is built on a Knowledge Graph.
doc-001:c01 ( 35) Nous Research develops open models.
```

### Buffer pattern

| Variable | ရည်ရွယ်ချက် |
| --- | --- |
| `buf` | လက်ရှိ စုစည်းနေသော sentence များ |
| `ordinal` | chunk နံပါတ် (0 မှ စ) |
| `candidate` | `buf` + sentence အသစ် (ထည့်လိုက်ရင် ဘယ်လောက်ဖြစ်မလဲ) |

အဓိက logic မှာ — sentence အသစ်ကို **ထည့်လိုက်ရင် `CHUNK_SIZE` ကျော်မလား** ကို
အရင် တွက်ပြီး (`candidate`)၊ ကျော်ရင် လက်ရှိ `buf` ကို chunk အဖြစ် **flush**
လုပ်ပါတယ်။ ဒါကြောင့် sentence တစ်ခုတည်းက size ကျော်လျှင်ပင် တစ်ခုတည်း chunk
ဖြစ်နိုင်ပါတယ် — sentence အလယ်တွင် ဖြတ်ခြင်း **မရှိ** ပါ။

### အကွက်တစ်ခုချင်း trace

```python
import re
from difflib import SequenceMatcher

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
CONF_EXACT, CONF_ALIAS, CONF_FUZZY, FUZZY_THRESHOLD = 0.95, 0.80, 0.55, 0.85
ALIAS_INDEX, CANONICAL_INDEX = {}, {}
for _entry in GAZETTEER:
    CANONICAL_INDEX[_entry["canonical"].lower()] = _entry
    for _alias in _entry["aliases"]:
        ALIAS_INDEX[_alias.lower()] = _entry
_BOUNDED = r"(?<![\w-])(?:%s)(?![\w-])" % "|".join(
    re.escape(a) for a in sorted(ALIAS_INDEX, key=len, reverse=True))
_DETERMINER = r"(?:(?:a|an|the)\s+)?"
PATTERN_RULES = [
    ("IS_A", r"(?:is|are)\s+(?:a|an)"),
    ("USES", r"(?:uses?|use)"),
    ("BUILT_ON", r"(?:is\s+built\s+on|runs?\s+on|is\s+based\s+on)"),
    ("DEVELOPED_BY", r"(?:was\s+developed\s+by|develops?)"),
    ("INCLUDES", r"(?:contains?|includes?)"),
]
COOCCURRENCE_CONFIDENCE = 0.45

CHUNK_SIZE = 140


def split_sentences(text):
    return [s.strip() for s in re.split(r"(?<=[.!?])\s+", text) if s.strip()]


TEXT = ("Neo4j  is a graph database. Neo4j uses Cypher as its query language. "
        "GraphRAG is built on a Knowledge Graph. Nous Research develops open models.")
buf, ordinal = "", 0
print("%-3s %-9s %5s %5s  %s" % ("i", "sentence", "buf", "cand", "action"))
for i, sentence in enumerate(split_sentences(TEXT)):
    candidate = (buf + " " + sentence).strip() if buf else sentence
    if buf and len(candidate) > CHUNK_SIZE:
        action = "flush %s:c%02d" % ("doc-001", ordinal)
        ordinal, buf = ordinal + 1, sentence
    else:
        action = "buffer"
        buf = candidate
    print("%-3d %-9s %5d %5d  %s" % (i, sentence.split()[0], len(buf), len(candidate), action))
```

Output —

```text
i   sentence    buf  cand  action
0   Neo4j        27    27  buffer
1   Neo4j        68    68  buffer
2   GraphRAG    108   108  buffer
3   Nous         35   144  flush doc-001:c00
```

| ကြိမ် | sentence | `buf` length | `candidate` | ဆုံးဖြတ်ချက် |
| --- | --- | --- | --- | --- |
| 0 | `Neo4j  is a graph database.` | 27 | 27 | buffer |
| 1 | `Neo4j uses Cypher as its query language.` | 68 | 68 | buffer |
| 2 | `GraphRAG is built on a Knowledge Graph.` | 108 | 108 | buffer |
| 3 | `Nous Research develops open models.` | 35 | **144** | flush (`144 > 140`) → `doc-001:c00` |

ကြိမ် ၃ တွင် `candidate = 144` ဖြစ်လို့ `CHUNK_SIZE = 140` ကို ကျော်ပါတယ်။
ဒါကြောင့် ယခင် `buf` (108) ကို flush လုပ်ပြီး sentence အသစ်ကို buffer အသစ်
အဖြစ် စပါတယ်။

---

## 3. `resolve_surface()` — surface form ကို canonical entity အဖြစ် ပြောင်းခြင်း

```python
import re
from difflib import SequenceMatcher

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
CONF_EXACT, CONF_ALIAS, CONF_FUZZY, FUZZY_THRESHOLD = 0.95, 0.80, 0.55, 0.85
ALIAS_INDEX, CANONICAL_INDEX = {}, {}
for _entry in GAZETTEER:
    CANONICAL_INDEX[_entry["canonical"].lower()] = _entry
    for _alias in _entry["aliases"]:
        ALIAS_INDEX[_alias.lower()] = _entry
_BOUNDED = r"(?<![\w-])(?:%s)(?![\w-])" % "|".join(
    re.escape(a) for a in sorted(ALIAS_INDEX, key=len, reverse=True))
_DETERMINER = r"(?:(?:a|an|the)\s+)?"
PATTERN_RULES = [
    ("IS_A", r"(?:is|are)\s+(?:a|an)"),
    ("USES", r"(?:uses?|use)"),
    ("BUILT_ON", r"(?:is\s+built\s+on|runs?\s+on|is\s+based\s+on)"),
    ("DEVELOPED_BY", r"(?:was\s+developed\s+by|develops?)"),
    ("INCLUDES", r"(?:contains?|includes?)"),
]
COOCCURRENCE_CONFIDENCE = 0.45


def resolve_surface(surface):
    key = surface.lower()
    if key in CANONICAL_INDEX:
        return CANONICAL_INDEX[key], CONF_EXACT, "canonical"
    if key in ALIAS_INDEX:
        return ALIAS_INDEX[key], CONF_ALIAS, "alias"
    best, best_ratio = None, 0.0
    for alias, entry in ALIAS_INDEX.items():
        ratio = SequenceMatcher(None, key, alias).ratio()
        if ratio > best_ratio:
            best, best_ratio = entry, ratio
    if best is not None and best_ratio >= FUZZY_THRESHOLD:
        return best, CONF_FUZZY, "fuzzy"
    return None, 0.0, "unresolved"


for surface in ["Neo4j", "neo4j", "Graph Rag", "Knowledg Graph", "knowledg graphs", "Banana"]:
    entry, conf, kind = resolve_surface(surface)
    name = entry["canonical"] if entry else "<none>"
    print("%-16s -> %-16s %.2f %s" % (surface, name, conf, kind))
```

Output —

```text
Neo4j            -> Neo4j            0.95 canonical
neo4j            -> Neo4j            0.95 canonical
Graph Rag        -> GraphRAG         0.80 alias
Knowledg Graph   -> Knowledge Graph  0.55 fuzzy
knowledg graphs  -> Knowledge Graph  0.55 fuzzy
Banana           -> <none>           0.00 unresolved
```

### သုံးဆင့် ကြည့်ခြင်း

Function က `(entry, confidence, kind)` သုံးခု ပြန်ပါတယ်။ အစဉ်လိုက် ကြည့်ပါတယ် —

| အဆင့် | စစ်ဆေးချက် | `kind` | `confidence` |
| --- | --- | --- | --- |
| 1 | canonical အမည် နှင့် ကိုက်သည် | `canonical` | 0.95 |
| 2 | alias စာရင်းထဲ ပါသည် | `alias` | 0.80 |
| 3 | fuzzy ratio ≥ `FUZZY_THRESHOLD` | `fuzzy` | 0.55 |
| — | မကိုက်ညီ | `unresolved` | 0.00 |

`Neo4j` နှင့် `neo4j` နှစ်ခုလုံး `0.95 canonical` ရတာကို ကြည့်ပါ။ `surface.lower()`
ကြောင့် case မခွဲဘဲ စစ်တာဖြစ်ပါတယ်။ `Graph Rag` က alias စာရင်းထဲ (`"graph rag"`)
တိုက်ရိုက် ပါလို့ `alias` ရတာဖြစ်ပြီး၊ `Knowledg Graph` က တိုက်ရိုက် မပါလို့
fuzzy အဆင့်သို့ ကျပါတယ်။

### Fuzzy fallback သည် linear search ဖြစ်သည်

```python
for alias, entry in ALIAS_INDEX.items():
    ratio = SequenceMatcher(None, key, alias).ratio()
    if ratio > best_ratio:
        best, best_ratio = entry, ratio
```

Alias အားလုံးကို တစ်ခုချင်း နှိုင်းယှဉ်ပြီး **အမြင့်ဆုံး ratio** ရှိသူကို
ရွေးပါတယ်။ Alias `N` ခုရှိရင် တစ်ကြိမ် resolve လုပ်တိုင်း `N` ကြိမ်
`SequenceMatcher` run ပါတယ်။ Corpus ကြီးလာရင် ဤအဆင့်က **hot path** ဖြစ်လာနိုင်ပါတယ် —
production တွင် block/trigram index ဖြင့် candidate ကို အရင်ကျဉ်းစေပါတယ်။

### `SequenceMatcher.ratio()` က ဘာပြန်သလဲ။

```python
from difflib import SequenceMatcher

print(round(SequenceMatcher(None, "knowledg graph", "knowledge graph").ratio(), 2))
print(round(SequenceMatcher(None, "banana", "graphrag").ratio(), 2))
print(round(SequenceMatcher(None, "graph rag", "graphrag").ratio(), 2))
```

Output —

```text
0.97
0.29
0.94
```

`ratio()` သည် `2 * matching / total_length` ဖြစ်ပြီး ၀.၀ မှ ၁.၀ အထိ
ပြန်ပါတယ်။ `knowledg graph` သည် `knowledge graph` နှင့် 0.97 ရသဖြင့်
`FUZZY_THRESHOLD = 0.85` ကို ကျော်ပါတယ်။ `banana` က 0.29 သာ ရသဖြင့်
unresolved ဖြစ်ပါတယ်။

---

## 4. `find_mentions()` — sentence ထဲက surface များ အစဉ်လိုက်

```python
import re
from difflib import SequenceMatcher

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
CONF_EXACT, CONF_ALIAS, CONF_FUZZY, FUZZY_THRESHOLD = 0.95, 0.80, 0.55, 0.85
ALIAS_INDEX, CANONICAL_INDEX = {}, {}
for _entry in GAZETTEER:
    CANONICAL_INDEX[_entry["canonical"].lower()] = _entry
    for _alias in _entry["aliases"]:
        ALIAS_INDEX[_alias.lower()] = _entry
_BOUNDED = r"(?<![\w-])(?:%s)(?![\w-])" % "|".join(
    re.escape(a) for a in sorted(ALIAS_INDEX, key=len, reverse=True))
_DETERMINER = r"(?:(?:a|an|the)\s+)?"
PATTERN_RULES = [
    ("IS_A", r"(?:is|are)\s+(?:a|an)"),
    ("USES", r"(?:uses?|use)"),
    ("BUILT_ON", r"(?:is\s+built\s+on|runs?\s+on|is\s+based\s+on)"),
    ("DEVELOPED_BY", r"(?:was\s+developed\s+by|develops?)"),
    ("INCLUDES", r"(?:contains?|includes?)"),
]
COOCCURRENCE_CONFIDENCE = 0.45


def find_mentions(sentence):
    hits = sorted(((m.start(), m.group(0)) for m in re.finditer(_BOUNDED, sentence, re.I)),
                  key=lambda i: i[0])
    return [surface for _, surface in hits]


print(find_mentions("Neo4j,  GraphRAG and Cypher are widely used in production."))
print(find_mentions("Neo4j uses Cypher as its query language."))
```

Output —

```text
['Neo4j', 'GraphRAG', 'Cypher']
['Neo4j', 'Cypher']
```

### `_BOUNDED` က ဘာကြောင့် လိုသလဲ။

```python
_BOUNDED = r"(?<![\w-])(?:%s)(?![\w-])" % "|".join(
    re.escape(a) for a in sorted(ALIAS_INDEX, key=len, reverse=True))
```

| အပိုင်း | ရည်ရွယ်ချက် |
| --- | --- |
| `(?<![\w-])` | ရှေ့တွင် စာလုံး/ဂဏန်း/underscore/hyphen မရှိရ — **negative lookbehind** |
| `(?:%s)` | alias များကို အုပ်စုအဖြစ် |
| `(?![\w-])` | နောက်တွင် စာလုံး/ဂဏန်း/underscore/hyphen မရှိရ — **negative lookahead** |

`sorted(..., key=len, reverse=True)` ကြောင့် **ရှည်ဆုံး alias အရင်** ရှာပါတယ်။
မဟုတ်ရင် `neo4j inc` ထဲက `neo4j` ကိုသာ ဖမ်းမိပြီး `inc` ကျန်ခဲ့ပါမယ်။

`re.finditer(_BOUNDED, sentence, re.I)` က `re.I` **ဖြင့်** run ပါတယ်။
`re.I` မထည့်ရင် `neo4j` (စာလုံးအသေး) ကို လုံးဝ မတွေ့ပါ။

### `finditer` က match object များ၊ `m.start()` က position

```python
hits = sorted(((m.start(), m.group(0)) for m in re.finditer(_BOUNDED, sentence, re.I)),
              key=lambda i: i[0])
```

`re.finditer()` က match object များကို iterator အဖြစ် ပြန်ပါတယ်။ `m.start()` က
တွေ့သည့် နေရာ၊ `m.group(0)` က တွေ့သည့် စာသား။ `(start, text)` tuple များကို
position အလိုက် `sorted()` လုပ်ပါတယ် — ဤအစီအစဉ်က co-occurrence pair ဖော်ရန်
အရေးကြီးပါတယ် (စာသားထဲ ဘယ်စာလုံးက ရှေးရှေးပေါ်လာလဲ ဆိုတာ ရေတွက်ရန်)။

---

## 5. `extract_from_chunk()` — pattern rule ဖြင့် triple ထုတ်ခြင်း

```python
import re

ALIASES = ["neo4j", "graphrag", "knowledge graph"]
BOUNDED = r"(?<![\w-])(?:%s)(?![\w-])" % "|".join(
    re.escape(a) for a in sorted(ALIASES, key=len, reverse=True))
DETERMINER = r"(?:(?:a|an|the)\s+)?"
connector = r"(?:is\s+built\s+on|runs?\s+on|is\s+based\s+on)"
pattern = r"(?P<a>%s)\s+%s\s+%s(?P<b>%s)" % (BOUNDED, connector, DETERMINER, BOUNDED)

print(pattern)
print()
for match in re.finditer(pattern, "GraphRAG is built on a Knowledge Graph.", re.I):
    print("a =", match.group("a"))
    print("b =", match.group("b"))
```

Output —

```text
(?P<a>(?<![\w-])(?:knowledge\ graph|graphrag|neo4j)(?![\w-]))\s+(?:is\s+built\s+on|runs?\s+on|is\s+based\s+on)\s+(?:(?:a|an|the)\s+)?(?P<b>(?<![\w-])(?:knowledge\ graph|graphrag|neo4j)(?![\w-]))

a = GraphRAG
b = Knowledge Graph
```

### Named group `(?P<a>...)`

`(?P<a>...)` က group ကို **အမည်ပေး** ပါတယ်။ ဒါကြောင့် `match.group(1)` လို့
နံပါတ်နဲ့ မမှတ်ဘဲ `match.group("a")` လို့ ဖတ်နိုင်ပါတယ်။ Pattern ရှည်လာတဲ့အခါ
အလွန်အသုံးဝင်ပါတယ် — နံပါတ်ရေတွက်စရာ မလိုပါ။

### Trap — `_DETERMINER` မထည့်ရင် triple လုံးဝ လျော့ကျသည်

```python
import re
from difflib import SequenceMatcher

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
CONF_EXACT, CONF_ALIAS, CONF_FUZZY, FUZZY_THRESHOLD = 0.95, 0.80, 0.55, 0.85
ALIAS_INDEX, CANONICAL_INDEX = {}, {}
for _entry in GAZETTEER:
    CANONICAL_INDEX[_entry["canonical"].lower()] = _entry
    for _alias in _entry["aliases"]:
        ALIAS_INDEX[_alias.lower()] = _entry
_BOUNDED = r"(?<![\w-])(?:%s)(?![\w-])" % "|".join(
    re.escape(a) for a in sorted(ALIAS_INDEX, key=len, reverse=True))
_DETERMINER = r"(?:(?:a|an|the)\s+)?"
PATTERN_RULES = [
    ("IS_A", r"(?:is|are)\s+(?:a|an)"),
    ("USES", r"(?:uses?|use)"),
    ("BUILT_ON", r"(?:is\s+built\s+on|runs?\s+on|is\s+based\s+on)"),
    ("DEVELOPED_BY", r"(?:was\s+developed\s+by|develops?)"),
    ("INCLUDES", r"(?:contains?|includes?)"),
]
COOCCURRENCE_CONFIDENCE = 0.45

SENTENCE = "GraphRAG is built on a Knowledge Graph."
connector = r"(?:is\s+built\s+on|runs?\s+on|is\s+based\s+on)"

with_det = r"(?P<a>%s)\s+%s\s+%s(?P<b>%s)" % (_BOUNDED, connector, _DETERMINER, _BOUNDED)
without_det = r"(?P<a>%s)\s+%s\s+(?P<b>%s)" % (_BOUNDED, connector, _BOUNDED)

print("with _DETERMINER    :", [m.group(0) for m in re.finditer(with_det, SENTENCE, re.I)])
print("without _DETERMINER :", [m.group(0) for m in re.finditer(without_det, SENTENCE, re.I)])
```

Output —

```text
with _DETERMINER    : ['GraphRAG is built on a Knowledge Graph']
without _DETERMINER : []
```

`is built on a Knowledge Graph` ထဲတွင် article `a` ပါနေတာကြောင့် `_DETERMINER`
မထည့်ရင် entity `b` ၏ အစကို `a` က ပိတ်ဆို့ပါတယ်။ `_DETERMINER` က
`(?:(?:a|an|the)\s+)?` ဖြစ်ပြီး **optional** (`?` ပါ) ဖြစ်တာကြောင့် article ရှိသည်ဖြစ်စေ၊
မရှိသည်ဖြစ်စေ match ရပါတယ်။ ဒါကြောင့် `USES` rule (`Neo4j uses Cypher`) ကဲ့သို့
article မပါတဲ့ sentence များလည်း မပျက်ပါ။

---

## 6. Co-occurrence fallback နှင့် `matched` flag

```python
import re
from difflib import SequenceMatcher

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
CONF_EXACT, CONF_ALIAS, CONF_FUZZY, FUZZY_THRESHOLD = 0.95, 0.80, 0.55, 0.85
ALIAS_INDEX, CANONICAL_INDEX = {}, {}
for _entry in GAZETTEER:
    CANONICAL_INDEX[_entry["canonical"].lower()] = _entry
    for _alias in _entry["aliases"]:
        ALIAS_INDEX[_alias.lower()] = _entry
_BOUNDED = r"(?<![\w-])(?:%s)(?![\w-])" % "|".join(
    re.escape(a) for a in sorted(ALIAS_INDEX, key=len, reverse=True))
_DETERMINER = r"(?:(?:a|an|the)\s+)?"
PATTERN_RULES = [
    ("IS_A", r"(?:is|are)\s+(?:a|an)"),
    ("USES", r"(?:uses?|use)"),
    ("BUILT_ON", r"(?:is\s+built\s+on|runs?\s+on|is\s+based\s+on)"),
    ("DEVELOPED_BY", r"(?:was\s+developed\s+by|develops?)"),
    ("INCLUDES", r"(?:contains?|includes?)"),
]
COOCCURRENCE_CONFIDENCE = 0.45


def resolve_surface(surface):
    key = surface.lower()
    if key in CANONICAL_INDEX:
        return CANONICAL_INDEX[key], CONF_EXACT, "canonical"
    if key in ALIAS_INDEX:
        return ALIAS_INDEX[key], CONF_ALIAS, "alias"
    return None, 0.0, "unresolved"


def find_mentions(sentence):
    hits = sorted(((m.start(), m.group(0)) for m in re.finditer(_BOUNDED, sentence, re.I)),
                  key=lambda i: i[0])
    return [surface for _, surface in hits]


def extract(sentence, use_matched_flag):
    triples, matched = [], False
    for predicate, connector in PATTERN_RULES:
        pattern = r"(?P<a>%s)\s+%s\s+%s(?P<b>%s)" % (_BOUNDED, connector, _DETERMINER, _BOUNDED)
        for match in re.finditer(pattern, sentence, re.I):
            a_entry, a_conf, _ = resolve_surface(match.group("a"))
            b_entry, b_conf, _ = resolve_surface(match.group("b"))
            if a_entry is None or b_entry is None:
                continue
            matched = True
            triples.append((a_entry["canonical"], predicate, b_entry["canonical"]))
    if not matched or not use_matched_flag:
        resolved = [e for e in (resolve_surface(m)[0] for m in find_mentions(sentence)) if e is not None]
        for left, right in zip(resolved, resolved[1:]):
            if left["canonical"] != right["canonical"]:
                triples.append((left["canonical"], "RELATED_TO", right["canonical"]))
    return triples


SENTENCE = "GraphRAG is built on a Knowledge Graph."
print("with matched flag :", extract(SENTENCE, True))
print("without flag      :", extract(SENTENCE, False))
```

Output —

```text
with matched flag : [('GraphRAG', 'BUILT_ON', 'Knowledge Graph')]
without flag      : [('GraphRAG', 'BUILT_ON', 'Knowledge Graph'), ('GraphRAG', 'RELATED_TO', 'Knowledge Graph')]
```

`matched` flag က "ဤ sentence တွင် pattern rule တစ်ခုခု ကိုက်ညီခဲ့ပြီးလား" ကို
မှတ်ထားပါတယ်။ Pattern ကိုက်ညီပြီးသားဆိုရင် co-occurrence fallback ကို
**မလုပ်တော့ပါ**။ flag မထည့်ရင် တူညီတဲ့ entity နှစ်ခုအတွက် triple နှစ်ခု
(တိကျတဲ့ `BUILT_ON` နှင့် မှန်းဆရတဲ့ `RELATED_TO`) ရလာပြီး graph ထဲ
အချက်အလက် **ပွားသွား** ပါတယ်။

### `zip(resolved, resolved[1:])` — ကပ်နေတဲ့ အတွဲများ

```python
import re

print(list(zip(["Neo4j", "GraphRAG", "Cypher"], ["GraphRAG", "Cypher"])))
```

Output —

```text
[('Neo4j', 'GraphRAG'), ('GraphRAG', 'Cypher')]
```

`resolved[1:]` က ပထမ element ကို ဖြုတ်လိုက်တဲ့ list ဖြစ်ပါတယ်။ `zip()` က
နှစ် list ကို ဒေါင်လိုက် တွဲပါတယ်။ ဒါကြောင့် **ကပ်နေတဲ့ အတွဲများ**
`(0,1)`, `(1,2)`, `(2,3)` … ရပါတယ်။ ဒါက **bigram window** pattern ဖြစ်ပါတယ်။
`if left["canonical"] != right["canonical"]` က စာလုံးတူတဲ့ အတွဲ (`Neo4j and Neo4j`)
ကို ဖယ်ပါတယ် — ဒါမှ self-loop မဖြစ်ပါ။

---

## 7. `run_pipeline()` — အဆင့်များ ချိတ်ဆက်ခြင်း

```python
import re
from difflib import SequenceMatcher

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
CONF_EXACT, CONF_ALIAS, CONF_FUZZY, FUZZY_THRESHOLD = 0.95, 0.80, 0.55, 0.85
ALIAS_INDEX, CANONICAL_INDEX = {}, {}
for _entry in GAZETTEER:
    CANONICAL_INDEX[_entry["canonical"].lower()] = _entry
    for _alias in _entry["aliases"]:
        ALIAS_INDEX[_alias.lower()] = _entry
_BOUNDED = r"(?<![\w-])(?:%s)(?![\w-])" % "|".join(
    re.escape(a) for a in sorted(ALIAS_INDEX, key=len, reverse=True))
_DETERMINER = r"(?:(?:a|an|the)\s+)?"
PATTERN_RULES = [
    ("IS_A", r"(?:is|are)\s+(?:a|an)"),
    ("USES", r"(?:uses?|use)"),
    ("BUILT_ON", r"(?:is\s+built\s+on|runs?\s+on|is\s+based\s+on)"),
    ("DEVELOPED_BY", r"(?:was\s+developed\s+by|develops?)"),
    ("INCLUDES", r"(?:contains?|includes?)"),
]
COOCCURRENCE_CONFIDENCE = 0.45

CHUNK_SIZE = 140
MIN_CONFIDENCE = 0.60
ALLOWED_PREDICATES = ("IS_A", "USES", "BUILT_ON", "DEVELOPED_BY", "INCLUDES", "RELATED_TO")
SAMPLE_CORPUS = [
    {"doc_id": "doc-001", "raw_text": "Neo4j  is a graph database.\nNeo4j uses Cypher as its query language. "
                                      "GraphRAG is built on a Knowledge Graph. Nous Research develops open models."},
    {"doc_id": "doc-002", "raw_text": "Graph Rag runs on Neo4j. GraphRAG is built on a Knowledge Graph. "
                                      "Neo4j was developed by Neo4j Inc. Neo4j,  GraphRAG and Cypher are widely "
                                      "used in production."},
    {"doc_id": "doc-003", "raw_text": "Entity Resolution merges duplicate nodes. GraphRAG uses Entity Resolution. "
                                      "LLM is a Transformer based model. Entity resolution includes alias mapping."},
]


def split_sentences(text):
    return [s.strip() for s in re.split(r"(?<=[.!?])\s+", text) if s.strip()]


def chunk_document(doc_id, text):
    chunks, buf, ordinal = [], "", 0
    for sentence in split_sentences(text):
        candidate = (buf + " " + sentence).strip() if buf else sentence
        if buf and len(candidate) > CHUNK_SIZE:
            chunks.append(("%s:c%02d" % (doc_id, ordinal), buf))
            ordinal, buf = ordinal + 1, sentence
        else:
            buf = candidate
    if buf:
        chunks.append(("%s:c%02d" % (doc_id, ordinal), buf))
    return chunks


def resolve_surface(surface):
    key = surface.lower()
    if key in CANONICAL_INDEX:
        return CANONICAL_INDEX[key], CONF_EXACT, "canonical"
    if key in ALIAS_INDEX:
        return ALIAS_INDEX[key], CONF_ALIAS, "alias"
    best, best_ratio = None, 0.0
    for alias, entry in ALIAS_INDEX.items():
        ratio = SequenceMatcher(None, key, alias).ratio()
        if ratio > best_ratio:
            best, best_ratio = entry, ratio
    if best is not None and best_ratio >= FUZZY_THRESHOLD:
        return best, CONF_FUZZY, "fuzzy"
    return None, 0.0, "unresolved"


def find_mentions(sentence):
    hits = sorted(((m.start(), m.group(0)) for m in re.finditer(_BOUNDED, sentence, re.I)),
                  key=lambda i: i[0])
    return [surface for _, surface in hits]


def extract_from_chunk(chunk_id, body):
    triples = []
    for sentence in split_sentences(body):
        matched = False
        for predicate, connector in PATTERN_RULES:
            pattern = r"(?P<a>%s)\s+%s\s+%s(?P<b>%s)" % (_BOUNDED, connector, _DETERMINER, _BOUNDED)
            for match in re.finditer(pattern, sentence, re.I):
                a_entry, a_conf, _ = resolve_surface(match.group("a"))
                b_entry, b_conf, _ = resolve_surface(match.group("b"))
                if a_entry is None or b_entry is None:
                    continue
                matched = True
                triples.append((a_entry["canonical"], predicate, b_entry["canonical"],
                                round(min(a_conf, b_conf), 2), chunk_id))
        if not matched:
            resolved = [e for e in (resolve_surface(m)[0] for m in find_mentions(sentence)) if e is not None]
            for left, right in zip(resolved, resolved[1:]):
                if left["canonical"] != right["canonical"]:
                    triples.append((left["canonical"], "RELATED_TO", right["canonical"],
                                    COOCCURRENCE_CONFIDENCE, chunk_id))
    return triples


def quality_gate(triples, names):
    accepted, rejected, seen, keys = [], [], set(), set()
    for name_a, predicate, name_b, conf, chunk_id in triples:
        key = (name_a, predicate, name_b)
        if name_a == name_b:
            rejected.append("self_loop")
        elif predicate not in ALLOWED_PREDICATES:
            rejected.append("unknown_predicate")
        elif name_a not in names or name_b not in names:
            rejected.append("dangling_endpoint")
        elif conf < MIN_CONFIDENCE:
            rejected.append("low_confidence")
        elif key in keys:
            rejected.append("duplicate")
        else:
            keys.add(key)
            accepted.append((name_a, predicate, name_b, conf, chunk_id))
    return accepted, rejected


chunks = [c for d in SAMPLE_CORPUS for c in chunk_document(d["doc_id"], d["raw_text"])]
raw_triples = []
for chunk_id, body in chunks:
    raw_triples.extend(extract_from_chunk(chunk_id, body))
names = {entry["canonical"] for entry in GAZETTEER}
merged, seen_keys = [], []
for triple in raw_triples:
    if (triple[0], triple[1], triple[2]) not in seen_keys:
        seen_keys.append((triple[0], triple[1], triple[2]))
        merged.append(triple)
accepted, rejected = quality_gate(merged, names)

print("ingest     : %d documents" % len(SAMPLE_CORPUS))
print("chunk      : %d chunks -> %s" % (len(chunks), [c[0] for c in chunks]))
print("extract    : %d raw triples (scripted extractor)" % len(raw_triples))
print("resolve    : %d canonical entities" % len({n for t in raw_triples for n in (t[0], t[2])}))
print("merge      : %d unique triples" % len(merged))
print("gate       : %d accepted / %d rejected" % (len(accepted), len(rejected)))

entry, conf, kind = resolve_surface("Graph Rag")
print("resolution : 'Graph Rag' -> %s (conf=%.2f, kind=%s)" % (entry["canonical"], conf, kind))
fuzzy_entry, fuzzy_conf, fuzzy_kind = resolve_surface("Knowledg Graph")
print("resolution : 'Knowledg Graph' -> %s (conf=%.2f, kind=%s)"
      % (fuzzy_entry["canonical"], fuzzy_conf, fuzzy_kind))

assert len(chunks) == 6 and len(raw_triples) == 9 and len(merged) == 8
assert len(accepted) == 5 and len(rejected) == 3
assert entry["canonical"] == "GraphRAG" and conf == 0.80 and kind == "alias"
```

Output —

```text
ingest     : 3 documents
chunk      : 6 chunks -> ['doc-001:c00', 'doc-001:c01', 'doc-002:c00', 'doc-002:c01', 'doc-003:c00', 'doc-003:c01']
extract    : 9 raw triples (scripted extractor)
resolve    : 7 canonical entities
merge      : 8 unique triples
gate       : 5 accepted / 3 rejected
resolution : 'Graph Rag' -> GraphRAG (conf=0.80, kind=alias)
resolution : 'Knowledg Graph' -> Knowledge Graph (conf=0.55, kind=fuzzy)
```

### `run_pipeline()` ၏ တစ်လိုင်းချင်း composition

```python
documents = [normalize_document(doc) for doc in ingest_corpus(corpus)]
chunks = [c for doc in documents for c in chunk_document(doc)]
raw_triples = [t for chunk in chunks for t in extract_from_chunk(chunk)]
```

| လိုင်း | အလုပ် | ရလဒ် အရေအတွက် |
| --- | --- | --- |
| `ingest_corpus(corpus)` | raw dict → `Document` | 3 |
| `[normalize_document(doc) ...]` | text သန့်ရှင်း | 3 |
| `[... for doc in documents for c in chunk_document(doc)]` | document → chunk | 6 |
| `[... for chunk in chunks for t in extract_from_chunk(chunk)]` | chunk → triple | 9 |
| `resolve_entities(raw_triples)` | triple → entity | 7 |
| `merge_triples(raw_triples)` | duplicate ပေါင်း | 8 |
| `quality_gate(merged, entities)` | စစ်ထုတ် | 5 / 3 |
| `export_*` | format သုံးမျိုး | Cypher 12 / JSON 7+5 / CSV 7+5 |

Nested comprehension `[t for chunk in chunks for t in extract_from_chunk(chunk)]` က
**အဆင့်နှစ်ခု** ကို တစ်လိုင်းတည်း flat လုပ်ပါတယ်။

```python
flat = [c for doc in [[1, 2], [3]] for c in doc]
print(flat)
```

Output —

```text
[1, 2, 3]
```

ပထမ `for` က အဆင့်ပြင်ပ (outer)၊ ဒုတိယ `for` က အဆင့်အတွင်း (inner) ဖြစ်ပါတယ်။
`extract` ရလဒ် ၉ ခုသည် `resolve` ရလဒ် ၇ ခု ဖြစ်တာကို ကြည့်ပါ — triple များသည်
entity **၇ ခု** သာ ညွှန်တာကြောင့်ပါ။

---

## 8. ကိုယ်တိုင်လေ့ကျင့်ကြည့်ပါ

**မေးခွန်း** — အောက်ပါ code က ဘယ်ရလဒ် ပြန်ပေးမလဲ။

```python
import re


def split_sentences(text):
    return [s.strip() for s in re.split(r"(?<=[.!?])\s+", text) if s.strip()]


print(split_sentences("  Neo4j uses Cypher.  "))
```

1. `['Neo4j uses Cypher.']` — အစနှင့် အဆုံး space များ ဖယ်ပြီး sentence တစ်ခု
2. `['  Neo4j uses Cypher.  ']` — space များ ကျန်
3. `['Neo4j uses Cypher', '']` — empty string ပါ

<details>
<summary>အဖြေ ကြည့်ရန်</summary>

**အဖြေ — 1. `['Neo4j uses Cypher.']`**

အကြောင်းရင်း — `re.split(r"(?<=[.!?])\s+", "  Neo4j uses Cypher.  ")` သည်
delimiter `.` နောက်က space များသာ ခွဲသည် (အဆုံး `.` က delimiter မဟုတ်၊ ဘေး
space များ ရှိလည်း lookbehind အတွက် `.` က တစ်ခုတည်း)။ ဒါကြောင့်
`['  Neo4j uses Cypher.  ']` ရပြီး၊ list comprehension ထဲက `s.strip()` က
`'Neo4j uses Cypher.'` ဖြစ်စေသည်။ `if s.strip()` က empty string များကို
ဖယ်သည် — ဤဥပမာတွင် `''` မဖြစ်လာလို့ ထပ်ဆင့် အလုပ်မလိုပါ။

</details>

---

**အဓိက မှတ်ထားရန်** — Pipeline ၏ အဆင့်တိုင်းသည် **input ပြောင်းလဲမှုတစ်ခု**
ဖြစ်ပါတယ် — corpus → document → chunk → triple → entity → validated triple → export။
အဆင့်တိုင်းကို function တစ်ခုတည်းဖြင့် ခွဲထားတာကြောင့် တစ်ခုချင်း test လုပ်နိုင်ပါတယ်။
`split_sentences` ၏ lookbehind မပါရင် sentence ၏ အဆုံးသတ် အမှတ်အသား ပျောက်သည်။
`_DETERMINER` မပါရင် article ပါသော sentence များမှ triple လုံးဝ လျော့ကျသည်။
`matched` flag မပါရင် co-occurrence fallback က triple ပွားစေသည်။ ဤသုံးချက်သည်
pipeline တစ်ခုလုံး၏ **recall နှင့် precision** ကို တိုက်ရိုက် သက်ရောက်သည်။
