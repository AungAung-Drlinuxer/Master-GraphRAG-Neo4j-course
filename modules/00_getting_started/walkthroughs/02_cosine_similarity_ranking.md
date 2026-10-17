# Walkthrough 02 — Cosine Similarity Ranking (Exercise 2)

> ဤဖိုင်သည် `solution.md` ၏ Exercise 2 ကို **Python အခြေခံမှ စ၍** အပိုင်းလိုက် ရှင်းပြသည့်
> walkthrough ဖြစ်သည်။ Format သည် `walkthroughs/01_pipeline_stage_ordering.md` နှင့် တူညီသည်။

---

ဤ exercise တွင် Python ကို အသုံးပြုပြီး Query တစ်ခုနှင့် အနီးစပ်ဆုံးတူညီသော text chunks တွေကို
similarity score အလိုက် စီစဉ်ခြင်းကို လေ့လာပါမည်။

ဤနည်းလမ်းကို RAG (Retrieval-Augmented Generation) chatbot တွေတွင် အသုံးပြုသည်။ ဥပမာ
IT Help Chatbot တွင် user က Kubernetes အကြောင်း မေးသည့်အခါ knowledge base ထဲက သက်ဆိုင်သော
document chunks တွေကို ရှာဖွေရန် အသုံးဝင်သည်။

ဤ code တွင် အဓိကလေ့လာရမည့် Python concepts များသည် —

- `import` နှင့် `math` module
- `def` နှင့် function
- `if`၊ `raise`၊ `return`
- `sum()`၊ `zip()`၊ `len()`
- List comprehension
- `lambda` နှင့် `sort()`
- `enumerate()` နှင့် tuple unpacking
- Cosine Similarity နှင့် vector ranking

---

## 1. Cosine Similarity ဟူသည် ဘာလဲ။

Cosine Similarity သည် vector နှစ်ခု၏ ဦးတည်ရာ (direction) မည်မျှ တူညီသည်ကို
တိုင်းတာသည့် နည်းလမ်းတစ်ခုဖြစ်သည်။

RAG system တွင် text ကို embedding model နှင့် vector အဖြစ်ပြောင်းပြီး query vector နှင့်
document chunk vector တို့၏ similarity ကို တွက်ချက်နိုင်သည်။

Embedding model က Query နှင့် chunks တွေကို vector ပြောင်းပေးပြီး Cosine Similarity က
ဘယ် chunk တွေက query နှင့် ပိုတူညီသည်ကို အမှတ်ပေးသည်။

Cosine Similarity ၏ formula က —

```text
cosine(A, B) = (A · B) / (||A|| · ||B||)
```

ဤတွင် —

- `A`, `B` — Vector နှစ်ခု
- `A · B` — Dot product
- `||A||`, `||B||` — Vector တစ်ခုစီ၏ magnitude (norm)

ပုံမှန်အားဖြင့် non-zero vector တွေအတွက် score က `-1` နှင့် `1` ကြားတွင် ရှိသည်။ Score က `1` နှင့်
နီးလေလေ direction ပိုတူလေလေ ဖြစ်သည်။ ဤ exercise ထဲက vector တွေတွင် component အားလုံး
non-negative ဖြစ်သည့်အတွက် score တွေက `0` နှင့် `1` ကြားတွင် ရှိပါမည်။

---

## 2. `import math`

```python
import math
```

`import` က အခြား module တစ်ခုထဲက functions တွေကို အသုံးပြုနိုင်ရန် ထည့်သွင်းပေးခြင်း ဖြစ်သည်။

`math` သည် Python ၏ built-in standard library module ဖြစ်ပြီး သင်္ချာဆိုင်ရာ functions တွေ
ပါဝင်သည်။ ဤ exercise တွင် —

```python
math.sqrt(...)
```

ကို အသုံးပြုသည်။ `math.sqrt()` က square root ကို တွက်ပေးသည်။

ဥပမာ —

```python
import math

print(math.sqrt(25))
print(math.sqrt(9))
```

Output —

```text
5.0
3.0
```

