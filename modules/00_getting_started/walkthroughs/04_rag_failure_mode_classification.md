# Walkthrough 04 — RAG Failure Mode Classification (Exercise 4)

> ဤဖိုင်သည် `solution.md` ၏ Exercise 4 ကို **Python အခြေခံမှ စ၍** အပိုင်းလိုက် ရှင်းပြသည့်
> walkthrough ဖြစ်သည်။ Format သည် `walkthroughs/01_pipeline_stage_ordering.md` မှ
> `03_retrieval_modality_selection.md` အထိ နှင့် တူညီသည်။

---

ဤ Exercise တွင် Python ကို အသုံးပြုပြီး RAG (Retrieval-Augmented Generation) system တစ်ခုတွင်
ဖြစ်ပေါ်နိုင်သည့် failure အမျိုးအစားတွေကို သတ်မှတ်ထားသော rules တွေအပေါ် မူတည်ပြီး
အလိုအလျောက် ခွဲခြားသတ်မှတ်ခြင်း (Failure Classification) ကို လေ့လာပါမည်။

အရင် Exercise 1 တွင် Pipeline stages တွေကို dependency အလိုက် စီခဲ့သည်။ Exercise 2 တွင်
Cosine Similarity ကို အသုံးပြုပြီး chunks တွေကို ranking လုပ်ခဲ့သည်။ Exercise 3 တွင်
Query features တွေအပေါ် မူတည်ပြီး retrieval modality ကို ရွေးချယ်ခဲ့သည်။

ဤ Exercise 4 တွင် RAG system က မေးခွန်းတစ်ခုကို မှန်ကန်စွာ မဖြေနိုင်သည့်အခါ မည်သို့
failure ဖြစ်နိုင်သည်ကို Python rules တွေနှင့် ခွဲခြားသတ်မှတ်မည်။

ဥပမာ IT Help Chatbot တွင် user က Kubernetes cluster ၏ configuration အကြောင်း မေးသည့်အခါ
အဖြေမှားသွားနိုင်သည့် အကြောင်းရင်းတွေက အမျိုးမျိုးရှိနိုင်သည်။

- လိုအပ်သော information ကို knowledge index ထဲ မထည့်ထားခြင်း။
- Documents အများအပြားထဲက အချက်အလက်တွေကို စုစည်းပြီး အကျဉ်းချုပ်ရန် မတတ်နိုင်ခြင်း။
- Entities တွေကြား relationships အများအပြားကို လိုက်ရှာရန် လိုအပ်ခြင်း။
- သက်ဆိုင်ရာ facts တွေကို chunks ခွဲလိုက်သည့်အတွက် တစ်စုတစ်စည်းတည်း ပြန်မရရှိခြင်း။

ဤ Exercise တွင် အဓိကလေ့လာရမည့် Python concepts များသည် tuple၊ `lambda`၊ `not`၊
`for` loop၊ `if`၊ `return`၊ dictionary comprehension၊ `Counter` နှင့် rule priority တို့
ဖြစ်သည်။

---

## 1. RAG Failure Mode ဟူသည် ဘာလဲ။

Failure Mode သည် system တစ်ခု အလုပ်မလုပ်နိုင်ခြင်း သို့မဟုတ် မျှော်လင့်ထားသောရလဒ်ကို
မရရှိခြင်း၏ ပုံစံ သို့မဟုတ် အကြောင်းရင်းအမျိုးအစားကို ဆိုလိုသည်။

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
              (features များကို rules တစ်ခုချင်းစီနှင့် စစ်ဆေးခြင်း)
                            |
          +-----------------+-----------------+
          |                 |                 |
          v                 v                 v
   ingestion_gap    multi_hop_failure   chunk_isolation
                            |
                            v
              global_summarization_failure
