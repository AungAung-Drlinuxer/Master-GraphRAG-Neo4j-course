# Walkthrough 06 — GraphRAG Readiness Check (Exercise 6)

> ဤဖိုင်သည် `solution.md` ၏ Exercise 6 ကို **Python အခြေခံမှ စ၍** အပိုင်းလိုက် ရှင်းပြသည့်
> walkthrough ဖြစ်သည်။ Format သည် `walkthroughs/01_pipeline_stage_ordering.md` မှ
> `05_triple_spo_parsing.md` အထိ နှင့် တူညီသည်။

---

ဒီ Exercise မှာ Python ကို အသုံးပြုပြီး GraphRAG system တစ်ခု တည်ဆောက်ဖို့
အဆင်သင့်ဖြစ်နေပြီလားဆိုတာကို Metrics နဲ့ Configuration Checks တွေအပေါ် မူတည်ပြီး
စစ်ဆေးခြင်း (Readiness Assessment) ကို လေ့လာပါမယ်။

အရင် Exercise 5 မှာ text ကနေ Subject, Predicate, Object (SPO) triples တွေကို
ထုတ်ယူခဲ့ပါတယ်။ ဒီ Exercise 6 မှာတော့ GraphRAG အတွက် အရေးကြီးတဲ့ entities၊
relationships၊ duplicate entities၊ chunk size နဲ့ indexing configuration တွေကို
စစ်ဆေးမှာ ဖြစ်ပါတယ်။

ဥပမာ Enterprise IT Help Chatbot တစ်ခုမှာ GraphRAG ကို အသုံးပြုမယ်ဆိုပါစို့။ Documents
တွေထဲက entities တွေကို လုံလောက်အောင် ထုတ်ယူထားသလား၊ relationships တွေ
လုံလောက်သလား၊ duplicate entities အလွန်များနေသလား၊ လိုအပ်တဲ့ indexes တွေ
တည်ဆောက်ထားသလားဆိုတာကို စစ်ဆေးဖို့ လိုအပ်ပါတယ်။

ဒီ Exercise မှာ အဓိကလေ့လာရမယ့် Python concepts တွေကတော့ —

- tuple နဲ့ configuration data
- `>=` နဲ့ `<=` comparison operators
- `if` statements နဲ့ `return`
- `for` loop
- `not` operator
- List အတွင်း results တွေ စုဆောင်းခြင်း
- Conditional expression
- Dictionary ထဲက metrics တွေကို ဖတ်ရှုခြင်း

---

## 1. GraphRAG Readiness Check ဆိုတာဘာလဲ။

GraphRAG (Graph Retrieval-Augmented Generation) က Knowledge Graph ထဲက entities နဲ့
relationships တွေကို အသုံးပြုပြီး information ရှာဖွေခြင်း၊ reasoning လုပ်ခြင်းနဲ့
answers ထုတ်ပေးခြင်းတွေကို ပံ့ပိုးပေးနိုင်ပါတယ်။ ဒါပေမဲ့ GraphRAG အတွက် data
quality နဲ့ infrastructure configuration တွေ အရေးကြီးပါတယ်။

```text
        GraphRAG Data & Configuration
   Entities, relationships, chunk size, indexes, summaries
                            |
                            v
                     Readiness Checks
         သတ်မှတ်ထားတဲ့ thresholds နဲ့ requirements တွေကို စစ်ဆေးခြင်း
                            |
              +-------------+-------------+
              |                           |
              v                           v
           READY                     NOT_READY
   Checks အားလုံး အောင်မြင်တယ်    Check တစ်ခု သို့မဟုတ်
                                  တစ်ခုထက်ပို၍ မအောင်မြင်ဘူး
```

ဒီ Exercise က **rule-based readiness checker** တစ်ခု ဖြစ်ပါတယ်။ သတ်မှတ်ထားတဲ့ metrics
တွေနဲ့ boolean configuration flags တွေကို စစ်ပြီး `READY` သို့မဟုတ် `NOT_READY` ကို
ပြန်ပေးပါတယ်။

