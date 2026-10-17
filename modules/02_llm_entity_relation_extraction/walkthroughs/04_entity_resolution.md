# Walkthrough 04 — Entity Resolution (Exercise 4)

> ဤဖိုင်သည် Module 02 ၏ `solution.md` ထဲက Exercise 4 ကို **Python အခြေခံမှ စ၍**
> အပိုင်းလိုက် ရှင်းပြသည့် walkthrough ဖြစ်သည်။

---

## 0. ဤ Exercise က ဘာကို ဖြေရှင်းပေးသလဲ။

Extraction ပြီးသည့်နောက် entity တူညီတစ်ခုကို **အမည်အမျိုးမျိုး** ဖြင့် တွေ့ရသည်။

```text
"Neo4j Inc."   (7 ကြိမ်)
"Neo4j"        (3 ကြိမ်)
"Neo4j Inc"    (2 ကြိမ်)      ← ဤသုံးခုသည် တူညီသော entity
"Sweeden"      (1 ကြိမ်)
"Sweden"       (4 ကြိမ်)      ← typo၊ တူညီသော entity
"E. Eifrem"    (1 ကြိမ်)
"Emil Eifrem"  (5 ကြိမ်)      ← အတိုကောက်၊ တူညီသော entity
```

ဒီအတိုင်း graph ထဲ ထည့်လျှင် entity တူညီသည့် node **၇ ခု** ဖြစ်သွားမည် —
duplicate nodes များသည် graph ကို အားနည်းစေသည် (traversal မှားသည်၊
count မှားသည်)။

ဤ Exercise က surface form များကို canonical entity အဖြစ် **cluster** လုပ်ပေးသည်။

```text
surface form ၇ ခု
        │
        ├─ အဆင့် ၁ — alias map  (တိကျသော၊ လက်ဖြင့် သတ်မှတ်)
        └─ အဆင့် ၂ — fuzzy match (typo ကို ဖမ်း၊ ratio ≥ 0.85)
                        │
                        ▼
                 entity ၃ ခု
```

အစဉ်သည် အရေးကြီးသည် — **alias ကို fuzzy အရင် run** ရသည်။ အကြောင်းရင်းကို
Section 8 တွင် run စစ်ပြထားသည်။

ဤ code မှာ လေ့လာရမည့် Python concepts များမှာ —

- List of tuple နှင့် tuple unpacking
- `dict.get(key)` နှင့် `None` စစ်ဆေးခြင်း (alias မရှိသည့်အခါ)
- `dict.setdefault(key, default)` နှင့် nested list
- Regex — `[^\w\s]` နှင့် `\s+`
- `unicodedata.normalize("NFKC", s)` နှင့် `casefold()` vs `lower()`
- `difflib.SequenceMatcher(None, a, b).ratio()`
- `>=` နှင့် `>` ကို တွဲစစ်ခြင်း (threshold + best ရွေးချယ်မှု)
- `max(iterable, key=...)` နှင့် tuple key (tie-break)
- Generator expression — `sum(m[2] for m in members)`
- `.format()`-style f-string (`{name!r:16}`, `{best_ratio:.3f}`)

---

## 1. `SURFACE_FORMS` — List of Tuple

```python
SURFACE_FORMS = [
    ("Neo4j Inc.", "ORGANIZATION", 7),
    ("Neo4j", "ORGANIZATION", 3),
    ("Neo4j Inc", "ORGANIZATION", 2),
    ("Emil Eifrem", "PERSON", 5),
    ("E. Eifrem", "PERSON", 1),
    ("Sweeden", "LOCATION", 1),
    ("Sweden", "LOCATION", 4),
]
```

Element တိုင်းသည် **tuple သုံးလုံး** ဖြစ်သည် — (အမည်၊ type၊ frequency)။
List ထဲတွင် tuple ထည့်ထားခြင်းဖြင့် အမည်တိုင်းကို attribute သုံးခုဖြင့်
ဖော်ပြနိုင်သည်။

| အမည် | Type | Frequency |
| --- | --- | --- |
| `Neo4j Inc.` | `ORGANIZATION` | 7 |
| `Neo4j` | `ORGANIZATION` | 3 |
| `Neo4j Inc` | `ORGANIZATION` | 2 |
| `Emil Eifrem` | `PERSON` | 5 |
| `E. Eifrem` | `PERSON` | 1 |
| `Sweeden` | `LOCATION` | 1 |
| `Sweden` | `LOCATION` | 4 |

### 1.1 Tuple Indexing နှင့် Unpacking

```python
first = ("Neo4j Inc.", "ORGANIZATION", 7)
print(first[0])
print(first[1])
print(first[2])
name, entity_type, frequency = first
print(name, "|", entity_type, "|", frequency)
```

Output —

```text
Neo4j Inc.
ORGANIZATION
7
Neo4j Inc. | ORGANIZATION | 7
```

`first[0]` သည် index ဖြင့် ဖတ်ခြင်း။ `name, entity_type, frequency = first` သည်
**tuple unpacking** — element တိုင်း variable တစ်ခုထဲ ဝင်သည်။ Loop တွင်
`for name, entity_type, frequency in surface_forms:` လို့ ရေးလျှင် tuple တိုင်းက
variable သုံးခုအဖြစ် အလိုအလျောက် ခွဲသည်။