```

ဤ diagram က concept ကို ရှင်းပြရန် ဖော်ပြထားခြင်း ဖြစ်သည်။ အောက်က Python code သည် input
features တွေပေါ်မူတည်ပြီး label တစ်ခုကို ပြန်ပေးသည့် rule-based classifier ဖြစ်သည်။
အမှန်တကယ် root cause ကို သေချာအတည်ပြုရန် production logs၊ retrieval results နှင့် knowledge
ingestion status တို့ကို ထပ်မံစစ်ဆေးရန် လိုအပ်နိုင်သည်။

---

## 2. `FAILURE_RULES` — Failure Classification Rules

အရင်ဆုံး code ၏ ပထမအပိုင်းကို ကြည့်ပါ။

```python
FAILURE_RULES = (
    ("ingestion_gap", lambda f: not f["required_entity_in_index"]),
    ("global_summarization_failure", lambda f: f["needs_corpus_wide_aggregate"]),
    ("multi_hop_failure", lambda f: f["hop_count"] >= 2),
    ("chunk_isolation", lambda f: f["facts_split_across_chunks"]),
)
```

ဤတွင် `FAILURE_RULES` က tuple တစ်ခုဖြစ်သည်။ Tuple ထဲတွင် rule ၄ ခု ပါဝင်ပြီး rule
တစ်ခုစီက tuple အတွင်းတွင် item နှစ်ခုစီ ပါသည်။

ပထမ item က failure label ဖြစ်ပြီး ဒုတိယ item က condition တစ်ခုကို စစ်ဆေးပေးသည့်
lambda function ဖြစ်သည်။

ဥပမာ —

```python
("ingestion_gap", lambda f: not f["required_entity_in_index"])
```

ဤတွင် အစိတ်အပိုင်း နှစ်ခု ရှိသည် —

- `"ingestion_gap"` — Failure အမျိုးအစား၏ label။
- `lambda f: not f["required_entity_in_index"]` — Input features တွေကို စစ်ဆေးမည့် function။

Python က `FAILURE_RULES` ကို စီထားသော အစီအစဉ်အတိုင်း နောက်ပိုင်းတွင် စစ်ဆေးသွားပါမည်။
ဤအစီအစဉ်က အလွန်အရေးကြီးသည်။

---

## 3. `lambda` function ဟူသည် ဘာလဲ။

ဤ Exercise ၏ အရေးကြီးဆုံး Python concepts တစ်ခုက `lambda` ဖြစ်သည်။

ပုံမှန်အားဖြင့် function တစ်ခုကို `def` နှင့် ဖန်တီးနိုင်သည်။

```python
def is_multi_hop(features):
    return features["hop_count"] >= 2