သတိပြုရန် — ဒီ code ထဲက thresholds တွေဟာ သင်ခန်းစာအတွက် သတ်မှတ်ထားတဲ့ ဥပမာတန်ဖိုးတွေ
ဖြစ်ပါတယ်။ GraphRAG system အားလုံးအတွက် မဖြစ်မနေ လိုက်နာရမယ့် universal industry
standards တွေ မဟုတ်ပါဘူး။ Production system တစ်ခုမှာ အသုံးပြုမယ့် data၊ retrieval
quality နဲ့ workload အပေါ် မူတည်ပြီး သတ်မှတ်သင့်ပါတယ်။

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

`NUMERIC_CHECKS` က tuple တစ်ခု ဖြစ်ပါတယ်။ အတွင်းမှာ numeric checks လေးခု
ပါဝင်ပါတယ်။ Tuple တစ်ခုစီမှာ items သုံးခု ပါဝင်ပါတယ်။

```python
("entity_coverage", ">=", 0.85)
```

အဲဒီ items တွေရဲ့ အဓိပ္ပာယ်က —

- `"entity_coverage"` — စစ်ဆေးမယ့် metric ရဲ့ အမည်။
- `">="` — အသုံးပြုမယ့် comparison operator။
- `0.85` — သတ်မှတ်ထားတဲ့ threshold သို့မဟုတ် အနည်းဆုံးတန်ဖိုး။

ဒီ configuration ကို ဖတ်ပြီး Python က metric တန်ဖိုးတစ်ခုစီကို threshold နဲ့
နှိုင်းယှဉ်နိုင်ပါတယ်။

### 2.1 `entity_coverage`

```python
("entity_coverage", ">=", 0.85)
```

ဒီစည်းမျဉ်းမှာ `entity_coverage` က `0.85` ထက်ကြီးရမယ်၊ ဒါမှမဟုတ် `0.85` နဲ့
ညီရပါမယ်။ `0.85` က percentage အနေနဲ့ 85% ကို ကိုယ်စားပြုပါတယ်။

ဥပမာ —

```python
entity_coverage = 0.93

print(entity_coverage >= 0.85)
```

Output —

```text
True
```

ဆိုလိုတာက entity coverage 93% ဖြစ်လို့ သတ်မှတ်ထားတဲ့ 85% threshold ကို
ကျော်လွန်နေပါတယ်။

Entity coverage က ဒီ Exercise အတွက် သတ်မှတ်ထားတဲ့ metric ဖြစ်ပြီး၊ အမှန်တကယ်
production system မှာ ဘယ် entities တွေကို denominator အဖြစ် အသုံးပြုမလဲဆိုတာ
ရှင်းလင်းစွာ သတ်မှတ်ဖို့ လိုအပ်ပါတယ်။

### 2.2 `relationship_density`

```python
("relationship_density", ">=", 1.50)
```

ဒီ metric ရဲ့တန်ဖိုးက `1.50` ထက်ကြီးရမယ်၊ ဒါမှမဟုတ် ညီရပါမယ်။

ဒီ Exercise မှာ `relationship_density` ကို numeric metric တစ်ခုအဖြစ်သာ ယူဆထားပါတယ်။
တကယ့် GraphRAG implementation မှာ ဒီ metric ကို ဘယ်လိုတွက်ချက်ထားသလဲဆိုတာ
အရေးကြီးပါတယ်။ ဥပမာ node တစ်ခုစီအတွက် ပျမ်းမျှ relationships အရေအတွက်လား၊
ဒါမှမဟုတ် အခြား graph density metric လားဆိုတာ သတ်မှတ်ဖို့ လိုအပ်ပါတယ်။

```python
relationship_density = 2.40

print(relationship_density >= 1.50)
```

Output —

```text
True
```

ဒီတန်ဖိုးက သတ်မှတ်ထားတဲ့ threshold ကို အောင်မြင်ပါတယ်။

### 2.3 `duplicate_entity_rate`

```python
("duplicate_entity_rate", "<=", 0.05)
```

ဒီတစ်ခုက အရင်နှစ်ခုနဲ့ မတူတဲ့ comparison operator ကို သုံးပါတယ်။ `<=` က
"ထက်ငယ် သို့မဟုတ် ညီမျှ" လို့ အဓိပ္ပာယ်ရပါတယ်။ ဒါကြောင့် `duplicate_entity_rate` က
`0.05` သို့မဟုတ် 5% ထက် မများရပါဘူး။

ဥပမာ —

