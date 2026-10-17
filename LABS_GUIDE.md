# LABS_GUIDE.md — Hands-on Labs လမ်းညွှန်

Course အတွင်းရှိ module ၉ ခုလုံး၏ algorithm များ၊ graph data structure၊ Cypher generation၊
retrieval pattern နှင့် pipeline logic များကို မိမိ local machine ပေါ်တွင် တိုက်ရိုက် run ၍
စမ်းသပ်နိုင်ရန် lab environment ပြင်ဆင်ထားသည်။

---

## ၁။ အမြန်စတင်နည်း (Dependency မလိုအပ်သော Core Labs)

Core lab အားလုံး (**exercise ၅၄ ခု**) သည် **Python standard library သာ အသုံးပြုထားသဖြင့်**
external package သွင်းရန် မလိုဘဲ ချက်ချင်း run နိုင်သည်။

### (က) Module အားလုံးကို တစ်ပြိုင်နက် run ခြင်း

```bash
python3 run_all_labs.py
```

Lab တိုင်းတွင် `assert` ဖြင့် ရလဒ်ကို စစ်ဆေးသဖြင့် — မှားပါက exit code `1` ဖြင့် ကျရှုံးသည်။

### (ခ) Module တစ်ခုတည်း run ခြင်း

```bash
python3 modules/00_getting_started/lab.py
python3 modules/01_traditional_ner_relation_extraction/lab.py
python3 modules/04_project_create_knowledge_graph/lab.py
python3 modules/07_knowledge_graph_rag/lab.py
```

### (ဂ) Runner ဖြင့် module ရွေးချယ်ခြင်း

```bash
python3 run_all_labs.py --module 06_in          # folder အမည်၏ တစ်စိတ်တစ်ပိုင်းဖြင့် ရွေးနိုင်သည်
python3 run_all_labs.py --verbose               # lab တိုင်း၏ output အပြည့်အစုံ
```

---

## ၂။ Lab များကို ဒီဇိုင်းရေးဆွဲသည့် မူ (Design Contract)

| လိုအပ်ချက် | အကောင်အထည်ဖော်ပုံ |
|---|---|
| Offline | network call၊ socket၊ API key တစ်ခုမှ မလိုအပ် |
| Deterministic | `random` မသုံး၊ system clock ပေါ် မမှီခို — run တိုင်း output တူ |
| Dependency-free | `numpy`၊ `networkx`၊ `neo4j driver` မသုံး — standard library သာ |
| Self-checking | exercise တိုင်းတွင် `assert` — ရလဒ်မှားပါက run ကျရှုံး |
| Database-optional | Neo4j server မလိုဘဲ run နိုင် — live test လိုပါက Docker ဖြင့် |

LLM extraction (M02, M03, M04) ကို **scripted deterministic extractor** ဖြင့် သရုပ်ပြသည်။
ထို extractor က ပြန်ပေးသည့် JSON သည် တကယ့် LLM တစ်ခု ပြန်ပေးသည့် format အတိုင်း ဖြစ်သဖြင့်
parsing၊ schema validation၊ entity resolution နှင့် hallucination filtering logic များသည်
production တွင် တိုက်ရိုက် အသုံးပြုနိုင်သော code ဖြစ်သည်။

---

## ၃။ Module အလိုက် Lab Exercise များ (စုစုပေါင်း ၅၄ ခု)

### M00 — `modules/00_getting_started/lab.py`
1. RAG Pipeline Stage Ordering
2. Cosine Similarity Ranking
3. Retrieval Modality Selection
4. RAG Failure Mode Classification
5. Triple (SPO) Parsing
6. GraphRAG Readiness Check

### M01 — `modules/01_traditional_ner_relation_extraction/lab.py`
1. Regex-based NER
2. BIO tagging decode
3. Gazetteer lookup
4. Pattern-based relationship extraction
5. Coreference resolution
6. Precision / Recall / F1

