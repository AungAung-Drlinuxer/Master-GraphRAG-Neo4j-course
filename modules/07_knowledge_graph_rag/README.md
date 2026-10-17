# M07 — Knowledge Graph-based RAG (GraphRAG)

Plain Vector RAG သည် chunk တစ်ခုချင်းစီကို အလွတ်တည်း retrieve လုပ်သောကြောင့် multi-hop question၊
entity အချင်းချင်း ဆက်စပ်မှုနှင့် corpus တစ်ခုလုံး၏ global question များတွင် ကျရှုံးသည်။ ဤ module သည်
Knowledge Graph ကို retrieval index အဖြစ် အသုံးပြု၍ ထိုကန့်သတ်ချက်များကို ဖြေရှင်းသော GraphRAG
retrieval pattern ၃ မျိုးကို အကောင်အထည်ဖော်သည် — entity-anchored subgraph retrieval၊ Text-to-Cypher၊
community-summary retrieval။ ဤ module ပြီးဆုံးချိန်တွင် vector-only baseline နှင့် နှိုင်းယှဉ်တိုင်းတာနိုင်သည်။

## သင်ယူလေ့လာမည့် အကြောင်းအရာများ

- GraphRAG retrieval pattern ၃ မျိုး၏ ကွာခြားချက်နှင့် ရွေးချယ်ရမည့် အခြေအနေ
- Query text မှ graph node သို့ entity linking (name/ALIAS matching ၏ ကန့်သတ်ချက်)
- k-hop subgraph retrieval နှင့် Hop budget ကို context size ဖြင့် ချိန်ညှိခြင်း
- Subgraph ကို LLM နားလည်နိုင်သော prompt context အဖြစ် serialize လုပ်ခြင်း
- Hybrid retrieval — Vector chunk နှင့် graph triple ကို Reciprocal Rank Fusion ဖြင့် ပေါင်းခြင်း၊ provenance deduplication
- Text-to-Cypher — Schema prompt၊ read-only guardrail၊ destructive clause rejection
- Community Detection (Louvain/Leiden basic) နှင့် hierarchical summarization ဖြင့် global question ဖြေဆိုခြင်း
- GraphRAG ကို vector-only baseline နှင့် နှိုင်းယှဉ် evaluation လုပ်ခြင်း

## Module အစိတ်အပိုင်းများ

| File | ရည်ရွယ်ချက် |
|---|---|
| `README.md` | Module scope၊ learning objectives၊ prerequisites၊ use case၊ references |
| `explanation.md` | Subtopic ၇ ခု၏ သဘောတရား၊ modularity formula၊ GraphRAG vs vector baseline |
| `exercise.md` | လေ့ကျင့်ခန်း ၆ ခု (Hints + Expected behavior) |
| `solution.md` | Exercise တိုင်းအတွက် reference implementation |
| `lab.py` | Standard library သာ သုံးသော executable lab (`assert` ဖြင့် စစ်ဆေး) |
| `walkthroughs/` | Exercise တိုင်းအတွက် Python အခြေခံမှစ၍ အပိုင်းလိုက် ရှင်းပြသည့် ဖတ်စာ |

`explanation.md` သည် အောက်ပါ subtopic ၇ ခုကို အစဉ်လိုက် ဖော်ပြသည် —

1. GraphRAG retrieval pattern ၃ မျိုး — entity-anchored subgraph၊ Text-to-Cypher၊ community-summary
2. Entity Linking — query text မှ graph node သို့ mapping လုပ်ခြင်း
3. Subgraph → prompt context serialization
4. Hybrid Retrieval — Vector chunk + graph triple ကို fusion လုပ်ခြင်း
5. Text-to-Cypher — schema prompt၊ guardrail၊ read-only validation
6. Community Detection နှင့် hierarchical summarization
7. Evaluation — GraphRAG ကို vector-only baseline နှင့် နှိုင်းယှဉ်ခြင်း

### Walkthroughs

`solution.md` ရှိ code များကို Python အခြေခံမှ စတင်၍ အပိုင်းလိုက် လိုက်ဖတ်လိုပါက
`walkthroughs/` folder ကို ကြည့်ပါ။ Walkthrough တစ်ခုစီသည် exercise တစ်ခုစီအတွက် ဖြစ်ပြီး —
concept အသစ်များ (`dict` comprehension၊ set union၊ `deque`/BFS၊ `zip`၊ `enumerate`၊ `sorted(key=…)`၊
`defaultdict`၊ `while` flag loop၊ `raise`/`try-except`) ကို ဥပမာနှင့် တွဲဖက် ရှင်းပြသည်။

| Walkthrough | Exercise |
|---|---|
| `walkthroughs/01_entity_linking.md` | Exercise 1 — Entity Linking |
| `walkthroughs/02_k_hop_subgraph_retrieval.md` | Exercise 2 — k-hop Subgraph Retrieval |
| `walkthroughs/03_subgraph_prompt_serialization.md` | Exercise 3 — Subgraph → Prompt Context Serialization |
| `walkthroughs/04_hybrid_retrieval_fusion.md` | Exercise 4 — Hybrid Retrieval Fusion |
| `walkthroughs/05_text_to_cypher_guardrails.md` | Exercise 5 — Text-to-Cypher Guardrails |
| `walkthroughs/06_community_detection.md` | Exercise 6 — Community Detection |

## Prerequisites

- Module M00 (RAG pipeline အခြေခံ)
- Module M05, M06 (Property Graph၊ Cypher၊ graph write pattern)
- Python standard library အသုံးပြု၍ ကိုယ်တိုင် run နိုင်သော အဆင့် (external package မလိုအပ်)

## Production Use Cases

- Internal knowledge assistant — policy၊ ticket၊ contract များမှ entity-anchored answer ထုတ်ခြင်း
- Compliance နှင့် audit retrieval — triple တိုင်းတွင် provenance chunk id ပါသောကြောင့် citation ပြန်ခြေရာခံနိုင်သည်
- Analyst tooling — Text-to-Cypher ဖြင့် read-only graph query ကို natural language မှ ထုတ်ခြင်း
- Corpus-level trend question — community summary ဖြင့် "အဓိက theme များ ဘာလဲ" ကဲ့သို့ global question ဖြေဆိုခြင်း

## References

- Neo4j Cypher Manual — https://neo4j.com/docs/cypher-manual/current/
- Neo4j Cypher `MATCH` clause — https://neo4j.com/docs/cypher-manual/current/clauses/match/
- Neo4j Cypher `WHERE` clause — https://neo4j.com/docs/cypher-manual/current/clauses/where/
- Neo4j Graph Data Science — Louvain — https://neo4j.com/docs/graph-data-science/current/algorithms/louvain/
- Neo4j Graph Data Science — Leiden — https://neo4j.com/docs/graph-data-science/current/algorithms/leiden/
- Microsoft GraphRAG paper (From Local to Global) — https://arxiv.org/abs/2404.16130
