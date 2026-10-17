# Walkthrough 01 — RAG Pipeline Stage Ordering (Exercise 1)

> ဤဖိုင်သည် `solution.md` ၏ Exercise 1 ကို **Python အခြေခံမှ စ၍** အပိုင်းလိုက် ရှင်းပြသည့်
> walkthrough ဖြစ်သည်။ `explanation.md` သည် သဘောတရားအတွက် ဖြစ်ပြီး၊ ဤဖိုင်သည် code ကို
> လိုင်းတစ်လိုင်းချင်း လိုက်ဖတ်လိုသူအတွက် ဖြစ်သည်။

---

ဤ Python code ကို RAG (Retrieval-Augmented Generation) pipeline တစ်ခုတွင် stages တွေကို
dependency အစီအစဉ်အတိုင်း အလိုအလျောက် စီပေးရန် အသုံးပြုထားသည်။

ဤ code တွင် အဓိကလေ့လာရမည့် Python concepts များသည် dictionary, tuple, list, set, while loop,
list comprehension, all(), assert နှင့် function တို့ဖြစ်သည်။

---

## 1. Pipeline ဟူသည် ဘာလဲ။

Pipeline သည် အလုပ်တစ်ခုကို အဆင့်ဆင့် ဆက်စပ်လုပ်ဆောင်စေသည့် workflow ဖြစ်သည်။

ဥပမာ IT Help Chatbot တွင် user ၏ မေးခွန်းကို ဖြေရန်အတွက် knowledge documents တွေကို
အရင်ပြင်ဆင်ပြီး၊ သက်ဆိုင်သော information တွေကို ရှာဖွေကာ နောက်ဆုံး LLM နှင့် အဖြေထုတ်ရသည်။

- **1. ingest** — Documents များကို လက်ခံသိမ်းဆည်းခြင်း
- **2. chunk** — Documents များကို အပိုင်းငယ်များ ခွဲခြင်း
- **3. embed** — Text ကို vector embeddings ပြောင်းခြင်း
- **4. index** — Vectors များကို ရှာဖွေနိုင်ရန် index လုပ်ခြင်း
- **5. retrieve** — သက်ဆိုင်ရာ content ကို ရှာဖွေခြင်း
- **6. generate** — LLM ဖြင့် အဖြေထုတ်ပေးခြင်း

ဥပမာ chunk stage ကို မလုပ်ရသေးဘဲ embed ကို အရင်လုပ်နိုင်ခြင်း မရှိပါ။ အကြောင်းက embed သည်
chunk ပြီးမှ ရလာသည့် data ကို လိုအပ်သောကြောင့် ဖြစ်သည်။

ဤသို့ အဆင့်တစ်ခုနှင့်တစ်ခု မှီခိုနေမှုကို **dependency** ဟုခေါ်သည်။

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

ဤနေရာတွင် `PIPELINE_DEPENDENCIES` သည် Python dictionary တစ်ခုဖြစ်သည်။ Dictionary တွင်
`key: value` ပုံစံနှင့် data တွေ သိမ်းထားသည်။

ဥပမာ — `"chunk": ("ingest",)` တွင်

- `"chunk"` က key ဖြစ်သည်။
- `("ingest",)` က value ဖြစ်ပြီး chunk အတွက် လိုအပ်သော dependency ကို ဖော်ပြသည်။

ဤ dictionary ထဲက key တစ်ခုချင်းစီသည် pipeline stage တစ်ခုဖြစ်ပြီး value က ထို stage မစခင်
ပြီးထားရမည့် stages တွေကို ဖော်ပြသည်။

| Stage | Dependency | အဓိပ္ပာယ် |
| --- | --- | --- |
| ingest | `()` | အရင်လုပ်စရာ stage မရှိ |
| chunk | `("ingest",)` | ingest ပြီးရမည် |
| embed | `("chunk",)` | chunk ပြီးရမည် |
| index | `("embed",)` | embed ပြီးရမည် |
| retrieve | `("index",)` | index ပြီးရမည် |
| generate | `("retrieve",)` | retrieve ပြီးရမည် |