```python
total = 0
for name, entity_type, frequency in SURFACE_FORMS:
    total += frequency
print("frequency စုစုပေါင်း:", total)
print("form အရေအတွက်    :", len(SURFACE_FORMS))
```

Output —

```text
frequency စုစုပေါင်း: 23
form အရေအတွက်    : 7
```

---

## 2. `ALIAS_MAP` — လက်ဖြင့် သတ်မှတ်ထားသော အမည်ညွှန်း

```python
ALIAS_MAP = {
    "neo4j": "Neo4j Inc.",
    "neo4j inc": "Neo4j Inc.",
    "e eifrem": "Emil Eifrem",
}
```

**အဓိကအချက်** — key များသည် **normalized အမည်** ဖြစ်သည်။ `"Neo4j Inc."`
မဟုတ်ဘဲ `"neo4j inc"` ဖြစ်သည် — စာလုံးအသေး၊ punctuation မပါ။ အကြောင်းရင်းက
`resolve_entities` က lookup မလုပ်မီ `normalize_surface()` ကို ခေါ်သဖြင့်
နှစ်ဖက်လုံး တူညီသော ပုံစံဖြစ်ရမည်။

```python
print("Neo4j Inc. ->", ALIAS_MAP.get("neo4j inc"))
print("NEO4J      ->", ALIAS_MAP.get("neo4j"))
print("emil       ->", ALIAS_MAP.get("emil"))
print("missing    ->", ALIAS_MAP.get("emil eifrem"))
```

Output —

```text
Neo4j Inc. -> Neo4j Inc.
NEO4J      -> Neo4j Inc.
emil       -> None
missing    -> None
```

`dict.get(key)` သည် key မရှိလျှင် `None` ပြန်သည် — `KeyError` မဖြစ်သည်။
ဤအချက်သည် အရေးကြီးသည်: `resolve_entities` က `if aliased is not None:`
ဖြင့် alias ရှိမရှိ ခွဲသည်။ `None` သည် "alias မရှိ" ၏ အချက်ပြဖြစ်သည်။

> **မှတ်ထားရန်** — `ALIAS_MAP["e eifrem"]` ရှိသော်လည်း `"emil eifrem"` မရှိပါ။
> ဒါကြောင့် `Emil Eifrem` သည် alias ဖြင့် မဟုတ်ဘဲ "new" အနေနှင့် စသည်။
> ၎င်းနောက် `E. Eifrem` က alias ဖြင့် ထိုထဲ ဝင်သည်။

---

## 3. `normalize_surface()` — အမည်ကို တူညီပုံစံ ပြောင်းခြင်း

```python
def normalize_surface(name):
    text = unicodedata.normalize("NFKC", name).casefold()
    text = re.sub(r"[^\w\s]", "", text)
    return re.sub(r"\s+", " ", text).strip()
```

အဆင့် သုံးဆင့် ရှိသည်။

### 3.1 `unicodedata.normalize("NFKC", name)`

Unicode တွင် တူညီသော စာလုံးကို ကုဒ်ပွိုင့် အမျိုးမျိုးဖြင့် ရေးနိုင်သည် —
ဥပမာ `ﬁ` (ligature) နှင့် `fi`။ NFKC သည် ထိုတူညီမှုများကို **တူညီသော
ပုံစံ** (`fi`) သို့ ညှိပေးသည်။

```python
import unicodedata

print("raw     :", repr("\ufb01nance"))
print("NFKC    :", repr(unicodedata.normalize("NFKC", "\ufb01nance")))
```

Output —

```text
raw     : 'ﬁnance'
NFKC    : 'finance'
```

### 3.2 `casefold()` နှင့် `lower()`

`casefold()` သည် `lower()` ထက် **ပိုပြင်းထန်သည်** — case ကွာခြားမှုကို
ပိုမိုပြည့်စုံစွာ ဖျောက်သည်။

```python
print("lower   :", "Stra\u00dfe".lower())
print("casefold:", "Stra\u00dfe".casefold())
print("same?   :", "Stra\u00dfe".lower() == "STRASSE".lower())
print("same?   :", "Stra\u00dfe".casefold() == "STRASSE".casefold())
```

Output —

```text
lower   : straße
casefold: strasse
same?   : False
same?   : True
```

`ß` ကို `lower()` က မပြောင်းဘဲ ထားသည်; `casefold()` က `ss` ဖြစ်စေသည်။
ထို့ကြောင့် `casefold()` သည် entity အမည် နှိုင်းယှဉ်မှုအတွက် ပိုမှန်ကန်သည်။

### 3.3 `re.sub(r"[^\w\s]", "", text)` — Punctuation ဖြတ်ခြင်း

Pattern `[^\w\s]` သည် **စာလုံး၊ ဂဏန်း၊ underscore၊ whitespace မဟုတ်သည့်**
အရာအားလုံးကို ကိုက်ညီသည် — ဆိုလိုသည်မှာ punctuation ဖြစ်သည်။
`sub("", text)` ဖြင့် ဖြတ်လိုက်သည်။

