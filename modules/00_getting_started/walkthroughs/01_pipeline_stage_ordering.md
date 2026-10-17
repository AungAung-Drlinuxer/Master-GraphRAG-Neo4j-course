# Walkthrough 01 — RAG Pipeline Stage Ordering (Exercise 1)

> ဤဖိုင်သည် `solution.md` ၏ Exercise 1 ကို **Python အခြေခံမှ စ၍** အပိုင်းလိုက် ရှင်းပြသည့်
> walkthrough ဖြစ်သည်။ `explanation.md` သည် သဘောတရားအတွက် ဖြစ်ပြီး၊ ဤဖိုင်သည် code ကို
> လိုင်းတစ်လိုင်းချင်း လိုက်ဖတ်လိုသူအတွက် ဖြစ်သည်။

---

ဒီ Python code ကို RAG (Retrieval-Augmented Generation) pipeline တစ်ခုမှာ stages တွေကို
dependency အစီအစဉ်အတိုင်း အလိုအလျောက် စီပေးဖို့ အသုံးပြုထားပါတယ်။

ဒီ code မှာ အဓိကလေ့လာရမယ့် Python concepts တွေကတော့ dictionary, tuple, list, set, while loop,
list comprehension, all(), assert နဲ့ function တို့ဖြစ်ပါတယ်။

---

## 1. Pipeline ဆိုတာဘာလဲ။

Pipeline ဆိုတာ အလုပ်တစ်ခုကို အဆင့်ဆင့် ဆက်စပ်လုပ်ဆောင်စေတဲ့ workflow ဖြစ်ပါတယ်။

ဥပမာ IT Help Chatbot မှာ user ၏ မေးခွန်းကို ဖြေဖို့အတွက် knowledge documents တွေကို
အရင်ပြင်ဆင်ပြီး၊ သက်ဆိုင်တဲ့ information တွေကို ရှာဖွေကာ နောက်ဆုံး LLM နဲ့ အဖြေထုတ်ရပါတယ်။

- **1. ingest** — Documents များကို လက်ခံသိမ်းဆည်းခြင်း
- **2. chunk** — Documents များကို အပိုင်းငယ်များ ခွဲခြင်း
- **3. embed** — Text ကို vector embeddings ပြောင်းခြင်း
- **4. index** — Vectors များကို ရှာဖွေနိုင်ရန် index လုပ်ခြင်း
- **5. retrieve** — သက်ဆိုင်ရာ content ကို ရှာဖွေခြင်း
- **6. generate** — LLM ဖြင့် အဖြေထုတ်ပေးခြင်း

ဥပမာ chunk stage ကို မလုပ်ရသေးဘဲ embed ကို အရင်လုပ်လို့ မရပါဘူး။ အကြောင်းက embed ဟာ
chunk ပြီးမှ ရလာတဲ့ data ကို လိုအပ်လို့ပါ။

ဒီလို အဆင့်တစ်ခုနဲ့တစ်ခု မှီခိုနေမှုကို **dependency** လို့ခေါ်ပါတယ်။

---

## 2. `PIPELINE_DEPENDENCIES` — Dependency တွေကို သတ်မှတ်ခြင်း

```python
PIPELINE_DEPENDENCIES = {
    "ingest": (),
    "chunk": ("ingest",),
    "embed": ("chunk",),
    "index": ("embed",),
    "retrieve": ("index",),
    "generate": ("retrieve",),
}
```

ဒီနေရာမှာ `PIPELINE_DEPENDENCIES` ဟာ Python dictionary တစ်ခုဖြစ်ပါတယ်။ Dictionary မှာ
`key: value` ပုံစံနဲ့ data တွေ သိမ်းထားပါတယ်။

ဥပမာ — `"chunk": ("ingest",)` မှာ

- `"chunk"` က key ဖြစ်ပါတယ်။
- `("ingest",)` က value ဖြစ်ပြီး chunk အတွက် လိုအပ်တဲ့ dependency ကို ဖော်ပြပါတယ်။

ဒီ dictionary ထဲက key တစ်ခုချင်းစီဟာ pipeline stage တစ်ခုဖြစ်ပြီး value က အဲဒီ stage မစခင်
ပြီးထားရမယ့် stages တွေကို ဖော်ပြပါတယ်။