### `()` နှင့် `("ingest",)` ဘာကွာသလား။

```python
"ingest": ()
```

`()` သည် empty tuple ဖြစ်သည်။ `ingest` stage တွင် dependency မရှိပါဟု ဆိုလိုသည်။

```python
"chunk": ("ingest",)
```

ဤတွင် `("ingest",)` သည် item တစ်ခုပါပါသော tuple ဖြစ်သည်။ Python တွင် item တစ်ခုပါပါသော tuple ကို
သတ်မှတ်သည့်အခါ comma `,` ထည့်ရန် လိုသည်။

```python
print(type(("ingest",)))   # <class 'tuple'>
print(type(("ingest")))    # <class 'str'>
```

ဤကွာခြားချက်က အရေးကြီးသည်။ Function က dependency တွေကို စစ်ဆေးသည့်အခါ tuple ဖြစ်နေရန်
လိုသည်။

---

## 3. `UNORDERED_STAGES` — မူလအစီအစဉ်မကျသည့် stages များ

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

ဤ list ထဲတွင် stages ၆ ခုကို ရည်ရွယ်ချက်ရှိရှိ အစီအစဉ်မကျအောင် ထည့်ထားသည်။

Python က ဤ list အတိုင်းသာ လုပ်ဆောင်မည်ဆိုလျှင် `generate` က အရင်ရောက်နေမည်။ သို့သော်
dependency အရ `generate` ကို နောက်ဆုံးမှ လုပ်ရမည်။

ထို့ကြောင့် `topological_order()` function ကို အသုံးပြုပြီး မှန်ကန်သောအစီအစဉ်ကို ပြန်စီမည်။

မှတ်ချက် — `UNORDERED_STAGES` ဆိုသည့် variable name က list ထဲတွင် မူလအစီအစဉ်ကို
မယုံကြည်ဘဲ dependency အပေါ်မူတည်ပြီး စီမည်ကို ဖော်ပြသည်။

---

## 4. `topological_order()` function

```python
def topological_order(stages, dependencies):
    """Return a deterministic order in which every stage follows its dependencies."""
```

ဤ code က `topological_order` ဆိုသည့် function ကို ဖန်တီးထားခြင်း ဖြစ်သည်။ Function တွင် parameters
နှစ်ခု ပါသည်။

- `stages` — စီစဉ်ပေးရမည့် stage တွေ။
- `dependencies` — Stage တစ်ခုစီ၏ dependency တွေ။

Function ကို ခေါ်သည့်အခါ —

```python
order = topological_order(
    UNORDERED_STAGES,
    PIPELINE_DEPENDENCIES,
)
```

ဆိုပြီး arguments တွေ ပေးလိုက်သည့်အတွက် —

- `stages` ထဲကို `UNORDERED_STAGES` ၏တန်ဖိုး ဝင်လာမည်။
- `dependencies` ထဲကို `PIPELINE_DEPENDENCIES` ၏တန်ဖိုး ဝင်လာမည်။

Function အတွင်းတွင် ဤ data တွေကို အသုံးပြုပြီး အစီအစဉ်ကို တွက်ချက်မည်။

`"""..."""` က docstring ဖြစ်ပြီး function ၏ ရည်ရွယ်ချက်ကို ရှင်းပြထားခြင်း ဖြစ်သည်။

> **မှတ်ချက်** — ဤနေရာတွင် function ၏ **ခေါင်းစီး (signature) နှင့် docstring ကိုသာ** ပြထားသည်။
> Body ကို အောက်ပိုင်း အပိုင်း ၅ မှ ၁၂ အထိ တစ်ကြောင်းချင်း ရှင်းပြထားသည်။ Function အပြည့်အစုံကို
> `solution.md` တွင်လည်း ကြည့်နိုင်ပြီး၊ အစိတ်အပိုင်းအားလုံး ပေါင်းစည်းထားသော runnable version ကို
> အပိုင်း ၁၃ တွင် ဖော်ပြထားသည်။

