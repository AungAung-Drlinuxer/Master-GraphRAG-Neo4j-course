# Walkthrough 03 — Build-vs-buy decision scorer (Exercise 3)

> ဤဖိုင်သည် Module 08 ၏ `solution.md` ထဲက Exercise 3 ကို **Python အခြေခံမှ စ၍**
> အပိုင်းလိုက် ရှင်းပြသည့် walkthrough ဖြစ်သည်။

---

## 0. ဤ Exercise က ဘာကို ဖြေရှင်းပေးသလဲ။

GraphRAG ကို **ကိုယ်တိုင် build** မလား၊ **managed service** ကို **buy** မလား။
ဒီမေးခွန်းကို ခံစားချက်နဲ့ ဖြေလို့ မရပါ။ Criteria တိုင်းကို 0–5 scale ဖြင့် score
ပေးပြီး၊ အဖွဲ့အစည်း အတွက် အရေးကြီးမှုကို **weight** အဖြစ် သတ်မှတ်ပြီးမှ
weighted total ကို နှိုင်းယှဉ်ရပါတယ်။

```text
criteria tိုင်း: weight (0..1) x score (0..5) = weighted term
                                       |
                     build terms ပေါင်း -> score_build
                     buy   terms ပေါင်း -> score_buy
                                       |
                     score_build > score_buy ? "build" : "buy"
```

အဓိက အချက်က — **weight ပြောင်းလိုက်ရင် ဆုံးဖြတ်ချက် ပြောင်းနိုင်သည်**။ ဒါကြောင့်
\"GraphRAG ကို build လုပ်သင့်သည်\" ဆိုတဲ့ universal အဖြေ မရှိပါ။

ဒီ Exercise မှာ လေ့လာရမယ့် Python concepts —

- `OrderedDict` နှင့် criteria စာရင်း
- `sum()` — list နှင့် **generator expression**
- `dict.items()` နှင့် tuple unpacking (`key, weight`)
- `assert` နှင့် `AssertionError`
- Conditional expression (`"build" if ... else "buy"`)
- Tuple return နှင့် unpacking
- `zip()` ဖြင့် dict နှစ်ခု တွဲခြင်း
- Default parameter (`build_scores=BUILD_SCORES`)

---

## 1. Criteria သုံးစု — Weights နှင့် Scores

```python
from collections import OrderedDict

BUILD_VS_BUY_WEIGHTS = OrderedDict([
    ("time_to_first_value", 0.25),
    ("control_and_customization", 0.20),
    ("operating_cost_at_scale", 0.20),
    ("compliance_and_data_residency", 0.15),
    ("engineering_capacity", 0.20),
])

BUILD_SCORES = OrderedDict([
    ("time_to_first_value", 2.0),
    ("control_and_customization", 5.0),
    ("operating_cost_at_scale", 4.0),
    ("compliance_and_data_residency", 5.0),
    ("engineering_capacity", 2.0),
])

BUY_SCORES = OrderedDict([
    ("time_to_first_value", 5.0),
    ("control_and_customization", 2.0),
    ("operating_cost_at_scale", 2.0),
    ("compliance_and_data_residency", 2.0),
    ("engineering_capacity", 5.0),
])

print(list(BUILD_VS_BUY_WEIGHTS))
print(BUILD_SCORES["time_to_first_value"])
print(BUY_SCORES["time_to_first_value"])
```

Output —

```text
['time_to_first_value', 'control_and_customization', 'operating_cost_at_scale', 'compliance_and_data_residency', 'engineering_capacity']
2.0
5.0
```

Dict သုံးခုလုံးမှာ **key ငါးခု တူညီ** ပါတယ် — criteria အမည်တူကို ကိုးကားလို့ပါ။
Key တူညီတာက အရေးကြီးပါတယ် — `weighted_score` က `scores[key]` လို့ key ဖြင့်
တွဲဖတ်လို့ပါ။

