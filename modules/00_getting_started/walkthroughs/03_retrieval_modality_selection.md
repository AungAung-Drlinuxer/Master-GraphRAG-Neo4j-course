# Walkthrough 03 — Retrieval Modality Selection (Exercise 3)

> ဤဖိုင်သည် `solution.md` ၏ Exercise 3 ကို **Python အခြေခံမှ စ၍** အပိုင်းလိုက် ရှင်းပြသည့်
> walkthrough ဖြစ်သည်။ Format သည် `walkthroughs/01_pipeline_stage_ordering.md` နှင့်
> `walkthroughs/02_cosine_similarity_ranking.md` တို့နှင့် တူညီသည်။

---

ဤ exercise တွင် Python ကို အသုံးပြုပြီး User ၏ မေးခွန်းအမျိုးအစားနှင့် လိုအပ်ချက်အပေါ် မူတည်ကာ
ဘယ် Retrieval နည်းလမ်းကို ရွေးချယ်မလဲခြင်းကို ဆုံးဖြတ်ခြင်းကို လေ့လာပါမည်။

အရင် Exercise 2 တွင် Cosine Similarity ကို အသုံးပြုပြီး Query နှင့် အနီးစပ်ဆုံးတူညီသော chunks တွေကို
Ranking လုပ်ခဲ့သည်။ ဤ Exercise 3 တွင် နောက်တစ်ဆင့်တက်ပြီး Query တစ်ခုချင်းစီအတွက် မည်သည့်
Retrieval Modality ကို အသုံးပြုသင့်သည်ကို စည်းမျဉ်းအလိုက် ရွေးချယ်မည်။

RAG system တစ်ခုတွင် Query အားလုံးကို Vector Search တစ်မျိုးတည်းနှင့် ဖြေရှင်းရန် မလိုအပ်ပါ။
ရိုးရှင်းသော မေးခွန်းတွေအတွက် Vector Search လုံလောက်နိုင်ပေမဲ့၊ Documents အများအပြားက
information တွေကို ဆက်စပ်ရှာရမည့် မေးခွန်းတွေတွင် GraphRAG က ပိုသင့်တော်နိုင်သည်။
Structured data ကို တိကျသော condition အလိုက် စစ်ထုတ်ရမည့် မေးခွန်းတွေအတွက် Text-to-Cypher
ကို အသုံးပြုနိုင်သည်။

ဤ code တွင် လေ့လာရမည့် Python concepts များသည် function၊ dictionary၊ `if`၊ `and`၊ `return`၊
list of tuples၊ `for` loop နှင့် unpacking တို့ ဖြစ်သည်။

---

## 1. Retrieval Modality ဟူသည် ဘာလဲ။

Retrieval Modality သည် မေးခွန်းတစ်ခုအတွက် သက်ဆိုင်ရာ information ကို ရှာဖွေရန်
အသုံးပြုမည့် နည်းလမ်းအမျိုးအစားကို ဆိုလိုသည်။

```text
                        User Query
                            |
                            v
                 Feature-based Router
              (Python ၏ condition တွေ စစ်ဆေးခြင်း)
                            |
          +-----------------+-----------------+
          |                 |                 |
          v                 v                 v
   Vector Search        GraphRAG        Text-to-Cypher
```

| Modality | အခြေခံသည် | အသုံးပြုသည့်နေရာ |
| --- | --- | --- |
| Vector Search | Semantic similarity | ရိုးရှင်းသော မေးခွန်းများ — Plain RAG |
| GraphRAG | Entities နှင့် relationships | Multi-hop နှင့် corpus-wide မေးခွန်းများ |
| Text-to-Cypher | Graph database query | Structured filtering |
| Plain RAG | Documents / text chunks | Vector Search ရလဒ်ကို LLM ထံ ပေးသည့် pipeline |

ဤ code က retrieval နည်းလမ်းတွေကို တကယ် run မလုပ်သေးပါ။ မည်သည့်နည်းလမ်းကို
အသုံးပြုသင့်သည်ကို ရွေးချယ်ပေးသည့် **routing logic** ကိုသာ ဖော်ပြထားခြင်း ဖြစ်သည်။

---

## 2. `select_modality(features)` function

အရင်ဆုံး function ကို ကြည့်ကြပါမည်။

```python
def select_modality(features):
    """Choose the cheapest retrieval modality that satisfies the query features."""
```

