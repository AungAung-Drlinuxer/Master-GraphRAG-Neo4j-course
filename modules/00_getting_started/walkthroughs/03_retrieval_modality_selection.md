# Walkthrough 03 — Retrieval Modality Selection (Exercise 3)

> ဤဖိုင်သည် `solution.md` ၏ Exercise 3 ကို **Python အခြေခံမှ စ၍** အပိုင်းလိုက် ရှင်းပြသည့်
> walkthrough ဖြစ်သည်။ Format သည် `walkthroughs/01_pipeline_stage_ordering.md` နှင့်
> `walkthroughs/02_cosine_similarity_ranking.md` တို့နှင့် တူညီသည်။

---

ဒီ exercise မှာ Python ကို အသုံးပြုပြီး User ရဲ့ မေးခွန်းအမျိုးအစားနဲ့ လိုအပ်ချက်အပေါ် မူတည်ကာ
ဘယ် Retrieval နည်းလမ်းကို ရွေးချယ်မလဲဆိုတာ ဆုံးဖြတ်ခြင်း ကို လေ့လာပါမယ်။

အရင် Exercise 2 မှာ Cosine Similarity ကို အသုံးပြုပြီး Query နဲ့ အနီးစပ်ဆုံးတူညီတဲ့ chunks တွေကို
Ranking လုပ်ခဲ့ပါတယ်။ ဒီ Exercise 3 မှာတော့ နောက်တစ်ဆင့်တက်ပြီး Query တစ်ခုချင်းစီအတွက် ဘယ်
Retrieval Modality ကို အသုံးပြုသင့်သလဲဆိုတာ စည်းမျဉ်းအလိုက် ရွေးချယ်မှာ ဖြစ်ပါတယ်။

RAG system တစ်ခုမှာ Query အားလုံးကို Vector Search တစ်မျိုးတည်းနဲ့ ဖြေရှင်းဖို့ မလိုအပ်ပါဘူး။
ရိုးရှင်းတဲ့ မေးခွန်းတွေအတွက် Vector Search လုံလောက်နိုင်ပေမဲ့၊ Documents အများအပြားက
information တွေကို ဆက်စပ်ရှာရမယ့် မေးခွန်းတွေမှာ GraphRAG က ပိုသင့်တော်နိုင်ပါတယ်။
Structured data ကို တိကျတဲ့ condition အလိုက် စစ်ထုတ်ရမယ့် မေးခွန်းတွေအတွက် Text-to-Cypher
ကို အသုံးပြုနိုင်ပါတယ်။

ဒီ code မှာ လေ့လာရမယ့် Python concepts တွေကတော့ function၊ dictionary၊ `if`၊ `and`၊ `return`၊
list of tuples၊ `for` loop နဲ့ unpacking တို့ ဖြစ်ပါတယ်။

---

## 1. Retrieval Modality ဆိုတာဘာလဲ။

Retrieval Modality ဆိုတာ မေးခွန်းတစ်ခုအတွက် သက်ဆိုင်ရာ information ကို ရှာဖွေရန်
အသုံးပြုမယ့် နည်းလမ်းအမျိုးအစားကို ဆိုလိုပါတယ်။

```text
                        User Query
                            |
                            v
                 Feature-based Router
              (Python ရဲ့ condition တွေ စစ်ဆေးခြင်း)
                            |
          +-----------------+-----------------+
          |                 |                 |
          v                 v                 v
   Vector Search        GraphRAG        Text-to-Cypher
```

| Modality | အခြေခံသည် | အသုံးပြုသည့်နေရာ |
| --- | --- | --- |
| Vector Search | Semantic similarity | ရိုးရှင်းသော မေးခွန်းများ — Plain RAG |
| GraphRAG | Entities နဲ့ relationships | Multi-hop နှင့် corpus-wide မေးခွန်းများ |
| Text-to-Cypher | Graph database query | Structured filtering |
| Plain RAG | Documents / text chunks | Vector Search ရလဒ်ကို LLM ထံ ပေးသည့် pipeline |