`BUILD_VS_BUY_WEIGHTS` က criteria တိုင်း၏ **အလေးချိန်** ဖြစ်ပြီး ပေါင်းလဒ်က
`1.0` ဖြစ်ရပါတယ် (normalized weights)။ `BUILD_SCORES` နဲ့ `BUY_SCORES` က
option နှစ်ခုအတွက် **0–5 score** ဖြစ်ပါတယ်။

```python
print(BUILD_VS_BUY_WEIGHTS["engineering_capacity"])
print(BUILD_SCORES["engineering_capacity"])
print(BUY_SCORES["engineering_capacity"])
```

Output —

```text
0.2
2.0
5.0
```

ဒီဇယားက ဆန့်ကျင်ဘက် ဖြစ်ပါတယ် — build က engineering capacity နည်း (`2.0`)၊
buy က မြင့် (`5.0`)။ Managed service က engineering ကို အစားထိုးပေးလို့ပါ။

---

## 2. `sum()` — List နှင့် Generator ဖြင့်

`sum(iterable)` က item များကို ပေါင်းပါတယ်။

```python
numbers = [1, 2, 3, 4]
print(sum(numbers))
print(sum(x * 2 for x in numbers))
print(sum([]))
```

Output —

```text
10
20
0
```

- ပထမလိုင်း — list ကို တိုက်ရိုက် ပေါင်း။
- ဒုတိယလိုင်း — **generator expression** `(x * 2 for x in numbers)` ကို ပေါင်း။
- တတိယလိုင်း — အလွတ် iterable အတွက် `0` ပြန်သည် (ပေါင်းစရာ မရှိ)။

Weight များ၏ ပေါင်းလဒ် စစ်တဲ့အခါ `dict.values()` ကို သုံးပါတယ်။

```python
from collections import OrderedDict

weights = OrderedDict([("a", 0.25), ("b", 0.20), ("c", 0.20), ("d", 0.15), ("e", 0.20)])
print(sum(weights.values()))
print(abs(sum(weights.values()) - 1.0) < 1e-9)
```

Output —

```text
1.0
True
```

`weights.values()` က value များ (`0.25, 0.20, …`) ကို ပြန်ပါတယ်။ ပေါင်းလဒ်က `1.0`
တိတိကျကျ ရပါတယ်။

---

## 3. `weighted_score()` — Term တိုင်း ခွဲပြခြင်း

```python
from collections import OrderedDict

weights = OrderedDict([
    ("time_to_first_value", 0.25),
    ("control_and_customization", 0.20),
    ("operating_cost_at_scale", 0.20),
    ("compliance_and_data_residency", 0.15),
    ("engineering_capacity", 0.20),
])
build = OrderedDict([
    ("time_to_first_value", 2.0),
    ("control_and_customization", 5.0),
    ("operating_cost_at_scale", 4.0),
    ("compliance_and_data_residency", 5.0),
    ("engineering_capacity", 2.0),
])

total = 0.0
for key, weight in weights.items():
    term = build[key] * weight
    total += term
    print("%.2f * %.1f = %.4f" % (weight, build[key], term))
print("total = %.3f" % total)
```

Output —

```text
0.25 * 2.0 = 0.5000
0.20 * 5.0 = 1.0000
0.20 * 4.0 = 0.8000
0.15 * 5.0 = 0.7500
0.20 * 2.0 = 0.4000
total = 3.450
```

| Criterion | weight | build score | term |
| --- | --- | --- | --- |
| time_to_first_value | 0.25 | 2.0 | 0.5000 |
| control_and_customization | 0.20 | 5.0 | 1.0000 |
| operating_cost_at_scale | 0.20 | 4.0 | 0.8000 |
| compliance_and_data_residency | 0.15 | 5.0 | 0.7500 |
| engineering_capacity | 0.20 | 2.0 | 0.4000 |
| **total (build)** | | | **3.450** |

`weights.items()` က `(key, value)` tuple များကို ပြန်ပါတယ်။ `for key, weight in ...`
လို့ tuple unpacking နဲ့ ခွဲယူပါတယ်။ `total += term` က running sum ဖြစ်ပါတယ်။

