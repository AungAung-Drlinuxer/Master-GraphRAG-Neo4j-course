# Walkthrough 02 — Cosine Similarity Ranking (Exercise 2)

> ဤဖိုင်သည် `solution.md` ၏ Exercise 2 ကို **Python အခြေခံမှ စ၍** အပိုင်းလိုက် ရှင်းပြသည့်
> walkthrough ဖြစ်သည်။ Format သည် `walkthroughs/01_pipeline_stage_ordering.md` နှင့် တူညီသည်။

---

ဒီ exercise မှာ Python ကို အသုံးပြုပြီး Query တစ်ခုနဲ့ အနီးစပ်ဆုံးတူညီတဲ့ text chunks တွေကို
similarity score အလိုက် စီစဉ်ခြင်း ကို လေ့လာပါမယ်။

ဒီနည်းလမ်းကို RAG (Retrieval-Augmented Generation) chatbot တွေမှာ အသုံးပြုပါတယ်။ ဥပမာ
IT Help Chatbot မှာ user က Kubernetes အကြောင်း မေးတဲ့အခါ knowledge base ထဲက သက်ဆိုင်တဲ့
document chunks တွေကို ရှာဖွေဖို့ အသုံးဝင်ပါတယ်။

ဒီ code မှာ အဓိကလေ့လာရမယ့် Python concepts တွေကတော့ —

- `import` နဲ့ `math` module
- `def` နဲ့ function
- `if`၊ `raise`၊ `return`
- `sum()`၊ `zip()`၊ `len()`
- List comprehension
- `lambda` နဲ့ `sort()`
- `enumerate()` နဲ့ tuple unpacking
- Cosine Similarity နဲ့ vector ranking

---

## 1. Cosine Similarity ဆိုတာဘာလဲ။

Cosine Similarity ဆိုတာ vector နှစ်ခုရဲ့ ဦးတည်ရာ (direction) ဘယ်လောက်တူညီသလဲဆိုတာ
တိုင်းတာတဲ့ နည်းလမ်းတစ်ခုဖြစ်ပါတယ်။

RAG system မှာ text ကို embedding model နဲ့ vector အဖြစ်ပြောင်းပြီး query vector နဲ့
document chunk vector တို့ရဲ့ similarity ကို တွက်ချက်နိုင်ပါတယ်။

Embedding model က Query နဲ့ chunks တွေကို vector ပြောင်းပေးပြီး Cosine Similarity က
ဘယ် chunk တွေက query နဲ့ ပိုတူညီသလဲဆိုတာ အမှတ်ပေးပါတယ်။

Cosine Similarity ရဲ့ formula က —

```text
cosine(A, B) = (A · B) / (||A|| · ||B||)
```

ဒီမှာ —

- `A`, `B` — Vector နှစ်ခု
- `A · B` — Dot product
- `||A||`, `||B||` — Vector တစ်ခုစီရဲ့ magnitude (norm)

ပုံမှန်အားဖြင့် non-zero vector တွေအတွက် score က `-1` နဲ့ `1` ကြားမှာ ရှိပါတယ်။ Score က `1` နဲ့
နီးလေလေ direction ပိုတူလေလေ ဖြစ်ပါတယ်။ ဒီ exercise ထဲက vector တွေမှာ component အားလုံး
non-negative ဖြစ်တဲ့အတွက် score တွေက `0` နဲ့ `1` ကြားမှာ ရှိပါမယ်။

---

## 2. `import math`

```python
import math
```

`import` က အခြား module တစ်ခုထဲက functions တွေကို အသုံးပြုနိုင်ဖို့ ထည့်သွင်းပေးတာပါ။

`math` ဟာ Python ရဲ့ built-in standard library module ဖြစ်ပြီး သင်္ချာဆိုင်ရာ functions တွေ
ပါဝင်ပါတယ်။ ဒီ exercise မှာ —

```python
math.sqrt(...)
```

ကို အသုံးပြုပါတယ်။ `math.sqrt()` က square root ကို တွက်ပေးပါတယ်။

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

Vector norm တွက်တဲ့အခါ square root လိုအပ်တာကြောင့် `math.sqrt()` ကို အသုံးပြုထားပါတယ်။

---

## 3. `cosine_similarity()` function ကို ဖန်တီးခြင်း

```python
def cosine_similarity(left, right):
```