ဤတွင် `select_modality` ဆိုသည့် function ကို သတ်မှတ်ထားသည်။

- `select_modality` — Function အမည်။
- `features` — Query တစ်ခု၏ လိုအပ်ချက်တွေကို သိမ်းထားသော dictionary။
- `"""..."""` — Function ၏ ရည်ရွယ်ချက်ကို ရှင်းပြထားသော docstring။

Function ကို ခေါ်သည့်အခါ `features` ထဲတွင် ဘယ်လို data တွေ ပါလာမလဲခြင်းက ဤ Exercise ၏
အဓိကအချက် ဖြစ်သည်။

ဥပမာ —

```python
features = {
    "hop_count": 3,
    "spans_documents": True,
    "needs_corpus_wide_summary": False,
    "needs_structured_filter": False,
}
```

ဤ dictionary က Query တစ်ခုတွင် document များစွာကြား relationship တွေကို လိုက်ရှာရန်
လိုအပ်နေကြောင်း ဖော်ပြထားသည်။

> **မှတ်ချက်** — ဤနေရာတွင် function ၏ ခေါင်းစီး (signature) နှင့် docstring ကိုသာ ပြထားသည်။
> Body ကို အပိုင်း ၄ မှ ၇ အထိ တစ်ကြောင်းချင်း ရှင်းပြထားပြီး၊ Function အပြည့်အစုံကို
> အပိုင်း ၇ အကုန်တွင်လည်းကောင်း၊ runnable version ကို အပိုင်း ၁၁ တွင်လည်းကောင်း
> ဖော်ပြထားသည်။

---

## 3. `features` dictionary ကို နားလည်ခြင်း

ဤ Exercise တွင် feature ၄ ခုကို သတ်မှတ်ထားသည်။

| Feature | အဓိပ္ပာယ် |
| --- | --- |
| `hop_count` | Graph ထဲတွင် ဆက်စပ်နေသော entities တွေကြား လိုက်ရှာရမည့် relationship hops အရေအတွက် |
| `spans_documents` | မေးခွန်းအတွက် Documents တစ်ခုထက်ပိုပြီး ချိတ်ဆက်စဉ်းစားရမလား |
| `needs_corpus_wide_summary` | Knowledge corpus တစ်ခုလုံး သို့မဟုတ် အပိုင်းအခြားကြီးတစ်ခုကို အကျဉ်းချုပ်ရန် လိုသလား |
| `needs_structured_filter` | Property၊ field၊ condition တို့အပေါ် မူတည်ပြီး structured records တွေကို စစ်ထုတ်ရန် လိုသလား |

ဥပမာ `"hop_count": 3` သည် Graph ထဲတွင် relationship သုံးခုအထိ ဖြတ်သန်းရှာရန် လိုအပ်သည်ဟု
ယူဆထားခြင်း ဖြစ်သည်။

`True` နှင့် `False` တို့က Boolean values ဖြစ်သည်။

```python
"spans_documents": True
```

ဆိုလျှင် Documents များစွာကို ချိတ်ဆက်စဉ်းစားရန် လိုအပ်သည်ဟု သတ်မှတ်ထားခြင်း ဖြစ်သည်။

```python
"spans_documents": False
```

ဆိုလျှင် ထို feature ကို မလိုအပ်ပါဟု သတ်မှတ်ထားခြင်း ဖြစ်သည်။

မှတ်သားရန် — ဤ feature တွေကို code ထဲတွင် ကြိုတင်ပေးထားသည်။ Production system တစ်ခုတွင်
ဤသို့ features တွေကို Query classifier၊ LLM-based router သို့မဟုတ် သီးခြားစည်းမျဉ်းတွေကနေ
ထုတ်ယူနိုင်သည်။

---

## 4. ပထမဆုံး `if` condition — GraphRAG: Entity-Anchored Subgraph Retrieval

```python
if features["hop_count"] >= 2 and features["spans_documents"]:
    return "GraphRAG - entity-anchored subgraph retrieval"
```

ဤအပိုင်းကို အဆင့်လိုက် ခွဲရှင်းကြည့်ကြပါမည်။

### 4.1 `features["hop_count"] >= 2`

```python
features["hop_count"] >= 2
```