```python
import re

for value in ("Neo4j Inc.", "Neo4j Inc", "E. Eifrem", "sg_rag-prd.m1"):
    print("%-14r -> %r" % (value, re.sub(r"[^\w\s]", "", value)))
```

Output —

```text
'Neo4j Inc.'   -> 'Neo4j Inc'
'Neo4j Inc'    -> 'Neo4j Inc'
'E. Eifrem'    -> 'E Eifrem'
'sg_rag-prd.m1' -> 'sg_ragprdm1'
```

`"Neo4j Inc."` နှင့် `"Neo4j Inc"` သည် ဤအဆင့်တွင် တူညီသွားသည် — `.` ဖြတ်ခံရသည်။
`E. Eifrem` သည် `E Eifrem` ဖြစ်သည် (`.` ဖြတ်၊ space ကျန်)။

> **မှတ်ထားရန်** — `\w` သည် underscore `_` ကို **ပါဝင်**သည်။ ထို့ကြောင့်
> `sg_rag-prd.m1` တွင် `_` ကျန်ခဲ့ပြီး `-` နှင့် `.` ဖြတ်ခံရသည်။

### 3.4 `re.sub(r"\s+", " ", text).strip()` — Whitespace စုစည်းခြင်း

`\s+` သည် whitespace တစ်ခုနှင့်အထက် ကိုက်ညီသည်။ `" "` ဖြင့် အစားထိုးသဖြင့်
space များစွာ ရှိလျှင် တစ်လုံးတည်း ဖြစ်သည်။ နောက်ဆုံး `.strip()` က
ရှေ့နောက် whitespace ကို ဖြတ်သည်။ အဆင့်သုံးဆင့်လုံး ပေါင်းထားသည့်
pipeline ကို run ကြည့်ပါ။

```python
import re
import unicodedata

def normalize_surface(name):
    text = unicodedata.normalize("NFKC", name).casefold()
    text = re.sub(r"[^\w\s]", "", text)
    return re.sub(r"\s+", " ", text).strip()

for value in ("Neo4j Inc.", "  Neo4j   Inc.  ", "Neo4j\tInc", "E. Eifrem", "SWEDEN"):
    print("%-20r -> %r" % (value, normalize_surface(value)))
```

Output —

```text
'Neo4j Inc.'         -> 'neo4j inc'
'  Neo4j   Inc.  '   -> 'neo4j inc'
'Neo4j\tInc'         -> 'neo4j inc'
'E. Eifrem'          -> 'e eifrem'
'SWEDEN'             -> 'sweden'
```

Space များစွာ၊ ရှေ့နောက် space၊ tab — သုံးခုလုံး `"neo4j inc"` ဖြစ်သွားသည်ကို
တွေ့နိုင်သည်။ Case လည်း အားလုံး စာလုံးအသေး ဖြစ်သည်။

Empty ဖြစ်သည့် အခြေအနေကို စမ်းကြည့်ပါ။

```python
import re
import unicodedata

def normalize_surface(name):
    text = unicodedata.normalize("NFKC", name).casefold()
    text = re.sub(r"[^\w\s]", "", text)
    return re.sub(r"\s+", " ", text).strip()

print("'!!!' ->", repr(normalize_surface("!!!")))
print("''    ->", repr(normalize_surface("")))
print("length:", len(normalize_surface("!!!")))
```

Output —

```text
'!!!' -> ''
''    -> ''
length: 0
```

`"!!!"` နှင့် `""` သည် **empty string** ဖြစ်သွားသည်ကို သတိထားပါ — ဤအချက်သည်
Exercise 5 ၏ grounding filter တွင် `if key and key in corpus:` guard လိုသည့်
အကြောင်းရင်း ဖြစ်သည်။

---

## 4. `fuzzy_ratio()` — စာသားနှစ်ခု ဘယ်လောက်တူလဲ

```python
def fuzzy_ratio(a, b):
    return difflib.SequenceMatcher(None, a, b).ratio()
```

`difflib.SequenceMatcher(None, a, b)` သည် စာသားနှစ်ခုကြား **ကိုက်ညီမှု
အချိုး** ကို 0.0 မှ 1.0 အထိ ပြန်သည်။ ပထမ argument `None` သည် ဤအသုံးအတွက်
default ဖြစ်သည်။

```python
import difflib

def fuzzy_ratio(a, b):
    return difflib.SequenceMatcher(None, a, b).ratio()

pairs = [
    ("sweden", "sweden"),
    ("sweeden", "sweden"),
    ("neo4j inc", "neo4j inc"),
    ("neo4j", "neo4j inc"),
    ("e eifrem", "emil eifrem"),
]
for a, b in pairs:
    print("%-12r vs %-14r = %.3f" % (a, b, fuzzy_ratio(a, b)))
```

Output —

```text
'sweden'     vs 'sweden'       = 1.000
'sweeden'    vs 'sweden'       = 0.923
'neo4j inc'  vs 'neo4j inc'    = 1.000
'neo4j'      vs 'neo4j inc'    = 0.714
'e eifrem'   vs 'emil eifrem'  = 0.842
```

