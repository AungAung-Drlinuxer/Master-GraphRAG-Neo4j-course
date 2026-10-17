# Walkthrough 03 — Map-Reduce triple aggregation (Exercise 3)

> ဤဖိုင်သည် Module 03 ၏ `solution.md` ထဲက Exercise 3 ကို **Python အခြေခံမှ စ၍**
> အပိုင်းလိုက် ရှင်းပြသည့် walkthrough ဖြစ်သည်။

---

## 0. ဤ Exercise က ဘာကို ဖြေရှင်းပေးသလဲ။

Corpus အရွယ်အစား ကြီးလာသည့်အခါ chunk အားလုံးကို တစ်ကြိမ်တည်း extract လုပ်ခြင်းသည်
မဖြစ်နိုင်တော့ပါ (memory၊ throughput၊ retry granularity)။ **Map-Reduce** pattern သည်
ဤအလုပ်ကို အဆင့်နှစ်ဆင့် ခွဲသည် —

```text
                 Map phase (chunk တစ်ခုချင်း၊ သီးခြား/parallel)
  chunk 0  ->  extract_triples  ->  [ (Alpha,acquired,Beta), (Beta,operates,Gamma) ]
  chunk 1  ->  extract_triples  ->  [ (Gamma,founded,Delta), (Delta,partners,Epsilon) ]
  chunk 2  ->  extract_triples  ->  [ (Epsilon,supplies,Zeta), (Zeta,acquired,Alpha) ]
                    |
                    v   record တိုင်းတွင် source chunk_hash ကို ထည့်
                 Reduce phase (merge_triples)
                    |
                    v
  unique triples 6   (freq၊ sources၊ confidence ဖြင့်)
```

Map phase သည် **stateless** ဖြစ်သဖြင့် worker အများအပြားဖြင့် run နိုင်သည်။ Reduce phase
တွင်သာ အားလုံးကို စုစည်းသည်။ Record တိုင်းတွင် `chunk_hash` ကို သိမ်းခြင်းဖြင့် triple
တိုင်း၏ မူလ chunk ကို ပြန်ခြေရာခံနိုင်သည် (provenance)။

ဤ code မှာ လေ့လာရမည့် Python concepts များမှာ —

- `frozenset` နှင့် membership test (`in`)
- `enumerate()` နှင့် chained comparison `0 < i < len(words) - 1`
- Tuple အဖြစ် triple သိမ်းခြင်း
- Dict literal ဖြင့် record ဖန်တီးခြင်း
- `hashlib.sha1(...).hexdigest()[:8]`
- `dict.setdefault()`
- `tuple(part.lower() ...)` generator expression
- `min()`၊ `round()`၊ `f"..."` မဟုတ်သော `%` formatting
- `sorted(dict)` ဖြင့် key များကို စီခြင်း

---

## 1. `VERBS` နှင့် `ENTITIES` — `frozenset`

```python
VERBS = frozenset({"acquired", "operates", "founded", "partners", "supplies"})
print("acquired" in VERBS)
print("Acquired" in VERBS)
print(type(VERBS))
print(len(VERBS))
print(sorted(VERBS))
```

Output —

```text
True
False
<class 'frozenset'>
5
['acquired', 'founded', 'operates', 'partners', 'supplies']
```

`{...}` သည် **set** ဖြစ်သည် — ထပ်တူတန်ဖိုး မရှိသော အစုအဝေး။ `frozenset` သည် ပြင်လို့မရသော
(immutable) set ဖြစ်သဖြင့် function ၏ default argument အဖြစ် သုံးနိုင်သည်။ `x in VERBS` သည်
membership test ဖြစ်ပြီး set တွင် အလွန်မြန်သည် (O(1))။

`"Acquired" in VERBS` သည် `False` ဖြစ်သည် — set ၏ membership သည် **case-sensitive** ဖြစ်သည်။
ဤအချက်သည် နောက်ပိုင်း `triple_key` တွင် case-fold လုပ်ရသည့် အကြောင်းရင်း ဖြစ်သည်။

