# Walkthrough 05 — Hallucination Filter / Grounding Check (Exercise 5)

> ဤဖိုင်သည် Module 02 ၏ `solution.md` ထဲက Exercise 5 ကို **Python အခြေခံမှ စ၍**
> အပိုင်းလိုက် ရှင်းပြသည့် walkthrough ဖြစ်သည်။

---

## 0. ဤ Exercise က ဘာကို ဖြေရှင်းပေးသလဲ။

LLM သည် schema မှန်ကန်သော payload တစ်ခုကို ပြန်ပေးနိုင်သော်လည်း
**source text ထဲတွင် မပါသော** entity တစ်ခုကို ထည့်လာနိုင်သည်။

```text
Source text
  "Neo4j Inc. is a graph database company. Neo4j Inc. was founded by Emil Eifrem. ..."
        │
        ▼
Model ပြန်ပေးသော payload
  entities: Neo4j Inc., Emil Eifrem, Sweden, AthenaDB     ← "AthenaDB" သည် source တွင် မရှိ
  relationships: (Neo4j Inc.)-[:PRODUCES]->(AthenaDB)     ← ၎င်းအပေါ် တည်ဆောက်ထားသည်
```

ဤကဲ့သို့ အရာကို **hallucination** ဟု ခေါ်သည်။ `AthenaDB` ကို graph ထဲ ထည့်လျှင်
မရှိသော entity တစ်ခုနှင့် မှားယွင်းသော relationship တစ်ခု ဝင်လာသည်။

ဤ Exercise က **gate နှစ်ခု** ဖြင့် စစ်ထုတ်သည်။

```text
Gate 1 — Entity grounding
  entity တိုင်း၏ surface form သည် normalized corpus ထဲ ပါသလား?
        │
        ▼ grounded_names (set)
Gate 2 — Relationship grounding
  (က) type သည် allowed list ထဲ ပါသလား?
  (ခ) endpoint နှစ်ခုလုံး Gate 1 ကို ဖြတ်ခဲ့သလား?
```

မဖြတ်သည့် အရာတိုင်းကို **drop** ပြီး အကြောင်းရင်းကို မှတ်တမ်းတင်သည်။

ဤ code မှာ လေ့လာရမည့် Python concepts များမှာ —

- `" ".join(dict.values())` — dict ၏ တန်ဖိုးများကို ဆက်ခြင်း
- `set` နှင့် `set.add()`, `in`
- Substring attestation — `key in corpus`
- Truthiness — `if key and key in corpus:`
- `list.append()` နှင့် parallel list နှစ်ခု (kept/dropped) ထိန်းခြင်း
- `if` / `elif` / `else` ၏ အစဉ်လိုက် ဆုံးဖြတ်ခြင်း
- Tuple ထဲ tuple — `(rel, "reason")` နှင့် nested indexing
- List comprehension အတွင်း dict access (`e['name']`)
- Float division နှင့် `:.2f` formatting

---

## 1. `build_grounding_corpus()` — Corpus ကို တစ်ခုတည်း စာသားအဖြစ်

```python
def build_grounding_corpus(chunks):
    return normalize_surface(" ".join(chunks.values()))
```

`chunks` သည် `chunk_id → text` ဖြစ်သည့် dict ဖြစ်သည်။ `chunks.values()` က
စာသားများကို ပေးသည်; `" ".join(...)` က space ဖြင့် ဆက်သည်။ ထို့နောက်
`normalize_surface()` (Exercise 4) ဖြင့် တူညီပုံစံ ဖြစ်စေသည်။

```python
SOURCE_CHUNKS = {
    "chunk-001": "Neo4j Inc. was founded by Emil Eifrem.",
    "chunk-002": "Emil Eifrem works for Neo4j Inc.",
}
print(list(SOURCE_CHUNKS.values()))
print(" ".join(SOURCE_CHUNKS.values()))
print("key များ:", list(SOURCE_CHUNKS))
```

Output —

