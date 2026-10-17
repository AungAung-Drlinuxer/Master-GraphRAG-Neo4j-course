# M01 — Traditional NER and Relationship Extraction

ဤ module သည် text မှ Entity နှင့် Relationship များကို ဆွဲထုတ်ရာတွင် အသုံးပြုသော classical (rule-based နှင့်
statistical) နည်းလမ်းများကို ဖော်ပြသည်။ LLM-based extraction ကို မသုံးမီ အခြေခံ mechanism များကို နားလည်ထားခြင်းသည်
နောက်ပိုင်း module များတွင် extraction quality ကို တိုင်းတာရန်နှင့် LLM output ကို validate လုပ်ရန် လိုအပ်သည်။
ဤနည်းလမ်းများသည် dependency မရှိ၊ deterministic ဖြစ်ပြီး latency နည်းသော်လည်း domain shift နှင့်
unseen entity type များတွင် recall ကျဆင်းသည်။

## သင်ယူလေ့လာမည့် အကြောင်းအရာများ

- Token classification နှင့် BIO tagging scheme (`B-PER`, `I-PER`, `O`) ကို decode လုပ်ပုံ
- Rule-based NER — regex pattern နှင့် Gazetteer lookup (longest match)
- Statistical NER — CRF ချဉ်းကပ်နည်း၏ feature engineering သဘောတရား
- Relationship Extraction — pattern-based နှင့် dependency parsing ချဉ်းကပ်နည်း
- Coreference resolution နှင့် duplicate node ဖြစ်ပေါ်ခြင်း၏ ဆက်စပ်မှု
- Classical pipeline ၏ ကန့်သတ်ချက်များနှင့် evaluation (Precision, Recall, F1)

## Module အစိတ်အပိုင်းများ

| File | အကြောင်းအရာ |
|---|---|
| `README.md` | Module scope၊ objectives၊ prerequisites၊ references |
| `explanation.md` | Subtopic ၆ ခု၏ သဘောတရားရှင်းလင်းချက်၊ formula၊ deterministic code example |
| `exercise.md` | ကိုယ်တိုင် implement လုပ်ရမည့် လေ့ကျင့်ခန်း ၆ ခု (Hints + Expected behavior) |
| `solution.md` | Exercise တိုင်းအတွက် reference implementation |
| `lab.py` | Standard library သာ သုံး၍ run နိုင်သော executable lab (exercise ၆ ခု) |
| `walkthroughs/` | Exercise တိုင်းအတွက် Python အခြေခံမှစ၍ အပိုင်းလိုက် ရှင်းပြသည့် ဖတ်စာ |

`explanation.md` တွင် အောက်ပါ subtopic များကို အစဉ်လိုက် ဖော်ပြသည် —

1. NER အခြေခံနှင့် Token classification — BIO tagging scheme
2. Rule-based နှင့် statistical NER — gazetteer၊ regex၊ CRF
3. Relationship Extraction — pattern-based နှင့် dependency parsing
4. Coreference resolution — antecedent mapping
5. Classical pipeline ၏ ကန့်သတ်ချက်များ — domain shift၊ training data၊ recall
6. Evaluation — Precision၊ Recall၊ F1

### Walkthroughs

`solution.md` ရှိ code များကို Python အခြေခံမှ စတင်၍ အပိုင်းလိုက် လိုက်ဖတ်လိုပါက
`walkthroughs/` folder ကို ကြည့်ပါ။ Walkthrough တစ်ခုစီသည် exercise တစ်ခုစီအတွက် ဖြစ်ပြီး —
concept အသစ်များ (`zip`၊ `enumerate`၊ set operations၊ `sorted(key=…)`၊ `while` loop၊
`finditer()`၊ callback function၊ short-circuit evaluation၊ closure) ကို ဥပမာနှင့်
တွဲဖက် ရှင်းပြသည်။

| Walkthrough | Exercise |
|---|---|
| `walkthroughs/01_regex_ner.md` | Exercise 1 — Regex-based NER |
| `walkthroughs/02_bio_tag_decoding.md` | Exercise 2 — BIO Tag Decoding |
| `walkthroughs/03_gazetteer_lookup.md` | Exercise 3 — Gazetteer Lookup |
| `walkthroughs/04_pattern_relationship_extraction.md` | Exercise 4 — Pattern-based Relationship Extraction |
| `walkthroughs/05_coreference_resolution.md` | Exercise 5 — Rule-based Coreference Resolution |
| `walkthroughs/06_precision_recall_f1.md` | Exercise 6 — Precision, Recall, F1 |

## Prerequisites

- Python အခြေခံ syntax (function၊ `dict`၊ `list`၊ `re` module) — ဤ module ၏ ရှင်းလင်းချက်များသည်
  program အခြေခံသဘောတရားကို ရှေးရှေးသိပြီးသားဟု ယူဆသည်။ အခြေခံမှ စတင်လိုပါက `walkthroughs/` ကို ဖတ်ပါ
- Regular expression အခြေခံ (capture group၊ word boundary `\b`)
- `re`, `json`, `collections` စသည့် standard library module များ အသုံးပြုနိုင်ခြင်း
- M00 ပြီးစီးထားခြင်း (Knowledge Graph၊ Triple၊ Node၊ Relationship အခြေခံသတ်မှတ်ချက်များ)

## Production Use Cases

- **High-volume, low-latency ingestion** — LLM call မလိုဘဲ regex/gazetteer ဖြင့် milli-second အဆင့် extraction
- **Closed-domain corpora** — medical code၊ ticker symbol၊ product SKU ကဲ့သို့ fixed vocabulary ရှိသော domain များ
- **Deterministic baseline** — LLM extraction ၏ Precision/Recall ကို နှိုင်းယှဉ်ရန် baseline အဖြစ်
- **Post-processing guardrail** — LLM output ထဲရှိ entity များကို gazetteer ဖြင့် ground လုပ်ခြင်း

## References

- spaCy — Linguistic Features / Named Entities: https://spacy.io/usage/linguistic-features#named-entities
- NLTK Book, Chapter 7 — Extracting Information from Text: https://www.nltk.org/book/ch07.html
- Stanford NER (CRF classifier) documentation: https://nlp.stanford.edu/software/CRF-NER.html
- CoNLL-2003 shared task (BIO tagging convention): https://www.clips.uantwerpen.be/conll2003/ner/
