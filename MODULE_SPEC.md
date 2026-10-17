# MODULE_SPEC.md — Module တိုင်း၏ အကြောင်းအရာ သတ်မှတ်ချက်

ဤဖိုင်သည် course outline တွင် ဖော်ပြထားသော အကြောင်းအရာများကို module များအဖြစ် ပုံဖော်ထားသည်။
Module တစ်ခုစီအတွက် ဖော်ပြထားသော subtopic များမှာ **မဖြစ်မနေ ပါဝင်ရမည်** (အနည်းဆုံး)။
အတိအကျ လိုက်နာရမည့် file ဖွဲ့စည်းပုံနှင့် အရေးအသားစည်းမျဉ်းများအတွက် `WRITING_RULES.md` ကို ဖတ်ပါ။

Course title — **Master Knowledge Graph Retrieval-Augmented Generation with Neo4j**

---

## M00 — `modules/00_getting_started/`

Course outline mapping — Introduction to the Course
- Getting Started
- Understanding the Path to Graph RAG

**ဖော်ပြရမည့် subtopic များ**

1. Course architecture — module များ ဘယ်လို ချိတ်ဆက်ထားသည်၊ lab များ run ပုံ
2. RAG ၏ အခြေခံ pipeline (ingest → chunk → embed → retrieve → generate) နှင့် FAQ
3. Plain Vector RAG ၏ ကန့်သတ်ချက်များ — chunk isolation၊ multi-hop မဖြေနိုင်ခြင်း၊ global summarization အားနည်းခြင်း
4. Graph RAG သို့ ရောက်ရှိသည့် လမ်းကြောင်း — Vector RAG → Hybrid Search → Knowledge Graph → GraphRAG
5. Knowledge Graph ၏ အစိတ်အပိုင်းများ — Node၊ Relationship၊ Label၊ Property၊ Triple (SPO)
6. Course အတွင်း အသုံးပြုမည့် toolchain — Python standard library၊ Neo4j၊ Cypher၊ Docker

**Lab exercises (၆ ခု)** — RAG pipeline stage များ၏ order၊ cosine similarity၊ retrieval modality ရွေးချယ်မှု၊
RAG ၏ failure mode ခွဲခြားမှု၊ Triple structure parsing၊ GraphRAG readiness check

---

## M01 — `modules/01_traditional_ner_relation_extraction/`

Course outline mapping — Constructing Knowledge Graphs → Traditional NER and Relationship Extraction Techniques

**ဖော်ပြရမည့် subtopic များ**

1. NER (Named Entity Recognition) ၏ အခြေခံ — token classification၊ BIO tagging scheme (`B-PER`, `I-PER`, `O`)
2. Rule-based နှင့် statistical NER — gazetteer၊ regex pattern၊ CRF ချဉ်းကပ်နည်းများ
3. Relationship Extraction — pattern-based extraction၊ dependency parsing၊ distance supervision
4. Coreference resolution — pronoun များကို antecedent entity သို့ ပြန်ညွှန်းခြင်း (entity များ မှားယွင်း duplicate ဖြစ်ခြင်း၏ အဓိကအကြောင်းရင်း)
5. Classical pipeline ၏ ကန့်သတ်ချက်များ — domain shift၊ custom entity type အသစ်များအတွက် training data လိုအပ်ခြင်း၊ recall နည်းခြင်း
6. Evaluation — Precision၊ Recall၊ F1 ဖြင့် extraction quality တိုင်းတာခြင်း

**Lab exercises (၆ ခု)** — Regex-based NER၊ BIO tagging decode၊ gazetteer lookup၊
pattern-based relationship extraction၊ coreference resolution၊ P/R/F1 ဖြင့် evaluation

---

## M02 — `modules/02_llm_entity_relation_extraction/`

Course outline mapping — Constructing Knowledge Graphs → Improved Entity and Relationship Extraction Using LLMs

**ဖော်ပြမည့် subtopic များ**

1. LLM-based extraction သည် classical NER ကို ဘာကြောင့် ကျော်လွှားသနည်း — zero-shot/few-shot၊ schema ကို prompt ဖြင့် သတ်မှတ်နိုင်ခြင်း
2. Extraction prompt design — entity type list၊ allowed relationship list၊ output schema (JSON) ကို တိကျစွာ သတ်မှတ်ခြင်း
3. Structured output enforcement — JSON schema validation၊ malformed output ကို handling လုပ်ခြင်း၊ retry strategy
4. Entity resolution — canonical name selection၊ alias mapping၊ fuzzy matching (normalized Levenshtein / token overlap)
5. Extraction quality control — hallucinated entity/relationship များကို filter လုပ်ခြင်း၊ grounding check
6. Cost နှင့် ကန့်သတ်ချက်များ — token cost၊ latency၊ prompt injection အန္တရာယ်၊ rate limit

