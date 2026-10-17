# Walkthrough 04 — RAG Failure Mode Classification (Exercise 4)

> ဤဖိုင်သည် `solution.md` ၏ Exercise 4 ကို **Python အခြေခံမှ စ၍** အပိုင်းလိုက် ရှင်းပြသည့်
> walkthrough ဖြစ်သည်။ Format သည် `walkthroughs/01_pipeline_stage_ordering.md` မှ
> `03_retrieval_modality_selection.md` အထိ နှင့် တူညီသည်။

---

ဒီ Exercise မှာ Python ကို အသုံးပြုပြီး RAG (Retrieval-Augmented Generation) system တစ်ခုမှာ
ဖြစ်ပေါ်နိုင်တဲ့ failure အမျိုးအစားတွေကို သတ်မှတ်ထားတဲ့ rules တွေအပေါ် မူတည်ပြီး
အလိုအလျောက် ခွဲခြားသတ်မှတ်ခြင်း (Failure Classification) ကို လေ့လာပါမယ်။

အရင် Exercise 1 မှာ Pipeline stages တွေကို dependency အလိုက် စီခဲ့ပါတယ်။ Exercise 2 မှာ
Cosine Similarity ကို အသုံးပြုပြီး chunks တွေကို ranking လုပ်ခဲ့ပါတယ်။ Exercise 3 မှာ
Query features တွေအပေါ် မူတည်ပြီး retrieval modality ကို ရွေးချယ်ခဲ့ပါတယ်။

ဒီ Exercise 4 မှာတော့ RAG system က မေးခွန်းတစ်ခုကို မှန်ကန်စွာ မဖြေနိုင်တဲ့အခါ ဘယ်လို
failure ဖြစ်နိုင်သလဲဆိုတာကို Python rules တွေနဲ့ ခွဲခြားသတ်မှတ်မှာ ဖြစ်ပါတယ်။

ဥပမာ IT Help Chatbot မှာ user က Kubernetes cluster ရဲ့ configuration အကြောင်း မေးတဲ့အခါ
အဖြေမှားသွားနိုင်တဲ့ အကြောင်းရင်းတွေက အမျိုးမျိုးရှိနိုင်ပါတယ်။

- လိုအပ်တဲ့ information ကို knowledge index ထဲ မထည့်ထားခြင်း။
- Documents အများအပြားထဲက အချက်အလက်တွေကို စုစည်းပြီး အကျဉ်းချုပ်ဖို့ မတတ်နိုင်ခြင်း။
- Entities တွေကြား relationships အများအပြားကို လိုက်ရှာဖို့ လိုအပ်ခြင်း။
- သက်ဆိုင်ရာ facts တွေကို chunks ခွဲလိုက်တဲ့အတွက် တစ်စုတစ်စည်းတည်း ပြန်မရရှိခြင်း။

ဒီ Exercise မှာ အဓိကလေ့လာရမယ့် Python concepts တွေကတော့ tuple၊ `lambda`၊ `not`၊
`for` loop၊ `if`၊ `return`၊ dictionary comprehension၊ `Counter` နဲ့ rule priority တို့
ဖြစ်ပါတယ်။

---

## 1. RAG Failure Mode ဆိုတာဘာလဲ။

Failure Mode ဆိုတာ system တစ်ခု အလုပ်မလုပ်နိုင်ခြင်း သို့မဟုတ် မျှော်လင့်ထားတဲ့ရလဒ်ကို
မရရှိခြင်းရဲ့ ပုံစံ သို့မဟုတ် အကြောင်းရင်းအမျိုးအစားကို ဆိုလိုပါတယ်။

```text
                       User Query
        (မေးခွန်းတစ်ခုကို ဖြေဆိုရန် လိုအပ်ချက်များ)
                            |
                            v
                      RAG Pipeline
            Ingestion -> Chunking -> Retrieval -> Generation
                            |
                            v
                    Failure Classifier
              (features တွေကို rules တစ်ခုချင်းစီနဲ့ စစ်ဆေးခြင်း)
                            |
          +-----------------+-----------------+
          |                 |                 |
          v                 v                 v
   ingestion_gap    multi_hop_failure   chunk_isolation
                            |
                            v
              global_summarization_failure
```

ဒီ diagram က concept ကို ရှင်းပြဖို့ ဖော်ပြထားတာ ဖြစ်ပါတယ်။ အောက်က Python code ကတော့ input
features တွေပေါ်မူတည်ပြီး label တစ်ခုကို ပြန်ပေးတဲ့ rule-based classifier ဖြစ်ပါတယ်။
အမှန်တကယ် root cause ကို သေချာအတည်ပြုဖို့ production logs၊ retrieval results နဲ့ knowledge
ingestion status တို့ကို ထပ်မံစစ်ဆေးဖို့ လိုအပ်နိုင်ပါတယ်။

---

## 2. `FAILURE_RULES` — Failure Classification Rules

