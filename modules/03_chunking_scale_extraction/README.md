# M03 — Chunking: Entity and Relationship Extraction with LLMs at Scale

Module ဤသည် LLM-based extraction ကို corpus အရွယ်အစား ကြီးမားသည့်အခါ ဘယ်လို run ရမည်ကို ဖြေရှင်းပေးသည်။
Entity နှင့် Relationship extraction သည် chunk တစ်ခုတည်းအတွင်းတွင်သာ အလုပ်လုပ်သောကြောင့် chunk boundary
ရွေးချယ်မှုသည် recall ကို တိုက်ရိုက် သက်ရောက်သည်။ Chunk အလွန်သေးပါက relationship များ ပြတ်တောက်ပြီး
chunk အလွန်ကြီးပါက token cost နှင့် latency တိုးလာသည်။ ဤ module သည် chunk size၊ overlap၊ Map-Reduce
pattern၊ cross-chunk reconnection၊ Triple deduplication နှင့် scale အတွက် batching/concurrency/checkpointing/
Idempotency/failure recovery ကို တိုင်းတာနိုင်သော engineering နည်းလမ်းများဖြင့် တင်ပြသည်။

## သင်ယူလေ့လာမည့် အကြောင်းအရာများ

- Chunk size နှင့် overlap သည် extraction precision/recall ကို ဘယ်လို သက်ရောက်သည်
- Token budget နှင့် Context Window ဆက်စပ်မှုမှ chunk size ကို ဘယ်လို တွက်ချက်သည်
- Map-Reduce extraction pattern ဖြင့် chunk တိုင်းမှ extract လုပ်ပြီး စုစည်းခြင်း
- Chunk boundary ဖြတ်သွားသော entity pair များကို ပြန်ချိတ်ဆက်ခြင်း (cross-chunk reconnection)
- Chunk အသီးသီးမှ ထွက်လာသော Triple များကို deduplicate လုပ်ပြီး merge လုပ်ခြင်း
- Batch၊ concurrency၊ Checkpoint၊ Idempotency နှင့် failure recovery ဖြင့် scale လုပ်ခြင်း

## Module အစိတ်အပိုင်းများ

| File | အကြောင်းအရာ |
|---|---|
| `README.md` | Module scope၊ objectives၊ prerequisites၊ production use cases |
| `explanation.md` | သဘောတရား ၆ ပိုင်း၊ formula၊ deterministic code၊ production considerations |
| `exercise.md` | ကိုယ်တိုင် implement လုပ်ရမည့် လေ့ကျင့်ခန်း ၆ ခု (Hints + Expected behavior) |
| `solution.md` | Exercise ၆ ခုအတွက် reference implementation အပြည့်အစုံ |
| `lab.py` | Standard library သာ သုံးသော executable lab (exercise ၆ ခု၊ `assert` ဖြင့် စစ်ဆေး) |
| `walkthroughs/` | Exercise တိုင်းအတွက် Python အခြေခံမှစ၍ အပိုင်းလိုက် ရှင်းပြသည့် ဖတ်စာ |

**explanation.md subtopics** — (၁) Chunk size နှင့် extraction quality၊ (၂) Token budget နှင့် Context Window
အပေါ် အခြေခံသော size/overlap ရွေးချယ်မှု၊ (၃) Map-Reduce extraction pattern၊ (၄) Cross-chunk relationship
reconnection၊ (၅) Triple deduplication နှင့် merge၊ (၆) Batching၊ concurrency၊ Checkpoint၊ Idempotency နှင့်
failure recovery။

### Walkthroughs

`solution.md` ရှိ code များကို Python အခြေခံမှ စတင်၍ အပိုင်းလိုက် လိုက်ဖတ်လိုပါက
`walkthroughs/` folder ကို ကြည့်ပါ။ Walkthrough တစ်ခုစီသည် exercise တစ်ခုစီအတွက် ဖြစ်ပြီး —
concept အသစ်များ (`while` loop၊ chained comparison၊ dict comprehension၊ `setdefault()`၊
`all()`၊ `zip()`၊ `dict.fromkeys()`၊ class နှင့် `self`၊ fixed-seed LCG၊ `while ... else`) ကို
ဥပမာနှင့် တွဲဖက် ရှင်းပြသည်။

| Walkthrough | Exercise |
|---|---|
| `walkthroughs/01_fixed_size_chunking.md` | Exercise 1 — Fixed-size chunking |
| `walkthroughs/02_chunk_overlap.md` | Exercise 2 — Overlap ထည့်ခြင်း |
| `walkthroughs/03_map_reduce_aggregation.md` | Exercise 3 — Map-Reduce triple aggregation |
| `walkthroughs/04_cross_chunk_relationships.md` | Exercise 4 — Cross-chunk relationship ပြန်ချိတ်ခြင်း |
| `walkthroughs/05_triple_dedup_merge.md` | Exercise 5 — Triple deduplication နှင့် merge |
| `walkthroughs/06_idempotent_batch_runner.md` | Exercise 6 — Idempotent batch runner |

## Prerequisites

- M02 — LLM-based entity/relationship extraction နှင့် structured output parsing၊ entity resolution
- Python 3.10+ (`dataclasses`၊ type hint) နှင့် standard library (`re`, `hashlib`, `collections`)
- Token နှင့် Context Window အယူအဆ အခြေခံ

## Production Use Cases

- စာရွက်စာတမ်း ထောင်ပေါင်းများစွာမှ Knowledge Graph တည်ဆောက်ခြင်း — chunk တိုင်းကို Map phase အဖြစ်
  parallel run လုပ်ပြီး Reduce phase တွင် deduplicate လုပ်ခြင်း
- Long-document extraction — overlap ဖြင့် boundary relationship များ မဆုံးရှုံးစေရန် ထိန်းချုပ်ခြင်း
- Incremental re-ingestion — checkpoint ကို သိမ်းထားခြင်းဖြင့် ပြောင်းလဲသော document များကိုသာ ပြန် run ခြင်း
- Pipeline ကျရှုံးပြီး ပြန်စသည့်အခါ Idempotency ကြောင့် duplicate Triple များ မဖြစ်ပေါ်စေရန် ကာကွယ်ခြင်း

## References

- Neo4j GraphRAG for Python — https://neo4j.com/docs/neo4j-graphrag-python/current/
- Neo4j Cypher Manual, `MERGE` — https://neo4j.com/docs/cypher-manual/current/clauses/merge/
- Neo4j Cypher Manual, `UNWIND` — https://neo4j.com/docs/cypher-manual/current/clauses/unwind/
- LangChain Text splitters (chunking concepts) — https://python.langchain.com/docs/concepts/text_splitters/
- From Local to Global: A Graph RAG Approach (Microsoft GraphRAG) — https://arxiv.org/abs/2404.16130
