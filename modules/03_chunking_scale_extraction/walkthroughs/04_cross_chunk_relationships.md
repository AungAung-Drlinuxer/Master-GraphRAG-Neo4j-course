# Walkthrough 04 — Cross-chunk relationship ပြန်ချိတ်ခြင်း (Exercise 4)

> ဤဖိုင်သည် Module 03 ၏ `solution.md` ထဲက Exercise 4 ကို **Python အခြေခံမှ စ၍**
> အပိုင်းလိုက် ရှင်းပြသည့် walkthrough ဖြစ်သည်။

---

## 0. ဤ Exercise က ဘာကို ဖြေရှင်းပေးသလဲ။

Chunk boundary သည် relationship တစ်ခုကို **အလယ်မှ** ဖြတ်သွားနိုင်သည်။ `size=5` ဖြင့် ခွဲသည့်အခါ
`Beta operates Gamma` သည် chunk 0 ၏ အဆုံးနှင့် chunk 1 ၏ အစ ကြား ကွဲသွားသည်။

```text
  chunk 0: Alpha acquired Beta Beta operates
                                         ^^^^^^^^ verb သည် boundary နောက်ဆုံးတွင် ရှိသည်
  chunk 1: Gamma Gamma founded Delta Delta
           ^^^^^ object သည် boundary နောက်တွင် ရှိသည်
                        |
                        v
  map phase မှ ဆုံးရှုံး — subject/verb/object သုံးလုံး chunk တစ်ခုတည်းအတွင်း မပါ
```

`extract_triples()` သည် "subject၊ verb နှင့် object သုံးလုံးလုံး chunk တစ်ခုတည်းအတွင်း ရှိရမည်"
ဟု ကန့်သတ်သဖြင့် ဤ relationship ကို **လွတ်သွား** သည်။ `reconnect_boundary_triples()` သည်
boundary နှစ်ဖက်ကို ကြည့်၍ ဆုံးရှုံးသွားသော Triple များကို Reduce side တွင် ပြန်ချိတ်ပေးသည်။

ဤ code မှာ လေ့လာရမည့် Python concepts များမှာ —

- List ၏ negative indexing (`left[-1]`, `left[-2]`)
- `range(len(chunks) - 1)` ဖြင့် adjacent pair
- `extend()` နှင့် `append()` ကွာခြားချက်
- Multiple condition ကို `and` ဖြင့် ဆက်ခြင်း
- Guard clause ဖြင့် empty/short list ကာကွယ်ခြင်း
- Tuple ကို tuple အသစ် ဖန်တီးခြင်း
- `dict.fromkeys()` ဖြင့် order-preserving dedup
- `try`/`except IndexError` ဖြင့် trap သရုပ်ပြခြင်း

---

## 1. `size=5` ဖြင့် Chunk ခွဲခြင်း

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
chunks = chunk_words(words, size=5, overlap=0)
print("chunk sizes: %s" % [len(c) for c in chunks])
for i, c in enumerate(chunks):
    print("  chunk %d (idx %2d:%2d): %s" % (i, i * 5, i * 5 + len(c), " ".join(c)))
```

Output —

```text
chunk sizes: [5, 5, 5, 3]
  chunk 0 (idx  0: 5): Alpha acquired Beta Beta operates
  chunk 1 (idx  5:10): Gamma Gamma founded Delta Delta
  chunk 2 (idx 10:15): partners Epsilon Epsilon supplies Zeta
  chunk 3 (idx 15:18): Zeta acquired Alpha
```

`size=5` သည် ၁၈ ကို ၅၊ ၅၊ ၅ နှင့် ကျန် ၃ ဖြင့် ခွဲသည်။ ပထမ chunk ၃ ခုသည် ဝါကျနှစ်ခုကြား
ကွဲသည် — chunk 0 တွင် `Beta operates` ဖြင့် ဆုံးပြီး object `Gamma` သည် chunk 1 တွင် ရှိသည်။

---

## 2. `reconnect_boundary_triples()` — Adjacent Pair Loop

```python
def reconnect_boundary_triples(chunks, verbs=VERBS, entities=ENTITIES):
    recovered = []
    for i in range(len(chunks) - 1):
        left, right = chunks[i], chunks[i + 1]
        if not left or not right:
            continue
        ...