```text
['Neo4j Inc. was founded by Emil Eifrem.', 'Emil Eifrem works for Neo4j Inc.']
Neo4j Inc. was founded by Emil Eifrem. Emil Eifrem works for Neo4j Inc.
key များ: ['chunk-001', 'chunk-002']
```

`dict.values()` နှင့် `dict.keys()` (`list(dict)` နှင့် တူညီ) တို့သည်
insertion order အတိုင်း ပြန်သည် — ထို့ကြောင့် ရလဒ်သည် deterministic ဖြစ်သည်။

### 1.1 Normalize ပြီးနောက်

```python
SOURCE_CHUNKS = {
    "chunk-001": "Neo4j Inc. was founded by Emil Eifrem.",
    "chunk-002": "Emil Eifrem works for Neo4j Inc.",
}
print(build_grounding_corpus(SOURCE_CHUNKS))
```

Output —

```text
neo4j inc was founded by emil eifrem emil eifrem works for neo4j inc
```

Punctuation (`.`) ဖြတ်ခံရပြီး စာလုံးအားလုံး စာလုံးအသေး ဖြစ်သည်။ Corpus သည်
**စာသားတစ်ခုတည်း** ဖြစ်သဖြင့် `in` ဖြင့် substring စစ်နိုင်သည်။

> **သတိပေးချက်** — ဤနည်းသည် **substring attestation** ဖြစ်သည် — "ဤစာလုံးစု
> သည် corpus ထဲ တစ်နေရာရာတွင် ပါသလား" ကို စစ်သည်။ စာလုံးအပိုင်းအစ ဖြစ်နိုင်သည်။
> ဤကန့်သတ်ချက်ကို Section 2.2 တွင် run စစ်ပြထားသည်။

---

## 2. `ground_extraction()` — Gate 1 (Entity Grounding)

```python
def ground_extraction(payload, corpus, relationship_types):
    kept_entities, dropped_entities = [], []
    grounded_names = set()
    for entity in payload["entities"]:
        key = normalize_surface(entity["name"])
        if key and key in corpus:
            kept_entities.append(entity)
            grounded_names.add(key)
        else:
            dropped_entities.append(entity["name"])
```

### 2.1 `key and key in corpus` — Truthiness Short-circuit

⚠️ **ဤတွင် ဆုံးဖြတ်ချက်နှစ်ခု** ပါသည်။

- `key` — normalized အမည်သည် **မဟာကွက်လပ် မဟုတ်ကြောင်း** စစ်သည်။
- `key in corpus` — corpus ထဲ **ပါကြောင်း** စစ်သည်။

`print(repr(normalize_surface("!!!")))` က `''` ပြန်သည်ကို Exercise 4 တွင်
တွေ့ခဲ့သည်။ ထို empty string ကို မစစ်ဘဲ ထားလျှင် ဘာဖြစ်လဲ စမ်းကြည့်ပါ။

```python
corpus = "neo4j inc is a graph database company"
print("'' in corpus :", "" in corpus)
print("bool('')     :", bool(""))
```

Output —

```text
'' in corpus : True
bool('')     : False
```

**အရေးကြီးသည့် တွေ့ရှိချက်** — **empty string သည် မည်သည့် string ထဲမဆို
ပါဝင်သည်** — `"" in corpus` က `True` ပြန်သည်။ ထို့ကြောင့် `key and` guard
မပါလျှင် အမည် လုံးဝ မရှိသည့် entity (ဥပမာ `"!!!"`) သည် **grounded** အဖြစ်
ဖြတ်သွားမည်။ `key and` က ၎င်းကို တားသည်။

**သတိပြုရန်** — `key and key in corpus` တွင် `and` သည် **short-circuit** ဖြစ်သည် —
`key` falsy ဖြစ်လျှင် `key in corpus` ကို မစစ်တော့ပါ။ ဤနေရာတွင် ၎င်းသည်
performance အကျိုးမရှိသော်လည်း guard ၏ ရည်ရွယ်ချက်ကို ရှင်းစေသည်။

### 2.2 Substring Attestation ၏ ကန့်သတ်ချက်

