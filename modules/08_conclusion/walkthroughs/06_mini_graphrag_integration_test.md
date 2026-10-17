# Walkthrough 06 — End-to-end mini GraphRAG integration test (Exercise 6)

> ဤဖိုင်သည် Module 08 ၏ `solution.md` ထဲက Exercise 6 ကို **Python အခြေခံမှ စ၍**
> အပိုင်းလိုက် ရှင်းပြသည့် walkthrough ဖြစ်သည်။ ဤသည် module ၏ အကြီးဆုံး
> exercise ဖြစ်ပြီး M03–M07 ကို တစ်ခုတည်း pipeline အဖြစ် ချိတ်ဆက်ပြသည်။

---

## 0. ဤ Exercise က ဘာကို ဖြေရှင်းပေးသလဲ။

Stage တိုင်း သီးခြား အလုပ်လုပ်ကြောင်း သိရုံနှင့် မလုံလောက်ပါ။ **ချိတ်ဆက်လိုက်သည့်အခါ**
pipeline တစ်ခုလုံး correctness ရှိကြောင်း စစ်ရသည်။ ဤ Exercise က LLM မလိုဘဲ
rule-based/deterministic အစားထိုးမှုများဖြင့် pipeline တစ်ခုလုံးကို **test** လုပ်သည်။

```text
CORPUS_SENTENCES
   |  chunk_sentences (sentence-aware, overlap)
   v
chunks ---> extract_chunk_triples (RELATION_PATTERNS) ---> raw triples
                                                              |  dedupe_triples
                                                              v
                                                     triples + provenance
                                                              |  Graph.add_triple
                                                              v
                                                        in-memory graph
                                                              |
     question ---> entity_link ---> anchors ---> k_hop_subgraph
                                                     |
                                          serialize_context ---> generate_answer ---> answer
```

ဤ Exercise တွင် လေ့လာရမည့် Python concepts —

- `re.compile`, `\b`, `re.sub`, `re.IGNORECASE`
- Nested `while` loop နှင့် char budget (running size)
- `str.strip(chars)`, `str.lower()`, `dict.get(key, default)`
- `pattern.search()` နှင့် `match.start()`, `match.end()` slicing
- `OrderedDict` ဖြင့် dedupe နှင့် provenance list
- `class` — `__init__`၊ method၊ `defaultdict(list)`
- `set` operations (`|=`, `-=`), `any()` generator
- f-string, `sorted()`, `enumerate()`
- `str.join()`, `str.splitlines()`

---

## 1. `CORPUS_SENTENCES` နှင့် `RELATION_PATTERNS`

```python
import re

CORPUS_SENTENCES = [
    "Alice manages the Payments squad.",
    "Payments squad builds the Ledger service.",
    "Bob supports the Ledger service.",
    "Ledger service stores data in the Audit Store.",
    "Carol leads the Payments team.",
]

RELATION_PATTERNS = [
    ("MANAGES", re.compile(r"\bmanages\b")),
    ("BUILDS", re.compile(r"\bbuilds\b")),
    ("SUPPORTS", re.compile(r"\bsupports\b")),
    ("LEADS", re.compile(r"\bleads\b")),
    ("STORES_DATA_IN", re.compile(r"\bstores data in\b")),
]

print(len(CORPUS_SENTENCES))
for relation, pattern in RELATION_PATTERNS:
    match = pattern.search("Alice manages the Payments squad.")
    print(relation, "->", None if not match else (match.start(), match.end()))
```

Output —

```text
5
MANAGES -> (6, 13)
BUILDS -> None
SUPPORTS -> None
LEADS -> None
STORES_DATA_IN -> None
```

`CORPUS_SENTENCES` က sentence ၅ ခုပါသော list ဖြစ်သည် — ၎င်းသည် LLM ကို ခေါ်စရာ
မလိုဘဲ deterministic test corpus အဖြစ် သုံးသည်။

`RELATION_PATTERNS` ထဲက item တိုင်းက `(relation, compiled_pattern)` tuple ဖြစ်သည်။
`\b` က word boundary — `manages` ကို စကားလုံးအလိုက် ကိုက်ညီသည်။ `pattern.search()`
သည် ပထမဆုံး ကိုက်ညီမှုကို ပြန်သည်၊ မတွေ့လျှင် `None`။

```python
import re

PATTERN = re.compile(r"\bmanages\b")
match = PATTERN.search("Alice manages the Payments squad.")
print(match.group())
print(match.start(), match.end())
print("Alice manages the Payments squad."[match.start():match.end()])
```

Output —

```text
manages
6 13
manages
```

`match.start()` က `6`၊ `match.end()` က `13` — `[6:13]` slice က `manages` ကို ပြန်သည်။
ဤ slice နည်းက subject နှင့် object ကို ခွဲထုတ်ရန် သုံးသည်။

---

## 2. `clean_surface()` — Surface Text သန့်ရှင်းခြင်း

```python
import re


def clean_surface(text):
    surface = re.sub(r"^(the|a|an)\s+", "", text.strip(), flags=re.IGNORECASE)
    return surface.strip(" .,;:")


print(repr(clean_surface("the Payments squad.")))
print(repr(clean_surface("  Ledger Service  ")))
print(repr(clean_surface("a Ledger service")))
```

Output —

```text
'Payments squad'
'Ledger Service'
'Ledger service'
```

တစ်လိုင်းချင်း —

- `text.strip()` — ရှေ့/နောက် whitespace ဖယ်။
- `re.sub(r"^(the|a|an)\s+", "", ..., flags=re.IGNORECASE)` — အစပိုင်းက `the`/`a`/`an`
  ကို case မခွဲဘဲ ဖယ်။ `^` က စာသားအစ၊ `(the|a|an)` က alternation၊ `\s+` က space တစ်ခုနှင့်အထက်။
- `surface.strip(" .,;:")` — ရှေ့/နောက်က `.`၊ `,`၊ `;`၊ `:`၊ space ဖယ်။

```python
text = "THE  Ledger:"
print(repr(text.strip()))
print(repr(__import__("re").sub(r"^(the|a|an)\s+", "", text.strip(), flags=__import__("re").IGNORECASE)))
```

