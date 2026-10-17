# Walkthrough 06 — GraphRAG Readiness Check (Exercise 6)

> ဤဖိုင်သည် `solution.md` ၏ Exercise 6 ကို **Python အခြေခံမှ စ၍** အပိုင်းလိုက် ရှင်းပြသည့်
> walkthrough ဖြစ်သည်။ Format သည် `walkthroughs/01_pipeline_stage_ordering.md` မှ
> `05_triple_spo_parsing.md` အထိ နှင့် တူညီသည်။

---

ဤ Exercise တွင် Python ကို အသုံးပြုပြီး GraphRAG system တစ်ခု တည်ဆောက်ရန်
အဆင်သင့် ဖြစ်/မဖြစ်ကို Metrics နှင့် Configuration Checks များအပေါ် မူတည်ပြီး
စစ်ဆေးခြင်း (Readiness Assessment) ကို လေ့လာပါမည်။

အရင် Exercise 5 တွင် text ကနေ Subject, Predicate, Object (SPO) triples တွေကို
ထုတ်ယူခဲ့သည်။ ဤ Exercise 6 တွင် GraphRAG အတွက် အရေးကြီးသော entities၊
relationships၊ duplicate entities၊ chunk size နှင့် indexing configuration တွေကို
စစ်ဆေးမည်။

ဥပမာ Enterprise IT Help Chatbot တစ်ခုတွင် GraphRAG ကို အသုံးပြုမည်ဆိုပါစို့။ Documents
တွေထဲက entities တွေကို လုံလောက်အောင် ထုတ်ယူထားသလား၊ relationships တွေ
လုံလောက်သလား၊ duplicate entities အလွန်များနေသလား၊ လိုအပ်သော indexes တွေ
တည်ဆောက်ထားခြင်း ရှိ/မရှိကို စစ်ဆေးရန် လိုအပ်သည်။

ဤ Exercise တွင် အဓိကလေ့လာရမည့် Python concepts များသည် —

- tuple နှင့် configuration data
- `>=` နှင့် `<=` comparison operators
- `if` statements နှင့် `return`
- `for` loop
- `not` operator
- List အတွင်း results တွေ စုဆောင်းခြင်း
- Conditional expression
- Dictionary ထဲက metrics တွေကို ဖတ်ရှုခြင်း

---

## 1. GraphRAG Readiness Check ဟူသည် ဘာလဲ။

GraphRAG (Graph Retrieval-Augmented Generation) က Knowledge Graph ထဲက entities နှင့်
relationships တွေကို အသုံးပြုပြီး information ရှာဖွေခြင်း၊ reasoning လုပ်ခြင်းနှင့်
answers ထုတ်ပေးခြင်းတွေကို ပံ့ပိုးပေးနိုင်သည်။ သို့သော် GraphRAG အတွက် data
quality နှင့် infrastructure configuration တွေ အရေးကြီးသည်။

```text
        GraphRAG Data & Configuration
   Entities, relationships, chunk size, indexes, summaries
                            |
                            v
                     Readiness Checks
         သတ်မှတ်ထားသည့် thresholds နှင့် requirements များကို စစ်ဆေးခြင်း
                            |
              +-------------+-------------+
              |                           |
              v                           v
           READY                     NOT_READY
   Checks အားလုံး အောင်မြင်    Check တစ်ခု သို့မဟုတ်
                                  တစ်ခုထက်ပို၍ မအောင်မြင်ပါ
```

ဤ Exercise က **rule-based readiness checker** တစ်ခု ဖြစ်သည်။ သတ်မှတ်ထားသော metrics
တွေနှင့် boolean configuration flags တွေကို စစ်ပြီး `READY` သို့မဟုတ် `NOT_READY` ကို
ပြန်ပေးသည်။

သတိပြုရန် — ဤ code ထဲက thresholds တွေသည် သင်ခန်းစာအတွက် သတ်မှတ်ထားသော ဥပမာတန်ဖိုးတွေ
ဖြစ်သည်။ GraphRAG system အားလုံးအတွက် မဖြစ်မနေ လိုက်နာရမည့် universal industry
standards တွေ မဟုတ်ပါ။ Production system တစ်ခုတွင် အသုံးပြုမည့် data၊ retrieval
quality နှင့် workload အပေါ် မူတည်ပြီး သတ်မှတ်သင့်သည်။

---

## 2. `NUMERIC_CHECKS` — ကိန်းဂဏန်း Metrics များကို စစ်ဆေးခြင်း

မူရင်း code ကို ကြည့်ပါ။