`key in corpus` သည် substring စစ်ခြင်းဖြစ်သဖြင့် **တိုသော အမည်များ**
မှားယွင်းစွာ ဖြတ်နိုင်သည်။ စစ်သည့်အခါ **normalize လုပ်ပြီးမှ** စစ်ရကြောင်း
သတိထားပါ — corpus သည် စာလုံးအသေးဖြစ်သဖြင့် စာလုံးကြီး probe သည်
တိုက်ရိုက် မကိုက်ညီပါ။

```python
corpus = build_grounding_corpus(SOURCE_CHUNKS)
for probe in ("Neo", "Eifrem", "Neo4j", "graph", "AthenaDB"):
    print("%-10s raw=%-6s normalized=%s"
          % (probe, probe in corpus, normalize_surface(probe) in corpus))
```

Output —

```text
Neo        raw=False  normalized=True
Eifrem     raw=False  normalized=True
Neo4j      raw=False  normalized=True
graph      raw=True   normalized=True
AthenaDB   raw=False  normalized=False
```

**တွေ့ရှိချက် နှစ်ခု** —

- `"Neo"`/`"Eifrem"`/`"Neo4j"` သည် raw အနေနှင့် `False` ဖြစ်သည် — corpus တွင်
  စာလုံးအသေးသာ ရှိသဖြင့် စာလုံးကြီးဖြင့် စစ်လျှင် မကိုက်ညီပါ။ `"graph"` သည်
  အသေးဖြစ်ပြီးသားသဖြင့် `True`။
- `normalize_surface(probe)` ဖြင့် စစ်လျှင် `"Neo"` (→ `"neo"`) နှင့်
  `"Eifrem"` (→ `"eifrem"`) သည် **`True`** ဖြစ်လာသည် — ၎င်းတို့သည် corpus ထဲ
  **အပိုင်းအစ အဖြစ်** ပါနေသဖြင့်ပါ။

`"Eifrem"` သည် `"Emil Eifrem"` ၏ အပိုင်းအစဖြစ်ပြီး `"Neo"` သည်
`"Neo4j Inc."` ၏ အပိုင်းအစဖြစ်သည် — မည်သည့် entity အမည်အဖြစ်မှ
တရားဝင် မဟုတ်ပါ။

> **မှတ်ထားရန်** — Substring gate သည် hallucination ကို **လျှော့ချ** ပေးသည်၊
> လုံးဝ မကာကွယ်ပါ။ Production တွင် **word-boundary** ဖြင့် စစ်ခြင်း (regex
> `\b` သို့မဟုတ် token list) သည် ပိုမှန်ကန်သည်။ ဤ Exercise ၏ ရည်ရွယ်ချက်မှာ
> gate ၏ **နေရာ** ကို ပြရန်ဖြစ်သည် — gate တစ်ခု ရှိခြင်းသည် ဖြေရှင်းချက်
> အပြည့်အစုံ မဟုတ်ပါ။

### 2.3 `set` နှင့် `add()`

```python
grounded = set()
grounded.add("neo4j inc")
grounded.add("emil eifrem")
grounded.add("neo4j inc")
print("size   :", len(grounded))
print("ပါမပါ  :", "neo4j inc" in grounded)
print("မပါသည့်အရာ:", "athenadb" in grounded)
```

Output —

```text
size   : 2
ပါမပါ  : True
မပါသည့်အရာ: False
```

`set` သည် **duplicate မထားပါ** — `"neo4j inc"` ကို နှစ်ကြိမ် `add` လုပ်သော်လည်း
size သည် 2 ဖြစ်သည်။ `<hash>` lookup ဖြစ်သဖြင့် `in` စစ်ခြင်း အလွန်မြန်သည်။
`grounded_names` ကို `list` အစား `set` ဖြင့် ထားရသည့် အကြောင်းရင်းမှာ
relationship တိုင်း စစ်ရာတွင် lookup အကြိမ်များစွာ လိုသဖြင့်ပါ။

