# M01 — Traditional NER and Relationship Extraction

ဤဖိုင်သည် classical NER နှင့် Relationship Extraction ၏ mechanism များကို ဖော်ပြသည်။ ဤနည်းလမ်းများသည်
Knowledge Graph ၏ Triple အရေအတွက်ကို တိုးပွားစေသော်လည်း precision/recall trade-off သည်
သတ်မှတ်ချက် (domain, language, entity type) ပေါ်တွင် ပြင်းထန်စွာ မှီခိုသည်။

## ၁။ NER အခြေခံနှင့် Token classification — BIO tagging scheme

NER သည် token တစ်ခုချင်းစီကို class တစ်ခုသို့ ခန့်အပ်သည် (token classification)။ Multi-token entity
(ဥပမာ `Sundar Pichai`) ကို တစ်ခုတည်းသော unit အဖြစ် ဖမ်းရန် **BIO tagging scheme** ကို သုံးသည် —

| Tag | အဓိပ္ပာယ် |
|---|---|
| `B-X` | entity type `X` ၏ ပထမ token (Beginning) |
| `I-X` | အလယ်/အဆုံး token (Inside) |
| `O` | entity မဟုတ်သော token (Outside) |

Token တိုင်းအတွက် tag တစ်ခုစီ ခန့်အပ်ထားသဖြင့် tag စဉ်ကို ပြန်ဖျက်ခြင်း (decode) ဖြင့် entity span ကို
ရရှိသည်။ ဤဖော်ပြချက်သည် fixed-length output ဖြစ်သဖြင့် CRF၊ BiLSTM၊ Transformer စသည့် model
များအတွက် တူညီသော interface ဖြစ်သည် — mechanism မတူသော်လည်း decode သည် အတူတူ ဖြစ်သည်။

```python
def decode_bio(tokens, tags):
    spans, current = [], None
    for index, (token, tag) in enumerate(zip(tokens, tags)):
        if tag.startswith("B-"):
            if current is not None:
                spans.append(current)
            current = {"type": tag[2:], "tokens": [token],
                       "start": index, "end": index + 1}
        elif tag.startswith("I-") and current and tag[2:] == current["type"]:
            current["tokens"].append(token)
            current["end"] = index + 1
        else:
            if current is not None:
                spans.append(current)
            current = None
    if current is not None:
        spans.append(current)
    return [{"type": s["type"], "text": " ".join(s["tokens"]),
             "start": s["start"], "end": s["end"]} for s in spans]

tokens = ["Sundar", "Pichai", "visited", "London", "on",
          "12", "March", "2019", "."]
tags = ["B-PER", "I-PER", "O", "B-LOC", "O",
        "B-DATE", "I-DATE", "I-DATE", "O"]
for span in decode_bio(tokens, tags):
    print(span["type"], "|", span["text"], "|", span["start"], span["end"])
# Expected output:
# PER | Sundar Pichai | 0 2
# LOC | London | 3 4
# DATE | 12 March 2019 | 5 8
```

**Rationale** — `B-` tag သည် boundary ကို တိကျစွာ သတ်မှတ်သဖြင့် entity နှစ်ခု ကပ်လျက် ရှိသည့်အခါ
(ဥပမာ `B-PER B-PER`) မှားယွင်းစွာ merge မဖြစ်စေပါ။

**မသုံးသင့်သည့်အခါ** — `I-` tag ဖြင့် စသော tag စဉ် (invalid transition) ကို ခွင့်ပြုသော model များတွင်
`B-` မပါဘဲ entity စတင်ခြင်းကို ပိတ်ရမည်။ Constraint decoding (Viterbi with transition rules) မပါပါက
invalid sequence များ ထွက်လာနိုင်သည်။

## ၂။ Rule-based နှင့် statistical NER — gazetteer၊ regex၊ CRF

### ၂.၁ Regex-based NER

Regex သည် fixed surface pattern (date၊ ticket number၊ email) အတွက် အကောင်းဆုံး ချဉ်းကပ်နည်း ဖြစ်သည်။
Capitalized word pair ကို person အဖြစ် ခန့်မှန်းနိုင်သည် —

```python
import re

PERSON_RE = re.compile(r"\b[A-Z][a-z]+ [A-Z][a-z]+\b")
text = ("Sundar Pichai visited London on 12 March 2019. "
        "Satya Nadella met Tim Cook in Paris.")
print(PERSON_RE.findall(text))
# Expected output:
# ['Sundar Pichai', 'Satya Nadella', 'Tim Cook']
```

**Rationale** — regex သည် zero training data ဖြင့် စတင်နိုင်ပြီး latency သည် microsecond အဆင့် ဖြစ်သည်။