```python
NUMERIC_CHECKS = (
    ("entity_coverage", ">=", 0.85),
    ("relationship_density", ">=", 1.50),
    ("duplicate_entity_rate", "<=", 0.05),
    ("avg_chunk_tokens", "<=", 512.0),
)
```

`NUMERIC_CHECKS` က tuple တစ်ခု ဖြစ်သည်။ အတွင်းတွင် numeric checks ၄ ခု
ပါဝင်သည်။ Tuple တစ်ခုစီတွင် items သုံးခု ပါဝင်သည်။

```python
("entity_coverage", ">=", 0.85)
```

ထို items တွေ၏ အဓိပ္ပာယ်က —

- `"entity_coverage"` — စစ်ဆေးမည့် metric ၏ အမည်။
- `">="` — အသုံးပြုမည့် comparison operator။
- `0.85` — သတ်မှတ်ထားသော threshold သို့မဟုတ် အနည်းဆုံးတန်ဖိုး။

ဤ configuration ကို ဖတ်ပြီး Python က metric တန်ဖိုးတစ်ခုစီကို threshold နှင့်
နှိုင်းယှဉ်နိုင်သည်။

### 2.1 `entity_coverage`

```python
("entity_coverage", ">=", 0.85)
```

ဤစည်းမျဉ်းတွင် `entity_coverage` က `0.85` ထက်ကြီးရမည်၊ သို့မဟုတ် `0.85` နှင့်
ညီရပါမည်။ `0.85` က percentage အနေနှင့် 85% ကို ကိုယ်စားပြုသည်။

ဥပမာ —

```python
entity_coverage = 0.93

print(entity_coverage >= 0.85)
```

Output —

```text
True
```

ဆိုလိုခြင်းက entity coverage 93% ဖြစ်သောကြောင့် သတ်မှတ်ထားသော 85% threshold ကို
ကျော်လွန်နေသည်။

Entity coverage က ဤ Exercise အတွက် သတ်မှတ်ထားသော metric ဖြစ်ပြီး၊ အမှန်တကယ်
production system တွင် ဘယ် entities တွေကို denominator အဖြစ် အသုံးပြုမလဲခြင်းကို
ရှင်းလင်းစွာ သတ်မှတ်ရန် လိုအပ်သည်။

### 2.2 `relationship_density`

```python
("relationship_density", ">=", 1.50)
```

ဤ metric ၏တန်ဖိုးက `1.50` ထက်ကြီးရမည်၊ သို့မဟုတ် ညီရပါမည်။

ဤ Exercise တွင် `relationship_density` ကို numeric metric တစ်ခုအဖြစ်သာ ယူဆထားသည်။
တကယ့် GraphRAG implementation တွင် ဤ metric ကို မည်သို့ တွက်ချက်ထားသည်ကို
အရေးကြီးသည်။ ဥပမာ node တစ်ခုစီအတွက် ပျမ်းမျှ relationships အရေအတွက်လား၊
သို့မဟုတ် အခြား graph density metric ဖြစ်/မဖြစ်ကို သတ်မှတ်ရန် လိုအပ်သည်။

```python
relationship_density = 2.40

print(relationship_density >= 1.50)
```

Output —

```text
True
```

ဤတန်ဖိုးက သတ်မှတ်ထားသော threshold ကို အောင်မြင်သည်။

### 2.3 `duplicate_entity_rate`

```python
("duplicate_entity_rate", "<=", 0.05)
```

ဤတစ်ခုက အရင်နှစ်ခုနှင့် မတူသော comparison operator ကို သုံးသည်။ `<=` က
"ထက်ငယ် သို့မဟုတ် ညီမျှ" ဟု အဓိပ္ပာယ်ရသည်။ ထို့ကြောင့် `duplicate_entity_rate` က
`0.05` သို့မဟုတ် 5% ထက် မများရပါ။

ဥပမာ —

```python
duplicate_entity_rate = 0.02

print(duplicate_entity_rate <= 0.05)
```

Output —

```text
True
```

ဤ metric က duplicate entity rate 2% ဖြစ်သောကြောင့် threshold 5% ကို အောင်မြင်သည်။

GraphRAG တွင် duplicate entities များလွန်းလျှင် entity တစ်ခုတည်းကို graph nodes
အများအပြားအဖြစ် ကိုယ်စားပြုမိနိုင်သည်။ ဥပမာ `Kubernetes Cluster A` နှင့်
`Cluster A` တို့က အတူတူ entity ဖြစ်နေပေမဲ့ မတူညီသော nodes အဖြစ် မှတ်တမ်းတင်မိလျှင်
graph relationships တွေ ပြန့်ကျဲသွားနိုင်သည်။

### 2.4 `avg_chunk_tokens`

```python
("avg_chunk_tokens", "<=", 512.0)
```

