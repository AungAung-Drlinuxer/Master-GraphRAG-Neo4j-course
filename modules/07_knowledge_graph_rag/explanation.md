# M07 — Knowledge Graph-based RAG: သဘောတရားရှင်းလင်းချက်

Vector RAG သည် query နှင့် အနီးစပ်ဆုံး chunk များကို ပြန်ပေးသည်။ သို့သော် ဖြေချက်သည် chunk တစ်ခုတည်းထဲ
မပါရှိဘဲ node နှစ်ခုကြား ဆက်စပ်မှုမှ ထွက်ပေါ်လာသောအခါ Vector RAG သည် recall ကို ဆုံးရှုံးသည်။
GraphRAG သည် Knowledge Graph ကို retrieval index အဖြစ် ထည့်သွင်းပြီး ထိုဆုံးရှုံးမှုကို ဖြည့်ဆည်းသည်။

---

## ၁။ GraphRAG Retrieval Pattern ၃ မျိုး

| Pattern | Retrieval unit | ဖြေဆိုနိုင်သော question အမျိုးအစား |
|---|---|---|
| Entity-anchored subgraph | Anchor node မှ k-hop အတွင်း triple များ | Multi-hop၊ entity-centric question |
| Text-to-Cypher | Graph ပေါ်ရှိ aggregate / filter query | အတိအကျ ရေတွက်ခြင်း၊ စစ်ထုတ်ခြင်း |
| Community-summary | Community တစ်ခုစီ၏ LLM summary | Global၊ corpus-level question |

**Engineering rationale** — pattern သုံးမျိုးသည် retrieval unit ကွာခြားသည်။ Entity-anchored subgraph သည်
precision မြင့်သော်လည်း anchor မတွေ့ပါက recall လုံးလုံး ပြိုလဲသည်။ Text-to-Cypher သည် exact answer
ပေးသော်လည်း schema drift နှင့် မမှန်သော generated Cypher အန္တရာယ် ရှိသည်။ Community-summary သည်
global question ကို ဖြေဆိုနိုင်သော်လည်း query တစ်ခုချင်းအတွက် precision နည်းသည်။

**ဘယ်အချိန် မသုံးသင့်သနည်း** — corpus သည် document ၅၀ အောက် ဖြစ်ပြီး question အားလုံး single-hop
ဖြစ်ပါက GraphRAG သည် entity linking error နှင့် graph maintenance cost ကို ပေါင်းထည့်ရုံသာ ဖြစ်သည်။
ထိုအခြေအနေတွင် vector-only baseline ကို ရွေးချယ်ရမည်။

---

## ၂။ Entity Linking — Query Text မှ Graph Node သို့

Entity linking သည် GraphRAG ၏ single point of failure ဖြစ်သည်။ မှားသော anchor သည် မှားသော subgraph
ကို ဆွဲထုတ်ပြီး LLM ကို မှားသော context ပေးသည်။ Deterministic baseline တစ်ခုကို အောက်ပါအတိုင်း
တည်ဆောက်နိုင်သည်။

```python
def fuzzy_score(surface, query):
    s, q = " ".join(tokenize(surface)), " ".join(tokenize(query))
    if not s:
        return 0.0
    if s in q:                      # surface သည် query ထဲ တိုက်ရိုက် ပါဝင်နေသည်
        return 1.0
    words = set(tokenize(surface))
    if not words:
        return 0.0
    overlap = len(words & set(tokenize(query))) / len(words)
    return round(max(overlap * 0.95, SequenceMatcher(None, s, q).ratio() * 0.6), 4)
```

Tokenizer သည် Unicode NFKD normalize လုပ်ပြီး ASCII အဖြစ် ချုံ့သည်။ ဤအဆင့်သည် accent နှင့်
case ကွာခြားချက်ကို ဖယ်ရှားပေးသော်လည်း Unicode-specific script (ဥပမာ မြန်မာစာ) တွင် information
ဆုံးရှုံးနိုင်သည်။ မြန်မာ entity များ ပါဝင်သော corpus တွင် ASCII fold ကို မသုံးသင့်ဘဲ original
codepoint ဖြင့် တိုက်ရိုက် normalize လုပ်ရမည်။

