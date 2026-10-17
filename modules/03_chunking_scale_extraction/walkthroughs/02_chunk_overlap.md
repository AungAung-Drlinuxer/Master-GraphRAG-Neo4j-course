# Walkthrough 02 — Overlap ထည့်ခြင်း (Exercise 2)

> ဤဖိုင်သည် Module 03 ၏ `solution.md` ထဲက Exercise 2 ကို **Python အခြေခံမှ စ၍**
> အပိုင်းလိုက် ရှင်းပြသည့် walkthrough ဖြစ်သည်။

---

## 0. ဤ Exercise က ဘာကို ဖြေရှင်းပေးသလဲ။

Exercise 1 ၏ chunking သည် chunk များကို ထပ်မစေဘဲ ခွဲသည်။ သို့သော် relationship တစ်ခုသည်
**boundary** ပေါ် ကျရောက်ပါက အစိတ်အပိုင်း ကွဲသွားနိုင်သည်။ `Beta operates Gamma` သည်
chunk နှစ်ခုကြား ကွဲသွားလျှင် မည်သည့် chunk အတွင်းမှာမျှ subject–verb–object သုံးလုံး
မပြည့်စုံတော့ပါ။

```text
overlap=0 (stride=6)
  chunk 0: Alpha acquired Beta | Beta operates Gamma
  chunk 1: Gamma founded Delta  | Delta partners Epsilon
             ^ "operates" သည် chunk 0 နှင့် တူပြီး "Gamma" သည် chunk 1 နှင့် တူသည်
```

**Overlap** သည် chunk နှစ်ခုကြား token အချို့ကို ရည်ရွယ်ချက်ရှိရှိ ထပ်စေသည်။ Boundary
အနီးရှိ relationship များ အနည်းဆုံး chunk တစ်ခုအတွင်း အပြည့်အစုံ ပါဝင်နိုင်ရန် ဖြစ်သည်။

```text
overlap=2 (stride=4)
  chunk 0: Alpha acquired Beta Beta operates Gamma
  chunk 1:             operates Gamma Gamma founded Delta Delta
  chunk 2:                        Delta Delta partners Epsilon Epsilon supplies
  chunk 3:                                              Epsilon supplies Zeta Zeta acquired Alpha
```

ဤ code မှာ လေ့လာရမည့် Python concepts များမှာ —

- Negative indexing (`chunk[-2:]`)
- Slicing နှစ်ခုကို `==` ဖြင့် နှိုင်းယှဉ်ခြင်း
- `range()` ဖြင့် index loop
- `zip()` ဖြင့် adjacent element စုံခြင်း
- `all()` နှင့် generator expression
- `set` ဖြင့် ထပ်တူတန်ဖိုး ရေတွက်ခြင်း
- Token cost တွက်ချက်ခြင်း (`sum()`)

---

## 1. Overlap နှစ်မျိုးကို နှိုင်းယှဉ်ခြင်း

```python
import re

CORPUS = (
    "Alpha acquired Beta . Beta operates Gamma . Gamma founded Delta . "
    "Delta partners Epsilon . Epsilon supplies Zeta . Zeta acquired Alpha ."
)


def tokenize(text):
    return re.findall(r"[A-Za-z]+", text)


def chunk_words(words, size, overlap):
    if not 0 <= overlap < size:
        raise ValueError("require 0 <= overlap < size")
    stride = size - overlap
    n = len(words)
    chunks, start = [], 0
    while start < n:
        chunks.append(words[start:start + size])
        if start + size >= n:
            break
        start += stride
    return chunks


words = tokenize(CORPUS)
no_overlap = chunk_words(words, size=6, overlap=0)
with_overlap = chunk_words(words, size=6, overlap=2)
print("overlap=0 -> %d chunks, sizes %s" % (len(no_overlap), [len(c) for c in no_overlap]))
print("overlap=2 -> %d chunks, sizes %s" % (len(with_overlap), [len(c) for c in with_overlap]))
```

Output —