Vector norm တွက်သည့်အခါ square root လိုအပ်ခြင်းကြောင့် `math.sqrt()` ကို အသုံးပြုထားသည်။

---

## 3. `cosine_similarity()` function ကို ဖန်တီးခြင်း

```python
def cosine_similarity(left, right):
```

ဤတွင် `cosine_similarity` ဆိုသည့် function ကို သတ်မှတ်ထားသည်။

- `left` — ပထမ vector
- `right` — ဒုတိယ vector

ဥပမာ —

```python
left = [1, 2, 3]
right = [4, 5, 6]
```

ဤ function က vector နှစ်ခုကို လက်ခံပြီး similarity score တစ်ခု ပြန်ပေးမည်။

### Step 3.1 — Vector dimensions စစ်ဆေးခြင်း

```python
if len(left) != len(right):
    raise ValueError("dimension mismatch")
```

`len()` က list ထဲက elements အရေအတွက်ကို ပြန်ပေးသည်။

```python
left = [1, 2, 3, 4]
right = [5, 6, 7, 8]

print(len(left))
print(len(right))
```

Output —

```text
4
4
```

Vector နှစ်ခုစလုံးတွင် dimensions ၄ ခုစီ ရှိသည်။

`!=` က မတူညီပါဟု ဆိုလိုသည်။ ထို့ကြောင့် —

```python
if len(left) != len(right):
```

သည် vector နှစ်ခု၏ dimensions မတူညီပါသလားဟု စစ်ခြင်း ဖြစ်သည်။ မတူညီလျှင် —

```python
raise ValueError("dimension mismatch")
```

က `ValueError` exception ကို ဖြစ်စေပြီး function ကို ရပ်တန့်စေသည်။

ဥပမာ —

```python
cosine_similarity([1, 2, 3], [4, 5])
```

ဤ vector တွေတွင် dimensions မတူညီသောအတွက် `ValueError: dimension mismatch` ဖြစ်ပါမည်။

ဘာကြောင့် စစ်ရသလား။ Vector နှစ်ခုကို component တစ်ခုစီအလိုက် နှိုင်းယှဉ်ပြီး dot product
တွက်ရန် dimension တူညီရန် လိုအပ်သည်။

---

## 4. Dot Product တွက်ချက်ခြင်း

```python
dot = sum(a * b for a, b in zip(left, right))
```

ဤတစ်ကြောင်းတွင် `zip()`၊ multiplication `*`၊ generator expression နှင့် `sum()` တို့ ပါဝင်သည်။

### Step 4.1 — `zip(left, right)`

`zip()` က list နှစ်ခုထဲက တူညီသော position တွင်ရှိသည့် elements တွေကို တွဲပေးသည်။

```python
left = [1, 2, 3]
right = [4, 5, 6]

print(list(zip(left, right)))
```

Output —

```python
[(1, 4), (2, 5), (3, 6)]
```

ပထမ list ၏ `1` ကို ဒုတိယ list ၏ `4` နှင့် တွဲပေးပြီး၊ `2` ကို `5` နှင့်၊ `3` ကို `6` နှင့်
တွဲပေးသည်။

### Step 4.2 — `a * b`

```python
a * b
```

တွဲထားသော values နှစ်ခုကို မြှောက်ခြင်း ဖြစ်သည်။ အထက်က ဥပမာတွင် —

```text
1 * 4 = 4
2 * 5 = 10
3 * 6 = 18
```

### Step 4.3 — `sum()`

```python
dot = sum(a * b for a, b in zip(left, right))
```

`sum()` က မြှောက်လဒ်တွေကို ပေါင်းပေးသည်။

```text
4 + 10 + 18 = 32
```

ထို့ကြောင့် `dot = 32` ဖြစ်သည်။

ဤသို့ vector တစ်ခု၏ component တွေကို နောက် vector ၏ component တွေနှင့် တစ်ခုချင်းမြှောက်ပြီး
ပေါင်းထားခြင်းကို **Dot Product** ဟုခေါ်သည်။

---

## 5. Vector Norm တွက်ချက်ခြင်း