`frozenset` ကို တိုက်ရိုက် print လျှင် ၎င်း၏ ပြသအစီအစဉ်သည် run တစ်ခုနှင့်တစ်ခု **ကွဲနိုင်သည်**
(hash randomization)။ ဒါကြောင့် အထက်တွင် `sorted(VERBS)` ကို သုံးထားသည်။

---

## 2. `extract_triples()` — Map Phase ၏ အူတိုင်

```python
VERBS = frozenset({"acquired", "operates", "founded", "partners", "supplies"})
ENTITIES = frozenset({"Alpha", "Beta", "Gamma", "Delta", "Epsilon", "Zeta"})


def extract_triples(words, verbs=VERBS, entities=ENTITIES):
    triples = []
    for i, token in enumerate(words):
        if token in verbs and 0 < i < len(words) - 1:
            subj, obj = words[i - 1], words[i + 1]
            if subj in entities and obj in entities:
                triples.append((subj, token, obj))
    return triples


chunk0 = ["Alpha", "acquired", "Beta", "Beta", "operates", "Gamma"]
print(extract_triples(chunk0))
print(len(extract_triples(chunk0)))
```

Output —

```text
[('Alpha', 'acquired', 'Beta'), ('Beta', 'operates', 'Gamma')]
2
```

Function ၏ လုပ်ငန်းစဉ် —

| အစဉ် | အပိုင်း | အဓိပ္ပာယ် |
| --- | --- | --- |
| 1 | `for i, token in enumerate(words)` | index နှင့် token ကို တစ်ပြိုင်နက် ရသည် |
| 2 | `token in verbs` | token သည် verb ဖြစ်မဖြစ် |
| 3 | `0 < i < len(words) - 1` | ရှေ့နှင့် နောက် token နှစ်ဖက်လုံး ရှိမရှိ |
| 4 | `subj, obj = words[i - 1], words[i + 1]` | verb ၏ ဝဲ/ယာ token ကို ယူသည် |
| 5 | `subj in entities and obj in entities` | နှစ်ဖက်လုံး entity ဖြစ်မဖြစ် |
| 6 | `triples.append((subj, token, obj))` | `(subject, predicate, object)` tuple ထည့် |

လိုင်း ၅ သည် **"subject နှင့် object သည် chunk တစ်ခုတည်းအတွင်း ရှိရမည်"** ဆိုသည့်
constraint ဖြစ်သည်။ `chunk0` တွင် `Phi` ကဲ့သို့ entity မဟုတ်သော token ပါလျှင် triple
အရေအတွက် လျော့မည်။

### `enumerate()` နှင့် index guard

```python
words = ["acquired", "Alpha", "Beta", "operates"]
for i, token in enumerate(words):
    print("i=%d token=%-9s inside_guard=%s" % (i, token, 0 < i < len(words) - 1))
```

Output —

```text
i=0 token=acquired  inside_guard=False
i=1 token=Alpha     inside_guard=True
i=2 token=Beta      inside_guard=True
i=3 token=operates  inside_guard=False
```

`0 < i < len(words) - 1` သည် `(0 < i) and (i < len(words) - 1)` ဖြစ်သည်။ `i=0` နှင့်
`i=len-1` တို့တွင် guard သည် `False` ဖြစ်သည် — အကြောင်းရင်းမှာ ထို အစွန်း index နှစ်ခုတွင်
`words[i - 1]` သို့မဟုတ် `words[i + 1]` သည် list ပြင်ပ ရောက်နိုင်သဖြင့်ပါ။

---

## 3. Guard မရှိပါက — Wrap-around နှင့် `IndexError`

Guard ကို ဖျောက်ကြည့်လျှင် bug နှစ်မျိုး ပေါ်လာသည်။

