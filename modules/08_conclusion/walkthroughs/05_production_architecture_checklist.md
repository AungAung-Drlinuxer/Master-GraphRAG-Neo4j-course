# Walkthrough 05 — Production architecture checklist (Exercise 5)

> ဤဖိုင်သည် Module 08 ၏ `solution.md` ထဲက Exercise 5 ကို **Python အခြေခံမှ စ၍**
> အပိုင်းလိုက် ရှင်းပြသည့် walkthrough ဖြစ်သည်။

---

## 0. ဤ Exercise က ဘာကို ဖြေရှင်းပေးသလဲ။

GraphRAG architecture တစ်ခုကို production တွင် ချထားမလုပ်မီ **control များ** ရှိ/မရှိ
စစ်ရသည်။ Control တိုင်း တူညီသော အလေးချိန် မဟုတ်ပါ —

```text
critical control တစ်ခု လွဲ  ->  design သည် မအောင်မြင် (total score မည်မျှပင်မြင့်စေကာမူ)
advisory control လွဲ        ->  score ကျပေမဲ့ design ကို ရပ်မထားပါ
```

ဤ Exercise က checklist ကို `(name, satisfied, critical)` tuple အဖြစ် ထားပြီး
audit လုပ်သည်။ အဓိက ရလဒ်က — **total score မြင့်နေခြင်းသည် လုံခြုံမှုကို
မဆိုလိုပါ**။ `read_only_cypher_guardrail` လို critical control တစ်ခု လွဲလျှင် score
`6/7` ဖြစ်နေသော်လည်း `passes=False` ဖြစ်သည်။

ဤ Exercise တွင် လေ့လာရမည့် Python concepts —

- List of tuples နှင့် 3-tuple unpacking
- Comprehension ထဲတွင် `_` placeholder အသုံးပြုခြင်း
- `sum()` generator နှင့် `if` condition
- List comprehension နှင့် `and` condition
- Empty list ၏ **truthiness** နှင့် `not`
- f-string ထဲ conditional expression
- Dict return

---

## 1. `CHECKLIST` — List of 3-Tuples

```python
CHECKLIST = [
    ("entity_uniqueness_constraint", True, True),
    ("ingestion_idempotent_upsert", True, True),
    ("provenance_on_every_triple", True, True),
    ("k_hop_bounded_retrieval", True, True),
    ("read_only_cypher_guardrail", True, True),
    ("retrieval_quality_eval_vs_baseline", True, False),
    ("latency_and_cost_monitoring", True, False),
]

print(CHECKLIST[0])
print(CHECKLIST[0][0])
print(CHECKLIST[0][2])
print(len(CHECKLIST))
```

Output —

```text
('entity_uniqueness_constraint', True, True)
entity_uniqueness_constraint
True
7
```

Item တိုင်းက **tuple သုံးလုံး** —

| နေရာ | အမည် | အဓိပ္ပာယ် |
| --- | --- | --- |
| `[0]` | name | control အမည် |
| `[1]` | satisfied | ဖြည့်ဆည်းပြီး/မပြီး (`True`/`False`) |
| `[2]` | critical | critical control ဖြစ်သည်လား၊ advisory ဖြစ်သည်လား |

`len(CHECKLIST)` က `7` ပြန်ခြင်းသည် control ခုနစ်ခု ရှိကြောင်း ဖော်ပြသည်။

---

## 2. Tuple Unpacking နှင့် Iteration

```python
CHECKLIST = [
    ("entity_uniqueness_constraint", True, True),
    ("latency_and_cost_monitoring", True, False),
]

for name, satisfied, critical in CHECKLIST:
    print(name, "| satisfied =", satisfied, "| critical =", critical)
```

Output —

```text
entity_uniqueness_constraint | satisfied = True | critical = True
latency_and_cost_monitoring | satisfied = True | critical = False
```

`for name, satisfied, critical in CHECKLIST:` က tuple တိုင်းကို **variable သုံးခု**
အဖြစ် ခွဲယူသည်။ `name`, `satisfied`, `critical` များကို loop အတွင်းတွင်
တိုက်ရိုက် သုံးနိုင်သည်။