```python
norm_left = math.sqrt(sum(a * a for a in left))
norm_right = math.sqrt(sum(b * b for b in right))
```

ဤနေရာတွင် vector တစ်ခုစီ၏ norm ကို တွက်သည်။ Norm သည် vector ၏ magnitude သို့မဟုတ်
အလျားကို ဆိုလိုသည်။ Formula က —

```text
||A|| = sqrt(a₁² + a₂² + ⋯ + aₙ²)
```

ဥပမာ — `left = [3, 4]`

ပထမဆုံး component တစ်ခုချင်းစီကို သူ့ကိုယ်သူ မြှောက်ပါမည်။

```text
3 * 3 = 9
4 * 4 = 16
```

ပြီးလျှင် ပေါင်းပါမည်။

```text
9 + 16 = 25
```

နောက်ဆုံး square root ယူပါမည်။

```text
sqrt(25) = 5
```

Python နှင့်ဆိုလျှင် —

```python
left = [3, 4]
norm_left = math.sqrt(sum(a * a for a in left))

print(norm_left)
```

Output —

```text
5.0
```

`norm_right` ကလည်း `right` vector အတွက် အလားတူ တွက်ချက်ခြင်း ဖြစ်သည်။

---

## 6. Zero Vector ကို စစ်ဆေးခြင်း

```python
if norm_left == 0.0 or norm_right == 0.0:
    return 0.0
```

ဤတွင် operator နှစ်ခုကို သတိပြုပါ။

- `==` — တူညီသလား စစ်ဆေးခြင်း။
- `or` — အခြေအနေနှစ်ခုထဲက တစ်ခုခု မှန်လျှင် condition တစ်ခုလုံး မှန်ခြင်း။

Vector တစ်ခု၏ norm က `0.0` ဖြစ်သည်ဆိုလျှင် ထို vector သည် zero vector ဖြစ်သည်။
Zero vector နှင့် cosine similarity တွက်သည့်အခါ denominator က သုညဖြစ်သွားနိုင်သည်။

```text
dot product / 0
```

ဤသို့ division by zero မဖြစ်အောင် —

```python
return 0.0
```

နှင့် score `0.0` ကို ပြန်ပေးထားခြင်း ဖြစ်သည်။ ၎င်းသည် application အတွက် ရွေးချယ်ထားသော **fallback**
ဖြစ်သည်။ သင်္ချာအရ zero vector ၏ cosine similarity ကို ပုံမှန်အားဖြင့် သတ်မှတ်နိုင်ခြင်း မရှိပါ။

---

## 7. Cosine Similarity Score ပြန်ပေးခြင်း

```python
return dot / (norm_left * norm_right)
```

၎င်းသည် function ၏ အဓိကတွက်ချက်မှု ဖြစ်သည်။

```text
cosine(A, B) = (A · B) / (||A|| · ||B||)
```

အပေါ်တွင် တွက်ထားသော dot product ကို vector နှစ်ခု၏ norm မြှောက်လဒ်နှင့် စားပေးသည်။

ဥပမာ —

```python
print(cosine_similarity([1, 0], [1, 0]))
print(cosine_similarity([1, 0], [0, 1]))
```

Output —

```text
1.0
0.0
```

ပထမ pair က direction တူသောကြောင့် score `1.0` ဖြစ်သည်။ ဒုတိယ pair က direction တွေ
perpendicular ဖြစ်သောကြောင့် score `0.0` ဖြစ်သည်။

---

## 8. Query Vector သတ်မှတ်ခြင်း

```python
QUERY_VECTOR = [0.90, 0.10, 0.00, 0.20]
```

ဤ list က user query ကို ကိုယ်စားပြုသည့် vector ဖြစ်သည်။ ဤဥပမာတွင် vector dimensions
၄ ခု ရှိသည်။

တကယ့် RAG system တွင် embedding model က query text ကို vector အဖြစ် ပြောင်းပေးခြင်းဖြစ်ပြီး
ဤနံပါတ်တွေကို ကိုယ်တိုင် ရွေးထည့်လေ့မရှိပါ။ ဤ exercise သည် cosine similarity ကို
လေ့လာနိုင်ရန် vector တွေကို ရိုးရှင်းစွာ သတ်မှတ်ထားခြင်း ဖြစ်သည်။