> **သတိပေးချက်** — `set` ၏ **ပြသအစီအစဉ်** သည် hash-randomised ဖြစ်သဖြင့်
> run တစ်ခုနှင့်တစ်ခု ကွာနိုင်သည်။ ဤ code တွင် `grounded_names` ကို print
> မလုပ်သဖြင့် ပြဿနာ မရှိပါ။ `list` လုပ်ရင် `set(...)` ကို run တိုင်း
> အစဉ်တူရန် `sorted(...)` ကို ဖြတ်ရမည်။

### 2.4 `kept` / `dropped` — Parallel List နှစ်ခု

```python
payload_entities = [{"name": "Neo4j Inc."}, {"name": "AthenaDB"}]
corpus = build_grounding_corpus(SOURCE_CHUNKS)
kept, dropped = [], []
for entity in payload_entities:
    key = normalize_surface(entity["name"])
    if key and key in corpus:
        kept.append(entity)
    else:
        dropped.append(entity["name"])
print("kept   :", [e["name"] for e in kept])
print("dropped:", dropped)
```

Output —

```text
kept   : ['Neo4j Inc.']
dropped: ['AthenaDB']
```

`kept` သည် entity **dict** များကို သိမ်းပြီး `dropped` သည် **အမည် (string)**
များကို သိမ်းသည်ကို သတိထားပါ — drop လုပ်ရသည့် အကြောင်းရင်း ရှင်းစေရန်
အမည်သာ လုံလောက်သည်။

`[e["name"] for e in kept]` သည် list comprehension အတွင်း dict access ဖြစ်သည် —
dict တိုင်း၏ `"name"` key ကို ဆွဲထုတ်သည်။

---

## 3. `ground_extraction()` — Gate 2 (Relationship Grounding)

```python
    kept_relationships, dropped_relationships = [], []
    for rel in payload["relationships"]:
        source_key = normalize_surface(rel["source"])
        target_key = normalize_surface(rel["target"])
        if rel["type"] not in relationship_types:
            dropped_relationships.append((rel, "type_not_allowed"))
        elif source_key not in grounded_names or target_key not in grounded_names:
            dropped_relationships.append((rel, "endpoint_not_grounded"))
        else:
            kept_relationships.append(rel)
    return kept_entities, dropped_entities, kept_relationships, dropped_relationships
```

### 3.1 Gate ၏ အစဉ် — `if` → `elif` → `else`

Relationship တိုင်းကို အစဉ်လိုက် စစ်သည်။

| အစဉ် | စစ်ချက် | မဖြတ်လျှင် reason |
| --- | --- | --- |
| ၁ | `rel["type"]` သည် allowed list ထဲ ပါသလား | `type_not_allowed` |
| ၂ | endpoint နှစ်ခုလုံး grounded ဖြစ်သလား | `endpoint_not_grounded` |
| ၃ | (အားလုံး ဖြတ်) | — kept |

`elif` ဖြစ်သဖြင့် **ပထမ gate မဖြတ်လျှင် ဒုတိယကို မစစ်တော့ပါ**။ ထို့ကြောင့်
gate နှစ်ခုလုံး ကျရှုံးသည့် relationship တစ်ခုအတွက် reason တစ်ခုသာ
မှတ်တမ်းတင်ခံရသည်။

```python
corpus = build_grounding_corpus(SOURCE_CHUNKS)
tricky = {"entities": [{"name": "Neo4j Inc.", "type": "ORGANIZATION"}],
          "relationships": [{"source": "Neo4j Inc.", "target": "AthenaDB", "type": "KNOWS"}]}
_, _, kept_r, dropped_r = ground_extraction(tricky, corpus, RELATIONSHIP_TYPES)
print("kept   :", len(kept_r))
print("reason :", [r[1] for r in dropped_r])
```

Output —

```text
kept   : 0
reason : ['type_not_allowed']
```

Relationship သည် type (`KNOWS`) နှင့် endpoint (`AthenaDB`) **နှစ်ခုလုံး**
မှားသော်လည်း reason တစ်ခုတည်း ပြန်သည် — `type_not_allowed`။ `elif` ၏
အကျိုးသက်ရောက်မှုဖြစ်သည်။