```python
row = ("read_only_cypher_guardrail", True, True)
name, satisfied, critical = row
print(name)
print(satisfied)
print(critical)
```

Output —

```text
read_only_cypher_guardrail
True
True
```

---

## 3. `{'x' if ok else ' '}` — f-string ထဲ Conditional

```python
for ok in (True, True, False):
    print(f"  [{'x' if ok else ' '}]")
```

Output —

```text
  [x]
  [x]
  [ ]
```

`f"[{'x' if ok else ' '}]"` တွင် `ok` မှန်လျှင် `'x'`၊ မှားလျှင် `' '` (space) ကို
ထည့်သည်။ ၎င်းသည် terminal checklist ပုံစံ — မျက်စိဖြင့် လျင်မြန်စွာ ဖတ်နိုင်သည်။
`'x'` နှင့် `' '` နှစ်ခုလုံး တူညီ width ဖြစ်သောကြောင့် column က မှန်နေသည်။

```python
for ok in (True, False):
    tag = "critical" if ok else "advisory"
    print(f"  [{'x' if ok else ' '}] {tag}")
```

Output —

```text
  [x] critical
  [ ] advisory
```

---

## 4. `sum(1 for _, ok, _ in checklist if ok)` — Underscore နှင့် Condition

```python
CHECKLIST = [
    ("a", True, True),
    ("b", True, False),
    ("c", False, True),
]

print(sum(1 for _, ok, _ in CHECKLIST if ok))
print(sum(1 for _, ok, _ in CHECKLIST))
```

Output —

```text
2
3
```

`sum(1 for _, ok, _ in CHECKLIST if ok)` က — tuple တိုင်းကို unpack လုပ်ပြီး `ok`
က `True` ဖြစ်သော item တိုင်းအတွက် `1` ကို ပေါင်းသည်။ ရလဒ် `2` က satisfied
control နှစ်ခု ရှိကြောင်း ပြသည်။

### `_` placeholder

`for _, ok, _ in CHECKLIST` တွင် `_` ကို **name** နှင့် **critical** နေရာတွင် သုံးသည်။
`_` က \"ဤတန်ဖိုးကို မလိုချင်ပါ\" ဆိုသည့် convention ဖြစ်သည်။ သို့သော် tuple ၏
**အရေအတွက်** ကို တိတိကျကျ ဖော်ပြရန် လိုအပ်သည် — 3-tuple ဖြစ်သောကြောင့် `_` သုံးခု
(သို့) variable သုံးခု လိုအပ်သည်။

```python
pair = ("Alice", 30)
name, _ = pair
print(name)
```

Output —

```text
Alice
```

---

## 5. `critical_failures` — List Comprehension

```python
CHECKLIST = [
    ("entity_uniqueness_constraint", True, True),
    ("read_only_cypher_guardrail", False, True),
    ("latency_and_cost_monitoring", True, False),
]

critical_failures = [name for name, ok, critical in CHECKLIST if critical and not ok]
print(critical_failures)
```

Output —

```text
['read_only_cypher_guardrail']
```

`[name for name, ok, critical in CHECKLIST if critical and not ok]` က **list
comprehension** ဖြစ်သည်။ Condition နှစ်ခု —

- `critical` — ဤ control သည် critical ဖြစ်သည်လား
- `not ok` — ဖြည့်ဆည်းမထားသည်လား (`ok` က `False` ဖြစ်သည်လား)

နှစ်ခုလုံး မှန်သော control များ၏ **name** ကို စုသည်။ `latency_and_cost_monitoring`
က `ok=True` ဖြစ်သောကြောင့် မပါပါ — `entity_uniqueness_constraint` ကလည်း `ok=True` ဖြစ်သောကြောင့်
မပါပါ။

```python
print([1, 2, 3, 4])
print([number for number in [1, 2, 3, 4] if number % 2 == 0])
```

Output —

```text
[1, 2, 3, 4]
[2, 4]
```

---

## 6. `not critical_failures` — Empty List ၏ Truthiness

```python
print(bool([]))
print(bool(["x"]))
print(not [])
print(not ["x"])
print(len([]), len(["x"]))
```

Output —

```text
False
True
True
False
0 1
```

Python တွင် **အလွတ် list က `False`**၊ item ရှိသော list က `True` (truthiness)။
ထို့ကြောင့် `not critical_failures` က —