ဤဇယားသည် Exercise ၏ အဓိကဆုံးဖြတ်ချက်ကို ပြသည်။

| pair | ratio | threshold 0.85 ဖြင့် | မှတ်ချက် |
| --- | --- | --- | --- |
| `sweeden` / `sweden` | 0.923 | **ဖြတ်သည်** | typo ဖမ်းမိ |
| `neo4j` / `neo4j inc` | 0.714 | မဖြတ် | "inc" ဖြည့်ထားသဖြင့် ကွာ |
| `e eifrem` / `emil eifrem` | 0.842 | **မဖြတ်** | 0.85 ထက် နည်းသည် |

**အရေးကြီးသည့် တွေ့ရှိချက်** — `e eifrem` / `emil eifrem` ၏ ratio သည်
**0.842** ဖြစ်ပြီး threshold `0.85` ထက် **နည်း**သည်။ ထို့ကြောင့် fuzzy match
ဖြင့် ဤအတိုကောက်ကို မဖမ်းနိုင်ပါ — ထိုအတွက် **alias list မဖြစ်မနေ လိုသည်**။
ဤအချက်သည် `ALIAS_MAP` တွင် `"e eifrem"` ထည့်ထားရသည့် အကြောင်းရင်းဖြစ်သည်။

---

## 5. `resolve_entities()` — ပင်မ Function

```python
def resolve_entities(surface_forms, alias_map, threshold=FUZZY_THRESHOLD):
    clusters = {}
    decisions = []
    for name, entity_type, frequency in surface_forms:
        key = normalize_surface(name)
        aliased = alias_map.get(key)
        if aliased is not None:
            canonical_key = normalize_surface(aliased)
            method = "alias"
        else:
            canonical_key = None
            best_ratio = 0.0
            for existing_key in clusters:
                ratio = fuzzy_ratio(key, existing_key)
                if ratio >= threshold and ratio > best_ratio:
                    best_ratio = ratio
                    canonical_key = existing_key
            if canonical_key is not None:
                method = f"fuzzy({best_ratio:.3f})"
            else:
                canonical_key = key
                method = "new"
        clusters.setdefault(canonical_key, []).append((name, entity_type, frequency))
        decisions.append((name, method, canonical_key))

    resolved = {}
    for canonical_key, members in clusters.items():
        names = [m[0] for m in members]
        frequency = sum(m[2] for m in members)
        entity_type = members[0][1]
        canonical_name = max(names, key=lambda n: (max(m[2] for m in members if m[0] == n), len(n), n))
        resolved[canonical_name] = {
            "type": entity_type,
            "surface_forms": names,
            "total_frequency": frequency,
        }
    return resolved, decisions
```

### 5.1 Structure——`clusters` နှင့် `decisions`

Function က dict နှစ်ခု တည်ဆောက်သည်။

- `clusters` — `canonical_key` → ထိုထဲ ဝင်သည့် member tuple များ၏ list။
- `decisions` — surface form တိုင်းအတွက် (အမည်၊ နည်းလမ်း၊ ရောက်သည့် key)။

`decisions` သည် **audit trail** ဖြစ်သည် — ဘယ် form က ဘယ်လိုနည်းလမ်းဖြင့်
ဘယ် entity ထဲ ဝင်သည်ကို နောက်ပိုင်း စစ်နိုင်သည်။

### 5.2 Alias Branch

```python
key = normalize_surface(name)
aliased = alias_map.get(key)
if aliased is not None:
    canonical_key = normalize_surface(aliased)
    method = "alias"
```

အမည်ကို normalize လုပ်ပြီး alias map ထဲ ရှာသည်။ ရှိလျှင် alias ၏ **တန်ဖိုး**
(canonical အမည်) ကို ထပ်မံ normalize လုပ်ပြီး `canonical_key` ဖြစ်စေသည်။
`canonical_key = normalize_surface(aliased)` သည် နောက်ပိုင်း fuzzy match
နှင့် cluster key နှစ်ခုလုံး တူညီသော အခြေခံပေါ်တွင် ရှိစေသည်။

```python
print(normalize_surface("Neo4j Inc."))
print(ALIAS_MAP.get("neo4j"))
print(normalize_surface(ALIAS_MAP.get("neo4j")))
```

Output —

```text
neo4j inc
Neo4j Inc.
neo4j inc
```

### 5.3 Fuzzy Branch နှင့် Best Ratio ရွေးချယ်မှု

```python
canonical_key = None
best_ratio = 0.0
for existing_key in clusters:
    ratio = fuzzy_ratio(key, existing_key)
    if ratio >= threshold and ratio > best_ratio:
        best_ratio = ratio
        canonical_key = existing_key
if canonical_key is not None:
    method = f"fuzzy({best_ratio:.3f})"
else:
    canonical_key = key
    method = "new"
```

Condition နှစ်ခုကို တွဲစစ်သည်။

- `ratio >= threshold` — အနည်းဆုံး သတ်မှတ်ချက် ဖြတ်ရမည်။
- `ratio > best_ratio` — လက်ရှိ အကောင်းဆုံးထက် **ပိုကောင်း** ရမည်။

