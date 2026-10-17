# COURSE_OUTLINE.md — Master Knowledge Graph Retrieval-Augmented Generation with Neo4j

Course outline တွင် ဖော်ပြထားသည့် အကြောင်းအရာများနှင့် repository အတွင်းရှိ module folder များ၏
တိုက်ရိုက် mapping ဖြစ်သည်။

---

## 1. Introduction to the Course → `modules/00_getting_started/`

| Outline | ဖော်ပြရမည့် အကြောင်းအရာ |
|---|---|
| Getting Started | Course architecture၊ module ချိတ်ဆက်ပုံ၊ lab များ run ပုံ၊ toolchain |
| Understanding the Path to Graph RAG | Vector RAG pipeline၊ ၎င်း၏ ကန့်သတ်ချက်များ၊ Hybrid Search → Knowledge Graph → GraphRAG သို့ ရောက်ရှိသည့် လမ်းကြောင်း |

## 2. Constructing Knowledge Graphs

| Outline | Module |
|---|---|
| Traditional NER and Relationship Extraction Techniques | `modules/01_traditional_ner_relation_extraction/` |
| Improved Entity and Relationship Extraction Using LLMs | `modules/02_llm_entity_relation_extraction/` |
| Chunking: Entity and Relationship Extraction with LLMs at Scale | `modules/03_chunking_scale_extraction/` |
| **Project: Create a Knowledge Graph from Text** | `modules/04_project_create_knowledge_graph/` |

## 3. Neo4j: Storing Entities and Relationships to Graph Database

| Outline | Module |
|---|---|
| Introduction to Neo4j | `modules/05_neo4j_introduction/` |
| Storing LLM Extracted Entities and Relationships in Neo4j | `modules/06_storing_entities_relationships_neo4j/` |

## 4. Integrating Knowledge Graphs with LLMs

| Outline | Module |
|---|---|
| Knowledge Graph-based RAG | `modules/07_knowledge_graph_rag/` |
| Conclusion | `modules/08_conclusion/` |

---

## Module အလိုက် လေ့လာရမည့် ရလဒ် (Learning Outcomes)

| Module | ပြီးဆုံးပါက ရရှိမည့် စွမ်းရည် |
|---|---|
| M00 | RAG ၏ pipeline stage များနှင့် GraphRAG ၏ တည်နေရာကို ရှင်းလင်းစွာ ဖော်ပြနိုင်ခြင်း |
| M01 | Rule-based NER၊ BIO tagging decode၊ relationship pattern extraction၊ coreference resolution ကို ကိုယ်တိုင် implement လုပ်နိုင်ခြင်း |
| M02 | LLM extraction prompt တည်ဆောက်ခြင်း၊ JSON output ကို validate လုပ်ခြင်း၊ entity resolution နှင့် hallucination filter ရေးနိုင်ခြင်း |
| M03 | Chunking strategy ရွေးချယ်ခြင်း၊ map-reduce extraction pattern နှင့် cross-chunk relationship ချိတ်ဆက်ခြင်း |
| M04 | Raw text မှ validated Knowledge Graph အထိ end-to-end pipeline တည်ဆောက်ပြီး Cypher/JSON/CSV export ထုတ်နိုင်ခြင်း |
| M05 | Property Graph model ဒီဇိုင်းရေးခြင်း၊ Cypher query ရေးခြင်း၊ constraint/index သတ်မှတ်ခြင်း |
| M06 | Triple များကို idempotent batch write ဖြင့် graph database ထဲ ထည့်ခြင်း၊ update/delete semantics ကိုင်တွယ်ခြင်း |
| M07 | GraphRAG retrieval pattern ၃ မျိုး တည်ဆောက်ခြင်း၊ hybrid fusion နှင့် Text-to-Cypher guardrail ရေးခြင်း |
| M08 | Production deployment decision (cost/latency/incremental update) ကို justification ဖြင့် ချမှတ်နိုင်ခြင်း |

---

## ၄ ပတ် လေ့လာမှု အစီအစဉ် (Study Plan)

**ပတ် ၁ — Foundations နှင့် Traditional Extraction**
- M00 (Getting Started, Path to Graph RAG)
- M01 (NER, BIO tagging, relationship extraction, coreference)
- Checkpoint — M01 ၏ P/R/F1 lab ကို run ၍ extraction quality တိုင်းတာပုံ ရှင်းပြနိုင်ရမည်

**ပတ် ၂ — LLM Extraction နှင့် Scale**
- M02 (prompt design, schema validation, entity resolution)
- M03 (chunking, map-reduce, cross-chunk merge)
- Checkpoint — chunk size ပြောင်းလဲမှုက extraction quality ကို ဘယ်လို သက်ရောက်သည် ရှင်းပြနိုင်ရမည်

**ပတ် ၃ — Project နှင့် Neo4j**
- M04 (end-to-end project — Create a Knowledge Graph from Text)
- M05 (Neo4j, Property Graph, Cypher, constraint/index)
- M06 (graph write path, MERGE/UNWIND, idempotency)
- Checkpoint — `docker compose up -d` ဖြင့် Neo4j ကို start ပြီး M06 ၏ Cypher output ကို လက်တွေ့ load လုပ်နိုင်ရမည်

**ပတ် ၄ — GraphRAG နှင့် Production**
- M07 (GraphRAG retrieval patterns, hybrid fusion, Text-to-Cypher, community detection)
- M08 (production considerations, decision criteria, capstone design)
- Checkpoint — ကိုယ်ပိုင် corpus တစ်ခုအတွက် GraphRAG architecture ကို trade-off ဖြင့် တင်ပြနိုင်ရမည်

---

## Assessment

Module တိုင်းတွင် — `exercise.md` ၏ လေ့ကျင့်ခန်း ၆ ခု၊ `solution.md` ၏ reference implementation နှင့်
`lab.py` ၏ automated assertion များ ပါဝင်သည်။ Module တစ်ခု ပြီးဆုံးကြောင်း အသိအမှတ်ပြုရန် —

```bash
python3 run_all_labs.py --module <module_folder>
```

သည် `[PASS] All 6/6 exercises passed successfully.` နှင့် exit code `0` ပြန်ရမည်။