```

`range(len(chunks) - 1)` သည် boundary များ၏ index များကို ပေးသည်။ Chunk ၄ ခုအတွက်
`0, 1, 2` (boundary ၃ ခု) ရသည်။ `left, right = chunks[i], chunks[i + 1]` ဖြင့် ဘယ်/ညာ
chunk ကို ယူသည်။ `range` ကို `len(chunks) - 1` အထိသာ လုပ်သဖြင့် `chunks[i + 1]` သည်
list ပြင်ပ မရောက်ပါ။

---

## 3. Pattern A — Verb က ဘယ်ဘက် Chunk ဆုံးတွင် ရှိခြင်း

```python
if left[-1] in verbs and len(left) >= 2 and left[-2] in entities and right[0] in entities:
    recovered.append((left[-2], left[-1], right[0]))
```

Pattern A သည် "ဘယ်ဘက် chunk သည် `subject + verb` ဖြင့် ဆုံးသည်" ဖြစ်ရပ် ဖြစ်သည်။

| အပိုင်း | အဓိပ္ပာယ် |
| --- | --- |
| `left[-1] in verbs` | ဘယ်ဘက် chunk ၏ နောက်ဆုံး token သည် verb |
| `len(left) >= 2` | ဘယ်ဘက် chunk တွင် အနည်းဆုံး token ၂ လုံး ရှိရမည် (`left[-2]` အတွက်) |
| `left[-2] in entities` | verb ၏ ရှေ့ token သည် entity — subject |
| `right[0] in entities` | ညာဘက် chunk ၏ ပထမ token သည် entity — object |

ဒါကြောင့် `(left[-2], left[-1], right[0])` သည် `(subject, verb, object)` ဖြစ်သည်။
`recovered.append(...)` သည် tuple အသစ်တစ်ခုကို list ထဲ ထည့်သည်။

---

## 4. Pattern B — Verb က ညာဘက် Chunk အစတွင် ရှိခြင်း

```python
if right[0] in verbs and len(right) >= 2 and left[-1] in entities and right[1] in entities:
    recovered.append((left[-1], right[0], right[1]))
```

Pattern B သည် "ညာဘက် chunk သည် `verb + object` ဖြင့် စသည်" ဖြစ်ရပ် ဖြစ်သည်။

| အပိုင်း | အဓိပ္ပာယ် |
| --- | --- |
| `right[0] in verbs` | ညာဘက် chunk ၏ ပထမ token သည် verb |
| `len(right) >= 2` | ညာဘက် chunk တွင် `right[1]` ရှိရန် အနည်းဆုံး token ၂ လုံး |
| `left[-1] in entities` | ဘယ်ဘက် chunk ၏ နောက်ဆုံး token သည် entity — subject |
| `right[1] in entities` | verb ၏ နောက် token သည် entity — object |

ဒါကြောင့် `(left[-1], right[0], right[1])` သည် `(subject, verb, object)` ဖြစ်သည်။

---

## 5. Boundary တိုင်းတွင် ဘယ် Pattern ဖြစ်သည်ကို စစ်ခြင်း

```python
VERBS = frozenset({"acquired", "operates", "founded", "partners", "supplies"})
ENTITIES = frozenset({"Alpha", "Beta", "Gamma", "Delta", "Epsilon", "Zeta"})
chunks = [
    ["Alpha", "acquired", "Beta", "Beta", "operates"],
    ["Gamma", "Gamma", "founded", "Delta", "Delta"],
    ["partners", "Epsilon", "Epsilon", "supplies", "Zeta"],
    ["Zeta", "acquired", "Alpha"],
]
for i in range(len(chunks) - 1):
    left, right = chunks[i], chunks[i + 1]
    a = left[-1] in VERBS and len(left) >= 2 and left[-2] in ENTITIES and right[0] in ENTITIES
    b = right[0] in VERBS and len(right) >= 2 and left[-1] in ENTITIES and right[1] in ENTITIES
    print("boundary %d: left[-2:]=%s right[:2]=%s A=%s B=%s"
          % (i, left[-2:], right[:2], a, b))
