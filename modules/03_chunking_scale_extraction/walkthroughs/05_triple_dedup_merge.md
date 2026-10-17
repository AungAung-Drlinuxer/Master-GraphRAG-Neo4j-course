# Walkthrough 05 — Triple deduplication နှင့် merge (Exercise 5)

> ဤဖိုင်သည် Module 03 ၏ `solution.md` ထဲက Exercise 5 ကို **Python အခြေခံမှ စ၍**
> အပိုင်းလိုက် ရှင်းပြသည့် walkthrough ဖြစ်သည်။

---

## 0. ဤ Exercise က ဘာကို ဖြေရှင်းပေးသလဲ။

Overlap သည် boundary relationship များကို ကယ်ပေမဲ့ **triple တူတူကို အကြိမ်များစွာ** ထုတ်လာစေသည်။
Chunk နှစ်ခုတွင် `Gamma founded Delta` ပါလျှင် ထို triple သည် raw record နှစ်ခု ဖြစ်လာသည်။

```text
  chunk 2: operates Gamma Gamma founded Delta      -> (Gamma, founded, Delta)
  chunk 3: Gamma founded Delta Delta partners      -> (Gamma, founded, Delta)   dup!
                 |
                 v   merge_triples (Reduce)
      key = ("gamma","founded","delta")  ->  freq = 2
                                          sources = [hash2, hash3]
                                          confidence = min(1.0, 0.5 + 0.25*2) = 1.0
```

**Deduplication** သည် အကြောင်းအရာတူ triple များကို တစ်ခုတည်း ပေါင်းပြီး၊ **merge** သည်
ထို triple ကို ဘယ် chunk များမှ ရခဲ့သည် (`sources`) နှင့် အကြိမ်မည်မျှ ထွက်ခဲ့သည်
(`freq`) ကို မှတ်တမ်းတင်သည်။ Neo4j တွင် ဤအလုပ်သည် `MERGE` ၏ semantics ဖြစ်သည်။

ဤ code မှာ လေ့လာရမည့် Python concepts များမှာ —

- Overlap ကြောင့် raw record အရေအတွက် တိုးလာခြင်း
- Tuple key ဖြင့် dict အသုံးပြုခြင်း
- `tuple(part.lower() for part in triple)`
- `dict.setdefault()` နှင့် `entry["freq"] += 1`
- List membership (`not in`) နှင့် `sort()`
- `round()` နှင့် `min()`
- `sorted()` ဖြင့် dict key စီခြင်း
- List comprehension ဖြင့် condition filter

---

## 1. `size=5, overlap=3` — Chunk ဖွဲ့စည်းပုံ

```python
import re

CORPUS = (
    "Alpha acquired Beta . Beta operates Gamma . Gamma founded Delta . "
    "Delta partners Epsilon . Epsilon supplies Zeta . Zeta acquired Alpha ."
)


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


words = tokenize(CORPUS)
chunks = chunk_words(words, size=5, overlap=3)
print("chunk count: %d" % len(chunks))
for i, c in enumerate(chunks):
    print("  chunk %d: %s" % (i, " ".join(c)))
```

Output —

```text
chunk count: 8
  chunk 0: Alpha acquired Beta Beta operates
  chunk 1: Beta Beta operates Gamma Gamma
  chunk 2: operates Gamma Gamma founded Delta
  chunk 3: Gamma founded Delta Delta partners
  chunk 4: Delta Delta partners Epsilon Epsilon
  chunk 5: partners Epsilon Epsilon supplies Zeta
  chunk 6: Epsilon supplies Zeta Zeta acquired
  chunk 7: Zeta Zeta acquired Alpha
```

`stride = 5 - 3 = 2` ဖြစ်သဖြင့် chunk ၈ ခု ရသည်။ Chunk တိုင်း token ၅ လုံး (နောက်ဆုံး chunk ၄
လုံး) ဖြစ်ပြီး boundary တိုင်းတွင် token ၃ လုံး ထပ်နေသည်။ ဤထပ်နေမှုကြောင့် ဝါကျတိုင်းသည်
chunk အနည်းဆုံး နှစ်ခုအတွင်း အပြည့်အစုံ ပါဝင်နိုင်သဖြင့် triple များ ထပ်ထွက်လာမည်။

---

## 2. Per-chunk Triple — Raw Record အရေအတွက်

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
chunks = chunk_words(words, size=5, overlap=3)
total = 0
for i, c in enumerate(chunks):
    triples = extract_triples(c)
    total += len(triples)
    print("  chunk %d: %-45s -> %s" % (i, " ".join(c), triples))
