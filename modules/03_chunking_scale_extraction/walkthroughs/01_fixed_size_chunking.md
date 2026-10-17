# Walkthrough 01 — Fixed-size chunking (Exercise 1)

> ဤဖိုင်သည် Module 03 ၏ `solution.md` ထဲက Exercise 1 ကို **Python အခြေခံမှ စ၍**
> အပိုင်းလိုက် ရှင်းပြသည့် walkthrough ဖြစ်သည်။ Format သည် Module 01 ၏
> `walkthroughs/` ဖိုင်များနှင့် တူညီသည်။

---

## 0. ဤ Exercise က ဘာကို ဖြေရှင်းပေးသလဲ။

LLM တစ်ခုက entity နှင့် relationship ကို **တစ်ကြိမ်လျှင် chunk တစ်ခု** အတွင်းသာ ဖတ်နိုင်သည်။ ဒါကြောင့်
စာရွက်စာတမ်းအရှည်ကြီးကို chunk များအဖြစ် ခွဲရမည်။ ခွဲသည့်နည်းအနက် အရိုးရှင်းဆုံးမှာ **fixed-size
chunking** ဖြစ်သည် — token အရေအတွက် တစ်သမတ်တည်းဖြင့် အစဉ်လိုက် ခွဲခြင်း။

```text
CORPUS (token 18 လုံး)
  Alpha acquired Beta . Beta operates Gamma . Gamma founded Delta .
  Delta partners Epsilon . Epsilon supplies Zeta . Zeta acquired Alpha .
        |
        |  size=6, overlap=0   ->  stride = 6
        v
  chunk 0: Alpha acquired Beta Beta operates Gamma
  chunk 1: Gamma founded Delta Delta partners Epsilon
  chunk 2: Epsilon supplies Zeta Zeta acquired Alpha
```

Chunk အရေအတွက်နှင့် chunk တိုင်း၏ size သည် **တွက်ချက်နိုင်သော (deterministic)** ဖြစ်ရမည်။ Token
cost၊ latency နှင့် recall တို့သည် chunk size ပေါ် တိုက်ရိုက် မှီခိုသဖြင့် ဤအဆင့်သည် pipeline
တစ်ခုလုံး၏ အခြေခံဖြစ်သည်။

ဤ code မှာ လေ့လာရမည့် Python concepts များမှာ —

- `import re` နှင့် `re.findall()`
- List slicing (`words[start:start + size]`)
- `while` loop နှင့် index ကို ကိုယ်တိုင် ထိန်းချုပ်ခြင်း
- Chained comparison (`0 <= overlap < size`)
- `raise ValueError(...)` နှင့် guard clause
- `enumerate()` နှင့် `str.join()`
- List comprehension နှင့် built-in `all()`
- `%` string formatting

---

## 1. Fixture — `CORPUS`

```python
CORPUS = (
    "Alpha acquired Beta . Beta operates Gamma . Gamma founded Delta . "
    "Delta partners Epsilon . Epsilon supplies Zeta . Zeta acquired Alpha ."
)
```

`CORPUS` သည် ဝါကျ ၆ ခုပါသော စာသားတစ်ခု ဖြစ်သည်။ `(` `)` အတွင်း ကပ်လျက်ရေးထားသော string literal
နှစ်ခုကို Python က **အလိုအလျောက် တစ်ခုတည်း ဆက်ပေးသည်**။

```python
CORPUS = (
    "Alpha acquired Beta . Beta operates Gamma . Gamma founded Delta . "
    "Delta partners Epsilon . Epsilon supplies Zeta . Zeta acquired Alpha ."
)
print(CORPUS)
```

Output —

```text
Alpha acquired Beta . Beta operates Gamma . Gamma founded Delta . Delta partners Epsilon . Epsilon supplies Zeta . Zeta acquired Alpha .
```

ဝါကျတိုင်းသည် `subject verb object .` ပုံစံဖြစ်သည် (`Alpha acquired Beta .`)။ ဤဖွဲ့စည်းပုံ တူညီမှုသည်
နောက် exercise များတွင် Triple ရှာရန် အခြေခံဖြစ်သည်။