အရင်ဆုံး code ရဲ့ ပထမအပိုင်းကို ကြည့်ပါ။

```python
FAILURE_RULES = (
    ("ingestion_gap", lambda f: not f["required_entity_in_index"]),
    ("global_summarization_failure", lambda f: f["needs_corpus_wide_aggregate"]),
    ("multi_hop_failure", lambda f: f["hop_count"] >= 2),
    ("chunk_isolation", lambda f: f["facts_split_across_chunks"]),
)
```

ဒီမှာ `FAILURE_RULES` က tuple တစ်ခုဖြစ်ပါတယ်။ Tuple ထဲမှာ rule လေးခု ပါဝင်ပြီး rule
တစ်ခုစီက tuple အတွင်းမှာ item နှစ်ခုစီ ပါပါတယ်။

ပထမ item က failure label ဖြစ်ပြီး ဒုတိယ item က condition တစ်ခုကို စစ်ဆေးပေးတဲ့
lambda function ဖြစ်ပါတယ်။

ဥပမာ —

```python
("ingestion_gap", lambda f: not f["required_entity_in_index"])
```

ဒီမှာ အစိတ်အပိုင်း နှစ်ခု ရှိပါတယ် —

- `"ingestion_gap"` — Failure အမျိုးအစားရဲ့ label။
- `lambda f: not f["required_entity_in_index"]` — Input features တွေကို စစ်ဆေးမယ့် function။

Python က `FAILURE_RULES` ကို စီထားတဲ့ အစီအစဉ်အတိုင်း နောက်ပိုင်းမှာ စစ်ဆေးသွားပါမယ်။
ဒီအစီအစဉ်က အလွန်အရေးကြီးပါတယ်။

---

## 3. `lambda` function ဆိုတာဘာလဲ။

ဒီ Exercise ရဲ့ အရေးကြီးဆုံး Python concepts တစ်ခုက `lambda` ဖြစ်ပါတယ်။

ပုံမှန်အားဖြင့် function တစ်ခုကို `def` နဲ့ ဖန်တီးနိုင်ပါတယ်။

```python
def is_multi_hop(features):
    return features["hop_count"] >= 2
```

ဒီ function က `features` dictionary ထဲက `hop_count` ကို စစ်ဆေးပါတယ်။ တန်ဖိုးက `2` သို့မဟုတ်
အထက်ဖြစ်ရင် `True` ပြန်ပေးပြီး၊ မဟုတ်ရင် `False` ပြန်ပေးပါတယ်။

အလားတူ logic ကို `lambda` နဲ့လည်း ရေးနိုင်ပါတယ်။

```python
is_multi_hop = lambda f: f["hop_count"] >= 2
```

ဒီမှာ —

- `lambda` — အမည်သီးခြားမပေးဘဲ function အသေးတစ်ခု ဖန်တီးတာ။
- `f` — Function ထဲကို ဝင်လာမယ့် argument။
- `f["hop_count"] >= 2` — စစ်ဆေးမယ့် expression။

ဥပမာ —

```python
is_multi_hop = lambda f: f["hop_count"] >= 2

features = {"hop_count": 3}

print(is_multi_hop(features))
```

Output —

```text
True
```

ဒီ Exercise မှာတော့ lambda function တွေကို variable တစ်ခုချင်းစီမှာ သီးခြားသိမ်းမထားဘဲ
`FAILURE_RULES` tuple ထဲမှာ တိုက်ရိုက်ထည့်ထားပါတယ်။ ဒါကြောင့် rule တစ်ခုစီမှာ label နဲ့
စစ်ဆေးမယ့် function ကို အတူတကွ သိမ်းထားနိုင်ပါတယ်။

---

## 4. Rule တစ်ခုချင်းစီကို နားလည်ခြင်း

### Rule 1 — `ingestion_gap`

```python
("ingestion_gap", lambda f: not f["required_entity_in_index"])
```

ဒီ rule က လိုအပ်တဲ့ entity ဟာ index ထဲမှာ ရှိမရှိကို စစ်ဆေးပါတယ်။

Dictionary ထဲက feature က —

```python
"required_entity_in_index": True
```

ဆိုရင် လိုအပ်တဲ့ entity ဟာ index ထဲမှာ ရှိတယ်လို့ ဖော်ပြပါတယ်။ အဲဒီအခါ —

```python
not True
```

ရဲ့ result က `False` ဖြစ်ပါတယ်။ ဒါကြောင့် `ingestion_gap` rule မကိုက်ညီပါဘူး။

ဒါပေမဲ့ —

```python
"required_entity_in_index": False
```

ဆိုရင် —

```python
not False
```

ရဲ့ result က `True` ဖြစ်ပါတယ်။ ဒါကြောင့် `ingestion_gap` ကို ရွေးချယ်နိုင်ပါတယ်။

Python ရဲ့ `not` operator က Boolean value ကို ပြောင်းပြန်လှန်ပေးတာပါ။