`lab.py` မှ တကယ်ရရှိသော output —

```text
query: How does Neo4j AuraDB use a vector index for retrieval?
  -> co:neo4j           score=1.0    surface='Neo4j'
  -> prod:aura          score=1.0    surface='Neo4j AuraDB'
  -> tech:vectorindex   score=1.0    surface='Vector Index'
```

**ဘယ်အချိန် မသုံးသင့်သနည်း** — ALIAS list ကို လက်ဖြင့် ထိန်းသိမ်းနိုင်သော entity အရေအတွက်
(တစ်ထောင်အောက်) အတွက် ဤ rule-based approach သည် လုံလောက်သည်။ Entity အရေအတွက် သောင်းချီသော
production တွင် embedding-based candidate generation ကို ရှေးဦး filter အဖြစ် ထည့်ရမည်၊
rule-based matching ကို second-stage verifier အဖြစ်သာ ထားရမည်။

---

## ၃။ Subgraph မှ Prompt Context သို့ Serialization

Triple များကို LLM သို့ တိုက်ရိုက် ပေးပို့နိုင်သည် မဟုတ်ဘဲ deterministic format တစ်ခုအဖြစ်
serialize လုပ်ရမည်။ Format မတည်ငြိမ်ပါက prompt သည် run တိုင်း ပြောင်းလဲပြီး evaluation ကို
ထပ်လုပ်နိုင်တော့မည် မဟုတ်။

Format နှစ်ပိုင်း ခွဲရမည် — entity line များ (node id ဖြင့် sort) နှင့် relation line များ
`(src, rel, dst)` ဖြင့် sort။

```text
[ENTITY] id=tech:cypher | label=Technology | name=Cypher | summary=Declarative graph query language.
[RELATION] co:neo4j -[CREATES]-> tech:cypher
[RELATION] co:neo4j -[DEVELOPS]-> prod:aura
```

Token estimate ကို `len(text) // 4` ဖြင့် ခန့်မှန်းပြီး `max_tokens` ကျော်ပါက ဖြတ်တောက်ရမည်။
`lab.py` တွင် 6 entities + 8 relations သည် `~256 tokens` ဖြစ်သည်။

**Engineering rationale** — Edge များကို hop count အလိုက် ဦးစားပေး မဖြတ်ဘဲ အစီအစဉ်အတိုင်း
ဖြတ်ခြင်းသည် အန္တရာယ်ရှိသည်၊ အဘယ်ကြောင့်ဆိုသော် context ရှိ node များ၏ relationship များ
တစ်စိတ်တစ်ပိုင်း ပြုတ်ကျသွားနိုင်သည်။ Anchor node ၏ အနီးဆုံး edge များကို ဦးစားပေး ထားရှိခြင်းသည်
ပိုမို ကောင်းသော recall ကို ပေးသည်။

---

## ၄။ Hybrid Retrieval — Vector Chunk နှင့် Graph Triple ၏ Fusion

Vector ranking နှင့် graph ranking သည် score scale မတူညီသောကြောင့် score ကို တိုက်ရိုက် ပေါင်း၍
မရပါ။ Reciprocal Rank Fusion (RRF) သည် rank ကိုသာ အသုံးပြုသောကြောင့် scale ပြဿနာကို ရှောင်သည်။

```text
score(item) = Σ_lists  1 / (k + rank_list(item))        k = 60
```

`lab.py` မှ တကယ်ရရှိသော output —

```text
  graph:0    rrf=0.016393  chunk=c1  Neo4j AuraDB is a managed cloud service that
  vec:c1     rrf=0.016393  chunk=c1  Neo4j AuraDB is a managed cloud service that
  graph:4    rrf=0.016129  chunk=c2  Cypher is the declarative query language cre
  vec:c4     rrf=0.016129  chunk=c4  The Louvain method optimises modularity to d
  graph:6    rrf=0.015873  chunk=c3  GraphRAG grounds generation in knowledge gra
  vec:c2     rrf=0.015873  chunk=c2  Cypher is the declarative query language cre
fused=['graph:0', 'vec:c1', 'graph:4', 'vec:c4', 'graph:6', 'vec:c2']
final=['graph:0', 'graph:4', 'vec:c4', 'graph:6']
```