```

ဤ function က `features` dictionary ထဲက `hop_count` ကို စစ်ဆေးသည်။ တန်ဖိုးက `2` သို့မဟုတ်
အထက်ဖြစ်လျှင် `True` ပြန်ပေးပြီး၊ မဟုတ်လျှင် `False` ပြန်ပေးသည်။

အလားတူ logic ကို `lambda` နှင့်လည်း ရေးနိုင်သည်။

```python
is_multi_hop = lambda f: f["hop_count"] >= 2
```

ဤတွင် —

- `lambda` — အမည်သီးခြားမပေးဘဲ function အသေးတစ်ခု ဖန်တီးခြင်း။
- `f` — Function ထဲကို ဝင်လာမည့် argument။
- `f["hop_count"] >= 2` — စစ်ဆေးမည့် expression။

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

ဤ Exercise တွင် lambda function တွေကို variable တစ်ခုချင်းစီတွင် သီးခြားသိမ်းမထားဘဲ
`FAILURE_RULES` tuple ထဲတွင် တိုက်ရိုက်ထည့်ထားသည်။ ထို့ကြောင့် rule တစ်ခုစီတွင် label နှင့်
စစ်ဆေးမည့် function ကို အတူတကွ သိမ်းထားနိုင်သည်။

---

## 4. Rule တစ်ခုချင်းစီကို နားလည်ခြင်း

### Rule 1 — `ingestion_gap`

```python
("ingestion_gap", lambda f: not f["required_entity_in_index"])
```

ဤ rule က လိုအပ်သော entity သည် index ထဲတွင် ရှိမရှိကို စစ်ဆေးသည်။

Dictionary ထဲက feature က —

```python
"required_entity_in_index": True
```

ဆိုလျှင် လိုအပ်သော entity သည် index ထဲတွင် ရှိသည်ဟု ဖော်ပြသည်။ ထိုအခါ —

```python
print(not True)
```

Output —

```text
False
```

ဤ expression ၏ result က `False` ဖြစ်သည်။ ထို့ကြောင့် `ingestion_gap` rule မကိုက်ညီပါ။

သို့သော် —

```python
"required_entity_in_index": False
```

ဆိုလျှင် —

```python
print(not False)
```

Output —

```text
True
```

ဤ expression ၏ result က `True` ဖြစ်သည်။ ထို့ကြောင့် `ingestion_gap` ကို ရွေးချယ်နိုင်သည်။

Python ၏ `not` operator က Boolean value ကို ပြောင်းပြန်လှန်ပေးခြင်း ဖြစ်သည်။

| Original value | `not` ဖြင့် ပြောင်းလဲပြီး |
| --- | --- |
| `True` | `False` |
| `False` | `True` |

RAG နှင့် ဆက်စပ်ကြည့်ပါ။ User က မေးထားသော entity၊ ဥပမာ `sg-rag-prd-m1` cluster အကြောင်းကို
သိရှိရန် လိုအပ်ပေမဲ့ ထို entity ဆိုင်ရာ information ကို indexing လုပ်ထားသော knowledge base
ထဲ မတွေ့ပါဆိုလျှင် ingestion သို့မဟုတ် indexing ပြဿနာ ဖြစ်နိုင်သည်။

သို့သော် index ထဲတွင် မတွေ့ရခြင်းတစ်ခုတည်းနှင့် ingestion ပျက်ကွက်သည်ဟု အတည်မပြုနိုင်ပါ။
Metadata filters၊ permissions၊ entity extraction နှင့် index lookup တွေကိုလည်း စစ်ဆေးရန်
လိုအပ်နိုင်သည်။

### Rule 2 — `global_summarization_failure`

```python
("global_summarization_failure", lambda f: f["needs_corpus_wide_aggregate"])
```

ဤ rule က corpus တစ်ခုလုံး သို့မဟုတ် knowledge base ၏ အပိုင်းအခြားကြီးတစ်ခုကို
ပေါင်းစပ်စဉ်းစားရန် လိုအပ်ကြောင်း သတ်မှတ်ထားသလား စစ်ဆေးသည်။

ဥပမာ —

```python
features = {
    "needs_corpus_wide_aggregate": True
}
```

ဤ condition က `True` ဖြစ်သည့်အတွက် rule ကိုက်ညီသည်။

ဤနေရာတွင် `not` မပါပါ။ ထို့ကြောင့် feature က `True` ဖြစ်နေလျှင် တိုက်ရိုက်ကိုက်ညီပြီး၊
`False` ဖြစ်နေလျှင် မကိုက်ညီပါ။

RAG ဥပမာ — "Knowledge base ထဲတွင် 2026 ခုနှစ်အတွင်း အဖြစ်အများဆုံးဖြစ်သည့် infrastructure
incidents တွေနှင့် common causes တွေကို အကျဉ်းချုပ်ပေးပါ" ဆိုသည့် မေးခွန်းသည် document
တစ်ခုတည်းကို ရှာဖွေခြင်းထက် information အများအပြားကို စုစည်းရန် လိုအပ်နိုင်သည်။

သို့သော် ဤ exercise တွင် `needs_corpus_wide_aggregate` က `True` ဖြစ်ခြင်းနှင့်
`global_summarization_failure` ဟု သတ်မှတ်ထားသည်။ တကယ့် system တွင်
အကျဉ်းချုပ်ရန် လိုအပ်ခြင်းသည် အလိုအလျောက် failure ဖြစ်နေသည်ဟု မဆိုလိုပါ။ မေးခွန်းကို
မှန်ကန်စွာ မဖြေနိုင်ခဲ့ကြောင်းနှင့် global summarization လုပ်ဆောင်မှု မအောင်မြင်ခဲ့ကြောင်းကို
သီးခြားသက်သေပြရန် လိုသည်။

### Rule 3 — `multi_hop_failure`

```python
("multi_hop_failure", lambda f: f["hop_count"] >= 2)
```

ဤ rule က relationship hops နှစ်ခုနှင့်အထက်ကို လိုက်ရှာရန် လိုအပ်သော Query ကို စစ်ဆေးသည်။

ဥပမာ —

```python
features = {"hop_count": 3}