**Lab exercises (၆ ခု)** — Extraction prompt template တည်ဆောက်ခြင်း၊ scripted LLM output ကို parse လုပ်ခြင်း၊
JSON schema validation၊ entity resolution (fuzzy matching)၊ hallucination filter၊ token cost ခန့်မှန်းခြင်း

---

## M03 — `modules/03_chunking_scale_extraction/`

Course outline mapping — Constructing Knowledge Graphs → Chunking: Entity and Relationship Extraction with LLMs at Scale

**ဖော်ပြမည့် subtopic များ**

1. Chunking သည် extraction quality ကို ဘယ်လို သက်ရောက်သည် — chunk သေးလွန်းပါက relationship ပြတ်တောက်ခြင်း
2. Chunk size နှင့် overlap ရွေးချယ်ခြင်း — token budget နှင့် context window ဆက်စပ်မှု
3. Map-reduce extraction pattern — chunk တိုင်းမှ extract လုပ်ပြီး စုစည်းခြင်း (map phase)
4. Cross-chunk relationship များ ကိုင်တွယ်ခြင်း — boundary ဖြတ်သွားသော entity pair များကို ပြန်ချိတ်ဆက်ခြင်း
5. Deduplication နှင့် merge — chunk အသီးသီးမှ ထွက်လာသော triple များကို ပေါင်းစည်းခြင်း
6. Scale အတွက် engineering — batching၊ concurrency၊ checkpointing၊ idempotency၊ failure recovery

**Lab exercises (၆ ခု)** — Fixed-size chunking၊ overlap ထည့်ခြင်း၊ map-reduce triple aggregation၊
cross-chunk relationship ပြန်ချိတ်ခြင်း၊ triple deduplication၊ idempotent batch runner

---

## M04 — `modules/04_project_create_knowledge_graph/`

Course outline mapping — Constructing Knowledge Graphs → Project: Create a Knowledge Graph from Text

**ဤသည် project module ဖြစ်သည် — သဘောတရားအသစ် မဟုတ်ဘဲ M01–M03 ကို ပေါင်းစည်းသည့် end-to-end project**
**ဖြစ်သည်။ ဖော်ပြရမည့် subtopic များ**

1. Project scope နှင့် deliverable — raw text corpus မှ validated Knowledge Graph အထိ
2. Pipeline အဆင့်ဆင့် — ingest → normalize → chunk → extract → resolve → merge → validate → export
3. Data model ဒီဇိုင်း — Node label များ၊ Relationship type များ၊ property schema
4. Provenance tracking — triple တိုင်းတွင် source chunk id၊ confidence၊ extraction method မှတ်သားခြင်း
5. Quality gates — empty triple၊ self-loop၊ missing endpoint၊ duplicate triple များကို စစ်ထုတ်ခြင်း
6. Export format — Cypher `MERGE` statements၊ JSON triple list၊ CSV (Neo4j Admin Import အတွက်)

**Lab exercises (၆ ခု)** — Corpus normalization၊ end-to-end pipeline run၊ data model validation၊
provenance metadata၊ quality gate filtering၊ Cypher/JSON export

---

## M05 — `modules/05_neo4j_introduction/`

Course outline mapping — Neo4j: Storing Entities and Relationships to Graph Database → Introduction to Neo4j

**ဖော်ပြမည့် subtopic များ**

1. Property Graph Model — Node၊ Label၊ Relationship (directed, typed)၊ Property
2. Neo4j architecture — index-free adjacency၊ storage၊ Bolt protocol၊ Neo4j Browser
3. Cypher language အခြေခံ — `MATCH`၊ `CREATE`၊ `MERGE`၊ `WHERE`၊ `RETURN`၊ `SET`၊ `DELETE`
4. Constraints နှင့် indexes — uniqueness constraint၊ full-text index၊ range index၊ index ၏ query plan သက်ရောက်မှု
5. Cypher အတွက် parameterization — `$param` အသုံးပြု၍ injection ကာကွယ်ခြင်း
6. Neo4j အခြား graph database များနှင့် နှိုင်းယှဉ်ချက် — အသုံးပြုရန် သင့်/မသင့် အခြေအနေများ

**Lab exercises (၆ ခု)** — Property Graph in-memory model၊ Cypher `MERGE` generation၊
Cypher statement parsing/validation၊ constraint definition၊ parameterized query builder၊
graph traversal (index-free adjacency simulation)

---

## M06 — `modules/06_storing_entities_relationships_neo4j/`