```

Output —

```text
boundary 0: left[-2:]=['Beta', 'operates'] right[:2]=['Gamma', 'Gamma'] A=True B=False
boundary 1: left[-2:]=['Delta', 'Delta'] right[:2]=['partners', 'Epsilon'] A=False B=True
boundary 2: left[-2:]=['supplies', 'Zeta'] right[:2]=['Zeta', 'acquired'] A=False B=False
```

| Boundary | left tail | right head | Pattern A | Pattern B | ရလဒ် |
| --- | --- | --- | --- | --- | --- |
| 0 | `Beta operates` | `Gamma Gamma` | `True` | `False` | `(Beta, operates, Gamma)` |
| 1 | `Delta Delta` | `partners Epsilon` | `False` | `True` | `(Delta, partners, Epsilon)` |
| 2 | `supplies Zeta` | `Zeta acquired` | `False` | `False` | — (relationship မကွဲ) |

Boundary 0 တွင် Pattern A သည် `['Beta','operates','Gamma']` ကို ကောက်ယူသည် — boundary
ကြောင့် ဆုံးရှုံးသွားသော `Beta operates Gamma` ဖြစ်သည်။ Boundary 2 တွင် နှစ်ဖက်လုံး
`False` ဖြစ်သည် — အကြောင်းရင်းမှာ `Zeta acquired Alpha` သည် chunk 3 (`size=3` ဖြစ်သဖြင့်
အပြည့်အစုံ) အတွင်း ပါဝင်ပြီးသား ဖြစ်သဖြင့် boundary မဖြစ်ပါ။

---

## 6. `extend()` နှင့် Map Phase ရလဒ်

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


def reconnect_boundary_triples(chunks, verbs=VERBS, entities=ENTITIES):
    recovered = []
    for i in range(len(chunks) - 1):
        left, right = chunks[i], chunks[i + 1]
        if not left or not right:
            continue
        if left[-1] in verbs and len(left) >= 2 and left[-2] in entities and right[0] in entities:
            recovered.append((left[-2], left[-1], right[0]))
        if right[0] in verbs and len(right) >= 2 and left[-1] in entities and right[1] in entities:
            recovered.append((left[-1], right[0], right[1]))
    return recovered


words = tokenize(CORPUS)
chunks = chunk_words(words, size=5, overlap=0)
mapped = []
for c in chunks:
    mapped.extend(extract_triples(c))
recovered = reconnect_boundary_triples(chunks)
print("mapped    : %d %s" % (len(mapped), mapped))
print("recovered : %d %s" % (len(recovered), recovered))
combined = list(dict.fromkeys(mapped + recovered))
print("combined  : %d %s" % (len(combined), combined))
```

Output —

```text
mapped    : 4 [('Alpha', 'acquired', 'Beta'), ('Gamma', 'founded', 'Delta'), ('Epsilon', 'supplies', 'Zeta'), ('Zeta', 'acquired', 'Alpha')]
recovered : 2 [('Beta', 'operates', 'Gamma'), ('Delta', 'partners', 'Epsilon')]
combined  : 6 [('Alpha', 'acquired', 'Beta'), ('Gamma', 'founded', 'Delta'), ('Epsilon', 'supplies', 'Zeta'), ('Zeta', 'acquired', 'Alpha'), ('Beta', 'operates', 'Gamma'), ('Delta', 'partners', 'Epsilon')]
```

`mapped.extend(extract_triples(c))` — `extend()` သည် list ထဲက element များကို **တစ်ခုချင်း**
ထည့်သည်။ `append()` ဖြစ်လျှင် list အလိုက် (nested) ဝင်မည်။ `size=5` ဖြစ်သဖြင့် map
phase သည် triple ၄ ခုသာ ရသည် — ကျန် ၂ ခုကို reconnection က ပြန်ရှာသည်။ စုစုပေါင်း ၆
ခုဖြစ်ပြီး corpus ၏ relationship ၆ ခုနှင့် ကိုက်ညီသည်။

---

## 7. Guard — Empty Chunk

```python
VERBS = frozenset({"operates"})
ENTITIES = frozenset({"Alpha", "Beta", "Gamma"})


def guarded(chunks):
    recovered = []
    for i in range(len(chunks) - 1):
        left, right = chunks[i], chunks[i + 1]
        if not left or not right:
            continue
        if left[-1] in VERBS and len(left) >= 2 and left[-2] in ENTITIES and right[0] in ENTITIES:
            recovered.append((left[-2], left[-1], right[0]))
    return recovered


def unguarded(chunks):
    recovered = []
    for i in range(len(chunks) - 1):
        left, right = chunks[i], chunks[i + 1]
        if left[-1] in VERBS and left[-2] in ENTITIES and right[0] in ENTITIES:
            recovered.append((left[-2], left[-1], right[0]))
    return recovered


bad = [["Alpha", "operates"], [], ["Gamma"]]
print("guarded  :", guarded(bad))
try:
    print("unguarded:", unguarded(bad))
except IndexError as exc:
    print("unguarded: IndexError:", exc)
```