---

## 5. `ordered = []`

```python
ordered = []
```

ဤတွင် empty list တစ်ခု ဖန်တီးထားသည်။ `ordered` ထဲတွင် dependency အရ မှန်ကန်သောအစီအစဉ်နှင့်
ရွေးချယ်ပြီးသား stages တွေကို ထည့်သွားမည်။

ဥပမာ —

```python
ordered = []
ordered.append("ingest")
```

အခု `ordered` ၏တန်ဖိုးက —

```python
["ingest"]
```

ဖြစ်သွားပါပြီ။ နောက်ထပ် stage တွေကို dependency ပြည့်မီသောအခါ ထပ်ထည့်သွားမည်။

---

## 6. `remaining = sorted(set(stages))`

```python
remaining = sorted(set(stages))
```

ဤတစ်ကြောင်းတွင် Python operations သုံးခုကို တွေ့ရသည်။

### `set(stages)`

`set()` က ထပ်နေသော items တွေကို ဖယ်ရှားပြီး unique values တွေကို ရရှိစေသည်။

ဥပမာ —

```python
stages = ["embed", "ingest", "embed", "chunk"]

print(set(stages))
```

Output က set အမျိုးအစား ဖြစ်သည်။ ပြသသည့်အစီအစဉ်က တစ်သမတ်တည်း ဖြစ်မည်ဟု မယူဆသင့်ပါ။

```text
{'embed', 'ingest', 'chunk'}
```

ဤနေရာတွင် `embed` က နှစ်ခါပါနေပေမဲ့ `set()` က တစ်ခုတည်းသာ ထားပေးသည်။

### `sorted(...)`

`sorted()` က items တွေကို sorting လုပ်ပြီး list အသစ်တစ်ခု ပြန်ပေးသည်။

```python
print(sorted(["generate", "embed", "ingest"]))
```

Output —

```python
['embed', 'generate', 'ingest']
```

ဤ code တွင် `set()` ကို အရင်သုံးပြီး `sorted()` ကို နောက်မှ သုံးထားခြင်းကြောင့် duplicate မရှိဘဲ
အစီအစဉ်တကျ ဖြစ်သွားသည်။

၎င်းကြောင့် —

```python
remaining = sorted(set(stages))
```

သည် stages တွေကို unique ဖြစ်အောင်လုပ်ပြီး alphabetical order နှင့် စီထားသော list ကို `remaining`
ထဲ သိမ်းခြင်းဖြစ်သည်။

သတိပြုရန် — Alphabetical order က dependency order မဟုတ်ပါ။ Function က dependency
ပြည့်မီသော stage ကိုသာ ရွေးချယ်မည်။

---

## 7. `while remaining:`

```python
while remaining:
```

`while` loop သည် condition မှန်နေသရွေ့ code တွေကို ထပ်ခါထပ်ခါ လုပ်ဆောင်ပေးခြင်း ဖြစ်သည်။

Python တွင် —

```python
remaining = ["chunk", "embed"]

while remaining:
    print(remaining)
    remaining.pop()
```

ဆိုလျှင် `remaining` list ထဲတွင် items ရှိနေသေးသရွေ့ loop ဆက်လုပ်ပါမည်။ List အလွတ်ဖြစ်သွားလျှင်
`while remaining` က `False` ဖြစ်သွားပြီး loop ရပ်သွားသည်။

ဤ pipeline code တွင် stage တစ်ခုကို ရွေးချယ်ပြီးတိုင်း `remaining` ထဲကနေ ဖယ်ရှားသည်။
Stage အားလုံး ရွေးချယ်ပြီးသည့်အခါ loop ရပ်သွားမည်။

---

## 8. `ready = [...]` — Dependency ပြည့်မီသော stage ကို ရှာခြင်း