- `features["hop_count"]` က dictionary ထဲက `hop_count` တန်ဖိုးကို ရယူသည်။
- `>=` က greater than or equal to ဖြစ်ပြီး "ထက်ကြီး သို့မဟုတ် ညီမျှ" ဟု အဓိပ္ပာယ်ရသည်။

ဥပမာ —

```python
print(3 >= 2)   # True
print(2 >= 2)   # True
print(1 >= 2)   # False
```

ထို့ကြောင့် Query တွင် Graph relationship နှစ်ခုနှင့်အထက်ကို လိုက်ရှာရန် လိုသည်ဟု
သတ်မှတ်ထားသလား စစ်ဆေးခြင်း ဖြစ်သည်။

### 4.2 `and features["spans_documents"]`

```python
features["hop_count"] >= 2 and features["spans_documents"]
```

`and` သည် condition နှစ်ခုစလုံး မှန်မှသာ `True` ဖြစ်သည်။

ဥပမာ —

```python
hop_count = 3
spans_documents = True

print(hop_count >= 2 and spans_documents)
```

Output —

```text
True
```

သို့သော် —

```python
hop_count = 3
spans_documents = False

print(hop_count >= 2 and spans_documents)
```

Output —

```text
False
```

ဤ condition က အချက်နှစ်ချက်လုံးကို လိုအပ်သည်။

- `hop_count` က `2` သို့မဟုတ် အထက် ဖြစ်ရမည်။
- `spans_documents` က `True` ဖြစ်ရမည်။

အချက်နှစ်ချက်လုံး ပြည့်မီလျှင် —

```python
return "GraphRAG - entity-anchored subgraph retrieval"
```

ဆိုပြီး ဤ Retrieval Modality ကို ရွေးချယ်ကာ function ၏ result ကို ပြန်ပေးသည်။

### Entity-Anchored Subgraph Retrieval ဟူသည် ဘာလဲ။

GraphRAG က Knowledge Graph ထဲတွင် entities တွေ၊ သူတို့အကြား relationships တွေကို
အသုံးပြုပြီး ရှာဖွေနိုင်သည်။

ဥပမာ IT environment တွင် —

```text
Application A → runs on → Kubernetes Cluster B → connects to → Database C
```

ဆိုသည့် relationships တွေ ရှိသည်ဟု ယူဆကြည့်ပါ။ User က "Application A က ဘယ် Database ကို
အသုံးပြုနေလဲ" ဟု မေးသည့်အခါ အစရှိသည့် entity တစ်ခုကနေ စတင်ပြီး relationships တွေကို
လိုက်ရှာနိုင်သည်။

ဤသို့ သတ်မှတ်ထားသော entity တစ်ခုကို အစပြုကာ သက်ဆိုင်ရာ subgraph ကို ရှာသည့်ပုံစံကို
**entity-anchored subgraph retrieval** ဟု ခေါ်သည်။

---

## 5. ဒုတိယ `if` condition — GraphRAG: Community Summary Retrieval

```python
if features["needs_corpus_wide_summary"]:
    return "GraphRAG - community summary retrieval"
```

ဤ condition က Query တွင် corpus တစ်ခုလုံး၊ သို့မဟုတ် knowledge graph ၏
အပိုင်းအခြားကြီးတစ်ခုအကြောင်း အကျဉ်းချုပ်ရန် လိုသလား စစ်ဆေးသည်။

```python
features = {"needs_corpus_wide_summary": True}

print(features["needs_corpus_wide_summary"])
```

Output —

```text
True
```

ဤ value က `True` ဖြစ်လျှင် အောက်ပါ result ကို ပြန်ပေးပါမည်။

```python
return "GraphRAG - community summary retrieval"
```

ဥပမာ User က —

> Our IT knowledge base ထဲက အများဆုံးတွေ့ရသည့် infrastructure problems တွေနှင့် သူတို့၏
> common causes တွေကို အကျဉ်းချုပ်ပေးပါ။

ဟု မေးသည်ဆိုပါစို့။ ဤမေးခွန်းကို ဖြေရန် document တစ်ခုတည်းထဲက paragraph တစ်ခုကို
ရှာရုံနှင့် မလုံလောက်နိုင်ပါ။ Knowledge base ထဲတွင်ရှိသည့် information အများအပြားကို
ပေါင်းစပ်ပြီး အကျဉ်းချုပ်ရန် လိုလာနိုင်သည်။