Output —

```text
guarded  : []
unguarded: IndexError: list index out of range
```

`if not left or not right: continue` သည် chunk တစ်ခုခု **empty** ဖြစ်ပါက ထို boundary ကို
ကျော်လိုက်သည်။ `not []` သည် `True` ဖြစ်သည်။ Guard မရှိပါက `right[0]` သည် empty list
ပေါ်တွင် `IndexError` ဖြစ်သည်။ Production တွင် chunking သည် empty chunk မထုတ်သော်လည်း
filter/dedup အဆင့်များကြား empty list ဖြစ်နိုင်သဖြင့် guard သည် လိုအပ်သည်။

---

## 8. Guard — `len(left) >= 2`

```python
VERBS = frozenset({"operates"})
ENTITIES = frozenset({"Alpha", "Beta", "Gamma"})


def with_len_guard(chunks):
    recovered = []
    for i in range(len(chunks) - 1):
        left, right = chunks[i], chunks[i + 1]
        if not left or not right:
            continue
        if left[-1] in VERBS and len(left) >= 2 and left[-2] in ENTITIES and right[0] in ENTITIES:
            recovered.append((left[-2], left[-1], right[0]))
    return recovered


def without_len_guard(chunks):
    recovered = []
    for i in range(len(chunks) - 1):
        left, right = chunks[i], chunks[i + 1]
        if left[-1] in VERBS and left[-2] in ENTITIES and right[0] in ENTITIES:
            recovered.append((left[-2], left[-1], right[0]))
    return recovered


print("with len guard               :", with_len_guard([["operates"], ["Gamma"]]))
print("with len guard (normal chunk):", with_len_guard([["Alpha", "operates"], ["Gamma"]]))
try:
    print("without len guard            :", without_len_guard([["operates"], ["Gamma"]]))
except IndexError as exc:
    print("without len guard            : IndexError:", exc)
```

Output —

```text
with len guard               : []
with len guard (normal chunk): [('Alpha', 'operates', 'Gamma')]
without len guard            : IndexError: list index out of range
```

`left` သည် token တစ်လုံးသာ ရှိပါက `left[-2]` သည် list ပြင်ပ ရောက်သဖြင့် `IndexError`
ဖြစ်သည်။ `len(left) >= 2` guard က ထို case ကို ကာကွယ်သည်။ ဤ guard သည် boundary
condition တိုင်းအတွက် **မဖြစ်မနေ** လိုသည် — size သေးသော chunk တွင် predicate တစ်လုံးတည်း
ကျန်နိုင်သည်။

---

## 9. `dict.fromkeys()` — Order-preserving Dedup

`mapped + recovered` ကို တိုက်ရိုက် ထည့်ပါက triple ထပ်နိုင်သည်။ `dict.fromkeys()` သည်
ထပ်တူ value များကို ပေါင်းပြီး **ပထမတွေ့သည့် အစီအစဉ်** ကို ထိန်းထားသည်။

```python
mapped = [("Alpha", "acquired", "Beta"), ("Beta", "operates", "Gamma")]
recovered = [("Beta", "operates", "Gamma"), ("Delta", "partners", "Epsilon")]
combined = list(dict.fromkeys(mapped + recovered))
print("mapped+recovered :", len(mapped) + len(recovered))
print("combined unique  :", len(combined))
print(combined)
```

Output —

```text
mapped+recovered : 4
combined unique  : 3
[('Alpha', 'acquired', 'Beta'), ('Beta', 'operates', 'Gamma'), ('Delta', 'partners', 'Epsilon')]
```

`mapped + recovered` သည် list နှစ်ခုကို ဆက်သည် (element ၄ ခု၊ `('Beta','operates','Gamma')`
နှစ်ခါ)။ `dict.fromkeys(...)` သည် element တိုင်းကို key အဖြစ် ထည့်ပြီး (value `None`) —
ထပ်တူ key က တစ်ခါသာ ရှိသည်။ ထို့နောက် `list(...)` သည် key များကို ပြန်ယူသည် (`3` ခု)။
ဤနည်းသည် **set-style dedup** ဖြစ်သော်လည်း အစီအစဉ်ကို မဆုံးရှုံးစေပါ။