ဤစည်းမျဉ်းက ပျမ်းမျှ chunk token count သည် `512` ထက် မကျော်ရပါဟု သတ်မှတ်ထားသည်။

```python
avg_chunk_tokens = 384.0

print(avg_chunk_tokens <= 512.0)
```

Output —

```text
True
```

ထို့ကြောင့် check အောင်မြင်သည်။

Chunk တစ်ခုချင်းစီ၏ အရွယ်အစားသည် retrieval quality၊ context completeness၊
embedding model နှင့် LLM context window တို့အပေါ် သက်ရောက်နိုင်သည်။ သို့သော် `512` သည်
အမြဲတမ်း အကောင်းဆုံးတန်ဖိုး မဟုတ်ပါ။ သုံးမည့် embedding model နှင့် document type
အပေါ် မူတည်ပြီး သတ်မှတ်သင့်သည်။

---

## 3. `BOOLEAN_CHECKS` — Configuration များကို စစ်ဆေးခြင်း

Code ၏ နောက်ထပ်အပိုင်းက —

```python
BOOLEAN_CHECKS = (
    "uniqueness_constraint",
    "fulltext_index",
    "community_summary",
)
```

ဤ tuple ထဲတွင် Boolean checks သုံးခု ပါဝင်သည်။ Numeric checks တွေတွင် `0.85`၊
`1.50`၊ `0.05` လို ကိန်းဂဏန်းတွေနှင့် နှိုင်းယှဉ်ခဲ့သည်။ ဤတစ်ခုတွင် configuration
တစ်ခုစီ ရှိမရှိ၊ ဖွင့်ထားခြင်း ရှိ/မရှိ၊ ပြီးစီးခြင်း ရှိ/မရှိကို `True` သို့မဟုတ် `False` နှင့်
စစ်ဆေးသည်။

### 3.1 `uniqueness_constraint`

ဤ check က Graph database တွင် entity တစ်ခုစီ၏ unique identity ကို ထိန်းသိမ်းပေးသည့်
uniqueness constraint လိုအပ်ချက်ကို ကိုယ်စားပြုသည်။

ဥပမာ Neo4j တွင် `Entity` node တစ်ခုစီ၏ `id` ကို unique ဖြစ်စေချင်လျှင် ထို property
အပေါ် constraint သတ်မှတ်နိုင်သည်။

ဤ Exercise တွင် —

```python
"uniqueness_constraint": True
```

ဆိုလျှင် လိုအပ်သော constraint ကို ပြင်ဆင်ထားပြီးဖြစ်သည်ဟု သတ်မှတ်သည်။

```python
"uniqueness_constraint": False
```

ဆိုလျှင် ဤ check မအောင်မြင်ပါ။

### 3.2 `fulltext_index`

```python
"fulltext_index": True
```

ဤ flag က လိုအပ်သော full-text index ကို ပြင်ဆင်ထားကြောင်း ကိုယ်စားပြုသည်။

Full-text search က စကားလုံးတွေ၊ စာသားအပိုင်းတွေကို ရှာဖွေရန် အသုံးဝင်သည်။ Vector
Search က semantic similarity အပေါ် အခြေခံပြီး ရှာဖွေသလိုမဟုတ်ဘဲ full-text index က
သတ်မှတ်ထားသော text-search mechanism ကို ပံ့ပိုးပေးသည်။

GraphRAG system တစ်ခုတွင် full-text retrieval နှင့် graph-based retrieval ကို
ပေါင်းစပ်အသုံးပြုရန် ဤသို့ index တစ်ခု လိုအပ်နိုင်သည်။ သို့သော် workload အားလုံးတွင်
full-text index မဖြစ်မနေလိုသည်ဟု ဤ code က သတ်မှတ်ထားခြင်း မဟုတ်ပါ။ ဤ Exercise
အတွက် readiness requirement အဖြစ် သတ်မှတ်ထားခြင်း ဖြစ်သည်။

### 3.3 `community_summary`

```python
"community_summary": True
```

ဤ flag က GraphRAG community summaries တွေကို လိုအပ်သောအတိုင်း ပြင်ဆင်ပြီး/မပြီးကို
ကိုယ်စားပြုသည်။

Community summary သည် Knowledge Graph ထဲက ဆက်စပ်နေသော entities နှင့် relationships
တွေကို အုပ်စုဖွဲ့ပြီး ထိုအုပ်စုအကြောင်း အကျဉ်းချုပ်ထားသော information ဖြစ်သည်။