ဒီ code က retrieval နည်းလမ်းတွေကို တကယ် run မလုပ်သေးပါဘူး။ ဘယ်နည်းလမ်းကို
အသုံးပြုသင့်သလဲဆိုတာကို ရွေးချယ်ပေးတဲ့ **routing logic** ကိုသာ ဖော်ပြထားတာ ဖြစ်ပါတယ်။

---

## 2. `select_modality(features)` function

အရင်ဆုံး function ကို ကြည့်ရအောင်။

```python
def select_modality(features):
    """Choose the cheapest retrieval modality that satisfies the query features."""
```

ဒီမှာ `select_modality` ဆိုတဲ့ function ကို သတ်မှတ်ထားပါတယ်။

- `select_modality` — Function အမည်။
- `features` — Query တစ်ခုရဲ့ လိုအပ်ချက်တွေကို သိမ်းထားတဲ့ dictionary။
- `"""..."""` — Function ရဲ့ ရည်ရွယ်ချက်ကို ရှင်းပြထားတဲ့ docstring။

Function ကို ခေါ်တဲ့အခါ `features` ထဲမှာ ဘယ်လို data တွေ ပါလာမလဲဆိုတာက ဒီ Exercise ရဲ့
အဓိကအချက် ဖြစ်ပါတယ်။

ဥပမာ —

```python
features = {
    "hop_count": 3,
    "spans_documents": True,
    "needs_corpus_wide_summary": False,
    "needs_structured_filter": False,
}
```

ဒီ dictionary က Query တစ်ခုမှာ document များစွာကြား relationship တွေကို လိုက်ရှာဖို့
လိုအပ်နေကြောင်း ဖော်ပြထားပါတယ်။

> **မှတ်ချက်** — ဤနေရာတွင် function ၏ ခေါင်းစီး (signature) နှင့် docstring ကိုသာ ပြထားသည်။
> Body ကို အပိုင်း ၄ မှ ၇ အထိ တစ်ကြောင်းချင်း ရှင်းပြထားပြီး၊ Function အပြည့်အစုံကို
> အပိုင်း ၇ အကုန်တွင်လည်းကောင်း၊ runnable version ကို အပိုင်း ၁၁ တွင်လည်းကောင်း
> ဖော်ပြထားသည်။

---

## 3. `features` dictionary ကို နားလည်ခြင်း

ဒီ Exercise မှာ feature လေးခုကို သတ်မှတ်ထားပါတယ်။

| Feature | အဓိပ္ပာယ် |
| --- | --- |
| `hop_count` | Graph ထဲမှာ ဆက်စပ်နေတဲ့ entities တွေကြား လိုက်ရှာရမယ့် relationship hops အရေအတွက် |
| `spans_documents` | မေးခွန်းအတွက် Documents တစ်ခုထက်ပိုပြီး ချိတ်ဆက်စဉ်းစားရမလား |
| `needs_corpus_wide_summary` | Knowledge corpus တစ်ခုလုံး သို့မဟုတ် အပိုင်းအခြားကြီးတစ်ခုကို အကျဉ်းချုပ်ဖို့ လိုသလား |
| `needs_structured_filter` | Property၊ field၊ condition တို့အပေါ် မူတည်ပြီး structured records တွေကို စစ်ထုတ်ဖို့ လိုသလား |

ဥပမာ `"hop_count": 3` ဆိုတာ Graph ထဲမှာ relationship သုံးခုအထိ ဖြတ်သန်းရှာဖို့ လိုအပ်တယ်လို့
ယူဆထားတာပါ။

`True` နဲ့ `False` တို့က Boolean values ဖြစ်ပါတယ်။

```python
"spans_documents": True
```

ဆိုရင် Documents များစွာကို ချိတ်ဆက်စဉ်းစားဖို့ လိုအပ်တယ်လို့ သတ်မှတ်ထားတာပါ။

```python
"spans_documents": False
```