| Stage | Dependency | အဓိပ္ပာယ် |
| --- | --- | --- |
| ingest | `()` | အရင်လုပ်စရာ stage မရှိ |
| chunk | `("ingest",)` | ingest ပြီးရမယ် |
| embed | `("chunk",)` | chunk ပြီးရမယ် |
| index | `("embed",)` | embed ပြီးရမယ် |
| retrieve | `("index",)` | index ပြီးရမယ် |
| generate | `("retrieve",)` | retrieve ပြီးရမယ် |

### `()` နဲ့ `("ingest",)` ဘာကွာသလဲ။

```python
"ingest": ()
```

`()` ဟာ empty tuple ဖြစ်ပါတယ်။ `ingest` stage မှာ dependency မရှိဘူးလို့ ဆိုလိုပါတယ်။

```python
"chunk": ("ingest",)
```

ဒီမှာ `("ingest",)` ဟာ item တစ်ခုပါတဲ့ tuple ဖြစ်ပါတယ်။ Python မှာ item တစ်ခုပါတဲ့ tuple ကို
သတ်မှတ်တဲ့အခါ comma `,` ထည့်ဖို့ လိုပါတယ်။

```python
print(type(("ingest",)))   # <class 'tuple'>
print(type(("ingest")))    # <class 'str'>
```

ဒီကွာခြားချက်က အရေးကြီးပါတယ်။ Function က dependency တွေကို စစ်ဆေးတဲ့အခါ tuple ဖြစ်နေဖို့
လိုပါတယ်။

---

## 3. `UNORDERED_STAGES` — မူလအစီအစဉ်မကျတဲ့ stages များ

```python
UNORDERED_STAGES = [
    "generate",
    "retrieve",
    "index",
    "embed",
    "ingest",
    "chunk",
]
```

ဒီ list ထဲမှာ stages ၆ ခုကို ရည်ရွယ်ချက်ရှိရှိ အစီအစဉ်မကျအောင် ထည့်ထားပါတယ်။

Python က ဒီ list အတိုင်းပဲ လုပ်ဆောင်မယ်ဆိုရင် `generate` က အရင်ရောက်နေမှာပါ။ ဒါပေမဲ့
dependency အရ `generate` ကို နောက်ဆုံးမှ လုပ်ရမှာ ဖြစ်ပါတယ်။

ဒါကြောင့် `topological_order()` function ကို အသုံးပြုပြီး မှန်ကန်တဲ့အစီအစဉ်ကို ပြန်စီမှာ ဖြစ်ပါတယ်။

မှတ်ချက် — `UNORDERED_STAGES` ဆိုတဲ့ variable name က list ထဲမှာ မူလအစီအစဉ်ကို
မယုံကြည်ဘဲ dependency အပေါ်မူတည်ပြီး စီမယ်ဆိုတာကို ဖော်ပြပါတယ်။

---

## 4. `topological_order()` function

```python
def topological_order(stages, dependencies):
    """Return a deterministic order in which every stage follows its dependencies."""
```

ဒီ code က `topological_order` ဆိုတဲ့ function ကို ဖန်တီးထားတာပါ။ Function မှာ parameters
နှစ်ခု ပါပါတယ်။

- `stages` — စီစဉ်ပေးရမယ့် stage တွေ။
- `dependencies` — Stage တစ်ခုစီ၏ dependency တွေ။

Function ကို ခေါ်တဲ့အခါ —

```python
order = topological_order(
    UNORDERED_STAGES,
    PIPELINE_DEPENDENCIES,
)
```

ဆိုပြီး arguments တွေ ပေးလိုက်တဲ့အတွက် —

- `stages` ထဲကို `UNORDERED_STAGES` ၏တန်ဖိုး ဝင်လာမယ်။
- `dependencies` ထဲကို `PIPELINE_DEPENDENCIES` ၏တန်ဖိုး ဝင်လာမယ်။

Function အတွင်းမှာ ဒီ data တွေကို အသုံးပြုပြီး အစီအစဉ်ကို တွက်ချက်မှာပါ။

`"""..."""` က docstring ဖြစ်ပြီး function ၏ ရည်ရွယ်ချက်ကို ရှင်းပြထားတာ ဖြစ်ပါတယ်။