ဥပမာ IT infrastructure graph တစ်ခုထဲတွင် Kubernetes clusters၊ applications၊
databases နှင့် monitoring tools တွေကို ဆက်စပ်မှုအရ community အုပ်စုတစ်ခုအဖြစ်
ဖွဲ့ထားနိုင်သည်။ ထို community အကြောင်း အကျဉ်းချုပ်ထားခြင်းက system အနှံ့ဆက်စပ်သည့်
မေးခွန်းတွေကို ဖြေဆိုရာတွင် အသုံးဝင်နိုင်သည်။

ဤ Exercise တွင် `community_summary` က `False` ဖြစ်နေလျှင် readiness check မအောင်မြင်ပါဟု
သတ်မှတ်သည်။

---

## 4. `_numeric_pass()` function — Numeric Check ကို စစ်ဆေးခြင်း

အခု numeric metrics တွေကို စစ်ဆေးပေးသည့် function ကို ကြည့်ပါ။

```python
def _numeric_pass(value, operator, threshold):
    if operator == ">=":
        return value >= threshold
    return value <= threshold
```

ဤ function က arguments သုံးခုကို လက်ခံသည်။

- `value` — စစ်ဆေးမည့် metric တန်ဖိုး။
- `operator` — အသုံးပြုမည့် comparison operator။
- `threshold` — နှိုင်းယှဉ်ရမည့် သတ်မှတ်တန်ဖိုး။

### 4.1 ပထမ `if` condition

```python
if operator == ">=":
    return value >= threshold
```

ဤတွင် `operator` ၏တန်ဖိုးက `">="` နှင့် ညီမညီ စစ်ဆေးသည်။

ဥပမာ —

```python
_numeric_pass(0.93, ">=", 0.85)
```

Function ထဲတွင် `0.93 >= 0.85` ကို စစ်ဆေးခြင်းကြောင့် `True` ပြန်ပေးသည်။

နောက်ဥပမာ —

```python
_numeric_pass(0.71, ">=", 0.85)
```

ဤတွင် `0.71` က `0.85` ထက်ငယ်သည့်အတွက် `False` ပြန်ပေးသည်။

### 4.2 နောက်ဆုံး `return`

```python
return value <= threshold
```

ဤ statement ကို ပထမ `if` condition မအောင်မြင်သည့်အခါ လုပ်ဆောင်သည်။

ဥပမာ —

```python
_numeric_pass(0.02, "<=", 0.05)
```

ဤအခါ `0.02 <= 0.05` ကို စစ်ဆေးပြီး `True` ပြန်ပေးသည်။

တစ်ဖန် —

```python
_numeric_pass(0.12, "<=", 0.05)
```

ဆိုလျှင် `0.12` သည် `0.05` ထက်ကြီးသည့်အတွက် `False` ပြန်ပေးသည်။

### 4.3 ဤ function အတွက် အရေးကြီးသော မှတ်ချက်

ဤ function က လက်ရှိ `NUMERIC_CHECKS` ထဲတွင် သတ်မှတ်ထားသော operator နှစ်မျိုးဖြစ်သည့် `>=`
နှင့် `<=` အတွက် အလုပ်လုပ်သည်။ သို့သော် operator က တခြားတန်ဖိုးတစ်ခု ဖြစ်နေခဲ့လျှင်လည်း
code က `return value <= threshold` ကို အလိုအလျောက် လုပ်ဆောင်သွားပါမည်။ ၎င်းသည်
မရည်ရွယ်ထားသော **bug** ဖြစ်နိုင်သည်။

ပိုမိုခိုင်မာအောင် ရေးမည်ဆိုလျှင် —

```python
def _numeric_pass(value, operator, threshold):
    if operator == ">=":
        return value >= threshold
    elif operator == "<=":
        return value <= threshold
    else:
        raise ValueError(f"Unsupported operator: {operator}")
```

ဟု ရေးနိုင်သည်။ ဤပုံစံတွင် မထောက်ပံ့ထားသော operator တစ်ခု ဝင်လာလျှင် မှားယွင်းသည့်
comparison ကို တိတ်တဆိတ် လုပ်မည့်အစား `ValueError` ကို ထုတ်ပေးပါလိမ့်မည်။

```text
ValueError: Unsupported operator: !=
```

---

## 5. `readiness_report(metrics)` function

ဤ function က Exercise 6 ၏ အဓိက logic ဖြစ်သည်။

```python
def readiness_report(metrics):
    failed = []
    for name, operator, threshold in NUMERIC_CHECKS:
        if not _numeric_pass(metrics[name], operator, threshold):
            failed.append(name)
    for name in BOOLEAN_CHECKS:
        if not metrics[name]:
            failed.append(name)
    return {
        "verdict": "READY" if not failed else "NOT_READY",
        "failed": failed,
    }
```