ဆိုရင် အဲဒီ feature ကို မလိုအပ်ဘူးလို့ သတ်မှတ်ထားတာ ဖြစ်ပါတယ်။

မှတ်သားရန် — ဒီ feature တွေကို code ထဲမှာ ကြိုတင်ပေးထားပါတယ်။ Production system တစ်ခုမှာ
ဒီလို features တွေကို Query classifier၊ LLM-based router သို့မဟုတ် သီးခြားစည်းမျဉ်းတွေကနေ
ထုတ်ယူနိုင်ပါတယ်။

---

## 4. ပထမဆုံး `if` condition — GraphRAG: Entity-Anchored Subgraph Retrieval

```python
if features["hop_count"] >= 2 and features["spans_documents"]:
    return "GraphRAG - entity-anchored subgraph retrieval"
```

ဒီအပိုင်းကို အဆင့်လိုက် ခွဲရှင်းကြည့်ရအောင်။

### 4.1 `features["hop_count"] >= 2`

```python
features["hop_count"] >= 2
```

- `features["hop_count"]` က dictionary ထဲက `hop_count` တန်ဖိုးကို ရယူပါတယ်။
- `>=` က greater than or equal to ဖြစ်ပြီး "ထက်ကြီး သို့မဟုတ် ညီမျှ" လို့ အဓိပ္ပာယ်ရပါတယ်။

ဥပမာ —

```python
print(3 >= 2)   # True
print(2 >= 2)   # True
print(1 >= 2)   # False
```

ဒါကြောင့် Query မှာ Graph relationship နှစ်ခုနှင့်အထက်ကို လိုက်ရှာဖို့ လိုတယ်လို့
သတ်မှတ်ထားသလား စစ်ဆေးတာ ဖြစ်ပါတယ်။

### 4.2 `and features["spans_documents"]`

```python
features["hop_count"] >= 2 and features["spans_documents"]
```

`and` ဆိုတာ condition နှစ်ခုစလုံး မှန်မှသာ `True` ဖြစ်ပါတယ်။

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

ဒါပေမဲ့ —

```python
hop_count = 3
spans_documents = False

print(hop_count >= 2 and spans_documents)
```

Output —

```text
False
```

ဒီ condition က အချက်နှစ်ချက်လုံးကို လိုအပ်ပါတယ်။

- `hop_count` က `2` သို့မဟုတ် အထက် ဖြစ်ရမယ်။
- `spans_documents` က `True` ဖြစ်ရမယ်။

အချက်နှစ်ချက်လုံး ပြည့်မီရင် —

```python
return "GraphRAG - entity-anchored subgraph retrieval"
```

ဆိုပြီး ဒီ Retrieval Modality ကို ရွေးချယ်ကာ function ရဲ့ result ကို ပြန်ပေးပါတယ်။

### Entity-Anchored Subgraph Retrieval ဆိုတာဘာလဲ။

GraphRAG က Knowledge Graph ထဲမှာ entities တွေ၊ သူတို့အကြား relationships တွေကို
အသုံးပြုပြီး ရှာဖွေနိုင်ပါတယ်။

ဥပမာ IT environment မှာ —

```text
Application A → runs on → Kubernetes Cluster B → connects to → Database C
```

ဆိုတဲ့ relationships တွေ ရှိတယ်လို့ ယူဆကြည့်ပါ။ User က "Application A က ဘယ် Database ကို
အသုံးပြုနေလဲ" လို့ မေးတဲ့အခါ အစရှိတဲ့ entity တစ်ခုကနေ စတင်ပြီး relationships တွေကို
လိုက်ရှာနိုင်ပါတယ်။

ဒီလို သတ်မှတ်ထားတဲ့ entity တစ်ခုကို အစပြုကာ သက်ဆိုင်ရာ subgraph ကို ရှာတဲ့ပုံစံကို
**entity-anchored subgraph retrieval** လို့ ခေါ်ပါတယ်။

---

## 5. ဒုတိယ `if` condition — GraphRAG: Community Summary Retrieval