```text
overlap=0 -> 3 chunks, sizes [6, 6, 6]
overlap=2 -> 4 chunks, sizes [6, 6, 6, 6]
```

Chunk အရေအတွက် ၃ မှ ၄ သို့ တိုးသည်။ အကြောင်းရင်းမှာ `stride` ပြောင်းလဲခြင်းဖြစ်သည် — overlap=0
တွင် `stride=6`၊ overlap=2 တွင် `stride=4`။ `stride` ငယ်လျှင် loop ပိုကြာ၍ chunk ပိုများလာသည်။
Chunk တိုင်း၏ size မှာ ၆ လုံးအတိုင်း ရှိနေသည်ကို သတိထားပါ။

---

## 2. Boundary တိုင်း Overlap ကို စစ်ဆေးခြင်း

Overlap သည် "ကောင်းကောင်း လုပ်ပြီ" ဟု ယူဆခြင်းမပြုရ — boundary တိုင်းတွင် ဘယ်ဘက် chunk ၏
**နောက်ဆုံး `overlap` လုံး** သည် ညာဘက် chunk ၏ **ပထမ `overlap` လုံး** နှင့် တူရမည်။

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
    n = len(words)
    chunks, start = [], 0
    while start < n:
        chunks.append(words[start:start + size])
        if start + size >= n:
            break
        start += stride
    return chunks


words = tokenize(CORPUS)
chunks = chunk_words(words, size=6, overlap=2)
for i in range(len(chunks) - 1):
    left, right = chunks[i], chunks[i + 1]
    print("boundary %d: left[-2:]=%s  right[:2]=%s  equal=%s"
          % (i, left[-2:], right[:2], left[-2:] == right[:2]))
```

Output —

```text
boundary 0: left[-2:]=['operates', 'Gamma']  right[:2]=['operates', 'Gamma']  equal=True
boundary 1: left[-2:]=['Delta', 'Delta']  right[:2]=['Delta', 'Delta']  equal=True
boundary 2: left[-2:]=['Epsilon', 'supplies']  right[:2]=['Epsilon', 'supplies']  equal=True
```

`range(len(chunks) - 1)` သည် `0, 1, 2` ကို ပေးသည် (chunk ၄ ခုအတွက် boundary ၃ ခု)။ `left, right =
chunks[i], chunks[i + 1]` သည် tuple unpacking ဖြစ်သည်။ Boundary သုံးခုစလုံးတွင် ညီမျှမှုကို စစ်သည်။

### Negative Indexing

`left[-2:]` သည် list ၏ **နောက်မှ ဒုတိယ element** မှ စ၍ အဆုံးအထိ ယူသည်။

```python
nums = ["Alpha", "acquired", "Beta", "Beta", "operates", "Gamma"]
print(nums[-2:])
print(nums[:2])
print(nums[-2:] == nums[:2])
print(["a", "b"][-2:] == ["a", "b"][:2])
```

Output —

```text
['operates', 'Gamma']
['Alpha', 'acquired']
False
True
```

`nums[-2:]` သည် အဆုံး နှစ်လုံး၊ `nums[:2]` သည် အစ နှစ်လုံး ဖြစ်သည်။ ဤ list ၏ အဆုံးနှင့် အစ
**မတူညီ** သဖြင့် `False` ဖြစ်သည်။ သို့သော် list တိုသည် `["a", "b"]` တွင် `[-2:]` နှင့် `[:2]`
နှစ်ခုလုံး element နှစ်လုံးလုံးကို ပြန်ပေးသဖြင့် တူညီသည် (`True`)။ ဤအချက်က slice သည်
**ကျန်သလောက်ဖြင့် ရပ်** ကြောင်း ထပ်မံ ပြသည်။

---

## 3. `zip()` ဖြင့် Adjacent Chunk စုံခြင်း

Index loop အစား `zip()` ကို သုံးနိုင်သည်။ `zip(a, b)` သည် list နှစ်ခုကို တစ်ခုချင်း စုံပေးသည်။
`chunks[1:]` သည် chunk အားလုံးမှ ပထမတစ်ခုကို ဖယ်ထားသော list ဖြစ်သဖြင့်
`zip(chunks, chunks[1:])` သည် `(chunk[i], chunk[i+1])` အားလုံးကို ပေးသည်။

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
    n = len(words)
    chunks, start = [], 0
    while start < n:
        chunks.append(words[start:start + size])
        if start + size >= n:
            break
        start += stride
    return chunks


words = tokenize(CORPUS)
chunks = chunk_words(words, size=6, overlap=2)
for left, right in zip(chunks, chunks[1:]):
    print("tail=%-38s head=%-38s equal=%s" % (left[-2:], right[:2], left[-2:] == right[:2]))
```