`graph:0` နှင့် `vec:c1` သည် chunk `c1` တစ်ခုတည်းမှ ဆင်းသက်သည်။ ထို duplicate ကို ဖယ်ရှားခြင်းကို
provenance deduplication ဟုခေါ်ပြီး `final` သည် `fused` ထက် item ၂ ခု လျော့သည်။

**ဘယ်အချိန် မသုံးသင့်သနည်း** — Graph triple များသည် chunk များထက် ပိုတိကျသော်လည်း
extraction error ကို အမွေယူသည်။ Extraction precision 0.8 အောက် ရှိသော pipeline တွင် graph triple
များကို same-weight ဖြင့် ပေါင်းခြင်းသည် vector-only ထက် ဖြေချက် ပိုဆိုးစေနိုင်သည်။ ထိုအခါ
graph item များကို weight လျှော့၍ (ဥပမာ RRF score × 0.7) ပေါင်းရမည်။

---

## ၅။ Text-to-Cypher — Schema Prompt နှင့် Read-only Guardrail

Graph ပေါ်ရှိ အတိအကျ query အတွက် LLM သည် Cypher ကို generate လုပ်နိုင်သည်။ Schema ကို prompt
ထဲတွင် တိကျစွာ ပေးရမည်။

```json
{
  "node_labels": {"Company": ["id", "name"], "Product": ["id", "name", "summary"],
                  "Technology": ["id", "name"], "Team": ["id", "name"]},
  "relationship_types": ["DEVELOPS", "CREATES", "EMPLOYS", "USES", "MAINTAINED_BY",
                         "PUBLISHES", "RUNS_ON"],
  "rules": ["read-only", "parameterize all literals", "always project with RETURN", "LIMIT <= 50"]
}
```

Schema prompt ပြီးနောက် မဖြစ်မနေ လိုအပ်သော အဆင့်သည် validator ဖြစ်သည်။ LLM output ကို
database ပေါ်သို့ မပို့မီ clause level တွင် စစ်ရမည်။

```python
FORBIDDEN_KEYWORDS = ("CREATE", "MERGE", "DELETE", "DETACH", "SET", "REMOVE", "DROP",
                      "FOREACH", "LOAD", "CALL", "GRANT", "DENY", "REVOKE", "ALTER", "RENAME")

def _strip_inert(query):
    """Comment နှင့် string literal ကို ဖယ်ရှားသည် — ထို content သည် mutate လုပ်နိုင်စွမ်း မရှိ။"""
    query = BLOCK_COMMENT_RE.sub(" ", query)
    return STRING_LITERAL_RE.sub(" '?' ", LINE_COMMENT_RE.sub(" ", query))
```

`lab.py` မှ တကယ်ရရှိသော output —

```text
  ok=True  expected=True  read-only query accepted                     | MATCH (p:Product {id: $id}) RETURN p.name AS name, p.sum
  ok=False expected=False destructive clause rejected: DELETE, DETACH  | MATCH (p:Product) DETACH DELETE p
  ok=False expected=False multiple statements are not allowed          | MATCH (n) RETURN n; MATCH (m) DELETE m
  ok=False expected=False labels outside the schema allowlist: Secret  | MATCH (x:Secret) RETURN x
```

**Security သတိပေးချက်** — Validator သည် defense in depth ၏ တစ်ဆင့်သာ ဖြစ်သည်။ Database user ကို
read-only role ဖြင့် bind လုပ်ခြင်းသည် မဖြစ်မနေ လိုအပ်သည်၊ အဘယ်ကြောင့်ဆိုသော် keyword
blacklist သည် obfuscation (comment interleaving၊ Unicode homoglyph) ဖြင့် ကျော်နိုင်သည်။
Parameterize မလုပ်သော query ကို reject လုပ်ခြင်းနှင့် `LIMIT` ကို server side တွင် အတင်းသတ်မှတ်ခြင်း
သည် ထပ်ဆောင်း လိုအပ်ချက် ဖြစ်သည်။

Read-only k-hop retrieval အတွက် reference Cypher —