Function အနေဖြင့် ပြန်ရေးရင် **generator expression** ဖြင့် တစ်လိုင်းတည်း —
`sum(scores[key] * weight for key, weight in weights.items())`။

---

## 4. `assert` — Weight စစ်ဆေးခြင်း

```python
from collections import OrderedDict


def weighted_score(scores, weights):
    assert abs(sum(weights.values()) - 1.0) < 1e-9, "weights must sum to 1.0"
    return sum(scores[key] * weight for key, weight in weights.items())


good = OrderedDict([("a", 0.5), ("b", 0.5)])
print(weighted_score(OrderedDict([("a", 1.0), ("b", 1.0)]), good))

bad = OrderedDict([("a", 0.5), ("b", 0.4)])
try:
    weighted_score(OrderedDict([("a", 1.0), ("b", 1.0)]), bad)
except AssertionError as exc:
    print("AssertionError:", exc)
```

Output —

```text
1.0
AssertionError: weights must sum to 1.0
```

`assert condition, message` က `condition` မှန်ရင် ဘာမှ မလုပ်ဘဲ ဆက်၊ မှားရင်
`AssertionError` ကို `message` နှင့်တကွ ပစ်ပါတယ်။ ဒီနေရာမှာ weight များ ပေါင်းလဒ်က
`1.0` မဖြစ်ရင် **program ကို ရပ်တန့်** စေပါတယ်။

`good` အတွက် term များ — `1.0 * 0.5 = 0.5`၊ `1.0 * 0.5 = 0.5`၊ ပေါင်းလဒ် `1.0`။
`bad` အတွက် ပေါင်းလဒ်က `0.9` ဖြစ်လို့ `abs(0.9 - 1.0) = 0.1 > 1e-9` အမှန် ဖြစ်ပြီး
assert က ကျပါတယ်။

> `assert` ကို၍ စစ်ဆေးချက်များ သည် **developer အတွက်** ဖြစ်သည်။ Production မှာ
> user input အတွက် `assert` မသုံးရပါ — `python -O` flag ဖြင့် run ရင် `assert` များ
> ကို Python က ကျော်လိုက်သည်။

---

## 5. `build_vs_buy()` — ဆုံးဖြတ်ချက် ထုတ်ခြင်း

```python
from collections import OrderedDict

BUILD_VS_BUY_WEIGHTS = OrderedDict([
    ("time_to_first_value", 0.25),
    ("control_and_customization", 0.20),
    ("operating_cost_at_scale", 0.20),
    ("compliance_and_data_residency", 0.15),
    ("engineering_capacity", 0.20),
])
BUILD_SCORES = OrderedDict([
    ("time_to_first_value", 2.0), ("control_and_customization", 5.0),
    ("operating_cost_at_scale", 4.0), ("compliance_and_data_residency", 5.0),
    ("engineering_capacity", 2.0),
])
BUY_SCORES = OrderedDict([
    ("time_to_first_value", 5.0), ("control_and_customization", 2.0),
    ("operating_cost_at_scale", 2.0), ("compliance_and_data_residency", 2.0),
    ("engineering_capacity", 5.0),
])


def weighted_score(scores, weights):
    assert abs(sum(weights.values()) - 1.0) < 1e-9, "weights must sum to 1.0"
    return sum(scores[key] * weight for key, weight in weights.items())


def build_vs_buy(weights, build_scores=BUILD_SCORES, buy_scores=BUY_SCORES):
    score_build = weighted_score(build_scores, weights)
    score_buy = weighted_score(buy_scores, weights)
    decision = "build" if score_build > score_buy else "buy"
    return decision, score_build, score_buy


decision, score_build, score_buy = build_vs_buy(BUILD_VS_BUY_WEIGHTS)
print(decision, "%.3f" % score_build, "%.3f" % score_buy)
```

Output —

```text
build 3.450 3.350
```

### 5.1 Default parameter