Output —

```text
'THE  Ledger:'
'Ledger:'
```

`re.IGNORECASE` က `THE` (uppercase) ကို လည်း ကိုက်ညီစေသည်။ `str.strip(chars)` တွင်
`chars` က **character set** ဖြစ်သည် — string တစ်ခုလုံး မဟုတ်ပါ။

```python
print(repr("...abc...".strip(".")))
print(repr("yyhelloYY".strip("yY")))
```

Output —

```text
'abc'
'hello'
```

---

## 3. `chunk_sentences()` — Sentence-aware Chunking

```python
def chunk_sentences(sentences, max_chars, overlap):
    """Sentence boundary ကို မချိုးဘဲ char budget အတွင်း ထည့်နိုင်သမျှ ထည့်သည်။"""
    chunks = []
    index = 0
    while index < len(sentences):
        current, size, cursor = [], 0, index
        while cursor < len(sentences):
            sentence = sentences[cursor]
            addition = len(sentence) + (1 if current else 0)
            if current and size + addition > max_chars:
                break
            current.append(sentence)
            size += addition
            cursor += 1
        chunks.append(current)
        if cursor >= len(sentences):
            break
        index = max(index + 1, cursor - overlap)
    return chunks


CORPUS_SENTENCES = [
    "Alice manages the Payments squad.",
    "Payments squad builds the Ledger service.",
    "Bob supports the Ledger service.",
    "Ledger service stores data in the Audit Store.",
    "Carol leads the Payments team.",
]
chunks = chunk_sentences(CORPUS_SENTENCES, 90, 1)
print([len(c) for c in chunks])
for chunk_id, chunk in enumerate(chunks):
    print("chunk %d: %s" % (chunk_id, chunk))
```

Output —

```text
[2, 2, 2, 2]
chunk 0: ['Alice manages the Payments squad.', 'Payments squad builds the Ledger service.']
chunk 1: ['Payments squad builds the Ledger service.', 'Bob supports the Ledger service.']
chunk 2: ['Bob supports the Ledger service.', 'Ledger service stores data in the Audit Store.']
chunk 3: ['Ledger service stores data in the Audit Store.', 'Carol leads the Payments team.']
```

### 3.1 Nested `while` နှင့် `size` budget

- **အပြင် `while index < len(sentences)`** — chunk တစ်ခု ဖန်တီးပြီးတိုင်း နောက် chunk ၏
  အစကို ရွေး။
- **အတွင်း `while cursor < len(sentences)`** — `max_chars` budget အတွင်း sentence များ
  ထည့်။

`addition = len(sentence) + (1 if current else 0)` က sentence အရှည်နှင့် သူ့အရှေ့က
space ကို (chunk အလွတ်မဟုတ်လျှင်) ထည့်တွက်သည်။

```python
current = []
for sentence in ["ab", "cde", "fg"]:
    addition = len(sentence) + (1 if current else 0)
    current.append(sentence)
    print("addition =", addition)
```

Output —

```text
addition = 2
addition = 4
addition = 3
```

ပထမဆုံး sentence အတွက် `current` က အလွတ်ဖြစ်သဖြင့် `+0`၊ ဒုတိယအတွက် ရှိပြီးဖြစ်သဖြင့် `+1`။
`len("cde") + 1 = 4`။

### 3.2 Overlap — `index = max(index + 1, cursor - overlap)`

`overlap=1` ဖြစ်သောကြောင့် နောက် chunk က sentence တစ်ခု **ပြန်စ** သည်။ ၎င်းသည် chunk boundary
၏ အခြေအနေကို ထိန်းသည် — သို့သော် triple များ **ထပ်ထွက်** စေသည် (Section 6 တွင်
dedupe ဖြင့် ပြန်ပေါင်း)။

```python
print(max(0 + 1, 2 - 1))
print(max(2 + 1, 4 - 1))
```

Output —

```text
1
3
```

`max(index + 1, cursor - overlap)` က `cursor - overlap` က `index + 1` ထက် မငယ်စေရပါ —
မဟုတ်လျှင် infinite loop ဖြစ်နိုင်သည်။

---

## 4. `resolve_entity()` — Entity Resolution

```python
import re


def clean_surface(text):
    surface = re.sub(r"^(the|a|an)\s+", "", text.strip(), flags=re.IGNORECASE)
    return surface.strip(" .,;:")


ENTITY_CANONICAL = {
    "alice": "Alice",
    "bob": "Bob",
    "carol": "Carol",
    "dave": "Dave",
    "payments squad": "Payments Squad",
    "ledger service": "Ledger Service",
    "audit store": "Audit Store",
}
ENTITY_ALIASES = {
    "payments team": "payments squad",
}


def resolve_entity(surface):
    key = re.sub(r"\s+", " ", clean_surface(surface).lower())
    key = ENTITY_ALIASES.get(key, key)
    return ENTITY_CANONICAL.get(key, clean_surface(surface))


print(repr(resolve_entity("Payments team")))
print(repr(resolve_entity("the Payments squad")))
print(repr(resolve_entity("Blob")))
```

Output —

```text
'Payments Squad'
'Payments Squad'
'Blob'
```

Entity resolution သုံးအဆင့် —

1. **normalize key** — `clean_surface(...).lower()` ပြီး `re.sub(r"\s+", " ", ...)` ဖြင့်
   whitespace များစွာကို space တစ်ခုတည်း ပြောင်း။
2. **alias ဖြေ** — `ENTITY_ALIASES.get(key, key)` က `"payments team"` ကို
   `"payments squad"` သို့ အစားထိုး။
3. **canonical ရှာ** — `ENTITY_CANONICAL.get(key, clean_surface(surface))` က
   canonical အမည် ပြန်၊ မရှိလျှင် မူရင်း surface ပြန်။

`dict.get(key, default)` က key မရှိလျှင် `default` ပြန်သည် — `KeyError` မဖြစ်ပါ။

```python
mapping = {"a": 1}
print(mapping.get("a", 0))
print(mapping.get("z", 0))
```

Output —

```text
1
0
```