**မသုံးသင့်သည့်အခါ** — ဤ pattern သည် sentence ပထမစကားလုံး၊ product name၊ place name များကိုပါ
person အဖြစ် မှားယွင်း ခန့်အပ်သည် (false positive)။ `London on 12 March` ကဲ့သို့ ဖြစ်ရပ်တွင်
`[A-Z][a-z]+ [A-Z][a-z]+` သည် `Tim Cook` လို မှန်သော case နှင့် မခွဲခြားနိုင်ပါ။

### ၂.၂ Gazetteer lookup

Gazetteer သည် alias → canonical name mapping ဖြစ်သည်။ Longest-match strategy သည် `Google LLC` ကို
`Google` အဖြစ် မဖြတ်တောက်စေဘဲ ပြန်ညွှန်းသည်။ ဤအဆင့်သည် **Entity Resolution** ၏ အစိတ်အပိုင်း ဖြစ်သည်။

```python
GAZETTEER = {
    "Google": ("ORG", "Google"),
    "Google LLC": ("ORG", "Google"),
    "Alphabet": ("ORG", "Alphabet"),
    "MSFT": ("ORG", "Microsoft"),
}

def gazetteer_lookup(text, gazetteer):
    keys = sorted(gazetteer, key=len, reverse=True)  # longest first
    matches, index = [], 0
    while index < len(text):
        for key in keys:
            end = index + len(key)
            if text.startswith(key, index) \
                    and (index == 0 or not text[index - 1].isalnum()) \
                    and (end == len(text) or not text[end].isalnum()):
                matches.append((key, gazetteer[key]))
                index = end
                break
        else:
            index += 1
    return matches

print(gazetteer_lookup("Google LLC is a subsidiary of Alphabet. MSFT competes.", GAZETTEER))
# Expected output:
# [('Google LLC', ('ORG', 'Google')), ('Alphabet', ('ORG', 'Alphabet')), ('MSFT', ('ORG', 'Microsoft'))]
```

**Rationale** — gazetteer သည် canonical name ကို တိုက်ရိုက် ပေးသဖြင့် alias မှ duplicate node
ဖြစ်ပေါ်ခြင်းကို မဖြစ်မီ တားဆီးသည်။ Boundary check (`isalnum`) မပါပါက `Googleplex` ထဲမှ `Google` ကို
မှားယွင်း ဖမ်းသည်။

**မသုံးသင့်သည့်အခါ** — vocabulary ကြီးလာသည့်အခါ linear scan သည် `O(len(text) × len(keys))` ဖြစ်လာသည်။
Real production တွင် trie/Aho–Corasick automaton သို့မဟုတ် DB-backed dictionary သို့ ပြောင်းရမည်။

### ၂.၃ Statistical NER — CRF

CRF (Conditional Random Field) သည် sequence labeler ဖြစ်ပြီး adjacent tag များအကြား dependency ကို
model လုပ်သည်။ Feature များမှာ — word shape (`Xxxx`၊ `XX`)၊ prefix/suffix (၃–၄ character)၊
previous/next word၊ gazetteer membership ဖြစ်သည်။

လေ့ကျင့်ရန် `(token, tag)` pair ရာဂဏန်းမှ ထောင်ဂဏန်းအထိ လိုအပ်သည်။ Domain shift (news corpus →
clinical note) ဖြစ်ပါက feature distribution ပြောင်းသွားသဖြင့် recall သိသိသာသာ ကျဆင်းသည်။
ဤအကြောင်းကြောင့် LLM-based extraction သည် schema ကို prompt ဖြင့် ပြောင်းနိုင်သော အားသာချက် ရရှိသည် (M02)။

## ၃။ Relationship Extraction — pattern-based နှင့် dependency parsing

### ၃.၁ Pattern-based extraction

Trigger phrase (`is the CEO of`၊ `founded`၊ `acquired`) ကို regex pattern အဖြစ် သတ်မှတ်ပြီး
subject-object pair ကို triple အဖြစ် ဆွဲထုတ်သည် —

```python
PERSON = r"\b[A-Z][a-z]+ [A-Z][a-z]+\b"
RULES = [
    (re.compile(r"(%s) is the CEO of ([A-Z][A-Za-z]+)" % PERSON), "CEO_OF"),
    (re.compile(r"(%s) founded ([A-Z][A-Za-z]+)" % PERSON), "FOUNDED"),
]
text = "Sundar Pichai is the CEO of Google. Larry Page founded Google."

triples = [(m.group(1), rel, m.group(2))
           for pat, rel in RULES for m in pat.finditer(text)]
print(triples)
# Expected output:
# [('Sundar Pichai', 'CEO_OF', 'Google'), ('Larry Page', 'FOUNDED', 'Google')]
```