ဒီမှာ `cosine_similarity` ဆိုတဲ့ function ကို သတ်မှတ်ထားပါတယ်။

- `left` — ပထမ vector
- `right` — ဒုတိယ vector

ဥပမာ —

```python
left = [1, 2, 3]
right = [4, 5, 6]
```

ဒီ function က vector နှစ်ခုကို လက်ခံပြီး similarity score တစ်ခု ပြန်ပေးမှာ ဖြစ်ပါတယ်။

### Step 3.1 — Vector dimensions စစ်ဆေးခြင်း

```python
if len(left) != len(right):
    raise ValueError("dimension mismatch")
```

`len()` က list ထဲက elements အရေအတွက်ကို ပြန်ပေးပါတယ်။

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

Vector နှစ်ခုစလုံးမှာ dimensions လေးခုစီ ရှိပါတယ်။

`!=` က မတူညီဘူးလို့ ဆိုလိုပါတယ်။ ဒါကြောင့် —

```python
if len(left) != len(right):
```

ဆိုတာ vector နှစ်ခုရဲ့ dimensions မတူညီဘူးလားလို့ စစ်တာပါ။ မတူညီရင် —

```python
raise ValueError("dimension mismatch")
```

က `ValueError` exception ကို ဖြစ်စေပြီး function ကို ရပ်တန့်စေပါတယ်။

ဥပမာ —

```python
cosine_similarity([1, 2, 3], [4, 5])
```

ဒီ vector တွေမှာ dimensions မတူညီတဲ့အတွက် `ValueError: dimension mismatch` ဖြစ်ပါမယ်။

ဘာကြောင့် စစ်ရသလဲ။ Vector နှစ်ခုကို component တစ်ခုစီအလိုက် နှိုင်းယှဉ်ပြီး dot product
တွက်ဖို့ dimension တူညီဖို့ လိုအပ်ပါတယ်။

---

## 4. Dot Product တွက်ချက်ခြင်း

```python
dot = sum(a * b for a, b in zip(left, right))
```

ဒီတစ်ကြောင်းမှာ `zip()`၊ multiplication `*`၊ generator expression နဲ့ `sum()` တို့ ပါဝင်ပါတယ်။

### Step 4.1 — `zip(left, right)`

`zip()` က list နှစ်ခုထဲက တူညီတဲ့ position မှာရှိတဲ့ elements တွေကို တွဲပေးပါတယ်။

```python
left = [1, 2, 3]
right = [4, 5, 6]

print(list(zip(left, right)))
```

Output —

```python
[(1, 4), (2, 5), (3, 6)]
```

ပထမ list ရဲ့ `1` ကို ဒုတိယ list ရဲ့ `4` နဲ့ တွဲပေးပြီး၊ `2` ကို `5` နဲ့၊ `3` ကို `6` နဲ့
တွဲပေးပါတယ်။

### Step 4.2 — `a * b`

```python
a * b
```

တွဲထားတဲ့ values နှစ်ခုကို မြှောက်တာပါ။ အထက်က ဥပမာမှာ —

```text
1 * 4 = 4
2 * 5 = 10
3 * 6 = 18
```

### Step 4.3 — `sum()`

```python
dot = sum(a * b for a, b in zip(left, right))
```

`sum()` က မြှောက်လဒ်တွေကို ပေါင်းပေးပါတယ်။

```text
4 + 10 + 18 = 32
```

ဒါကြောင့် `dot = 32` ဖြစ်ပါတယ်။

ဒီလို vector တစ်ခုရဲ့ component တွေကို နောက် vector ရဲ့ component တွေနဲ့ တစ်ခုချင်းမြှောက်ပြီး
ပေါင်းထားတာကို **Dot Product** လို့ခေါ်ပါတယ်။

---

## 5. Vector Norm တွက်ချက်ခြင်း

```python
norm_left = math.sqrt(sum(a * a for a in left))
norm_right = math.sqrt(sum(b * b for b in right))
```

ဒီနေရာမှာ vector တစ်ခုစီရဲ့ norm ကို တွက်ပါတယ်။ Norm ဆိုတာ vector ရဲ့ magnitude သို့မဟုတ်
အလျားကို ဆိုလိုပါတယ်။ Formula က —

```text
||A|| = sqrt(a₁² + a₂² + ⋯ + aₙ²)
```