ဤ function ကို အဆင့်လိုက် ရှင်းပြပါမည်။

### 5.1 `failed = []`

```python
failed = []
```

ဤတွင် empty list တစ်ခု ဖန်တီးထားသည်။ မအောင်မြင်သည့် checks တွေ၏ အမည်တွေကို ဤ list
ထဲတွင် စုဆောင်းသွားမည်။

ဥပမာ —

```python
failed = []
failed.append("entity_coverage")
failed.append("fulltext_index")

print(failed)
```

Output —

```text
['entity_coverage', 'fulltext_index']
```

Check အားလုံး အောင်မြင်လျှင် `failed` က empty list အတိုင်း ကျန်နေပါမည်။

### 5.2 Numeric checks တွေကို Loop လုပ်ခြင်း

```python
for name, operator, threshold in NUMERIC_CHECKS:
    if not _numeric_pass(metrics[name], operator, threshold):
        failed.append(name)
```

ဤတွင် `NUMERIC_CHECKS` tuple ထဲက check ၄ ခုကို တစ်ခုချင်းစီ ယူသည်။ ဥပမာ —

```python
("entity_coverage", ">=", 0.85)
```

ဤ tuple ကို unpack လုပ်လိုက်သည့်အခါ —

```text
name      = "entity_coverage"
operator  = ">="
threshold = 0.85
```

ဖြစ်လာသည်။ ပြီးလျှင် —

```python
metrics[name]
```

ကို အသုံးပြုပြီး `metrics` dictionary ထဲက လက်ရှိ metric တန်ဖိုးကို ရယူသည်။

ဥပမာ —

```python
metrics = {
    "entity_coverage": 0.93
}

print(metrics["entity_coverage"])
```

Output —

```text
0.93
```

ဤတန်ဖိုးကို `_numeric_pass()` function ထဲ ပေးပြီး threshold နှင့် နှိုင်းယှဉ်သည်။

### `if not _numeric_pass(...)` ဟူသည် ဘာလဲ။

```python
if not _numeric_pass(metrics[name], operator, threshold):
    failed.append(name)
```

`_numeric_pass()` က `True` ပြန်ပေးလျှင် check အောင်မြင်သည်။ ထို `True` ၏ ရှေ့တွင်
`not` ထည့်ထားသောအတွက် `False` ဖြစ်သွားသည်။ ထို့ကြောင့် `failed.append(name)` ကို
မလုပ်ပါ။

တစ်ဖန် `_numeric_pass()` က `False` ပြန်ပေးလျှင် `not False` က `True` ဖြစ်သည်။
ထို့ကြောင့် metric name ကို `failed` list ထဲ ထည့်သည်။

အဓိပ္ပာယ်က **check မအောင်မြင်သည့် metrics တွေကိုသာ** `failed` ထဲ ထည့်ခြင်း ဖြစ်သည်။

### 5.3 Boolean checks တွေကို Loop လုပ်ခြင်း

```python
for name in BOOLEAN_CHECKS:
    if not metrics[name]:
        failed.append(name)
```

ဤအပိုင်းက `BOOLEAN_CHECKS` ထဲက configuration သုံးခုကို စစ်ဆေးသည်။

ဥပမာ —

```python
metrics = {
    "uniqueness_constraint": True,
    "fulltext_index": False,
    "community_summary": False,
}
```

Loop က `name` တစ်ခုချင်းစီကို ရယူသည်။ `if not metrics[name]:` တွင် တန်ဖိုးက `False`
ဖြစ်နေလျှင် `not False` က `True` ဖြစ်သည့်အတွက် ထို configuration name ကို `failed`
list ထဲ ထည့်သည်။

ထို့ကြောင့် အထက်က ဥပမာတွင် —

```python
[
    "fulltext_index",
    "community_summary",
]
```

ဆိုသည့် `failed` list ကို ရရှိပါမည်။

### 5.4 `return` နှင့် Verdict ပြန်ပေးခြင်း

```python
return {
    "verdict": "READY" if not failed else "NOT_READY",
    "failed": failed,
}
```

ဤအပိုင်းတွင် dictionary တစ်ခုကို ပြန်ပေးထားသည်။ Dictionary ထဲတွင် key နှစ်ခု
ပါဝင်သည်။

- `"verdict"` — Readiness result။
- `"failed"` — မအောင်မြင်သည့် checks တွေ၏ အမည်တွေ။

ဤ expression က Python ၏ **conditional expression** ဖြစ်သည်။

### Conditional expression ၏ အသုံးပြုပုံ

```python
"READY" if not failed else "NOT_READY"
```

အဓိပ္ပာယ်က —