| Original value | `not` ဖြင့် ပြောင်းလဲပြီး |
| --- | --- |
| `True` | `False` |
| `False` | `True` |

RAG နဲ့ ဆက်စပ်ကြည့်ပါ။ User က မေးထားတဲ့ entity၊ ဥပမာ `sg-rag-prd-m1` cluster အကြောင်းကို
သိရှိဖို့ လိုအပ်ပေမဲ့ အဲဒီ entity ဆိုင်ရာ information ကို indexing လုပ်ထားတဲ့ knowledge base
ထဲ မတွေ့ဘူးဆိုရင် ingestion သို့မဟုတ် indexing ပြဿနာ ဖြစ်နိုင်ပါတယ်။

သို့သော် index ထဲမှာ မတွေ့ရခြင်းတစ်ခုတည်းနဲ့ ingestion ပျက်ကွက်တယ်လို့ အတည်မပြုနိုင်ပါဘူး။
Metadata filters၊ permissions၊ entity extraction နဲ့ index lookup တွေကိုလည်း စစ်ဆေးဖို့
လိုအပ်နိုင်ပါတယ်။

### Rule 2 — `global_summarization_failure`

```python
("global_summarization_failure", lambda f: f["needs_corpus_wide_aggregate"])
```

ဒီ rule က corpus တစ်ခုလုံး ဒါမှမဟုတ် knowledge base ရဲ့ အပိုင်းအခြားကြီးတစ်ခုကို
ပေါင်းစပ်စဉ်းစားဖို့ လိုအပ်ကြောင်း သတ်မှတ်ထားသလား စစ်ဆေးပါတယ်။

ဥပမာ —

```python
features = {
    "needs_corpus_wide_aggregate": True
}
```

ဒီ condition က `True` ဖြစ်တဲ့အတွက် rule ကိုက်ညီပါတယ်။

ဒီနေရာမှာ `not` မပါပါဘူး။ ဒါကြောင့် feature က `True` ဖြစ်နေရင် တိုက်ရိုက်ကိုက်ညီပြီး၊
`False` ဖြစ်နေရင် မကိုက်ညီပါဘူး။

RAG ဥပမာ — "Knowledge base ထဲမှာ 2026 ခုနှစ်အတွင်း အဖြစ်အများဆုံးဖြစ်တဲ့ infrastructure
incidents တွေနဲ့ common causes တွေကို အကျဉ်းချုပ်ပေးပါ" ဆိုတဲ့ မေးခွန်းဟာ document
တစ်ခုတည်းကို ရှာဖွေတာထက် information အများအပြားကို စုစည်းဖို့ လိုအပ်နိုင်ပါတယ်။

ဒါပေမဲ့ ဒီ exercise မှာ `needs_corpus_wide_aggregate` က `True` ဖြစ်တာနဲ့
`global_summarization_failure` လို့ သတ်မှတ်ထားပါတယ်။ တကယ့် system မှာတော့
အကျဉ်းချုပ်ဖို့ လိုအပ်ခြင်းဟာ အလိုအလျောက် failure ဖြစ်နေတယ်လို့ မဆိုလိုပါဘူး။ မေးခွန်းကို
မှန်ကန်စွာ မဖြေနိုင်ခဲ့ကြောင်းနဲ့ global summarization လုပ်ဆောင်မှု မအောင်မြင်ခဲ့ကြောင်းကို
သီးခြားသက်သေပြဖို့ လိုပါတယ်။

### Rule 3 — `multi_hop_failure`

```python
("multi_hop_failure", lambda f: f["hop_count"] >= 2)
```

ဒီ rule က relationship hops နှစ်ခုနဲ့အထက်ကို လိုက်ရှာဖို့ လိုအပ်တဲ့ Query ကို စစ်ဆေးပါတယ်။

ဥပမာ —

```python
features = {"hop_count": 3}

print(features["hop_count"] >= 2)
```

Output —

```text
True
```

`>=` က "ထက်ကြီး သို့မဟုတ် ညီမျှ" လို့ ဆိုလိုတာဖြစ်တဲ့အတွက် `2`၊ `3`၊ `4` စတဲ့
တန်ဖိုးတွေအားလုံးမှာ `True` ဖြစ်ပါတယ်။

IT infrastructure ဥပမာနဲ့ ကြည့်ရအောင်။

```text
Application A → Kubernetes Cluster B → Database C
```

User က "Application A က ဘယ် Database ကို ချိတ်ဆက်အသုံးပြုနေလဲ" လို့ မေးတဲ့အခါ
relationship အများအပြားကို ဖြတ်သန်းရှာဖွေဖို့ လိုအပ်နိုင်ပါတယ်။

Graph သို့မဟုတ် multi-hop retrieval လိုအပ်တဲ့ Query ကို မမှန်ကန်စွာ ဖြေရှင်းခဲ့တယ်လို့
သတ်မှတ်ရင် ဒီ rule ကို အသုံးပြုနိုင်ပါတယ်။