ဥပမာ — `left = [3, 4]`

ပထမဆုံး component တစ်ခုချင်းစီကို သူ့ကိုယ်သူ မြှောက်ပါမယ်။

```text
3 * 3 = 9
4 * 4 = 16
```

ပြီးရင် ပေါင်းပါမယ်။

```text
9 + 16 = 25
```

နောက်ဆုံး square root ယူပါမယ်။

```text
sqrt(25) = 5
```

Python နဲ့ဆိုရင် —

```python
left = [3, 4]
norm_left = math.sqrt(sum(a * a for a in left))

print(norm_left)
```

Output —

```text
5.0
```

`norm_right` ကလည်း `right` vector အတွက် အလားတူ တွက်ချက်တာပါ။

---

## 6. Zero Vector ကို စစ်ဆေးခြင်း

```python
if norm_left == 0.0 or norm_right == 0.0:
    return 0.0
```

ဒီမှာ operator နှစ်ခုကို သတိပြုပါ။

- `==` — တူညီသလား စစ်ဆေးခြင်း။
- `or` — အခြေအနေနှစ်ခုထဲက တစ်ခုခု မှန်ရင် condition တစ်ခုလုံး မှန်ခြင်း။

Vector တစ်ခုရဲ့ norm က `0.0` ဖြစ်တယ်ဆိုရင် အဲဒီ vector ဟာ zero vector ဖြစ်ပါတယ်။
Zero vector နဲ့ cosine similarity တွက်တဲ့အခါ denominator က သုညဖြစ်သွားနိုင်ပါတယ်။

```text
dot product / 0
```

ဒီလို division by zero မဖြစ်အောင် —

```python
return 0.0
```

နဲ့ score `0.0` ကို ပြန်ပေးထားတာပါ။ ဒီဟာက application အတွက် ရွေးချယ်ထားတဲ့ **fallback**
ဖြစ်ပါတယ်။ သင်္ချာအရ zero vector ရဲ့ cosine similarity ကို ပုံမှန်အားဖြင့် သတ်မှတ်လို့ မရပါဘူး။

---

## 7. Cosine Similarity Score ပြန်ပေးခြင်း

```python
return dot / (norm_left * norm_right)
```

ဒါက function ရဲ့ အဓိကတွက်ချက်မှု ဖြစ်ပါတယ်။

```text
cosine(A, B) = (A · B) / (||A|| · ||B||)
```

အပေါ်မှာ တွက်ထားတဲ့ dot product ကို vector နှစ်ခုရဲ့ norm မြှောက်လဒ်နဲ့ စားပေးပါတယ်။

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

ပထမ pair က direction တူလို့ score `1.0` ဖြစ်ပါတယ်။ ဒုတိယ pair က direction တွေ
perpendicular ဖြစ်လို့ score `0.0` ဖြစ်ပါတယ်။

---

## 8. Query Vector သတ်မှတ်ခြင်း

```python
QUERY_VECTOR = [0.90, 0.10, 0.00, 0.20]
```

ဒီ list က user query ကို ကိုယ်စားပြုတဲ့ vector ဖြစ်ပါတယ်။ ဒီဥပမာမှာ vector dimensions
လေးခု ရှိပါတယ်။

တကယ့် RAG system မှာ embedding model က query text ကို vector အဖြစ် ပြောင်းပေးတာဖြစ်ပြီး
ဒီနံပါတ်တွေကို ကိုယ်တိုင် ရွေးထည့်လေ့မရှိပါဘူး။ ဒီ exercise ကတော့ cosine similarity ကို
လေ့လာနိုင်ဖို့ vector တွေကို ရိုးရှင်းစွာ သတ်မှတ်ထားတာပါ။

---

## 9. `CHUNK_VECTORS` — Document chunks တွေရဲ့ vectors

```python
CHUNK_VECTORS = {
    "chunk-01": [0.85, 0.15, 0.05, 0.10],
    "chunk-02": [0.10, 0.80, 0.60, 0.10],
    "chunk-03": [0.00, 0.20, 0.95, 0.30],
    "chunk-04": [0.70, 0.05, 0.10, 0.90],
}
```

ဒီ data structure က dictionary ဖြစ်ပါတယ်။

- Key — Chunk ID၊ ဥပမာ `"chunk-01"`
- Value — အဲဒီ chunk ကို ကိုယ်စားပြုတဲ့ vector