```python
VERBS = frozenset({"acquired", "operates", "founded", "partners", "supplies"})
ENTITIES = frozenset({"Alpha", "Beta", "Gamma"})


def extract_no_guard(words):
    triples = []
    for i, token in enumerate(words):
        if token in VERBS:                     # index guard မရှိ
            subj, obj = words[i - 1], words[i + 1]
            if subj in ENTITIES and obj in ENTITIES:
                triples.append((subj, token, obj))
    return triples


print("words[-1] (wrap-around) :", ["acquired", "Alpha", "Beta"][-1])
print("naive on verb-first list:", extract_no_guard(["acquired", "Alpha", "Beta"]))
try:
    print(extract_no_guard(["Alpha", "acquired", "Beta", "operates"]))
except IndexError as exc:
    print("naive on verb-last list : IndexError:", exc)
```

Output —

```text
words[-1] (wrap-around) : Beta
naive on verb-first list: [('Beta', 'acquired', 'Alpha')]
naive on verb-last list : IndexError: list index out of range
```

Trap နှစ်ခု —

- **Verb က ပထမ token ဖြစ်လျှင်** — `words[i - 1]` က `words[-1]` ဖြစ်သည်။ Python ၏
  negative index ကြောင့် error မဖြစ်ဘဲ **နောက်ဆုံး token** ကို ယူသည် (wrap-around)။
  ထို့ကြောင့် `('Beta', 'acquired', 'Alpha')` ဆိုသည့် **phantom triple** ထွက်လာသည်။
- **Verb က နောက်ဆုံး token ဖြစ်လျှင်** — `words[i + 1]` သည် list ပြင်ပ ရောက်သဖြင့်
  `IndexError` ဖြစ်သည်။

Guard သည် ဤနှစ်မျိုးလုံးကို တစ်ပြိုင်နက် ကာကွယ်သည်။

---

## 4. `chunk_hash()` — Provenance

```python
import hashlib


def chunk_hash(words):
    return hashlib.sha1(" ".join(words).encode("utf-8")).hexdigest()[:8]


chunks = [
    ["Alpha", "acquired", "Beta", "Beta", "operates", "Gamma"],
    ["Gamma", "founded", "Delta", "Delta", "partners", "Epsilon"],
    ["Epsilon", "supplies", "Zeta", "Zeta", "acquired", "Alpha"],
]
for c in chunks:
    print("%s  %s" % (chunk_hash(c), " ".join(c)))
print("stable across calls:", chunk_hash(chunks[0]) == chunk_hash(chunks[0]))
```

Output —

```text
6d43dca0  Alpha acquired Beta Beta operates Gamma
16f213ff  Gamma founded Delta Delta partners Epsilon
2e403250  Epsilon supplies Zeta Zeta acquired Alpha
stable across calls: True
```

`hashlib.sha1(data).hexdigest()` သည် ၄၀ လုံး hex digest ကို ပြန်သည်။ `[:8]` သည်
**ပထမ ၈ လုံး** ကို ယူသဖြင့် ဖတ်ရလွယ်သော short id ဖြစ်သည်။ `.encode("utf-8")` သည်
string ကို bytes သို့ ပြောင်းသည် (`hashlib` သည် bytes သာ လက်ခံသည်)။

Chunk ၏ **အကြောင်းအရာ** တူညီလျှင် hash တူညီသည် (stable)။ ဤအချက်ကြောင့် hash ကို
checkpoint key၊ dedup key နှင့် provenance အတွက် သုံးနိုင်သည်။ Chunk အကြောင်းအရာ ပြောင်းလျှင်
hash ပြောင်းသည်ကို `" ".join(words)` အပိုင်းက သေချာစေသည်။

---

## 5. Map Phase — Record များ စုစည်းခြင်း