> **မှတ်ထားရန်** — reason တစ်ခုတည်း ပြန်ခြင်းသည် **debugging အတွက်
> လုံလောက်သည်** (ပထမဆုံး ဖြေရှင်းရမည့်အရာကို ညွှန်သည်) သို့သော် audit
> အတွက် reason အပြည့်အစုံ လိုလျှင် `if` နှစ်ခုကို သီးခြား စစ်ရမည်။ ဤအချက်က
> **gate အစဉ်သည် ရလဒ်ကို ပြောင်းသည်** ဆိုသည်ကို ပြသည်။

### 3.2 `or` Short-circuit

```python
grounded = {"neo4j inc", "emil eifrem"}
print("source ဖြတ်သလား :", "neo4j inc" in grounded)
print("target ဖြတ်သလား :", "athenadb" in grounded)
print("တစ်ခုခုမဖြတ်   :", "neo4j inc" not in grounded or "athenadb" not in grounded)
```

Output —

```text
source ဖြတ်သလား : True
target ဖြတ်သလား : False
တစ်ခုခုမဖြတ်   : True
```

`source_key not in grounded_names or target_key not in grounded_names` — `or`
ဖြစ်သဖြင့် **တစ်ခုခု** မဖြတ်လျှင် `True` ဖြစ်သည်။ Endpoint နှစ်ခုလုံး
grounded ဖြစ်ရမည်။

### 3.3 `(rel, "reason")` — Tuple ထဲ Tuple

```python
rel = {"source": "Neo4j Inc.", "type": "PRODUCES", "target": "AthenaDB"}
record = (rel, "endpoint_not_grounded")
print("record      :", record)
print("rel         :", record[0])
print("reason      :", record[1])
print("rel ၏ type  :", record[0]["type"])
print("triple      :", (record[0]["source"], record[0]["type"], record[0]["target"]))
```

Output —

```text
record      : ({'source': 'Neo4j Inc.', 'type': 'PRODUCES', 'target': 'AthenaDB'}, 'endpoint_not_grounded')
rel         : {'source': 'Neo4j Inc.', 'type': 'PRODUCES', 'target': 'AthenaDB'}
reason      : endpoint_not_grounded
rel ၏ type  : PRODUCES
triple      : ('Neo4j Inc.', 'PRODUCES', 'AthenaDB')
```

`record[0]` သည် dict ဖြစ်သည် — ထို့ကြောင့် `record[0]["type"]` လို့ **nested
indexing** လုပ်ရသည်။ `record[1]` သည် reason string ဖြစ်သည်။ Loop တွင်
`for rel, reason in dropped_relationships:` လို့ unpack လုပ်သည်။

### 3.4 Return Value

```python
return kept_entities, dropped_entities, kept_relationships, dropped_relationships
```

**Tuple ၄ ခု** ပြန်သည်။ Caller က `kept_e, dropped_e, kept_r, dropped_r =
ground_extraction(...)` ဖြင့် ခွဲယူသည်။ Tuple ဖြစ်သဖြင့် အစဉ်သည် သတ်မှတ်ထားသည် —
အစဉ် လွဲလျှင် variable များ လွဲမည်။

**မှတ်ထားရန်** — ဤ function သည် gate နှစ်ခုလုံးကို လုပ်ပြီး ရလဒ်၄ မျိုး
တစ်ခါတည်း ပြန်သဖြင့် caller က မည်သည့် အဆင့်မှ ရလဒ်ကိုမဆို ရနိုင်သည်။

---

## 4. ရလဒ်ကို Run လုပ်ကြည့်ခြင်း

```python
corpus = build_grounding_corpus(SOURCE_CHUNKS)
payload, _ = parse_llm_json(MOCK_LLM_RESPONSES["chunk-001"])
kept_e, dropped_e, kept_r, dropped_r = ground_extraction(payload, corpus, RELATIONSHIP_TYPES)

print(f"entities kept            : {[e['name'] for e in kept_e]}")
print(f"entities dropped         : {dropped_e}")
print(f"relationships kept       : {[(r['source'], r['type'], r['target']) for r in kept_r]}")
for rel, reason in dropped_r:
    print(f"relationship dropped     : {(rel['source'], rel['type'], rel['target'])} -> {reason}")
grounded_precision = len(kept_r) / len(payload["relationships"])
print(f"relationship precision   : {grounded_precision:.2f} after grounding")
```