```python
duplicate_entity_rate = 0.02

print(duplicate_entity_rate <= 0.05)
```

Output —

```text
True
```

ဒီ metric က duplicate entity rate 2% ဖြစ်လို့ threshold 5% ကို အောင်မြင်ပါတယ်။

GraphRAG မှာ duplicate entities များလွန်းရင် entity တစ်ခုတည်းကို graph nodes
အများအပြားအဖြစ် ကိုယ်စားပြုမိနိုင်ပါတယ်။ ဥပမာ `Kubernetes Cluster A` နဲ့
`Cluster A` တို့က အတူတူ entity ဖြစ်နေပေမဲ့ မတူညီတဲ့ nodes အဖြစ် မှတ်တမ်းတင်မိရင်
graph relationships တွေ ပြန့်ကျဲသွားနိုင်ပါတယ်။

### 2.4 `avg_chunk_tokens`

```python
("avg_chunk_tokens", "<=", 512.0)
```

ဒီစည်းမျဉ်းက ပျမ်းမျှ chunk token count ဟာ `512` ထက် မကျော်ရဘူးလို့ သတ်မှတ်ထားပါတယ်။

```python
avg_chunk_tokens = 384.0

print(avg_chunk_tokens <= 512.0)
```

Output —

```text
True
```

ဒါကြောင့် check အောင်မြင်ပါတယ်။

Chunk တစ်ခုချင်းစီရဲ့ အရွယ်အစားဟာ retrieval quality၊ context completeness၊
embedding model နဲ့ LLM context window တို့အပေါ် သက်ရောက်နိုင်ပါတယ်။ ဒါပေမဲ့ `512` ဟာ
အမြဲတမ်း အကောင်းဆုံးတန်ဖိုး မဟုတ်ပါဘူး။ သုံးမယ့် embedding model နဲ့ document type
အပေါ် မူတည်ပြီး သတ်မှတ်သင့်ပါတယ်။

---

## 3. `BOOLEAN_CHECKS` — Configuration များကို စစ်ဆေးခြင်း

Code ရဲ့ နောက်ထပ်အပိုင်းက —

```python
BOOLEAN_CHECKS = (
    "uniqueness_constraint",
    "fulltext_index",
    "community_summary",
)
```

ဒီ tuple ထဲမှာ Boolean checks သုံးခု ပါဝင်ပါတယ်။ Numeric checks တွေမှာ `0.85`၊
`1.50`၊ `0.05` လို ကိန်းဂဏန်းတွေနဲ့ နှိုင်းယှဉ်ခဲ့ပါတယ်။ ဒီတစ်ခုမှာတော့ configuration
တစ်ခုစီ ရှိမရှိ၊ ဖွင့်ထားသလား၊ ပြီးစီးထားသလားဆိုတာကို `True` သို့မဟုတ် `False` နဲ့
စစ်ဆေးပါတယ်။

### 3.1 `uniqueness_constraint`

ဒီ check က Graph database မှာ entity တစ်ခုစီရဲ့ unique identity ကို ထိန်းသိမ်းပေးတဲ့
uniqueness constraint လိုအပ်ချက်ကို ကိုယ်စားပြုပါတယ်။

ဥပမာ Neo4j မှာ `Entity` node တစ်ခုစီရဲ့ `id` ကို unique ဖြစ်စေချင်ရင် အဲဒီ property
အပေါ် constraint သတ်မှတ်နိုင်ပါတယ်။

ဒီ Exercise မှာ —

```python
"uniqueness_constraint": True
```

ဆိုရင် လိုအပ်တဲ့ constraint ကို ပြင်ဆင်ထားပြီးဖြစ်တယ်လို့ သတ်မှတ်ပါတယ်။

```python
"uniqueness_constraint": False
```

ဆိုရင် ဒီ check မအောင်မြင်ပါဘူး။

### 3.2 `fulltext_index`

```python
"fulltext_index": True
```

ဒီ flag က လိုအပ်တဲ့ full-text index ကို ပြင်ဆင်ထားကြောင်း ကိုယ်စားပြုပါတယ်။