```python
import re
import hashlib

CORPUS = (
    "Alpha acquired Beta . Beta operates Gamma . Gamma founded Delta . "
    "Delta partners Epsilon . Epsilon supplies Zeta . Zeta acquired Alpha ."
)
VERBS = frozenset({"acquired", "operates", "founded", "partners", "supplies"})
ENTITIES = frozenset({"Alpha", "Beta", "Gamma", "Delta", "Epsilon", "Zeta"})


def tokenize(text):
    return re.findall(r"[A-Za-z]+", text)


def chunk_words(words, size, overlap):
    stride = size - overlap
    n, start, chunks = len(words), 0, []
    while start < n:
        chunks.append(words[start:start + size])
        if start + size >= n:
            break
        start += stride
    return chunks


def chunk_hash(words):
    return hashlib.sha1(" ".join(words).encode("utf-8")).hexdigest()[:8]


def extract_triples(words, verbs=VERBS, entities=ENTITIES):
    triples = []
    for i, token in enumerate(words):
        if token in verbs and 0 < i < len(words) - 1:
            subj, obj = words[i - 1], words[i + 1]
            if subj in entities and obj in entities:
                triples.append((subj, token, obj))
    return triples


words = tokenize(CORPUS)
chunks = chunk_words(words, size=6, overlap=0)
records = []
for c in chunks:
    for triple in extract_triples(c):
        records.append({"s": triple[0], "p": triple[1], "o": triple[2],
                        "chunk_hash": chunk_hash(c)})
print("raw records:", len(records))
for r in records:
    print("  %-8s %-9s %-8s %s" % (r["s"], r["p"], r["o"], r["chunk_hash"]))
```

Output —

```text
raw records: 6
  Alpha    acquired  Beta     6d43dca0
  Beta     operates  Gamma    6d43dca0
  Gamma    founded   Delta    16f213ff
  Delta    partners  Epsilon  16f213ff
  Epsilon  supplies  Zeta     2e403250
  Zeta     acquired  Alpha    2e403250
```

Nested loop နှစ်ခုဖြစ်သည် — အပြင်က chunk များ၊ အတွင်းက ထို chunk ၏ triple များ။ Record
တိုင်းတွင် `chunk_hash(c)` ကို ထည့်သဖြင့် triple တစ်ခုစီ၏ source ကို ပြန်ခြေရာခံနိုင်သည်
(ဤနေရာတွင် chunk 0 ၏ triple နှစ်ခုလုံး `6d43dca0` ကို မျှဝေသည်)။

### Record သည် dict တစ်ခု

```python
triple = ("Alpha", "acquired", "Beta")
record = {"s": triple[0], "p": triple[1], "o": triple[2], "chunk_hash": "a1b2c3d4"}
print(record)
print(record["s"], record["p"], record["o"])
```

Output —

```text
{'s': 'Alpha', 'p': 'acquired', 'o': 'Beta', 'chunk_hash': 'a1b2c3d4'}
Alpha acquired Beta
```

Dict သည် key → value မြေပုံဖြစ်သည်။ Tuple ၏ element များကို `triple[0]`, `triple[1]`,
`triple[2]` ဖြင့် ဖွင့်ယူသည်။

---

## 6. `merge_triples()` — Reduce Phase

```python
def triple_key(triple):
    return tuple(part.lower() for part in triple)


def merge_triples(records):
    merged = {}
    for rec in records:
        key = triple_key((rec["s"], rec["p"], rec["o"]))
        entry = merged.setdefault(key, {"s": rec["s"], "p": rec["p"], "o": rec["o"],
                                        "sources": [], "freq": 0})
        if rec["chunk_hash"] not in entry["sources"]:
            entry["sources"].append(rec["chunk_hash"])
        entry["freq"] += 1
    for entry in merged.values():
        entry["sources"].sort()
        entry["confidence"] = round(min(1.0, 0.5 + 0.25 * entry["freq"]), 2)
    return merged


records = [
    {"s": "Alpha", "p": "acquired", "o": "Beta", "chunk_hash": "aaaaaaaa"},
    {"s": "alpha", "p": "acquired", "o": "beta", "chunk_hash": "bbbbbbbb"},
    {"s": "Gamma", "p": "founded", "o": "Delta", "chunk_hash": "cccccccc"},
]
merged = merge_triples(records)
for key in sorted(merged):
    e = merged[key]
    print(key, "->", {"s": e["s"], "freq": e["freq"], "sources": e["sources"], "confidence": e["confidence"]})
```