- `critical_failures = []` → `not []` = `True` → `passes = True`
- `critical_failures = ["read_only_cypher_guardrail"]` → `not [...]` = `False` → `passes = False`

၎င်းသည် `len(critical_failures) == 0` နှင့် အလုပ်တူသော်လည်း ပိုတိုသည်။

```python
for failures in ([], ["read_only_cypher_guardrail"]):
    print(failures, "-> passes =", not failures)
```

Output —

```text
[] -> passes = True
['read_only_cypher_guardrail'] -> passes = False
```

---

## 7. `audit_architecture()` — Function တစ်ခုလုံး

```python
def audit_architecture(checklist):
    total = len(checklist)
    satisfied = sum(1 for _, ok, _ in checklist if ok)
    critical_failures = [name for name, ok, critical in checklist if critical and not ok]
    return {
        "satisfied": satisfied,
        "total": total,
        "score": satisfied / total,
        "critical_failures": critical_failures,
        "passes": not critical_failures,
    }
```

| လိုင်း | လုပ်သည့် အလုပ် |
| --- | --- |
| `total = len(checklist)` | control စုစုပေါင်း |
| `satisfied = sum(...)` | ဖြည့်ဆည်းပြီး အရေအတွက် |
| `critical_failures = [...]` | critical ဖြစ်ပြီး မဖြည့်ဆည်းသေးသော name များ |
| `satisfied / total` | `float` အဖြစ် score |
| `not critical_failures` | critical တစ်ခုမှ မလွဲလျှင် `True` |

---

## 8. Full Run — Score 7/7

```python
CHECKLIST = [
    ("entity_uniqueness_constraint", True, True),
    ("ingestion_idempotent_upsert", True, True),
    ("provenance_on_every_triple", True, True),
    ("k_hop_bounded_retrieval", True, True),
    ("read_only_cypher_guardrail", True, True),
    ("retrieval_quality_eval_vs_baseline", True, False),
    ("latency_and_cost_monitoring", True, False),
]


def audit_architecture(checklist):
    total = len(checklist)
    satisfied = sum(1 for _, ok, _ in checklist if ok)
    critical_failures = [name for name, ok, critical in checklist if critical and not ok]
    return {
        "satisfied": satisfied,
        "total": total,
        "score": satisfied / total,
        "critical_failures": critical_failures,
        "passes": not critical_failures,
    }


report = audit_architecture(CHECKLIST)
for name, ok, critical in CHECKLIST:
    tag = "critical" if critical else "advisory"
    print(f"  [{'x' if ok else ' '}] {name:<36} ({tag})")
print("  score=%d/%d critical_failures=%s" % (report["satisfied"], report["total"], report["critical_failures"]))
print("  passes =", report["passes"])
```

Output —

```text
  [x] entity_uniqueness_constraint         (critical)
  [x] ingestion_idempotent_upsert          (critical)
  [x] provenance_on_every_triple           (critical)
  [x] k_hop_bounded_retrieval              (critical)
  [x] read_only_cypher_guardrail           (critical)
  [x] retrieval_quality_eval_vs_baseline   (advisory)
  [x] latency_and_cost_monitoring          (advisory)
  score=7/7 critical_failures=[]
  passes = True
```

Control ငါးခုက **critical**၊ နှစ်ခုက **advisory** ဖြစ်သည်။ စုစုပေါင်း `score = 7/7 = 1.0`
ဖြစ်ပြီး critical failure သုညဖြစ်သောကြောင့် `passes=True` ပါ။

`{name:<36}` က control အမည်ကို ၃၆ character ကျယ်အောင် ဘယ်ဘက်ချိန်သည်။
`report["score"]` ကို `%d/%d` ဖြင့် ပြရန် `satisfied` နှင့် `total` ကို ခွဲထုတ်ထားသည်
(score က float ဖြစ်သောကြောင့် `%d` မသုံးနိုင်ပါ)။

---

## 9. Guardrail ဖယ်လိုက်ခြင်း — Critical Failure

