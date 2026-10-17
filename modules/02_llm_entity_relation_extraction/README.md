# M02 — Improved Entity and Relationship Extraction Using LLMs

Module ဤသည် classical NER pipeline (M01) ၏ ကန့်သတ်ချက်များကို LLM-based extraction ဖြင့် ကျော်လွှားပုံကို
ဖော်ပြသည်။ အဓိကပြဿနာမှာ model ကို ယုံကြည်စိတ်ချရန်မဟုတ်ဘဲ **model output ကို engineering discipline
ဖြင့် စစ်ထုတ်နိုင်သော pipeline အဖြစ် ပြောင်းလဲခြင်း** ဖြစ်သည် — Prompt design၊ JSON Schema enforcement၊
malformed output handling၊ Entity Resolution နှင့် grounding-based Hallucination filter များဖြစ်သည်။

## သင်ယူလေ့လာမည့် အကြောင်းအရာများ

- Zero-shot / few-shot Prompt ဖြင့် entity type နှင့် relationship type များကို code ပြောင်းလဲမှုမလိုဘဲ
  schema အသစ်အဖြစ် သတိပေးနိုင်ခြင်း
- Extraction Prompt design — entity type list၊ allowed relationship list၊ output JSON Schema တို့ကို
  တိကျစွာ သတ်မှတ်ခြင်းနှင့် untrusted input ကို delimiter ဖြင့် ခွဲထုတ်ခြင်း
- Structured output enforcement — JSON Schema validation၊ malformed output (code fence၊ trailing comma၊
  truncation) ကို repair သို့မဟုတ် retry ဖြင့် ကိုင်တွယ်ခြင်း
- Entity Resolution — alias mapping၊ normalized fuzzy matching နှင့် canonical name selection
- Hallucination filter / grounding check — source text တွင် မတွေ့ရှိသော entity/relationship ကို ဖယ်ရှားခြင်း
- Token cost၊ latency နှင့် prompt injection အန္တရာယ် ခန့်မှန်းခြင်း

## Module အစိတ်အပိုင်းများ

| File | ရည်ရွယ်ချက် |
|---|---|
| `README.md` | Module scope၊ objectives၊ prerequisites၊ references |
| `explanation.md` | Subtopic ၆ ခု၏ သဘောတရားနှင့် production considerations |
| `exercise.md` | ကိုယ်တိုင် implement လုပ်ရမည့် exercise ၆ ခု |
| `solution.md` | Exercise တိုင်းအတွက် reference implementation |
| `lab.py` | Standard library သာ သုံး၍ run နိုင်သော executable lab (offline) |

`explanation.md` တွင် ဖော်ပြမည့် subtopic များ —

1. LLM-based extraction သည် classical NER ကို ဘာကြောင့် ကျော်လွှားသနည်း — zero-shot / few-shot
2. Extraction prompt design — entity type၊ allowed relationship၊ output schema
3. Structured output enforcement — JSON Schema validation နှင့် retry strategy
4. Entity resolution — alias mapping နှင့် fuzzy matching
5. Extraction quality control — hallucination filter၊ grounding check
6. Cost၊ latency နှင့် ကန့်သတ်ချက်များ — token cost၊ prompt injection၊ rate limit

## Prerequisites

- M01 ပြီးစီးထားခြင်း (NER၊ BIO tagging၊ classical pipeline ၏ ကန့်သတ်ချက်များ)
- Python standard library အသုံးပြုနိုင်ခြင်း — `re`၊ `json`၊ `difflib`၊ `unicodedata`
- JSON Schema ၏ အခြေခံ (`type`၊ `required`၊ `properties`၊ `enum`)
- Knowledge Graph ၏ Triple (subject–predicate–object) သဘောတရား

## Production Use Cases

- Unstructured document များမှ triple များကို batch extract လုပ်ပြီး Neo4j သို့ ingestion မလုပ်မီ
  quality gate အဖြစ် grounding filter အသုံးပြုခြင်း
- Customer-supplied text များတွင် prompt injection ရှာဖွေခြင်း (retrieval-augmented pipeline ၏
  လုံခြုံရေးအဆင့်)
- အဖွဲ့အစည်းအတွင်း entity များ၏ alias စာရင်း (ဥပမာ ကုမ္ပဏီအမည် အတိုကောက်များ) ကို canonical node
  အဖြစ် ပေါင်းစည်းခြင်း
- LLM extraction ကို run မီ token cost နှင့် latency ကို ခန့်မှန်း၍ budget လျာထားခြင်း

## References

- OpenAI Structured Outputs — https://platform.openai.com/docs/guides/structured-outputs
- OpenAI Prompt Engineering guide — https://platform.openai.com/docs/guides/prompt-engineering
- JSON Schema specification — https://json-schema.org/understanding-json-schema/
- Python `difflib` documentation — https://docs.python.org/3/library/difflib.html
- Python `json` documentation — https://docs.python.org/3/library/json.html
- OWASP LLM01: Prompt Injection — https://genai.owasp.org/llmrisk/llm01-prompt-injection/
- Neo4j Cypher `MERGE` (downstream ingestion) — https://neo4j.com/docs/cypher-manual/current/clauses/merge/