GraphRAG ၏ community summary retrieval ပုံစံတွင် Graph ထဲက ဆက်စပ်နေသော entities နှင့်
relationships တွေကို community အုပ်စုများအဖြစ် စုစည်းထားပြီး ထို community summary တွေကို
အသုံးပြုနိုင်သည်။

အရေးကြီးခြင်းက ဤ code တွင် ပထမ condition မပြည့်မှသာ ဒုတိယ condition ကို စစ်ဆေးသည်။
အကြောင်းရင်းတွင် `return` ကို ရောက်သွားလျှင် function က result ကို ပြန်ပေးပြီး
ရပ်သွားသောကြောင့် ဖြစ်သည်။

---

## 6. တတိယ `if` condition — Text-to-Cypher

```python
if features["needs_structured_filter"]:
    return "Text-to-Cypher"
```

ဤ condition က structured filtering လိုအပ်သလား စစ်ဆေးသည်။

ဥပမာ Query တစ်ခုက —

> Production environment တွင်ရှိသည့် Kubernetes clusters တွေထဲက CPU usage 80% ကျော်နေသော
> cluster တွေကို ပြပေးပါ။

ဤမေးခွန်းတွင် စစ်ဆေးရန် လိုအပ်သော criteria တွေက —

- Environment က `production` ဖြစ်ရမည်။
- CPU usage က `80%` ထက်ကြီးရမည်။

ဤသို့ structured conditions တွေကို data ထဲတွင် တိတိကျကျ ရှာဖွေရန် လိုအပ်သောအခါ
Text-to-Cypher နည်းလမ်းကို သုံးနိုင်သည်။

Cypher သည် Neo4j လို graph databases တွေတွင် Graph data ကို ရှာဖွေ၊ စစ်ထုတ်ရန်
အသုံးပြုနိုင်သည့် query language ဖြစ်သည်။ Text-to-Cypher သည် natural-language
မေးခွန်းကို Cypher query အဖြစ် ပြောင်းပေးသည့် နည်းလမ်းကို ဆိုလိုသည်။

ဥပမာ ရိုးရှင်းသော Cypher query တစ်ခုက —

```cypher
MATCH (c:Cluster)
WHERE c.environment = "production"
  AND c.cpu_usage > 80
RETURN c
```

ဤဥပမာက `Cluster` entities တွေထဲတွင် `production` environment ဖြစ်ပြီး CPU usage `80`
ထက်ကြီးသည့် records တွေကို ရှာဖွေရန် ရည်ရွယ်ထားသည်။

ဤ exercise ၏ Python code က Cypher ကို တကယ် generate လုပ်ခြင်း၊ သို့မဟုတ် query ကို
database ပေါ်တွင် run လုပ်ခြင်း မဟုတ်ပါ။ `needs_structured_filter` က `True` ဖြစ်လျှင်
`"Text-to-Cypher"` ဆိုသည့် label ကိုသာ ပြန်ပေးသည်။

Production system တွင် LLM က generate လုပ်ထားသော database queries တွေကို execute မလုပ်ခင်
validate လုပ်ရန်၊ permissions ကန့်သတ်ရန်နှင့် read-only access အသုံးပြုရန် စဉ်းစားသင့်သည်။

---

## 7. နောက်ဆုံး `return` — Vector Search / Plain RAG

```python
return "Vector Search - plain RAG"
```

ဤသို့ `return` ကို `if` condition တွေ၏ အပြင်ဘက်တွင် ရေးထားသည်။ ထို့ကြောင့် အရင်
condition သုံးခုစလုံး မပြည့်မီသောအခါ ဤ result ကို **default** အနေနှင့် ပြန်ပေးသည်။

ထို condition သုံးခုက —

- Multi-hop relationship retrieval ကို မလိုအပ်ပါ။
- Corpus-wide summary ကို မလိုအပ်ပါ။
- Structured filtering ကို မလိုအပ်ပါ။

ဆိုလျှင် `"Vector Search - plain RAG"` ကို ရွေးချယ်သည်။

ဥပမာ User က —

> How do I restart a Kubernetes Deployment?

ဟု မေးသည်ဆိုပါစို့။ Knowledge base ထဲက သက်ဆိုင်သော text chunks တွေကို embedding
similarity အပေါ်မူတည်ပြီး ရှာဖွေရန် လိုအပ်နိုင်သည်။ ဤအခါ Vector Search / Plain RAG က
သင့်တော်သော default ရွေးချယ်မှု ဖြစ်နိုင်သည်။