Course outline mapping — Neo4j: Storing Entities and Relationships to Graph Database → Storing LLM Extracted Entities and Relationships in Neo4j

**ဖော်ပြမည့် subtopic များ**

1. Triple မှ graph write အထိ — batch `MERGE` pattern၊ `UNWIND` ဖြင့် bulk insert
2. Idempotent graph write — `MERGE` နှင့် `CREATE` ၏ ကွာခြားချက်၊ duplicate node ဖြစ်ပေါ်ခြင်းကို ကာကွယ်ခြင်း
3. Constraint ဖြင့် entity uniqueness ထိန်းချုပ်ခြင်း — `REQUIRE n.id IS UNIQUE`
4. Update နှင့် delete semantics — relationship အဟောင်း ဖယ်ရှားခြင်း၊ orphan node cleanup၊ cascade delete
5. Batch performance — transaction batching၊ `UNWIND`၊ driver session pool၊ index အရေးပါမှု
6. Python driver အခြေခံ — `GraphDatabase.driver`၊ session၊ `session.run(query, **params)`၊ result handling (offline simulation နှင့် live test ခွဲခြားပုံ)

**Lab exercises (၆ ခု)** — Triple → Cypher batch generator (`UNWIND`)၊ idempotent merge simulator၊
constraint validation၊ relationship update/delete diff၊ batch transaction sizing၊ driver call sequence simulation

---

## M07 — `modules/07_knowledge_graph_rag/`

Course outline mapping — Integrating Knowledge Graphs with LLMs → Knowledge Graph-based RAG

**ဖော်ပြမည့် subtopic များ**

1. GraphRAG retrieval patterns ၃ မျိုး — (က) entity-anchored subgraph retrieval၊ (ခ) Text-to-Cypher၊ (ဂ) community-summary retrieval
2. Entity linking — query text မှ entity များကို graph node များသို့ map လုပ်ခြင်း
3. Subgraph → prompt context serialization — triple များကို LLM နားလည်နိုင်သော format အဖြစ် ပြောင်းခြင်း
4. Hybrid retrieval (vector chunks + graph triples) — fusion strategy၊ ranking၊ deduplication
5. Text-to-Cypher — schema prompt၊ guardrails၊ read-only validation၊ error recovery
6. Community Detection နှင့် hierarchical summarization — Louvain/Leiden algorithm ၏ အခြေခံ၊ global question များကို ဖြေဆိုခြင်း
7. Evaluation — GraphRAG ၏ retrieval quality ကို vector-only baseline နှင့် နှိုင်းယှဉ်ခြင်း

**Lab exercises (၆ ခု)** — Entity linking၊ k-hop subgraph retrieval၊ triple → prompt context serialization၊
hybrid fusion ranking၊ Text-to-Cypher guardrail validation၊ community detection (connected components / modularity)

---

## M08 — `modules/08_conclusion/`

Course outline mapping — Integrating Knowledge Graphs with LLMs → Conclusion

**ဖော်ပြမည့် subtopic များ**

1. Course အတွင်း လေ့လာခဲ့သည့် အရာများ ပြန်လည်စုစည်းခြင်း — pipeline တစ်ခုလုံး၏ map
2. Production deployment စဉ်းစားရမည့်အချက်များ — cost၊ latency၊ incremental update၊ monitoring
3. GraphRAG သည် မည်သည့်အခြေအနေတွင် တန်ဖိုးရှိသည် / မရှိသည် — decision criteria
4. ဆက်လက် လေ့လာရန် လမ်းကြောင်းများ — Ontology၊ Graph Neural Network၊ Agentic RAG၊ evaluation framework များ
5. Capstone design exercise — ကိုယ်တိုင် corpus တစ်ခုအတွက် GraphRAG architecture ရေးဆွဲခြင်း
6. Course wrap-up — files၊ labs၊ references ပြန်လည်ရှာဖွေပုံ

**Lab exercises (၆ ခု)** — Full pipeline recap (stage ordering)၊ cost/latency model၊
build-vs-buy decision scorer၊ incremental update planner၊ architecture checklist၊
end-to-end mini GraphRAG integration test

---

## Project (Course Outline ၏ "Project: Create a Knowledge Graph from Text")

Project ကို **M04** တွင် အကောင်အထည်ဖော်သည်။ M04 ၏ `lab.py` သည် M01–M03 ၏ algorithm များကို
တစ်ခုတည်းသော end-to-end pipeline အဖြစ် ပေါင်းစည်းပြရမည် —
raw text corpus ထည့် → normalized + chunked → LLM-style extraction (scripted deterministic extractor)
→ entity resolution → triple merge/dedup → quality gate → Cypher + JSON export။