- `failed` list အလွတ်ဖြစ်လျှင် `"READY"`။
- `failed` list ထဲတွင် အနည်းဆုံး item တစ်ခုရှိလျှင် `"NOT_READY"`။

Python တွင် empty list က falsy ဖြစ်သည့်အတွက် —

```python
not []
```

က `True` ပြန်ပေးသည်။ ဥပမာ —

```python
failed = []
verdict = "READY" if not failed else "NOT_READY"

print(verdict)
```

Output —

```text
READY
```

တစ်ဖန် —

```python
failed = ["fulltext_index"]
verdict = "READY" if not failed else "NOT_READY"

print(verdict)
```

Output —

```text
NOT_READY
```

ဤသို့ conditional expression သုံးခြင်းက `if`/`else` block ကို သီးခြားရေးစရာမလိုဘဲ တန်ဖိုးတစ်ခုကို
အတိုချုံး ရွေးချယ်နိုင်သည့် နည်းလမ်းဖြစ်သည်။

---

## 6. `READY_PROFILE` — Checks အားလုံး အောင်မြင်သော Profile

```python
READY_PROFILE = {
    "entity_coverage": 0.93,
    "relationship_density": 2.40,
    "duplicate_entity_rate": 0.02,
    "avg_chunk_tokens": 384.0,
    "uniqueness_constraint": True,
    "fulltext_index": True,
    "community_summary": True,
}
```

ဤ dictionary က readiness checks အားလုံးကို အောင်မြင်ရန် ရည်ရွယ်ထားသော sample metrics
တွေကို သိမ်းထားသည်။ အခု check တစ်ခုချင်းစီကို တွက်ကြည့်ပါမည်။

| Metric / Configuration | တန်ဖိုး | လိုအပ်ချက် | ရလဒ် |
| --- | --- | --- | --- |
| `entity_coverage` | 0.93 | `>= 0.85` | Pass |
| `relationship_density` | 2.40 | `>= 1.50` | Pass |
| `duplicate_entity_rate` | 0.02 | `<= 0.05` | Pass |
| `avg_chunk_tokens` | 384.0 | `<= 512.0` | Pass |
| `uniqueness_constraint` | `True` | `True` ဖြစ်ရမည် | Pass |
| `fulltext_index` | `True` | `True` ဖြစ်ရမည် | Pass |
| `community_summary` | `True` | `True` ဖြစ်ရမည် | Pass |

Numeric checks ၄ ခုလုံး အောင်မြင်ပြီး Boolean checks သုံးခုလုံးလည်း `True` ဖြစ်သည်။
ထို့ကြောင့် —

```python
print(readiness_report(READY_PROFILE))
```

ကို run လုပ်သည့်အခါ အောက်ပါ output ကို ရရှိသည်။

```text
{'verdict': 'READY', 'failed': []}
```

`failed` က empty list ဖြစ်နေသောအတွက် check မအောင်မြင်သည့် metric မရှိပါ။ ထို့ကြောင့်
`verdict` က `"READY"` ဖြစ်သည်။

သို့သော် ဤရလဒ်သည် ဤ Exercise တွင် သတ်မှတ်ထားသော checks တွေကို အောင်မြင်သည်ဟု
ဆိုလိုခြင်းသာ ဖြစ်သည်။ Production quality၊ retrieval accuracy၊ security၊ latency နှင့်
answer correctness အားလုံးကို အတည်ပြုပေးခြင်း မဟုတ်ပါ။

---

## 7. `BLOCKED_PROFILE` — Checks အချို့ မအောင်မြင်သော Profile

အခု ဒုတိယ profile ကို ကြည့်ကြပါမည်။

```python
BLOCKED_PROFILE = {
    "entity_coverage": 0.71,
    "relationship_density": 1.10,
    "duplicate_entity_rate": 0.12,
    "avg_chunk_tokens": 640.0,
    "uniqueness_constraint": True,
    "fulltext_index": False,
    "community_summary": False,
}
```

ဤ profile တွင် readiness requirements အချို့ မပြည့်မီပါ။

### 7.1 Numeric checks

| Metric | တန်ဖိုး | လိုအပ်ချက် | ဘာကြောင့် မအောင်မြင်သလား |
| --- | --- | --- | --- |
| `entity_coverage` | 0.71 | `>= 0.85` | Coverage 71% ဖြစ်သောကြောင့် လိုအပ်သော 85% ထက်နည်းသည် |
| `relationship_density` | 1.10 | `>= 1.50` | သတ်မှတ်ထားသော threshold ထက်နည်းသည် |
| `duplicate_entity_rate` | 0.12 | `<= 0.05` | Duplicate rate 12% ဖြစ်သောကြောင့် 5% ထက်များသည် |
| `avg_chunk_tokens` | 640.0 | `<= 512.0` | ပျမ်းမျှ token count က 512 ထက်များသည် |

