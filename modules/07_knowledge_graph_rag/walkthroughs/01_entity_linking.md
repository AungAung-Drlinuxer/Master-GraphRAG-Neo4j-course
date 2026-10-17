# Walkthrough 01 — Entity Linking (Exercise 1)

> ဤဖိုင်သည် Module 07 ၏ `solution.md` ထဲက Exercise 1 ကို **Python အခြေခံမှ စ၍**
> အပိုင်းလိုက် ရှင်းပြသည့် walkthrough ဖြစ်သည်။ Format သည် Module 01 ၏
> `walkthroughs/01_regex_ner.md` နှင့် `walkthroughs/03_gazetteer_lookup.md` နှင့်
> တူညီသည်။

---

## 0. ဤ Exercise က ဘာကို ဖြေရှင်းပေးသလဲ။

GraphRAG တွင် retrieval သည် **graph** ပေါ်မှာ စသည်။ သို့သော် user က ပေးလာသည့် အရာက
**query text** ဖြစ်သည်၊ graph node မဟုတ်ပါ။ ဤကွက်လပ်ကို ဖြည့်သည့် အလုပ်ကို
**entity linking** (သို့) **anchor resolution** ဟု ခေါ်သည် — query ထဲပါ entity အမည်များကို
graph node id များအဖြစ် ပြောင်းခြင်း ဖြစ်သည်။

```text
query text: "How does Neo4j AuraDB use a vector index for retrieval?"
                              |
                     entity linking
                              |
                              v
anchor ids: ["co:neo4j", "prod:aura", "tech:vectorindex"]
                              |
                     (Exercise 2 မှ ဆက်လက် k-hop expand)
```

Anchor မှားလျှင် နောက်ပိုင်း လုပ်ငန်းစဉ် အားလုံး မှားသည် — မှားသော node မှ k-hop expand
လုပ်လျှင် retrieval စဉ်တစ်ခုလုံး မသက်ဆိုင်သည့် triple များ ဖြစ်လာသည်။ ထို့ကြောင့် linking
တွင် **precision ကို recall ထက် ဦးစားပေး** သည်။

ဤ code မှာ လေ့လာရမည့် Python concepts များမှာ —

- Dictionary ကို `id -> (label, name, aliases, summary)` အဖြစ် အသုံးပြုခြင်း
- Tuple unpacking (`label, name, aliases, summary = NODES[node_id]`)
- Tuple နှစ်ခုကို ဆက်ပေါင်းခြင်း (`(name,) + tuple(aliases)`)
- List comprehension (nested list comprehension အပါ)
- `sorted()` နှင့် `key=lambda`
- `max()` က tuple များအပေါ် အလုပ်လုပ်ပုံ
- Set union / intersection (`&`)
- `try`/`else` မလိုဘဲ guard clause ဖြင့် early return လုပ်ခြင်း
- `unicodedata.normalize()` နှင့် `difflib.SequenceMatcher`

---

## 1. `NODES` — Fixture (in-memory property graph)

```python
# node id -> (label, name, aliases, summary)
NODES = {
    "co:neo4j": ("Company", "Neo4j", ("Neo4j Inc", "Neo4j, Inc."), "Graph database vendor."),
    "prod:aura": ("Product", "AuraDB", ("Neo4j AuraDB", "Aura"), "Managed cloud graph database service."),
    "tech:cypher": ("Technology", "Cypher", ("openCypher", "Cypher Query Language"), "Declarative graph query language."),
    "tech:louvain": ("Technology", "Louvain", ("Louvain method",), "Greedy modularity optimisation for community detection."),
    "org:cnrs": ("Organization", "CNRS", (), "Research organisation of the Louvain authors."),
    "person:eifrem": ("Person", "Vincent Blondel", ("Blondel",), "Lead author of the Louvain method."),
    "tech:graphrag": ("Technology", "GraphRAG", ("Graph RAG", "Microsoft GraphRAG"), "Retrieval pattern grounded in a knowledge graph."),
    "tech:vectorindex": ("Technology", "Vector Index", ("vector search index", "HNSW index"), "Approximate nearest neighbour index over embeddings."),
    "org:neo4jeng": ("Team", "Neo4j Engineering", (), "Engineering team maintaining Cypher."),
    "paper:louvain": ("Paper", "Fast unfolding of communities in large networks", (), "The 2008 Louvain method paper."),
}
```

Dictionary ၏ key သည် **node id** (`co:neo4j`) ဖြစ်ပြီး value သည် element ၄ ခုပါသည့်
**tuple** ဖြစ်သည်။ `aliases` နေရာတွင် tuple ထပ်တစ်ခု ထည့်ထားသည် — ထို့ကြောင့် nested
structure ဖြစ်သည်။ `("Louvain method",)` လို element တစ်ခုတည်း ရှိသည့် tuple တွင်
**comma မဖြစ်မနေ လိုသည်** — `("Louvain method")` သည် ကွင်းသာဖြစ်ပြီး စာသားတစ်ခုတည်း
ဖြစ်သွားသည်။