print("total raw:", total)
```

Output —

```text
  chunk 0: Alpha acquired Beta Beta operates             -> [('Alpha', 'acquired', 'Beta')]
  chunk 1: Beta Beta operates Gamma Gamma                -> [('Beta', 'operates', 'Gamma')]
  chunk 2: operates Gamma Gamma founded Delta            -> [('Gamma', 'founded', 'Delta')]
  chunk 3: Gamma founded Delta Delta partners            -> [('Gamma', 'founded', 'Delta')]
  chunk 4: Delta Delta partners Epsilon Epsilon          -> [('Delta', 'partners', 'Epsilon')]
  chunk 5: partners Epsilon Epsilon supplies Zeta        -> [('Epsilon', 'supplies', 'Zeta')]
  chunk 6: Epsilon supplies Zeta Zeta acquired           -> [('Epsilon', 'supplies', 'Zeta')]
  chunk 7: Zeta Zeta acquired Alpha                      -> [('Zeta', 'acquired', 'Alpha')]
total raw: 8
```

| Chunk | Triple | မှတ်ချက် |
| --- | --- | --- |
| 0 | `(Alpha, acquired, Beta)` | — |
| 1 | `(Beta, operates, Gamma)` | — |
| 2 | `(Gamma, founded, Delta)` | — |
| 3 | `(Gamma, founded, Delta)` | chunk 2 နှင့် **ထပ်** |
| 4 | `(Delta, partners, Epsilon)` | — |
| 5 | `(Epsilon, supplies, Zeta)` | — |
| 6 | `(Epsilon, supplies, Zeta)` | chunk 5 နှင့် **ထပ်** |
| 7 | `(Zeta, acquired, Alpha)` | — |

Raw record ၈ ခုတွင် triple ထပ်သည့် record ၂ ခု ပါဝင်သဖြင့် unique သည် ၆ သာ ရှိမည်။

---

## 3. `triple_key()` — Case-fold Key

```python
def triple_key(triple):
    return tuple(part.lower() for part in triple)


records = [
    {"s": "Alpha", "p": "acquired", "o": "Beta"},
    {"s": "alpha", "p": "acquired", "o": "beta"},
]
raw_keys = {(r["s"], r["p"], r["o"]) for r in records}
fold_keys = {triple_key((r["s"], r["p"], r["o"])) for r in records}
print("raw keys      :", len(raw_keys))
print("case-fold keys:", len(fold_keys))
print(sorted(raw_keys))
print(sorted(fold_keys))
```

Output —

```text
raw keys      : 2
case-fold keys: 1
[('Alpha', 'acquired', 'Beta'), ('alpha', 'acquired', 'beta')]
[('alpha', 'acquired', 'beta')]
```

`tuple(part.lower() for part in triple)` သည် triple ၏ အပိုင်းတိုင်းကို စာလုံးအသေးသို့
ပြောင်းသည်။ `{... for r in records}` သည် **set comprehension** ဖြစ်သည်။ Raw triple ဖြင့်
key လုပ်လျှင် `Alpha`/`alpha` သည် key နှစ်ခု ဖြစ်နေသည် (raw keys = 2)။ Case-fold ပြီးမှ
key လုပ်လျှင် key တစ်ခုတည်း ဖြစ်သည် (case-fold keys = 1)။ ဒါကြောင့် `merge_triples` သည်
`triple_key` ကို သုံးသည်။

`entry["s"]` တွင် **မူရင်း surface form** (`Alpha`) ကို ထိန်းထားပြီး key တွင်သာ စာလုံးအသေး
ဖြစ်သည်ကို သတိထားပါ — display အမည်နှင့် comparison key ကို ခွဲထားခြင်းဖြစ်သည်။

---

## 4. `merge_triples()` — Reduce Phase ၏ လုပ်ငန်းစဉ်

```python
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
```

လုပ်ငန်းစဉ်ကို အဆင့်လိုက် ဖတ်ကြည့်ပါ —

| အစဉ် | လိုင်း | အဓိပ္ပာယ် |
| --- | --- | --- |
| 1 | `merged = {}` | key → entry dict အသစ် |
| 2 | `key = triple_key(...)` | record ကို case-folded key သို့ ပြောင်း |
| 3 | `merged.setdefault(key, {...})` | key မရှိလျှင် entry အသစ် ဖန်တီး၊ ရှိလျှင် လက်ရှိကို ယူ |
| 4 | `if rec["chunk_hash"] not in entry["sources"]` | ထပ်တူ source hash ကို တစ်ခါသာ ထည့် |
| 5 | `entry["freq"] += 1` | record တိုင်း အကြိမ်ရေ တိုး |
| 6 | `entry["sources"].sort()` | source များကို စီ (deterministic) |
| 7 | `entry["confidence"] = round(min(1.0, 0.5 + 0.25*freq), 2)` | confidence တွက် |

`merged.setdefault(key, default)` သည် dict တွင် `key` မရှိလျှင် `default` ကို ထည့်ပြီး
ပြန်ပေးသည်၊ ရှိပြီးလျှင် လက်ရှိ value ကို ပြန်ပေးသည်။ `entry["freq"] += 1` သည်
`entry["freq"] = entry["freq"] + 1` ၏ အတိုကောက်ဖြစ်သည်။

---

## 5. `confidence` Formula နှင့် `min()` Cap

Formula မှာ `confidence = min(1.0, 0.5 + 0.25 * freq)` ဖြစ်သည်။

```python
for freq in [1, 2, 3, 4, 8]:
    confidence = round(min(1.0, 0.5 + 0.25 * freq), 2)
    print("freq=%d -> confidence=%.2f" % (freq, confidence))