ဤ metric ၄ ခုလုံးက check မအောင်မြင်သည့်အတွက် `failed` list ထဲ ထည့်ပါမည်။

### 7.2 Boolean checks

| Configuration | တန်ဖိုး | ရလဒ် |
| --- | --- | --- |
| `uniqueness_constraint` | `True` | Pass |
| `fulltext_index` | `False` | Fail |
| `community_summary` | `False` | Fail |

`uniqueness_constraint` က `True` ဖြစ်သည့်အတွက် မအောင်မြင်သည့် list ထဲ မပါဝင်ပါ။ သို့သော်
`fulltext_index` နှင့် `community_summary` နှစ်ခုစလုံး `False` ဖြစ်သည့်အတွက် `failed`
list ထဲ ထည့်ပါမည်။

ဤ profile အတွက် စုစုပေါင်း failed checks ခြောက်ခု ရှိသည်။

- `entity_coverage`
- `relationship_density`
- `duplicate_entity_rate`
- `avg_chunk_tokens`
- `fulltext_index`
- `community_summary`

ထို့ကြောင့် —

```python
print(readiness_report(BLOCKED_PROFILE))
```

၏ output က —

```text
{'verdict': 'NOT_READY', 'failed': ['entity_coverage', 'relationship_density', 'duplicate_entity_rate', 'avg_chunk_tokens', 'fulltext_index', 'community_summary']}
```

ဖြစ်သည်။ `uniqueness_constraint` တစ်ခုတည်းက အောင်မြင်ပေမဲ့ ကျန်သော checks ခြောက်ခု
မအောင်မြင်သည့်အတွက် `verdict` က `"NOT_READY"` ဖြစ်သည်။

---

## 8. Code တစ်ခုလုံး အလုပ်လုပ်ပုံ

ဤ Exercise ကို အဆင့်လိုက် flow အနေနှင့် ပြန်ကြည့်ကြပါမည်။

```text
Step 1 — Read Metrics
   READY_PROFILE သို့မဟုတ် BLOCKED_PROFILE ကို လက်ခံခြင်း
                |
                v
Step 2 — Numeric Checks
   Metrics ၄ ခုကို သတ်မှတ်ထားသည့် thresholds နှင့် စစ်ဆေးခြင်း
                |
                v
Step 3 — Boolean Checks
   Configuration flags ၃ ခုကို စစ်ဆေးခြင်း
                |
                v
Step 4 — Collect Failed Checks
   မအောင်မြင်သည့် check names များကို failed list ထဲ ထည့်ခြင်း
                |
      +---------+---------+
      |                   |
      v                   v
   READY              NOT_READY
 failed == []       Failed checks ရှိသည်
```

---

## 9. ပြန်လည်လေ့ကျင့်ရန် Runnable Code

အောက်ပါ code ကို Python REPL တွင် တိုက်ရိုက် run လုပ်နိုင်သည်။ Function definition
တစ်ခုစီပြီးသွားသည့်အခါ blank line ထည့်ရန် လိုသည်။ ပိုလွယ်ကူအောင် `.py` file ထဲတွင်
အပြည့်အစုံ သိမ်းပြီး run လုပ်လည်း ရသည်။

```python
NUMERIC_CHECKS = (
    ("entity_coverage", ">=", 0.85),
    ("relationship_density", ">=", 1.50),
    ("duplicate_entity_rate", "<=", 0.05),
    ("avg_chunk_tokens", "<=", 512.0),
)

BOOLEAN_CHECKS = (
    "uniqueness_constraint",
    "fulltext_index",
    "community_summary",
)

def _numeric_pass(value, operator, threshold):
    if operator == ">=":
        return value >= threshold
    elif operator == "<=":
        return value <= threshold
    else:
        raise ValueError(f"Unsupported operator: {operator}")

def readiness_report(metrics):
    failed = []
    for name, operator, threshold in NUMERIC_CHECKS:
        if not _numeric_pass(metrics[name], operator, threshold):
            failed.append(name)
    for name in BOOLEAN_CHECKS:
        if not metrics[name]:
            failed.append(name)
    return {
        "verdict": "READY" if not failed else "NOT_READY",
        "failed": failed,
    }

READY_PROFILE = {
    "entity_coverage": 0.93,
    "relationship_density": 2.40,
    "duplicate_entity_rate": 0.02,
    "avg_chunk_tokens": 384.0,
    "uniqueness_constraint": True,
    "fulltext_index": True,
    "community_summary": True,
}

BLOCKED_PROFILE = {
    "entity_coverage": 0.71,
    "relationship_density": 1.10,
    "duplicate_entity_rate": 0.12,
    "avg_chunk_tokens": 640.0,
    "uniqueness_constraint": True,
    "fulltext_index": False,
    "community_summary": False,
}

print(readiness_report(READY_PROFILE))
print(readiness_report(BLOCKED_PROFILE))
```