`def build_vs_buy(weights, build_scores=BUILD_SCORES, buy_scores=BUY_SCORES):`
တွင် `build_scores` နဲ့ `buy_scores` က **default value** ရှိပါတယ်။ ဒါကြောင့်
`build_vs_buy(weights)` လို့ ခေါ်ရင် default score များကို သုံးပါတယ်။

```python
def greet(name, greeting="Hello"):
    print(greeting, name)

greet("Alice")
greet("Bob", "Hi")
```

Output —

```text
Hello Alice
Hi Bob
```

### 5.2 Conditional expression

`decision = "build" if score_build > score_buy else "buy"` က **conditional expression**
(traditional term — ternary) ဖြစ်ပါတယ်။ `X if condition else Y` ပုံစံမို့
`if/else` block ကို တစ်လိုင်းတည်း ရေးတာပါ။

```python
print("build" if 3.45 > 3.35 else "buy")
print("build" if 3.05 > 3.80 else "buy")
print("tie" if 3.5 > 3.5 else "buy")
```

Output —

```text
build
buy
buy
```

တတိယလိုင်းက `3.5 > 3.5` က `False` ဖြစ်လို့ `"buy"` ရပါတယ်။ Code ထဲမှာ `>` သုံးသဖြင့်
**score တူညီပါက `buy` ကို ရွေး**ပါတယ်။ ဒါက deterministic tie-breaking ဖြစ်ပါတယ် —
ဒါမှ rerun တိုင်း output တူမှာပါ။

### 5.3 Tuple return နှင့် unpacking

`return decision, score_build, score_buy` က tuple သုံးလုံး ပြန်ပါတယ်။
`decision, score_build, score_buy = build_vs_buy(...)` က unpacking ပါ။

```python
def min_max(values):
    return min(values), max(values)

low, high = min_max([3, 1, 4, 1, 5])
print(low, high)
```

Output —

```text
1 5
```

---

## 6. Default Weight ဖြင့် ရလဒ် — Losing Option ပါ ပြခြင်း

```python
from collections import OrderedDict

def weighted_score(scores, weights):
    return sum(scores[key] * weight for key, weight in weights.items())


weights = OrderedDict([
    ("time_to_first_value", 0.25), ("control_and_customization", 0.20),
    ("operating_cost_at_scale", 0.20), ("compliance_and_data_residency", 0.15),
    ("engineering_capacity", 0.20),
])
build = OrderedDict([
    ("time_to_first_value", 2.0), ("control_and_customization", 5.0),
    ("operating_cost_at_scale", 4.0), ("compliance_and_data_residency", 5.0),
    ("engineering_capacity", 2.0),
])
buy = OrderedDict([
    ("time_to_first_value", 5.0), ("control_and_customization", 2.0),
    ("operating_cost_at_scale", 2.0), ("compliance_and_data_residency", 2.0),
    ("engineering_capacity", 5.0),
])

for key, weight in weights.items():
    print("%-32s %.2f*%.1f=%.4f  buy %.2f*%.1f=%.4f"
          % (key, weight, build[key], build[key] * weight,
             weight, buy[key], buy[key] * weight))
score_build = weighted_score(build, weights)
score_buy = weighted_score(buy, weights)
print("summary: build=%.3f buy=%.3f winner=%s"
      % (score_build, score_buy, "build" if score_build > score_buy else "buy"))
```

Output —

```text
time_to_first_value              0.25*2.0=0.5000  buy 0.25*5.0=1.2500
control_and_customization        0.20*5.0=1.0000  buy 0.20*2.0=0.4000
operating_cost_at_scale          0.20*4.0=0.8000  buy 0.20*2.0=0.4000
compliance_and_data_residency    0.15*5.0=0.7500  buy 0.15*2.0=0.3000
engineering_capacity             0.20*2.0=0.4000  buy 0.20*5.0=1.0000
summary: build=3.450 buy=3.350 winner=build
```