Full-text search က စကားလုံးတွေ၊ စာသားအပိုင်းတွေကို ရှာဖွေဖို့ အသုံးဝင်ပါတယ်။ Vector
Search က semantic similarity အပေါ် အခြေခံပြီး ရှာဖွေသလိုမဟုတ်ဘဲ full-text index က
သတ်မှတ်ထားတဲ့ text-search mechanism ကို ပံ့ပိုးပေးပါတယ်။

GraphRAG system တစ်ခုမှာ full-text retrieval နဲ့ graph-based retrieval ကို
ပေါင်းစပ်အသုံးပြုဖို့ ဒီလို index တစ်ခု လိုအပ်နိုင်ပါတယ်။ ဒါပေမဲ့ workload အားလုံးမှာ
full-text index မဖြစ်မနေလိုတယ်လို့ ဒီ code က သတ်မှတ်ထားခြင်း မဟုတ်ပါဘူး။ ဒီ Exercise
အတွက် readiness requirement အဖြစ် သတ်မှတ်ထားတာ ဖြစ်ပါတယ်။

### 3.3 `community_summary`

```python
"community_summary": True
```

ဒီ flag က GraphRAG community summaries တွေကို လိုအပ်တဲ့အတိုင်း ပြင်ဆင်ပြီးပြီလားဆိုတာကို
ကိုယ်စားပြုပါတယ်။

Community summary ဆိုတာ Knowledge Graph ထဲက ဆက်စပ်နေတဲ့ entities နဲ့ relationships
တွေကို အုပ်စုဖွဲ့ပြီး အဲဒီအုပ်စုအကြောင်း အကျဉ်းချုပ်ထားတဲ့ information ဖြစ်ပါတယ်။

ဥပမာ IT infrastructure graph တစ်ခုထဲမှာ Kubernetes clusters၊ applications၊
databases နဲ့ monitoring tools တွေကို ဆက်စပ်မှုအရ community အုပ်စုတစ်ခုအဖြစ်
ဖွဲ့ထားနိုင်ပါတယ်။ အဲဒီ community အကြောင်း အကျဉ်းချုပ်ထားခြင်းက system အနှံ့ဆက်စပ်တဲ့
မေးခွန်းတွေကို ဖြေဆိုရာမှာ အသုံးဝင်နိုင်ပါတယ်။

ဒီ Exercise မှာ `community_summary` က `False` ဖြစ်နေရင် readiness check မအောင်မြင်ဘူးလို့
သတ်မှတ်ပါတယ်။

---

## 4. `_numeric_pass()` function — Numeric Check ကို စစ်ဆေးခြင်း

အခု numeric metrics တွေကို စစ်ဆေးပေးတဲ့ function ကို ကြည့်ပါ။

```python
def _numeric_pass(value, operator, threshold):
    if operator == ">=":
        return value >= threshold
    return value <= threshold
```

ဒီ function က arguments သုံးခုကို လက်ခံပါတယ်။

- `value` — စစ်ဆေးမယ့် metric တန်ဖိုး။
- `operator` — အသုံးပြုမယ့် comparison operator။
- `threshold` — နှိုင်းယှဉ်ရမယ့် သတ်မှတ်တန်ဖိုး။

### 4.1 ပထမ `if` condition

```python
if operator == ">=":
    return value >= threshold
```

ဒီမှာ `operator` ရဲ့တန်ဖိုးက `">="` နဲ့ ညီမညီ စစ်ဆေးပါတယ်။

ဥပမာ —

```python
_numeric_pass(0.93, ">=", 0.85)
```

Function ထဲမှာ `0.93 >= 0.85` ကို စစ်ဆေးတာကြောင့် `True` ပြန်ပေးပါတယ်။

နောက်ဥပမာ —

```python
_numeric_pass(0.71, ">=", 0.85)
```

ဒီမှာ `0.71` က `0.85` ထက်ငယ်တဲ့အတွက် `False` ပြန်ပေးပါတယ်။

### 4.2 နောက်ဆုံး `return`

```python
return value <= threshold
```

ဒီ statement ကို ပထမ `if` condition မအောင်မြင်တဲ့အခါ လုပ်ဆောင်ပါတယ်။

ဥပမာ —

```python
_numeric_pass(0.02, "<=", 0.05)
```

ဒီအခါ `0.02 <= 0.05` ကို စစ်ဆေးပြီး `True` ပြန်ပေးပါတယ်။

တစ်ဖန် —