`resolve_entity("Blob")` က canonical မရှိသောကြောင့် `"Blob"` ကို ပြန်သည် — entity
resolution က fallback ကို ထိန်းထားသည်။ ၎င်းသည် **graph ထဲ node မဖြစ်သင့်သော** surface
ဆိုလျှင် downstream တွင် filter ရမည့် အပိုင်းပါ။

---

## 5. `extract_chunk_triples()` — Scripted Extraction

```python
import re

RELATION_PATTERNS = [
    ("MANAGES", re.compile(r"\bmanages\b")),
    ("LEADS", re.compile(r"\bleads\b")),
]


def clean_surface(text):
    surface = re.sub(r"^(the|a|an)\s+", "", text.strip(), flags=re.IGNORECASE)
    return surface.strip(" .,;:")


def extract_chunk_triples(chunk, chunk_id):
    records = []
    for sentence in chunk:
        for relation, pattern in RELATION_PATTERNS:
            match = pattern.search(sentence)
            if not match:
                continue
            subject = clean_surface(sentence[:match.start()])
            obj = clean_surface(sentence[match.end():])
            if not subject or not obj:
                continue
            records.append((chunk_id, subject, relation, obj))
    return records


for record in extract_chunk_triples(["Alice manages the Payments squad.", "Carol leads the Payments team."], 0):
    print(record)
```

Output —

```text
(0, 'Alice', 'MANAGES', 'Payments squad')
(0, 'Carol', 'LEADS', 'Payments team')
```

`sentence[:match.start()]` က verb အရှေ့က စာသား (subject)၊ `sentence[match.end():]`
ကနောက်က စာသား (object)။ `if not subject or not obj:` က အလွတ်ဖြစ်လျှင် ကျော်သည် —
၎င်းသည် `or` ၏ **short-circuit** ဖြစ်သည်။

> ဤနေရာတွင် `resolve_entity` မပါသေး — ဤ walkthrough ၏ assembed script တွင်
> `records.append((chunk_id, resolve_entity(subject), relation, resolve_entity(obj)))`
> ဟူသော ပုံစံဖြင့် resolve ကို ခေါ်ပါသည်။ ဤ section က slicing logic ကိုသာ ပြသည်။

---

## 6. `dedupe_triples()` — Provenance ပါ Dedupe

```python
from collections import OrderedDict


def dedupe_triples(records):
    merged = OrderedDict()
    for chunk_id, subject, relation, obj in records:
        key = (subject, relation, obj)
        if key not in merged:
            merged[key] = {"subject": subject, "relation": relation, "object": obj, "chunks": [chunk_id]}
        elif chunk_id not in merged[key]["chunks"]:
            merged[key]["chunks"].append(chunk_id)
    return list(merged.values())


records = [
    (0, "Payments Squad", "BUILDS", "Ledger Service"),
    (1, "Payments Squad", "BUILDS", "Ledger Service"),
    (0, "Alice", "MANAGES", "Payments Squad"),
]
for triple in dedupe_triples(records):
    print(triple)
```

Output —

```text
{'subject': 'Payments Squad', 'relation': 'BUILDS', 'object': 'Ledger Service', 'chunks': [0, 1]}
{'subject': 'Alice', 'relation': 'MANAGES', 'object': 'Payments Squad', 'chunks': [0]}
```

`key = (subject, relation, obj)` က dedupe ၏ အခြေခံဖြစ်သည်။ Triple တူညီပါက
`chunks` list ထဲ chunk id ကို **ထပ်မထည့်** ဘဲ (provenance list ထဲ ရှိပြီး/မရှိ စစ်ဆေးပြီး)
ပေါင်းသည်။ ဤနည်းဖြင့် — overlap ကြောင့် triple ထပ်ထွက်သော်လည်း — ရလဒ် triple က
တစ်ခုတည်း ဖြစ်ပြီး၊ ဘယ် chunk များမှ လာသည်ကို သိမ်းထားသည်။

`OrderedDict` က triple အစဉ်ကို ပထမ ပေါ်ပေါက်သည့် အစီအစဉ်အတိုင်း ထိန်းသည် — ထိုမှသာ
output က run တိုင်း တူပါမည်။

---

## 7. `Graph` Class — In-memory Graph

```python
from collections import defaultdict


class Graph:
    def __init__(self):
        self.nodes = set()
        self.out = defaultdict(list)
        self.inn = defaultdict(list)

    def add_triple(self, subject, relation, obj):
        self.nodes.add(subject)
        self.nodes.add(obj)
        if (relation, obj) not in self.out[subject]:
            self.out[subject].append((relation, obj))
        if (relation, subject) not in self.inn[obj]:
            self.inn[obj].append((relation, subject))

    def edges(self):
        return sorted((s, r, o) for s in self.out for (r, o) in self.out[s])

    def neighbors(self, node):
        found = {obj for _, obj in self.out[node]}
        found |= {subject for _, subject in self.inn[node]}
        return found


graph = Graph()
graph.add_triple("Alice", "MANAGES", "Payments Squad")
graph.add_triple("Carol", "LEADS", "Payments Squad")
print(sorted(graph.nodes))
print(graph.edges())
print(sorted(graph.neighbors("Payments Squad")))
```

Output —

```text
['Alice', 'Carol', 'Payments Squad']
[('Alice', 'MANAGES', 'Payments Squad'), ('Carol', 'LEADS', 'Payments Squad')]
['Alice', 'Carol']
```

### 7.1 `__init__` နှင့် `defaultdict`

`__init__(self)` က object ဖန်တီးချိန် run သည်။ Field သုံးခု —

- `self.nodes` — set (node အမည်များ)
- `self.out` — subject → `(relation, object)` list (အထွက် edge များ)
- `self.inn` — object → `(relation, subject)` list (အဝင် edge များ)

`defaultdict(list)` က **မရှိသေးသော key** ကို ဖတ်သည့်အခါ အလွတ် list `[]` ဖန်တီးပေးသည် —
`KeyError` မဖြစ်ပါ။

```python
from collections import defaultdict

normal = {}
try:
    normal["x"].append(1)
except KeyError as exc:
    print("KeyError:", exc)

auto = defaultdict(list)
auto["x"].append(1)
print(dict(auto))
```