---

## 2. `tokenize()` — `re.findall()` ဖြင့် Token ခွဲခြင်း

```python
import re

CORPUS = (
    "Alpha acquired Beta . Beta operates Gamma . Gamma founded Delta . "
    "Delta partners Epsilon . Epsilon supplies Zeta . Zeta acquired Alpha ."
)


def tokenize(text):
    return re.findall(r"[A-Za-z]+", text)
```

`re.findall(pattern, text)` သည် `text` ထဲတွင် `pattern` နှင့် ကိုက်ညီသော အပိုင်းအားလုံးကို **list**
အဖြစ် ပြန်ပေးသည်။ Pattern `r"[A-Za-z]+"` ၏ အဓိပ္ပာယ်မှာ —

| အပိုင်း | အဓိပ္ပာယ် |
| --- | --- |
| `[A-Za-z]` | အင်္ဂလိပ် စာလုံးကြီး သို့မဟုတ် စာလုံးအသေး တစ်လုံး |
| `+` | ရှေ့က အပိုင်းကို တစ်လုံး သို့မဟုတ် ထို့ထက် ပို ရှိရမည် |
| `r"..."` | Raw string — backslash များကို မူရင်းအတိုင်း ထိန်းသည် |

ဒါကြောင့် `r"[A-Za-z]+"` သည် **စာလုံးတွေ ဆက်နေသော အစုတစ်ခုစီ** (တနည်း word တစ်လုံး) ကို ဖမ်းသည်။
`.` `!` ကဲ့သို့ punctuation သည် `[A-Za-z]` နှင့် မကိုက်ညီသဖြင့် ဖယ်ထုတ်ခံရသည်။

```python
import re

print(re.findall(r"[A-Za-z]+", "Alpha acquired Beta ."))
print(re.findall(r"[A-Za-z]+", "Alpha, Beta. Gamma!"))
```

Output —

```text
['Alpha', 'acquired', 'Beta']
['Alpha', 'Beta', 'Gamma']
```

လိုင်းနှစ်လိုင်းလုံးတွင် punctuation မပါဝင်ပါ။ ဤအချက်ကြောင့် နောက်ပိုင်း `len(words)` သည်
punctuation မပါသော token အရေအတွက်ကို တွက်သည်။

### `tokenize()` ကို fixture အပေါ် run ခြင်း

```python
import re

CORPUS = (
    "Alpha acquired Beta . Beta operates Gamma . Gamma founded Delta . "
    "Delta partners Epsilon . Epsilon supplies Zeta . Zeta acquired Alpha ."
)


def tokenize(text):
    return re.findall(r"[A-Za-z]+", text)


print(tokenize(CORPUS))
print(len(tokenize(CORPUS)))
```

Output —

```text
['Alpha', 'acquired', 'Beta', 'Beta', 'operates', 'Gamma', 'Gamma', 'founded', 'Delta', 'Delta', 'partners', 'Epsilon', 'Epsilon', 'supplies', 'Zeta', 'Zeta', 'acquired', 'Alpha']
18
```

Token ၁၈ လုံး ရသည်။ ဝါကျ ၆ ခု × စကားလုံး ၃ လုံး = ၁၈ နှင့် ကိုက်ညီသည်။ ဤ ၁၈ လုံးသည် Exercise
တိုင်း၏ အခြေခံဖြစ်သည်။

---

## 3. `chunk_words()` — Signature နှင့် Guard

```python
def chunk_words(words, size, overlap):
    if not 0 <= overlap < size:
        raise ValueError("require 0 <= overlap < size")
    ...
```

Function ၏ argument သုံးခုမှာ —

- `words` — token များ၏ list (tokenize ရလဒ်)။
- `size` — chunk တစ်ခုတွင် ပါဝင်မည့် token အရေအတွက်။
- `overlap` — chunk နှစ်ခုကြား ထပ်နေမည့် token အရေအတွက်။

### Chained comparison `0 <= overlap < size`