> **မှတ်ချက်** — ဒီနေရာမှာ function ၏ **ခေါင်းစီး (signature) နှင့် docstring ကိုသာ** ပြထားသည်။
> Body ကို အောက်ပိုင်း အပိုင်း ၅ မှ ၁၂ အထိ တစ်ကြောင်းချင်း ရှင်းပြထားသည်။ Function အပြည့်အစုံကို
> `solution.md` တွင်လည်း ကြည့်နိုင်ပြီး၊ အစိတ်အပိုင်းအားလုံး ပေါင်းစည်းထားသော runnable version ကို
> အပိုင်း ၁၃ တွင် ဖော်ပြထားသည်။

---

## 5. `ordered = []`

```python
ordered = []
```

ဒီမှာ empty list တစ်ခု ဖန်တီးထားပါတယ်။ `ordered` ထဲမှာ dependency အရ မှန်ကန်တဲ့အစီအစဉ်နဲ့
ရွေးချယ်ပြီးသား stages တွေကို ထည့်သွားမှာပါ။

ဥပမာ —

```python
ordered = []
ordered.append("ingest")
```

အခု `ordered` ၏တန်ဖိုးက —

```python
["ingest"]
```

ဖြစ်သွားပါပြီ။ နောက်ထပ် stage တွေကို dependency ပြည့်မီတဲ့အခါ ထပ်ထည့်သွားမှာပါ။

---

## 6. `remaining = sorted(set(stages))`

```python
remaining = sorted(set(stages))
```

ဒီတစ်ကြောင်းမှာ Python operations သုံးခုကို တွေ့ရပါတယ်။

### `set(stages)`

`set()` က ထပ်နေတဲ့ items တွေကို ဖယ်ရှားပြီး unique values တွေကို ရရှိစေပါတယ်။

ဥပမာ —

```python
stages = ["embed", "ingest", "embed", "chunk"]

print(set(stages))
```

Output က set အမျိုးအစား ဖြစ်ပါတယ်။ ပြသတဲ့အစီအစဉ်က တစ်သမတ်တည်း ဖြစ်မယ်လို့ မယူဆသင့်ပါဘူး။

```text
{'embed', 'ingest', 'chunk'}
```

ဒီနေရာမှာ `embed` က နှစ်ခါပါနေပေမဲ့ `set()` က တစ်ခုတည်းသာ ထားပေးပါတယ်။

### `sorted(...)`

`sorted()` က items တွေကို sorting လုပ်ပြီး list အသစ်တစ်ခု ပြန်ပေးပါတယ်။

```python
print(sorted(["generate", "embed", "ingest"]))
```

Output —

```python
['embed', 'generate', 'ingest']
```

ဒီ code မှာ `set()` ကို အရင်သုံးပြီး `sorted()` ကို နောက်မှ သုံးထားတာကြောင့် duplicate မရှိဘဲ
အစီအစဉ်တကျ ဖြစ်သွားပါတယ်။

အဲဒါကြောင့် —

```python
remaining = sorted(set(stages))
```

ဟာ stages တွေကို unique ဖြစ်အောင်လုပ်ပြီး alphabetical order နဲ့ စီထားတဲ့ list ကို `remaining`
ထဲ သိမ်းတာဖြစ်ပါတယ်။

သတိပြုရန် — Alphabetical order က dependency order မဟုတ်ပါဘူး။ Function က dependency
ပြည့်မီတဲ့ stage ကိုသာ ရွေးချယ်မှာ ဖြစ်ပါတယ်။

---

## 7. `while remaining:`

```python
while remaining:
```

`while` loop ဆိုတာ condition မှန်နေသရွေ့ code တွေကို ထပ်ခါထပ်ခါ လုပ်ဆောင်ပေးတာပါ။

Python မှာ —

```python
remaining = ["chunk", "embed"]

while remaining:
    print(remaining)
    remaining.pop()
```

ဆိုရင် `remaining` list ထဲမှာ items ရှိနေသေးသရွေ့ loop ဆက်လုပ်ပါမယ်။ List အလွတ်ဖြစ်သွားရင်
`while remaining` က `False` ဖြစ်သွားပြီး loop ရပ်သွားပါတယ်။

ဒီ pipeline code မှာ stage တစ်ခုကို ရွေးချယ်ပြီးတိုင်း `remaining` ထဲကနေ ဖယ်ရှားပါတယ်။
Stage အားလုံး ရွေးချယ်ပြီးတဲ့အခါ loop ရပ်သွားမှာပါ။

---

## 8. `ready = [...]` — Dependency ပြည့်မီတဲ့ stage ကို ရှာခြင်း