Tuple ကို index ဖြင့် ဖတ်နိုင်သည်၊ tuple unpacking ဖြင့်လည် ဖတ်နိုင်သည်။

```python
NODES = {
    "tech:cypher": ("Technology", "Cypher", ("openCypher", "Cypher Query Language"), "Declarative graph query language."),
}

print(NODES["tech:cypher"])
label, name, aliases, summary = NODES["tech:cypher"]
print(label, "|", name, "|", aliases, "|", summary)
```

Output —

```text
('Technology', 'Cypher', ('openCypher', 'Cypher Query Language'), 'Declarative graph query language.')
Technology | Cypher | ('openCypher', 'Cypher Query Language') | Declarative graph query language.
```

`label` သည် GraphRAG ၏ schema level (Company၊ Product၊ Technology၊ Person) ဖြစ်ပြီး
`name` သည် canonical surface form ဖြစ်သည်။ `aliases` သည် ထို entity ကို စာသားထဲ
ရေးနိုင်သည့် အခြားနည်းလမ်းများ ဖြစ်သည်။ Linking တွင် `name` **နှင့်** alias အားလုံးကို
တစ်ပြေးညီ စစ်ရသည်။

---

## 2. `_fold()` — Unicode Normalization

```python
import unicodedata


def _fold(text):
    return unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode().casefold()
```

ဤ function တစ်လိုင်းတည်းတွင် အဆင့် ၃ ဆင့် ရှိသည်။

| အဆင့် | Method | အလုပ် |
| --- | --- | --- |
| ၁ | `unicodedata.normalize("NFKD", text)` | accented စာလုံးများကို base + combining mark အဖြစ် ခွဲထုတ် (`é` → `e` + mark) |
| ၂ | `.encode("ascii", "ignore")` | ASCII မဟုတ်သည့် byte များကို **ဖယ်ရှား** |
| ၃ | `.casefold()` | စာလုံးအသေးသို့ ပြောင်း (`lower()` ထက် ပို၍ ပြင်းထန်သည်) |

Method များကို `.` ဖြင့် အစဉ်လိုက် ချိတ်ထားသည်ကို **method chaining** ဟု ခေါ်သည်။
အဆင့်တိုင်း၏ ရလဒ်သည် နောက်အဆင့်၏ input ဖြစ်သည်။ ဤ function သည် `name` မဟုတ်သည့်
id (`tech:cypher`) ကို မဆိုင်ပါ — surface form များအတွက်သာ ဖြစ်သည်။

```python
import unicodedata


def _fold(text):
    return unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode().casefold()


print(_fold("Neo4j, Inc."))
print(_fold("Café Aura"))
```

Output —

```text
neo4j, inc.
cafe aura
```

`Café` → `cafe` ဖြစ်သွားသည်ကို တွေ့နိုင်သည်။ Punctuation (`,`၊ `.`) ကို
`_fold()` က **မဖယ်ပါ** — ဖယ်ရှားသည့် အလုပ်ကို နောက် function ဖြစ်သည့် `tokenize()` က
လုပ်သည်။

---

## 3. `tokenize()` — Token ခွဲထုတ်ခြင်း

```python
import re
import unicodedata


def _fold(text):
    return unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode().casefold()


def tokenize(text):
    return re.findall(r"[a-z0-9]+", _fold(text))
```

`re.findall(r"[a-z0-9]+", text)` သည် စာလုံးအသေး သို့မဟုတ် ဂဏန်း **တစ်ခုထက် မနည်း**
ဆက်နေသည့် အပိုင်းတိုင်းကို list အဖြစ် ပြန်ပေးသည်။ `_fold()` က စာလုံးအားလုံးကို
အသေးဖြစ်စေပြီးသား ဖြစ်သောကြောင့် pattern တွင် `A-Z` ထည့်ရန် မလိုပါ။ Punctuation
နှင့် space သည် pattern နှင့် မကိုက်ညီသဖြင့် token များကို ခြားပေးသလို အလုပ်လုပ်သည်။

```python
import re
import unicodedata


def _fold(text):
    return unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode().casefold()


def tokenize(text):
    return re.findall(r"[a-z0-9]+", _fold(text))


print(_fold("Neo4j, Inc."))
print(tokenize("Neo4j, Inc."))
print(tokenize("How does Neo4j AuraDB use a vector index?"))
```

Output —

```text
neo4j, inc.
['neo4j', 'inc']
['how', 'does', 'neo4j', 'auradb', 'use', 'a', 'vector', 'index']
```

`re.findall()` သည် ကိုက်ညီသည့် အပိုင်းအားလုံးကို **list** အဖြစ် ပြန်ပေးသည်။
မတွေ့လျှင် empty list `[]` ပြန်သည်။ `"Neo4j, Inc."` မှ token နှစ်ခု ရသည် — `neo4j`
နှင့် `inc`။ ဤ token list ကို set အဖြစ် ပြောင်းလျှင် **set operations** (`&`၊ `-`၊ `|`)
သုံးနိုင်သည်။

---