Output —

```text
('alpha', 'acquired', 'beta') -> {'s': 'Alpha', 'freq': 2, 'sources': ['aaaaaaaa', 'bbbbbbbb'], 'confidence': 1.0}
('gamma', 'founded', 'delta') -> {'s': 'Gamma', 'freq': 1, 'sources': ['cccccccc'], 'confidence': 0.75}
```

### `triple_key()` — Case Fold

`tuple(part.lower() for part in triple)` သည် triple ၏ အပိုင်းသုံးခုကို စာလုံးအသေးသို့
ပြောင်းပြီး tuple အသစ် ဖန်တီးသည်။ ဒါကြောင့် `("Alpha","acquired","Beta")` နှင့်
`("alpha","acquired","beta")` သည် **key တူညီ** သည်။ `freq=2` ဖြစ်ပြီး `s` field တွင်
**ပထမ တွေ့ခဲ့သော** surface form (`Alpha`) ကို ထိန်းထားသည်။

### `dict.setdefault()`

`merged.setdefault(key, default)` သည် —

- `key` မရှိလျှင် `default` ကို ထည့်ပြီး ထို value ကို **ပြန်ပေးသည်**။
- `key` ရှိပြီးသားလျှင် လက်ရှိ value ကို ပြန်ပေးသည် (default ကို မထည့်)။

ဒါကြောင့် လိုင်းတစ်လိုင်းတည်းဖြင့် "မရှိရင် အသစ်ဖန်တီး၊ ရှိရင် လက်ရှိကို ယူ" ဆိုသည့်
အလုပ်နှစ်ခုလုံး ပြီးသည်။ `merged.get(key)` ဖြင့် ရေးလျှင် `None` ဖြစ်သည့်အခါ အသစ်ဖန်တီးရန်
if လိုသည် — `setdefault` က ပိုတို သည်။

### `sources` နှင့် `confidence`

- `if rec["chunk_hash"] not in entry["sources"]` — ထပ်တူ chunk မှ ထပ်တူ hash ကို
  တစ်ခါသာ ထည့်သည်။
- `entry["sources"].sort()` — list ကို အစီအစဉ်တကျ စီသည် (deterministic output အတွက်)။
- `confidence = round(min(1.0, 0.5 + 0.25 * freq), 2)` — freq ၁ အတွက် 0.75၊ freq ၂ အတွက်
  `0.5 + 0.5 = 1.0`။ `min(1.0, ...)` က 1.0 ထက် မကျော်စေရန် ကာကွယ်သည်။

---

## 7. Per-chunk Triple Count Table

```python
import re

CORPUS = (
    "Alpha acquired Beta . Beta operates Gamma . Gamma founded Delta . "
    "Delta partners Epsilon . Epsilon supplies Zeta . Zeta acquired Alpha ."
)
VERBS = frozenset({"acquired", "operates", "founded", "partners", "supplies"})
ENTITIES = frozenset({"Alpha", "Beta", "Gamma", "Delta", "Epsilon", "Zeta"})


def tokenize(text):
    return re.findall(r"[A-Za-z]+", text)


def chunk_words(words, size, overlap):
    stride = size - overlap
    n, start, chunks = len(words), 0, []
    while start < n:
        chunks.append(words[start:start + size])
        if start + size >= n:
            break
        start += stride
    return chunks


def extract_triples(words, verbs=VERBS, entities=ENTITIES):
    triples = []
    for i, token in enumerate(words):
        if token in verbs and 0 < i < len(words) - 1:
            subj, obj = words[i - 1], words[i + 1]
            if subj in entities and obj in entities:
                triples.append((subj, token, obj))
    return triples


words = tokenize(CORPUS)
chunks = chunk_words(words, size=6, overlap=0)
per_chunk = []
for c in chunks:
    mapped = extract_triples(c)
    per_chunk.append(len(mapped))
    print("  %-42s -> %d" % (" ".join(c), len(mapped)))
print("per-chunk counts:", per_chunk)
```