print(features["hop_count"] >= 2)
```

Output —

```text
True
```

`>=` က "ထက်ကြီး သို့မဟုတ် ညီမျှ" ဟု ဆိုလိုခြင်းဖြစ်သည့်အတွက် `2`၊ `3`၊ `4` စသည့်
တန်ဖိုးတွေအားလုံးတွင် `True` ဖြစ်သည်။

IT infrastructure ဥပမာနှင့် ကြည့်ကြပါမည်။

```text
Application A → Kubernetes Cluster B → Database C
```

User က "Application A က ဘယ် Database ကို ချိတ်ဆက်အသုံးပြုနေလဲ" ဟု မေးသည့်အခါ
relationship အများအပြားကို ဖြတ်သန်းရှာဖွေရန် လိုအပ်နိုင်သည်။

Graph သို့မဟုတ် multi-hop retrieval လိုအပ်သော Query ကို မမှန်ကန်စွာ ဖြေရှင်းခဲ့သည်ဟု
သတ်မှတ်လျှင် ဤ rule ကို အသုံးပြုနိုင်သည်။

ဤ exercise သည် `hop_count >= 2` ဖြစ်ရုံနှင့် `multi_hop_failure` ကို ပြန်ပေးသည်။
အမှန်တကယ် multi-hop retrieval မအောင်မြင်ခဲ့ကြောင်းကိုတော့ သီးခြားစစ်ဆေးရမည်။

### Rule 4 — `chunk_isolation`

```python
("chunk_isolation", lambda f: f["facts_split_across_chunks"])
```

ဤ rule က အဖြေအတွက် လိုအပ်သော facts တွေသည် document chunks အများအပြားထဲတွင် ပြန့်ကျဲနေသလား
စစ်ဆေးသည်။

ဥပမာ knowledge base တွင် —

```text
Chunk A
  Application A runs on Kubernetes Cluster B.

Chunk B
  Kubernetes Cluster B connects to Database C.
```

User က "Application A က ဘယ် database ကို အသုံးပြုသလား" ဟု မေးသည့်အခါ မှန်ကန်သော အဖြေထုတ်ရန်
Chunk A နှင့် Chunk B နှစ်ခုလုံးက information တွေ လိုအပ်သည်။

Retrieval က Chunk A တစ်ခုတည်းကိုသာ ပြန်ပေးခဲ့လျှင် လိုအပ်သော relationship chain ကို
ပြည့်စုံစွာ မရနိုင်ပါ။

ဤသို့ facts တွေ သီးခြား chunks တွေအဖြစ် ခွဲထွက်နေမှုနှင့် retrieval ပြဿနာကို ရိုးရှင်းစွာ
ကိုယ်စားပြုရန် —

```python
"facts_split_across_chunks": True
```

ဟု သတ်မှတ်ထားသည်။

၎င်းသည် chunking အမြဲမှားနေသည်ဟု ဆိုလိုခြင်း မဟုတ်ပါ။ Chunk တွေကို သင့်တော်စွာ
ခွဲထားပေမဲ့ retrieval အချိန်တွင် လိုအပ်သော chunks တွေ အားလုံးကို ပြန်မရခြင်းလည်း
ဖြစ်နိုင်သည်။

---

## 5. `classify_failure(features)` function

Rules တွေကို သတ်မှတ်ပြီးသည့်နောက် failure အမျိုးအစားကို ရွေးချယ်ပေးမည့် function ကို
ဖန်တီးထားသည်။

```python
def classify_failure(features):
    for label, rule in FAILURE_RULES:
        if rule(features):
            return label
    return "no_failure"