ဒုတိယ condition က **အကောင်းဆုံး တူညီမှုကို ရွေး**စေသည် — ပထမဆုံး ဖြတ်သည့်
key တွင် ရပ်လိုက်လျှင် cluster မှားနိုင်သည်။ မဖြတ်လျှင် `canonical_key` သည်
`None` ဖြစ်နေပြီး `key` ကိုယ်တိုင် cluster key ဖြစ်သည် (`method = "new"`)။

`f"fuzzy({best_ratio:.3f})"` တွင် `:.3f` သည် **ဒသမ သုံးနေရာ** ဖြင့် ပြသည် —
`0.923`။

```python
print("fuzzy(%s)" % ("%.3f" % 0.9230769))
print(f"fuzzy({0.9230769:.3f})")
print(f"{0.5:.3f}", f"{1.0:.3f}", f"{0.8416:.3f}")
```

Output —

```text
fuzzy(0.923)
fuzzy(0.923)
0.500 1.000 0.842
```

### 5.4 `setdefault()` — Cluster ထဲ ထည့်ခြင်း

```python
clusters.setdefault(canonical_key, []).append((name, entity_type, frequency))
```

`setdefault(key, [])` သည် —

- key ရှိလျှင် ရှိပြီးသား list ကို ပြန်သည်။
- key မရှိလျှင် **`[]` ကို ထည့်ပြီး** ထို list ကို ပြန်သည်။

ထို့နောက် `.append(...)` က member ကို ထည့်သည်။ `if key not in clusters:
clusters[key] = []` နှင့် တူညီသော ရည်ရွယ်ချက်၊ ပိုတိုသည်။

```python
clusters = {}
clusters.setdefault("kira", []).append(("Kira", "PERSON", 2))
clusters.setdefault("kira", []).append(("KIRA", "PERSON", 1))
clusters.setdefault("bob", []).append(("Bob", "PERSON", 3))
print(clusters)
print("kiras:", len(clusters["kira"]))
```

Output —

```text
{'kira': [('Kira', 'PERSON', 2), ('KIRA', 'PERSON', 1)], 'bob': [('Bob', 'PERSON', 3)]}
kiras: 2
```

> **သတိပေးချက်** — dict ၏ ပြသအစီအစဉ်သည် **insertion order** ဖြစ်ပြီး
> key များ ပထမဆုံး ထည့်သည့် အစဉ်အတိုင်း ဖြစ်သည်။ ဤ code တွင် key များသည်
> input အစဉ်အလိုက် ဖြစ်သဖြင့် deterministic ဖြစ်သည်။ `set` ဖြစ်လျှင်
> အစီအစဉ် ပြောင်းနိုင်သည် — ဤနေရာတွင် `dict` ဖြစ်သဖြင့် ပြဿနာ မရှိပါ။

### 5.5 ဒုတိယ Loop — Canonical Name ရွေးချယ်ခြင်း

```python
resolved = {}
for canonical_key, members in clusters.items():
    names = [m[0] for m in members]
    frequency = sum(m[2] for m in members)
    entity_type = members[0][1]
    canonical_name = max(names, key=lambda n: (max(m[2] for m in members if m[0] == n), len(n), n))
    resolved[canonical_name] = {
        "type": entity_type,
        "surface_forms": names,
        "total_frequency": frequency,
    }
```

`clusters.items()` သည် (key၊ value) tuple များကို ပေးသည်။

- `names = [m[0] for m in members]` — list comprehension ဖြင့် အမည်များကို ဆွဲထုတ်သည်။
- `frequency = sum(m[2] for m in members)` — generator expression ဖြင့်
  frequency များကို ပေါင်းသည်။
- `entity_type = members[0][1]` — ပထမ member ၏ type ကို ယူသည်။

```python
members = [("Neo4j Inc.", "ORGANIZATION", 7), ("Neo4j", "ORGANIZATION", 3)]
names = [m[0] for m in members]
print("names :", names)
print("total :", sum(m[2] for m in members))
print("type  :", members[0][1])
print("nested:", members[0][0])
```

Output —

```text
names : ['Neo4j Inc.', 'Neo4j']
total : 10
type  : ORGANIZATION
nested: Neo4j Inc.
```

`members[0][0]` သည် **nested indexing** — ပထမ tuple ၏ ပထမ element။

### 5.6 Return Value

```python
return resolved, decisions
```

Tuple နှစ်ခု ပြန်သည် — `resolved` (dict) နှင့် `decisions` (list)။ Caller က
`resolved, decisions = resolve_entities(...)` ဖြင့် ခွဲယူသည်။

---

## 6. Canonical Name — `max()` နှင့် Tuple Key

```python
canonical_name = max(names, key=lambda n: (max(m[2] for m in members if m[0] == n), len(n), n))
```

`max(iterable, key=func)` သည် `func` အရ **အကြီးဆုံး** element ကို ရွေးသည်။
`key` က tuple ပြန်သဖြင့် **အဆင့်လိုက်** နှိုင်းယှဉ်သည်။