Output —

```text
  Alpha acquired Beta Beta operates Gamma    -> 2
  Gamma founded Delta Delta partners Epsilon -> 2
  Epsilon supplies Zeta Zeta acquired Alpha  -> 2
per-chunk counts: [2, 2, 2]
```

| Chunk | Content | Triples |
| --- | --- | --- |
| 0 | `Alpha acquired Beta Beta operates Gamma` | `(Alpha,acquired,Beta)`, `(Beta,operates,Gamma)` |
| 1 | `Gamma founded Delta Delta partners Epsilon` | `(Gamma,founded,Delta)`, `(Delta,partners,Epsilon)` |
| 2 | `Epsilon supplies Zeta Zeta acquired Alpha` | `(Epsilon,supplies,Zeta)`, `(Zeta,acquired,Alpha)` |

Chunk တိုင်း triple ၂ ခု၊ စုစုပေါင်း ၆ ခု။ Chunk တိုင်း၏ ဝါကျ ၂ ခုစလုံးသည် chunk
အတွင်းမှာ အပြည့်အစုံ ပါဝင်သဖြင့် boundary ပြတ်တောက်မှု မရှိပါ (size=6 သည် ဝါကျနှစ်ခုနှင့်
တိတိကျကျ ကိုက်ညီသည်)။

---

## 8. Reduce ရလဒ် အပြည့်အစုံ

```python
import re
import hashlib

CORPUS = (
    "Alpha acquired Beta . Beta operates Gamma . Gamma founded Delta . "
    "Delta partners Epsilon . Epsilon supplies Zeta . Zeta acquired Alpha ."
)
VERBS = frozenset({"acquired", "operates", "founded", "partners", "supplies"})
ENTITIES = frozenset({"Alpha", "Beta", "Gamma", "Delta", "Epsilon", "Zeta"})


def tokenize(text):
    return re.findall(r"[A-Za-z]+", text)


def chunk_words(words, size, overlap):
    stride = size - overlap
    n, start, chunks = len(words), 0, []
    while start < n:
        chunks.append(words[start:start + size])
        if start + size >= n:
            break
        start += stride
    return chunks


def chunk_hash(words):
    return hashlib.sha1(" ".join(words).encode("utf-8")).hexdigest()[:8]


def extract_triples(words, verbs=VERBS, entities=ENTITIES):
    triples = []
    for i, token in enumerate(words):
        if token in verbs and 0 < i < len(words) - 1:
            subj, obj = words[i - 1], words[i + 1]
            if subj in entities and obj in entities:
                triples.append((subj, token, obj))
    return triples


def triple_key(triple):
    return tuple(part.lower() for part in triple)


def merge_triples(records):
    merged = {}
    for rec in records:
        key = triple_key((rec["s"], rec["p"], rec["o"]))
        entry = merged.setdefault(key, {"s": rec["s"], "p": rec["p"], "o": rec["o"],
                                        "sources": [], "freq": 0})
        if rec["chunk_hash"] not in entry["sources"]:
            entry["sources"].append(rec["chunk_hash"])
        entry["freq"] += 1
    for entry in merged.values():
        entry["sources"].sort()
        entry["confidence"] = round(min(1.0, 0.5 + 0.25 * entry["freq"]), 2)
    return merged


words = tokenize(CORPUS)
chunks = chunk_words(words, size=6, overlap=0)
records = []
for c in chunks:
    for triple in extract_triples(c):
        records.append({"s": triple[0], "p": triple[1], "o": triple[2],
                        "chunk_hash": chunk_hash(c)})
merged = merge_triples(records)
print("unique triples %d" % len(merged))
for key in sorted(merged):
    e = merged[key]
    print("  (%s) -[%s]-> (%s) freq=%d" % (e["s"], e["p"], e["o"], e["freq"]))
```