```python
_numeric_pass(0.12, "<=", 0.05)
```

ဆိုရင် `0.12` ဟာ `0.05` ထက်ကြီးတဲ့အတွက် `False` ပြန်ပေးပါတယ်။

### 4.3 ဒီ function အတွက် အရေးကြီးတဲ့ မှတ်ချက်

ဒီ function က လက်ရှိ `NUMERIC_CHECKS` ထဲမှာ သတ်မှတ်ထားတဲ့ operator နှစ်မျိုးဖြစ်တဲ့ `>=`
နဲ့ `<=` အတွက် အလုပ်လုပ်ပါတယ်။ ဒါပေမဲ့ operator က တခြားတန်ဖိုးတစ်ခု ဖြစ်နေခဲ့ရင်လည်း
code က `return value <= threshold` ကို အလိုအလျောက် လုပ်ဆောင်သွားပါမယ်။ ဒါက
မရည်ရွယ်ထားတဲ့ **bug** ဖြစ်နိုင်ပါတယ်။

ပိုမိုခိုင်မာအောင် ရေးမယ်ဆိုရင် —

```python
def _numeric_pass(value, operator, threshold):
    if operator == ">=":
        return value >= threshold
    elif operator == "<=":
        return value <= threshold
    else:
        raise ValueError(f"Unsupported operator: {operator}")
```

လို့ ရေးနိုင်ပါတယ်။ ဒီပုံစံမှာ မထောက်ပံ့ထားတဲ့ operator တစ်ခု ဝင်လာရင် မှားယွင်းတဲ့
comparison ကို တိတ်တဆိတ် လုပ်မယ့်အစား `ValueError` ကို ထုတ်ပေးပါလိမ့်မယ်။

```text
ValueError: Unsupported operator: !=
```

---

## 5. `readiness_report(metrics)` function

ဒီ function က Exercise 6 ရဲ့ အဓိက logic ဖြစ်ပါတယ်။

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

ဒီ function ကို အဆင့်လိုက် ရှင်းပြပါမယ်။

### 5.1 `failed = []`

```python
failed = []
```

ဒီမှာ empty list တစ်ခု ဖန်တီးထားပါတယ်။ မအောင်မြင်တဲ့ checks တွေရဲ့ အမည်တွေကို ဒီ list
ထဲမှာ စုဆောင်းသွားမှာပါ။

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

Check အားလုံး အောင်မြင်ရင် `failed` က empty list အတိုင်း ကျန်နေပါမယ်။

### 5.2 Numeric checks တွေကို Loop လုပ်ခြင်း

```python
for name, operator, threshold in NUMERIC_CHECKS:
    if not _numeric_pass(metrics[name], operator, threshold):
        failed.append(name)
```

ဒီမှာ `NUMERIC_CHECKS` tuple ထဲက check လေးခုကို တစ်ခုချင်းစီ ယူပါတယ်။ ဥပမာ —

```python
("entity_coverage", ">=", 0.85)
```

ဒီ tuple ကို unpack လုပ်လိုက်တဲ့အခါ —

```text
name      = "entity_coverage"
operator  = ">="
threshold = 0.85
```

ဖြစ်လာပါတယ်။ ပြီးရင် —

```python
metrics[name]
```

ကို အသုံးပြုပြီး `metrics` dictionary ထဲက လက်ရှိ metric တန်ဖိုးကို ရယူပါတယ်။

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

ဒီတန်ဖိုးကို `_numeric_pass()` function ထဲ ပေးပြီး threshold နဲ့ နှိုင်းယှဉ်ပါတယ်။

### `if not _numeric_pass(...)` ဆိုတာဘာလဲ။

```python
if not _numeric_pass(metrics[name], operator, threshold):
    failed.append(name)
```

`_numeric_pass()` က `True` ပြန်ပေးရင် check အောင်မြင်ပါတယ်။ အဲဒီ `True` ရဲ့ ရှေ့မှာ
`not` ထည့်ထားတဲ့အတွက် `False` ဖြစ်သွားပါတယ်။ ဒါကြောင့် `failed.append(name)` ကို
မလုပ်ပါဘူး။

တစ်ဖန် `_numeric_pass()` က `False` ပြန်ပေးရင် `not False` က `True` ဖြစ်ပါတယ်။
ဒါကြောင့် metric name ကို `failed` list ထဲ ထည့်ပါတယ်။