```cypher
MATCH path = (a)-[r*1..2]-(b)
WHERE a.id IN $anchor_ids
UNWIND relationships(path) AS rel
RETURN DISTINCT startNode(rel).id AS src, type(rel) AS rel_type, endNode(rel).id AS dst
LIMIT $limit
```

---

## ၆။ Community Detection နှင့် Hierarchical Summarization

Global question ("corpus ထဲက အဓိက theme များ ဘာလဲ") ကို k-hop subgraph ဖြင့် မဖြေနိုင်ပါ။
Graph ကို community အဖြစ် partition လုပ်ပြီး community တိုင်းကို summary တစ်ခု ဖန်တီးရမည်။
ထို summary များသည် global question အတွက် retrieval unit ဖြစ်လာသည်။

Newman modularity —

```text
Q = Σ_c [ L_c / m − ( k_c / 2m )² ]
```

- `m` = edge အရေအတွက်၊ `L_c` = community `c` အတွင်းရှိ edge အရေအတွက်
- `k_c` = community `c` ရှိ node များ၏ degree ပေါင်း

Louvain သည် node တစ်ခုစီကို အိမ်နီးချင်း community သို့ ရွှေ့ကြည့်ပြီး `Q` တက်သော ရွှေ့မှုကိုသာ
လက်ခံသည်။ ထို့နောက် community များကို super-node အဖြစ် ချုံ့၍ level ထပ်မံ တည်ဆောက်သည်။
Leiden သည် ထိုအဆင့်တွင် ပြုပြင်ထားသော refinement ကို ထည့်သွင်းပြီး degenerate community
(အတွင်းပိုင်း ချိတ်ဆက်မှု အားနည်းသော community) ကို ဖယ်ရှားသည်။

`lab.py` မှ တကယ်ရရှိသော output —

```text
level 0 (singletons)  communities=10 Q=-0.1145833333
level 1 (components)  communities=2 Q=0.4444444444
level 2 (refinement)  communities=2 Q=0.4444444444
  Community 0 covers: AuraDB, Cypher, GraphRAG, Neo4j, Neo4j Engineering, Vector Index
  Community 1 covers: CNRS, Fast unfolding of communities in large networks, Louvain, Vincent Blondel
```

**Engineering rationale** — Hierarchy နှစ်ဆင့် (level 1 connected component၊ level 2 modularity refinement)
ထားခြင်းသည် coarse-to-fine retrieval ကို ဖွင့်ပေးသည်။ "corpus တစ်ခုလုံး အကြောင်း ဘာပြောနိုင်သနည်း"
ဆိုသောမေးခွန်းတွင် level 1 summary များ (community ၂ ခု) ကို ပေးရမည်။ "Neo4j ecosystem အကြောင်း
ဘာပြောနိုင်သနည်း" မေးခွန်းတွင် level 2 community တစ်ခုတည်း၏ summary ကို ပေးရမည်။

**ဘယ်အချိန် မသုံးသင့်သနည်း** — Community summary သည် pre-computed ဖြစ်သောကြောင့် graph ကို
update လုပ်တိုင်း summary များ ပြန်လည် generate လုပ်ရမည်။ Incremental ingestion မြင့်သော
(တစ်နာရီတစ်ခါ write ရှိသော) system တွင် community summary ကို batch (ဥပမာ တစ်ညတစ်ခါ)
အဖြစ်သာ refresh လုပ်ရမည်၊ query path အတွင်းတွင် တွက်ချက်ခြင်း မပြုရ။

---

## ၇။ Evaluation — Vector-only Baseline နှင့် နှိုင်းယှဉ်ခြင်း

GraphRAG ၏ တန်ဖိုးကို ပြရန် vector-only baseline ဖြင့် တိုက်ရိုက် နှိုင်းယှဉ်ရမည်။ အနည်းဆုံး
metric သုံးမျိုး တိုင်းရမည် —

- **Recall@k** — လိုအပ်သော triple/chunk များ ကို top-k အတွင်း ရရှိမှု အချိုး
- **Context token cost** — prompt ထဲ ပို့သော token အရေအတွက် (GraphRAG သည် ပိုများလေ့ရှိသည်)
- **Answer grounding** — ဖြေချက်ထဲရှိ claim တိုင်း retrieved context မှ ခြေရာခံနိုင်မှု