Output —

```text
tail=['operates', 'Gamma']                  head=['operates', 'Gamma']                  equal=True
tail=['Delta', 'Delta']                     head=['Delta', 'Delta']                     equal=True
tail=['Epsilon', 'supplies']                head=['Epsilon', 'supplies']                equal=True
```

`zip()` သည် အတိုဆုံး list ဆုံးသည့်အထိ လုပ်သဖြင့် boundary အရေအတွက်နှင့် တိတိကျကျ ကိုက်ညီသည်။
Index ကို လက်ဖြင့် မထိန်းရသဖြင့် off-by-one error ဖြစ်နိုင်ခြေ နည်းသည်။

---

## 4. `all()` ဖြင့် Boundary အားလုံးကို တစ်ပြိုင်နက် စစ်ခြင်း

Assertion အတွက် boundary အားလုံးကို boolean တစ်ခုသို့ စုစည်းလိုသည်။ `all()` သည် element
အားလုံး truthy ဖြစ်မှ `True` ပြန်သည်။

```python
chunks = [
    ["Alpha", "acquired", "Beta", "Beta", "operates", "Gamma"],
    ["operates", "Gamma", "Gamma", "founded", "Delta", "Delta"],
    ["Delta", "Delta", "partners", "Epsilon", "Epsilon", "supplies"],
    ["Epsilon", "supplies", "Zeta", "Zeta", "acquired", "Alpha"],
]
print("all boundaries align :", all(chunks[i][-2:] == chunks[i + 1][:2] for i in range(len(chunks) - 1)))
print("chunk count          :", len(chunks))
print("distinct tails       :", len(set(tuple(c[-2:]) for c in chunks[:-1])))
```

Output —

```text
all boundaries align : True
chunk count          : 4
distinct tails       : 3
```

`all(... for i in range(...))` အတွင်းက အပိုင်းသည် **generator expression** ဖြစ်သည် — element များကို
တစ်ခုချင်း တွက်ပြီး `all()` က ရပ်လိုသည့်အခါ ချက်ချင်း ရပ်နိုင်သည်။ `chunks[:-1]` သည် နောက်ဆုံး
chunk မပါသော list ဖြစ်သည် (tail ရှိသည့် chunk များသာ)။ `set(tuple(c[-2:]) ...)` သည် tail
များကို tuple အဖြစ် ပြောင်း၍ ထပ်တူများကို ပေါင်းသည် — boundary ၃ ခုတွင် tail သုံးမျိုး ကွဲပြားသည်။

---

## 5. Trap — `stride` တွင် Overlap မပါခြင်း

Overlap ကို parameter အဖြစ် လက်ခံပေမဲ့ `stride` တွက်ရာတွင် မသုံးမိပါက chunk များ **ထပ်တော့မည်
မဟုတ်ပါ**။ ဤ bug ကို ညာဘက် ဇယားဖြင့် သရုပ်ပြသည်။