---

## 10. Trap — Overlap နှင့် Reconnection ကို တွဲသုံးခြင်း

Reconnection သည် **overlap မရှိသော** chunking အတွက် ရည်ရွယ်ထားသည်။ Overlap ရှိပြီးသား
chunk များပေါ် ထပ်မံ run လျှင် **phantom triple** များ ထွက်လာနိုင်သည်။

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


def reconnect_boundary_triples(chunks, verbs=VERBS, entities=ENTITIES):
    recovered = []
    for i in range(len(chunks) - 1):
        left, right = chunks[i], chunks[i + 1]
        if not left or not right:
            continue
        if left[-1] in verbs and len(left) >= 2 and left[-2] in entities and right[0] in entities:
            recovered.append((left[-2], left[-1], right[0]))
        if right[0] in verbs and len(right) >= 2 and left[-1] in entities and right[1] in entities:
            recovered.append((left[-1], right[0], right[1]))
    return recovered


words = tokenize(CORPUS)
chunks = chunk_words(words, size=6, overlap=2)
mapped = []
for c in chunks:
    mapped.extend(extract_triples(c))
recovered = reconnect_boundary_triples(chunks)
print("mapped    :", mapped)
print("recovered :", recovered)
combined = list(dict.fromkeys(mapped + recovered))
print("raw total :", len(mapped) + len(recovered))
print("combined  :", len(combined), combined)
```

Output —

```text
mapped    : [('Alpha', 'acquired', 'Beta'), ('Beta', 'operates', 'Gamma'), ('Gamma', 'founded', 'Delta'), ('Delta', 'partners', 'Epsilon'), ('Epsilon', 'supplies', 'Zeta'), ('Zeta', 'acquired', 'Alpha')]
recovered : [('Gamma', 'operates', 'Gamma'), ('Epsilon', 'supplies', 'Epsilon')]
raw total : 8
combined  : 8 [('Alpha', 'acquired', 'Beta'), ('Beta', 'operates', 'Gamma'), ('Gamma', 'founded', 'Delta'), ('Delta', 'partners', 'Epsilon'), ('Epsilon', 'supplies', 'Zeta'), ('Zeta', 'acquired', 'Alpha'), ('Gamma', 'operates', 'Gamma'), ('Epsilon', 'supplies', 'Epsilon')]
```

`overlap=2` ဖြစ်ပါက boundary ရှိ relationship များသည် **chunk အတွင်းမှာပင် အပြည့်အစုံ ပါဝင်ပြီး**
ဖြစ်သဖြင့် `mapped` တွင် ၆ ခုလုံး ရှိပြီးသားဖြစ်သည်။ သို့သော် Pattern B သည် boundary
တွင် ထပ်မံ fired ဖြစ်ပြီး `('Gamma','operates','Gamma')` နှင့်
`('Epsilon','supplies','Epsilon')` ကို ထုတ်လိုက်သည် — ဤနှစ်ခုတွင် **subject နှင့် object
တူညီ** နေသည် (phantom)။ ဒါကြောင့် reconnection ကို overlap=0 ဖြစ်သည့်အခါတွင်သာ
သုံးသင့်ပြီး၊ သုံးလျှင် subject == object ကဲ့သို့သော validation ကို ထည့်ရမည်။

---

## 11. Code တစ်ခုလုံး — Run လုပ်နိုင်သော Version

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


def reconnect_boundary_triples(chunks, verbs=VERBS, entities=ENTITIES):
    recovered = []
    for i in range(len(chunks) - 1):
        left, right = chunks[i], chunks[i + 1]
        if not left or not right:
            continue
        if left[-1] in verbs and len(left) >= 2 and left[-2] in entities and right[0] in entities:
            recovered.append((left[-2], left[-1], right[0]))
        if right[0] in verbs and len(right) >= 2 and left[-1] in entities and right[1] in entities:
            recovered.append((left[-1], right[0], right[1]))
    return recovered


words = tokenize(CORPUS)
chunks = chunk_words(words, size=5, overlap=0)
print("chunk sizes: %s" % [len(c) for c in chunks])
mapped = []
for c in chunks:
    mapped.extend(extract_triples(c))
recovered = reconnect_boundary_triples(chunks)
print("mapped triples    : %d" % len(mapped))
print("recovered triples : %d" % len(recovered))
for t in recovered:
    print("  recovered: (%s) -[%s]-> (%s)" % t)
combined = list(dict.fromkeys(mapped + recovered))
print("combined unique   : %d" % len(combined))
```