Multi-hop question set တစ်ခုတွင် GraphRAG သည် recall ကို မြင့်စေသော်လည်း context token cost ကို
နှစ်ဆအထက် တိုးစေသည်။ Single-hop question တွင် နှစ်မျိုးလုံး recall သည် ကွာခြားချက် မရှိသလောက်
ဖြစ်ပြီး GraphRAG သည် cost ပိုပေးရုံသာ ဖြစ်သည်။ ထို့ကြောင့် evaluation set ကို hop count အလိုက်
ခွဲ၍ တိုင်းတာရမည်၊ စုစုပေါင်း average တစ်ခုတည်းဖြင့် ဆုံးဖြတ်ခြင်း မပြုရ။

Deterministic evaluation harness အတွက် `random` ကို မသုံးရ။ Question set ကို fixed list အဖြစ်
သိမ်းပြီး scoring ကို set intersection ဖြင့် တွက်ရမည်။

---

## Production Considerations

- **Provenance မဖြစ်မနေ** — graph triple တိုင်းတွင် source chunk id ထားရမည်။ မရှိပါက deduplication
  (ပိုင်း ၄) ကို လုပ်နိုင်မည် မဟုတ်ဘဲ citation ကိုလည်း မပြသနိုင်ပါ။
- **Hop budget ကို config ဖြစ်စေ** — `k = 2` သည် လေ့လာမှု အတွက် default ကောင်းသော်လည်း graph သိပ်သည်းမှု
  နှင့် context window အလိုက် ချိန်ညှိရမည်။ Degree distribution သည် heavy-tail ဖြစ်ပါက k-hop expansion
  သည် node တစ်ခုတည်းမှ ထောင်ချီသော node ကို ဆွဲထုတ်နိုင်သည်၊ ထို့ကြောင့် per-hop node cap ထားရမည်။
- **Entity linking အမှားကို တိုင်းတာ** — anchor precision နှင့် recall ကို သီးခြား metric အဖြစ်
  တိုင်းရမည်။ စုစုပေါင်း answer quality ထဲတွင် ဖုံးကွယ်ထားပါက ပြဿနာ၏ အမြစ်ကို မတွေ့နိုင်ပါ။
- **Text-to-Cypher ကို error recovery နှင့် တွဲ** — Generated Cypher သည် syntax error ဖြစ်ပါက error message
  ကို prompt ထဲ ပြန်ထည့်၍ retry အကြိမ်ကို ကန့်သတ်ရမည် (ဥပမာ ၂ ကြိမ်)။ ကျော်လွန်ပါက entity-anchored
  pattern သို့ fallback လုပ်ရမည်။

---

## Summary Checklist

- [ ] GraphRAG pattern ၃ မျိုးကို retrieval unit အလိုက် ခွဲခြားဖော်ပြနိုင်သည်
- [ ] Entity linking ကို name + ALIAS + fuzzy matching ဖြင့် implement လုပ်နိုင်သည်
- [ ] Query ဘာသာစကား မတူညီမှုတွင် ASCII fold မသုံးသင့်သည့် အကြောင်းရင်းကို ရှင်းပြနိုင်သည်
- [ ] k-hop subgraph ကို BFS ဖြင့် ထုတ်ယူပြီး deterministic ordering ဖြင့် serialize လုပ်နိုင်သည်
- [ ] RRF ဖြင့် vector rank နှင့် graph rank ကို ပေါင်းပြီး provenance အလိုက် dedup လုပ်နိုင်သည်
- [ ] Text-to-Cypher validator တွင် destructive clause rejection နှင့် read-only shape check ပါဝင်သည်
- [ ] Modularity formula ကို အသုံးပြု၍ partition တစ်ခု၏ အရည်အသွေးကို တွက်နိုင်သည်
- [ ] Community summary ကို coarse-to-fine retrieval unit အဖြစ် အသုံးချနိုင်သည်
- [ ] GraphRAG ကို vector-only baseline နှင့် recall နှင့် token cost နှစ်ခုလုံးဖြင့် နှိုင်းယှဉ်တိုင်းတာနိုင်သည်