| Criterion | build term | buy term | ဘက် မြင့်သည် |
| --- | --- | --- | --- |
| time_to_first_value | 0.5000 | 1.2500 | buy |
| control_and_customization | 1.0000 | 0.4000 | build |
| operating_cost_at_scale | 0.8000 | 0.4000 | build |
| compliance_and_data_residency | 0.7500 | 0.3000 | build |
| engineering_capacity | 0.4000 | 1.0000 | buy |
| **total** | **3.450** | **3.350** | **build** |

`buy` က criteria ၂ ခုတွင် မြင့်ပေမဲ့ total က `3.350` ဖြစ်လို့ **ရှုံး**ပါတယ်။
`build` က total `3.450` ဖြင့် အနိုင်ရပါတယ်။ ရှုံးတဲ့ option ၏ score ကို ပြထားတာက
ဆုံးဖြတ်ချက်၏ **margin** (`0.100`) ကို မြင်စေပါတယ်။

---

## 7. Weight ပြောင်းလိုက်ခြင်း — ဆုံးဖြတ်ချက် လှန်ခြင်း

```python
from collections import OrderedDict

time_first = OrderedDict([
    ("time_to_first_value", 0.40),
    ("control_and_customization", 0.15),
    ("operating_cost_at_scale", 0.15),
    ("compliance_and_data_residency", 0.10),
    ("engineering_capacity", 0.20),
])
build = OrderedDict([("time_to_first_value", 2.0), ("control_and_customization", 5.0),
                     ("operating_cost_at_scale", 4.0), ("compliance_and_data_residency", 5.0),
                     ("engineering_capacity", 2.0)])
buy = OrderedDict([("time_to_first_value", 5.0), ("control_and_customization", 2.0),
                   ("operating_cost_at_scale", 2.0), ("compliance_and_data_residency", 2.0),
                   ("engineering_capacity", 5.0)])


def weighted_score(scores, weights):
    return sum(scores[key] * weight for key, weight in weights.items())


score_build = weighted_score(build, time_first)
score_buy = weighted_score(buy, time_first)
print("summary: build=%.3f buy=%.3f winner=%s"
      % (score_build, score_buy, "build" if score_build > score_buy else "buy"))
```

Output —

```text
summary: build=3.050 buy=3.800 winner=buy
```

`time_to_first_value` weight ကို `0.25` မှ `0.40` သို့ တင်လိုက်ခြင်းဖြင့် —
build `3.450 → 3.050` ကျပြီး buy `3.350 → 3.800` တက်ပါတယ်။ ဘာကြောင့်လဲ —
`time_to_first_value` မှာ buy ၏ score (`5.0`) က build (`2.0`) ထက် အများကြီး မြင့်လို့
အလေးချိန် တင်လိုက်ရင် buy က အကျိုးအမြတ် ပိုရပါတယ်။

| Weight set | score_build | score_buy | winner |
| --- | --- | --- | --- |
| default (`time_to_first_value=0.25`) | `3.450` | `3.350` | build |
| time-first (`time_to_first_value=0.40`) | `3.050` | `3.800` | buy |

ဒီဇယားက Exercise ၏ အဓိက ရလဒ်ပါ — **weight sensitivity**။ Weight က
အဖွဲ့အစည်း၏ ဦးစားပေးမှုကို ဖော်ပြသဖြင့်၊ weight ကို ရှင်းရှင်းလင်းလင်း
ညှိနှိုင်းပြီးမှ ဆုံးဖြတ်ရပါတယ်။

---

## 8. `zip()` — Dict နှစ်ခု တွဲခြင်း

`zip(a, b)` က iterable နှစ်ခုကို item တစ်လုံးချင်း တွဲပါတယ်။

```python
from collections import OrderedDict

scores = OrderedDict([("a", 2.0), ("b", 5.0), ("c", 4.0)])
weights = OrderedDict([("a", 0.25), ("b", 0.20), ("c", 0.20)])

print(list(zip(scores, weights)))
print(list(zip(scores.values(), weights.values())))
```

Output —