Query vector နဲ့ chunk vector တစ်ခုချင်းစီကို နှိုင်းယှဉ်ပြီး score တွက်မှာပါ။

ဥပမာ —

```python
CHUNK_VECTORS["chunk-01"]
```

ဒီလိုရေးရင် `chunk-01` ရဲ့ vector ကို ပြန်ရပါတယ်။ Chunk ID တွေကို key အဖြစ်
အသုံးပြုထားတဲ့အတွက် similarity score တစ်ခုချင်းစီဟာ ဘယ် chunk နဲ့ သက်ဆိုင်တယ်ဆိုတာ
သိနိုင်ပါတယ်။

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

ဒီ function ရဲ့ ရည်ရွယ်ချက်က chunk တစ်ခုချင်းစီရဲ့ similarity score ကို တွက်ချက်ပြီး
score အမြင့်ဆုံးကနေ အနိမ့်ဆုံးအထိ စီပေးဖို့ ဖြစ်ပါတယ်။

### Step 10.1 — `chunks.items()`

```python
for chunk_id, vector in chunks.items()
```

Dictionary ရဲ့ `.items()` က key နဲ့ value ကို တွဲပြီး ထုတ်ပေးပါတယ်။

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

ဒီမှာ `chunk_id` ထဲကို key ဝင်ပြီး `vector` ထဲကို value ဝင်ပါတယ်။ ဒီလို variable နှစ်ခုထဲကို
တန်ဖိုးခွဲထည့်တာကို **unpacking** လို့ခေါ်ပါတယ်။

### Step 10.2 — List comprehension နဲ့ score တွက်ခြင်း

```python
scored = [
    (chunk_id, cosine_similarity(query, vector))
    for chunk_id, vector in chunks.items()
]
```

ဒီ code က chunk တစ်ခုချင်းစီအတွက် tuple တစ်ခု ဖန်တီးပါတယ်။

```python
(chunk_id, cosine_similarity(query, vector))
```

Tuple ထဲမှာ —

- Chunk ID
- အဲဒီ chunk ရဲ့ cosine similarity score

တို့ ပါဝင်ပါတယ်။ ဥပမာ result က ဒီလိုပုံစံ ဖြစ်ပါမယ်။

```python
[
    ("chunk-01", 0.991173),
    ("chunk-02", 0.202864),
    ("chunk-03", 0.084898),
    ("chunk-04", 0.767112),
]
```

အခုအချိန်မှာ ဒီ list က မူလ dictionary အစီအစဉ်အတိုင်း ဖြစ်နေသေးပါတယ်။ Ranking
မလုပ်ရသေးပါဘူး။

### Step 10.3 — `scored.sort(...)`

```python
scored.sort(key=lambda item: (-item[1], item[0]))
```

ဒီတစ်ကြောင်းက ranking လုပ်ပေးတဲ့ အဓိက code ဖြစ်ပါတယ်။ အရင်ဆုံး `sort()` ကို
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

`sort()` က list ကို မူလ list အတွင်းမှာပဲ ပြင်ဆင်စီစဉ်ပေးပါတယ်။ ဒီ exercise မှာတော့ `key`
parameter နဲ့ sorting လုပ်မယ့်စည်းမျဉ်းကို သတ်မှတ်ထားပါတယ်။

### `lambda item`

```python
lambda item: (-item[1], item[0])
```

`lambda` ဆိုတာ နာမည်မပေးထားတဲ့ function အသေးစားတစ်ခု ဖန်တီးတဲ့နည်းလမ်း ဖြစ်ပါတယ်။
ဒီ expression ကို ပုံမှန် function နဲ့ ရေးမယ်ဆိုရင် —

```python
def sort_key(item):
    return (-item[1], item[0])
```

နဲ့ အဓိပ္ပာယ်တူပါတယ်။

ဥပမာ —

```python
item = ("chunk-01", 0.991173)
```

ဒီ tuple မှာ —

- `item[0]` က `"chunk-01"`
- `item[1]` က `0.991173`

ဖြစ်ပါတယ်။

### ဘာကြောင့် `-item[1]` သုံးတာလဲ။

Python ရဲ့ `sort()` က ပုံမှန်အားဖြင့် ascending order နဲ့ စီပါတယ်။

```python
scores = [0.20, 0.99, 0.76]
scores.sort()

print(scores)
```