---

## 9. `CHUNK_VECTORS` — Document chunks တွေ၏ vectors

```python
CHUNK_VECTORS = {
    "chunk-01": [0.85, 0.15, 0.05, 0.10],
    "chunk-02": [0.10, 0.80, 0.60, 0.10],
    "chunk-03": [0.00, 0.20, 0.95, 0.30],
    "chunk-04": [0.70, 0.05, 0.10, 0.90],
}
```

ဤ data structure က dictionary ဖြစ်သည်။

- Key — Chunk ID၊ ဥပမာ `"chunk-01"`
- Value — ထို chunk ကို ကိုယ်စားပြုသည့် vector

Query vector နှင့် chunk vector တစ်ခုချင်းစီကို နှိုင်းယှဉ်ပြီး score တွက်မည်။

ဥပမာ —

```python
CHUNK_VECTORS["chunk-01"]
```

ဤသို့ရေးလျှင် `chunk-01` ၏ vector ကို ပြန်ရသည်။ Chunk ID တွေကို key အဖြစ်
အသုံးပြုထားသောအတွက် similarity score တစ်ခုချင်းစီသည် ဘယ် chunk နှင့် သက်ဆိုင်သည်ကို
သိနိုင်သည်။

---

## 10. `rank_chunks()` function — Chunk တွေကို Ranking လုပ်ခြင်း

```python
def rank_chunks(query, chunks):
    scored = [
        (chunk_id, cosine_similarity(query, vector))
        for chunk_id, vector in chunks.items()
    ]
    scored.sort(key=lambda item: (-item[1], item[0]))
    return scored
```

ဤ function ၏ ရည်ရွယ်ချက်က chunk တစ်ခုချင်းစီ၏ similarity score ကို တွက်ချက်ပြီး
score အမြင့်ဆုံးကနေ အနိမ့်ဆုံးအထိ စီပေးရန် ဖြစ်သည်။

### Step 10.1 — `chunks.items()`

```python
for chunk_id, vector in chunks.items()
```

Dictionary ၏ `.items()` က key နှင့် value ကို တွဲပြီး ထုတ်ပေးသည်။

ဥပမာ —

```python
chunks = {
    "chunk-01": [0.85, 0.15],
    "chunk-02": [0.10, 0.80],
}

for chunk_id, vector in chunks.items():
    print(chunk_id, vector)
```

Output —

```text
chunk-01 [0.85, 0.15]
chunk-02 [0.1, 0.8]
```

ဤတွင် `chunk_id` ထဲကို key ဝင်ပြီး `vector` ထဲကို value ဝင်သည်။ ဤသို့ variable နှစ်ခုထဲကို
တန်ဖိုးခွဲထည့်ခြင်းကို **unpacking** ဟုခေါ်သည်။

### Step 10.2 — List comprehension နှင့် score တွက်ခြင်း

```python
scored = [
    (chunk_id, cosine_similarity(query, vector))
    for chunk_id, vector in chunks.items()
]
```

ဤ code က chunk တစ်ခုချင်းစီအတွက် tuple တစ်ခု ဖန်တီးသည်။

```python
(chunk_id, cosine_similarity(query, vector))
```

Tuple ထဲတွင် —

- Chunk ID
- ထို chunk ၏ cosine similarity score

တို့ ပါဝင်သည်။ ဥပမာ result က ဤသို့ပုံစံ ဖြစ်ပါမည်။

### ဥပမာ result ပုံစံ

```python
[
    ("chunk-01", 0.991173),
    ("chunk-02", 0.202864),
    ("chunk-03", 0.084898),
    ("chunk-04", 0.767112),
]
```

အခုအချိန်တွင် ဤ list က မူလ dictionary အစီအစဉ်အတိုင်း ဖြစ်နေသေးသည်။ Ranking
မလုပ်ရသေးပါ။

### Step 10.3 — `scored.sort(...)`

```python
scored.sort(key=lambda item: (-item[1], item[0]))
```