```python
print(0 <= 0 < 6, 0 <= 2 < 6, 0 <= 6 < 6)
```

Output —

```text
True True False
```

Python သည် `0 <= overlap < size` ကို `(0 <= overlap) and (overlap < size)` ဟု ဖတ်သည်။ ဤအပိုင်းက
overlap ကို **အနုတ်မဖြစ်ရ** နှင့် **size ထက် ငယ်ရမည်** ဟု တစ်ပြိုင်နက် စစ်သည်။

### `raise ValueError(...)` — Guard Clause

```python
def chunk_words(words, size, overlap):
    if not 0 <= overlap < size:
        raise ValueError("require 0 <= overlap < size")
    return []


for overlap in [0, 2, 6, 7]:
    try:
        chunk_words(["a", "b", "c", "d", "e", "f"], 6, overlap)
        print("overlap=%d -> ok" % overlap)
    except ValueError as exc:
        print("overlap=%d -> ValueError: %s" % (overlap, exc))
```

Output —

```text
overlap=0 -> ok
overlap=2 -> ok
overlap=6 -> ValueError: require 0 <= overlap < size
overlap=7 -> ValueError: require 0 <= overlap < size
```

`raise` က error တစ်ခုကို ဖန်တီး၍ function ကို ချက်ချင်း ရပ်လိုက်သည်။ `try`/`except` က ထို error ကို
ဖမ်းပြီး program မကျဆင်းစေဘဲ ဆက်လုပ်ခွင့်ပေးသည်။ ဤနေရာတွင် `overlap` သည် `size` နှင့် တူညီ
သို့မဟုတ် ထို့ထက် ကြီးပါက ဖမ်းမိပြီး **`ValueError`** ဖြစ်သည်။

---

## 4. Guard မရှိပါက — `stride = 0` Trap

Guard က အလှဆင်မဟုတ်ပါ။ `overlap == size` ဖြစ်ပါက `stride = size - overlap == 0` ဖြစ်ပြီး chunk
အသစ်မရွေ့တော့သဖြင့် loop က **မဆုံးနိုင်တော့ပါ**။ ဤဖြစ်ရပ်ကို iteration အရေအတွက် ကန့်သတ်ထားသော
variant တစ်ခုနှင့် သရုပ်ပြမည်။

```python
def naive_chunk(words, size, overlap, limit=6):
    stride = size - overlap          # guard မရှိ
    n = len(words)
    chunks, start, steps = [], 0, 0
    while start < n and steps < limit:
        chunks.append(words[start:start + size])
        start += stride
        steps += 1
    return chunks, steps


words = ["Alpha", "acquired", "Beta", "Beta", "operates", "Gamma"]
chunks, steps = naive_chunk(words, size=6, overlap=6)   # stride = 0
print("steps run before the cap :", steps)
print("distinct chunk count     :", len(set(tuple(c) for c in chunks)))
print("first chunk              :", chunks[0])
```

Output —

```text
steps run before the cap : 6
distinct chunk count     : 1
first chunk              : ['Alpha', 'acquired', 'Beta', 'Beta', 'operates', 'Gamma']
```

`stride=0` ဖြစ်သဖြင့် `start` သည် မတိုးတော့ဘဲ chunk **တူတူကို** ထပ်ခါထပ်ခါ ထည့်သည် (distinct chunk
count = 1)။ Guard မရှိသော production run တွင် ဤ loop သည် အဆုံးမရှိ run ပြီး worker တစ်ခုလုံး ပိတ်ဆို့
သွားမည်။ ဒါကြောင့် `chunk_words` သည် ပထမဆုံး လိုင်းတွင် `raise` ဖြင့် ကာကွယ်ထားသည်။

---

## 5. `stride = size - overlap`

```python
size, overlap = 6, 2
stride = size - overlap
print("size=%d overlap=%d -> stride=%d" % (size, overlap, stride))
for s in [(6, 0), (6, 2), (5, 3)]:
    print("size=%d overlap=%d -> stride=%d" % (s[0], s[1], s[0] - s[1]))
```