Output —

```python
[0.2, 0.76, 0.99]
```

ဒါပေမဲ့ ကျွန်တော်တို့က similarity score အမြင့်ဆုံးကို အရင်ပြချင်ပါတယ်။

```python
scores = [0.20, 0.99, 0.76]
scores.sort(key=lambda score: -score)

print(scores)
```

Output —

```python
[0.99, 0.76, 0.2]
```

Score ကို အနုတ်လက္ခဏာ ပြောင်းပြီး sorting လုပ်တာကြောင့် score အမြင့်ဆုံးက
အရင်ရောက်လာပါတယ်။

### ဘာကြောင့် `item[0]` ကိုလည်း ထည့်ထားတာလဲ။

```python
(-item[1], item[0])
```

ဒီမှာ sorting key နှစ်ခုရှိပါတယ်။

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

Score တူညီနေတဲ့ `chunk-01` နဲ့ `chunk-02` ကို chunk ID အရ စီပေးထားပါတယ်။ ဒါကြောင့်
output က **deterministic** ဖြစ်ပါတယ်။

### Step 10.4 — `return scored`

```python
return scored
```

Sorting ပြီးသွားတဲ့ list ကို function က ပြန်ပေးပါတယ်။

---

## 11. `enumerate()` နဲ့ Result ကို ပြသခြင်း

```python
for rank, (chunk_id, score) in enumerate(
    rank_chunks(QUERY_VECTOR, CHUNK_VECTORS),
    start=1
):
    print("%d. %s similarity=%.6f" % (rank, chunk_id, score))
```

ဒီအပိုင်းမှာ ranking လုပ်ပြီးသား result တွေကို နံပါတ်တပ်ပြီး ပြသပါတယ်။

### `rank_chunks(QUERY_VECTOR, CHUNK_VECTORS)`

ဒီ function call က query vector နဲ့ chunk vectors တွေကို အသုံးပြုပြီး ranking result ကို
ပြန်ပေးပါတယ်။

### `enumerate(..., start=1)`

`enumerate()` က item တစ်ခုချင်းစီအတွက် counter တစ်ခု ထည့်ပေးပါတယ်။

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

`start=1` ကို မထည့်ရင် default အနေနဲ့ `0` က စပါမယ်။

### `rank, (chunk_id, score)`

ဒါက unpacking ဖြစ်ပါတယ်။ Ranking function က tuple တွေကို ပြန်ပေးထားပါတယ်။

```python
("chunk-01", 0.991173)
```

`enumerate()` က အဲဒီ tuple နဲ့ rank ကို တွဲပေးတဲ့အတွက် loop တစ်ပတ်စီမှာ —

- `rank` — အဆင့်နံပါတ်
- `chunk_id` — Chunk အမည်
- `score` — Similarity score

တို့ ရရှိပါတယ်။

### `print()` ထဲက `%d`, `%s`, `%.6f`

```python
print("%d. %s similarity=%.6f" % (rank, chunk_id, score))
```

ဒီဟာက Python ရဲ့ old-style string formatting ဖြစ်ပါတယ်။

| Format | အဓိပ္ပာယ် |
| --- | --- |
| `%d` | Integer အတွက် |
| `%s` | String အတွက် |
| `%.6f` | Decimal point နောက်မှာ ဂဏန်း ၆ လုံးပြရန် |

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

## 12. Code တစ်ခုလုံးရဲ့ Output — အစိတ်အပိုင်းအားလုံး ပေါင်းစည်းခြင်း

အပိုင်း ၂ မှ ၁၁ အထိ ရှင်းပြခဲ့သည့် အစိတ်အပိုင်းအားလုံးကို ပေါင်းစည်းလိုက်ပါက runnable
script တစ်ခု အပြည့်အစုံ ရရှိပါတယ် —

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

Terminal မှာ ဒီလို ပြပါမယ် —

```text
1. chunk-01 similarity=0.991173
2. chunk-04 similarity=0.767112
3. chunk-02 similarity=0.202864
4. chunk-03 similarity=0.084898
```

အဓိပ္ပာယ်က —

- `chunk-01` — Query vector နဲ့ အနီးစပ်ဆုံး တူညီပါတယ်။
- `chunk-04` — ဒုတိယအနီးစပ်ဆုံး ဖြစ်ပါတယ်။
- `chunk-02` — Similarity ပိုနည်းပါတယ်။
- `chunk-03` — ဒီ query နဲ့ similarity အနည်းဆုံး ဖြစ်ပါတယ်။

