# M04 — Project: Create a Knowledge Graph from Text

ဤ module သည် M01–M03 တွင် သီးခြားစီ လေ့လာခဲ့သည့် NER၊ LLM-based Entity နှင့် Relationship Extraction၊ Chunking၊
Entity Resolution နှင့် Deduplication ကို **end-to-end Pipeline တစ်ခုတည်း** အဖြစ် ပေါင်းစည်းသည်။
Input သည် raw text corpus ဖြစ်ပြီး output သည် validated Knowledge Graph ဖြစ်သည် — ထို graph ကို Cypher
`MERGE` statements၊ JSON triple list နှင့် Neo4j Admin Import CSV သုံးမျိုးဖြင့် export လုပ်သည်။
Course အတွင်း ဤ module သည် "Project: Create a Knowledge Graph from Text" ၏ အကောင်အထည်ဖော်မှု ဖြစ်သည်။

## သင်ယူလေ့လာမည့် အကြောင်းအရာများ

- raw text corpus မှ validated Knowledge Graph အထိ Pipeline အဆင့်ဆင့်ကို ဒီဇိုင်းဆွဲခြင်း
- Node label၊ Relationship type နှင့် property schema ကို contract အဖြစ် သတ်မှတ်ခြင်း
- Triple တိုင်းတွင် Provenance (source chunk id၊ confidence၊ extraction method) မှတ်သားခြင်း
- Quality Gate ဖြင့် self-loop၊ empty endpoint၊ low confidence၊ unknown predicate စသည်ကို စစ်ထုတ်ခြင်း
- Canonical id နှင့် idempotent Cypher `MERGE` သုံး၍ export လုပ်ခြင်း
- Deterministic scripted extractor ဖြင့် LLM မလိုဘဲ Pipeline တစ်ခုလုံးကို ပြန်လည် run နိုင်ခြင်း

## Module အစိတ်အပိုင်းများ

| File | အကြောင်းအရာ |
|---|---|
| `README.md` | Module scope၊ learning objectives၊ prerequisites၊ production use cases |
| `explanation.md` | Pipeline ဒီဇိုင်း၊ data model၊ provenance၊ quality gate၊ export format |
| `exercise.md` | ကိုယ်တိုင် implement လုပ်ရမည့် လေ့ကျင့်ခန်း ၆ ခု (Hints + Expected behavior) |
| `solution.md` | Exercise တိုင်းအတွက် reference implementation |
| `lab.py` | Run နိုင်သော end-to-end lab (exercise ၆ ခု၊ `assert` ဖြင့် စစ်ဆေးသည်) |

`explanation.md` တွင် ဖော်ပြသည့် subtopic များ —

1. Project scope နှင့် deliverable — raw text corpus မှ validated Knowledge Graph အထိ
2. Pipeline အဆင့်ဆင့် — ingest → normalize → chunk → extract → resolve → merge → validate → export
3. Data model ဒီဇိုင်း — Node label များ၊ Relationship type များ၊ property schema
4. Provenance tracking — source chunk id၊ confidence၊ extraction method
5. Quality gates — empty triple၊ self-loop၊ missing endpoint၊ duplicate triple စစ်ထုတ်ခြင်း
6. Export format — Cypher `MERGE` statements၊ JSON triple list၊ CSV (Neo4j Admin Import)

## Prerequisites

- M01 — rule-based NER နှင့် pattern-based Relationship Extraction
- M02 — LLM extraction output schema၊ Entity Resolution၊ hallucination filter
- M03 — fixed-size Chunking၊ map-reduce triple aggregation၊ deduplication
- Python standard library level — `re`၊ `json`၊ `dataclasses`၊ `difflib`၊ `collections`
- Cypher အခြေခံ — `MERGE`၊ `MATCH`၊ parameter `$param` (M05 တွင် အသေးစိတ်)

## Production Use Cases

- **Document intelligence** — စာချုပ်၊ သတင်းနှင့် report များမှ entity/relationship graph ကို nightly batch အဖြစ် တည်ဆောက်ခြင်း
- **GraphRAG knowledge base** — M07 ၏ Retrieval အတွက် triple များကို provenance အပြည့်အစုံဖြင့် ထုတ်လုပ်ခြင်း
- **Compliance audit** — triple တိုင်း၏ source chunk id ကြောင့် ရလဒ်ကို မူရင်းစာသားအထိ trace ပြန်လိုက်နိုင်ခြင်း
- **Catalog ပေါင်းစည်းခြင်း** — alias များသော product/company အမည်များကို Entity Resolution ဖြင့် merge လုပ်ခြင်း

## References

- Neo4j Cypher — `MERGE` clause: https://neo4j.com/docs/cypher-manual/current/clauses/merge/
- Neo4j Cypher Manual: https://neo4j.com/docs/cypher-manual/current/
- Neo4j Admin Import (CSV): https://neo4j.com/docs/operations-manual/current/tools/neo4j-admin/neo4j-admin-import/
- Neo4j constraints (uniqueness): https://neo4j.com/docs/cypher-manual/current/constraints/
- Python `unicodedata`: https://docs.python.org/3/library/unicodedata.html
- Python `difflib` (SequenceMatcher): https://docs.python.org/3/library/difflib.html