ဒီ exercise ကတော့ `hop_count >= 2` ဖြစ်ရုံနဲ့ `multi_hop_failure` ကို ပြန်ပေးပါတယ်။
အမှန်တကယ် multi-hop retrieval မအောင်မြင်ခဲ့ကြောင်းကိုတော့ သီးခြားစစ်ဆေးရမှာ ဖြစ်ပါတယ်။

### Rule 4 — `chunk_isolation`

```python
("chunk_isolation", lambda f: f["facts_split_across_chunks"])
```

ဒီ rule က အဖြေအတွက် လိုအပ်တဲ့ facts တွေဟာ document chunks အများအပြားထဲမှာ ပြန့်ကျဲနေသလား
စစ်ဆေးပါတယ်။

ဥပမာ knowledge base မှာ —

```text
Chunk A
  Application A runs on Kubernetes Cluster B.

Chunk B
  Kubernetes Cluster B connects to Database C.
```

User က "Application A က ဘယ် database ကို အသုံးပြုသလဲ" လို့ မေးတဲ့အခါ မှန်ကန်တဲ့ အဖြေထုတ်ဖို့
Chunk A နဲ့ Chunk B နှစ်ခုလုံးက information တွေ လိုအပ်ပါတယ်။

Retrieval က Chunk A တစ်ခုတည်းကိုသာ ပြန်ပေးခဲ့ရင် လိုအပ်တဲ့ relationship chain ကို
ပြည့်စုံစွာ မရနိုင်ပါဘူး။

ဒီလို facts တွေ သီးခြား chunks တွေအဖြစ် ခွဲထွက်နေမှုနဲ့ retrieval ပြဿနာကို ရိုးရှင်းစွာ
ကိုယ်စားပြုဖို့ —

```python
"facts_split_across_chunks": True
```

လို့ သတ်မှတ်ထားပါတယ်။

ဒါက chunking အမြဲမှားနေတယ်လို့ ဆိုလိုတာ မဟုတ်ပါဘူး။ Chunk တွေကို သင့်တော်စွာ
ခွဲထားပေမဲ့ retrieval အချိန်မှာ လိုအပ်တဲ့ chunks တွေ အားလုံးကို ပြန်မရတာလည်း
ဖြစ်နိုင်ပါတယ်။

---

## 5. `classify_failure(features)` function

Rules တွေကို သတ်မှတ်ပြီးတဲ့နောက် failure အမျိုးအစားကို ရွေးချယ်ပေးမယ့် function ကို
ဖန်တီးထားပါတယ်။

```python
def classify_failure(features):
    for label, rule in FAILURE_RULES:
        if rule(features):
            return label
    return "no_failure"
```

ဒီ function က `features` dictionary ကို input အဖြစ် လက်ခံပြီး failure label တစ်ခုကို
ပြန်ပေးပါတယ်။ ဒီ function အတွင်းမှာ အရေးကြီးတဲ့ logic သုံးခု ရှိပါတယ်။

- `for` loop နဲ့ rules တွေကို အစဉ်လိုက် စစ်ဆေးခြင်း။
- `if rule(features)` နဲ့ လက်ရှိ rule ကို စမ်းသပ်ခြင်း။
- `return label` နဲ့ ပထမဆုံးကိုက်ညီတဲ့ rule ရဲ့ label ကို ပြန်ပေးခြင်း။

### Step 5.1 — `for label, rule in FAILURE_RULES`

```python
for label, rule in FAILURE_RULES:
```

`FAILURE_RULES` ထဲမှာ tuple လေးခု ရှိပါတယ်။ Tuple တစ်ခုချင်းစီမှာ item နှစ်ခုစီ ပါဝင်ပါတယ်။
ဥပမာ —

```python
("ingestion_gap", lambda f: not f["required_entity_in_index"])
```

ဒီ tuple ကို loop က ရယူတဲ့အခါ —

- `label` ထဲကို `"ingestion_gap"` ဝင်လာမယ်။
- `rule` ထဲကို `lambda` function ဝင်လာမယ်။

ဒီလို tuple ထဲက item တွေကို variable တစ်ခုချင်းစီ ခွဲထည့်ခြင်းဟာ **tuple unpacking**
ဖြစ်ပါတယ်။

### Step 5.2 — `if rule(features)`

```python
if rule(features):
```

ဒီ code က `rule` variable ထဲမှာ သိမ်းထားတဲ့ function ကို `features` argument ပေးပြီး
ခေါ်တာပါ။

ဥပမာ —

```python
rule = lambda f: f["hop_count"] >= 2

features = {"hop_count": 3}

print(rule(features))
```

Output —

```text
True
```

အဲဒီလိုပဲ `classify_failure()` က rule တစ်ခုချင်းစီကို စမ်းသပ်ပြီး result က `True`
ဖြစ်မဖြစ် စစ်ဆေးပါတယ်။

### Step 5.3 — `return label`