Output —

```text
KeyError: 'x'
{'x': [1]}
```

### 7.2 `neighbors()` — Undirected Neighbor

Directed edge ကို **undirected** အဖြစ် ဖြန့်ကြည့်သည်။

- `{obj for _, obj in self.out[node]}` — node က subject ဖြစ်သော edge များ၏ object
- `found |= {subject for _, subject in self.inn[node]}` — node က object ဖြစ်သော edge များ၏ subject
- `|=` က set union

`Payments Squad` အတွက် — `Alice` (manages)၊ `Carol` (leads) နှစ်ခုလုံး ရသည်။

```python
out = {"Payments Squad": [("BUILDS", "Ledger Service")]}
inn = {"Payments Squad": [("MANAGES", "Alice")]}
found = {obj for _, obj in out["Payments Squad"]}
found |= {subject for _, subject in inn["Payments Squad"]}
print(sorted(found))
```

Output —

```text
['Alice', 'Ledger Service']
```

---

## 8. `build_knowledge_graph()` — Stage များ ချိတ်ခြင်း

```python
import re
from collections import OrderedDict, defaultdict

CORPUS_SENTENCES = [
    "Alice manages the Payments squad.",
    "Payments squad builds the Ledger service.",
    "Bob supports the Ledger service.",
    "Ledger service stores data in the Audit Store.",
    "Carol leads the Payments team.",
]
RELATION_PATTERNS = [
    ("MANAGES", re.compile(r"\bmanages\b")),
    ("BUILDS", re.compile(r"\bbuilds\b")),
    ("SUPPORTS", re.compile(r"\bsupports\b")),
    ("LEADS", re.compile(r"\bleads\b")),
    ("STORES_DATA_IN", re.compile(r"\bstores data in\b")),
]
ENTITY_CANONICAL = {
    "alice": "Alice", "bob": "Bob", "carol": "Carol", "dave": "Dave",
    "payments squad": "Payments Squad", "ledger service": "Ledger Service",
    "audit store": "Audit Store",
}
ENTITY_ALIASES = {"payments team": "payments squad"}


def clean_surface(text):
    surface = re.sub(r"^(the|a|an)\s+", "", text.strip(), flags=re.IGNORECASE)
    return surface.strip(" .,;:")


def resolve_entity(surface):
    key = re.sub(r"\s+", " ", clean_surface(surface).lower())
    key = ENTITY_ALIASES.get(key, key)
    return ENTITY_CANONICAL.get(key, clean_surface(surface))


def chunk_sentences(sentences, max_chars, overlap):
    chunks = []
    index = 0
    while index < len(sentences):
        current, size, cursor = [], 0, index
        while cursor < len(sentences):
            sentence = sentences[cursor]
            addition = len(sentence) + (1 if current else 0)
            if current and size + addition > max_chars:
                break
            current.append(sentence)
            size += addition
            cursor += 1
        chunks.append(current)
        if cursor >= len(sentences):
            break
        index = max(index + 1, cursor - overlap)
    return chunks


def extract_chunk_triples(chunk, chunk_id):
    records = []
    for sentence in chunk:
        for relation, pattern in RELATION_PATTERNS:
            match = pattern.search(sentence)
            if not match:
                continue
            subject = clean_surface(sentence[:match.start()])
            obj = clean_surface(sentence[match.end():])
            if not subject or not obj:
                continue
            records.append((chunk_id, resolve_entity(subject), relation, resolve_entity(obj)))
    return records


def dedupe_triples(records):
    merged = OrderedDict()
    for chunk_id, subject, relation, obj in records:
        key = (subject, relation, obj)
        if key not in merged:
            merged[key] = {"subject": subject, "relation": relation, "object": obj, "chunks": [chunk_id]}
        elif chunk_id not in merged[key]["chunks"]:
            merged[key]["chunks"].append(chunk_id)
    return list(merged.values())


class Graph:
    def __init__(self):
        self.nodes = set()
        self.out = defaultdict(list)
        self.inn = defaultdict(list)

    def add_triple(self, subject, relation, obj):
        self.nodes.add(subject)
        self.nodes.add(obj)
        if (relation, obj) not in self.out[subject]:
            self.out[subject].append((relation, obj))
        if (relation, subject) not in self.inn[obj]:
            self.inn[obj].append((relation, subject))

    def edges(self):
        return sorted((s, r, o) for s in self.out for (r, o) in self.out[s])

    def neighbors(self, node):
        found = {obj for _, obj in self.out[node]}
        found |= {subject for _, subject in self.inn[node]}
        return found


def build_knowledge_graph(max_chars=90, overlap=1):
    chunks = chunk_sentences(CORPUS_SENTENCES, max_chars, overlap)
    raw = []
    for chunk_id, chunk in enumerate(chunks):
        raw.extend(extract_chunk_triples(chunk, chunk_id))
    triples = dedupe_triples(raw)
    graph = Graph()
    for triple in triples:
        graph.add_triple(triple["subject"], triple["relation"], triple["object"])
    return graph


graph = build_knowledge_graph()
chunks = chunk_sentences(CORPUS_SENTENCES, 90, 1)
raw = []
for chunk_id, chunk in enumerate(chunks):
    raw.extend(extract_chunk_triples(chunk, chunk_id))
print("raw =", len(raw), "after dedup =", len(dedupe_triples(raw)))
print("nodes =", len(graph.nodes))
print("edges =", len(graph.edges()))
print(graph.edges())
```

Output —

```text
raw = 8 after dedup = 5
nodes = 6
edges = 5
[('Alice', 'MANAGES', 'Payments Squad'), ('Bob', 'SUPPORTS', 'Ledger Service'), ('Carol', 'LEADS', 'Payments Squad'), ('Ledger Service', 'STORES_DATA_IN', 'Audit Store'), ('Payments Squad', 'BUILDS', 'Ledger Service')]
```

`build_knowledge_graph()` က stage ငါးခုကို တစ်လိုင်းစီ ချိတ်သည် — chunk → extract →
dedupe → add_triple။ Graph တွင် **node ၆ ခု၊ edge ၅ ခု** ရသည်။ `raw.extend(...)`
က list ထဲ list ကို ဖြန့်ထည့်သည်။