Output —

```text
size=6 overlap=2 -> stride=4
size=6 overlap=0 -> stride=6
size=6 overlap=2 -> stride=4
size=5 overlap=3 -> stride=2
```

`for s in [...]:` သည် tuple များကို တစ်ခုချင်း ဖတ်ပြီး `s[0]`၊ `s[1]` ဖြင့် ဖွင့်သည်။ `stride` သည်
chunk အသစ်တစ်ခု စမည့် အကွာအဝေး ဖြစ်သည်။ `overlap=0` ဖြစ်ပါက `stride == size` ဖြစ်ပြီး chunk
များ ထပ်မနေပါ။ `overlap` တိုးလာလျှင် `stride` ငယ်လာပြီး chunk အရေအတွက် တိုးလာသည် — ဆိုလိုသည်မှာ
token cost တိုးလာသည်။

---

## 6. `while` loop နှင့် Slicing

```python
words = ["Alpha", "acquired", "Beta", "Beta", "operates", "Gamma",
         "Gamma", "founded", "Delta", "Delta", "partners", "Epsilon",
         "Epsilon", "supplies", "Zeta", "Zeta", "acquired", "Alpha"]
size, overlap = 6, 0
stride = size - overlap
n = len(words)
start = 0
while start < n:
    print("start=%2d -> words[%d:%d] len=%d %s"
          % (start, start, start + size, len(words[start:start + size]), words[start:start + size]))
    if start + size >= n:
        break
    start += stride
```

Output —

```text
start= 0 -> words[0:6] len=6 ['Alpha', 'acquired', 'Beta', 'Beta', 'operates', 'Gamma']
start= 6 -> words[6:12] len=6 ['Gamma', 'founded', 'Delta', 'Delta', 'partners', 'Epsilon']
start=12 -> words[12:18] len=6 ['Epsilon', 'supplies', 'Zeta', 'Zeta', 'acquired', 'Alpha']
```

`for` မသုံးဘဲ `while` သုံးရသည့် အကြောင်းရင်းမှာ `start` ကို `stride` အလိုက် **ခုန်** စေလိုခြင်း
ဖြစ်သည်။ `for` loop က index ကို တစ်လုံးချင်း တိုးသည်။

`words[start:start + size]` သည် **list slicing** ဖြစ်သည်။ Index `start` မှ စ၍ `start + size`
မတိုင်မီအထိ element များကို ယူသည် (အဆုံးအပိုင်း `size` သည် မပါဝင်ပါ)။

```python
words = ["Alpha", "acquired", "Beta", "Beta", "operates", "Gamma", "Delta"]
print(words[0:6])
print(words[6:12])
print(words[4:10])
```

Output —

```text
['Alpha', 'acquired', 'Beta', 'Beta', 'operates', 'Gamma']
['Delta']
['operates', 'Gamma', 'Delta']
```

`words[6:12]` တွင် element တစ်လုံးသာ ကျန်သဖြင့် slice သည် **ကျန်သလောက်ကိုသာ** ပြန်ပေးသည်။
List ကျော်လွန်သော index ပေးလျှင် `IndexError` မဖြစ်ဘဲ slice က ကျန်သလောက်ဖြင့် ရပ်သည်။ ဤ
အချက်ကြောင့် `start + size >= n` ဖြစ်သည့် နောက်ဆုံး chunk သည် size ငယ်နိုင်သည်။

---

## 7. `enumerate()` ဖြင့် ရလဒ်ထုတ်ခြင်း

```python
chunks = [["Alpha", "acquired", "Beta"], ["Gamma", "founded", "Delta"]]
for i, c in enumerate(chunks):
    print("  chunk %d: %s" % (i, " ".join(c)))
print(" ".join(["Alpha", "acquired", "Beta"]))
```

Output —

```text
  chunk 0: Alpha acquired Beta
  chunk 1: Gamma founded Delta
Alpha acquired Beta
```