| အစဉ် | နှိုင်းယှဉ်သည့်အရာ | ရည်ရွယ်ချက် |
| --- | --- | --- |
| ၁ | ထို အမည်၏ frequency | အများဆုံး တွေ့ရသော ပုံစံကို ရွေး |
| ၂ | `len(n)` | frequency တူလျှင် ရှည်သည့်အမည်ကို ရွေး |
| ၃ | `n` (အက္ခရာစဉ်) | ကျန်လျှင် lexicographic |

ဒုတိယနှင့် တတိယက **tie-break** ဖြစ်သည် — run တိုင်း တူညီသော ရလဒ် ရစေသည်။
မထည့်လျှင် Python သည် list ၏ အစဉ်အလိုက် ပထမဆုံးကို ရွေးနိုင်သည် —
input အစဉ်ပြောင်းလျှင် ရလဒ် ပြောင်းနိုင်သည်။

```python
members_neo4j = [
    ("Neo4j Inc.", "ORGANIZATION", 7),
    ("Neo4j", "ORGANIZATION", 3),
    ("Neo4j Inc", "ORGANIZATION", 2),
]
names = [m[0] for m in members_neo4j]
best = max(names, key=lambda n: (max(m[2] for m in members_neo4j if m[0] == n), len(n), n))
print("names   :", names)
print("chosen  :", best)
```

Output —

```text
names   : ['Neo4j Inc.', 'Neo4j', 'Neo4j Inc']
chosen  : Neo4j Inc.
```

`Neo4j Inc.` (freq 7) နှင့် `Neo4j Inc` (freq 2) တို့သည် ရှည်ချင်း တူညီကြသော်လည်း
frequency ကွာသဖြင့် `Neo4j Inc.` ကို ရွေးသည်။

```python
tie = [("Aa", "X", 5), ("Bb", "X", 5)]
names = [m[0] for m in tie]
best = max(names, key=lambda n: (max(m[2] for m in tie if m[0] == n), len(n), n))
print("tie ဖြစ်လျှင် ရွေးသည့်အမည်:", best)
```

Output —

```text
tie ဖြစ်လျှင် ရွေးသည့်အမည်: Bb
```

Frequency (5) နှင့် length (2) တူသဖြင့် lexicographic သို့ ရောက်သည် —
`"Bb"` > `"Aa"`။ ဤအစဉ်သည် deterministic ဖြစ်သည်။

---

## 7. ရလဒ်ကို Run လုပ်ကြည့်ခြင်း

```python
resolved, decisions = resolve_entities(SURFACE_FORMS, ALIAS_MAP)

for name, method, canonical_key in decisions:
    print(f"  {name!r:16} -> {method:14} -> key {canonical_key!r}")
print(f"resolved entity count    : {len(resolved)} of {len(SURFACE_FORMS)} surface forms")
for canonical_name, info in sorted(resolved.items()):
    print(
        f"  {canonical_name}: type={info['type']}, "
        f"forms={len(info['surface_forms'])}, freq={info['total_frequency']}"
    )
```

Output —

```text
  'Neo4j Inc.'     -> alias          -> key 'neo4j inc'
  'Neo4j'          -> alias          -> key 'neo4j inc'
  'Neo4j Inc'      -> alias          -> key 'neo4j inc'
  'Emil Eifrem'    -> new            -> key 'emil eifrem'
  'E. Eifrem'      -> alias          -> key 'emil eifrem'
  'Sweeden'        -> new            -> key 'sweeden'
  'Sweden'         -> fuzzy(0.923)   -> key 'sweeden'
resolved entity count    : 3 of 7 surface forms
  Emil Eifrem: type=PERSON, forms=2, freq=6
  Neo4j Inc.: type=ORGANIZATION, forms=3, freq=12
  Sweden: type=LOCATION, forms=2, freq=5
```

`{name!r:16}` တွင် `!r` သည် `repr()` ကို သုံးသည် (quote ပါသည်)၊ `:16` သည်
ကော်လံ ၁၆ ခု ကျယ်စေသည်။ `{method:14}` နှင့် `{best_ratio:.3f}` သည်
`format()` spec များဖြစ်သည်။

### 7.1 Decision ဇယား

| Surface form | နည်းလမ်း | ရောက်သည့် key |
| --- | --- | --- |
| `Neo4j Inc.` | `alias` | `neo4j inc` |
| `Neo4j` | `alias` | `neo4j inc` |
| `Neo4j Inc` | `alias` | `neo4j inc` |
| `Emil Eifrem` | `new` | `emil eifrem` |
| `E. Eifrem` | `alias` | `emil eifrem` |
| `Sweeden` | `new` | `sweeden` |
| `Sweden` | `fuzzy(0.923)` | `sweeden` |

`Sweeden` သည် `new` ဖြစ်ပြီး `Sweden` ကမှ fuzzy ဖြင့် ထိုထဲ ဝင်သည် — **အစဉ်သည်
အရေးကြီးသည်**။ Input အစဉ် ပြောင်းလျှင် ဘယ်တစ်ခုက `new` ဖြစ်မည် ပြောင်းနိုင်သည်
(ရလဒ် cluster မပြောင်း)။

### 7.2 Resolved Entity ဇယား