```python
raw = []
raw.extend([1, 2])
raw.extend([3])
print(raw)
```

Output —

```text
[1, 2, 3]
```

---

## 9. `entity_link()` — Question မှ Anchor

```python
from collections import defaultdict


def entity_link(graph, question):
    lowered = question.lower()
    anchors = []
    for node in sorted(graph.nodes):
        surfaces = [node.lower()] + ALIASES_BY_NODE.get(node, [])
        if any(surface in lowered for surface in surfaces):
            anchors.append(node)
    return anchors


class MiniGraph:
    def __init__(self):
        self.nodes = {"Alice", "Carol", "Payments Squad", "Ledger Service"}


ALIASES_BY_NODE = defaultdict(list)
ALIASES_BY_NODE["Payments Squad"].append("payments team")

graph = MiniGraph()
print(entity_link(graph, "Who leads the Payments Squad?"))
print(entity_link(graph, "who leads the payments team?"))
```

Output —

```text
['Payments Squad']
['Payments Squad']
```

`sorted(graph.nodes)` က node များကို အစီအစဉ်တကျ စစ်သည် — ထိုမှသာ anchor အစီအစဉ်
deterministic ဖြစ်သည်။ Surface တိုင်းအတွက် `node.lower()` နှင့် alias များကို စုပြီး
`any(surface in lowered for surface in surfaces)` ဖြင့် question ထဲ ရှိ/မရှိ စစ်သည်။

`any(...)` က item တစ်ခုခု `True` ဖြစ်လျှင် `True` ပြန်သည် (မဟုတ်လျှင် `False`)။
Alias ရှိသောကြောင့် `"payments team"` ပါသော question ကလည်း `Payments Squad` ကို ရသည် —
၎င်းသည် `Payments team` နှင့် `Payments squad` ကို graph တွင် node တစ်ခုတည်း ဖြစ်စေသည်။

---

## 10. `k_hop_subgraph()` — Bounded Retrieval

```python
from collections import defaultdict


class Graph:
    def __init__(self):
        self.nodes = set()
        self.out = defaultdict(list)
        self.inn = defaultdict(list)

    def add_triple(self, subject, relation, obj):
        self.nodes.add(subject)
        self.nodes.add(obj)
        if (relation, obj) not in self.out[subject]:
            self.out[subject].append((relation, obj))
        if (relation, subject) not in self.inn[obj]:
            self.inn[obj].append((relation, subject))

    def edges(self):
        return sorted((s, r, o) for s in self.out for (r, o) in self.out[s])

    def neighbors(self, node):
        found = {obj for _, obj in self.out[node]}
        found |= {subject for _, subject in self.inn[node]}
        return found


def k_hop_subgraph(graph, anchors, hops):
    visited = set(anchors)
    frontier = set(anchors)
    for _ in range(hops):
        nxt = set()
        for node in frontier:
            nxt |= graph.neighbors(node)
        nxt -= visited
        visited |= nxt
        frontier = nxt
    edges = [edge for edge in graph.edges() if edge[0] in visited and edge[2] in visited]
    return visited, edges


graph = Graph()
graph.add_triple("Alice", "MANAGES", "Payments Squad")
graph.add_triple("Carol", "LEADS", "Payments Squad")
graph.add_triple("Payments Squad", "BUILDS", "Ledger Service")
graph.add_triple("Ledger Service", "STORES_DATA_IN", "Audit Store")

nodes, edges = k_hop_subgraph(graph, ["Payments Squad"], hops=1)
print(sorted(nodes))
print(len(edges))
print(edges)
```

Output —

```text
['Alice', 'Carol', 'Ledger Service', 'Payments Squad']
3
[('Alice', 'MANAGES', 'Payments Squad'), ('Carol', 'LEADS', 'Payments Squad'), ('Payments Squad', 'BUILDS', 'Ledger Service')]
```

`hops=1` ဖြစ်သောကြောင့် anchor `Payments Squad` ၏ တိုက်ရိုက် neighbor များသာ ဝင်သည် —
`Alice`၊ `Carol`၊ `Ledger Service`။ `Audit Store` က 2-hop ဖြစ်သောကြောင့် **မပါ** ပါ။

- `visited` — သွားပြီးသား node စုစုပေါင်း
- `frontier` — လက်ရှိ hop ၏ ဝင်ရောက်နေသော node များ
- `nxt -= visited` က ပြန်လာသော node များကို ဖယ်သည် (၎င်းသည် loop ကို တားဆီးသည်)

```python
visited = {"A"}
nxt = {"B", "C", "A"}
nxt -= visited
print(sorted(nxt))
visited |= nxt
print(sorted(visited))
```

Output —

```text
['B', 'C']
['A', 'B', 'C']
```

> set တစ်ခုကို `print(nxt)` ဖြင့် တိုက်ရိုက် ပြလျှင် အစီအစဉ်က run တစ်ခုနှင့်တစ်ခု ကွဲနိုင်သည်
> (ဥပမာ `{'B', 'C'}` သို့မဟုတ် `{'C', 'B'}`)။ ထို့ကြောင့် output ကို `sorted(...)` ဖြင့်
> ပြသသည်။

### `hops=2` ဖြစ်လျှင်

```python
from collections import defaultdict


class Graph:
    def __init__(self):
        self.nodes = set()
        self.out = defaultdict(list)
        self.inn = defaultdict(list)

    def add_triple(self, subject, relation, obj):
        self.nodes.add(subject)
        self.nodes.add(obj)
        if (relation, obj) not in self.out[subject]:
            self.out[subject].append((relation, obj))
        if (relation, subject) not in self.inn[obj]:
            self.inn[obj].append((relation, subject))

    def edges(self):
        return sorted((s, r, o) for s in self.out for (r, o) in self.out[s])

    def neighbors(self, node):
        found = {obj for _, obj in self.out[node]}
        found |= {subject for _, subject in self.inn[node]}
        return found


def k_hop_subgraph(graph, anchors, hops):
    visited = set(anchors)
    frontier = set(anchors)
    for _ in range(hops):
        nxt = set()
        for node in frontier:
            nxt |= graph.neighbors(node)
        nxt -= visited
        visited |= nxt
        frontier = nxt
    edges = [edge for edge in graph.edges() if edge[0] in visited and edge[2] in visited]
    return visited, edges


graph = Graph()
graph.add_triple("Carol", "LEADS", "Payments Squad")
graph.add_triple("Payments Squad", "BUILDS", "Ledger Service")
graph.add_triple("Ledger Service", "STORES_DATA_IN", "Audit Store")

nodes2, edges2 = k_hop_subgraph(graph, ["Payments Squad"], hops=2)
print(sorted(nodes2))
print(len(edges2))
```