ဤတစ်ကြောင်းက ranking လုပ်ပေးသည့် အဓိက code ဖြစ်သည်။ အရင်ဆုံး `sort()` ကို
နားလည်ရအောင်။

```python
numbers = [30, 10, 20]
numbers.sort()

print(numbers)
```

Output —

```text
[10, 20, 30]
```

`sort()` က list ကို မူလ list အတွင်းတွင်သာ ပြင်ဆင်စီစဉ်ပေးသည်။ ဤ exercise တွင် `key`
parameter နှင့် sorting လုပ်မည့်စည်းမျဉ်းကို သတ်မှတ်ထားသည်။

### `lambda item`

```python
lambda item: (-item[1], item[0])
```

`lambda` သည် နာမည်မပေးထားသော function အသေးစားတစ်ခု ဖန်တီးသည့်နည်းလမ်း ဖြစ်သည်။
ဤ expression ကို ပုံမှန် function နှင့် ရေးမည်ဆိုလျှင် —

```python
def sort_key(item):
    return (-item[1], item[0])
```

နှင့် အဓိပ္ပာယ်တူသည်။

ဥပမာ —

```python
item = ("chunk-01", 0.991173)
```

ဤ tuple တွင် —

- `item[0]` က `"chunk-01"`
- `item[1]` က `0.991173`

ဖြစ်သည်။

### ဘာကြောင့် `-item[1]` သုံးခြင်းလဲ။

Python ၏ `sort()` က ပုံမှန်အားဖြင့် ascending order နှင့် စီသည်။

```python
scores = [0.20, 0.99, 0.76]
scores.sort()

print(scores)
```

Output —

```python
[0.2, 0.76, 0.99]
```

သို့သော် ကျွန်တော်တို့က similarity score အမြင့်ဆုံးကို အရင်ပြချင်သည်။

```python
scores = [0.20, 0.99, 0.76]
scores.sort(key=lambda score: -score)

print(scores)
```

Output —

```python
[0.99, 0.76, 0.2]
```

Score ကို အနုတ်လက္ခဏာ ပြောင်းပြီး sorting လုပ်ခြင်းကြောင့် score အမြင့်ဆုံးက
အရင်ရောက်လာသည်။

### ဘာကြောင့် `item[0]` ကိုလည်း ထည့်ထားခြင်းလဲ။

```python
(-item[1], item[0])
```

ဤတွင် sorting key နှစ်ခုရှိသည်။

- `-item[1]` — Similarity score အမြင့်ဆုံးကို အရင်စီခြင်း။
- `item[0]` — Score တူညီနေပါက chunk ID ကို alphabetical order အတိုင်း စီခြင်း။

ဥပမာ —

```python
scored = [
    ("chunk-02", 0.9),
    ("chunk-01", 0.9),
    ("chunk-03", 0.7),
]

scored.sort(key=lambda item: (-item[1], item[0]))

print(scored)
```

Output —

```python
[('chunk-01', 0.9), ('chunk-02', 0.9), ('chunk-03', 0.7)]
```

Score တူညီနေသော `chunk-01` နှင့် `chunk-02` ကို chunk ID အရ စီပေးထားသည်။ ထို့ကြောင့်
output က **deterministic** ဖြစ်သည်။

### Step 10.4 — `return scored`

```python
return scored
```

Sorting ပြီးသွားသည့် list ကို function က ပြန်ပေးသည်။

---

## 11. `enumerate()` နှင့် Result ကို ပြသခြင်း

```python
for rank, (chunk_id, score) in enumerate(
    rank_chunks(QUERY_VECTOR, CHUNK_VECTORS),
    start=1
):
    print("%d. %s similarity=%.6f" % (rank, chunk_id, score))
```

ဤအပိုင်းတွင် ranking လုပ်ပြီးသား result တွေကို နံပါတ်တပ်ပြီး ပြသသည်။

### `rank_chunks(QUERY_VECTOR, CHUNK_VECTORS)`

ဤ function call က query vector နှင့် chunk vectors တွေကို အသုံးပြုပြီး ranking result ကို
ပြန်ပေးသည်။