Output —

```text
entities kept            : ['Neo4j Inc.', 'Emil Eifrem', 'Sweden']
entities dropped         : ['AthenaDB']
relationships kept       : [('Neo4j Inc.', 'FOUNDED_BY', 'Emil Eifrem'), ('Emil Eifrem', 'WORKS_FOR', 'Neo4j Inc.'), ('Neo4j Inc.', 'LOCATED_IN', 'Sweden')]
relationship dropped     : ('Neo4j Inc.', 'PRODUCES', 'AthenaDB') -> endpoint_not_grounded
relationship precision   : 0.75 after grounding
```

### 4.1 Entity ဇယား

| Entity | Corpus တွင် တွေ့ရ? | ရလဒ် |
| --- | --- | --- |
| `Neo4j Inc.` | `neo4j inc` — ရှိ | kept |
| `Emil Eifrem` | `emil eifrem` — ရှိ | kept |
| `Sweden` | `sweden` — ရှိ | kept |
| `AthenaDB` | `athenadb` — မရှိ | dropped |

### 4.2 Relationship ဇယား

| Relationship | Type ဖြတ်? | Endpoint ဖြတ်? | ရလဒ် |
| --- | --- | --- | --- |
| `(Neo4j Inc.)-[:FOUNDED_BY]->(Emil Eifrem)` | ဖြတ် | နှစ်ခုလုံး ဖြတ် | kept |
| `(Emil Eifrem)-[:WORKS_FOR]->(Neo4j Inc.)` | ဖြတ် | နှစ်ခုလုံး ဖြတ် | kept |
| `(Neo4j Inc.)-[:LOCATED_IN]->(Sweden)` | ဖြတ် | နှစ်ခုလုံး ဖြတ် | kept |
| `(Neo4j Inc.)-[:PRODUCES]->(AthenaDB)` | ဖြတ် | `athenadb` မဖြတ် | dropped — `endpoint_not_grounded` |

`PRODUCES` သည် allowed relationship list ထဲ **ပါသည်** — ထို့ကြောင့် type gate
ကို ဖြတ်သည်။ သို့သော် endpoint gate က ဖမ်းသည်။

> **အဓိကသင်ခန်းစာ** — **Hallucinated relationship သည် type မှန်နိုင်သော်လည်း
> endpoint မတည်မြဲနိုင်ပါ**။ Type validation တစ်ခုတည်းဖြင့် မလုံလောက်ပါ —
> endpoint grounding မဖြစ်မနေ လိုသည်။ Gate နှစ်ခုလုံး ရှိခြင်းသည်
> defense-in-depth ဖြစ်သည်။

### 4.3 Precision

```python
kept_count = 3
total_count = 4
precision = kept_count / total_count
print("raw       :", precision)
print("formatted :", "%.2f" % precision)
print("f-string  :", f"{precision:.2f}")
```

Output —

```text
raw       : 0.75
formatted : 0.75
f-string  : 0.75
```

`len(kept_r) / len(payload["relationships"])` — `/` သည် **float division** ဖြစ်သည်
(Python 3)။ `0.75` ရသည်။ `:.2f` က ဒသမ နှစ်နေရာ ဖြင့် ပြသည်။ Precision `0.75`
သည် relationship ၄ ခုထဲမှ ၃ ခုသာ ရှင်ကျန်ကြောင်း ပြသည် — grounding က
**recall ကို လျှော့ချ** ပြီး precision ကို **ကာကွယ်**သည်။

---

## 5. Code တစ်ခုလုံး — Run လုပ်နိုင်သော Version

```python
# (assembled 05) Run လုပ်နိုင်သော version — အပိုင်းအားလုံး ပေါင်းစည်းထားသည်
import json
import re
import unicodedata

FENCE = "`" * 3