အခု Function တစ်ခုလုံးကို ပြန်ကြည့်ကြပါမည်။

### Function တစ်ခုလုံး၏ ပုံစံ

```python
def select_modality(features):
    """Choose the cheapest retrieval modality that satisfies the query features."""

    if features["hop_count"] >= 2 and features["spans_documents"]:
        return "GraphRAG - entity-anchored subgraph retrieval"

    if features["needs_corpus_wide_summary"]:
        return "GraphRAG - community summary retrieval"

    if features["needs_structured_filter"]:
        return "Text-to-Cypher"

    return "Vector Search - plain RAG"
```

မှတ်ချက် — Docstring တွင် "cheapest retrieval modality" ဟု ရေးထားပေမဲ့ ဤ code က
retrieval နည်းလမ်းတစ်ခုချင်းစီ၏ တကယ့်ကုန်ကျစရိတ်ကို တွက်ချက်ခြင်း မဟုတ်ပါ။
သတ်မှတ်ထားသော condition တွေနှင့် အစီအစဉ်အရ ရွေးချယ်ခြင်းဖြစ်သည်။ တကယ့် cheapest modality
ကို ရွေးချယ်ရန် latency၊ compute cost၊ token usage နှင့် retrieval quality စသည့်အချက်တွေကိုပါ
ထည့်သွင်းစဉ်းစားရန် လိုသည်။

---

## 8. `QUERIES` — စမ်းသပ်မည့် Query များ

```python
QUERIES = [
    ("Q1", {
        "hop_count": 0,
        "spans_documents": False,
        "needs_corpus_wide_summary": False,
        "needs_structured_filter": False
    }),
    ("Q2", {
        "hop_count": 3,
        "spans_documents": True,
        "needs_corpus_wide_summary": False,
        "needs_structured_filter": False
    }),
    ("Q3", {
        "hop_count": 1,
        "spans_documents": False,
        "needs_corpus_wide_summary": True,
        "needs_structured_filter": False
    }),
    ("Q4", {
        "hop_count": 0,
        "spans_documents": False,
        "needs_corpus_wide_summary": False,
        "needs_structured_filter": True
    }),
]
```

ဤတွင် `QUERIES` က **list တစ်ခု** ဖြစ်သည်။ List ထဲတွင် tuple ၄ ခု ပါဝင်ပြီး တစ်ခုချင်းစီတွင် —

- Query ID
- Query features dictionary

တို့ ပါဝင်သည်။ ဥပမာ —

```python
("Q1", {
    "hop_count": 0,
    "spans_documents": False,
    "needs_corpus_wide_summary": False,
    "needs_structured_filter": False
})
```

ဤ tuple တွင် `"Q1"` က Query ၏ ID ဖြစ်ပြီး ဒုတိယ item က Query ၏ features တွေဖြစ်သည်။

Q1 ၏ features အားလုံးက ပထမသုံးခုသော routing conditions တွေကို မပြည့်မီပါ။ ထို့ကြောင့်
default ဖြစ်သည့် Vector Search ကို ရွေးချယ်ရမည်။

---

## 9. Query တစ်ခုချင်းစီအတွက် Modality ရွေးချယ်ခြင်း

### Q1 — Plain RAG

Features အားလုံးက ရှုပ်ထွေးသည့် retrieval နည်းလမ်းတွေကို မလိုအပ်ကြောင်း ဖော်ပြထားသည်။

- `hop_count = 0`
- `spans_documents = False`
- `needs_corpus_wide_summary = False`
- `needs_structured_filter = False`

**Result:** `Vector Search - plain RAG`

### Q2 — Entity-Anchored GraphRAG

Relationship hops 3 ခု လိုအပ်ပြီး Documents များစွာကို ချိတ်ဆက်စဉ်းစားရသည်။

- `hop_count = 3`
- `spans_documents = True`

**Result:** `GraphRAG - entity-anchored subgraph retrieval`

### Q3 — Community Summary GraphRAG

ဤ Query တွင် corpus-wide summary လိုအပ်ကြောင်း သတ်မှတ်ထားသည်။

- `hop_count = 1`
- `needs_corpus_wide_summary = True`

**Result:** `GraphRAG - community summary retrieval`

### Q4 — Text-to-Cypher

Structured filtering လိုအပ်သည်။

- `needs_structured_filter = True`