## 4. `fuzzy_score()` — Two-signal Score

```python
from difflib import SequenceMatcher


def fuzzy_score(surface, query):
    """Surface-form match score in [0, 1] between a node name/alias and a query."""
    s, q = " ".join(tokenize(surface)), " ".join(tokenize(query))
    if not s:
        return 0.0
    if s in q:
        return 1.0
    words = set(tokenize(surface))
    if not words:
        return 0.0
    overlap = len(words & set(tokenize(query))) / len(words)
    return round(max(overlap * 0.95, SequenceMatcher(None, s, q).ratio() * 0.6), 4)
```

### 4.1 `s, q = ... , ...` — Parallel assignment

```python
surface, query = "Neo4j AuraDB", "How does Neo4j AuraDB use a vector index?"
s, q = " ".join(tokenize(surface)), " ".join(tokenize(query))
print(repr(s))
print(repr(q))
```

Output —

```text
'neo4j auradb'
'how does neo4j auradb use a vector index'
```

`" ".join(list)` သည် list ထဲက စာသားများကို space ဖြင့် ပြန်ဆက်သည်။ Token list ကို
space ဖြင့် ပြန်ဆက်ထားသည့် form ကို **normalized form** ဟု ခေါ်သည် — မူရင်း
punctuation မည်သို့ပင်ဖြစ်ပါစေ normalized form တူညီသော surface များ တူညီသော
score ရမည်။

### 4.2 Guard clause

```python
if not s:
    return 0.0
```

`not s` သည် empty string `""` အတွက် `True` ဖြစ်သည်။ ဤလိုင်းက နောက်ပိုင်း
`SequenceMatcher` နှင့် division များကို error မဖြစ်စေရန် ကာကွယ်သည်။ ဤပုံစံကို
**guard clause** (သို့) **early return** ဟု ခေါ်သည် — `if/else` ကို အတွင်းထပ်မထားဘဲ
မဖြစ်နိုင်သည့် case ကို အပေါ်ဆုံးတွင် ဖယ်လိုက်သည်။

### 4.3 Substring signal — score 1.0

```python
if s in q:
    return 1.0
```

`in` သည် substring စစ်ခြင်း ဖြစ်သည် — `s` သည် `q` ထဲ တိုက်ရိုက် ပါဝင်နေလျှင် `True`။
`"neo4j auradb" in "how does neo4j auradb use a vector index"` → `True`။ ဤ signal သည်
အမှား အနည်းဆုံးဖြစ်သော်လည်း **inflection နှင့် spelling variant** ကို မဖမ်းနိုင်ပါ —
`AuraDB` ကို query ထဲ `auradb` လို့သာ ရေးထားရမည်။

### 4.4 Overlap signal — token အချင်းချင်း ထပ်မှု

```python
words = set(tokenize(surface))
if not words:
    return 0.0
overlap = len(words & set(tokenize(query))) / len(words)
```

`set(tokenize(surface))` သည် surface ၏ token များကို set အဖြစ် ပြောင်းသည်။ `&`
သည် **intersection** — နှစ်ဖက်လုံးတွင် ပါသည့် token များ။ `words` က denominator
ဖြစ်သည့်အတွက် ဤအပိုင်းသည် \"surface ၏ token မည်မျှ ရာခိုင်နှုန်း query ထဲ ပါသလဲ\"
ကို တိုင်းသည်။

### 4.5 SequenceMatcher signal နှင့် `max()`

```python
return round(max(overlap * 0.95, SequenceMatcher(None, s, q).ratio() * 0.6), 4)
```

`SequenceMatcher(None, a, b).ratio()` သည် စာသားနှစ်ခုကြား similarity ကို `[0, 1]`
အတွင်း ပြန်ပေးသည် — အစားထိုးမှု၊ ဖျက်မှု၊ ထည့်မှုများကို အခြေခံသည်။ `max(a, b)`
သည် ကြီးသည့် တန်ဖိုးကို ရွေးသည်။ `* 0.95` နှင့် `* 0.6` သည် signal တိုင်း၏ weight
ဖြစ်သည်။ `* 0.95` ကို လျှော့ထားရသည့် အကြောင်းရင်းမှာ overlap သည် false positive
ဖြစ်နိုင်သောကြောင့် ဖြစ်သည်။

တကယ့် တန်ဖိုးများဖြင့် တစ်ဆင့်ချင်း တွက်ကြည့်ပါ။