**Rationale** — pattern သည် deterministic ဖြစ်ပြီး precision မြင့်သည်။ သို့သော် coverage သည်
pattern အရေအတွက်အပေါ် တိုက်ရိုက် မှီခိုသည် — `is the CEO of` မှ `became CEO of`၊ `serves as CEO of`
စသည်တို့ကို မဖမ်းပါ။

**မသုံးသင့်သည့်အခါ** — Pattern အရေအတွက် တိုးလာသည်နှင့်အမျှ maintenance cost နှင့် false positive
နှုန်းသည် တပြိုင်နက် တက်လာသည်။ Paraphrase (တူညီသော အဓိပ္ပာယ်၊ မတူညီသော စကားလုံး) များအတွက်
pattern ဖြင့် မလုံလောက်ပါ။

### ၃.၂ Dependency parsing

Dependency tree သည် grammatical relation (`nsubj`၊ `dobj`၊ `prep`၊ `pobj`) ကို ပေးသည်။
`(nsubj) ← verb → (dobj)` path ကို ရှာခြင်းဖြင့် word order ပြောင်းလဲမှုကို ခံနိုင်ရည် ရှိသည်။

**Rationale** — surface order မဟုတ်ဘဲ syntax structure ကို သုံးသဖြင့် pattern ထက် general ဖြစ်သည်။
**မသုံးသင့်သည့်အခါ** — parser error propagation ဖြစ်သည် — parse မှားပါက extraction မှာ အလိုအလျောက်
မှားသည်။ Short text (social post၊ heading) တွင် dependency signal အားနည်းသည်။

### ၃.၃ Distance supervision

Knowledge base (တကယ်ရှိသော triple) ကို label အဖြစ် သုံး၍ sentence များကို automatic label လုပ်သည်။
ဤနည်းသည် labeling cost ကို သုညနီးပါး လျှော့ချသော်လည်း noisy label များ (false positive triple)
ထည့်သွင်းသည်။

## ၄။ Coreference resolution — antecedent mapping

Pronoun (`He`၊ `She`၊ `It`၊ `They`) နှင့် possessive (`His`၊ `Her`) များကို ယခင် ဖော်ပြထားသော
entity သို့ ပြန်ညွှန်းသည်။ ဤအဆင့် မရှိပါက entity တစ်ခုတည်းမှ mention များစွာ ထွက်လာပြီး
Knowledge Graph တွင် duplicate node (isolated component) များ ဖြစ်ပေါ်သည်။

```python
import re

persons = {"Sundar Pichai": "M"}
pattern = re.compile(r"\b(%s|He|She|His|Her)\b"
                     % "|".join(re.escape(n) for n in persons))
state = {"last": None}

def replace(match):
    token = match.group(1)
    if token in persons:
        state["last"] = token
        return token
    if state["last"] is None:
        return token
    return state["last"] + "'s" if token.lower() in {"his", "her"} else state["last"]

text = "Sundar Pichai leads Google. He became CEO in 2015. His tenure expanded."
print(pattern.sub(replace, text))
# Expected output:
# Sundar Pichai leads Google. Sundar Pichai became CEO in 2015. Sundar Pichai's tenure expanded.
```

**Rationale** — Coreference resolution သည် Entity Resolution ၏ အဓိက အကြောင်းရင်း ဖြစ်သည်။ Node
တစ်ခုတည်းသာ ရှိရမည့် entity မှ node များစွာ ဖြစ်ပါက graph traversal (multi-hop) သည် အဟောင်း
duplicate branch များသို့ ရောက်သည်။

**မသုံးသင့်သည့်အခါ** — Gender-based heuristic သည် gender-neutral pronoun (`they`)၊ အရာဝတ္ထု (`it`)
နှင့် long-distance (စာပိုဒ်ကြား) coreference များအတွက် မမှန်ပါ။ Production တွင် mention-ranking
model သို့မဟုတ် LLM-based resolution လိုအပ်သည်။

## ၅။ Classical pipeline ၏ ကန့်သတ်ချက်များ

| ကန့်သတ်ချက် | အကျိုးသက်ရောက်မှု |
|---|---|
| Domain shift | news → clinical/legal တွင် feature distribution ပြောင်း၊ recall ကျဆင်း |
| Custom entity type အသစ် | entity type တစ်ခု တိုးတိုင်း training data ပြန်လိုအပ် |
| Paraphrase coverage | trigger phrase မတူပါက relationship လွတ်သွား၊ recall နည်း |
| Coreference failure | duplicate node များ၊ graph connectivity ကျဆင်း |
| Nested/overlapping entity | BIO သည် single-label ဖြစ်သဖြင့် overlap ကို မဖမ်းနိုင် |
| Labeling cost | CRF feature engineering နှင့် annotation cost မြင့် |

