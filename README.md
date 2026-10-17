# Master Knowledge Graph Retrieval-Augmented Generation with Neo4j

Raw text မှ စတင်၍ Knowledge Graph တည်ဆောက်ခြင်း၊ ၎င်းကို Neo4j တွင် သိမ်းဆည်းခြင်းနှင့်
GraphRAG retrieval pattern များဖြင့် LLM ကို အဖြေထုတ်စေခြင်းအထိ — အဆင့်ဆင့် လက်တွေ့
တည်ဆောက်လေ့လာသည့် course ဖြစ်သည်။ Module ၉ ခု၊ executable lab ၅၄ exercise ပါဝင်ပြီး
lab အားလုံးကို **Python standard library သာ** သုံး၍ local machine ပေါ်တွင် dependency မလိုဘဲ
run နိုင်သည်။

---

## Course ဖွဲ့စည်းပုံ

| # | Module | အကြောင်းအရာ |
|---|---|---|
| M00 | `00_getting_started/` | Course architecture၊ RAG pipeline၊ Vector RAG ၏ ကန့်သတ်ချက်များနှင့် Graph RAG သို့ ရောက်ရှိသည့် လမ်းကြောင်း |
| M01 | `01_traditional_ner_relation_extraction/` | NER၊ BIO tagging၊ gazetteer၊ relationship extraction၊ coreference resolution၊ P/R/F1 evaluation |
| M02 | `02_llm_entity_relation_extraction/` | LLM extraction prompt design၊ structured output validation၊ entity resolution၊ hallucination filter |
| M03 | `03_chunking_scale_extraction/` | Chunk size နှင့် extraction quality၊ overlap၊ map-reduce pattern၊ cross-chunk merge၊ idempotent batch |
| M04 | `04_project_create_knowledge_graph/` | **Project** — raw text မှ validated Knowledge Graph အထိ end-to-end pipeline |
| M05 | `05_neo4j_introduction/` | Property Graph Model၊ Neo4j architecture၊ Cypher fundamentals၊ constraint/index၊ parameterization |
| M06 | `06_storing_entities_relationships_neo4j/` | Triple → graph write path၊ `MERGE`/`UNWIND` batch၊ idempotency၊ update/delete semantics |
| M07 | `07_knowledge_graph_rag/` | GraphRAG retrieval pattern ၃ မျိုး၊ entity linking၊ hybrid fusion၊ Text-to-Cypher guardrail၊ community detection |
| M08 | `08_conclusion/` | Production deployment considerations၊ GraphRAG decision criteria၊ capstone design |

Module တစ်ခုစီတွင် file ၅ ခု ပါဝင်သည် —

| File | အကြောင်းအရာ |
|---|---|
| `README.md` | Module scope နှင့် learning objectives |
| `explanation.md` | သဘောတရားရှင်းလင်းချက်၊ engineering rationale၊ deterministic code example |
| `exercise.md` | ကိုယ်တိုင် implement လုပ်ရမည့် လေ့ကျင့်ခန်း ၆ ခု |
| `solution.md` | Reference implementation နှင့် ရှင်းလင်းချက် |
| `lab.py` | Local machine ပေါ်တွင် ချက်ချင်း run ၍ assertion ဖြင့် စစ်ဆေးနိုင်သော executable lab |

---

## စတင်အသုံးပြုခြင်း (Quickstart)

**Module lab အားလုံးကို run ခြင်း** — dependency တစ်ခုမှ မလိုအပ်ပါ:

```bash
python3 run_all_labs.py
```

**Module တစ်ခုတည်း run ခြင်း:**

```bash
python3 modules/01_traditional_ner_relation_extraction/lab.py
python3 modules/04_project_create_knowledge_graph/lab.py
```

**Neo4j instance အစစ်ဖြင့် စမ်းသပ်ခြင်း** (M05, M06, M07 အတွက် optional):

```bash
docker compose up -d
# Neo4j Browser   — http://localhost:7474
# Bolt endpoint   — bolt://localhost:7687
# Credentials     — neo4j / graphrag123
```

Container စတင်ပြီးပါက `docker/neo4j_init.cypher` ကို cypher-shell ဖြင့် load လုပ်နိုင်သည် —

```bash
docker compose exec neo4j cypher-shell -u neo4j -p graphrag123 \
  -f /init/neo4j_init.cypher
```

Live database လိုအပ်သော integration test များအတွက် optional dependency များ သွင်းပါ:

```bash
pip install -r requirements.txt
```

---

## Repository Layout

```text
Master-GraphRAG-Neo4j-course/
├── README.md                       # ဤဖိုင်
├── COURSE_OUTLINE.md               # Course outline → module mapping နှင့် လေ့လာမှုအစီအစဉ်
├── WRITING_RULES.md                # အရေးအသား၊ code နှင့် lab စည်းမျဉ်းများ
├── MODULE_SPEC.md                  # Module တိုင်း၏ အကြောင်းအရာ သတ်မှတ်ချက်
├── LABS_GUIDE.md                   # Lab များ run ပုံနှင့် အသေးစိတ်လမ်းညွှန်
├── run_all_labs.py                 # Automated lab runner (module ၉ ခုလုံး)
├── docker-compose.yml              # Neo4j 5 Community + pgvector services
├── docker/
│   └── neo4j_init.cypher           # Constraint, index နှင့် sample graph data
├── requirements.txt                # Optional live-database dependencies
└── modules/
    ├── 00_getting_started/
    │   ├── README.md
    │   ├── explanation.md
    │   ├── exercise.md
    │   ├── solution.md
    │   └── lab.py
    ├── ...
    └── 08_conclusion/
```

---

## Prerequisites

- Python 3.10+ (module lab များအတွက် standard library သာ လိုအပ်သည်)
- Docker နှင့် Docker Compose (Neo4j ကို လက်တွေ့ စမ်းသပ်လိုပါက)
- ရင်းနှီးထားသင့်သည့် အခြေခံ — Python standard library၊ SQL သို့မဟုတ် query language တစ်မျိုး၊ graph နှင့် vector search ၏ အခြေခံသဘောတရား

## ဤ Course မှ မရရှိမည့် အရာ (Scope ကန့်သတ်ချက်)

- ၎င်းသည် API key သို့မဟုတ် cloud account မလိုသော **offline study course** ဖြစ်သည်။ LLM extraction
  ကို deterministic scripted extractor ဖြင့် သရုပ်ပြသည် — ထို logic သည် တကယ့် LLM သို့
  ချိတ်ဆက်ရာတွင် တိုက်ရိုက် အသုံးပြုနိုင်သော parsing၊ validation နှင့် resolution layer ဖြစ်သည်။
- Neo4j driver ကို lab များတွင် မလိုအပ်စေရန် in-memory graph simulation ဖြင့် သင်ကြားသည် —
  live database ဖြင့် စမ်းသပ်လိုပါက `docker-compose.yml` ကို အသုံးပြုနိုင်သည်။

## References

- Neo4j Documentation — https://neo4j.com/docs/
- Cypher Query Language Reference — https://neo4j.com/docs/cypher-manual/current/
- Neo4j Python Driver Manual — https://neo4j.com/docs/python-manual/current/
- Microsoft GraphRAG (From Local to Global, arXiv:2404.16130) — https://arxiv.org/abs/2404.16130
- Neo4j GraphRAG for Python — https://neo4j.com/docs/neo4j-graphrag-python/current/