### `enumerate(..., start=1)`

`enumerate()` က item တစ်ခုချင်းစီအတွက် counter တစ်ခု ထည့်ပေးသည်။

```python
fruits = ["apple", "banana", "orange"]

for rank, fruit in enumerate(fruits, start=1):
    print(rank, fruit)
```

Output —

```text
1 apple
2 banana
3 orange
```

`start=1` ကို မထည့်လျှင် default အနေနှင့် `0` က စပါမည်။

### `rank, (chunk_id, score)`

၎င်းသည် unpacking ဖြစ်သည်။ Ranking function က tuple တွေကို ပြန်ပေးထားသည်။

```python
("chunk-01", 0.991173)
```

`enumerate()` က ထို tuple နှင့် rank ကို တွဲပေးသည့်အတွက် loop တစ်ပတ်စီတွင် —

- `rank` — အဆင့်နံပါတ်
- `chunk_id` — Chunk အမည်
- `score` — Similarity score

တို့ ရရှိသည်။

### `print()` ထဲက `%d`, `%s`, `%.6f`

```python
print("%d. %s similarity=%.6f" % (rank, chunk_id, score))
```

၎င်းသည် Python ၏ old-style string formatting ဖြစ်သည်။

| Format | အဓိပ္ပာယ် |
| --- | --- |
| `%d` | Integer အတွက် |
| `%s` | String အတွက် |
| `%.6f` | Decimal point နောက်တွင် ဂဏန်း ၆ လုံးပြရန် |

ဥပမာ —

```python
rank = 1
chunk_id = "chunk-01"
score = 0.991172953

print("%d. %s similarity=%.6f" % (rank, chunk_id, score))
```

Output —

```text
1. chunk-01 similarity=0.991173
```

---

## 12. Code တစ်ခုလုံး၏ Output — အစိတ်အပိုင်းအားလုံး ပေါင်းစည်းခြင်း

အပိုင်း ၂ မှ ၁၁ အထိ ရှင်းပြခဲ့သည့် အစိတ်အပိုင်းအားလုံးကို ပေါင်းစည်းလိုက်ပါက runnable
script တစ်ခု အပြည့်အစုံ ရရှိသည် —

```python
import math

def cosine_similarity(left, right):
    if len(left) != len(right):
        raise ValueError("dimension mismatch")
    dot = sum(a * b for a, b in zip(left, right))
    norm_left = math.sqrt(sum(a * a for a in left))
    norm_right = math.sqrt(sum(b * b for b in right))
    if norm_left == 0.0 or norm_right == 0.0:
        return 0.0
    return dot / (norm_left * norm_right)

QUERY_VECTOR = [0.90, 0.10, 0.00, 0.20]
CHUNK_VECTORS = {
    "chunk-01": [0.85, 0.15, 0.05, 0.10],
    "chunk-02": [0.10, 0.80, 0.60, 0.10],
    "chunk-03": [0.00, 0.20, 0.95, 0.30],
    "chunk-04": [0.70, 0.05, 0.10, 0.90],
}

def rank_chunks(query, chunks):
    scored = [
        (chunk_id, cosine_similarity(query, vector))
        for chunk_id, vector in chunks.items()
    ]
    scored.sort(key=lambda item: (-item[1], item[0]))
    return scored

for rank, (chunk_id, score) in enumerate(rank_chunks(QUERY_VECTOR, CHUNK_VECTORS), start=1):
    print("%d. %s similarity=%.6f" % (rank, chunk_id, score))
```

Terminal တွင် ဤသို့ ပြပါမည် —

```text
1. chunk-01 similarity=0.991173
2. chunk-04 similarity=0.767112
3. chunk-02 similarity=0.202864
4. chunk-03 similarity=0.084898
```

အဓိပ္ပာယ်က —

- `chunk-01` — Query vector နှင့် အနီးစပ်ဆုံး တူညီသည်။
- `chunk-04` — ဒုတိယအနီးစပ်ဆုံး ဖြစ်သည်။
- `chunk-02` — Similarity ပိုနည်းသည်။
- `chunk-03` — ဤ query နှင့် similarity အနည်းဆုံး ဖြစ်သည်။