အဓိပ္ပာယ်က **check မအောင်မြင်တဲ့ metrics တွေကိုသာ** `failed` ထဲ ထည့်ခြင်း ဖြစ်ပါတယ်။

### 5.3 Boolean checks တွေကို Loop လုပ်ခြင်း

```python
for name in BOOLEAN_CHECKS:
    if not metrics[name]:
        failed.append(name)
```

ဒီအပိုင်းက `BOOLEAN_CHECKS` ထဲက configuration သုံးခုကို စစ်ဆေးပါတယ်။

ဥပမာ —

```python
metrics = {
    "uniqueness_constraint": True,
    "fulltext_index": False,
    "community_summary": False,
}
```

Loop က `name` တစ်ခုချင်းစီကို ရယူပါတယ်။ `if not metrics[name]:` မှာ တန်ဖိုးက `False`
ဖြစ်နေရင် `not False` က `True` ဖြစ်တဲ့အတွက် အဲဒီ configuration name ကို `failed`
list ထဲ ထည့်ပါတယ်။

ဒါကြောင့် အထက်က ဥပမာမှာ —

```python
[
    "fulltext_index",
    "community_summary",
]
```

ဆိုတဲ့ `failed` list ကို ရရှိပါမယ်။

### 5.4 `return` နဲ့ Verdict ပြန်ပေးခြင်း

```python
return {
    "verdict": "READY" if not failed else "NOT_READY",
    "failed": failed,
}
```

ဒီအပိုင်းမှာ dictionary တစ်ခုကို ပြန်ပေးထားပါတယ်။ Dictionary ထဲမှာ key နှစ်ခု
ပါဝင်ပါတယ်။

- `"verdict"` — Readiness result။
- `"failed"` — မအောင်မြင်တဲ့ checks တွေရဲ့ အမည်တွေ။

ဒီ expression က Python ရဲ့ **conditional expression** ဖြစ်ပါတယ်။

```python
"READY" if not failed else "NOT_READY"
```

အဓိပ္ပာယ်က —

- `failed` list အလွတ်ဖြစ်ရင် `"READY"`။
- `failed` list ထဲမှာ အနည်းဆုံး item တစ်ခုရှိရင် `"NOT_READY"`။

Python မှာ empty list က falsy ဖြစ်တဲ့အတွက် —

```python
not []
```

က `True` ပြန်ပေးပါတယ်။ ဥပမာ —

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

ဒီလို conditional expression သုံးတာက `if`/`else` block ကို သီးခြားရေးစရာမလိုဘဲ တန်ဖိုးတစ်ခုကို
အတိုချုံး ရွေးချယ်နိုင်တဲ့ နည်းလမ်းဖြစ်ပါတယ်။

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

ဒီ dictionary က readiness checks အားလုံးကို အောင်မြင်ဖို့ ရည်ရွယ်ထားတဲ့ sample metrics
တွေကို သိမ်းထားပါတယ်။ အခု check တစ်ခုချင်းစီကို တွက်ကြည့်ပါမယ်။

| Metric / Configuration | တန်ဖိုး | လိုအပ်ချက် | ရလဒ် |
| --- | --- | --- | --- |
| `entity_coverage` | 0.93 | `>= 0.85` | Pass |
| `relationship_density` | 2.40 | `>= 1.50` | Pass |
| `duplicate_entity_rate` | 0.02 | `<= 0.05` | Pass |
| `avg_chunk_tokens` | 384.0 | `<= 512.0` | Pass |
| `uniqueness_constraint` | `True` | `True` ဖြစ်ရမယ် | Pass |
| `fulltext_index` | `True` | `True` ဖြစ်ရမယ် | Pass |
| `community_summary` | `True` | `True` ဖြစ်ရမယ် | Pass |

Numeric checks လေးခုလုံး အောင်မြင်ပြီး Boolean checks သုံးခုလုံးလည်း `True` ဖြစ်ပါတယ်။
ဒါကြောင့် —

```python
print(readiness_report(READY_PROFILE))
```

ကို run လုပ်တဲ့အခါ အောက်ပါ output ကို ရရှိပါတယ်။

```text
{'verdict': 'READY', 'failed': []}
```