### M02 — `modules/02_llm_entity_relation_extraction/lab.py`
1. Extraction prompt template and input hardening
2. Parsing scripted LLM output
3. JSON schema validation and retry strategy
4. Entity resolution (alias + fuzzy matching)
5. Hallucination filter and grounding check
6. Token cost and latency estimate

### M03 — `modules/03_chunking_scale_extraction/lab.py`
1. Fixed-size chunking
2. Overlap selection
3. Map-reduce triple aggregation
4. Cross-chunk relationship reconnection
5. Triple deduplication and merge
6. Idempotent batch runner

### M04 — `modules/04_project_create_knowledge_graph/lab.py`
1. Corpus Normalization
2. End-to-End Pipeline Run
3. Data Model Validation
4. Provenance Metadata
5. Quality Gate Filtering
6. Cypher / JSON / CSV Export

### M05 — `modules/05_neo4j_introduction/lab.py`
1. Property Graph in-memory model
2. Cypher MERGE generation
3. Cypher statement parsing and validation
4. Constraint and Index definitions
5. Parameterized query builder and injection defense
6. Index-free adjacency traversal

### M06 — `modules/06_storing_entities_relationships_neo4j/lab.py`
1. Triple → Cypher batch generator (UNWIND)
2. Idempotent merge simulator (MERGE vs CREATE)
3. Uniqueness constraint validation
4. Relationship update/delete diff
5. Batch transaction sizing
6. Driver call sequence simulation

### M07 — `modules/07_knowledge_graph_rag/lab.py`
1. Entity Linking
2. k-hop Subgraph Retrieval
3. Subgraph Serialization
4. Hybrid Retrieval Fusion
5. Text-to-Cypher Guardrails
6. Community Detection

### M08 — `modules/08_conclusion/lab.py`
1. Full pipeline recap (stage ordering)
2. Cost / latency model
3. Build-vs-buy decision scorer
4. Incremental update planner
5. Production architecture checklist
6. End-to-end mini GraphRAG integration test

---

## ၄။ Neo4j Instance အစစ်ဖြင့် စမ်းသပ်ခြင်း

M05, M06, M07 ၏ Cypher output များကို တကယ့် Neo4j server ပေါ်တွင် run လိုပါက —

### (က) Container စတင်ခြင်း

```bash
docker compose up -d neo4j
```

| အချက် | တန်ဖိုး |
|---|---|
| Neo4j Browser | http://localhost:7474 |
| Bolt endpoint | `bolt://localhost:7687` |
| Username | `neo4j` |
| Password | `graphrag123` |
| Image | `neo4j:5.26-community` (APOC plugin ပါဝင်) |

### (ခ) Schema နှင့် sample graph load လုပ်ခြင်း

```bash
docker compose exec neo4j cypher-shell -u neo4j -p graphrag123 \
  -f /init/neo4j_init.cypher
```

ထို file တွင် — node identity constraint များ၊ `Entity.name`/`Entity.type` index၊
entity linking အတွက် full-text index နှင့် course lab များနှင့် တူညီသော sample graph
(Provider / Network / Service / Team / Document / Chunk node များ) ပါဝင်သည်။

### (ဂ) Python driver ဖြင့် စမ်းသပ်ခြင်း

```bash
pip install -r requirements.txt
```

```python
from neo4j import GraphDatabase

driver = GraphDatabase.driver("bolt://localhost:7687", auth=("neo4j", "graphrag123"))
with driver.session(database="neo4j") as session:
    rows = session.run(
        "MATCH (s:Entity)-[r]->(o:Entity) RETURN s.name AS subject, type(r) AS predicate, o.name AS object"
    )
    for row in rows:
        print(row["subject"], "-[", row["predicate"], "]->", row["object"])
driver.close()
```

### (ဃ) ရပ်တန့်ခြင်း

```bash
docker compose down          # container ရပ်တန့် (data ကျန်)
docker compose down -v       # container နှင့် volume အတူ ဖျက်
```