```python
CHECKLIST = [
    ("entity_uniqueness_constraint", True, True),
    ("ingestion_idempotent_upsert", True, True),
    ("provenance_on_every_triple", True, True),
    ("k_hop_bounded_retrieval", True, True),
    ("read_only_cypher_guardrail", True, True),
    ("retrieval_quality_eval_vs_baseline", True, False),
    ("latency_and_cost_monitoring", True, False),
]


def audit_architecture(checklist):
    total = len(checklist)
    satisfied = sum(1 for _, ok, _ in checklist if ok)
    critical_failures = [name for name, ok, critical in checklist if critical and not ok]
    return {
        "satisfied": satisfied,
        "total": total,
        "score": satisfied / total,
        "critical_failures": critical_failures,
        "passes": not critical_failures,
    }


broken = [(name, ok and name != "read_only_cypher_guardrail", critical)
          for name, ok, critical in CHECKLIST]
broken_report = audit_architecture(broken)
print("  score=%d/%d critical_failures=%s" % (broken_report["satisfied"], broken_report["total"], broken_report["critical_failures"]))
print("  score value = %.4f" % broken_report["score"])
print("  passes =", broken_report["passes"])
```

Output —

```text
  score=6/7 critical_failures=['read_only_cypher_guardrail']
  score value = 0.8571
  passes = False
```

### `ok and name != "read_only_cypher_guardrail"`

List comprehension ထဲက expression `(name, ok and name != "read_only_cypher_guardrail", critical)`
သည်—

- `read_only_cypher_guardrail` အတွက် — `True and ("read_only_cypher_guardrail" != "read_only_cypher_guardrail")`
  = `True and False` = `False`။
- အခြား control များအတွက် — `True and True` = `True`။

ထို့ကြောင့် `read_only_cypher_guardrail` ၏ `ok` ကို **`False`** လုပ်ပြီး critical
control တစ်ခု လွဲသည့် အခြေအနေကို **simulate** လုပ်သည်။

| အခြေအနေ | satisfied | score | critical_failures | passes |
| --- | --- | --- | --- | --- |
| ပြည့်စုံသော design | `7` | `1.0` (`7/7`) | `[]` | `True` |
| guardrail ဖယ်လိုက် | `6` | `0.8571` (`6/7`) | `['read_only_cypher_guardrail']` | `False` |

Score က `0.8571` — **မြင့်နေဆဲ** ဖြစ်သော်လည်း `passes` က `False` ဖြစ်သည်။ ၎င်းသည်
Exercise ၏ အဓိက သင်ခန်းစာ — critical control ကို total score နှင့် မပေါင်းရပါ။

---

## 10. Code တစ်ခုလုံး — Run လုပ်နိုင်သော Version

```python
CHECKLIST = [
    ("entity_uniqueness_constraint", True, True),
    ("ingestion_idempotent_upsert", True, True),
    ("provenance_on_every_triple", True, True),
    ("k_hop_bounded_retrieval", True, True),
    ("read_only_cypher_guardrail", True, True),
    ("retrieval_quality_eval_vs_baseline", True, False),
    ("latency_and_cost_monitoring", True, False),
]


def audit_architecture(checklist):
    total = len(checklist)
    satisfied = sum(1 for _, ok, _ in checklist if ok)
    critical_failures = [name for name, ok, critical in checklist if critical and not ok]
    return {
        "satisfied": satisfied,
        "total": total,
        "score": satisfied / total,
        "critical_failures": critical_failures,
        "passes": not critical_failures,
    }


report = audit_architecture(CHECKLIST)
for name, ok, critical in CHECKLIST:
    tag = "critical" if critical else "advisory"
    print(f"  [{'x' if ok else ' '}] {name:<36} ({tag})")
print("  score=%d/%d critical_failures=%s" % (report["satisfied"], report["total"], report["critical_failures"]))
print("  passes =", report["passes"])

broken = [(name, ok and name != "read_only_cypher_guardrail", critical)
          for name, ok, critical in CHECKLIST]
broken_report = audit_architecture(broken)
print("  guardrail removed -> critical_failures=%s" % broken_report["critical_failures"])
print("  passes =", broken_report["passes"])
print("a single missing critical control blocks the design regardless of total score")
```

Output —