```text
[('a', 'a'), ('b', 'b'), ('c', 'c')]
[(2.0, 0.25), (5.0, 0.2), (4.0, 0.2)]
```

Dict ကို `zip` ထဲ ထည့်ရင် **key** များကို တွဲပါတယ် (dict က key အပေါ် iterate လုပ်လို့)။
`.values()` ဖြင့် တွဲရင် `(2.0, 0.25)` လို score-weight အတွဲ ရပါတယ်။

```python
for score, weight in zip([2.0, 5.0, 4.0], [0.25, 0.20, 0.20]):
    print("%.1f x %.2f = %.4f" % (score, weight, score * weight))
```

Output —

```text
2.0 x 0.25 = 0.5000
5.0 x 0.20 = 1.0000
4.0 x 0.20 = 0.8000
```

`zip` ဖြင့် weight နဲ့ score ကို တွဲပြီး term များ ထုတ်နိုင်ပါတယ်။

---

## 9. Code တစ်ခုလုံး — Run လုပ်နိုင်သော Version

```python
from collections import OrderedDict

BUILD_VS_BUY_WEIGHTS = OrderedDict([
    ("time_to_first_value", 0.25),
    ("control_and_customization", 0.20),
    ("operating_cost_at_scale", 0.20),
    ("compliance_and_data_residency", 0.15),
    ("engineering_capacity", 0.20),
])

BUILD_SCORES = OrderedDict([
    ("time_to_first_value", 2.0),
    ("control_and_customization", 5.0),
    ("operating_cost_at_scale", 4.0),
    ("compliance_and_data_residency", 5.0),
    ("engineering_capacity", 2.0),
])

BUY_SCORES = OrderedDict([
    ("time_to_first_value", 5.0),
    ("control_and_customization", 2.0),
    ("operating_cost_at_scale", 2.0),
    ("compliance_and_data_residency", 2.0),
    ("engineering_capacity", 5.0),
])


def weighted_score(scores, weights):
    assert abs(sum(weights.values()) - 1.0) < 1e-9, "weights must sum to 1.0"
    return sum(scores[key] * weight for key, weight in weights.items())


def build_vs_buy(weights, build_scores=BUILD_SCORES, buy_scores=BUY_SCORES):
    score_build = weighted_score(build_scores, weights)
    score_buy = weighted_score(buy_scores, weights)
    decision = "build" if score_build > score_buy else "buy"
    return decision, score_build, score_buy


decision, score_build, score_buy = build_vs_buy(BUILD_VS_BUY_WEIGHTS)
for key, weight in BUILD_VS_BUY_WEIGHTS.items():
    print("  %-32s weight=%.2f  build=%.1f  buy=%.1f"
          % (key, weight, BUILD_SCORES[key], BUY_SCORES[key]))
print("  weighted: build=%.3f  buy=%.3f  -> decision=%s"
      % (score_build, score_buy, decision))

time_first = OrderedDict([
    ("time_to_first_value", 0.40),
    ("control_and_customization", 0.15),
    ("operating_cost_at_scale", 0.15),
    ("compliance_and_data_residency", 0.10),
    ("engineering_capacity", 0.20),
])
decision2, score_build2, score_buy2 = build_vs_buy(time_first)
print("  time-to-value weighted up: build=%.3f buy=%.3f -> %s"
      % (score_build2, score_buy2, decision2))
```

Output —

```text
  time_to_first_value              weight=0.25  build=2.0  buy=5.0
  control_and_customization        weight=0.20  build=5.0  buy=2.0
  operating_cost_at_scale          weight=0.20  build=4.0  buy=2.0
  compliance_and_data_residency    weight=0.15  build=5.0  buy=2.0
  engineering_capacity             weight=0.20  build=2.0  buy=5.0
  weighted: build=3.450  buy=3.350  -> decision=build
  time-to-value weighted up: build=3.050 buy=3.800 -> buy
```

---

## 10. ရလဒ်ကို ပြန်ကြည့်ခြင်း