Output —

```text
['Audit Store', 'Carol', 'Ledger Service', 'Payments Squad']
3
```

`hops=2` ဖြစ်လျှင် `Audit Store` ပါ ဝင်လာပြီး edge သုံးခု ဖြစ်သည်။ `hops` တန်ဖိုး
တိုးလိုက်ခြင်းက context ကို ကြီးထွားစေသည် — ထို့ကြောင့် hop bound ကို
token budget အလိုက် သတ်မှတ်ရသည်။

---

## 11. `serialize_context()` — Prompt Context

```python
def serialize_context(edges):
    lines = [f"{s} --{r}--> {o}" for (s, r, o) in sorted(edges)]
    return "Knowledge Graph triples:\n" + "\n".join(lines)


edges = [
    ("Alice", "MANAGES", "Payments Squad"),
    ("Carol", "LEADS", "Payments Squad"),
    ("Payments Squad", "BUILDS", "Ledger Service"),
]
context = serialize_context(edges)
print(context)
print(context.splitlines())
```

Output —

```text
Knowledge Graph triples:
Alice --MANAGES--> Payments Squad
Carol --LEADS--> Payments Squad
Payments Squad --BUILDS--> Ledger Service
['Knowledge Graph triples:', 'Alice --MANAGES--> Payments Squad', 'Carol --LEADS--> Payments Squad', 'Payments Squad --BUILDS--> Ledger Service']
```

List comprehension က edge တိုင်းကို `f"{s} --{r}--> {o}"` ဖြင့် string line အဖြစ်
ပြောင်းသည်။ `"\n".join(lines)` က line များကို newline ဖြင့် ဆက်သည်။ `\n` က
string literal ထဲတွင် **newline character** ဖြစ်သည်။

`context.splitlines()` က string ကို newline အလိုက် ခွဲပြီး list ပြန်သည် (newline
မပါ)။ ၎င်းသည် prompt context ကို retrieve မှုတိုင်း တိကျစွာ ပြန်စစ်ရန် သုံးသည်။

---

## 12. `generate_answer()` — Rule-based Generator

```python
import re

RELATION_KEYWORDS = [
    ("leads", "LEADS"),
    ("manages", "MANAGES"),
    ("builds", "BUILDS"),
    ("supports", "SUPPORTS"),
    ("stores", "STORES_DATA_IN"),
]


def generate_answer(question, edges, anchors):
    words = [re.sub(r"[^a-z]", "", token) for token in question.lower().split()]
    targets = []
    for keyword, relation in RELATION_KEYWORDS:
        if keyword in words:
            targets.append(relation)
    for relation in targets:
        for subject, edge_relation, obj in sorted(edges):
            if edge_relation == relation and obj in anchors:
                return subject
    return "Unknown"


edges = [
    ("Alice", "MANAGES", "Payments Squad"),
    ("Carol", "LEADS", "Payments Squad"),
    ("Payments Squad", "BUILDS", "Ledger Service"),
]
print(generate_answer("Who leads the Payments Squad?", edges, ["Payments Squad"]))
print(generate_answer("Who builds the Ledger service?", edges, ["Ledger Service"]))
print(generate_answer("Who owns the Audit Store?", edges, ["Payments Squad"]))
```

Output —

```text
Carol
Payments Squad
Unknown
```

`[re.sub(r"[^a-z]", "", token) for token in question.lower().split()]` က question ကို
စကားလုံးများအဖြစ် ခွဲပြီး (split)၊ စာလုံးမဟုတ်သည့် character များ (`?`, space) ဖယ်သည်။
`[^a-z]` က \"`a-z` မဟုတ်သော\" ဆိုလိုသည်။

`if keyword in words:` က `words` list ထဲ keyword ရှိ/မရှိ စစ်ဆေးခြင်း ဖြစ်သည်။ ရှိလျှင် သက်ဆိုင်ရာ
relation ကို `targets` ထဲ ထည့်သည်။ ပြီးလျှင် target relation တိုင်းအတွက် edge များကို
စစ်ပြီး object က anchor ဖြစ်လျှင် **subject** ကို အဖြေအဖြစ် ပြန်သည်။

တတိယလိုင်းက သက်ဆိုင်သော edge မတွေ့သောကြောင့် `"Unknown"` ပြန်သည် — unknown အခြေအနေကို
generator က လုံခြုံစွာ ကိုင်တွယ်သည်။

---

## 13. Code တစ်ခုလုံး — Run လုပ်နိုင်သော Version