SOURCE_CHUNKS = {
    "chunk-001": (
        "Neo4j Inc. is a graph database company. Neo4j Inc. was founded by "
        "Emil Eifrem. Emil Eifrem works for Neo4j Inc. Neo4j Inc. is located in Sweden."
    ),
    "chunk-002": (
        "Emil Eifrem works for Neo4j Inc. The Neo4j Inc. headquarters is "
        "located in Sweden."
    ),
    "chunk-003": "Neo4j Inc. released a new version of the graph platform.",
}

RELATIONSHIP_TYPES = ["FOUNDED_BY", "LOCATED_IN", "WORKS_FOR", "PRODUCES"]

MOCK_CHUNK_001 = FENCE + "json\n" + json.dumps({
    "entities": [
        {"name": "Neo4j Inc.", "type": "ORGANIZATION"},
        {"name": "Emil Eifrem", "type": "PERSON"},
        {"name": "Sweden", "type": "LOCATION"},
        {"name": "AthenaDB", "type": "ORGANIZATION"},
    ],
    "relationships": [
        {"source": "Neo4j Inc.", "target": "Emil Eifrem", "type": "FOUNDED_BY"},
        {"source": "Emil Eifrem", "target": "Neo4j Inc.", "type": "WORKS_FOR"},
        {"source": "Neo4j Inc.", "target": "Sweden", "type": "LOCATED_IN"},
        {"source": "Neo4j Inc.", "target": "AthenaDB", "type": "PRODUCES"},
    ],
}, indent=2) + "\n" + FENCE

CODE_FENCE_RE = re.compile(FENCE + r"(?:json)?\s*(.*?)" + FENCE, re.DOTALL)
TRAILING_COMMA_RE = re.compile(r",(\s*[}\]])")


def strip_code_fence(raw):
    match = CODE_FENCE_RE.search(raw)
    if match:
        return match.group(1).strip(), True
    return raw.strip(), False


def parse_llm_json(raw):
    repairs = []
    text, fenced = strip_code_fence(raw)
    if fenced:
        repairs.append("stripped_code_fence")
    try:
        return json.loads(text), repairs
    except json.JSONDecodeError:
        return None, "parse error"


def normalize_surface(name):
    text = unicodedata.normalize("NFKC", name).casefold()
    text = re.sub(r"[^\w\s]", "", text)
    return re.sub(r"\s+", " ", text).strip()


def build_grounding_corpus(chunks):
    return normalize_surface(" ".join(chunks.values()))


def ground_extraction(payload, corpus, relationship_types):
    kept_entities, dropped_entities = [], []
    grounded_names = set()
    for entity in payload["entities"]:
        key = normalize_surface(entity["name"])
        if key and key in corpus:
            kept_entities.append(entity)
            grounded_names.add(key)
        else:
            dropped_entities.append(entity["name"])

    kept_relationships, dropped_relationships = [], []
    for rel in payload["relationships"]:
        source_key = normalize_surface(rel["source"])
        target_key = normalize_surface(rel["target"])
        if rel["type"] not in relationship_types:
            dropped_relationships.append((rel, "type_not_allowed"))
        elif source_key not in grounded_names or target_key not in grounded_names:
            dropped_relationships.append((rel, "endpoint_not_grounded"))
        else:
            kept_relationships.append(rel)
    return kept_entities, dropped_entities, kept_relationships, dropped_relationships


corpus = build_grounding_corpus(SOURCE_CHUNKS)
payload, _ = parse_llm_json(MOCK_CHUNK_001)
kept_e, dropped_e, kept_r, dropped_r = ground_extraction(
    payload, corpus, RELATIONSHIP_TYPES
)

print(f"entities kept            : {[e['name'] for e in kept_e]}")
print(f"entities dropped         : {dropped_e}")
print(f"relationships kept       : {[(r['source'], r['type'], r['target']) for r in kept_r]}")
for rel, reason in dropped_r:
    print(f"relationship dropped     : {(rel['source'], rel['type'], rel['target'])} -> {reason}")