Output —

```text
unique triples 6
  (Alpha) -[acquired]-> (Beta) freq=1
  (Beta) -[operates]-> (Gamma) freq=1
  (Delta) -[partners]-> (Epsilon) freq=1
  (Epsilon) -[supplies]-> (Zeta) freq=1
  (Gamma) -[founded]-> (Delta) freq=1
  (Zeta) -[acquired]-> (Alpha) freq=1
```

`sorted(merged)` သည် dict ၏ key များကို (case-folded tuple) အက္ခရာအစဉ်ဖြင့် စီသည်။
ဤနေရာတွင် `freq` အားလုံး ၁ ဖြစ်သည် — overlap=0 ဖြစ်သဖြင့် triple တစ်ခုမျှ ထပ်မထွက်ပါ။

---

## 9. Code တစ်ခုလုံး — Run လုပ်နိုင်သော Version

```python
import hashlib
import re

CORPUS = (
    "Alpha acquired Beta . Beta operates Gamma . Gamma founded Delta . "
    "Delta partners Epsilon . Epsilon supplies Zeta . Zeta acquired Alpha ."
)
VERBS = frozenset({"acquired", "operates", "founded", "partners", "supplies"})
ENTITIES = frozenset({"Alpha", "Beta", "Gamma", "Delta", "Epsilon", "Zeta"})


def tokenize(text):
    return re.findall(r"[A-Za-z]+", text)


def chunk_words(words, size, overlap):
    stride = size - overlap
    n, start, chunks = len(words), 0, []
    while start < n:
        chunks.append(words[start:start + size])
        if start + size >= n:
            break
        start += stride
    return chunks


def chunk_hash(words):
    return hashlib.sha1(" ".join(words).encode("utf-8")).hexdigest()[:8]


def extract_triples(words, verbs=VERBS, entities=ENTITIES):
    triples = []
    for i, token in enumerate(words):
        if token in verbs and 0 < i < len(words) - 1:
            subj, obj = words[i - 1], words[i + 1]
            if subj in entities and obj in entities:
                triples.append((subj, token, obj))
    return triples


def triple_key(triple):
    return tuple(part.lower() for part in triple)


def merge_triples(records):
    merged = {}
    for rec in records:
        key = triple_key((rec["s"], rec["p"], rec["o"]))
        entry = merged.setdefault(key, {"s": rec["s"], "p": rec["p"], "o": rec["o"],
                                        "sources": [], "freq": 0})
        if rec["chunk_hash"] not in entry["sources"]:
            entry["sources"].append(rec["chunk_hash"])
        entry["freq"] += 1
    for entry in merged.values():
        entry["sources"].sort()
        entry["confidence"] = round(min(1.0, 0.5 + 0.25 * entry["freq"]), 2)
    return merged


words = tokenize(CORPUS)
chunks = chunk_words(words, size=6, overlap=0)
records, per_chunk = [], []
for c in chunks:
    mapped = extract_triples(c)
    per_chunk.append(len(mapped))
    for triple in mapped:
        records.append({"s": triple[0], "p": triple[1], "o": triple[2],
                        "chunk_hash": chunk_hash(c)})
merged = merge_triples(records)
print("map phase   : per-chunk triple counts %s" % per_chunk)
print("map phase   : raw records %d" % len(records))
print("reduce phase: unique triples %d" % len(merged))
for key in sorted(merged):
    e = merged[key]
    print("  (%s) -[%s]-> (%s) freq=%d" % (e["s"], e["p"], e["o"], e["freq"]))
```