| Canonical | Type | Surface forms | Total frequency |
| --- | --- | --- | --- |
| `Emil Eifrem` | `PERSON` | 2 | 6 |
| `Neo4j Inc.` | `ORGANIZATION` | 3 | 12 |
| `Sweden` | `LOCATION` | 2 | 5 |

Surface form ၇ ခုမှ entity **၃ ခု** ဖြစ်လာသည်။ `Neo4j Inc.` cluster ၏
total frequency သည် 7 + 3 + 2 = **12** ဖြစ်သည်။

---

## 8. Alias-First နှင့် Fuzzy-First နှိုင်းယှဉ်ခြင်း

Alias map ကို ဖယ်လိုက်လျှင် ဘာဖြစ်လဲ စမ်းကြည့်ပါ။

```python
resolved_no_alias, decisions_no_alias = resolve_entities(SURFACE_FORMS, {})

for name, method, canonical_key in decisions_no_alias:
    print(f"  {name!r:16} -> {method:14} -> key {canonical_key!r}")
print("entity အရေအတွက်:", len(resolved_no_alias))
```

Output —

```text
  'Neo4j Inc.'     -> new            -> key 'neo4j inc'
  'Neo4j'          -> new            -> key 'neo4j'
  'Neo4j Inc'      -> fuzzy(1.000)   -> key 'neo4j inc'
  'Emil Eifrem'    -> new            -> key 'emil eifrem'
  'E. Eifrem'      -> new            -> key 'e eifrem'
  'Sweeden'        -> new            -> key 'sweeden'
  'Sweden'         -> fuzzy(0.923)   -> key 'sweeden'
entity အရေအတွက်: 5
```

Alias map မပါလျှင် entity **၅ ခု** ဖြစ်သည်။

| ပြဿနာ | အကြောင်းရင်း |
| --- | --- |
| `Neo4j` နှင့် `Neo4j Inc.` ကွဲ | ratio 0.714 < 0.85 |
| `E. Eifrem` ကွဲ | ratio 0.842 < 0.85 |

### Threshold ကို လျှော့ကြည့်ခြင်း

```python
resolved_low, _ = resolve_entities(SURFACE_FORMS, {}, threshold=0.80)
print("threshold 0.80 entity:", len(resolved_low))
```

Output —

```text
threshold 0.80 entity: 4
```

Threshold ကို 0.80 သို့ လျှော့လျှင် `e eifrem`/`emil eifrem` (0.842) ဖြတ်သဖြင့်
entity ၄ ခု ဖြစ်သည်။ သို့သော် `Neo4j`/`Neo4j Inc.` (0.714) က မဖြတ်တော့သဖြင့်
ပြဿနာ ကျန်နေသည်။

> **မှတ်ထားရန်** — Threshold ကို လျှော့ခြင်းသည် **wrong reason ဖြင့်** အချို့
> case များကို ကယ်သည်၊ ဒါပေမဲ့ တခြား false positive များ ဝင်လာစေနိုင်သည်
> (မတူညီသော entity များကို ပေါင်းလိုက်ခြင်း)။ Abbreviation အတွက်
> **alias list သည် မှန်ကန်သော ဖြေရှင်းချက်** ဖြစ်သည် — threshold မဟုတ်ပါ။

---

## 9. Code တစ်ခုလုံး — Run လုပ်နိုင်သော Version

```python
# (assembled 04) Run လုပ်နိုင်သော version — အပိုင်းအားလုံး ပေါင်းစည်းထားသည်
import difflib
import re
import unicodedata

SURFACE_FORMS = [
    ("Neo4j Inc.", "ORGANIZATION", 7),
    ("Neo4j", "ORGANIZATION", 3),
    ("Neo4j Inc", "ORGANIZATION", 2),
    ("Emil Eifrem", "PERSON", 5),
    ("E. Eifrem", "PERSON", 1),
    ("Sweeden", "LOCATION", 1),
    ("Sweden", "LOCATION", 4),
]

ALIAS_MAP = {
    "neo4j": "Neo4j Inc.",
    "neo4j inc": "Neo4j Inc.",
    "e eifrem": "Emil Eifrem",
}

FUZZY_THRESHOLD = 0.85


def normalize_surface(name):
    text = unicodedata.normalize("NFKC", name).casefold()
    text = re.sub(r"[^\w\s]", "", text)
    return re.sub(r"\s+", " ", text).strip()


def fuzzy_ratio(a, b):
    return difflib.SequenceMatcher(None, a, b).ratio()


def resolve_entities(surface_forms, alias_map, threshold=FUZZY_THRESHOLD):
    clusters = {}
    decisions = []
    for name, entity_type, frequency in surface_forms:
        key = normalize_surface(name)
        aliased = alias_map.get(key)
        if aliased is not None:
            canonical_key = normalize_surface(aliased)
            method = "alias"
        else:
            canonical_key = None
            best_ratio = 0.0
            for existing_key in clusters:
                ratio = fuzzy_ratio(key, existing_key)
                if ratio >= threshold and ratio > best_ratio:
                    best_ratio = ratio
                    canonical_key = existing_key
            if canonical_key is not None:
                method = f"fuzzy({best_ratio:.3f})"
            else:
                canonical_key = key
                method = "new"
        clusters.setdefault(canonical_key, []).append((name, entity_type, frequency))
        decisions.append((name, method, canonical_key))

    resolved = {}
    for canonical_key, members in clusters.items():
        names = [m[0] for m in members]
        frequency = sum(m[2] for m in members)
        entity_type = members[0][1]
        canonical_name = max(names, key=lambda n: (max(m[2] for m in members if m[0] == n), len(n), n))
        resolved[canonical_name] = {
            "type": entity_type,
            "surface_forms": names,
            "total_frequency": frequency,
        }
    return resolved, decisions


resolved, decisions = resolve_entities(SURFACE_FORMS, ALIAS_MAP)

for name, method, canonical_key in decisions:
    print(f"  {name!r:16} -> {method:14} -> key {canonical_key!r}")
print(f"resolved entity count    : {len(resolved)} of {len(SURFACE_FORMS)} surface forms")
for canonical_name, info in sorted(resolved.items()):
    print(
        f"  {canonical_name}: type={info['type']}, "
        f"forms={len(info['surface_forms'])}, freq={info['total_frequency']}"
    )
```