```python
if features["needs_corpus_wide_summary"]:
    return "GraphRAG - community summary retrieval"
```

ဒီ condition က Query မှာ corpus တစ်ခုလုံး၊ ဒါမှမဟုတ် knowledge graph ရဲ့
အပိုင်းအခြားကြီးတစ်ခုအကြောင်း အကျဉ်းချုပ်ဖို့ လိုသလား စစ်ဆေးပါတယ်။

```python
features["needs_corpus_wide_summary"]
```

ဒီ value က `True` ဖြစ်ရင် အောက်ပါ result ကို ပြန်ပေးပါမယ်။

```python
return "GraphRAG - community summary retrieval"
```

ဥပမာ User က —

> Our IT knowledge base ထဲက အများဆုံးတွေ့ရတဲ့ infrastructure problems တွေနဲ့ သူတို့ရဲ့
> common causes တွေကို အကျဉ်းချုပ်ပေးပါ။

လို့ မေးတယ်ဆိုပါစို့။ ဒီမေးခွန်းကို ဖြေဖို့ document တစ်ခုတည်းထဲက paragraph တစ်ခုကို
ရှာရုံနဲ့ မလုံလောက်နိုင်ပါဘူး။ Knowledge base ထဲမှာရှိတဲ့ information အများအပြားကို
ပေါင်းစပ်ပြီး အကျဉ်းချုပ်ဖို့ လိုလာနိုင်ပါတယ်။

GraphRAG ရဲ့ community summary retrieval ပုံစံမှာ Graph ထဲက ဆက်စပ်နေတဲ့ entities နဲ့
relationships တွေကို community အုပ်စုများအဖြစ် စုစည်းထားပြီး အဲဒီ community summary တွေကို
အသုံးပြုနိုင်ပါတယ်။

အရေးကြီးတာက ဒီ code မှာ ပထမ condition မပြည့်မှသာ ဒုတိယ condition ကို စစ်ဆေးပါတယ်။
ဘာကြောင့်လဲဆိုတော့ `return` ကို ရောက်သွားရင် function က result ကို ပြန်ပေးပြီး
ရပ်သွားလို့ပါ။

---

## 6. တတိယ `if` condition — Text-to-Cypher

```python
if features["needs_structured_filter"]:
    return "Text-to-Cypher"
```

ဒီ condition က structured filtering လိုအပ်သလား စစ်ဆေးပါတယ်။

ဥပမာ Query တစ်ခုက —

> Production environment မှာရှိတဲ့ Kubernetes clusters တွေထဲက CPU usage 80% ကျော်နေတဲ့
> cluster တွေကို ပြပေးပါ။

ဒီမေးခွန်းမှာ စစ်ဆေးဖို့ လိုအပ်တဲ့ criteria တွေက —

- Environment က `production` ဖြစ်ရမယ်။
- CPU usage က `80%` ထက်ကြီးရမယ်။

ဒီလို structured conditions တွေကို data ထဲမှာ တိတိကျကျ ရှာဖွေဖို့ လိုအပ်တဲ့အခါ
Text-to-Cypher နည်းလမ်းကို သုံးနိုင်ပါတယ်။

Cypher ဆိုတာ Neo4j လို graph databases တွေမှာ Graph data ကို ရှာဖွေ၊ စစ်ထုတ်ဖို့
အသုံးပြုနိုင်တဲ့ query language ဖြစ်ပါတယ်။ Text-to-Cypher ဆိုတာ natural-language
မေးခွန်းကို Cypher query အဖြစ် ပြောင်းပေးတဲ့ နည်းလမ်းကို ဆိုလိုပါတယ်။

ဥပမာ ရိုးရှင်းတဲ့ Cypher query တစ်ခုက —

```cypher
MATCH (c:Cluster)
WHERE c.environment = "production"
  AND c.cpu_usage > 80
RETURN c
```

ဒီဥပမာက `Cluster` entities တွေထဲမှာ `production` environment ဖြစ်ပြီး CPU usage `80`
ထက်ကြီးတဲ့ records တွေကို ရှာဖွေဖို့ ရည်ရွယ်ထားပါတယ်။