```

Output —

```text
freq=1 -> confidence=0.75
freq=2 -> confidence=1.00
freq=3 -> confidence=1.00
freq=4 -> confidence=1.00
freq=8 -> confidence=1.00
```

| freq | `0.5 + 0.25*freq` | `min(1.0, ...)` | confidence |
| --- | --- | --- | --- |
| 1 | 0.75 | 0.75 | 0.75 |
| 2 | 1.00 | 1.00 | 1.00 |
| 3 | 1.25 | **1.00** | 1.00 |
| 4 | 1.50 | **1.00** | 1.00 |
| 8 | 2.50 | **1.00** | 1.00 |

`min(1.0, x)` သည် x ကို **၁.၀ ထက် မကျော်စေရန်** ကန့်သတ်သည်။ ဤ cap မရှိပါက freq=3 တွင်
`confidence` သည် 1.25 ဖြစ်သွားပြီး "probability" ၏ အဓိပ္ပာယ်ကို ချိုးဖောက်မည်။ `round(x, 2)`
သည် ဒဿမ ၂ လုံးအထိ လှည့်သည်။

---

## 6. Raw 8 → Unique 6 အပြည့်အစုံ

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
chunks = chunk_words(words, size=5, overlap=3)
records = []
for c in chunks:
    chash = chunk_hash(c)
    for triple in extract_triples(c):
        records.append({"s": triple[0], "p": triple[1], "o": triple[2],
                        "chunk_hash": chash})
merged = merge_triples(records)
print("raw records   : %d" % len(records))
print("unique triples: %d" % len(merged))
for key in sorted(merged):
    e = merged[key]
    print("  (%s) -[%s]-> (%s) freq=%d confidence=%.2f sources=%d"
          % (e["s"], e["p"], e["o"], e["freq"], e["confidence"], len(e["sources"])))
```

Output —

```text
raw records   : 8
unique triples: 6
  (Alpha) -[acquired]-> (Beta) freq=1 confidence=0.75 sources=1
  (Beta) -[operates]-> (Gamma) freq=1 confidence=0.75 sources=1
  (Delta) -[partners]-> (Epsilon) freq=1 confidence=0.75 sources=1
  (Epsilon) -[supplies]-> (Zeta) freq=2 confidence=1.00 sources=2
  (Gamma) -[founded]-> (Delta) freq=2 confidence=1.00 sources=2
  (Zeta) -[acquired]-> (Alpha) freq=1 confidence=0.75 sources=1
```

`sorted(merged)` သည် case-folded key များကို စီသဖြင့် အစီအစဉ်သည် deterministic ဖြစ်သည်။
freq=2 ဖြစ်သည့် triple နှစ်ခုသည် confidence 1.00 ရပြီး sources ၂ ခု ရှိသည်။ ကျန် ၄ ခုသည်
freq=1၊ confidence 0.75 ဖြစ်သည်။ Depuplication ratio မှာ `8 / 6 = 1.33` ဖြစ်ပြီး overlap ကြောင့်
ဖြစ်သည့် overhead ကို တိုင်းတာသည်။

---

## 7. Trap — Dedup မလုပ်ဘဲ Record များကို သိမ်းခြင်း

```python
records = [
    {"s": "Gamma", "p": "founded", "o": "Delta", "chunk_hash": "aaaaaaaa"},
    {"s": "Gamma", "p": "founded", "o": "Delta", "chunk_hash": "bbbbbbbb"},
    {"s": "Zeta", "p": "acquired", "o": "Alpha", "chunk_hash": "cccccccc"},
]
kept = [{"s": r["s"], "p": r["p"], "o": r["o"]} for r in records]
print("naive kept :", len(kept))
print(kept)
```

Output —

```text
naive kept : 3
[{'s': 'Gamma', 'p': 'founded', 'o': 'Delta'}, {'s': 'Gamma', 'p': 'founded', 'o': 'Delta'}, {'s': 'Zeta', 'p': 'acquired', 'o': 'Alpha'}]
```