```python
if rule(features):
    return label
```

လက်ရှိ rule က `True` ပြန်ပေးရင် သက်ဆိုင်တဲ့ label ကို ပြန်ပေးပြီး function ကို
ရပ်တန့်ပါတယ်။

ဥပမာ —

```python
features = {
    "required_entity_in_index": False,
    "needs_corpus_wide_aggregate": False,
    "hop_count": 0,
    "facts_split_across_chunks": False,
}
```

ပထမ rule က —

```python
lambda f: not f["required_entity_in_index"]
```

ဖြစ်ပါတယ်။ `required_entity_in_index` က `False` ဖြစ်တဲ့အတွက် `not False` ရဲ့ result က
`True` ဖြစ်ပါတယ်။ ဒါကြောင့် function က —

```python
return "ingestion_gap"
```

ကို ပြန်ပေးပြီး နောက်ထပ် rules တွေကို ဆက်မစစ်တော့ပါဘူး။

### Step 5.4 — `return "no_failure"`

```python
return "no_failure"
```

ဒီလို `return` က `for` loop အပြင်ဘက်မှာ ရှိနေပါတယ်။ အဓိပ္ပာယ်က rules လေးခုစလုံးကို
စစ်ဆေးပြီး တစ်ခုမှ `True` မဖြစ်ခဲ့ရင် `"no_failure"` ကို default result အနေနဲ့
ပြန်ပေးမှာ ဖြစ်ပါတယ်။

ဒီနေရာမှာ `"no_failure"` ဆိုတာ ဒီ rule set အရ သတ်မှတ်ထားတဲ့ failure rules တွေကို
မတွေ့ဘူး လို့ ဆိုလိုပါတယ်။ RAG system တစ်ခုလုံးမှာ failure လုံးဝမရှိဘူးလို့
အတည်ပြုတာ မဟုတ်ပါဘူး။

---

## 6. Rule Priority — ဘယ် Rule ကို အရင်ရွေးမလဲ။

ဒီ code မှာ သတိထားရမယ့် အရေးကြီးဆုံးအချက်တစ်ခုက rule တွေရဲ့ အစီအစဉ် ဖြစ်ပါတယ်။

ဥပမာ —

```python
features = {
    "required_entity_in_index": True,
    "needs_corpus_wide_aggregate": False,
    "hop_count": 2,
    "facts_split_across_chunks": True,
}
```

ဒီ feature တွေမှာ —

- `ingestion_gap` condition က `False` ဖြစ်တယ်။
- `global_summarization_failure` condition က `False` ဖြစ်တယ်။
- `multi_hop_failure` condition က `True` ဖြစ်တယ်။
- `chunk_isolation` condition ကလည်း `True` ဖြစ်တယ်။

ဒါဆို failure နှစ်မျိုးနဲ့ ကိုက်ညီနေပါတယ်။ ဒါပေမဲ့ function က ပထမဆုံး ကိုက်ညီတဲ့ rule
ဖြစ်တဲ့ `multi_hop_failure` ကိုသာ ပြန်ပေးပါမယ်။

ဘာကြောင့်လဲဆိုတော့ —

```python
if rule(features):
    return label
```

ဒီနေရာမှာ `return` ရောက်တာနဲ့ function ရပ်သွားလို့ပါ။ ဒီလို logic ကို **first-match rule
priority** လို့ မှတ်သားနိုင်ပါတယ်။

ဒီ priority က လုပ်ဆောင်ပုံအရ မှန်ကန်ပေမဲ့ failure အမျိုးအစားအားလုံးကို သိချင်တဲ့
diagnostic system တစ်ခုအတွက်တော့ ကန့်သတ်ချက် ရှိပါတယ်။ အဲဒီလိုအပ်ချက်ရှိရင် ပထမဆုံး
ကိုက်ညီတဲ့ label တစ်ခုတည်းကို ပြန်မပေးဘဲ ကိုက်ညီတဲ့ rules အားလုံးကို စုဆောင်းပေးဖို့
ပြောင်းလဲနိုင်ပါတယ်။

---

## 7. `FAILURE_SCENARIOS` — စမ်းသပ်မယ့် Scenario များ

```python
FAILURE_SCENARIOS = [
    ("S1", {
        "required_entity_in_index": True,
        "needs_corpus_wide_aggregate": False,
        "hop_count": 0,
        "facts_split_across_chunks": False
    }),
    ("S2", {
        "required_entity_in_index": False,
        "needs_corpus_wide_aggregate": False,
        "hop_count": 0,
        "facts_split_across_chunks": False
    }),
    ("S3", {
        "required_entity_in_index": True,
        "needs_corpus_wide_aggregate": False,
        "hop_count": 2,
        "facts_split_across_chunks": True
    }),
    ("S4", {
        "required_entity_in_index": True,
        "needs_corpus_wide_aggregate": True,
        "hop_count": 0,
        "facts_split_across_chunks": False
    }),
    ("S5", {
        "required_entity_in_index": True,
        "needs_corpus_wide_aggregate": False,
        "hop_count": 1,
        "facts_split_across_chunks": True
    }),
]
```