```python
import re
import unicodedata
from difflib import SequenceMatcher


def _fold(text):
    return unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode().casefold()


def tokenize(text):
    return re.findall(r"[a-z0-9]+", _fold(text))


def fuzzy_score(surface, query):
    s, q = " ".join(tokenize(surface)), " ".join(tokenize(query))
    if not s:
        return 0.0
    if s in q:
        return 1.0
    words = set(tokenize(surface))
    if not words:
        return 0.0
    overlap = len(words & set(tokenize(query))) / len(words)
    return round(max(overlap * 0.95, SequenceMatcher(None, s, q).ratio() * 0.6), 4)


surface = "Neo4j Engineering"
query = "How does Neo4j AuraDB use a vector index for retrieval?"
s = " ".join(tokenize(surface))
q = " ".join(tokenize(query))
words = set(tokenize(surface))
overlap = len(words & set(tokenize(query))) / len(words)
print("s =", repr(s))
print("q =", repr(q))
print("s in q ->", s in q)
print("words =", sorted(words))
print("overlap =", overlap)
print("overlap * 0.95 =", round(overlap * 0.95, 4))
print("SequenceMatcher ratio =", SequenceMatcher(None, s, q).ratio())
print("ratio * 0.6 =", round(SequenceMatcher(None, s, q).ratio() * 0.6, 4))
print("fuzzy_score =", fuzzy_score(surface, query))
```

Output —

```text
s = 'neo4j engineering'
q = 'how does neo4j auradb use a vector index for retrieval'
s in q -> False
words = ['engineering', 'neo4j']
overlap = 0.5
overlap * 0.95 = 0.475
SequenceMatcher ratio = 0.36619718309859156
ratio * 0.6 = 0.2197
fuzzy_score = 0.475
```

`words` သည် set ဖြစ်သဖြင့် **ပြသအစီအစဉ်သည် run တစ်ခုနှင့်တစ်ခု ကွဲနိုင်သည်**
(`{'engineering', 'neo4j'}` နှင့် `{'neo4j', 'engineering'}` နှစ်မျိုးလုံး တွေ့နိုင်သည်)။
ဤဖိုင်ရှိ အခြား output များမှာ ဤကဲ့သို့ တူညီအစီအစဉ် မလိုအပ်သည့် tuple/list
များသာ ဖြစ်သည်။

Overlap signal က `0.475` ပေးပြီး SequenceMatcher signal က `0.2197` ပေးသည်။ `max()`
သည် `0.475` ကို ရွေးသည်။ `round(..., 4)` က ဆယ်လုံးနောက်ပိုင်းကို ဖြတ်သည်။

---

## 5. `link_query()` — Iteration

```python
def link_query(query, threshold=0.7):
    """Return [(node_id, score, matched_surface)] sorted by score desc, id asc."""
    hits = []
    for node_id in sorted(NODES):
        label, name, aliases, summary = NODES[node_id]
        scored = [(fuzzy_score(s, query), s) for s in (name,) + tuple(aliases)]
        best_score, best_surface = max(scored)
        if best_score >= threshold:
            hits.append((node_id, best_score, best_surface))
    return sorted(hits, key=lambda h: (-h[1], h[0]))
```

### 5.1 Default argument — `threshold=0.7`

`def link_query(query, threshold=0.7)` တွင် `threshold` သည် **default argument** ဖြစ်သည်။
`link_query("...")` လို့ ခေါ်လျှင် `0.7` ကို အသုံးပြုသည်; `link_query("...", 0.4)` လို့
ခေါ်လျှင် override ဖြစ်သည်။

### 5.2 `sorted(NODES)` — Deterministic iteration

Dictionary ကို `for` ဖြင့် လှမ်းလျှင် **insertion order** အတိုင်း လာသည်။ ထို order
သည် code ပြင်လိုက်တိုင်း ပြောင်းနိုင်သည်။ `sorted(NODES)` က node id များကို
အက္ခရာအစီအစဉ်ဖြင့် ပြန်စီသဖြင့် run တိုင်း တူညီသည်။

```python
NODES = {
    "co:neo4j": ("Company", "Neo4j", ("Neo4j Inc",), "Graph database vendor."),
    "prod:aura": ("Product", "AuraDB", ("Neo4j AuraDB",), "Managed cloud service."),
    "tech:cypher": ("Technology", "Cypher", ("openCypher",), "Declarative graph query language."),
    "org:cnrs": ("Organization", "CNRS", (), "Research organisation."),
    "org:neo4jeng": ("Team", "Neo4j Engineering", (), "Engineering team."),
    "paper:louvain": ("Paper", "Fast unfolding", (), "The 2008 paper."),
    "person:eifrem": ("Person", "Vincent Blondel", ("Blondel",), "Lead author."),
    "tech:graphrag": ("Technology", "GraphRAG", ("Graph RAG",), "Retrieval pattern."),
    "tech:louvain": ("Technology", "Louvain", ("Louvain method",), "Greedy modularity."),
    "tech:vectorindex": ("Technology", "Vector Index", ("HNSW index",), "Approximate index."),
}

print(list(NODES)[:3])
print(sorted(NODES)[:3])
```

Output —

```text
['co:neo4j', 'prod:aura', 'tech:cypher']
['co:neo4j', 'org:cnrs', 'org:neo4jeng']
```

Insertion order သည် `prod:aura` ကို ဒုတိယ ထားသည်၊ sort ပြီးနောက် `org:cnrs` က
ဒုတိယ ဖြစ်သည်။

### 5.3 `scored` — Nested list comprehension

```python
scored = [(fuzzy_score(s, query), s) for s in (name,) + tuple(aliases)]
```

