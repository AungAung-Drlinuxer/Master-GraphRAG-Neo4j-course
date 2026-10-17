# M05 — Introduction to Neo4j

ဤ module သည် Knowledge Graph ကို store လုပ်ရန် အသုံးပြုမည့် Neo4j ၏ data model နှင့် query language ကို
တည်ဆောက်ပေးသည်။ M04 အထိ ထုတ်လုပ်ခဲ့သော validated triple များကို graph database တစ်ခုအတွင်း မည်သို့
ကိုယ်စားပြုမည်၊ မည်သို့ စစ်ဆေးမည်၊ မည်သို့ ထိရောက်စွာ query လုပ်မည်ကို ဤနေရာတွင် သတ်မှတ်သည်။

## သင်ယူလေ့လာမည့် အကြောင်းအရာများ

- Property Graph Model — Node၊ Label၊ directed typed Relationship၊ Property များ၏ တိကျသော semantics
- Neo4j architecture — index-free adjacency၊ storage၊ Bolt protocol၊ Neo4j Browser
- Cypher အခြေခံ — `MATCH`၊ `CREATE`၊ `MERGE`၊ `WHERE`၊ `RETURN`၊ `SET`၊ `DELETE`
- Constraint နှင့် Index — uniqueness constraint၊ range index၊ full-text index၊ query plan သက်ရောက်မှု
- Parameterization — `$param` ဖြင့် Cypher injection ကာကွယ်ခြင်း
- Neo4j ကို အခြား graph database များနှင့် နှိုင်းယှဉ်ခြင်း၊ အသုံးပြုသင့်/မသင့် အခြေအနေများ

## Module အစိတ်အပိုင်းများ

| File | ရည်ရွယ်ချက် |
|---|---|
| `README.md` | Module scope၊ learning objectives၊ prerequisites၊ references |
| `explanation.md` | Subtopic ၆ ခု၏ သဘောတရားနှင့် engineering rationale |
| `exercise.md` | ကိုယ်တိုင် implement လုပ်ရမည့် လေ့ကျင့်ခန်း ၆ ခု (Hints + Expected behavior) |
| `solution.md` | Exercise တိုင်းအတွက် reference implementation နှင့် အဓိကအယူအဆ |
| `lab.py` | Standard library သာ သုံး၍ run နိုင်သော executable lab (`assert` ၆ ခု) |
| `walkthroughs/` | Exercise တိုင်းအတွက် Python အခြေခံမှစ၍ အပိုင်းလိုက် ရှင်းပြသည့် ဖတ်စာ |

`explanation.md` ၏ subtopic များ — (၁) Property Graph Model — Node၊ Label၊ typed directed Relationship၊
Property · (၂) Neo4j architecture — index-free adjacency၊ storage၊ Bolt protocol၊ Neo4j Browser ·
(၃) Cypher အခြေခံ — `MATCH`၊ `CREATE`၊ `MERGE`၊ `WHERE`၊ `RETURN`၊ `SET`၊ `DELETE` ·
(၄) Constraint နှင့် Index — uniqueness၊ range၊ full-text နှင့် query plan သက်ရောက်မှု ·
(၅) Parameterization — `$param` နှင့် Cypher injection ကာကွယ်ခြင်း ·
(၆) Neo4j နှင့် အခြား graph database နှိုင်းယှဉ်ချက် — decision criteria

### Walkthroughs

`solution.md` ရှိ code များကို Python အခြေခံမှ စတင်၍ အပိုင်းလိုက် လိုက်ဖတ်လိုပါက
`walkthroughs/` folder ကို ကြည့်ပါ။ Walkthrough တစ်ခုစီသည် exercise တစ်ခုစီအတွက် ဖြစ်ပြီး —
`@dataclass`၊ `field(default_factory=…)`၊ `sorted(key=…)`၊ list comprehension၊
`re.finditer()`၊ generator နှင့် `any()`၊ `collections.deque`၊ BFS၊ `math.log()`/`math.ceil()`
စသည့် concept များကို ဥပမာနှင့် တွဲဖက် ရှင်းပြသည်။

| Walkthrough | Exercise |
|---|---|
| `walkthroughs/01_property_graph_model.md` | Exercise 1 — Property Graph in-memory model |
| `walkthroughs/02_cypher_merge_generation.md` | Exercise 2 — Cypher `MERGE` generation |
| `walkthroughs/03_cypher_statement_validation.md` | Exercise 3 — Cypher statement validation |
| `walkthroughs/04_constraints_and_indexes.md` | Exercise 4 — Constraint နှင့် Index definitions |
| `walkthroughs/05_parameterized_query_builder.md` | Exercise 5 — Parameterized query builder နှင့် injection defense |
| `walkthroughs/06_index_free_adjacency.md` | Exercise 6 — Index-free adjacency traversal |

## Prerequisites

- M00 — RAG pipeline၊ Knowledge Graph အစိတ်အပိုင်းများ (Node၊ Relationship၊ Triple)
- M01–M04 — NER၊ relationship extraction၊ chunking၊ triple quality gate နှင့် Cypher export format
- Python အခြေခံ၊ command line အခြေခံ

Neo4j server မလိုအပ် — `lab.py` သည် Property Graph ကို in-memory adjacency map ဖြင့် simulate လုပ်ပြီး
Cypher string များကို generate/validate သာ လုပ်သည်။ Real Neo4j instance လိုပါက repo ရှိ
`docker-compose.yml` ဖြင့် start နိုင်သည် — Neo4j 5 Community၊ Bolt port `7687`၊ Browser port `7474`၊
credentials `neo4j` / `graphrag123`။ ထို compose file သည် pgvector ကိုပါ တွဲဖက် run ပေးသည်။

## Production Use Cases

- LLM မှ ထုတ်လုပ်သော entity/relationship များကို `MERGE` ဖြင့် idempotent အနေဖြင့် graph အဖြစ် store လုပ်ခြင်း
- Entity uniqueness ကို uniqueness constraint ဖြင့် database အဆင့်တွင် အာမခံခြင်း
- Entity name များအတွက် full-text index ဖြင့် entity linking ကို speed up လုပ်ခြင်း
- Text-to-Cypher pipeline တွင် `$param` parameterization နှင့် read-only guardrail သုံးခြင်း
- Multi-hop traversal လိုအပ်သော GraphRAG retrieval (entity-anchored subgraph)

## References

- Neo4j — Getting Started: https://neo4j.com/docs/getting-started/
- Cypher Manual — Introduction: https://neo4j.com/docs/cypher-manual/current/introduction/
- Cypher Manual — `MERGE`: https://neo4j.com/docs/cypher-manual/current/clauses/merge/
- Cypher Manual — Parameters: https://neo4j.com/docs/cypher-manual/current/syntax/parameters/
- Cypher Manual — Constraints: https://neo4j.com/docs/cypher-manual/current/constraints/
- Cypher Manual — Indexes: https://neo4j.com/docs/cypher-manual/current/indexes/
- Bolt Protocol: https://neo4j.com/docs/bolt/current/bolt/