Output —

```text
  'Neo4j Inc.'     -> alias          -> key 'neo4j inc'
  'Neo4j'          -> alias          -> key 'neo4j inc'
  'Neo4j Inc'      -> alias          -> key 'neo4j inc'
  'Emil Eifrem'    -> new            -> key 'emil eifrem'
  'E. Eifrem'      -> alias          -> key 'emil eifrem'
  'Sweeden'        -> new            -> key 'sweeden'
  'Sweden'         -> fuzzy(0.923)   -> key 'sweeden'
resolved entity count    : 3 of 7 surface forms
  Emil Eifrem: type=PERSON, forms=2, freq=6
  Neo4j Inc.: type=ORGANIZATION, forms=3, freq=12
  Sweden: type=LOCATION, forms=2, freq=5
```

ဤ output သည် `lab.py` ၏ Exercise 4 output နှင့် တူညီသည်။

---

## 10. ကိုယ်တိုင်လေ့ကျင့်ကြည့်ပါ

**မေးခွန်း** — အောက်ပါ code က `normalize_surface` ၏ ရလဒ်ကို ဘယ်လို ပြမလဲ။

```python
for value in ("Neo4j_Inc", "Neo4j-Inc", "Neo4j Inc"):
    print(repr(normalize_surface(value)))
```

1. `'neo4j_inc'`၊ `'neo4jinc'`၊ `'neo4j inc'`
2. `'neo4jinc'`၊ `'neo4jinc'`၊ `'neo4j inc'`
3. သုံးခုလုံး `'neo4j inc'`
4. `'neo4j_inc'`၊ `'neo4j_inc'`၊ `'neo4j inc'`

<details>
<summary>အဖြေ ကြည့်ရန်</summary>

**အဖြေ — 1. `'neo4j_inc'`၊ `'neo4jinc'`၊ `'neo4j inc'`**

အကြောင်းရင်း — `[^\w\s]` ဖြတ်သည့် pattern တွင် `\w` သည် **underscore `_` ကို
ပါဝင်**သည်။ ထို့ကြောင့် `Neo4j_Inc` တွင် `_` ကျန်ခဲ့ပြီး `neo4j_inc` ဖြစ်သည်။
`Neo4j-Inc` တွင် `-` သည် `\w` မဟုတ်၊ `\s` မဟုတ်သဖြင့် ဖြတ်ခံရပြီး `neo4jinc`
ဖြစ်သည် (`_` မရှိသဖြင့် စာလုံးများ ကပ်သွားသည်)။ `Neo4j Inc` တွင် space ရှိသဖြင့်
`neo4j inc` ဖြစ်သည်။

ဤအချက်က **underscore နှင့် hyphen ကို မတူညီစွာ ကိုင်တွယ်သည်** ဆိုသည့်
အရေးကြီးသော ကန့်သတ်ချက်ကို ပြသည် — entity အမည်များတွင် underscore ပါလာလျှင်
(feature flag သို့မဟုတ် cluster အမည်များ) normalization အပြုအမူ ကွာနိုင်သည်။

</details>

---

**အဓိက မှတ်ထားရန်** — Alias mapping ကို fuzzy အရင် run ခြင်းသည် precision ကို
ကာကွယ်သည်။ Fuzzy matching သည် `Sweeden`/`Sweden` (0.923) ကဲ့သို့ typo ကို
ဖမ်းသည်; သို့သော် `E. Eifrem`/`Emil Eifrem` (0.842) ကဲ့သို့ abbreviation ကို
**threshold 0.85 တွင် မဖမ်းနိုင်ပါ** — ထိုအတွက် alias list မဖြစ်မနေ လိုသည်။
Threshold ကို လျှော့ခြင်းသည် abbreviation ကို ကယ်နိုင်သော်လည်း false positive
များ ဝင်လာစေနိုင်သည်။ Canonical name ကို frequency ဖြင့် ရွေးပြီး
length/lexicographic ဖြင့် tie-break လုပ်ခြင်းသည် run တိုင်း တူညီသော
ရလဒ် ရစေသည်။