ဒီအပိုင်းက code ၏ အဓိက logic ဖြစ်ပါတယ်။

```python
ready = [
    s for s in remaining
    if all(d in ordered for d in dependencies[s])
]
```

ဒါကို **list comprehension** လို့ခေါ်ပါတယ်။ အဓိပ္ပာယ်ကို အပိုင်းလိုက် ကြည့်ရအောင်။

### `for s in remaining`

```python
for s in remaining
```

`remaining` ထဲက stage တစ်ခုချင်းစီကို `s` ဆိုတဲ့ variable ထဲ ယူပါတယ်။

ဥပမာ —

```python
remaining = ["chunk", "embed", "generate", "index", "ingest", "retrieve"]
```

ဒီ loop က stage တစ်ခုချင်းစီကို စစ်ဆေးသွားမှာပါ။

### `dependencies[s]`

```python
dependencies[s]
```

ဒါက dictionary ထဲက `s` နဲ့ သက်ဆိုင်တဲ့ dependency ကို ယူတာပါ။

ဥပမာ —

```python
dependencies["chunk"]
```

Output —

```python
("ingest",)
```

နောက်ဥပမာ —

```python
dependencies["ingest"]
```

Output —

```python
()
```

### `d in ordered`

```python
d in ordered
```

ဒါက `d` ဆိုတဲ့ dependency ဟာ `ordered` list ထဲမှာ ရှိပြီးသားလားဆိုတာ စစ်ဆေးပါတယ်။
ရှိရင် `True`၊ မရှိရင် `False` ပြန်ပေးပါတယ်။

```python
ordered = ["ingest"]

print("ingest" in ordered)   # True
print("chunk" in ordered)    # False
```

### `all(...)`

```python
all(d in ordered for d in dependencies[s])
```

`all()` က condition အားလုံး `True` ဖြစ်မှ `True` ပြန်ပေးပါတယ်။

ဥပမာ —

```python
ordered = ["ingest", "chunk"]

print(all(d in ordered for d in ("ingest", "chunk")))
```

Output —

```text
True
```

ဒါပေမဲ့ —

```python
print(all(d in ordered for d in ("ingest", "embed")))
```

Output —

```text
False
```

အကြောင်းက `embed` က `ordered` ထဲမှာ မရှိသေးလို့ပါ။

အထူးသတိထားရန် — `dependencies[s]` က empty tuple `()` ဖြစ်နေတဲ့အခါ `all()` က `True`
ပြန်ပေးပါတယ်။ ဒါကြောင့် dependency မရှိတဲ့ `ingest` လို stage တွေကို အစမှာ ရွေးချယ်နိုင်တာပါ။

### ဒီ logic ကို ရိုးရိုး Python နဲ့ ရေးကြည့်မယ်

အောက်ပါ code က list comprehension နဲ့ အဓိပ္ပာယ်တူပါတယ်။

```python
ready = []

for s in remaining:
    if all(d in ordered for d in dependencies[s]):
        ready.append(s)
```

ဒီပုံစံနဲ့ ရေးကြည့်ရင် အလုပ်လုပ်ပုံကို ပိုနားလည်နိုင်ပါတယ်။

---

## 9. `assert ready, "dependency cycle detected"`

```python
assert ready, "dependency cycle detected"
```

`assert` က condition တစ်ခု မှန်မမှန် စစ်ဆေးဖို့ အသုံးပြုပါတယ်။

- `ready` ထဲမှာ stage တစ်ခုခုရှိရင် condition က `True` ဖြစ်ပြီး ဆက်လုပ်ပါမယ်။
- `ready` က empty list ဖြစ်နေရင် `AssertionError` ဖြစ်ပြီး `"dependency cycle detected"`
  ဆိုတဲ့ message ကို ပြပါမယ်။

ဘာကြောင့် empty ဖြစ်နိုင်တာလဲ။ ဥပမာ —

```python
dependencies = {
    "ingest": ("chunk",),
    "chunk": ("ingest",),
}
```

ဒီမှာ `ingest` က `chunk` ကို စောင့်နေပြီး `chunk` ကလည်း `ingest` ကို စောင့်နေပါတယ်။
ဘယ် stage ကိုမှ အရင်စလုပ်လို့ မရတော့ပါဘူး။ ဒါကို **dependency cycle** လို့ခေါ်ပါတယ်။