`kept` သည် list comprehension ဖြင့် record တိုင်းကို ဖြတ်ယူရုံသာ ဖြစ်သည် — dedup မလုပ်ပါ။
ထို့ကြောင့် `(Gamma, founded, Delta)` သည် **နှစ်ခါ** ပါနေသည် (၃ record)။ Neo4j တွင် ဤသို့
`CREATE` ဖြင့် ထည့်လျှင် relationship ထပ်နေမည်။ မှန်သည့်နည်းမှာ `merge_triples` ကဲ့သို့
key ဖြင့် ပေါင်းခြင်း (သို့) Cypher တွင် `MERGE` ကို သုံးခြင်းဖြစ်သည်။

---

## 8. Code တစ်ခုလုံး — Run လုပ်နိုင်သော Version

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
chunks = chunk_words(words, size=5, overlap=3)
records = []
for c in chunks:
    chash = chunk_hash(c)
    for triple in extract_triples(c):
        records.append({"s": triple[0], "p": triple[1], "o": triple[2],
                        "chunk_hash": chash})
merged = merge_triples(records)
print("chunks %d -> raw records %d" % (len(chunks), len(records)))
print("unique triples after dedup: %d" % len(merged))
duplicated = sorted(k for k, e in merged.items() if e["freq"] > 1)
for key in duplicated:
    e = merged[key]
    print("  dup (%s) -[%s]-> (%s) freq=%d confidence=%.2f sources=%d"
          % (e["s"], e["p"], e["o"], e["freq"], e["confidence"], len(e["sources"])))
```

Output —

```text
chunks 8 -> raw records 8
unique triples after dedup: 6
  dup (Epsilon) -[supplies]-> (Zeta) freq=2 confidence=1.00 sources=2
  dup (Gamma) -[founded]-> (Delta) freq=2 confidence=1.00 sources=2
```

`duplicated = sorted(k for k, e in merged.items() if e["freq"] > 1)` သည် `merged.items()` မှ
`(key, entry)` tuple များကို ဖတ်ပြီး `freq > 1` ဖြစ်သည့် key များကိုသာ ယူသည်။ ထို့နောက်
`sorted()` က စီသည်။ ဤအစီအစဉ်ကြောင့် output သည် deterministic ဖြစ်သည်။

---

## 9. ကိုယ်တိုင်လေ့ကျင့်ကြည့်ပါ

**မေးခွန်း** — `confidence = min(1.0, 0.5 + 0.25 * freq)` ဖြင့် **freq=3** အတွက် ရလဒ်သည်
ဘာဖြစ်မလဲ။

1. 0.75
2. 1.00
3. 1.25
4. 1.50

<details>
<summary>အဖြေ ကြည့်ရန်</summary>

**အဖြေ — 2. 1.00**

```python
for freq in [1, 2, 3]:
    capped = round(min(1.0, 0.5 + 0.25 * freq), 2)
    uncapped = round(0.5 + 0.25 * freq, 2)
    print("freq=%d -> min-capped=%.2f  uncapped=%.2f" % (freq, capped, uncapped))
```

Output —

```text
freq=1 -> min-capped=0.75  uncapped=0.75
freq=2 -> min-capped=1.00  uncapped=1.00
freq=3 -> min-capped=1.00  uncapped=1.25
```

အကြောင်းရင်း — `0.5 + 0.25 * 3 = 1.25` ဖြစ်သော်လည်း `min(1.0, 1.25) = 1.0` ဖြစ်သည်။
`min()` သည် cap အဖြစ် အလုပ်လုပ်သဖြင့် confidence သည် 1.0 ကို မကျော်ပါ (uncapped column
တွင် 1.25 ဖြစ်နေသည်ကို တွေ့နိုင်သည်)။

</details>

---

**အဓိက မှတ်ထားရန်** — Overlap သည် boundary recall ကို တိုးပေမဲ့ triple များ ထပ်ထွက်လာစေသည်
(ဤနေရာတွင် raw ၈ မှ unique ၆)။ `merge_triples()` သည် case-folded `triple_key` ဖြင့်
`dict.setdefault` သုံး၍ record များကို ပေါင်းသည် — `freq` ဖြင့် အကြိမ်ရေ၊ `sources` ဖြင့်
provenance ကို ထိန်းသည်။ Confidence သည် `min(1.0, 0.5 + 0.25*freq)` ဖြစ်ပြီး `min()` က
cap အဖြစ် လုပ်သည်။ Neo4j တွင် ဤ semantics ကို `MERGE ... ON CREATE SET ... ON MATCH SET r.freq = r.freq + 1`
ဖြင့် simulate လုပ်သည်။