**Result:** `Text-to-Cypher`

---

## 10. `for query_id, features in QUERIES`

Code ၏ နောက်ဆုံးအပိုင်းက ဤသို့ဖြစ်သည်။

```python
for query_id, features in QUERIES:
    print("%s -> %s" % (query_id, select_modality(features)))
```

ဤ loop က Query ၄ ခုလုံးကို တစ်ခုချင်းစီ ယူပြီး modality ကို ရွေးချယ်ပေးသည်။

### 10.1 Tuple unpacking

```python
for query_id, features in QUERIES:
```

`QUERIES` ထဲက tuple တစ်ခုချင်းစီကို variable နှစ်ခုထဲ ခွဲထည့်သည်။ ဥပမာ —

```python
("Q1", {
    "hop_count": 0,
    "spans_documents": False,
    "needs_corpus_wide_summary": False,
    "needs_structured_filter": False
})
```

ဤ tuple ကို ယူလိုက်သည့်အခါ —

- `query_id` ထဲကို `"Q1"` ဝင်လာမည်။
- `features` ထဲကို dictionary ဝင်လာမည်။

၎င်းသည် အရင် Python သင်ခန်းစာတွင် လေ့လာခဲ့သည့် unpacking concept နှင့် အတူတူပင်။

### 10.2 `select_modality(features)`

```python
select_modality(features)
```

ဤ function call က လက်ရှိ Query ၏ features တွေကို function ထဲပို့ပြီး သင့်တော်သော modality
label ကို ပြန်ယူသည်။

Q1 အတွက်ဆိုလျှင် —

```python
print(select_modality({
    "hop_count": 0,
    "spans_documents": False,
    "needs_corpus_wide_summary": False,
    "needs_structured_filter": False
}))
```

Result (`print()` ဖြင့် function က ပြန်ပေးသည့် တန်ဖိုးကို screen ပေါ်တွင် ဖော်ပြထားသည်) —

```text
Vector Search - plain RAG
```

အလားတူ Q2၊ Q3 နှင့် Q4 ကိုလည်း တစ်ခုချင်းစီ စစ်ဆေးသွားသည်။

### 10.3 `print("%s -> %s" % (...))`

```python
print("%s -> %s" % (query_id, select_modality(features)))
```

၎င်းသည် string formatting ဖြစ်သည်။

- ပထမ `%s` — Query ID ကို ထည့်ပေးသည်။
- `->` — Query နှင့် ရွေးချယ်ထားသော modality ကို ဆက်စပ်ပြသည်။
- ဒုတိယ `%s` — Function က ပြန်ပေးသည့် modality အမည်ကို ထည့်သည်။

ဥပမာ —

```python
query_id = "Q1"
modality = "Vector Search - plain RAG"

print("%s -> %s" % (query_id, modality))
```

Output —

```text
Q1 -> Vector Search - plain RAG
```

ဤနည်းက ရှင်းလင်းသည့် output တစ်ခုကို ပြသပေးသည်။

---

## 11. Code တစ်ခုလုံး၏ Expected Output

အပိုင်း ၂ မှ ၁၀ အထိ ရှင်းပြခဲ့သည့် အစိတ်အပိုင်းအားလုံးကို ပေါင်းစည်းလိုက်ပါက runnable
script တစ်ခု အပြည့်အစုံ ရရှိသည် —

```python
def select_modality(features):
    """Choose the cheapest retrieval modality that satisfies the query features."""
    if features["hop_count"] >= 2 and features["spans_documents"]:
        return "GraphRAG - entity-anchored subgraph retrieval"
    if features["needs_corpus_wide_summary"]:
        return "GraphRAG - community summary retrieval"
    if features["needs_structured_filter"]:
        return "Text-to-Cypher"
    return "Vector Search - plain RAG"

QUERIES = [
    ("Q1", {"hop_count": 0, "spans_documents": False, "needs_corpus_wide_summary": False,
            "needs_structured_filter": False}),
    ("Q2", {"hop_count": 3, "spans_documents": True, "needs_corpus_wide_summary": False,
            "needs_structured_filter": False}),
    ("Q3", {"hop_count": 1, "spans_documents": False, "needs_corpus_wide_summary": True,
            "needs_structured_filter": False}),
    ("Q4", {"hop_count": 0, "spans_documents": False, "needs_corpus_wide_summary": False,
            "needs_structured_filter": True}),
]

for query_id, features in QUERIES:
    print("%s -> %s" % (query_id, select_modality(features)))
```