```python
import re

CORPUS = (
    "Alpha acquired Beta . Beta operates Gamma . Gamma founded Delta . "
    "Delta partners Epsilon . Epsilon supplies Zeta . Zeta acquired Alpha ."
)


def tokenize(text):
    return re.findall(r"[A-Za-z]+", text)


def real_overlap(words, size, overlap):
    stride = size - overlap
    n, start, chunks = len(words), 0, []
    while start < n:
        chunks.append(words[start:start + size])
        if start + size >= n:
            break
        start += stride
    return chunks


def ignores_overlap(words, size, overlap):
    stride = size                       # overlap ကို လျစ်လျူရှုထားသည်
    n, start, chunks = len(words), 0, []
    while start < n:
        chunks.append(words[start:start + size])
        if start + size >= n:
            break
        start += stride
    return chunks


words = tokenize(CORPUS)
real = real_overlap(words, size=6, overlap=2)
ignored = ignores_overlap(words, size=6, overlap=2)
print("real    -> %d chunks" % len(real))
print("ignored -> %d chunks" % len(ignored))
print("boundary 0 equal : real=%s  ignored=%s"
      % (real[0][-2:] == real[1][:2], ignored[0][-2:] == ignored[1][:2]))
```

Output —

```text
real    -> 4 chunks
ignored -> 3 chunks
boundary 0 equal : real=True  ignored=False
```

`ignores_overlap` သည် overlap ကို လက်ခံပေမဲ့ `stride = size` ဟု သတ်မှတ်သဖြင့် overlap=0
ကဲ့သို့သာ ပြုမူသည် (၃ chunk)။ Boundary တွင် ညီမျှမှု `False` ဖြစ်သည်။ ဤအချက်က function ၏
output ကို **assertion ဖြင့် စစ်ရန် မဖြစ်မနေ လိုသည်** ဆိုသည်ကို ပြသည် — parameter တစ်ခု
လက်ခံရုံဖြင့် အလုပ်လုပ်သည်ဟု မဆိုနိုင်ပါ။

---

## 6. Overlap ရွေးချယ်မှု Table — Cost Trade-off

Overlap တိုးလာသည့်အခါ chunk အရေအတွက်နှင့် စုစုပေါင်း token (extraction cost) ဘယ်လို
တိုးလာသည်ကို တိုင်းတာသည်။

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
for overlap in range(6):
    chunks = chunk_words(words, size=6, overlap=overlap)
    tokens = sum(len(c) for c in chunks)
    print("overlap=%d stride=%d -> %d chunks, tokens=%d"
          % (overlap, 6 - overlap, len(chunks), tokens))
```

Output —

```text
overlap=0 stride=6 -> 3 chunks, tokens=18
overlap=1 stride=5 -> 4 chunks, tokens=21
overlap=2 stride=4 -> 4 chunks, tokens=24
overlap=3 stride=3 -> 5 chunks, tokens=30
overlap=4 stride=2 -> 7 chunks, tokens=42
overlap=5 stride=1 -> 13 chunks, tokens=78
```

| overlap | stride | chunks | tokens | baseline (18) အပေါ် အချိုး |
| --- | --- | --- | --- | --- |
| 0 | 6 | 3 | 18 | 1.00× |
| 1 | 5 | 4 | 21 | 1.17× |
| 2 | 4 | 4 | 24 | 1.33× |
| 3 | 3 | 5 | 30 | 1.67× |
| 4 | 2 | 7 | 42 | 2.33× |
| 5 | 1 | 13 | 78 | 4.33× |

Token အရေအတွက်သည် `size / stride` အချိုးဖြင့် တိုးသည် — `overlap=5`, `stride=1` ဖြစ်ပါက
token cost သည် baseline ၏ ၄ ဆကျော်ဖြစ်သည်။ Production တွင် overlap ကို
`size` ၏ ၁၀–၂၀% (ဤနေရာတွင် overlap=1) ခန့်ဖြင့် ကန့်သတ်လေ့ရှိသည်။

---

## 7. Trap — Overlap Region ၏ နေရာအမှန်းခြေ

Boundary တစ်ခုကို လက်ဖြင့် စစ်သည့်အခါ "chunk 0 ၏ အလယ်အပိုင်း" ကို မယူမိရန် လိုသည်။
Overlap region သည် ဘယ်ဘက် chunk တွင် **အဆုံးအပိုင်း (`[-overlap:]`)**၊ ညာဘက် chunk တွင်
**အစအပိုင်း (`[:overlap]`)** ဖြစ်သည်။

```python
chunks = [
    ["Alpha", "acquired", "Beta", "Beta", "operates", "Gamma"],
    ["operates", "Gamma", "Gamma", "founded", "Delta", "Delta"],
]
print(chunks[0][-2:])
print(chunks[0][-2:] == ["operates", "Gamma"])
print(chunks[0][2:4] == chunks[1][0:2])
```

Output —

```text
['operates', 'Gamma']
True
False
```

`chunks[0][2:4]` သည် `['Beta', 'Beta']` ဖြစ်သည် — overlap region မဟုတ်ပါ။ `size=6` နှင့်
`overlap=2` အတွက် overlap region ၏ ဘယ်ဘက် နေရာသည် index `size - overlap = 4` မှ စသည်။
ဒါကြောင့် `[-overlap:]` (သို့) `[size - overlap:]` ကို သုံးရသည်။

---

## 8. Chunk Content အပြည့်အစုံ

```python
import re