```

ဤ function က `features` dictionary ကို input အဖြစ် လက်ခံပြီး failure label တစ်ခုကို
ပြန်ပေးသည်။ ဤ function အတွင်းတွင် အရေးကြီးသော logic သုံးခု ရှိသည်။

- `for` loop နှင့် rules တွေကို အစဉ်လိုက် စစ်ဆေးခြင်း။
- `if rule(features)` နှင့် လက်ရှိ rule ကို စမ်းသပ်ခြင်း။
- `return label` နှင့် ပထမဆုံးကိုက်ညီသည့် rule ၏ label ကို ပြန်ပေးခြင်း။

### Step 5.1 — `for label, rule in FAILURE_RULES`

```python
for label, rule in FAILURE_RULES:
```

`FAILURE_RULES` ထဲတွင် tuple ၄ ခု ရှိသည်။ Tuple တစ်ခုချင်းစီတွင် item နှစ်ခုစီ ပါဝင်သည်။
ဥပမာ —

```python
("ingestion_gap", lambda f: not f["required_entity_in_index"])
```

ဤ tuple ကို loop က ရယူသည့်အခါ —

- `label` ထဲကို `"ingestion_gap"` ဝင်လာမည်။
- `rule` ထဲကို `lambda` function ဝင်လာမည်။

ဤသို့ tuple ထဲက item တွေကို variable တစ်ခုချင်းစီ ခွဲထည့်ခြင်းသည် **tuple unpacking**
ဖြစ်သည်။

### Step 5.2 — `if rule(features)`

```python
if rule(features):
```

ဤ code က `rule` variable ထဲတွင် သိမ်းထားသော function ကို `features` argument ပေးပြီး
ခေါ်ခြင်း ဖြစ်သည်။

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

ထိုသို့သာ `classify_failure()` က rule တစ်ခုချင်းစီကို စမ်းသပ်ပြီး result က `True`
ဖြစ်မဖြစ် စစ်ဆေးသည်။

### Step 5.3 — `return label`

```python
if rule(features):
    return label
```

လက်ရှိ rule က `True` ပြန်ပေးလျှင် သက်ဆိုင်သော label ကို ပြန်ပေးပြီး function ကို
ရပ်တန့်သည်။

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

ဖြစ်သည်။ `required_entity_in_index` က `False` ဖြစ်သည့်အတွက် `not False` ၏ result က
`True` ဖြစ်သည်။ ထို့ကြောင့် function က —

### Function က ပြန်ပေးသည့် label

```python
return "ingestion_gap"
```

ကို ပြန်ပေးပြီး နောက်ထပ် rules တွေကို ဆက်မစစ်တော့ပါ။

### Step 5.4 — `return "no_failure"`

```python
return "no_failure"
```

ဤသို့ `return` က `for` loop အပြင်ဘက်တွင် ရှိနေသည်။ အဓိပ္ပာယ်က rules ၄ ခုစလုံးကို
စစ်ဆေးပြီး တစ်ခုမှ `True` မဖြစ်ခဲ့လျှင် `"no_failure"` ကို default result အနေနှင့်
ပြန်ပေးမည်။

ဤနေရာတွင် `"no_failure"` သည် ဤ rule set အရ သတ်မှတ်ထားသော failure rules တွေကို
မတွေ့ပါ ဟု ဆိုလိုသည်။ RAG system တစ်ခုလုံးတွင် failure လုံးဝမရှိပါဟု
အတည်ပြုခြင်း မဟုတ်ပါ။

---

## 6. Rule Priority — ဘယ် Rule ကို အရင်ရွေးမလဲ။

ဤ code တွင် သတိထားရမည့် အရေးကြီးဆုံးအချက်တစ်ခုက rule တွေ၏ အစီအစဉ် ဖြစ်သည်။

ဥပမာ —

```python
features = {
    "required_entity_in_index": True,
    "needs_corpus_wide_aggregate": False,
    "hop_count": 2,
    "facts_split_across_chunks": True,
}
```

ဤ feature တွေတွင် —

- `ingestion_gap` condition က `False` ဖြစ်သည်။
- `global_summarization_failure` condition က `False` ဖြစ်သည်။
- `multi_hop_failure` condition က `True` ဖြစ်သည်။
- `chunk_isolation` condition ကလည်း `True` ဖြစ်သည်။

သို့ဖြစ်လျှင် failure နှစ်မျိုးနှင့် ကိုက်ညီနေသည်။ သို့သော် function က ပထမဆုံး ကိုက်ညီသည့် rule
ဖြစ်သည့် `multi_hop_failure` ကိုသာ ပြန်ပေးပါမည်။

အကြောင်းရင်းတွင် —

```python
if rule(features):
    return label