Expected output —

```text
{'verdict': 'READY', 'failed': []}
{'verdict': 'NOT_READY', 'failed': ['entity_coverage', 'relationship_density', 'duplicate_entity_rate', 'avg_chunk_tokens', 'fulltext_index', 'community_summary']}
```

ဤ version တွင် `_numeric_pass()` ကို နည်းနည်းပိုမိုခိုင်မာအောင် ပြင်ထားသည်။ `">="` နှင့်
`"<="` ကို ရှင်းလင်းစွာ စစ်ဆေးပြီး တခြား operator ဖြစ်လာလျှင် `ValueError` ထုတ်ပေးတွင်
ဖြစ်သည်။ Readiness logic ၏ ရလဒ်သည် မူရင်း Exercise နှင့် အတူတူပင်။

နောက်ထပ် သတိပြုရန် — `metrics[name]` က မဖြစ်မနေ လိုအပ်သော key မရှိခဲ့လျှင် `KeyError`
ဖြစ်နိုင်သည်။ Production system တွင် ဤ function ကို အသုံးပြုမည်ဆိုလျှင် metrics
အားလုံး ပါဝင်မှုရှိမရှိ၊ values တွေက numeric သို့မဟုတ် Boolean အမျိုးအစားမှန်မမှန်ကိုပါ
စစ်ဆေးရန် သင့်တော်သည်။

```text
KeyError: 'relationship_density'
```

---

## 10. ကိုယ်တိုင်လေ့ကျင့်ကြည့်ပါ

**မေးခွန်း** — `failed = ["fulltext_index"]` ဖြစ်နေသည်ဆိုပါစို့။ ဤ expression က ဘာကို
ပြန်ပေးမလဲ။

```python
"READY" if not failed else "NOT_READY"
```

1. `READY`
2. `NOT_READY`
3. `True`
4. Empty list

<details>
<summary>အဖြေ ကြည့်ရန်</summary>

**အဖြေ — 2. `NOT_READY`**

အကြောင်းရင်း — `failed` သည် item တစ်ခုပါသော list ဖြစ်သဖြင့် truthy ဖြစ်သည်။
`not failed` သည် `False` ဖြစ်သည်။ Conditional expression
`A if condition else B` တွင် condition မှားပါက `B` ကို ပြန်ပေးသဖြင့် `"NOT_READY"`
ရရှိသည်။

`failed` အလွတ်ဖြစ်ပါက `not []` → `True` ဖြစ်ပြီး `"READY"` ရရှိမည်။ ဤအချက်က
`readiness_report()` ၏ `"verdict"` တန်ဖိုး ဆုံးဖြတ်ပုံနှင့် တူညီသည်။

</details>

---

## အဓိက မှတ်ထားရန်

ဤ Exercise တွင် readiness checker တည်ဆောက်ရန် Python concepts တွေကို
ပေါင်းစပ်အသုံးပြုခဲ့သည်။

- `NUMERIC_CHECKS` က metrics တွေ၏ thresholds တွေကို သိမ်းထားသည်။
- `BOOLEAN_CHECKS` က မဖြစ်မနေ အောင်မြင်ရမည့် configuration flags တွေကို
  သတ်မှတ်ထားသည်။
- `_numeric_pass()` က metric တန်ဖိုးတစ်ခု ခွင့်ပြုထားသော threshold အတွင်း ရှိမရှိ
  စစ်ဆေးသည်။
- `readiness_report()` က check မအောင်မြင်သည့်အရာတွေကို စုဆောင်းပြီး verdict
  ပြန်ပေးသည်။
- Conditional expression က `failed` list အလွတ်ဖြစ်မဖြစ်အပေါ် မူတည်ပြီး `READY`
  သို့မဟုတ် `NOT_READY` ကို ရွေးချယ်သည်။

ဤသို့ readiness checker ကို GraphRAG deployment မလုပ်ခင် validation အဆင့်တစ်ခုအဖြစ်
အသုံးပြုနိုင်သည်။ သို့သော် `READY` ရရှိခြင်းသည် သတ်မှတ်ထားသော checks တွေ
အောင်မြင်ကြောင်းသာ ဆိုလိုပြီး system တစ်ခုလုံး၏ accuracy၊ performance နှင့် reliability
အားလုံးကို အာမမခံပါ။