`(name,) + tuple(aliases)` သည် tuple နှစ်ခုကို ဆက်ပေါင်းသည်။ `co:neo4j` အတွက်
`("Neo4j",) + ("Neo4j Inc", "Neo4j, Inc.")` → `("Neo4j", "Neo4j Inc", "Neo4j, Inc.")`။
`aliases` သည် tuple ဖြစ်ပြီးသား ဖြစ်သော်လည်း `()` ဖြစ်နိုင်သဖြင့် `tuple(...)` ဖြင့်
သေချာစေသည်။ List comprehension က element တိုင်းအတွက် `(score, surface)` tuple
တစ်ခု ဖန်တီးပြီး list တစ်ခုအဖြစ် ပြန်သည်။

List comprehension ကို `for` loop အပြည့်ဖြင့် ရေးလျှင် —

```python
name, aliases = "Louvain", ("Louvain method",)
query = "Who proposed the Louvain method?"
scored = []
for s in (name,) + tuple(aliases):
    scored.append((fuzzy_score(s, query), s))
print(scored)
```

Output —

```text
[(1.0, 'Louvain'), (1.0, 'Louvain method')]
```

`fuzzy_score()` ကို ဤနေရာတွင် အသုံးပြုရန် လိုသော်လည်း အထက်တွင် သတ်မှတ်ပြီးသား
function ဖြစ်သည်။ သီးခြား run လုပ်လိုလျှင် ဤနေရာတွင် `_fold`၊ `tokenize`၊
`fuzzy_score` ကို ပြန်ထည့်ရသည် (Section 7 ၏ အပြည့်အစုံ code ကို ကြည့်ပါ)။

### 5.4 `max(scored)` — Tuple တစ်ခုလုံးကို နှိုင်းယှဉ်ခြင်း

`max(scored)` သည် `(score, surface)` tuple များကို နှိုင်းယှဉ်သည်။ Tuple နှိုင်းယှဉ်မှုသည်
**element အစဉ်လိုက်** ဖြစ်သည် — ပထမ `score` ကို နှိုင်းယှဉ်ပြီး တူညီလျှင် ဒုတိယ
`surface` ကို နှိုင်းယှဉ်သည်။

```python
print(max([(1.0, "Neo4j"), (1.0, "Neo4j AuraDB")]))
print(max([(1.0, "Louvain"), (1.0, "Louvain method")]))
print(max([(0.475, "Neo4j Engineering"), (1.0, "Neo4j")]))
```

Output —

```text
(1.0, 'Neo4j AuraDB')
(1.0, 'Louvain method')
(1.0, 'Neo4j')
```

ပထမ နှစ်လိုင်းတွင် score တူညီသဖြင့် **surface စာသား အက္ခရာအကြီး** က အနိုင်ရသည်
(`Neo4j AuraDB` > `Neo4j`၊ `Louvain method` > `Louvain`)။ ဤအချက်ကို သိထားရန်
လိုသည် — `max()` သည် surface အရှည်ဆုံးကို မရွေးပါ၊ အက္ခရာအစီအစဉ် နောက်ဆုံးကို
ရွေးသည်။ တတိယလိုင်းတွင် score မတူသဖြင့် score ကြီးသည့် tuple အနိုင်ရသည်။
`(best_score, best_surface) = max(scored)` သည် ဤ tuple ကို element နှစ်ခုအဖြစ် ခွဲယူသည်။

### 5.5 Threshold နှင့် `hits.append()`

```python
if best_score >= threshold:
    hits.append((node_id, best_score, best_surface))
```

`>=` ဖြစ်သည်၊ `>` မဟုတ်ပါ — score `0.7` နှင့် အတိအကျ တူလျှင် လက်ခံသည်။
မလက်ခံလျှင် ထို node သည် `hits` ထဲ လုံးဝ မပါပါ — 0 ဖြင့် မထည့်ပါ။

### 5.6 Final sort — `key=lambda`

`key` သည် function တစ်ခု လက်ခံသည်။ `link_query` ၏ နောက်ဆုံးလိုင်းမှာ —

```python
return sorted(hits, key=lambda h: (-h[1], h[0]))
```

`lambda h: (-h[1], h[0])` သည် `hits` ထဲက tuple တစ်ခုစီအတွက် **sort key** ကို
ဖန်တီးသည်။ `-h[1]` က score ကို အမှတ်လှန်သဖြင့် score မြင့်သည့်အရာ အရင်လာသည်
(descending)။ `h[0]` က tie ဖြစ်လျှင် node id အက္ခရာအစီအစဉ်ဖြင့် ဖြတ်သည်။ ဤ
tie-break မရှိလျှင် score တူညီသည့် run များတွင် ရလဒ် အစီအစဉ် ကွဲနိုင်သည်။

ထို `return` လိုင်းကို inline လုပ်ပြီး တိုက်ရိုက် run ကြည့်ပါ။

```python
hits = [("co:neo4j", 1.0), ("prod:aura", 1.0), ("tech:vectorindex", 1.0)]
print(sorted(hits, key=lambda h: (-h[1], h[0])))
```