သတိပြုရန် — ဒီ `assert` က cycle ရှိတာတစ်ခုတည်းကို သက်သေမပြနိုင်ပါဘူး။ `ready` မရှိရခြင်းဟာ
stage တစ်ခု၏ dependency ကို dictionary ထဲမှာ မထည့်ထားတာကြောင့်လည်း ဖြစ်နိုင်ပါတယ်။
ဒီဥပမာမှာတော့ dependency dictionary ပြည့်စုံပြီး မှန်ကန်တယ်လို့ ယူဆထားပါတယ်။

---

## 10. `chosen = ready[0]`

```python
chosen = ready[0]
```

`ready` ထဲမှာ dependency ပြည့်မီတဲ့ stage တွေ ရှိနေပါတယ်။ `ready[0]` က list ၏ ပထမဆုံး
item ကို ရွေးယူတာဖြစ်ပါတယ်။ Python list indexing က `0` ကနေ စပါတယ်။

ဥပမာ —

```python
ready = ["ingest", "chunk"]

chosen = ready[0]

print(chosen)
```

Output —

```text
ingest
```

ဒီ code မှာ `remaining` ကို အရင် `sorted()` လုပ်ထားတဲ့အတွက် တစ်ချိန်တည်းမှာ ရွေးချယ်နိုင်တဲ့
stage အများအပြားရှိရင် alphabetical order အရ ပထမဆုံး stage ကို ရွေးချယ်ပါတယ်။ ဒါကြောင့်
result က **deterministic** ဖြစ်ပါတယ်။

---

## 11. `ordered.append(chosen)` နှင့် `remaining.remove(chosen)`

```python
ordered.append(chosen)
remaining.remove(chosen)
```

ဒီနှစ်ကြောင်းက stage တစ်ခု ရွေးချယ်ပြီးနောက် လုပ်ဆောင်ရမယ့် အဆင့်တွေပါ။

ပထမကြောင်း —

```python
ordered.append(chosen)
```

ရွေးချယ်ပြီးသား stage ကို `ordered` list ၏ အဆုံးမှာ ထည့်ပါတယ်။

ဒုတိယကြောင်း —

```python
remaining.remove(chosen)
```

အဲဒီ stage ကို `remaining` list ထဲက ဖယ်ရှားပါတယ်။

ဥပမာ —

```python
ordered = []
remaining = ["chunk", "ingest"]

chosen = "ingest"

ordered.append(chosen)
remaining.remove(chosen)

print(ordered)
print(remaining)
```

Output —

```text
['ingest']
['chunk']
```

အခု `ingest` က ပြီးသွားပြီလို့ သတ်မှတ်ထားတဲ့အတွက် `chunk` ကို နောက်တစ်ကြိမ် dependency
စစ်တဲ့အခါ ရွေးချယ်နိုင်ပါပြီ။

---

## 12. `return ordered`

```python
return ordered
```

Function အလုပ်လုပ်ပြီးဆုံးတဲ့အခါ ရရှိလာတဲ့ list ကို ပြန်ပေးပါတယ်။ `return` က function ၏
result ကို function ကို ခေါ်ထားတဲ့နေရာဆီ ပြန်ပို့ပေးတာပါ။

```python
order = topological_order(UNORDERED_STAGES, PIPELINE_DEPENDENCIES)
```

ဒီမှာ function က ပြန်ပေးတဲ့ list ကို `order` variable ထဲ သိမ်းထားပါတယ်။

---

## 13. နောက်ဆုံး `print(order)` — အစိတ်အပိုင်းအားလုံး ပေါင်းစည်းခြင်း

အပိုင်း ၄ မှ ၁၂ အထိ ရှင်းပြခဲ့သည့် အစိတ်အပိုင်းအားလုံးကို ပေါင်းစည်းလိုက်ပါက runnable script
တစ်ခု အပြည့်အစုံ ရရှိပါတယ်။ အောက်ပါ code ကို ကူးပြီး run ကြည့်နိုင်ပါတယ် —