| စစ်ဆေးချက် | Code | ရလဒ် |
| --- | --- | --- |
| Default: build ရွေး | `decision == "build"` | `True` |
| Default score | `score_build=3.45, score_buy=3.35` | `assert` အောင်သည် |
| Time-first: buy ရွေး | `decision2 == "buy"` | `True` |
| Time-first score | `score_build2=3.05, score_buy2=3.80` | `assert` အောင်သည် |
| Weight ပေါင်းလဒ် | `sum(weights.values()) == 1.0` | `True` |

ဒီဇယားက ဆုံးဖြတ်ချက် နှစ်ခုလုံးကို စစ်ဆေးပြပါတယ်။ Weight က `1.0` ဖြစ်ရမည်ဆိုတဲ့
စည်းမျဉ်းကို `assert` က ကာကွယ်ပါတယ် — weight များ မှားယွင်းပေါင်းမိရင် score က
scale ပြောင်းသွားပြီး ဆုံးဖြတ်ချက် မှားနိုင်ပါတယ်။

---

## 11. ကိုယ်တိုင်လေ့ကျင့်ကြည့်ပါ

**မေးခွန်း** — အောက်ပါ code က ဘယ်ရလဒ် ပြန်ပေးမလဲ။

```python
from collections import OrderedDict


def weighted_score(scores, weights):
    return sum(scores[key] * weight for key, weight in weights.items())


weights = OrderedDict([("a", 0.50), ("b", 0.50)])
build = OrderedDict([("a", 1.0), ("b", 5.0)])
buy = OrderedDict([("a", 5.0), ("b", 1.0)])
score_build = weighted_score(build, weights)
score_buy = weighted_score(buy, weights)
print("%.3f %.3f %s" % (score_build, score_buy, "build" if score_build > score_buy else "buy"))
```

1. `3.000 3.000 build` — weight များတူလို့
2. `3.000 3.000 buy` — tie ဖြစ်လို့ `else` branch
3. `1.000 5.000 build` — score တိုက်ရိုက်
4. `6.000 6.000 buy` — sum မှား

<details>
<summary>အဖြေ ကြည့်ရန်</summary>

**အဖြေ — 2. `3.000 3.000 buy`**

အကြောင်းရင်း — build ၏ term များ — `1.0 * 0.5 = 0.5`၊ `5.0 * 0.5 = 2.5`၊ ပေါင်းလဒ် `3.0`။
buy ၏ term များ — `5.0 * 0.5 = 2.5`၊ `1.0 * 0.5 = 0.5`၊ ပေါင်းလဒ် `3.0`။ နှစ်ခုလုံး
`3.000` ဖြစ်သည်။

ဆုံးဖြတ်ချက်က `"build" if score_build > score_buy else "buy"` ဖြစ်သည်။ `3.000 > 3.000`
က `False` ဖြစ်သဖြင့် `else` branch ကို ယူပြီး `"buy"` ရသည်။ ဤအချက်သည် tie
ဖြစ်သည့်အခါ code က `buy` ကို deterministic အနေဖြင့် ရွေးကြောင်း ပြသည် —
တန်ဖိုးများ ပြောင်းလိုက်သည့်အခါ ဤ tie-breaking ကို သိထားရသည်။

</details>

---

**အဓိက မှတ်ထားရန်** — Score သည် weight ပေါ်တွင် မှီခိုသည်၊ ထို့ကြောင့် \"GraphRAG ကို
build လုပ်သင့်သည်\" ဆိုသည့် ဖြေချက် မရှိပါ။ အဖွဲ့အစည်း၏ engineering capacity နှင့်
time-to-value ဦးစားပေးမှုကို weight အဖြစ် တိတိကျကျ ရေးပြီးမှ ဆုံးဖြတ်ရမည်။ ဤ code ၏
score များ (0–5) နှင့် weight များသည် course example ဖြစ်သည် — သင့် context အတွက်
ကိုယ်တိုင် သတ်မှတ်ရမည်။