Output —

```text
[('co:neo4j', 1.0), ('prod:aura', 1.0), ('tech:vectorindex', 1.0)]
```

---

## 6. ရလဒ်ကို နှိုင်းယှဉ်ခြင်း — အစစ်အမှန် Score ဇယား

Query ၁ အတွက် node တိုင်း၏ အကောင်းဆုံး score များကို တကယ်တွက်ထားသည်။

```python
NODES = {
    "co:neo4j": ("Company", "Neo4j", ("Neo4j Inc", "Neo4j, Inc."), "Graph database vendor."),
    "prod:aura": ("Product", "AuraDB", ("Neo4j AuraDB", "Aura"), "Managed cloud graph database service."),
    "tech:cypher": ("Technology", "Cypher", ("openCypher", "Cypher Query Language"), "Declarative graph query language."),
    "tech:louvain": ("Technology", "Louvain", ("Louvain method",), "Greedy modularity optimisation."),
    "org:cnrs": ("Organization", "CNRS", (), "Research organisation of the Louvain authors."),
    "person:eifrem": ("Person", "Vincent Blondel", ("Blondel",), "Lead author of the Louvain method."),
    "tech:graphrag": ("Technology", "GraphRAG", ("Graph RAG", "Microsoft GraphRAG"), "Retrieval pattern grounded in a knowledge graph."),
    "tech:vectorindex": ("Technology", "Vector Index", ("vector search index", "HNSW index"), "Approximate nearest neighbour index."),
    "org:neo4jeng": ("Team", "Neo4j Engineering", (), "Engineering team maintaining Cypher."),
    "paper:louvain": ("Paper", "Fast unfolding of communities in large networks", (), "The 2008 Louvain method paper."),
}
import re
import unicodedata
from difflib import SequenceMatcher


def _fold(text):
    return unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode().casefold()


def tokenize(text):
    return re.findall(r"[a-z0-9]+", _fold(text))


def fuzzy_score(surface, query):
    s, q = " ".join(tokenize(surface)), " ".join(tokenize(query))
    if not s:
        return 0.0
    if s in q:
        return 1.0
    words = set(tokenize(surface))
    if not words:
        return 0.0
    overlap = len(words & set(tokenize(query))) / len(words)
    return round(max(overlap * 0.95, SequenceMatcher(None, s, q).ratio() * 0.6), 4)


query = "How does Neo4j AuraDB use a vector index for retrieval?"
for node_id in sorted(NODES):
    label, name, aliases, _summary = NODES[node_id]
    best = max([(fuzzy_score(s, query), s) for s in (name,) + tuple(aliases)])
    print("%-18s score=%-7s surface=%r" % (node_id, best[0], best[1]))
```

Output —

```text
co:neo4j           score=1.0     surface='Neo4j'
org:cnrs           score=0.0621  surface='CNRS'
org:neo4jeng       score=0.475   surface='Neo4j Engineering'
paper:louvain      score=0.1545  surface='Fast unfolding of communities in large networks'
person:eifrem      score=0.118   surface='Blondel'
prod:aura          score=1.0     surface='Neo4j AuraDB'
tech:cypher        score=0.1125  surface='openCypher'
tech:graphrag      score=0.1333  surface='Microsoft GraphRAG'
tech:louvain       score=0.0787  surface='Louvain'
tech:vectorindex   score=1.0     surface='Vector Index'
```

| Node | Best score | Threshold 0.7 ကျော်သလား | အဓိကအကြောင်းရင်း |
| --- | --- | --- | --- |
| `co:neo4j` | 1.0 | ကျော်သည် | `neo4j` သည် query ထဲ substring |
| `prod:aura` | 1.0 | ကျော်သည် | `Neo4j AuraDB` သည် query ထဲ substring |
| `tech:vectorindex` | 1.0 | ကျော်သည် | `Vector Index` သည် query ထဲ substring |
| `org:neo4jeng` | 0.475 | မကျော်ပါ | `Neo4j` token တစ်ခုသာ ထပ်သည် (overlap `0.5 × 0.95`) |
| `paper:louvain` | 0.1545 | မကျော်ပါ | SequenceMatcher signal သာ |
| `tech:graphrag` | 0.1333 | မကျော်ပါ | SequenceMatcher signal သာ |
| `person:eifrem` | 0.118 | မကျော်ပါ | SequenceMatcher signal သာ |
| `tech:cypher` | 0.1125 | မကျော်ပါ | SequenceMatcher signal သာ |
| `tech:louvain` | 0.0787 | မကျော်ပါ | SequenceMatcher signal သာ |
| `org:cnrs` | 0.0621 | မကျော်ပါ | SequenceMatcher signal သာ |