```

ဤနေရာတွင် `return` ရောက်ခြင်းနှင့် function ရပ်သွားသောကြောင့် ဖြစ်သည်။ ဤသို့ logic ကို **first-match rule
priority** ဟု မှတ်သားနိုင်သည်။

ဤ priority က လုပ်ဆောင်ပုံအရ မှန်ကန်ပေမဲ့ failure အမျိုးအစားအားလုံးကို သိချင်သည့်
diagnostic system တစ်ခုအတွက်တော့ ကန့်သတ်ချက် ရှိသည်။ ထိုသို့အပ်ချက်ရှိလျှင် ပထမဆုံး
ကိုက်ညီသည့် label တစ်ခုတည်းကို ပြန်မပေးဘဲ ကိုက်ညီသည့် rules အားလုံးကို စုဆောင်းပေးရန်
ပြောင်းလဲနိုင်သည်။

---

## 7. `FAILURE_SCENARIOS` — စမ်းသပ်မည့် Scenario များ

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

`FAILURE_SCENARIOS` သည် scenario ငါးခုပါဝင်သည့် list တစ်ခု ဖြစ်သည်။ Scenario တစ်ခုစီတွင် —

- `"S1"`, `"S2"` စသည့် scenario ID။
- Failure classifier ကို စမ်းသပ်ပေးမည့် features dictionary။

တို့ ပါဝင်သည်။ အခု scenario တစ်ခုချင်းစီက ဘာကြောင့် ဤ label ကို ရရှိသည်ကို
ကြည့်ကြပါမည်။

---

## 8. Scenario တစ်ခုချင်းစီကို စစ်ဆေးခြင်း

| Scenario | အရေးကြီးသော feature | ရွေးချယ်မည့် label | အကြောင်းရင်း |
| --- | --- | --- | --- |
| S1 | Failure conditions အားလုံး `False` | `no_failure` | ဘယ် rule မှ မကိုက်ညီပါ |
| S2 | `required_entity_in_index = False` | `ingestion_gap` | ပထမ rule က `True` ဖြစ်သည် |
| S3 | `hop_count = 2`, `facts_split_across_chunks = True` | `multi_hop_failure` | Rule 3 က အရင်ကိုက်ညီသည် |
| S4 | `needs_corpus_wide_aggregate = True` | `global_summarization_failure` | Rule 2 က ကိုက်ညီသည် |
| S5 | `facts_split_across_chunks = True` | `chunk_isolation` | နောက်ဆုံး rule ကိုက်ညီသည် |

အထူးသဖြင့် S3 က စိတ်ဝင်စားသင့်သည်။ `multi_hop_failure` နှင့် `chunk_isolation`
နှစ်ခုစလုံးကိုက်ညီပေမဲ့ `FAILURE_RULES` ထဲတွင် `multi_hop_failure` က အရင်ရှိသည့်အတွက်
ထို label ကိုသာ ရွေးချယ်သည်။

### S1 — `no_failure`

```python
("S1", {
    "required_entity_in_index": True,
    "needs_corpus_wide_aggregate": False,
    "hop_count": 0,
    "facts_split_across_chunks": False
})
```

ပထမ rule တွင် `not True` က `False` ဖြစ်သည်။ ကျန်သော rule တွေလည်း `False` ဖြစ်သည့်အတွက်
default result ဖြစ်သည့် `no_failure` ကို ပြန်ပေးသည်။

### S2 — `ingestion_gap`

```python
("S2", {
    "required_entity_in_index": False,
    "needs_corpus_wide_aggregate": False,
    "hop_count": 0,
    "facts_split_across_chunks": False
})
```

ပထမ rule တွင် `not False` က `True` ဖြစ်ခြင်းကြောင့် `ingestion_gap` ကို ပြန်ပေးသည်။

### S3 — `multi_hop_failure`

```python
("S3", {
    "required_entity_in_index": True,
    "needs_corpus_wide_aggregate": False,
    "hop_count": 2,
    "facts_split_across_chunks": True
})
```

ဤ scenario တွင် —

```python
2 >= 2  # True
```

ဖြစ်သည့်အတွက် `multi_hop_failure` ကို ပြန်ပေးသည်။ `facts_split_across_chunks` လည်း
`True` ဖြစ်ပေမဲ့ function က `return` လုပ်ပြီး ရပ်သွားပြီဖြစ်သည့်အတွက် `chunk_isolation` ကို
မရောက်တော့ပါ။

### S4 — `global_summarization_failure`

```python
("S4", {
    "required_entity_in_index": True,
    "needs_corpus_wide_aggregate": True,
    "hop_count": 0,
    "facts_split_across_chunks": False
})
```

ပထမ rule က `False` ဖြစ်ပြီး ဒုတိယ rule တွင် `needs_corpus_wide_aggregate` က `True`
ဖြစ်သည့်အတွက် `global_summarization_failure` ကို ပြန်ပေးသည်။

### S5 — `chunk_isolation`

```python
("S5", {
    "required_entity_in_index": True,
    "needs_corpus_wide_aggregate": False,
    "hop_count": 1,
    "facts_split_across_chunks": True
})
```

ပထမ rule က `False` ဖြစ်သည်။ ဒုတိယ rule လည်း `False` ဖြစ်သည်။ တတိယ rule ကလည်း
`1 >= 2` ဖြစ်သည့်အတွက် `False` ဖြစ်သည်။ နောက်ဆုံးတွင် `facts_split_across_chunks` က
`True` ဖြစ်သည့်အတွက် `chunk_isolation` ကို ပြန်ပေးသည်။

---

## 9. Dictionary Comprehension — ရလဒ်အားလုံးကို စုဆောင်းခြင်း

အခု code ၏ နောက်တစ်ပိုင်းကို ကြည့်ပါ။

```python
outcomes = {
    sid: classify_failure(features)
    for sid, features in FAILURE_SCENARIOS
}
```

ဤ code က `FAILURE_SCENARIOS` ထဲက scenario ငါးခုလုံးကို loop ပတ်ပြီး scenario
တစ်ခုစီအတွက် failure label ကို တွက်ချက်သည်။ ဤ syntax ကို **dictionary
comprehension** ဟုခေါ်သည်။

ပုံမှန် `for` loop နှင့် ရေးမည်ဆိုလျှင် —

```python
outcomes = {}