`enumerate(chunks)` သည် element တိုင်းအတွက် `(index, element)` tuple ကို ပေးသည်။ ဒါကြောင့်
`for i, c in ...` ဖြင့် index နှင့် content ကို တစ်ပြိုင်နက် ရနိုင်သည်။ `" ".join(c)` သည် token
list ကို space ဖြင့် ဆက်၍ စာသားတစ်ကြောင်း ဖန်တီးသည်။

### `chunk_words()` အပြည့်အစုံ

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
    chunks = []
    start = 0
    while start < n:
        chunks.append(words[start:start + size])
        if start + size >= n:
            break
        start += stride
    return chunks


words = tokenize(CORPUS)
chunks = chunk_words(words, size=6, overlap=0)
print("chunk count : %d" % len(chunks))
print("chunk sizes : %s" % [len(c) for c in chunks])
for i, c in enumerate(chunks):
    print("  chunk %d: %s" % (i, " ".join(c)))
```

Output —

```text
chunk count : 3
chunk sizes : [6, 6, 6]
  chunk 0: Alpha acquired Beta Beta operates Gamma
  chunk 1: Gamma founded Delta Delta partners Epsilon
  chunk 2: Epsilon supplies Zeta Zeta acquired Alpha
```

`[len(c) for c in chunks]` သည် **list comprehension** ဖြစ်သည်။ Chunk တိုင်း၏ အရှည်ကို list
အသစ်တစ်ခုအဖြစ် စုစည်းသည်။ `return chunks` က ရလဒ်ကို function ပြင်ပ ပြန်ပေးသည်။

---

## 8. Remainder Trap — နောက်ဆုံး Token များ ဆုံးရှုံးခြင်း

`while start < n` (ဤ exercise ၏ version) သည် ကျန်တာကို **အားလုံး ဖုံးလွှမ်း** သည်။ သို့သော်
`while start + size <= n` ဟု ရေးမိပါက **နောက်ဆုံး ကျန်တဲ့ token များ ကျန်ခဲ့မည်**။ n သည် size
နှင့် မစားပြတ်သည့်အခါ ဤ bug ပေါ်လာသည်။

```python
import re

CORPUS = (
    "Alpha acquired Beta . Beta operates Gamma . Gamma founded Delta . "
    "Delta partners Epsilon . Epsilon supplies Zeta . Zeta acquired Alpha ."
)


def tokenize(text):
    return re.findall(r"[A-Za-z]+", text)


def correct_chunks(words, size, overlap):
    stride = size - overlap
    n = len(words)
    chunks, start = [], 0
    while start < n:
        chunks.append(words[start:start + size])
        if start + size >= n:
            break
        start += stride
    return chunks


def drop_remainder(words, size, overlap):
    stride = size - overlap
    n = len(words)
    chunks, start = [], 0
    while start + size <= n:
        chunks.append(words[start:start + size])
        start += stride
    return chunks


words = tokenize(CORPUS)
correct = correct_chunks(words, size=4, overlap=0)
dropped = drop_remainder(words, size=4, overlap=0)
print("correct sizes : %s  (covers %d tokens)" % ([len(c) for c in correct], sum(len(c) for c in correct)))
print("dropped sizes : %s  (covers %d tokens)" % ([len(c) for c in dropped], sum(len(c) for c in dropped)))
print("correct tail  : %s" % correct[-1])
print("lost tail     : %s" % words[len(words) - (len(words) % 4):])
```

Output —

```text
correct sizes : [4, 4, 4, 4, 2]  (covers 18 tokens)
dropped sizes : [4, 4, 4, 4]  (covers 16 tokens)
correct tail  : ['acquired', 'Alpha']
lost tail     : ['acquired', 'Alpha']
```

`size=4` ဖြစ်ပါက ၁၈ သည် ၄ နှင့် မစားပြတ်သဖြင့် နောက်ဆုံး token ၂ လုံး ကျန်သည်။ `correct_chunks`
သည် ထို ၂ လုံးကို chunk အဖြစ် ထည့်သည် (18 tokens ဖုံးလွှမ်းသည်)။ `drop_remainder` သည် ထို ၂ လုံးကို
**စွန့်ပစ်** သည် (16 tokens သာ ဖုံးလွှမ်းသည်)။ ဆုံးရှုံးသွားသည့် token များသည် corpus ၏ နောက်ဆုံး
token ၂ လုံးနှင့် ထပ်တူဖြစ်သည် — အဆုံးစွန်း relationship (`Zeta acquired Alpha`) ဆုံးရှုံးမည်။

---

## 9. Boundary Table — size/overlap ရွေးချယ်မှု

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
for size, overlap in [(6, 0), (6, 2), (5, 0), (5, 3), (4, 0)]:
    chunks = chunk_words(words, size, overlap)
    print("size=%d overlap=%d stride=%d -> %d chunks sizes=%s"
          % (size, overlap, size - overlap, len(chunks), [len(c) for c in chunks]))
```