CORPUS = (
    "Alpha acquired Beta . Beta operates Gamma . Gamma founded Delta . "
    "Delta partners Epsilon . Epsilon supplies Zeta . Zeta acquired Alpha ."
)


def tokenize(text):
    return re.findall(r"[A-Za-z]+", text)


def chunk_words(words, size, overlap):
    if not 0 <= overlap < size:
        raise ValueError("require 0 <= overlap < size")
    stride = size - overlap
    n = len(words)
    chunks, start = [], 0
    while start < n:
        chunks.append(words[start:start + size])
        if start + size >= n:
            break
        start += stride
    return chunks


words = tokenize(CORPUS)
with_overlap = chunk_words(words, size=6, overlap=2)
for i, c in enumerate(with_overlap):
    print("  chunk %d: %s" % (i, " ".join(c)))
```

Output —

```text
  chunk 0: Alpha acquired Beta Beta operates Gamma
  chunk 1: operates Gamma Gamma founded Delta Delta
  chunk 2: Delta Delta partners Epsilon Epsilon supplies
  chunk 3: Epsilon supplies Zeta Zeta acquired Alpha
```

Chunk 0 တွင် `Beta operates Gamma` ပါပြီး chunk 1 တွင် `operates Gamma` မှ စသဖြင့်
boundary relationship တစ်ခုစီသည် အနည်းဆုံး chunk တစ်ခုအတွင်း အပြည့်အစုံ ပါဝင်နိုင်သည်။

---

## 9. Progress Table — Chunk ဖွဲ့စည်းပုံ

| Chunk | index range | content | မှတ်ချက် |
| --- | --- | --- | --- |
| 0 | `0:6` | `Alpha acquired Beta Beta operates Gamma` | — |
| 1 | `4:10` | `operates Gamma Gamma founded Delta Delta` | head token ၂ လုံး chunk 0 ၏ tail နှင့် ထပ် |
| 2 | `8:14` | `Delta Delta partners Epsilon Epsilon supplies` | head token ၂ လုံး chunk 1 ၏ tail နှင့် ထပ် |
| 3 | `12:18` | `Epsilon supplies Zeta Zeta acquired Alpha` | နောက်ဆုံး chunk၊ `12+6 >= 18` ဖြစ်သဖြင့် ရပ် |

Chunk တိုင်း၏ စ `index` သည် `0, 4, 8, 12` — တစ်ခုနှင့်တစ်ခု `stride=4` ခြားသည်။

---

## 10. Code တစ်ခုလုံး — Run လုပ်နိုင်သော Version

```python
import re

CORPUS = (
    "Alpha acquired Beta . Beta operates Gamma . Gamma founded Delta . "
    "Delta partners Epsilon . Epsilon supplies Zeta . Zeta acquired Alpha ."
)