ဒီ exercise ရဲ့ Python code က Cypher ကို တကယ် generate လုပ်တာ၊ ဒါမှမဟုတ် query ကို
database ပေါ်မှာ run လုပ်တာ မဟုတ်ပါဘူး။ `needs_structured_filter` က `True` ဖြစ်ရင်
`"Text-to-Cypher"` ဆိုတဲ့ label ကိုသာ ပြန်ပေးပါတယ်။

Production system မှာ LLM က generate လုပ်ထားတဲ့ database queries တွေကို execute မလုပ်ခင်
validate လုပ်ဖို့၊ permissions ကန့်သတ်ဖို့နဲ့ read-only access အသုံးပြုဖို့ စဉ်းစားသင့်ပါတယ်။

---

## 7. နောက်ဆုံး `return` — Vector Search / Plain RAG

```python
return "Vector Search - plain RAG"
```

ဒီလို `return` ကို `if` condition တွေရဲ့ အပြင်ဘက်မှာ ရေးထားပါတယ်။ ဒါကြောင့် အရင်
condition သုံးခုစလုံး မပြည့်မီတဲ့အခါ ဒီ result ကို **default** အနေနဲ့ ပြန်ပေးပါတယ်။

အဲဒီ condition သုံးခုက —

- Multi-hop relationship retrieval ကို မလိုအပ်ဘူး။
- Corpus-wide summary ကို မလိုအပ်ဘူး။
- Structured filtering ကို မလိုအပ်ဘူး။

ဆိုရင် `"Vector Search - plain RAG"` ကို ရွေးချယ်ပါတယ်။

ဥပမာ User က —

> How do I restart a Kubernetes Deployment?

လို့ မေးတယ်ဆိုပါစို့။ Knowledge base ထဲက သက်ဆိုင်တဲ့ text chunks တွေကို embedding
similarity အပေါ်မူတည်ပြီး ရှာဖွေဖို့ လိုအပ်နိုင်ပါတယ်။ ဒီအခါ Vector Search / Plain RAG က
သင့်တော်တဲ့ default ရွေးချယ်မှု ဖြစ်နိုင်ပါတယ်။

အခု Function တစ်ခုလုံးကို ပြန်ကြည့်ရအောင်။

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

မှတ်ချက် — Docstring မှာ "cheapest retrieval modality" လို့ ရေးထားပေမဲ့ ဒီ code က
retrieval နည်းလမ်းတစ်ခုချင်းစီရဲ့ တကယ့်ကုန်ကျစရိတ်ကို တွက်ချက်တာ မဟုတ်ပါဘူး။
သတ်မှတ်ထားတဲ့ condition တွေနဲ့ အစီအစဉ်အရ ရွေးချယ်တာဖြစ်ပါတယ်။ တကယ့် cheapest modality
ကို ရွေးချယ်ဖို့ latency၊ compute cost၊ token usage နဲ့ retrieval quality စတဲ့အချက်တွေကိုပါ
ထည့်သွင်းစဉ်းစားဖို့ လိုပါတယ်။

---

## 8. `QUERIES` — စမ်းသပ်မယ့် Query များ

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

ဒီမှာ `QUERIES` က **list တစ်ခု**ပါ။ List ထဲမှာ tuple လေးခု ပါဝင်ပြီး တစ်ခုချင်းစီမှာ —

- Query ID
- Query features dictionary

တို့ ပါဝင်ပါတယ်။ ဥပမာ —

```python
("Q1", {
    "hop_count": 0,
    "spans_documents": False,
    "needs_corpus_wide_summary": False,
    "needs_structured_filter": False
})
```

ဒီ tuple မှာ `"Q1"` က Query ရဲ့ ID ဖြစ်ပြီး ဒုတိယ item က Query ရဲ့ features တွေဖြစ်ပါတယ်။