for sid, features in FAILURE_SCENARIOS:
    outcomes[sid] = classify_failure(features)
```

ဆိုပြီး ရေးနိုင်သည်။ နှစ်ခုလုံး၏ ရည်ရွယ်ချက်က တူညီသည်။

ဥပမာ — `sid = "S2"` ဆိုလျှင် `classify_failure(features)` က `"ingestion_gap"` ပြန်ပေးတွင်
ဖြစ်သည်။ ထို့ကြောင့် dictionary ထဲတွင် —

```python
outcomes["S2"] = "ingestion_gap"
```

ဆိုပြီး သိမ်းဆည်းထားသည်။ Loop အားလုံးပြီးသည့်အခါ `outcomes` က ဤသို့ဖြစ်လာပါမည်။

```python
{
    "S1": "no_failure",
    "S2": "ingestion_gap",
    "S3": "multi_hop_failure",
    "S4": "global_summarization_failure",
    "S5": "chunk_isolation"
}
```

ဤ dictionary က scenario ID တစ်ခုချင်းစီနှင့် သက်ဆိုင်ရာ classification result ကို
တွဲဖက်ပေးထားသည်။

---

## 10. `Counter` — Failure အမျိုးအစားတစ်ခုစီ ဘယ်နှကြိမ်ဖြစ်သလား။

```python
from collections import Counter
```

ဤတွင် Python ၏ `collections` standard library module ထဲက `Counter` ကို import
လုပ်ထားသည်။ `Counter` က items တစ်ခုချင်းစီ မည်မျှအကြိမ် ပါဝင်သည်ကို ရေတွက်ပေးသည့်
data structure ဖြစ်သည်။

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

`ingestion_gap` က နှစ်ကြိမ်ပါဝင်သည့်အတွက် `2` ဟု ပြသည်။ ကျန်သော labels တွေက
တစ်ကြိမ်စီပါဝင်သည့်အတွက် `1` ဟု ပြသည်။

### 10.1 `Counter(outcomes.values())`

```python
print(Counter(outcomes.values()))
```

ဤနေရာတွင် `.values()` က `outcomes` dictionary ထဲက values တွေကိုသာ ယူပေးသည်။

```python
outcomes.values()
```

ထဲက values တွေက —

```text
[
    "no_failure",
    "ingestion_gap",
    "multi_hop_failure",
    "global_summarization_failure",
    "chunk_isolation"
]
```

ဖြစ်သည်။ ထို values တွေကို `Counter()` ထဲ ပေးလိုက်သည့်အတွက် failure label
တစ်ခုစီ၏ အကြိမ်ရေကို ရေတွက်ပေးနိုင်သည်။

ဤ exercise တွင် labels ငါးမျိုးလုံး တစ်ကြိမ်စီသာ ပါဝင်သည့်အတွက် result က —

```text
Counter({'no_failure': 1, 'ingestion_gap': 1, 'multi_hop_failure': 1, 'global_summarization_failure': 1, 'chunk_isolation': 1})
```

ဖြစ်လာမည်။

---

## 11. Code တစ်ခုလုံး၏ Expected Output

အပိုင်း ၂ မှ ၁၀ အထိ ရှင်းပြခဲ့သည့် အစိတ်အပိုင်းအားလုံးကို ပေါင်းစည်းလိုက်ပါက runnable
script တစ်ခု အပြည့်အစုံ ရရှိသည် —

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

Terminal တွင် ဤသို့ ပြပါမည် —

```text
{'S1': 'no_failure', 'S2': 'ingestion_gap', 'S3': 'multi_hop_failure', 'S4': 'global_summarization_failure', 'S5': 'chunk_isolation'}
Counter({'no_failure': 1, 'ingestion_gap': 1, 'multi_hop_failure': 1, 'global_summarization_failure': 1, 'chunk_isolation': 1})
```

Python ၏ `Counter` သည် ပထမဆုံးတွေ့ရသည့် item အစီအစဉ်အတိုင်း ပြနိုင်သည့်အတွက် ဤ example တွင်
အပေါ်ပါ order အတိုင်း ပေါ်လာသည်။

---

## 12. ကိုယ်တိုင်လေ့ကျင့်ကြည့်ပါ

**မေးခွန်း** — အောက်ပါ features တွေကို `classify_failure()` ထဲ ပေးလိုက်လျှင် ဘယ် label ကို
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

အကြောင်းရင်း — ဤ features တွင် rule **၄ ခုစလုံး** ကိုက်ညီသည် —

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

**အဓိက မှတ်ထားရန်** — Exercise 1 တွင် pipeline stages တွေကို dependency အရ စီခဲ့သည်။
Exercise 2 တွင် similarity score တွေကို ranking လုပ်ခဲ့သည်။ Exercise 3 တွင် query features
အပေါ် မူတည်ပြီး retrieval modality ကို ရွေးချယ်ခဲ့သည်။ ဤ Exercise 4 တွင် **rule
priority** ကို အသုံးပြုပြီး failure အမျိုးအစားကို ခွဲခြားသတ်မှတ်ခဲ့သည်။ Exercise 3
နှင့် Exercise 4 နှစ်ခုလုံးသည် **first-match rule table** ပုံစံတူညီပြီး ကွာခြားချက်တွင်
rule များကို tuple of tuples တွင် data အဖြစ် သိမ်းထားခြင်း (Exercise 4) နှင့် `if`
statement အဖြစ် တိုက်ရိုက်ရေးထားခြင်း (Exercise 3) ဖြစ်သည်။