`failed` က empty list ဖြစ်နေတဲ့အတွက် check မအောင်မြင်တဲ့ metric မရှိပါဘူး။ ဒါကြောင့်
`verdict` က `"READY"` ဖြစ်ပါတယ်။

သို့သော် ဒီရလဒ်ဟာ ဒီ Exercise မှာ သတ်မှတ်ထားတဲ့ checks တွေကို အောင်မြင်တယ်လို့
ဆိုလိုတာသာ ဖြစ်ပါတယ်။ Production quality၊ retrieval accuracy၊ security၊ latency နဲ့
answer correctness အားလုံးကို အတည်ပြုပေးတာ မဟုတ်ပါဘူး။

---

## 7. `BLOCKED_PROFILE` — Checks အချို့ မအောင်မြင်သော Profile

အခု ဒုတိယ profile ကို ကြည့်ရအောင်။

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

ဒီ profile မှာ readiness requirements အချို့ မပြည့်မီပါဘူး။

### 7.1 Numeric checks

| Metric | တန်ဖိုး | လိုအပ်ချက် | ဘာကြောင့် မအောင်မြင်သလဲ |
| --- | --- | --- | --- |
| `entity_coverage` | 0.71 | `>= 0.85` | Coverage 71% ဖြစ်လို့ လိုအပ်တဲ့ 85% ထက်နည်းတယ် |
| `relationship_density` | 1.10 | `>= 1.50` | သတ်မှတ်ထားတဲ့ threshold ထက်နည်းတယ် |
| `duplicate_entity_rate` | 0.12 | `<= 0.05` | Duplicate rate 12% ဖြစ်လို့ 5% ထက်များတယ် |
| `avg_chunk_tokens` | 640.0 | `<= 512.0` | ပျမ်းမျှ token count က 512 ထက်များတယ် |

ဒီ metric လေးခုလုံးက check မအောင်မြင်တဲ့အတွက် `failed` list ထဲ ထည့်ပါမယ်။

### 7.2 Boolean checks

| Configuration | တန်ဖိုး | ရလဒ် |
| --- | --- | --- |
| `uniqueness_constraint` | `True` | Pass |
| `fulltext_index` | `False` | Fail |
| `community_summary` | `False` | Fail |

`uniqueness_constraint` က `True` ဖြစ်တဲ့အတွက် မအောင်မြင်တဲ့ list ထဲ မပါဝင်ပါဘူး။ ဒါပေမဲ့
`fulltext_index` နဲ့ `community_summary` နှစ်ခုစလုံး `False` ဖြစ်တဲ့အတွက် `failed`
list ထဲ ထည့်ပါမယ်။

ဒီ profile အတွက် စုစုပေါင်း failed checks ခြောက်ခု ရှိပါတယ်။

- `entity_coverage`
- `relationship_density`
- `duplicate_entity_rate`
- `avg_chunk_tokens`
- `fulltext_index`
- `community_summary`

ဒါကြောင့် —

```python
print(readiness_report(BLOCKED_PROFILE))
```

ရဲ့ output က —

```text
{'verdict': 'NOT_READY', 'failed': ['entity_coverage', 'relationship_density', 'duplicate_entity_rate', 'avg_chunk_tokens', 'fulltext_index', 'community_summary']}
```

ဖြစ်ပါတယ်။ `uniqueness_constraint` တစ်ခုတည်းက အောင်မြင်ပေမဲ့ ကျန်တဲ့ checks ခြောက်ခု
မအောင်မြင်တဲ့အတွက် `verdict` က `"NOT_READY"` ဖြစ်ပါတယ်။

---

## 8. Code တစ်ခုလုံး အလုပ်လုပ်ပုံ

ဒီ Exercise ကို အဆင့်လိုက် flow အနေနဲ့ ပြန်ကြည့်ရအောင်။

```text
Step 1 — Read Metrics
   READY_PROFILE သို့မဟုတ် BLOCKED_PROFILE ကို လက်ခံခြင်း
                |
                v
Step 2 — Numeric Checks
   Metrics ၄ ခုကို သတ်မှတ်ထားတဲ့ thresholds နဲ့ စစ်ဆေးခြင်း
                |
                v
Step 3 — Boolean Checks
   Configuration flags ၃ ခုကို စစ်ဆေးခြင်း
                |
                v
Step 4 — Collect Failed Checks
   မအောင်မြင်တဲ့ check names တွေကို failed list ထဲ ထည့်ခြင်း
                |
      +---------+---------+
      |                   |
      v                   v
   READY              NOT_READY
 failed == []       Failed checks ရှိတယ်
```