ဤအပိုင်းက code ၏ အဓိက logic ဖြစ်သည်။

```python
ready = [
    s for s in remaining
    if all(d in ordered for d in dependencies[s])
]
```

၎င်းကို **list comprehension** ဟုခေါ်သည်။ အဓိပ္ပာယ်ကို အပိုင်းလိုက် ကြည့်ကြပါမည်။

### `for s in remaining`

```python
for s in remaining
```

`remaining` ထဲက stage တစ်ခုချင်းစီကို `s` ဆိုသည့် variable ထဲ ယူသည်။

ဥပမာ —

```python
remaining = ["chunk", "embed", "generate", "index", "ingest", "retrieve"]
```

ဤ loop က stage တစ်ခုချင်းစီကို စစ်ဆေးသွားမည်။

### `dependencies[s]`

```python
dependencies[s]
```

၎င်းသည် dictionary ထဲက `s` နှင့် သက်ဆိုင်သော dependency ကို ယူခြင်း ဖြစ်သည်။

ဥပမာ —

```python
dependencies = {
    "ingest": (),
    "chunk": ("ingest",),
}

print(dependencies["chunk"])
```

Output —

```text
('ingest',)
```

နောက်ဥပမာ —

```python
dependencies = {
    "ingest": (),
    "chunk": ("ingest",),
}

print(dependencies["ingest"])
```

Output —

```text
()
```

### `d in ordered`

```python
d in ordered
```

၎င်းသည် `d` ဆိုသည့် dependency သည် `ordered` list ထဲတွင် ရှိပြီးသားဖြစ်ခြင်းကို စစ်ဆေးသည်။
ရှိလျှင် `True`၊ မရှိလျှင် `False` ပြန်ပေးသည်။

```python
ordered = ["ingest"]

print("ingest" in ordered)   # True
print("chunk" in ordered)    # False
```

### `all(...)`

```python
all(d in ordered for d in dependencies[s])
```

`all()` က condition အားလုံး `True` ဖြစ်မှ `True` ပြန်ပေးသည်။

ဥပမာ —

```python
ordered = ["ingest", "chunk"]

print(all(d in ordered for d in ("ingest", "chunk")))
```

Output —

```text
True
```

သို့သော် —

```python
ordered = ["ingest", "chunk"]

print(all(d in ordered for d in ("ingest", "embed")))
```

Output —

```text
False
```

အကြောင်းက `embed` က `ordered` ထဲတွင် မရှိသေးသောကြောင့် ဖြစ်သည်။

အထူးသတိထားရန် — `dependencies[s]` က empty tuple `()` ဖြစ်နေသောအခါ `all()` က `True`
ပြန်ပေးသည်။ ထို့ကြောင့် dependency မရှိသည့် `ingest` လို stage တွေကို အစတွင် ရွေးချယ်နိုင်ခြင်း ဖြစ်သည်။

### ဤ logic ကို ရိုးရိုး Python နှင့် ရေးကြည့်မည်

အောက်ပါ code က list comprehension နှင့် အဓိပ္ပာယ်တူသည်။

```python
ready = []

for s in remaining:
    if all(d in ordered for d in dependencies[s]):
        ready.append(s)
```

ဤပုံစံနှင့် ရေးကြည့်လျှင် အလုပ်လုပ်ပုံကို ပိုနားလည်နိုင်သည်။

---

## 9. `assert ready, "dependency cycle detected"`

```python
assert ready, "dependency cycle detected"
```

`assert` က condition တစ်ခု မှန်မမှန် စစ်ဆေးရန် အသုံးပြုသည်။

- `ready` ထဲတွင် stage တစ်ခုခုရှိလျှင် condition က `True` ဖြစ်ပြီး ဆက်လုပ်ပါမည်။
- `ready` က empty list ဖြစ်နေလျှင် `AssertionError` ဖြစ်ပြီး `"dependency cycle detected"`
  ဆိုသည့် message ကို ပြပါမည်။