`pgvector` service ကို M07 ၏ hybrid retrieval lane (vector chunk + graph triple) အတွက်
optional အဖြစ် ထည့်သွင်းထားသည် — lab များတွင် မဖြစ်မနေ မလိုအပ်။

---

## ၅။ ပြဿနာဖြေရှင်းခြင်း (Troubleshooting)

| လက္ခဏာ | အကြောင်းရင်းနှင့် ဖြေရှင်းပုံ |
|---|---|
| `ModuleNotFoundError` | Core lab များတွင် မဖြစ်သင့်ပါ — Python 3.10+ ဖြစ်ကြောင်း စစ်ပါ |
| Lab exit code `1` | `assert` ကျရှုံးသည် — `python3 <lab.py>` ကို တိုက်ရိုက် run ၍ ကျရှုံးသည့် exercise ကို ကြည့်ပါ |
| `docker compose up` ပြီးပါက container `Restarting` ဖြစ်နေခြင်း | Neo4j entrypoint သည် `/data`, `/logs`, `/import` ကို start တိုင်း `chown` လုပ်သည် — ထို directory များအတွင်း read-only bind mount မထားရ။ ဤ repo ၏ `neo4j_init.cypher` ကို `/init` (Neo4j မစီမံသော path) တွင် mount ထားသည် |
| Neo4j container healthy မဖြစ်ခြင်း | heap memory setting နှင့် port `7474`/`7687` လွတ်ကြောင်း စစ်ပါ |
| `cypher-shell` auth error | `docker compose exec neo4j cypher-shell -u neo4j -p graphrag123` ဖြင့် တိုက်ရိုက် ဝင်ကြည့်ပါ |
| `neo4j_init.cypher` ကို ပြင်ပြီးနောက် အပြောင်းအလဲ မတွေ့ရခြင်း | single-file bind mount သည် container ဖန်တီးစဉ်က inode ကို ကိုင်ထားသည် — `docker compose up -d --force-recreate neo4j` ဖြင့် container ကို ပြန်ဖန်တီးပါ |
| M02/M03/M04 ရလဒ် မမျှော်လင့်သည့်အတိုင်း | ထို module များသည် deterministic scripted extractor သုံးသည် — output ကို ပြောင်းလိုပါက module အတွင်းရှိ `MOCK_LLM_RESPONSES`/scripted extractor data ကို ပြင်ပါ |

---

## ၆။ စစ်ဆေးပြီးသော ပတ်ဝန်းကျင် (Verified Environment)

ဤ repository ကို အောက်ပါပတ်ဝန်းကျင်တွင် တကယ် run ၍ စစ်ဆေးထားသည် —

| အချက် | တန်ဖိုး |
|---|---|
| Module lab | 9 module / 54 exercise — `python3 run_all_labs.py` → exit `0` |
| Neo4j | `neo4j:5.26-community` container `Up (healthy)` |
| Constraint | `entity_id_unique`, `document_id_unique`, `chunk_id_unique` — live server ပေါ်တွင် တည်ဆောက်ပြီး `SHOW CONSTRAINTS` ဖြင့် အတည်ပြု |
| Index | range index ၃ ခု + `entity_fulltext_index` (full-text entity linking အလုပ်လုပ်ကြောင်း `db.index.fulltext.queryNodes('entity_fulltext_index','guard')` ဖြင့် စစ်ဆေး) |
| Graph write | M06 ၏ `UNWIND $rows AS row ... MERGE (h)-[r:WORKED_AT]->(t)` batch statement ကို live server ပေါ် တိုက်ရိုက် execute — ဒုတိယအကြိမ် run တွင် node/relationship count မပြောင်းလဲ (idempotency အတည်ပြု) |
| Multi-hop query | `MATCH (v:Entity {id:'vpc_prod'})<-[:MONITORS]-(svc)-[:MANAGED_BY]->(team) RETURN svc.name, team.name` → `GuardDuty, SecOps_Team` |