Output —

```text
chunk sizes: [5, 5, 5, 3]
mapped triples    : 4
recovered triples : 2
  recovered: (Beta) -[operates]-> (Gamma)
  recovered: (Delta) -[partners]-> (Epsilon)
combined unique   : 6
```

`for t in recovered: print(... % t)` သည် tuple `t` ၏ အပိုင်းသုံးခုကို `%s` သုံးခုအဖြစ်
အတိအကျ ဖြန့်ပေးသည် (tuple unpacking format)။

---

## 12. ကိုယ်တိုင်လေ့ကျင့်ကြည့်ပါ

**မေးခွန်း** — အောက်ပါ chunk နှစ်ခုအတွက် `reconnect_boundary_triples()` သည် triple
ဘယ်နှစ်ခု ပြန်ရှာမလဲ။
`chunks = [["Alpha", "Beta", "operates"], ["Gamma", "founded", "Delta"]]`

1. ၀ ခု
2. ၁ ခု — `(Beta, operates, Gamma)`
3. ၂ ခု — `(Beta, operates, Gamma)` နှင့် `(Gamma, founded, Delta)`
4. ၁ ခု — `(Alpha, operates, Gamma)`

<details>
<summary>အဖြေ ကြည့်ရန်</summary>

**အဖြေ — 2. ၁ ခု — `(Beta, operates, Gamma)`**

```python
VERBS = frozenset({"acquired", "operates", "founded", "partners", "supplies"})
ENTITIES = frozenset({"Alpha", "Beta", "Gamma", "Delta", "Epsilon", "Zeta"})


def reconnect_boundary_triples(chunks, verbs=VERBS, entities=ENTITIES):
    recovered = []
    for i in range(len(chunks) - 1):
        left, right = chunks[i], chunks[i + 1]
        if not left or not right:
            continue
        if left[-1] in verbs and len(left) >= 2 and left[-2] in entities and right[0] in entities:
            recovered.append((left[-2], left[-1], right[0]))
        if right[0] in verbs and len(right) >= 2 and left[-1] in entities and right[1] in entities:
            recovered.append((left[-1], right[0], right[1]))
    return recovered


chunks = [["Alpha", "Beta", "operates"], ["Gamma", "founded", "Delta"]]
print("recovered:", reconnect_boundary_triples(chunks))
```

Output —

```text
recovered: [('Beta', 'operates', 'Gamma')]
```

အကြောင်းရင်း — Boundary 0 တွင် `left[-1] = 'operates'` သည် verb၊ `left[-2] = 'Beta'` သည်
entity၊ `right[0] = 'Gamma'` သည် entity ဖြစ်သဖြင့် Pattern A fired ဖြစ်သည်။ Pattern B
တွင် `right[0] = 'Gamma'` သည် verb မဟုတ်သဖြင့် fired မဖြစ်ပါ။ `('Gamma','founded','Delta')`
သည် boundary မဟုတ်ဘဲ chunk 1 အတွင်းမှာပင် အပြည့်အစုံ ရှိသဖြင့် reconnection မလိုပါ။

</details>

---

**အဓိက မှတ်ထားရန်** — `reconnect_boundary_triples()` သည် `chunk[i]` ၏ အဆုံးနှင့်
`chunk[i+1]` ၏ အစကို ကြည့်၍ boundary ဖြတ်သွားသော relationship များကို ပြန်ချိတ်သည်။
Pattern A (verb က ဘယ်ဘက်ဆုံး) နှင့် Pattern B (verb က ညာဘက်အစ) နှစ်မျိုး ရှိသည်။
`if not left or not right` နှင့် `len(...) >= 2` guard နှစ်ခုသည် `IndexError` ကို
ကာကွယ်ရန် မဖြစ်မနေ လိုသည်။ `dict.fromkeys()` ဖြင့် mapped + recovered ကို dedup
လုပ်ရမည်။ Reconnection ကို **overlap=0** ဖြစ်သည့်အခါတွင်သာ သုံးသင့်သည် — overlap
ရှိပြီးသား chunk များပေါ်တွင် run လျှင် subject == object ကဲ့သို့သော phantom triple
များ ထွက်လာသည်။