ဤ score တွေက vector တွေ၏ ဦးတည်ရာတူညီမှုကို ဖော်ပြခြင်းဖြစ်ပြီး၊ စာသားအဓိပ္ပာယ်ကို
လူတစ်ယောက်က နားလည်သလို တိုက်ရိုက်တိုင်းတာခြင်း မဟုတ်ပါ။ ရလဒ်၏ အရည်အသွေးက
အသုံးပြုထားသော embedding model နှင့် data ပေါ်လည်း မူတည်သည်။

---

## 13. RAG Pipeline နှင့် ဘယ်လိုဆက်စပ်သလား။

ဤ exercise ကို အရင်လေ့လာခဲ့သည့် pipeline stages တွေနှင့် ချိတ်ဆက်ကြည့်ကြပါမည်။

- **Ingest** — Documents လက်ခံခြင်း
- **Chunk** — Documents ခွဲခြင်း
- **Embed** — Query နှင့် chunks ကို vectors ပြောင်းခြင်း
- **Index** — Vectors တွေကို index လုပ်ခြင်း
- **Retrieve** — Cosine Similarity သို့မဟုတ် အခြား retrieval နည်းဖြင့် ranking လုပ်ခြင်း
- **Generate** — ရွေးချယ်ထားသော context ကို LLM ထံပေးပြီး အဖြေထုတ်ခြင်း

ဤ exercise က အဓိကအားဖြင့် **retrieve** အဆင့်တွင် similarity score တွက်ပြီး chunks တွေကို
ranking လုပ်သည့် logic ကို လေ့ကျင့်ပေးခြင်း ဖြစ်သည်။

တကယ့် production RAG system တွေတွင် vector database ၏ similarity search,
approximate nearest neighbor (ANN), metadata filtering နှင့် reranking model တွေကိုလည်း
အသုံးပြုနိုင်သည်။

---

## 14. ကိုယ်တိုင်လေ့ကျင့်ကြည့်ပါ

**မေးခွန်း** — `scored.sort(key=lambda item: (-item[1], item[0]))` တွင် `-item[1]` ကို `item[1]`
ဟု ပြောင်းလိုက်လျှင် ဘာဖြစ်မလဲ။

1. Similarity score အမြင့်ဆုံးက အရင်ပေါ်မည်။
2. Similarity score အနိမ့်ဆုံးက အရင်ပေါ်မည်။
3. Score တွေကို မတွက်တော့ပါ။
4. Chunk ID တွေ ပျောက်သွားမည်။

<details>
<summary>အဖြေ ကြည့်ရန်</summary>

**အဖြေ — 2. Similarity score အနိမ့်ဆုံးက အရင်ပေါ်မည်**

အကြောင်းရင်း — `sort()` သည် ascending order ဖြင့် စီသည်။ `-item[1]` သည် score ကို
အနုတ်လက္ခဏာ ပြောင်းထားသဖြင့် score အမြင့်ဆုံး၏ အနုတ်တန်ဖိုး သည် အငယ်ဆုံး ဖြစ်လာပြီး
အရင်ရောက်သည်။ အနုတ်လက္ခဏာ ဖျက်လိုက်ပါက score အနိမ့်ဆုံးက အရင်ရောက်လာမည်။

ဤ query နှင့် `CHUNK_VECTORS` အတွက် အစီအစဉ်သည် —

```text
['chunk-03', 'chunk-02', 'chunk-04', 'chunk-01']
```

ဖြစ်သွားမည် — ဆိုလိုသည်တွင် `chunk-01` သည် နောက်ဆုံးတွင် ရှိမည် ဖြစ်သည်။

</details>

**အဓိက မှတ်ထားရန်** — ဤ code က query တစ်ခုနှင့် chunk တစ်ခုချင်းစီ၏ cosine similarity ကို
တွက်သည်၊ score အလိုက် စီသည်၊ နောက်ဆုံးတွင် အနီးစပ်ဆုံး chunk ကို rank 1 အဖြစ် ပြပေးသည်။