`FAILURE_SCENARIOS` ဟာ scenario ငါးခုပါဝင်တဲ့ list တစ်ခု ဖြစ်ပါတယ်။ Scenario တစ်ခုစီမှာ —

- `"S1"`, `"S2"` စတဲ့ scenario ID။
- Failure classifier ကို စမ်းသပ်ပေးမယ့် features dictionary။

တို့ ပါဝင်ပါတယ်။ အခု scenario တစ်ခုချင်းစီက ဘာကြောင့် ဒီ label ကို ရရှိသလဲဆိုတာ
ကြည့်ရအောင်။

---

## 8. Scenario တစ်ခုချင်းစီကို စစ်ဆေးခြင်း

| Scenario | အရေးကြီးတဲ့ feature | ရွေးချယ်မယ့် label | အကြောင်းရင်း |
| --- | --- | --- | --- |
| S1 | Failure conditions အားလုံး `False` | `no_failure` | ဘယ် rule မှ မကိုက်ညီဘူး |
| S2 | `required_entity_in_index = False` | `ingestion_gap` | ပထမ rule က `True` ဖြစ်တယ် |
| S3 | `hop_count = 2`, `facts_split_across_chunks = True` | `multi_hop_failure` | Rule 3 က အရင်ကိုက်ညီတယ် |
| S4 | `needs_corpus_wide_aggregate = True` | `global_summarization_failure` | Rule 2 က ကိုက်ညီတယ် |
| S5 | `facts_split_across_chunks = True` | `chunk_isolation` | နောက်ဆုံး rule ကိုက်ညီတယ် |

အထူးသဖြင့် S3 က စိတ်ဝင်စားဖို့ကောင်းပါတယ်။ `multi_hop_failure` နဲ့ `chunk_isolation`
နှစ်ခုစလုံးကိုက်ညီပေမဲ့ `FAILURE_RULES` ထဲမှာ `multi_hop_failure` က အရင်ရှိတဲ့အတွက်
အဲဒီ label ကိုပဲ ရွေးချယ်ပါတယ်။

### S1 — `no_failure`

```python
("S1", {
    "required_entity_in_index": True,
    "needs_corpus_wide_aggregate": False,
    "hop_count": 0,
    "facts_split_across_chunks": False
})
```

ပထမ rule မှာ `not True` က `False` ဖြစ်ပါတယ်။ ကျန်တဲ့ rule တွေလည်း `False` ဖြစ်တဲ့အတွက်
default result ဖြစ်တဲ့ `no_failure` ကို ပြန်ပေးပါတယ်။

### S2 — `ingestion_gap`

```python
("S2", {
    "required_entity_in_index": False,
    "needs_corpus_wide_aggregate": False,
    "hop_count": 0,
    "facts_split_across_chunks": False
})
```

ပထမ rule မှာ `not False` က `True` ဖြစ်တာကြောင့် `ingestion_gap` ကို ပြန်ပေးပါတယ်။

### S3 — `multi_hop_failure`

```python
("S3", {
    "required_entity_in_index": True,
    "needs_corpus_wide_aggregate": False,
    "hop_count": 2,
    "facts_split_across_chunks": True
})
```

ဒီ scenario မှာ —

```python
2 >= 2  # True
```

ဖြစ်တဲ့အတွက် `multi_hop_failure` ကို ပြန်ပေးပါတယ်။ `facts_split_across_chunks` လည်း
`True` ဖြစ်ပေမဲ့ function က `return` လုပ်ပြီး ရပ်သွားပြီဖြစ်တဲ့အတွက် `chunk_isolation` ကို
မရောက်တော့ပါဘူး။

### S4 — `global_summarization_failure`

```python
("S4", {
    "required_entity_in_index": True,
    "needs_corpus_wide_aggregate": True,
    "hop_count": 0,
    "facts_split_across_chunks": False
})
```

ပထမ rule က `False` ဖြစ်ပြီး ဒုတိယ rule မှာ `needs_corpus_wide_aggregate` က `True`
ဖြစ်တဲ့အတွက် `global_summarization_failure` ကို ပြန်ပေးပါတယ်။

### S5 — `chunk_isolation`

```python
("S5", {
    "required_entity_in_index": True,
    "needs_corpus_wide_aggregate": False,
    "hop_count": 1,
    "facts_split_across_chunks": True
})
```

ပထမ rule က `False` ဖြစ်ပါတယ်။ ဒုတိယ rule လည်း `False` ဖြစ်ပါတယ်။ တတိယ rule ကလည်း
`1 >= 2` ဖြစ်တဲ့အတွက် `False` ဖြစ်ပါတယ်။ နောက်ဆုံးမှာ `facts_split_across_chunks` က
`True` ဖြစ်တဲ့အတွက် `chunk_isolation` ကို ပြန်ပေးပါတယ်။