Output —

```text
size=6 overlap=0 stride=6 -> 3 chunks sizes=[6, 6, 6]
size=6 overlap=2 stride=4 -> 4 chunks sizes=[6, 6, 6, 6]
size=5 overlap=0 stride=5 -> 4 chunks sizes=[5, 5, 5, 3]
size=5 overlap=3 stride=2 -> 8 chunks sizes=[5, 5, 5, 5, 5, 5, 5, 4]
size=4 overlap=0 stride=4 -> 5 chunks sizes=[4, 4, 4, 4, 2]
```

| size | overlap | stride | chunks | sizes | မှတ်ချက် |
| --- | --- | --- | --- | --- | --- |
| 6 | 0 | 6 | 3 | `[6, 6, 6]` | ထပ်မနေ၊ နောက်ဆုံး chunk ပြည့် |
| 6 | 2 | 4 | 4 | `[6, 6, 6, 6]` | Boundary တိုင်း token ၂ လုံး ထပ် |
| 5 | 0 | 5 | 4 | `[5, 5, 5, 3]` | နောက်ဆုံး chunk ကျန်သလောက် |
| 5 | 3 | 2 | 8 | `[5, 5, 5, 5, 5, 5, 5, 4]` | Overlap များသဖြင့် chunk များ နှစ်ဆနီးပါး |
| 4 | 0 | 4 | 5 | `[4, 4, 4, 4, 2]` | နောက်ဆုံး ၂ လုံး ကျန် |

ဇယားက trade-off ကို ပြသည် — `size=5, overlap=3` သည် ၈ chunk ဖြစ်သဖြင့် token ကုန်ကျစရိတ် (extraction
cost) သည် `size=6, overlap=0` ထက် ခန့်မှန်းချေ ၂ ဆကျော် တိုးသည်။ Overlap သည် boundary
relationship များ မပြတ်စေရန် အထောက်အကူဖြစ်သော်လည်း cost ဖြင့် ဝယ်ရသည်။

---

## 10. Assertion များ

`lab.py` ၏ exercise သည် ရလဒ်ကို `assert` ဖြင့် စစ်သည်။ `assert condition` သည် condition
မှန်ပါက ဘာမှမလုပ်ဘဲ ဆက်သွားပြီး မှားပါက `AssertionError` ဖြင့် ကျဆင်းသည်။

```python
words = ["Alpha", "acquired", "Beta", "Beta", "operates", "Gamma",
         "Gamma", "founded", "Delta", "Delta", "partners", "Epsilon",
         "Epsilon", "supplies", "Zeta", "Zeta", "acquired", "Alpha"]
chunks = [words[i * 6:(i + 1) * 6] for i in range(3)]
print("all boundary-aligned :", all(c == words[i * 6:(i + 1) * 6] for i, c in enumerate(chunks)))
print([len(c) for c in chunks])
```

Output —

```text
all boundary-aligned : True
[6, 6, 6]
```

`all(iterable)` သည် element အားလုံး truthy ဖြစ်မှ `True` ပြန်သည်။ ဤနေရာတွင် chunk တိုင်းသည်
`words` ၏ သက်ဆိုင်ရာ slice နှင့် တူကြောင်း စစ်သည်။ `range(3)` ကြောင့် i သည် `0, 1, 2` ဖြစ်ပြီး
`words[i*6:(i+1)*6]` ကို ဖန်တီးသည်။