ဇယားက **threshold 0.7** ၏ အခန်းကဏ္ဍကို ရှင်းရှင်းလင်းလင်း ပြသည်။ `org:neo4jeng` ၏
score `0.475` သည် ကျော်လုနီးပါး ဖြစ်သော်လည်း မကျော်ပါ။ ဤ node သည် `Neo4j`
ကို အမည်အစပိုင်းတွင် ပါသော်လည်း query ၏ ရည်ရွယ်ချက် (AuraDB + vector index)
မဟုတ်ပါ။ Threshold သည် ဤ false positive ကို ဖြတ်လိုက်သည်။

Threshold ကို လျှော့ကြည့်လျှင် ဤအချက် ထင်ရှားလာသည်။

```python
print("threshold 0.7 ->", [h[0] for h in link_query("How does Neo4j AuraDB use a vector index for retrieval?")])
print("threshold 0.4 ->", [h[0] for h in link_query("How does Neo4j AuraDB use a vector index for retrieval?", threshold=0.4)])
```

Output —

```text
threshold 0.7 -> ['co:neo4j', 'prod:aura', 'tech:vectorindex']
threshold 0.4 -> ['co:neo4j', 'prod:aura', 'tech:vectorindex', 'org:neo4jeng']
```

`0.4` သို့ လျှော့လိုက်လျှင် `org:neo4jeng` ပါ ဝင်လာသည် — ၄ ခု ဖြစ်သွားသည်။ ဤအချက်
သည် threshold ၏ တန်ဖိုးကို empirical ဖြင့် ရွေးရသည့် သဘောကို ပြသည်။

---

## 7. Code တစ်ခုလုံး — Run လုပ်နိုင်သော Version

```python
# end-to-end: exercise_1
import re
import unicodedata
from difflib import SequenceMatcher

NODES = {
    "co:neo4j": ("Company", "Neo4j", ("Neo4j Inc", "Neo4j, Inc."), "Graph database vendor."),
    "prod:aura": ("Product", "AuraDB", ("Neo4j AuraDB", "Aura"), "Managed cloud graph database service."),
    "tech:cypher": ("Technology", "Cypher", ("openCypher", "Cypher Query Language"), "Declarative graph query language."),
    "tech:louvain": ("Technology", "Louvain", ("Louvain method",), "Greedy modularity optimisation for community detection."),
    "org:cnrs": ("Organization", "CNRS", (), "Research organisation of the Louvain authors."),
    "person:eifrem": ("Person", "Vincent Blondel", ("Blondel",), "Lead author of the Louvain method."),
    "tech:graphrag": ("Technology", "GraphRAG", ("Graph RAG", "Microsoft GraphRAG"), "Retrieval pattern grounded in a knowledge graph."),
    "tech:vectorindex": ("Technology", "Vector Index", ("vector search index", "HNSW index"), "Approximate nearest neighbour index over embeddings."),
    "org:neo4jeng": ("Team", "Neo4j Engineering", (), "Engineering team maintaining Cypher."),
    "paper:louvain": ("Paper", "Fast unfolding of communities in large networks", (), "The 2008 Louvain method paper."),
}


def _fold(text):
    return unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode().casefold()


def tokenize(text):
    return re.findall(r"[a-z0-9]+", _fold(text))


def fuzzy_score(surface, query):
    s, q = " ".join(tokenize(surface)), " ".join(tokenize(query))
    if not s:
        return 0.0
    if s in q:
        return 1.0
    words = set(tokenize(surface))
    if not words:
        return 0.0
    overlap = len(words & set(tokenize(query))) / len(words)
    return round(max(overlap * 0.95, SequenceMatcher(None, s, q).ratio() * 0.6), 4)


def link_query(query, threshold=0.7):
    hits = []
    for node_id in sorted(NODES):
        label, name, aliases, summary = NODES[node_id]
        scored = [(fuzzy_score(s, query), s) for s in (name,) + tuple(aliases)]
        best_score, best_surface = max(scored)
        if best_score >= threshold:
            hits.append((node_id, best_score, best_surface))
    return sorted(hits, key=lambda h: (-h[1], h[0]))


queries = (
    "How does Neo4j AuraDB use a vector index for retrieval?",
    "Which algorithm does the Louvain method use to detect communities?",
    "Who proposed the Louvain method?",
)
linked = {}
for query in queries:
    hits = link_query(query)
    linked[query] = [h[0] for h in hits]
    print(f"query: {query}")
    for node_id, score, surface in hits:
        print(f"  -> {node_id:<18} score={score:<6} surface={surface!r}")

assert linked[queries[0]] == ["co:neo4j", "prod:aura", "tech:vectorindex"]
assert linked[queries[1]] == ["tech:louvain"]
assert linked[queries[2]] == ["tech:louvain"]
assert "org:cnrs" not in linked[queries[0]]
assert "person:eifrem" not in linked[queries[2]]
print("[ok] query -> node anchors resolved without false positives")
```

Output —

```text
query: How does Neo4j AuraDB use a vector index for retrieval?
  -> co:neo4j           score=1.0    surface='Neo4j'
  -> prod:aura          score=1.0    surface='Neo4j AuraDB'
  -> tech:vectorindex   score=1.0    surface='Vector Index'
query: Which algorithm does the Louvain method use to detect communities?
  -> tech:louvain       score=1.0    surface='Louvain method'
query: Who proposed the Louvain method?
  -> tech:louvain       score=1.0    surface='Louvain method'
[ok] query -> node anchors resolved without false positives
```