---

## 9. Dictionary Comprehension — ရလဒ်အားလုံးကို စုဆောင်းခြင်း

အခု code ရဲ့ နောက်တစ်ပိုင်းကို ကြည့်ပါ။

```python
outcomes = {
    sid: classify_failure(features)
    for sid, features in FAILURE_SCENARIOS
}
```

ဒီ code က `FAILURE_SCENARIOS` ထဲက scenario ငါးခုလုံးကို loop ပတ်ပြီး scenario
တစ်ခုစီအတွက် failure label ကို တွက်ချက်ပါတယ်။ ဒီ syntax ကို **dictionary
comprehension** လို့ခေါ်ပါတယ်။

ပုံမှန် `for` loop နဲ့ ရေးမယ်ဆိုရင် —

```python
outcomes = {}

for sid, features in FAILURE_SCENARIOS:
    outcomes[sid] = classify_failure(features)
```

ဆိုပြီး ရေးနိုင်ပါတယ်။ နှစ်ခုလုံးရဲ့ ရည်ရွယ်ချက်က တူညီပါတယ်။

ဥပမာ — `sid = "S2"` ဆိုရင် `classify_failure(features)` က `"ingestion_gap"` ပြန်ပေးမှာ
ဖြစ်ပါတယ်။ ဒါကြောင့် dictionary ထဲမှာ —

```python
outcomes["S2"] = "ingestion_gap"
```

ဆိုပြီး သိမ်းဆည်းထားပါတယ်။ Loop အားလုံးပြီးတဲ့အခါ `outcomes` က ဒီလိုဖြစ်လာပါမယ်။

```python
{
    "S1": "no_failure",
    "S2": "ingestion_gap",
    "S3": "multi_hop_failure",
    "S4": "global_summarization_failure",
    "S5": "chunk_isolation"
}
```

ဒီ dictionary က scenario ID တစ်ခုချင်းစီနဲ့ သက်ဆိုင်ရာ classification result ကို
တွဲဖက်ပေးထားပါတယ်။

---

## 10. `Counter` — Failure အမျိုးအစားတစ်ခုစီ ဘယ်နှကြိမ်ဖြစ်သလဲ။

```python
from collections import Counter
```

ဒီမှာ Python ရဲ့ `collections` standard library module ထဲက `Counter` ကို import
လုပ်ထားပါတယ်။ `Counter` က items တစ်ခုချင်းစီ ဘယ်နှကြိမ် ပါဝင်သလဲဆိုတာ ရေတွက်ပေးတဲ့
data structure ဖြစ်ပါတယ်။

ဥပမာ —

```python
from collections import Counter

results = [
    "ingestion_gap",
    "chunk_isolation",
    "ingestion_gap",
    "no_failure",
]

print(Counter(results))
```

Output —

```text
Counter({'ingestion_gap': 2, 'chunk_isolation': 1, 'no_failure': 1})
```

`ingestion_gap` က နှစ်ကြိမ်ပါဝင်တဲ့အတွက် `2` လို့ ပြပါတယ်။ ကျန်တဲ့ labels တွေက
တစ်ကြိမ်စီပါဝင်တဲ့အတွက် `1` လို့ ပြပါတယ်။

### 10.1 `Counter(outcomes.values())`

```python
print(Counter(outcomes.values()))
```

ဒီနေရာမှာ `.values()` က `outcomes` dictionary ထဲက values တွေကိုသာ ယူပေးပါတယ်။

```python
outcomes.values()
```

ထဲက values တွေက —

```python
[
    "no_failure",
    "ingestion_gap",
    "multi_hop_failure",
    "global_summarization_failure",
    "chunk_isolation"
]
```

ဖြစ်ပါတယ်။ အဲဒီ values တွေကို `Counter()` ထဲ ပေးလိုက်တဲ့အတွက် failure label
တစ်ခုစီရဲ့ အကြိမ်ရေကို ရေတွက်ပေးနိုင်ပါတယ်။

ဒီ exercise မှာ labels ငါးမျိုးလုံး တစ်ကြိမ်စီပဲ ပါဝင်တဲ့အတွက် result က —

```text
Counter({'no_failure': 1, 'ingestion_gap': 1, 'multi_hop_failure': 1, 'global_summarization_failure': 1, 'chunk_isolation': 1})
```

ဖြစ်လာမှာပါ။

---

## 11. Code တစ်ခုလုံးရဲ့ Expected Output

အပိုင်း ၂ မှ ၁၀ အထိ ရှင်းပြခဲ့သည့် အစိတ်အပိုင်းအားလုံးကို ပေါင်းစည်းလိုက်ပါက runnable
script တစ်ခု အပြည့်အစုံ ရရှိပါတယ် —

