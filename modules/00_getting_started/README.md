# M00 — Getting Started

ဤ module သည် course တစ်ခုလုံး၏ ဝင်ပေါက်ဖြစ်သည်။ ပထမဦးစွာ **Plain Vector RAG** ၏ pipeline ကို
အစိတ်အပိုင်း (ingest → chunk → embed → retrieve → generate) အလိုက် ပြန်ဖြိုခွဲပြသည်။ ထို့နောက် ထို
pipeline သည် မည်သည့်နေရာတွင် ကျရှုံးသည်ကို တိုင်းတာနိုင်သော failure mode များအဖြစ် ခွဲထုတ်ပြီး
**Knowledge Graph** နှင့် **GraphRAG** သို့ ရောက်ရှိသည့် လမ်းကြောင်းကို တည်ဆောက်သည်။

Module တိုင်းတွင် file ၅ ခု တူညီစွာ ရှိပြီး `lab.py` တစ်ခုစီသည် Python standard library သာ
အသုံးပြုကာ offline တွင် run နိုင်သည်။ Neo4j server မလိုအပ်ပါ။

## သင်ယူလေ့လာမည့် အကြောင်းအရာများ

- RAG pipeline ၏ အဆင့်များနှင့် ၎င်းတို့၏ dependency order ကို ဖော်ထုတ်နိုင်ခြင်း
- Cosine similarity ဖြင့် Embedding များကို ranking လုပ်ခြင်း၊ Vector Search ၏ အခြေခံသင်္ချာ
- Query feature အပေါ် မူတည်၍ retrieval modality (Vector Search / Text-to-Cypher / GraphRAG) ရွေးချယ်ခြင်း
- Plain Vector RAG ၏ failure mode များကို ခွဲခြားပြီး graph ဖြင့် ဖြေရှင်းနိုင်သော အုပ်စုကို ခွဲထုတ်ခြင်း
- Knowledge Graph ၏ အစိတ်အပိုင်းများ (Node, Relationship, Label, Property) နှင့် Triple (SPO) structure
- GraphRAG အတွက် corpus readiness ကို တိုင်းတာနိုင်သော check list အဖြစ် ပြောင်းခြင်း

## Module အစိတ်အပိုင်းများ

| File | အကြောင်းအရာ |
|---|---|
| `README.md` | Module scope၊ learning objectives၊ prerequisites၊ production use case |
| `explanation.md` | သဘောတရား ၆ ခု — pipeline၊ vector limitation၊ graph လမ်းကြောင်း၊ KG အစိတ်အပိုင်း၊ toolchain |
| `exercise.md` | လေ့ကျင့်ခန်း ၆ ခု (Hints နှင့် Expected behavior ပါ) |
| `solution.md` | Exercise တိုင်းအတွက် reference implementation အပြည့်အစုံ |
| `lab.py` | Run နိုင်၊ စစ်ဆေးနိုင်သော deterministic lab (assert-based) |
| `walkthroughs/` | Exercise တိုင်းအတွက် Python အခြေခံမှစ၍ လိုင်းတစ်လိုင်းချင်း ရှင်းပြသည့် ဖတ်စာ (`walkthroughs/01_pipeline_stage_ordering.md`) |

`explanation.md` subtopic များ — (၁) Course architecture နှင့် lab run ပုံ၊ (၂) RAG pipeline အခြေခံ၊
(၃) Plain Vector RAG ၏ ကန့်သတ်ချက်များ၊ (၄) Graph RAG သို့ ရောက်ရှိသည့် လမ်းကြောင်း၊
(၅) Knowledge Graph ၏ အစိတ်အပိုင်းများနှင့် Triple၊ (၆) Toolchain နှင့် environment။

### Walkthroughs

`solution.md` ရှိ code များကို Python အခြေခံမှ စတင်၍ အပိုင်းလိုက် လိုက်ဖတ်လိုပါက
`walkthroughs/` folder ကို ကြည့်ပါ။ Walkthrough တစ်ခုစီသည် exercise တစ်ခုစီအတွက် ဖြစ်ပြီး —
concept အသစ်များ (dictionary၊ tuple၊ set၊ while loop၊ list comprehension၊ `all()`၊ `assert`)
ကို ဥပမာနှင့် တွဲဖက် ရှင်းပြသည်။

| Walkthrough | Exercise |
|---|---|
| `walkthroughs/01_pipeline_stage_ordering.md` | Exercise 1 — RAG Pipeline Stage Ordering (Topological Sorting) |
| `walkthroughs/02_cosine_similarity_ranking.md` | Exercise 2 — Cosine Similarity Ranking |
| `walkthroughs/03_retrieval_modality_selection.md` | Exercise 3 — Retrieval Modality Selection |
| `walkthroughs/04_rag_failure_mode_classification.md` | Exercise 4 — RAG Failure Mode Classification |

## Prerequisites

- Python 3.9+ (standard library သာ — third-party package မလိုအပ်)
- Command line အခြေခံ၊ text file နှင့် JSON ကို ဖတ်နိုင်ခြင်း
- RAG၊ Embedding၊ LLM ဆိုသည့် ဝေါဟာရများကို တစ်ကြိမ်တစ်ခါ ကြားဖူးခြင်း (အသေးစိတ် မလိုအပ်)
- နောက် module များအတွက် — Docker နှင့် Neo4j (M05 မှစ၍ လိုအပ်သည်၊ ဤ module တွင် မလိုအပ်)

## Production Use Cases

- **Baseline သတ်မှတ်ခြင်း** — GraphRAG မတည်ဆောက်မီ Plain Vector RAG ၏ retrieval quality ကို
  baseline အဖြစ် တိုင်းတာထားခြင်းသည် နောက်ပိုင်း ရင်းနှီးမှု (graph build cost၊ ingestion latency) ကို
  ခုခံနိုင်သည့် အထောက်အထား ဖြစ်သည်။
- **Retrieval routing** — query အမျိုးအစားအလိုက် modality ရွေးချယ်ခြင်းသည် token cost နှင့် latency
  ကို လျှော့ချသည် — local fact query အားလုံးကို graph traversal ဖြင့် မဖြေရန် ဆုံးဖြတ်နိုင်သည်။
- **Pre-flight readiness gate** — corpus ကို GraphRAG pipeline ထဲ မထည့်မီ entity coverage၊
  duplicate rate၊ index ရှိ/မရှိ ကို စစ်ထုတ်ခြင်းသည် ingestion ရင်းနှီးမှု ပျက်ပြယ်ခြင်းကို ကာကွယ်သည်။

## References

- Neo4j — Cypher Manual: https://neo4j.com/docs/cypher-manual/current/
- Neo4j — Python Driver Manual: https://neo4j.com/docs/python-manual/current/
- Neo4j — Getting Started (Docker): https://neo4j.com/docs/operations-manual/current/docker/
- Microsoft GraphRAG (global summarization အကောင်အထည်ဖော်မှု): https://microsoft.github.io/graphrag/
- Edge et al., "From Local to Global: A Graph RAG Approach": https://arxiv.org/abs/2404.16130
- Python standard library: https://docs.python.org/3/library/