Query ၂ နှင့် ၃ တွင် `tech:louvain` **တစ်ခုတည်း** ရသည်ကို သတိထားပါ။ Query ၃
(\"Who proposed the Louvain method?\") တွင် `person:eifrem` (Vincent Blondel — ထို method
ကို တီထွင်သူ) သည် anchor အဖြစ် **မပါပါ**။ အကြောင်းရင်းမှာ query ထဲတွင် \"Blondel\"
ဟူသော စာသား လုံးဝ မပါသောကြောင့် ဖြစ်သည်။ Entity linking သည် **စာသားတူမှုကိုသာ**
ကြည့်သည်၊ world knowledge ကို မသုံးပါ — ဤအချက်သည် embedding-based linking
လိုအပ်လာသည့် အကြောင်းရင်းဖြစ်သည်။

`assert` လိုင်းများသည် run လုပ်သည့်အခါ ဘာမှ မပြပါ။ Claim မှားလျှင် `AssertionError`
ဖြစ်ပြီး script ရပ်သည် — ထို့ကြောင့် output ပြသရာတွင် `[ok]` လိုင်းတစ်လိုင်းသာ
ပေါ်သည်။

---

## 8. ကိုယ်တိုင်လေ့ကျင့်ကြည့်ပါ

**မေးခွန်း** — အောက်ပါ code က `cosine` အတွက် ဘယ် score ပြန်ပေးမလဲ။

```python
import re
import unicodedata
from difflib import SequenceMatcher


def _fold(text):
    return unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode().casefold()


def tokenize(text):
    return re.findall(r"[a-z0-9]+", _fold(text))


def fuzzy_score(surface, query):
    s, q = " ".join(tokenize(surface)), " ".join(tokenize(query))
    if not s:
        return 0.0
    if s in q:
        return 1.0
    words = set(tokenize(surface))
    if not words:
        return 0.0
    overlap = len(words & set(tokenize(query))) / len(words)
    return round(max(overlap * 0.95, SequenceMatcher(None, s, q).ratio() * 0.6), 4)


print(fuzzy_score("openCypher", "How does Neo4j AuraDB use a vector index?"))
```

1. `1.0` — `cypher` သည် substring တစ်ခုခုနှင့် ကိုက်ညီသည်
2. `0.475` — token တစ်ဝက် ထပ်သည်
3. `0.0` — ဘယ် token မှ မထပ်ပါ
4. `0.12` — SequenceMatcher signal သာ ကျန်သည်

<details>
<summary>အဖြေ ကြည့်ရန်</summary>

**အဖြေ — 4. `0.12`**

အကြောင်းရင်း — `openCypher` ၏ normalized form သည် `"opencypher"` ဖြစ်ပြီး ထို
စာသားသည် query ၏ normalized form ထဲ **တိုက်ရိုက် မပါပါ** — ထို့ကြောင့် substring
signal (1.0) မရပါ။ Token level တွင်လည်း `{"opencypher"}` နှင့် query token
များကြား ထပ်မှု မရှိပါ (`cypher` သည် `opencypher` နှင့် **မတူပါ** — regex
tokenizer သည် စာလုံးအားလုံးကို အတူတကွ token တစ်ခုအဖြစ် ယူသည်)။ ထို့ကြောင့်
`overlap = 0.0` ဖြစ်ပြီး ကျန်သည့် signal မှာ SequenceMatcher သာ ဖြစ်သည် —
`0.2 × 0.6 = 0.12`။

ဤအချက်က **substring matching နှင့် token matching နှစ်မျိုးလုံး၏ ကန့်သတ်ချက်**ကို
ပြသည် — စာလုံးအပိုင်းအစ (`cypher`) ကို စာသားတစ်လုံးတည်းအဖြစ် ပေါင်းထားသည့်
surface (`openCypher`) ကို ဤ approach ဖြင့် ဖမ်းမရပါ။

</details>

---

**အဓိက မှတ်ထားရန်** — Entity linking တွင် signal နှစ်ခု (substring နှင့် token
overlap) ကို weight ဖြင့် ပေါင်းပြီး threshold တစ်ခုဖြင့် ဖြတ်သည်။ Substring signal
သည် precision မြင့်သော်လည်း coverage နည်းသည်; token overlap သည် coverage
မြင့်သော်လည်း false positive ဖြစ်နိုင်သည်။ `sorted(NODES)` iteration နှင့်
`(-score, node_id)` sort သည် deterministic output ကို အာမခံသည်။ Threshold
အတွက် သတိထားရန် — ဤ approach သည် **စာသားတူမှုသာ** ကြည့်သောကြောင့် synonym
(`Blondel` ↔ `proposed Louvain`) ကို လုံးဝ မဖမ်းနိုင်ပါ။ ထိုကဲ့သို့ case အတွက်
embedding-based entity linking လိုအပ်သည်။