ဘာကြောင့် empty ဖြစ်နိုင်ခြင်းလဲ။ ဥပမာ —

```python
dependencies = {
    "ingest": ("chunk",),
    "chunk": ("ingest",),
}
```

ဤတွင် `ingest` က `chunk` ကို စောင့်နေပြီး `chunk` ကလည်း `ingest` ကို စောင့်နေသည်။
ဘယ် stage ကိုမှ အရင်စလုပ်နိုင်ခြင်း မရှိတော့ပါ။ ၎င်းကို **dependency cycle** ဟုခေါ်သည်။

သတိပြုရန် — ဤ `assert` က cycle ရှိခြင်းတစ်ခုတည်းကို သက်သေမပြနိုင်ပါ။ `ready` မရှိရခြင်းသည်
stage တစ်ခု၏ dependency ကို dictionary ထဲတွင် မထည့်ထားခြင်းကြောင့်လည်း ဖြစ်နိုင်သည်။
ဤဥပမာတွင် dependency dictionary ပြည့်စုံပြီး မှန်ကန်သည်ဟု ယူဆထားသည်။

---

## 10. `chosen = ready[0]`

```python
chosen = ready[0]
```

`ready` ထဲတွင် dependency ပြည့်မီသော stage တွေ ရှိနေသည်။ `ready[0]` က list ၏ ပထမဆုံး
item ကို ရွေးယူခြင်းဖြစ်သည်။ Python list indexing က `0` ကနေ စသည်။

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

ဤ code တွင် `remaining` ကို အရင် `sorted()` လုပ်ထားသောအတွက် တစ်ချိန်တည်းတွင် ရွေးချယ်နိုင်သည့်
stage အများအပြားရှိလျှင် alphabetical order အရ ပထမဆုံး stage ကို ရွေးချယ်သည်။ ထို့ကြောင့်
result က **deterministic** ဖြစ်သည်။

---

## 11. `ordered.append(chosen)` နှင့် `remaining.remove(chosen)`

```python
ordered.append(chosen)
remaining.remove(chosen)
```

ဤနှစ်ကြောင်းက stage တစ်ခု ရွေးချယ်ပြီးနောက် လုပ်ဆောင်ရမည့် အဆင့်များ ဖြစ်သည်။

ပထမကြောင်း —

```python
ordered.append(chosen)
```

ရွေးချယ်ပြီးသား stage ကို `ordered` list ၏ အဆုံးတွင် ထည့်သည်။

ဒုတိယကြောင်း —

```python
remaining.remove(chosen)
```

ထို stage ကို `remaining` list ထဲက ဖယ်ရှားသည်။

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

အခု `ingest` က ပြီးသွားပြီဟု သတ်မှတ်ထားသောအတွက် `chunk` ကို နောက်တစ်ကြိမ် dependency
စစ်သည့်အခါ ရွေးချယ်နိုင်ပါပြီ။

---

## 12. `return ordered`

```python
return ordered
```

Function အလုပ်လုပ်ပြီးဆုံးသည့်အခါ ရရှိလာသည့် list ကို ပြန်ပေးသည်။ `return` က function ၏
result ကို function ကို ခေါ်ထားသောနေရာဆီ ပြန်ပို့ပေးခြင်း ဖြစ်သည်။

### Function ကို ခေါ်သုံးခြင်း

```python
order = topological_order(UNORDERED_STAGES, PIPELINE_DEPENDENCIES)
```

ဤတွင် function က ပြန်ပေးသည့် list ကို `order` variable ထဲ သိမ်းထားသည်။

---

## 13. နောက်ဆုံး `print(order)` — အစိတ်အပိုင်းအားလုံး ပေါင်းစည်းခြင်း