```python
import re
from collections import OrderedDict, defaultdict

CORPUS_SENTENCES = [
    "Alice manages the Payments squad.",
    "Payments squad builds the Ledger service.",
    "Bob supports the Ledger service.",
    "Ledger service stores data in the Audit Store.",
    "Carol leads the Payments team.",
]

RELATION_PATTERNS = [
    ("MANAGES", re.compile(r"\bmanages\b")),
    ("BUILDS", re.compile(r"\bbuilds\b")),
    ("SUPPORTS", re.compile(r"\bsupports\b")),
    ("LEADS", re.compile(r"\bleads\b")),
    ("STORES_DATA_IN", re.compile(r"\bstores data in\b")),
]

ENTITY_CANONICAL = {
    "alice": "Alice", "bob": "Bob", "carol": "Carol", "dave": "Dave",
    "payments squad": "Payments Squad", "ledger service": "Ledger Service",
    "audit store": "Audit Store",
}
ENTITY_ALIASES = {"payments team": "payments squad"}

RELATION_KEYWORDS = [
    ("leads", "LEADS"), ("manages", "MANAGES"), ("builds", "BUILDS"),
    ("supports", "SUPPORTS"), ("stores", "STORES_DATA_IN"),
]

ALIASES_BY_NODE = defaultdict(list)
for _alias, _canonical_key in ENTITY_ALIASES.items():
    ALIASES_BY_NODE[ENTITY_CANONICAL[_canonical_key]].append(_alias)


def clean_surface(text):
    surface = re.sub(r"^(the|a|an)\s+", "", text.strip(), flags=re.IGNORECASE)
    return surface.strip(" .,;:")


def resolve_entity(surface):
    key = re.sub(r"\s+", " ", clean_surface(surface).lower())
    key = ENTITY_ALIASES.get(key, key)
    return ENTITY_CANONICAL.get(key, clean_surface(surface))


def chunk_sentences(sentences, max_chars, overlap):
    chunks = []
    index = 0
    while index < len(sentences):
        current, size, cursor = [], 0, index
        while cursor < len(sentences):
            sentence = sentences[cursor]
            addition = len(sentence) + (1 if current else 0)
            if current and size + addition > max_chars:
                break
            current.append(sentence)
            size += addition
            cursor += 1
        chunks.append(current)
        if cursor >= len(sentences):
            break
        index = max(index + 1, cursor - overlap)
    return chunks


def extract_chunk_triples(chunk, chunk_id):
    records = []
    for sentence in chunk:
        for relation, pattern in RELATION_PATTERNS:
            match = pattern.search(sentence)
            if not match:
                continue
            subject = clean_surface(sentence[:match.start()])
            obj = clean_surface(sentence[match.end():])
            if not subject or not obj:
                continue
            records.append((chunk_id, resolve_entity(subject), relation, resolve_entity(obj)))
    return records


def dedupe_triples(records):
    merged = OrderedDict()
    for chunk_id, subject, relation, obj in records:
        key = (subject, relation, obj)
        if key not in merged:
            merged[key] = {"subject": subject, "relation": relation, "object": obj, "chunks": [chunk_id]}
        elif chunk_id not in merged[key]["chunks"]:
            merged[key]["chunks"].append(chunk_id)
    return list(merged.values())


class Graph:
    def __init__(self):
        self.nodes = set()
        self.out = defaultdict(list)
        self.inn = defaultdict(list)

    def add_triple(self, subject, relation, obj):
        self.nodes.add(subject)
        self.nodes.add(obj)
        if (relation, obj) not in self.out[subject]:
            self.out[subject].append((relation, obj))
        if (relation, subject) not in self.inn[obj]:
            self.inn[obj].append((relation, subject))

    def edges(self):
        return sorted((s, r, o) for s in self.out for (r, o) in self.out[s])

    def neighbors(self, node):
        found = {obj for _, obj in self.out[node]}
        found |= {subject for _, subject in self.inn[node]}
        return found


def build_knowledge_graph(max_chars=90, overlap=1):
    chunks = chunk_sentences(CORPUS_SENTENCES, max_chars, overlap)
    raw = []
    for chunk_id, chunk in enumerate(chunks):
        raw.extend(extract_chunk_triples(chunk, chunk_id))
    triples = dedupe_triples(raw)
    graph = Graph()
    for triple in triples:
        graph.add_triple(triple["subject"], triple["relation"], triple["object"])
    return graph


def k_hop_subgraph(graph, anchors, hops):
    visited = set(anchors)
    frontier = set(anchors)
    for _ in range(hops):
        nxt = set()
        for node in frontier:
            nxt |= graph.neighbors(node)
        nxt -= visited
        visited |= nxt
        frontier = nxt
    edges = [edge for edge in graph.edges() if edge[0] in visited and edge[2] in visited]
    return visited, edges


def entity_link(graph, question):
    lowered = question.lower()
    anchors = []
    for node in sorted(graph.nodes):
        surfaces = [node.lower()] + ALIASES_BY_NODE.get(node, [])
        if any(surface in lowered for surface in surfaces):
            anchors.append(node)
    return anchors


def serialize_context(edges):
    lines = [f"{s} --{r}--> {o}" for (s, r, o) in sorted(edges)]
    return "Knowledge Graph triples:\n" + "\n".join(lines)


def generate_answer(question, edges, anchors):
    words = [re.sub(r"[^a-z]", "", token) for token in question.lower().split()]
    targets = []
    for keyword, relation in RELATION_KEYWORDS:
        if keyword in words:
            targets.append(relation)
    for relation in targets:
        for subject, edge_relation, obj in sorted(edges):
            if edge_relation == relation and obj in anchors:
                return subject
    return "Unknown"


print("--- mini GraphRAG pipeline ---")
chunks = chunk_sentences(CORPUS_SENTENCES, max_chars=90, overlap=1)
print(f"corpus sentences={len(CORPUS_SENTENCES)} -> chunks={len(chunks)} (overlap=1 sentence)")
for chunk_id, chunk in enumerate(chunks):
    print(f"  chunk {chunk_id}: {len(chunk)} sentences")

raw = []
for chunk_id, chunk in enumerate(chunks):
    raw.extend(extract_chunk_triples(chunk, chunk_id))
triples = dedupe_triples(raw)
print(f"extracted triples: raw={len(raw)} after dedup={len(triples)}")

graph = build_knowledge_graph()
print(f"in-memory graph: nodes={len(graph.nodes)} edges={len(graph.edges())}")

question = "Who leads the Payments Squad?"
anchors = entity_link(graph, question)
nodes, edges = k_hop_subgraph(graph, anchors, hops=1)
print(f"question: {question}")
print(f"  entity linking -> anchors={anchors}")
print(f"  1-hop subgraph -> nodes={sorted(nodes)}")
print(f"  retained edges = {len(edges)}, hops bound excluded Audit Store")
context = serialize_context(edges)
print("  serialized prompt context:")
for line in context.splitlines():
    print(f"    {line}")
answer = generate_answer(question, edges, anchors)
print(f"  generator answer -> {answer}")

question2 = "Who builds the Ledger service?"
anchors2 = entity_link(graph, question2)
nodes2, edges2 = k_hop_subgraph(graph, anchors2, hops=1)
answer2 = generate_answer(question2, edges2, anchors2)
print(f"question: {question2} -> anchors={anchors2} answer={answer2}")
print("full pipeline ingest -> retrieve -> serialize -> generate: OK")
```