grounded_precision = len(kept_r) / len(payload["relationships"])
print(f"relationship precision   : {grounded_precision:.2f} after grounding")
```

Output —

```text
entities kept            : ['Neo4j Inc.', 'Emil Eifrem', 'Sweden']
entities dropped         : ['AthenaDB']
relationships kept       : [('Neo4j Inc.', 'FOUNDED_BY', 'Emil Eifrem'), ('Emil Eifrem', 'WORKS_FOR', 'Neo4j Inc.'), ('Neo4j Inc.', 'LOCATED_IN', 'Sweden')]
relationship dropped     : ('Neo4j Inc.', 'PRODUCES', 'AthenaDB') -> endpoint_not_grounded
relationship precision   : 0.75 after grounding
```

ဤ output သည် `lab.py` ၏ Exercise 5 output နှင့် တူညီသည်။

---

## 6. ကိုယ်တိုင်လေ့ကျင့်ကြည့်ပါ

**မေးခွန်း** — အောက်ပါ code က ဘယ်ရလဒ် ပြန်ပေးမလဲ။

```python
corpus = build_grounding_corpus(SOURCE_CHUNKS)
payload = {"entities": [{"name": "!!!"}], "relationships": []}
kept_e, dropped_e, kept_r, dropped_r = ground_extraction(payload, corpus, RELATIONSHIP_TYPES)
print(len(kept_e), kept_e)
print(dropped_e)
```

1. `1 []` နှင့် `[]`
2. `0 []` နှင့် `['!!!']`
3. `0 []` နှင့် `[]`
4. error — empty string ကို စစ်လို့မရ

<details>
<summary>အဖြေ ကြည့်ရန်</summary>

**အဖြေ — 2. `0 []` နှင့် `['!!!']`**

အကြောင်းရင်း — `normalize_surface("!!!")` သည် `""` ပြန်သည် (punctuation အားလုံး
ဖြတ်ခံရသည်)။ ထို့နောက် `if key and key in corpus:` ကို စစ်သည့်အခါ `key` သည်
empty string ဖြစ်ပြီး **falsy** ဖြစ်သဖြင့် `and` က ချက်ချင်း ရပ်သည် —
`grounded` အဖြစ် မဖြတ်ပါ။ ထို့ကြောင့် entity သည် `else` branch သို့ ရောက်ပြီး
`dropped_entities` ထဲ ဝင်သည်။

**ဤအကြောင်းရင်းကြောင့်သာ `key and` guard မဖြစ်မနေ လိုသည်** — guard မပါလျှင်
`"" in corpus` သည် `True` ဖြစ်သဖြင့် အမည်မရှိသည့် entity သည် grounded အဖြစ်
**မှားယွင်းစွာ** ဖြတ်သွားမည် (answer 1 ဖြစ်သွားမည်)။

</details>

---

**အဓိက မှတ်ထားရန်** — Gate နှစ်ခုလုံး လိုသည်။ `PRODUCES` သည် allowed list
အတွင်းရှိသည် (type gate ကို ဖြတ်သည်) သို့သော် `AthenaDB` သည် corpus တွင်
မတွေ့ရသဖြင့် endpoint gate ဖြင့် ဖမ်းခံရသည်။ ဤဖြစ်စဉ်သည် **hallucinated
relationship သည် type မှန်သော်လည်း endpoint မတည်မြဲနိုင်ကြောင်း** ပြသည် —
type validation တစ်ခုတည်းဖြင့် မလုံလောက်ပါ။ Substring attestation သည်
hallucination ကို လျှော့ချပေးသည်၊ လုံးဝ မကာကွယ်ပါ (`"Neo"`၊ `"Eifrem"`
ကဲ့သို့ အပိုင်းအစများ ဖြတ်နိုင်သည်)။ `if key and key in corpus` ရှိ `key and`
guard သည် empty normalized အမည်များ — `"" in corpus` က `True` ဖြစ်သဖြင့် —
မှားယွင်းစွာ grounded ဖြစ်ခြင်းကို တားသည်။