Output —

```text
map phase   : per-chunk triple counts [2, 2, 2]
map phase   : raw records 6
reduce phase: unique triples 6
  (Alpha) -[acquired]-> (Beta) freq=1
  (Beta) -[operates]-> (Gamma) freq=1
  (Delta) -[partners]-> (Epsilon) freq=1
  (Epsilon) -[supplies]-> (Zeta) freq=1
  (Gamma) -[founded]-> (Delta) freq=1
  (Zeta) -[acquired]-> (Alpha) freq=1
```

---

## 10. ကိုယ်တိုင်လေ့ကျင့်ကြည့်ပါ

**မေးခွန်း** — အောက်ပါ chunk ကို `extract_triples()` ဖြင့် run လျှင် triple ဘယ်နှစ်ခု
ထွက်မလဲ။ `["operates", "Gamma", "Gamma", "founded", "Delta", "Delta"]`

1. ၃ ခု
2. ၂ ခု
3. ၁ ခု
4. ၀ ခု

<details>
<summary>အဖြေ ကြည့်ရန်</summary>

**အဖြေ — 3. ၁ ခု**

```python
VERBS = frozenset({"acquired", "operates", "founded", "partners", "supplies"})
ENTITIES = frozenset({"Alpha", "Beta", "Gamma", "Delta", "Epsilon", "Zeta"})


def extract_triples(words, verbs=VERBS, entities=ENTITIES):
    triples = []
    for i, token in enumerate(words):
        if token in verbs and 0 < i < len(words) - 1:
            subj, obj = words[i - 1], words[i + 1]
            if subj in entities and obj in entities:
                triples.append((subj, token, obj))
    return triples


print(extract_triples(["Beta", "operates", "Gamma", "Gamma", "founded", "Delta"]))
print(extract_triples(["operates", "Gamma", "Gamma", "founded", "Delta", "Delta"]))
```

Output —

```text
[('Beta', 'operates', 'Gamma'), ('Gamma', 'founded', 'Delta')]
[('Gamma', 'founded', 'Delta')]
```

အကြောင်းရင်း — ဒုတိယ list တွင် ပထမ token `operates` သည် verb ဖြစ်သော်လည်း `i=0`
ဖြစ်သဖြင့် guard `0 < i` က ပိတ်ထားသည်။ ဒါကြောင့် `('Delta','operates','Gamma')`
ဆိုသည့် phantom triple မထွက်ပါ။ `founded` (i=4) တွင်သာ triple တစ်ခု ထွက်သည်။
Guard မရှိပါက ပထမ guard case က `words[-1] = 'Delta'` ကို wrap-around ယူပြီး
phantom triple ထပ်ထွက်မည်။

</details>

---

**အဓိက မှတ်ထားရန်** — Map-Reduce pattern သည် extraction ကို chunk တိုင်းအတွက် သီးခြား
(map) လုပ်ပြီး နောက်ဆုံးမှ စုစည်း (reduce) သည်။ `extract_triples` ၏ index guard
`0 < i < len(words) - 1` သည် wrap-around phantom triple နှင့် `IndexError` နှစ်မျိုးလုံးကို
ကာကွယ်သည်။ Record တိုင်းတွင် `chunk_hash` ထည့်ခြင်းဖြင့် provenance ကို မဆုံးရှုံးစေရန်
လိုသည်။ `merge_triples` တွင် key ကို case-fold လုပ်သဖြင့် `Alpha`/`alpha` ကဲ့သို့
မျက်နှာပြင်ကွဲပြားမှုကို ပေါင်းနိုင်သည် — ဤအလုပ်သည် နောက်ပိုင်း entity resolution ၏
အခြေခံဖြစ်သည်။