Terminal တွင် ဤသို့ ပြပါမည် —

```text
Q1 -> Vector Search - plain RAG
Q2 -> GraphRAG - entity-anchored subgraph retrieval
Q3 -> GraphRAG - community summary retrieval
Q4 -> Text-to-Cypher
```

---

## 12. အရေးကြီးဆုံး Python concept — `if` အစီအစဉ်

ဤ code တွင် `if` condition တွေ အစီအစဉ်လိုက် ရှိနေခြင်းက အရေးကြီးသည်။

ဥပမာ ဤ features တွေကို စဉ်းစားကြည့်ပါ။

```python
features = {
    "hop_count": 3,
    "spans_documents": True,
    "needs_corpus_wide_summary": True,
    "needs_structured_filter": True,
}
```

ဤ Query တွင် condition သုံးခုစလုံး ပြည့်မီသည်။ သို့သော် ပထမ `if` condition က
အောင်မြင်သွားခြင်းနှင့် —

```python
return "GraphRAG - entity-anchored subgraph retrieval"
```

function က ရပ်သွားပါလိမ့်မည်။ နောက်ထပ် condition တွေကို ဆက်စစ်တော့တွင် မဟုတ်ပါ။

ထို့ကြောင့် ဤ code သည် condition တွေကို အစဉ်လိုက် စစ်ဆေးပြီး ပထမဆုံး ပြည့်မီသော rule ကိုသာ
ရွေးချယ်သည့် **rule-based router** ဖြစ်သည်။

တကယ့် production system တစ်ခုတွင် Query တွင် လိုအပ်ချက်အများအပြား ရှိလာနိုင်ခြင်းကြောင့်
rule precedence ကို ဂရုတစိုက် သတ်မှတ်ရပါမည်။ တချို့ system တွေတွင် modality တစ်ခုတည်းကို
မရွေးဘဲ **Hybrid Retrieval** အနေနှင့် နည်းလမ်းအများအပြားကို ပေါင်းစပ်နိုင်သည်။

---

## 13. ကိုယ်တိုင်လေ့ကျင့်ကြည့်ပါ

**မေးခွန်း** — အောက်ပါ Query features ကို function ထဲ ပေးလိုက်လျှင် ဘယ် Modality ကို
ပြန်ပေးမလဲ။

```python
{
    "hop_count": 0,
    "spans_documents": False,
    "needs_corpus_wide_summary": False,
    "needs_structured_filter": True
}
```

1. `Vector Search - plain RAG`
2. `GraphRAG - community summary retrieval`
3. `Text-to-Cypher`
4. `GraphRAG - entity-anchored subgraph retrieval`

<details>
<summary>အဖြေ ကြည့်ရန်</summary>

**အဖြေ — 3. `Text-to-Cypher`**

အကြောင်းရင်း — Condition တစ်ခုချင်းစီကို အစဉ်လိုက် စစ်ဆေးသည် —

1. `hop_count = 0` ဖြစ်သဖြင့် `0 >= 2` သည် `False` — ပထမ `if` မပြည့်မီပါ။
2. `needs_corpus_wide_summary = False` — ဒုတိယ `if` လည်း မပြည့်မီပါ။
3. `needs_structured_filter = True` — တတိယ `if` ပြည့်မီသဖြင့် `"Text-to-Cypher"` ပြန်ပေးသည်။

ဤ features သည် `QUERIES` ထဲက **Q4** နှင့် တူညီသည်။

</details>

**အဓိက မှတ်ထားရန်** — Exercise 1 တွင် Pipeline stages တွေကို dependency အရ စီခဲ့သည်။
Exercise 2 တွင် Vector similarity score တွေကို ranking လုပ်ခဲ့သည်။ ဤ Exercise 3 တွင်
Query features တွေအပေါ် မူတည်ပြီး retrieval နည်းလမ်းကို ရွေးချယ်ရန် Python `if` statements
နှင့် rule-based routing ကို တည်ဆောက်ခဲ့သည်။ ဤ concept တွေကို ပေါင်းစပ်လိုက်လျှင် RAG
system တစ်ခု၏ retrieval workflow ကို ပိုမိုထိရောက်အောင် ဒီဇိုင်းလုပ်နိုင်သည်။