---

## 11. Code တစ်ခုလုံး — Run လုပ်နိုင်သော Version

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
    chunks = []
    start = 0
    while start < n:
        chunks.append(words[start:start + size])
        if start + size >= n:
            break
        start += stride
    return chunks


words = tokenize(CORPUS)
chunks = chunk_words(words, size=6, overlap=0)
print("token count : %d" % len(words))
print("chunk count : %d" % len(chunks))
print("chunk sizes : %s" % [len(c) for c in chunks])
for i, c in enumerate(chunks):
    print("  chunk %d: %s" % (i, " ".join(c)))
```

Output —

```text
token count : 18
chunk count : 3
chunk sizes : [6, 6, 6]
  chunk 0: Alpha acquired Beta Beta operates Gamma
  chunk 1: Gamma founded Delta Delta partners Epsilon
  chunk 2: Epsilon supplies Zeta Zeta acquired Alpha
```

ဤ script ကို `python3 fixed_chunking.py` ဖြင့် run လျှင် အထက်ပါ output ကို အတိအကျ ရသည်။

---

## 12. ကိုယ်တိုင်လေ့ကျင့်ကြည့်ပါ

**မေးခွန်း** — Token ၁၈ လုံးပါသော `CORPUS` ကို `chunk_words(words, size=5, overlap=0)` ဖြင့်
ခွဲလျှင် chunk အရေအတွက်နှင့် နောက်ဆုံး chunk သည် ဘာဖြစ်မလဲ။

1. chunk ၄ ခု၊ နောက်ဆုံး chunk = `['Zeta', 'acquired', 'Alpha']`
2. chunk ၃ ခု၊ နောက်ဆုံး chunk = `['Zeta', 'acquired', 'Alpha']`
3. chunk ၄ ခု၊ နောက်ဆုံး chunk = `['Epsilon', 'supplies', 'Zeta', 'Zeta', 'acquired']`
4. `ValueError` ဖြစ်သည် — ၁၈ သည် ၅ နှင့် မစားပြတ်ပါ

<details>
<summary>အဖြေ ကြည့်ရန်</summary>

**အဖြေ — 1. chunk ၄ ခု၊ နောက်ဆုံး chunk = `['Zeta', 'acquired', 'Alpha']`**

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
chunks = chunk_words(words, size=5, overlap=0)
print("chunk count:", len(chunks))
print("last chunk:", chunks[-1])
```

Output —

```text
chunk count: 4
last chunk: ['Zeta', 'acquired', 'Alpha']
```

အကြောင်းရင်း — `stride=5` ဖြစ်သဖြင့် `start` သည် `0, 5, 10, 15` သို့ ရွေ့သည်။ `start=15` တွင်
`words[15:20]` ကို ယူရာ token ၃ လုံးသာ ကျန်သဖြင့် နောက်ဆုံး chunk သည် ၃ လုံးဖြစ်သည်။
`[15, 16, 17]` မှာ `Zeta, acquired, Alpha` ဖြစ်သည်။

</details>

---

**အဓိက မှတ်ထားရန်** — Fixed-size chunking သည် `size`၊ `overlap` နှင့် `stride = size - overlap`
သုံးလုံးဖြင့် အပြည့်အဝ ဖော်ပြနိုင်သည်။ Boundary case နှစ်ခုကို အမြဲ စစ်ရမည် — (၁) `overlap >= size`
ဖြစ်ပါက `stride <= 0` ဖြစ်ပြီး infinite loop ဖြစ်သဖြင့် guard လိုသည်၊ (၂) `len(words)` သည်
`size` နှင့် မစားပြတ်ပါက နောက်ဆုံး chunk ကို မစွန့်ရ။ Overlap သည် boundary relationship
recall ကို တိုးပေမဲ့ token cost ကို `size / stride` အချိုးဖြင့် တိုးစေသည်။