Output —

```text
--- mini GraphRAG pipeline ---
corpus sentences=5 -> chunks=4 (overlap=1 sentence)
  chunk 0: 2 sentences
  chunk 1: 2 sentences
  chunk 2: 2 sentences
  chunk 3: 2 sentences
extracted triples: raw=8 after dedup=5
in-memory graph: nodes=6 edges=5
question: Who leads the Payments Squad?
  entity linking -> anchors=['Payments Squad']
  1-hop subgraph -> nodes=['Alice', 'Carol', 'Ledger Service', 'Payments Squad']
  retained edges = 3, hops bound excluded Audit Store
  serialized prompt context:
    Knowledge Graph triples:
    Alice --MANAGES--> Payments Squad
    Carol --LEADS--> Payments Squad
    Payments Squad --BUILDS--> Ledger Service
  generator answer -> Carol
question: Who builds the Ledger service? -> anchors=['Ledger Service'] answer=Payments Squad
full pipeline ingest -> retrieve -> serialize -> generate: OK
```

---

## 14. Stage တိုင်း၏ ရလဒ်

| Stage | Input | Output | မှတ်ချက် |
| --- | --- | --- | --- |
| chunk_sentences | sentence ၅ ခု | chunk ၄ ခု | overlap ၁ sentence |
| extract_chunk_triples | chunk ၄ ခု | raw triple ၈ ခု | overlap ကြောင့် ထပ် |
| dedupe_triples | raw ၈ ခု | triple ၅ ခု | provenance ပေါင်း |
| Graph | triple ၅ ခု | node ၆၊ edge ၅ | entity resolution ဖြင့် ချိတ် |
| entity_link | question | anchor | alias ဖြင့် လည်း ချိတ် |
| k_hop_subgraph | anchor, hops=1 | node ၄၊ edge ၃ | Audit Store ဖယ် |
| generate_answer | edges, anchor | Carol | rule-based |

| Question | anchors | nodes | edges | answer |
| --- | --- | --- | --- | --- |
| Who leads the Payments Squad? | `['Payments Squad']` | `4` | `3` | `Carol` |
| Who builds the Ledger service? | `['Ledger Service']` | — | — | `Payments Squad` |

`Audit Store` သည် hop ကန့်သတ်ချက်ကြောင့် context မှ ထွက်သွားသည် — ဤသို့ hop bound
ကို တိတိကျကျ သတ်မှတ်ခြင်းဖြင့် context token၊ Cost နှင့် latency ကို ထိန်းနိုင်သည်။
Entity resolution မရှိပါက graph တွင် `Payments Squad` နှင့် `Payments team` node
နှစ်ခု ကွဲနေပြီး \"ဘယ်သူက Payments squad ကို leads\" ဆိုသည့် question ကို ဖြေနိုင်တော့မည်
မဟုတ်ပါ။

---

## 15. ကိုယ်တိုင်လေ့ကျင့်ကြည့်ပါ

**မေးခွန်း** — အောက်ပါ code က ဘယ်ရလဒ် ပြန်ပေးမလဲ။

```python
def clean_surface(text):
    return text.strip(" .,;:")


def resolve_entity(surface, canonical, aliases):
    key = surface.strip(" .,;:").lower()
    key = aliases.get(key, key)
    return canonical.get(key, surface.strip(" .,;:"))


canonical = {"payments squad": "Payments Squad"}
aliases = {"payments team": "payments squad"}
print(repr(resolve_entity("Payments team.", canonical, aliases)))
print(repr(resolve_entity("Unknown Corp.", canonical, aliases)))
```

1. `'Payments Squad'` နှင့် `'Unknown Corp'`
2. `'Payments team'` နှင့် `'Unknown Corp'`
3. `'Payments Squad'` နှင့် `'Unknown Corp.'`
4. `'Payments Team'` နှင့် `'Unknown'`

<details>
<summary>အဖြေ ကြည့်ရန်</summary>

**အဖြေ — 1. `'Payments Squad'` နှင့် `'Unknown Corp'`**

အကြောင်းရင်း — ပထမ — `"Payments team."` ကို `strip(" .,;:")` လိုက်လျှင် `"Payments team"`။
`.lower()` လိုက်လျှင် `"payments team"`။ `aliases.get("payments team", ...)` က
`"payments squad"` ပြန်သည်။ ထို key အတွက် `canonical.get(...)` က `"Payments Squad"` ပြန်သည်။

ဒုတိယ — `"Unknown Corp."` ကို strip လိုက်လျှင် `"Unknown Corp"`။ lower = `"unknown corp"`။
Alias တွင်မရှိ၊ canonical တွင်လည်းမရှိသဖြင့် fallback ဖြစ်သည့်
`surface.strip(" .,;:")` = `"Unknown Corp"` ကို ပြန်သည်။ fallback တွင်
**မူရင်း case ထိန်း** ထားပြီး trailing `.` ဖယ်ထားသည်ကို သတိထားပါ။

</details>

---

**အဓိက မှတ်ထားရန်** — Pipeline တစ်ခုလုံး၏ correctness (chunk → graph → retrieval →
answer) ကို LLM မလိုဘဲ test လုပ်နိုင်သည်။ Overlap က triple များကို ထပ်ထွက်စေသော်လည်း
dedupe က provenance ပါ ထိန်းပြီး ပေါင်းသည်။ Entity resolution မရှိလျှင် graph ကွဲပြီး
multi-hop question ဖြေနိုင်တော့မည် မဟုတ်ပါ။ hop bound ကို တိတိကျကျ သတ်မှတ်ခြင်းဖြင့်
context token ကို ထိန်းသည်။ Lab ဤခုသည် M08 ၏ exercise ခြောက်ခုလုံးကို
`[PASS] All 6/6 exercises passed successfully.` ဖြင့် ပိတ်သည်။