```python
from collections import Counter

FAILURE_RULES = (
    ("ingestion_gap", lambda f: not f["required_entity_in_index"]),
    ("global_summarization_failure", lambda f: f["needs_corpus_wide_aggregate"]),
    ("multi_hop_failure", lambda f: f["hop_count"] >= 2),
    ("chunk_isolation", lambda f: f["facts_split_across_chunks"]),
)

def classify_failure(features):
    for label, rule in FAILURE_RULES:
        if rule(features):
            return label
    return "no_failure"

FAILURE_SCENARIOS = [
    ("S1", {"required_entity_in_index": True, "needs_corpus_wide_aggregate": False,
            "hop_count": 0, "facts_split_across_chunks": False}),
    ("S2", {"required_entity_in_index": False, "needs_corpus_wide_aggregate": False,
            "hop_count": 0, "facts_split_across_chunks": False}),
    ("S3", {"required_entity_in_index": True, "needs_corpus_wide_aggregate": False,
            "hop_count": 2, "facts_split_across_chunks": True}),
    ("S4", {"required_entity_in_index": True, "needs_corpus_wide_aggregate": True,
            "hop_count": 0, "facts_split_across_chunks": False}),
    ("S5", {"required_entity_in_index": True, "needs_corpus_wide_aggregate": False,
            "hop_count": 1, "facts_split_across_chunks": True}),
]

outcomes = {
    sid: classify_failure(features)
    for sid, features in FAILURE_SCENARIOS
}

print(outcomes)
print(Counter(outcomes.values()))
```

Terminal မှာ ဒီလို ပြပါမယ် —

```text
{'S1': 'no_failure', 'S2': 'ingestion_gap', 'S3': 'multi_hop_failure', 'S4': 'global_summarization_failure', 'S5': 'chunk_isolation'}
Counter({'no_failure': 1, 'ingestion_gap': 1, 'multi_hop_failure': 1, 'global_summarization_failure': 1, 'chunk_isolation': 1})
```

Python ရဲ့ `Counter` ဟာ ပထမဆုံးတွေ့ရတဲ့ item အစီအစဉ်အတိုင်း ပြနိုင်တဲ့အတွက် ဒီ example မှာ
အပေါ်ပါ order အတိုင်း ပေါ်လာပါတယ်။

---

## 12. ကိုယ်တိုင်လေ့ကျင့်ကြည့်ပါ

**မေးခွန်း** — အောက်ပါ features တွေကို `classify_failure()` ထဲ ပေးလိုက်ရင် ဘယ် label ကို
ပြန်ပေးမလဲ။

```python
{
    "required_entity_in_index": False,
    "needs_corpus_wide_aggregate": True,
    "hop_count": 3,
    "facts_split_across_chunks": True
}
```

1. `no_failure`
2. `ingestion_gap`
3. `multi_hop_failure`
4. `chunk_isolation`

<details>
<summary>အဖြေ ကြည့်ရန်</summary>

**အဖြေ — 2. `ingestion_gap`**

အကြောင်းရင်း — ဤ features တွင် rule **လေးခုစလုံး** ကိုက်ညီသည် —

| Rule | စစ်ဆေးချက် | ရလဒ် |
| --- | --- | --- |
| `ingestion_gap` | `not False` | `True` ✓ |
| `global_summarization_failure` | `True` | `True` ✓ |
| `multi_hop_failure` | `3 >= 2` | `True` ✓ |
| `chunk_isolation` | `True` | `True` ✓ |

သို့သော် `FAILURE_RULES` ထဲတွင် `ingestion_gap` သည် **ပထမဆုံး** ဖြစ်သဖြင့်
first-match rule priority အရ ၎င်းကိုသာ ပြန်ပေးသည်။ `multi_hop_failure` ကို
ရွေးချယ်လိုပါက rule များကို ပြန်စီရမည် — သို့မဟုတ် ကိုက်ညီသည့် label အားလုံးကို
စုဆောင်းပေးသည့် function သို့ ပြောင်းရမည်။

</details>

**အဓိက မှတ်ထားရန်** — Exercise 1 မှာ pipeline stages တွေကို dependency အရ စီခဲ့ပါတယ်။
Exercise 2 မှာ similarity score တွေကို ranking လုပ်ခဲ့ပါတယ်။ Exercise 3 မှာ query features
အပေါ် မူတည်ပြီး retrieval modality ကို ရွေးချယ်ခဲ့ပါတယ်။ ဒီ Exercise 4 မှာတော့ **rule
priority** ကို အသုံးပြုပြီး failure အမျိုးအစားကို ခွဲခြားသတ်မှတ်ခဲ့ပါတယ်။ Exercise 3
နှင့် Exercise 4 နှစ်ခုလုံးသည် **first-match rule table** ပုံစံတူညီပြီး ကွာခြားချက်မှာ
rule များကို tuple of tuples တွင် data အဖြစ် သိမ်းထားခြင်း (Exercise 4) နှင့် `if`
statement အဖြစ် တိုက်ရိုက်ရေးထားခြင်း (Exercise 3) ဖြစ်သည်။