ဒီ score တွေက vector တွေရဲ့ ဦးတည်ရာတူညီမှုကို ဖော်ပြတာဖြစ်ပြီး၊ စာသားအဓိပ္ပာယ်ကို
လူတစ်ယောက်က နားလည်သလို တိုက်ရိုက်တိုင်းတာတာ မဟုတ်ပါဘူး။ ရလဒ်ရဲ့ အရည်အသွေးက
အသုံးပြုထားတဲ့ embedding model နဲ့ data ပေါ်လည်း မူတည်ပါတယ်။

---

## 13. RAG Pipeline နဲ့ ဘယ်လိုဆက်စပ်သလဲ။

ဒီ exercise ကို အရင်လေ့လာခဲ့တဲ့ pipeline stages တွေနဲ့ ချိတ်ဆက်ကြည့်ရအောင်။

- **Ingest** — Documents လက်ခံခြင်း
- **Chunk** — Documents ခွဲခြင်း
- **Embed** — Query နဲ့ chunks ကို vectors ပြောင်းခြင်း
- **Index** — Vectors တွေကို index လုပ်ခြင်း
- **Retrieve** — Cosine Similarity သို့မဟုတ် အခြား retrieval နည်းဖြင့် ranking လုပ်ခြင်း
- **Generate** — ရွေးချယ်ထားတဲ့ context ကို LLM ထံပေးပြီး အဖြေထုတ်ခြင်း

ဒီ exercise က အဓိကအားဖြင့် **retrieve** အဆင့်မှာ similarity score တွက်ပြီး chunks တွေကို
ranking လုပ်တဲ့ logic ကို လေ့ကျင့်ပေးတာ ဖြစ်ပါတယ်။

တကယ့် production RAG system တွေမှာတော့ vector database ရဲ့ similarity search,
approximate nearest neighbor (ANN), metadata filtering နဲ့ reranking model တွေကိုလည်း
အသုံးပြုနိုင်ပါတယ်။

---

## 14. ကိုယ်တိုင်လေ့ကျင့်ကြည့်ပါ

**မေးခွန်း** — `scored.sort(key=lambda item: (-item[1], item[0]))` မှာ `-item[1]` ကို `item[1]`
လို့ ပြောင်းလိုက်ရင် ဘာဖြစ်မလဲ။

1. Similarity score အမြင့်ဆုံးက အရင်ပေါ်မယ်။
2. Similarity score အနိမ့်ဆုံးက အရင်ပေါ်မယ်။
3. Score တွေကို မတွက်တော့ဘူး။
4. Chunk ID တွေ ပျောက်သွားမယ်။

<details>
<summary>အဖြေ ကြည့်ရန်</summary>

**အဖြေ — 2. Similarity score အနိမ့်ဆုံးက အရင်ပေါ်မယ်**

အကြောင်းရင်း — `sort()` သည် ascending order ဖြင့် စီသည်။ `-item[1]` သည် score ကို
အနုတ်လက္ခဏာ ပြောင်းထားသဖြင့် score အမြင့်ဆုံး၏ အနုတ်တန်ဖိုး သည် အငယ်ဆုံး ဖြစ်လာပြီး
အရင်ရောက်သည်။ အနုတ်လက္ခဏာ ဖျက်လိုက်ပါက score အနိမ့်ဆုံးက အရင်ရောက်လာမည်။

ဤ query နှင့် `CHUNK_VECTORS` အတွက် အစီအစဉ်သည် —

```text
['chunk-03', 'chunk-02', 'chunk-04', 'chunk-01']
```

ဖြစ်သွားမည် — ဆိုလိုသည်မှာ `chunk-01` သည် နောက်ဆုံးတွင် ရှိမည် ဖြစ်သည်။

</details>

**အဓိက မှတ်ထားရန်** — ဒီ code က query တစ်ခုနဲ့ chunk တစ်ခုချင်းစီရဲ့ cosine similarity ကို
တွက်တယ်၊ score အလိုက် စီတယ်၊ နောက်ဆုံးမှာ အနီးစပ်ဆုံး chunk ကို rank 1 အဖြစ် ပြပေးပါတယ်။