```text
  [x] entity_uniqueness_constraint         (critical)
  [x] ingestion_idempotent_upsert          (critical)
  [x] provenance_on_every_triple           (critical)
  [x] k_hop_bounded_retrieval              (critical)
  [x] read_only_cypher_guardrail           (critical)
  [x] retrieval_quality_eval_vs_baseline   (advisory)
  [x] latency_and_cost_monitoring          (advisory)
  score=7/7 critical_failures=[]
  passes = True
  guardrail removed -> critical_failures=['read_only_cypher_guardrail']
  passes = False
a single missing critical control blocks the design regardless of total score
```

---

## 11. ရလဒ်ကို ပြန်ကြည့်ခြင်း

| စစ်ဆေးချက် | Code | ရလဒ် |
| --- | --- | --- |
| ပြည့်စုံသော design အောင် | `report["passes"] is True` | `True` |
| Score 1.0 | `report["score"] == 1.0` | `True` |
| Critical failure မရှိ | `report["critical_failures"] == []` | `True` |
| Guardrail ဖယ်လျှင် မအောင် | `broken_report["passes"] is False` | `False` |
| Failure အမည် တိကျ | `broken_report["critical_failures"] == ["read_only_cypher_guardrail"]` | `True` |

`retrieval_quality_eval_vs_baseline` နှင့် `latency_and_cost_monitoring` က advisory
ဖြစ်သောကြောင့် လွဲလျှင် score ကျသော်လည်း `passes` က `True` ဆက်ဖြစ်သည်။

---

## 12. ကိုယ်တိုင်လေ့ကျင့်ကြည့်ပါ

**မေးခွန်း** — အောက်ပါ code က ဘယ်ရလဒ် ပြန်ပေးမလဲ။

```python
CHECKLIST = [
    ("a", False, True),
    ("b", False, False),
    ("c", True, False),
]
total = len(CHECKLIST)
satisfied = sum(1 for _, ok, _ in CHECKLIST if ok)
critical_failures = [name for name, ok, critical in CHECKLIST if critical and not ok]
print("satisfied=%d/%d critical_failures=%s passes=%s"
      % (satisfied, total, critical_failures, not critical_failures))
```

1. `satisfied=1/3 critical_failures=['a'] passes=False`
2. `satisfied=2/3 critical_failures=['a'] passes=False`
3. `satisfied=1/3 critical_failures=[] passes=True`
4. `satisfied=1/3 critical_failures=['a', 'b'] passes=False`

<details>
<summary>အဖြေ ကြည့်ရန်</summary>

**အဖြေ — 1. `satisfied=1/3 critical_failures=['a'] passes=False`**

အကြောင်းရင်း — `ok` က `True` ဖြစ်သည့် item က `("c", True, False)` တစ်ခုတည်း
ဖြစ်သဖြင့် `satisfied=1`၊ `total=3`။

`critical_failures` အတွက် condition က `critical and not ok` —

- `("a", False, True)` — `critical=True`၊ `ok=False` → ပါသည်
- `("b", False, False)` — `critical=False` → `not ok` ဖြစ်သော်လည်း `critical` မမှန်၊ မပါ
- `("c", True, False)` — `ok=True` → မပါ

ထို့ကြောင့် `critical_failures=['a']`။ `not ['a']` က `False` ဖြစ်သဖြင့် `passes=False`
ဖြစ်သည်။

</details>

---

**အဓိက မှတ်ထားရန်** — Text-to-Cypher ကဲ့သို့ LLM က graph ကို တိုက်ရိုက်ရေးနိုင်သော
pattern တွင် read-only guardrail သည် အဓိက control ဖြစ်သည်။ `DELETE`၊
`DETACH DELETE`၊ `DROP` clause များကို block မလုပ်ပါက prompt injection တစ်ခုတည်းဖြင့်
graph တစ်ခုလုံး ပျက်စီးနိုင်သည်။ Critical control ကို total score နှင့် မ
ပေါင်းရ — score မြင့်နေခြင်းသည် လုံခြုံမှုကို မဆိုလိုပါ။ Checklist ထဲက control
အမည်များနှင့် critical/advisory ခွဲခြားမှုသည် course example ဖြစ်သည် — သင့်
threat model အလိုက် ပြန်သတ်မှတ်ရမည်။