Pipeline တစ်ခုလုံး၏ error သည် accumulate ဖြစ်သည် — NER recall 0.85 နှင့် RE recall 0.80 ဖြစ်ပါက
end-to-end recall သည် အကြမ်းဖျင်း 0.68 ဝန်းကျင် ဖြစ်သည်။ ဤအကြောင်းကြောင့် component တစ်ခုချင်းမက
end-to-end pipeline quality ကို တိုင်းတာရမည်။

## ၆။ Evaluation — Precision၊ Recall၊ F1

Triple-level evaluation တွင် predicted triple set ကို gold triple set နှင့် တိုက်ရိုက် နှိုင်းယှဉ်သည် —

- **Precision** = TP / (TP + FP) — ဆွဲထုတ်ခဲ့သည့် triple များထဲမှ မှန်သည့် အချိုး
- **Recall** = TP / (TP + FN) — gold triple များထဲမှ ဖမ်းမိသည့် အချိုး
- **F1** = 2 · Precision · Recall / (Precision + Recall) — harmonic mean

```python
gold = {("Sundar Pichai", "CEO_OF", "Google"),
        ("Larry Page", "FOUNDED", "Google"),
        ("Satya Nadella", "CEO_OF", "Microsoft")}
pred = {("Sundar Pichai", "CEO_OF", "Google"),
        ("Larry Page", "FOUNDED", "Google"),
        ("Sundar Pichai", "CEO_OF", "Alphabet")}

tp = len(gold & pred); fp = len(pred - gold); fn = len(gold - pred)
precision = tp / (tp + fp); recall = tp / (tp + fn)
f1 = 2 * precision * recall / (precision + recall)
print("tp=%d fp=%d fn=%d" % (tp, fp, fn))
print("precision=%.4f recall=%.4f f1=%.4f" % (precision, recall, f1))
# Expected output:
# tp=2 fp=1 fn=1
# precision=0.6667 recall=0.6667 f1=0.6667
```

**Rationale** — Exact-match (subject၊ relation type၊ object အားလုံး တူရမည်) ကို သုံးသဖြင့်
relation type အမှား (`CEO_OF` → `FOUNDED`) သည် FP နှင့် FN နှစ်ခုလုံး ဖြစ်စေသည်။

**အဓိက သတိပြုရမည့်အချက်** — Accuracy သည် imbalanced label များတွင် အသုံးမဝင်ပါ။ `O` tag များသော
NER task တွင် token accuracy 0.95 ရှိသော်လည်း entity-level F1 သည် 0.60 ဝန်းကျင်သာ ဖြစ်နိုင်သည်။

**မသုံးသင့်သည့်အခါ** — Partial match (subject မှန်၊ object မှား) ကို ခွဲခြားလိုပါက exact-match F1
မလုံလောက်ပါ — span-level F1 ကို သီးခြား တိုင်းတာရမည်။

## Summary Checklist

- [ ] BIO tagging scheme (`B-X`၊ `I-X`၊ `O`) နှင့် decode algorithm ကို ရှင်းပြနိုင်သည်
- [ ] Regex NER ၏ အားသာချက် (zero training data၊ low latency) နှင့် အားနည်းချက် (false positive) ကို ခွဲခြားနိုင်သည်
- [ ] Gazetteer longest-match lookup ၏ boundary condition (`isalnum`) ကို ရှင်းပြနိုင်သည်
- [ ] CRF အတွက် လိုအပ်သော feature အမျိုးအစားများကို စာရင်းပြုနိုင်သည်
- [ ] Pattern-based နှင့် dependency-based relationship extraction ၏ trade-off ကို နှိုင်းယှဉ်နိုင်သည်
- [ ] Coreference resolution မရှိပါက duplicate node များ ဖြစ်ပေါ်သည့် အကြောင်းရင်းကို ရှင်းပြနိုင်သည်
- [ ] Precision၊ Recall၊ F1 ကို triple-level တွင် ကိုယ်တိုင် တွက်ချက်နိုင်သည်
- [ ] Classical pipeline ၏ ကန့်သတ်ချက်များ (domain shift၊ custom entity type၊ recall) ကို စာရင်းပြုနိုင်သည်
- [ ] `lab.py` ကို `python3` ဖြင့် run ၍ `[PASS] All 6/6 exercises passed successfully.` ရရှိကြောင်း အတည်ပြုပြီး