အပိုင်း ၄ မှ ၁၂ အထိ ရှင်းပြခဲ့သည့် အစိတ်အပိုင်းအားလုံးကို ပေါင်းစည်းလိုက်ပါက runnable script
တစ်ခု အပြည့်အစုံ ရရှိသည်။ အောက်ပါ code ကို ကူးပြီး run ကြည့်နိုင်သည် —

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

`print(order)` က result ကို screen ပေါ်တွင် ပြပေးခြင်း ဖြစ်သည်။

---

## 14. Loop တစ်ပတ်ချင်းစီ ဘယ်လိုပြောင်းလဲသလား

အောက်က table တွင် function အလုပ်လုပ်ပုံကို အဆင့်လိုက် ကြည့်နိုင်သည်။

| Loop | ရွေးချယ်နိုင်သည့် stage (`ready`) | ရွေးချယ်သည့် stage | `ordered` |
| --- | --- | --- | --- |
| 1 | ingest | ingest | ingest |
| 2 | chunk | chunk | ingest, chunk |
| 3 | embed | embed | ingest, chunk, embed |
| 4 | index | index | ... embed, index |
| 5 | retrieve | retrieve | ... index, retrieve |
| 6 | generate | generate | ... retrieve, generate |

ဤဥပမာတွင် stage တစ်ခုချင်းစီသည် stage တစ်ခုတည်းအပေါ် မှီခိုနေခြင်းကြောင့် အစီအစဉ်က တစ်ဆင့်ချင်း
ဖြစ်သည်။ အခြား pipeline တွေတွင် stage တစ်ခုက dependency အများအပြားအပေါ် မှီခိုနေနိုင်ပြီး၊
dependency ပြည့်မီသော stage အများအပြားကိုလည်း ရွေးချယ်နိုင်သည်။

---

## 15. ကိုယ်တိုင်လေ့ကျင့်ကြည့်ပါ

ဤ code ၏ အဓိကအယူအဆကို နားလည်ရန် မေးခွန်းတစ်ခု ဖြစ်သည်။

**မေးခွန်း** — အောက်ပါ dependency ရှိသည်ဆိုပါစို့။

```python
dependencies = {
    "ingest": (),
    "chunk": ("ingest",),
    "embed": ("chunk",),
}
```

`ordered = ["ingest"]` ဖြစ်နေသောအချိန်တွင် ဘယ် stage ကို `ready` ထဲ ထည့်နိုင်မလဲ။

1. `ingest` တစ်ခုတည်း
2. `chunk` တစ်ခုတည်း
3. `chunk` နှင့် `embed` နှစ်ခုလုံး
4. Stage အားလုံး

<details>
<summary>အဖြေ ကြည့်ရန်</summary>

**အဖြေ — 2. `chunk` တစ်ခုတည်း**

အကြောင်းရင်း — `ready` ထဲ ဝင်ရန် `dependencies[s]` က `ordered` ထဲ အားလုံး ရှိပြီးသား
ဖြစ်ရသည်။

- `ingest` — `ordered` ထဲ ရှိပြီးသား၊ သို့သော် `remaining` ထဲ မရှိတော့သဖြင့် ထပ်ရွေးစရာ မလို
- `chunk` — dependency `("ingest",)` ဖြစ်ပြီး `ingest` က `ordered` ထဲ ရှိပြီး → **ready**
- `embed` — dependency `("chunk",)` ဖြစ်ပြီး `chunk` က `ordered` ထဲ မရှိသေး → ready မဖြစ်

</details>

ဤ code ၏ အဓိကသဘောတရားက stage တစ်ခုကို dependency အားလုံး ပြည့်မီမှ ရွေးချယ်ပြီး၊
ရွေးချယ်ပြီးသည့် stage ကို မှတ်တမ်းတင်ကာ နောက် stage တွေအတွက် ထပ်စစ်ဆေးခြင်း ဖြစ်သည်။
ဤနည်းလမ်းကို **Topological Sorting** ဟုခေါ်ပြီး workflow orchestration, build systems နှင့်
data pipelines တွေတွင် အသုံးပြုနိုင်သည်။