Q1 ရဲ့ features အားလုံးက ပထမသုံးခုသော routing conditions တွေကို မပြည့်မီပါဘူး။ ဒါကြောင့်
default ဖြစ်တဲ့ Vector Search ကို ရွေးချယ်ရမှာပါ။

---

## 9. Query တစ်ခုချင်းစီအတွက် Modality ရွေးချယ်ခြင်း

### Q1 — Plain RAG

Features အားလုံးက ရှုပ်ထွေးတဲ့ retrieval နည်းလမ်းတွေကို မလိုအပ်ကြောင်း ဖော်ပြထားပါတယ်။

- `hop_count = 0`
- `spans_documents = False`
- `needs_corpus_wide_summary = False`
- `needs_structured_filter = False`

**Result:** `Vector Search - plain RAG`

### Q2 — Entity-Anchored GraphRAG

Relationship hops 3 ခု လိုအပ်ပြီး Documents များစွာကို ချိတ်ဆက်စဉ်းစားရပါတယ်။

- `hop_count = 3`
- `spans_documents = True`

**Result:** `GraphRAG - entity-anchored subgraph retrieval`

### Q3 — Community Summary GraphRAG

ဒီ Query မှာ corpus-wide summary လိုအပ်ကြောင်း သတ်မှတ်ထားပါတယ်။

- `hop_count = 1`
- `needs_corpus_wide_summary = True`

**Result:** `GraphRAG - community summary retrieval`

### Q4 — Text-to-Cypher

Structured filtering လိုအပ်ပါတယ်။

- `needs_structured_filter = True`

**Result:** `Text-to-Cypher`

---

## 10. `for query_id, features in QUERIES`

Code ရဲ့ နောက်ဆုံးအပိုင်းက ဒီလိုဖြစ်ပါတယ်။

```python
for query_id, features in QUERIES:
    print("%s -> %s" % (query_id, select_modality(features)))
```

ဒီ loop က Query လေးခုလုံးကို တစ်ခုချင်းစီ ယူပြီး modality ကို ရွေးချယ်ပေးပါတယ်။

### 10.1 Tuple unpacking

```python
for query_id, features in QUERIES:
```

`QUERIES` ထဲက tuple တစ်ခုချင်းစီကို variable နှစ်ခုထဲ ခွဲထည့်ပါတယ်။ ဥပမာ —

```python
("Q1", {
    "hop_count": 0,
    "spans_documents": False,
    "needs_corpus_wide_summary": False,
    "needs_structured_filter": False
})
```

ဒီ tuple ကို ယူလိုက်တဲ့အခါ —

- `query_id` ထဲကို `"Q1"` ဝင်လာမယ်။
- `features` ထဲကို dictionary ဝင်လာမယ်။

ဒါဟာ အရင် Python သင်ခန်းစာမှာ လေ့လာခဲ့တဲ့ unpacking concept နဲ့ အတူတူပါပဲ။

### 10.2 `select_modality(features)`

```python
select_modality(features)
```

ဒီ function call က လက်ရှိ Query ရဲ့ features တွေကို function ထဲပို့ပြီး သင့်တော်တဲ့ modality
label ကို ပြန်ယူပါတယ်။

Q1 အတွက်ဆိုရင် —

```python
select_modality({
    "hop_count": 0,
    "spans_documents": False,
    "needs_corpus_wide_summary": False,
    "needs_structured_filter": False
})
```

Result (print မလုပ်ထားသဖြင့် screen ပေါ်တွင် မပေါ်ပါ — function က ပြန်ပေးသည့် တန်ဖိုးကို
ဖော်ပြထားသည်) —

```text
Vector Search - plain RAG
```

အလားတူ Q2၊ Q3 နဲ့ Q4 ကိုလည်း တစ်ခုချင်းစီ စစ်ဆေးသွားပါတယ်။

### 10.3 `print("%s -> %s" % (...))`

```python
print("%s -> %s" % (query_id, select_modality(features)))
```

ဒီဟာက string formatting ပါ။

