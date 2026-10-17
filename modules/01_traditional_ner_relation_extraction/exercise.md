# M01 — Exercises: Traditional NER and Relationship Extraction

Exercise ၆ ခုလုံးကို `solution.md` မကြည့်မီ ကိုယ်တိုင် implement လုပ်ရမည်။ Python standard library သာ သုံးရမည်။
`lab.py` ကို run ပါက exercise တိုင်း၏ ရလဒ်ကို `assert` ဖြင့် စစ်ဆေးသည်။

## Exercise 1 — Regex-based NER

Fixed corpus မှ person name နှင့် date entity များကို `re` ဖြင့် ဆွဲထုတ်ပါ။ `{label: [surface, ...]}` dict ပြန်ရမည်။
**Input:** `Sundar Pichai visited London on 12 March 2019 to open the new Google office. Satya Nadella met Tim Cook in Paris on 3 January 2020.`
**Hints:** person အတွက် `\b[A-Z][a-z]+ [A-Z][a-z]+\b`၊ date အတွက် month alternation `(?:January|...|December)`။
**Expected behavior:** `PER` = `['Sundar Pichai', 'Satya Nadella', 'Tim Cook']`၊ `DATE` = `['12 March 2019', '3 January 2020']`။

## Exercise 2 — BIO tagging decode

Token list နှင့် tag list မှ entity span စာရင်း ပြန်ပေးသည့် `decode_bio()` ကို ရေးပါ။ Span တိုင်းတွင် `type`၊ `text`၊ `start`၊ `end` (exclusive) ပါရမည်။
**Input:** `tokens = ["Sundar","Pichai","visited","London","on","12","March","2019","."]`၊ `tags = ["B-PER","I-PER","O","B-LOC","O","B-DATE","I-DATE","I-DATE","O"]`
**Hints:** `B-` တွေ့ပါက လက်ရှိ span ကို ပိတ်ပြီး အသစ် စပါ။ `I-` သည် type တူပြီး span ဖွင့်ထားမှသာ ဆက်ရမည်။
**Expected behavior:** span ၃ ခု — `PER | Sundar Pichai | tokens[0:2]`၊ `LOC | London | tokens[3:4]`၊ `DATE | 12 March 2019 | tokens[5:8]`။ စဉ်အဆုံးတွင် span ဖွင့်ထားပါက ပိတ်ရမည်။

## Exercise 3 — Gazetteer lookup

Alias → `(type, canonical)` dict မှ mention များကို **longest match** ဖြင့် ရှာပါ။ Word boundary ကို တင်းကြပ်စွာ စစ်ရမည် (`isalnum`)။
**Input:** gazetteer — `"Google"`၊ `"Google LLC"` → `Google`၊ `"Alphabet"`၊ `"MSFT"` → `Microsoft`၊ `"Microsoft"`။ text — `"Google LLC is a subsidiary of Alphabet. MSFT competes with Google."`
**Hints:** key များကို length အနည်းစဉ် sort လုပ်ပါ။ match တွေ့ပါက index ကို match အလျားအတိုင်း ရှေ့တိုးပါ။
**Expected behavior:** alias အစဉ် `Google LLC`၊ `Alphabet`၊ `MSFT`၊ `Google`။ canonical အစဉ် `Google`၊ `Alphabet`၊ `Microsoft`၊ `Google`။ `Googleplex` ထဲမှ partial match မဖြစ်ရ။

## Exercise 4 — Pattern-based relationship extraction

Regex rule စာရင်း (`(pattern, relation)`) မှ `(subject, relation, object)` triple စာရင်း ပြန်ပေးပါ။
**Input:** text — `"Sundar Pichai is the CEO of Google. Larry Page founded Google."`။ rule — `CEO_OF` (trigger `is the CEO of`)၊ `FOUNDED` (trigger `founded`)။
**Hints:** `PERSON` pattern ကို rule တိုင်းတွင် ပြန်သုံးပါ။ subject = capture group 1၊ object = group 2။
**Expected behavior:** `('Sundar Pichai', 'CEO_OF', 'Google')` နှင့် `('Larry Page', 'FOUNDED', 'Google')` ပါရမည်။ triple စုစုပေါင်း ၂ ခု သာ (duplicate မဖြစ်ရ)။

## Exercise 5 — Coreference resolution

Pronoun (`He`၊ `She`၊ `His`၊ `Her`၊ `They`၊ `Their`) များကို ယခင် person ဖြင့် အစားထိုးပါ။ Possessive ဖြစ်ပါက `'s` ထည့်ရမည်။
**Input:** persons — `{"Sundar Pichai": "M", "Larry Page": "M"}`။ text — `"Sundar Pichai leads Google. He became CEO in 2015. His tenure expanded the company."`
**Hints:** `re.sub()` ကို callable replacement function ဖြင့် သုံးပါ။ လက်ရှိ person ကို state (`dict`) တွင် မှတ်ပါ။
**Expected behavior:** output — `Sundar Pichai leads Google. Sundar Pichai became CEO in 2015. Sundar Pichai's tenure expanded the company.`။ `He` လုံးဝ မကျန်ရ။

## Exercise 6 — Precision / Recall / F1 evaluation

Gold နှင့် predicted triple set ကို exact match (subject၊ relation၊ object အားလုံး တူရမည်) ဖြင့် နှိုင်းယှဉ်ပါ။
**Input:** gold — `(Sundar Pichai, CEO_OF, Google)`၊ `(Larry Page, FOUNDED, Google)`၊ `(Satya Nadella, CEO_OF, Microsoft)`။ predicted — `(Sundar Pichai, CEO_OF, Google)`၊ `(Larry Page, FOUNDED, Google)`၊ `(Sundar Pichai, CEO_OF, Alphabet)`။
**Hints:** set operation — `TP = |gold ∩ pred|`၊ `FP = |pred − gold|`၊ `FN = |gold − pred|`။ denominator သုည ဖြစ်နိုင်သော case ကို handle လုပ်ပါ။
**Expected behavior:** `tp=2 fp=1 fn=1` နှင့် `precision=0.6667 recall=0.6667 f1=0.6667`။

## Self-check

- [ ] exercise ၆ ခုလုံး `bool` ပြန်သည်၊ ကျရှုံးပါက `AssertionError` ဖြင့် ရပ်သည်
- [ ] external package တစ်ခုမှ မသုံးထားပါ၊ `random` မပါ၊ output သည် deterministic ဖြစ်သည်
- [ ] `python3 modules/01_traditional_ner_relation_extraction/lab.py` → exit code 0