---

## 9. ပြန်လည်လေ့ကျင့်ရန် Runnable Code

အောက်ပါ code ကို Python REPL မှာ တိုက်ရိုက် run လုပ်နိုင်ပါတယ်။ Function definition
တစ်ခုစီပြီးသွားတဲ့အခါ blank line ထည့်ဖို့ လိုပါတယ်။ ပိုလွယ်ကူအောင် `.py` file ထဲမှာ
အပြည့်အစုံ သိမ်းပြီး run လုပ်လည်း ရပါတယ်။

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

ဒီ version မှာ `_numeric_pass()` ကို နည်းနည်းပိုမိုခိုင်မာအောင် ပြင်ထားပါတယ်။ `">="` နဲ့
`"<="` ကို ရှင်းလင်းစွာ စစ်ဆေးပြီး တခြား operator ဖြစ်လာရင် `ValueError` ထုတ်ပေးမှာ
ဖြစ်ပါတယ်။ Readiness logic ရဲ့ ရလဒ်ကတော့ မူရင်း Exercise နဲ့ အတူတူပါပဲ။

နောက်ထပ် သတိပြုရန် — `metrics[name]` က မဖြစ်မနေ လိုအပ်တဲ့ key မရှိခဲ့ရင် `KeyError`
ဖြစ်နိုင်ပါတယ်။ Production system မှာ ဒီ function ကို အသုံးပြုမယ်ဆိုရင် metrics
အားလုံး ပါဝင်မှုရှိမရှိ၊ values တွေက numeric သို့မဟုတ် Boolean အမျိုးအစားမှန်မမှန်ကိုပါ
စစ်ဆေးဖို့ သင့်တော်ပါတယ်။

```text
KeyError: 'relationship_density'
```

---

## 10. ကိုယ်တိုင်လေ့ကျင့်ကြည့်ပါ

**မေးခွန်း** — `failed = ["fulltext_index"]` ဖြစ်နေတယ်ဆိုပါစို့။ ဒီ expression က ဘာကို
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
`readiness_report()` ရဲ့ `"verdict"` တန်ဖိုး ဆုံးဖြတ်ပုံနှင့် တူညီသည်။

</details>

---

## အဓိက မှတ်ထားရန်

ဒီ Exercise မှာ readiness checker တည်ဆောက်ဖို့ Python concepts တွေကို
ပေါင်းစပ်အသုံးပြုခဲ့ပါတယ်။

- `NUMERIC_CHECKS` က metrics တွေရဲ့ thresholds တွေကို သိမ်းထားပါတယ်။
- `BOOLEAN_CHECKS` က မဖြစ်မနေ အောင်မြင်ရမယ့် configuration flags တွေကို
  သတ်မှတ်ထားပါတယ်။
- `_numeric_pass()` က metric တန်ဖိုးတစ်ခု ခွင့်ပြုထားတဲ့ threshold အတွင်း ရှိမရှိ
  စစ်ဆေးပါတယ်။
- `readiness_report()` က check မအောင်မြင်တဲ့အရာတွေကို စုဆောင်းပြီး verdict
  ပြန်ပေးပါတယ်။
- Conditional expression က `failed` list အလွတ်ဖြစ်မဖြစ်အပေါ် မူတည်ပြီး `READY`
  သို့မဟုတ် `NOT_READY` ကို ရွေးချယ်ပါတယ်။

ဒီလို readiness checker ကို GraphRAG deployment မလုပ်ခင် validation အဆင့်တစ်ခုအဖြစ်
အသုံးပြုနိုင်ပါတယ်။ သို့သော် `READY` ရရှိခြင်းဟာ သတ်မှတ်ထားတဲ့ checks တွေ
အောင်မြင်ကြောင်းသာ ဆိုလိုပြီး system တစ်ခုလုံးရဲ့ accuracy၊ performance နဲ့ reliability
အားလုံးကို အာမမခံပါဘူး။