def tokenize(text):
    return re.findall(r"[A-Za-z]+", text)


def chunk_words(words, size, overlap):
    if not 0 <= overlap < size:
        raise ValueError("require 0 <= overlap < size")
    stride = size - overlap
    n = len(words)
    chunks, start = [], 0
    while start < n:
        chunks.append(words[start:start + size])
        if start + size >= n:
            break
        start += stride
    return chunks


words = tokenize(CORPUS)
no_overlap = chunk_words(words, size=6, overlap=0)
with_overlap = chunk_words(words, size=6, overlap=2)
print("overlap=0 -> %d chunks, sizes %s" % (len(no_overlap), [len(c) for c in no_overlap]))
print("overlap=2 -> %d chunks, sizes %s" % (len(with_overlap), [len(c) for c in with_overlap]))
for i, c in enumerate(with_overlap):
    print("  chunk %d: %s" % (i, " ".join(c)))
```

Output —

```text
overlap=0 -> 3 chunks, sizes [6, 6, 6]
overlap=2 -> 4 chunks, sizes [6, 6, 6, 6]
  chunk 0: Alpha acquired Beta Beta operates Gamma
  chunk 1: operates Gamma Gamma founded Delta Delta
  chunk 2: Delta Delta partners Epsilon Epsilon supplies
  chunk 3: Epsilon supplies Zeta Zeta acquired Alpha
```

---

## 11. ကိုယ်တိုင်လေ့ကျင့်ကြည့်ပါ

**မေးခွန်း** — Token ၁၈ လုံး corpus ကို `size=6, overlap=3` ဖြင့် ခွဲလျှင် chunk အရေအတွက်နှင့်
စုစုပေါင်း token သည် ဘာဖြစ်မလဲ။

1. chunk ၄ ခု၊ စုစုပေါင်း token ၂၄
2. chunk ၅ ခု၊ စုစုပေါင်း token ၃၀
3. chunk ၅ ခု၊ စုစုပေါင်း token ၂၄
4. chunk ၃ ခု၊ စုစုပေါင်း token ၁၈

<details>
<summary>အဖြေ ကြည့်ရန်</summary>

**အဖြေ — 2. chunk ၅ ခု၊ စုစုပေါင်း token ၃၀**

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
chunks = chunk_words(words, size=6, overlap=3)
print("chunk count:", len(chunks))
print("total tokens:", sum(len(c) for c in chunks))
print("boundary 0:", chunks[0][-3:] == chunks[1][:3], chunks[0][-3:])
```

Output —

```text
chunk count: 5
total tokens: 30
boundary 0: True ['Beta', 'operates', 'Gamma']
```

အကြောင်းရင်း — `stride = 6 - 3 = 3` ဖြစ်သဖြင့် `start` သည် `0, 3, 6, 9, 12` သို့ ရွေ့သည် (၅
chunk)။ Chunk တိုင်း ၆ လုံးဖြစ်သဖြင့် စုစုပေါင်း token = ၅ × ၆ = ၃၀ ဖြစ်သည်။ Overlap region
သည် `[-3:]` (chunk 0) နှင့် `[:3]` (chunk 1) ဖြစ်ပြီး `['Beta', 'operates', 'Gamma']` ဖြစ်သည်။

</details>

---

**အဓိက မှတ်ထားရန်** — Overlap သည် `stride = size - overlap` အချိုးအစားအားလုံးဖြစ်သည်။ Overlap
တိုးလျှင် boundary relationship recall တိုးသော်လည်း token cost သည် `size / stride` အချိုးဖြင့်
တိုးသည်။ Overlap ကို parameter အဖြစ် လက်ခံရုံဖြင့် မလုံလောက် — `stride` တွင် အမှန်
သုံးကြောင်းနှင့် boundary တိုင်း `left[-overlap:] == right[:overlap]` ဖြစ်ကြောင်း assertion
ဖြင့် စစ်ရမည်။