```python
PIPELINE_DEPENDENCIES = {
    "ingest": (),
    "chunk": ("ingest",),
    "embed": ("chunk",),
    "index": ("embed",),
    "retrieve": ("index",),
    "generate": ("retrieve",),
}
UNORDERED_STAGES = ["generate", "retrieve", "index", "embed", "ingest", "chunk"]

def topological_order(stages, dependencies):
    """Return a deterministic order in which every stage follows its dependencies."""
    ordered = []
    remaining = sorted(set(stages))
    while remaining:
        ready = [s for s in remaining if all(d in ordered for d in dependencies[s])]
        assert ready, "dependency cycle detected"
        chosen = ready[0]
        ordered.append(chosen)
        remaining.remove(chosen)
    return ordered

order = topological_order(UNORDERED_STAGES, PIPELINE_DEPENDENCIES)
print(order)
```

Output —

```python
['ingest', 'chunk', 'embed', 'index', 'retrieve', 'generate']
```

`print(order)` က result ကို screen ပေါ်မှာ ပြပေးတာပါ။

---

## 14. Loop တစ်ပတ်ချင်းစီ ဘယ်လိုပြောင်းလဲသလဲ

အောက်က table မှာ function အလုပ်လုပ်ပုံကို အဆင့်လိုက် ကြည့်နိုင်ပါတယ်။

| Loop | ရွေးချယ်နိုင်တဲ့ stage (`ready`) | ရွေးချယ်သည့် stage | `ordered` |
| --- | --- | --- | --- |
| 1 | ingest | ingest | ingest |
| 2 | chunk | chunk | ingest, chunk |
| 3 | embed | embed | ingest, chunk, embed |
| 4 | index | index | ... embed, index |
| 5 | retrieve | retrieve | ... index, retrieve |
| 6 | generate | generate | ... retrieve, generate |

ဒီဥပမာမှာ stage တစ်ခုချင်းစီဟာ stage တစ်ခုတည်းအပေါ် မှီခိုနေတာကြောင့် အစီအစဉ်က တစ်ဆင့်ချင်း
ဖြစ်ပါတယ်။ အခြား pipeline တွေမှာ stage တစ်ခုက dependency အများအပြားအပေါ် မှီခိုနေနိုင်ပြီး၊
dependency ပြည့်မီတဲ့ stage အများအပြားကိုလည်း ရွေးချယ်နိုင်ပါတယ်။

---

## 15. ကိုယ်တိုင်လေ့ကျင့်ကြည့်ပါ

ဒီ code ၏ အဓိကအယူအဆကို နားလည်ဖို့ မေးခွန်းတစ်ခုပါ။

**မေးခွန်း** — အောက်ပါ dependency ရှိတယ်ဆိုပါစို့။

```python
dependencies = {
    "ingest": (),
    "chunk": ("ingest",),
    "embed": ("chunk",),
}
```

`ordered = ["ingest"]` ဖြစ်နေတဲ့အချိန်မှာ ဘယ် stage ကို `ready` ထဲ ထည့်နိုင်မလဲ။

1. `ingest` တစ်ခုတည်း
2. `chunk` တစ်ခုတည်း
3. `chunk` နဲ့ `embed` နှစ်ခုလုံး
4. Stage အားလုံး

<details>
<summary>အဖြေ ကြည့်ရန်</summary>

**အဖြေ — 2. `chunk` တစ်ခုတည်း**

အကြောင်းရင်း — `ready` ထဲ ဝင်ဖို့ `dependencies[s]` က `ordered` ထဲ အားလုံး ရှိပြီးသား
ဖြစ်ရပါတယ်။

- `ingest` — `ordered` ထဲ ရှိပြီးသား၊ ဒါပေမဲ့ `remaining` ထဲ မရှိတော့သဖြင့် ထပ်ရွေးစရာ မလို
- `chunk` — dependency `("ingest",)` ဖြစ်ပြီး `ingest` က `ordered` ထဲ ရှိပြီး → **ready**
- `embed` — dependency `("chunk",)` ဖြစ်ပြီး `chunk` က `ordered` ထဲ မရှိသေး → ready မဖြစ်

</details>

ဒီ code ၏ အဓိကသဘောတရားက stage တစ်ခုကို dependency အားလုံး ပြည့်မီမှ ရွေးချယ်ပြီး၊
ရွေးချယ်ပြီးတဲ့ stage ကို မှတ်တမ်းတင်ကာ နောက် stage တွေအတွက် ထပ်စစ်ဆေးခြင်း ဖြစ်ပါတယ်။
ဒီနည်းလမ်းကို **Topological Sorting** လို့ခေါ်ပြီး workflow orchestration, build systems နဲ့
data pipelines တွေမှာ အသုံးပြုနိုင်ပါတယ်။