- ပထမ `%s` — Query ID ကို ထည့်ပေးပါတယ်။
- `->` — Query နဲ့ ရွေးချယ်ထားတဲ့ modality ကို ဆက်စပ်ပြပါတယ်။
- ဒုတိယ `%s` — Function က ပြန်ပေးတဲ့ modality အမည်ကို ထည့်ပါတယ်။

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

ဒီနည်းက ရှင်းလင်းတဲ့ output တစ်ခုကို ပြသပေးပါတယ်။

---

## 11. Code တစ်ခုလုံးရဲ့ Expected Output

အပိုင်း ၂ မှ ၁၀ အထိ ရှင်းပြခဲ့သည့် အစိတ်အပိုင်းအားလုံးကို ပေါင်းစည်းလိုက်ပါက runnable
script တစ်ခု အပြည့်အစုံ ရရှိပါတယ် —

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

Terminal မှာ ဒီလို ပြပါမယ် —

```text
Q1 -> Vector Search - plain RAG
Q2 -> GraphRAG - entity-anchored subgraph retrieval
Q3 -> GraphRAG - community summary retrieval
Q4 -> Text-to-Cypher
```

---

## 12. အရေးကြီးဆုံး Python concept — `if` အစီအစဉ်

ဒီ code မှာ `if` condition တွေ အစီအစဉ်လိုက် ရှိနေခြင်းက အရေးကြီးပါတယ်။

ဥပမာ ဒီ features တွေကို စဉ်းစားကြည့်ပါ။

```python
features = {
    "hop_count": 3,
    "spans_documents": True,
    "needs_corpus_wide_summary": True,
    "needs_structured_filter": True,
}
```

ဒီ Query မှာ condition သုံးခုစလုံး ပြည့်မီပါတယ်။ ဒါပေမဲ့ ပထမ `if` condition က
အောင်မြင်သွားတာနဲ့ —

```python
return "GraphRAG - entity-anchored subgraph retrieval"
```

function က ရပ်သွားပါလိမ့်မယ်။ နောက်ထပ် condition တွေကို ဆက်စစ်တော့မှာ မဟုတ်ပါဘူး။

ဒါကြောင့် ဒီ code ဟာ condition တွေကို အစဉ်လိုက် စစ်ဆေးပြီး ပထမဆုံး ပြည့်မီတဲ့ rule ကိုသာ
ရွေးချယ်တဲ့ **rule-based router** ဖြစ်ပါတယ်။

တကယ့် production system တစ်ခုမှာ Query မှာ လိုအပ်ချက်အများအပြား ရှိလာနိုင်တာကြောင့်
rule precedence ကို ဂရုတစိုက် သတ်မှတ်ရပါမယ်။ တချို့ system တွေမှာ modality တစ်ခုတည်းကို
မရွေးဘဲ **Hybrid Retrieval** အနေနဲ့ နည်းလမ်းအများအပြားကို ပေါင်းစပ်နိုင်ပါတယ်။

---

## 13. ကိုယ်တိုင်လေ့ကျင့်ကြည့်ပါ

**မေးခွန်း** — အောက်ပါ Query features ကို function ထဲ ပေးလိုက်ရင် ဘယ် Modality ကို
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

**အဓိက မှတ်ထားရန်** — Exercise 1 မှာ Pipeline stages တွေကို dependency အရ စီခဲ့ပါတယ်။
Exercise 2 မှာ Vector similarity score တွေကို ranking လုပ်ခဲ့ပါတယ်။ ဒီ Exercise 3 မှာတော့
Query features တွေအပေါ် မူတည်ပြီး retrieval နည်းလမ်းကို ရွေးချယ်ဖို့ Python `if` statements
နဲ့ rule-based routing ကို တည်ဆောက်ခဲ့ပါတယ်။ ဒီ concept တွေကို ပေါင်းစပ်လိုက်ရင် RAG
system တစ်ခုရဲ့ retrieval workflow ကို ပိုမိုထိရောက်အောင် ဒီဇိုင်းလုပ်နိုင်ပါတယ်။
