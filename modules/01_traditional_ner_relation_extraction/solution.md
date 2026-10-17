# M01 — Solutions: Traditional NER and Relationship Extraction

Solution များသည် `lab.py` နှင့် algorithm အရ ကိုက်ညီသည်။ `lab.py` တွင် `print` နှင့် `assert` ပိုထည့်ထားသည်။
Code block များရှိ `# Expected output:` သည် run စမ်းပြီး ရရှိသော output အပေါ် အခြေခံသည်။

---

## Exercise 1 — Regex-based NER

```python
import re

CORPUS = (
    "Sundar Pichai visited London on 12 March 2019 to open the new Google office. "
    "Satya Nadella met Tim Cook in Paris on 3 January 2020."
)

MONTHS = (
    "January|February|March|April|May|June|July|August|September|"
    "October|November|December"
)
PERSON_RE = re.compile(r"\b[A-Z][a-z]+ [A-Z][a-z]+\b")
DATE_RE = re.compile(r"\b\d{1,2} (?:%s) \d{4}\b" % MONTHS)


def regex_ner(text, patterns):
    return {label: pattern.findall(text) for label, pattern in patterns}


entities = regex_ner(CORPUS, [("PER", PERSON_RE), ("DATE", DATE_RE)])
print("PER  :", entities["PER"])
print("DATE :", entities["DATE"])
# Expected output:
# PER  : ['Sundar Pichai', 'Satya Nadella', 'Tim Cook']
# DATE : ['12 March 2019', '3 January 2020']
```

**အဓိကအယူအဆ** — `\b` word boundary သည် `Pichai` ကို `Pichaix` မှ ခွဲထုတ်သည်။ Person pattern သည်
capitalized bigram ကို ခန့်မှန်းသော heuristic သာဖြစ်သဖြင့် sentence-initial word များကို
false positive အဖြစ် ပေးနိုင်သည်။ Date pattern တွင်တော့ structure (`<number> <Month> <year>`)
တိကျသဖြင့် precision မြင့်သည်။

---

## Exercise 2 — BIO tagging decode

```python
def decode_bio(tokens, tags):
    spans, current = [], None
    for index, (token, tag) in enumerate(zip(tokens, tags)):
        if tag.startswith("B-"):
            if current is not None:
                spans.append(current)
            current = {"type": tag[2:], "tokens": [token],
                       "start": index, "end": index + 1}
        elif tag.startswith("I-") and current is not None and tag[2:] == current["type"]:
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
    print("%-5s %-15s tokens[%d:%d]"
          % (span["type"], span["text"], span["start"], span["end"]))
# Expected output:
# PER   Sundar Pichai   tokens[0:2]
# LOC   London          tokens[3:4]
# DATE  12 March 2019   tokens[5:8]
```

**အဓိကအယူအဆ** — `I-` tag သည် လက်ရှိ span ၏ type နှင့် တူမှသာ ဆက်ရမည်။ Type မတူပါက (ဥပမာ `B-PER`
နောက် `I-LOC`) သို့မဟုတ် span မဖွင့်ထားဘဲ `I-` ရောက်ပါက အသစ် စတင်ခြင်း သို့မဟုတ် စွန့်ပစ်ခြင်း
မူဝါဒကို ဆုံးဖြတ်ရမည်။ `end` သည် exclusive ဖြစ်သဖြင့် `tokens[start:end]` slice နှင့် တိုက်ရိုက် ကိုက်ညီသည်။

---

## Exercise 3 — Gazetteer lookup

```python
GAZETTEER = {
    "Google": ("ORG", "Google"),
    "Google LLC": ("ORG", "Google"),
    "Alphabet": ("ORG", "Alphabet"),
    "MSFT": ("ORG", "Microsoft"),
    "Microsoft": ("ORG", "Microsoft"),
}
GAZETTEER_TEXT = ("Google LLC is a subsidiary of Alphabet. "
                  "MSFT competes with Google.")


def gazetteer_lookup(text, gazetteer):
    keys = sorted(gazetteer, key=len, reverse=True)   # longest match first
    matches, index = [], 0
    while index < len(text):
        for key in keys:
            end = index + len(key)
            if text.startswith(key, index) \
                    and (index == 0 or not text[index - 1].isalnum()) \
                    and (end == len(text) or not text[end].isalnum()):
                entity_type, canonical = gazetteer[key]
                matches.append({"alias": key, "type": entity_type,
                                "canonical": canonical, "start": index})
                index = end
                break
        else:
            index += 1
    return matches


for match in gazetteer_lookup(GAZETTEER_TEXT, GAZETTEER):
    print("  %-10s -> %-10s (%s)"
          % (match["alias"], match["canonical"], match["type"]))
# Expected output:
#   Google LLC -> Google     (ORG)
#   Alphabet   -> Alphabet   (ORG)
#   MSFT       -> Microsoft  (ORG)
#   Google     -> Google     (ORG)
```

**အဓိကအယူအဆ** — Key များကို length အနည်းစဉ် sort လုပ်ခြင်းသည် longest-match ကို အာမခံသည်။
`text.startswith(key, index)` နှင့် `index = end` ပေါင်းစပ်မှုသည် overlap ဖြစ်ခြင်းကို တားသည် —
`Google LLC` ကို ဖမ်းပြီး index ကို ၁၀ ရှေ့တိုးသဖြင့် `Google` ကို ထပ်မဖမ်းပါ။ Boundary check
နှစ်ဖက်လုံး (`before` နှင့် `after`) လိုအပ်သည် — တစ်ဖက်သာ စစ်ပါက `Googleplex` ထဲမှ `Google` လွတ်သွားသည်။

---

## Exercise 4 — Pattern-based relationship extraction

```python
import re

PERSON = r"\b[A-Z][a-z]+ [A-Z][a-z]+\b"
REL_RULES = [
    (re.compile(r"(%s) is the CEO of ([A-Z][A-Za-z]+)" % PERSON), "CEO_OF"),
    (re.compile(r"(%s) founded ([A-Z][A-Za-z]+)" % PERSON), "FOUNDED"),
]
REL_TEXT = "Sundar Pichai is the CEO of Google. Larry Page founded Google."


def extract_relations(text, rules):
    return [(m.group(1), relation, m.group(2))
            for pattern, relation in rules
            for m in pattern.finditer(text)]


for triple in extract_relations(REL_TEXT, REL_RULES):
    print("  (%s, %s, %s)" % triple)
# Expected output:
#   (Sundar Pichai, CEO_OF, Google)
#   (Larry Page, FOUNDED, Google)
```

**အဓိကအယူအဆ** — Rule တိုင်းတွင် trigger phrase ကို literal အဖြစ် တိကျစွာ ရေးထားသဖြင့် precision
မြင့်သည်။ `finditer` ကို သုံးခြင်းသည် sentence တစ်ခုတွင် relationship များစွာ ပါဝင်သည့်အခါ
အားလုံးကို ရရှိစေသည်။ Trigger phrase အရေအတွက် တိုးလာသည်နှင့်အမျှ coverage တက်သော်လည်း
rule များအချင်းချင်း ထပ်နေပါက duplicate triple များ ထွက်လာနိုင်သည် — deduplicate လုပ်ရမည်။

---

## Exercise 5 — Coreference resolution

```python
import re

COREF_PERSONS = {"Sundar Pichai": "M", "Larry Page": "M"}
COREF_TEXT = ("Sundar Pichai leads Google. He became CEO in 2015. "
              "His tenure expanded the company.")


def resolve_coreference(text, persons):
    name_pattern = "|".join(re.escape(name) for name in persons)
    pattern = re.compile(r"\b(%s|He|She|They|His|Her|Their)\b" % name_pattern)
    state = {"last": None}

    def replace(match):
        token = match.group(1)
        if token in persons:                 # new antecedent
            state["last"] = token
            return token
        if state["last"] is None:            # no antecedent yet
            return token
        if token.lower() in {"his", "her", "their"}:
            return state["last"] + "'s"
        return state["last"]

    return pattern.sub(replace, text)


print("before:", COREF_TEXT)
print("after :", resolve_coreference(COREF_TEXT, COREF_PERSONS))
# Expected output:
# before: Sundar Pichai leads Google. He became CEO in 2015. His tenure expanded the company.
# after : Sundar Pichai leads Google. Sundar Pichai became CEO in 2015. Sundar Pichai's tenure expanded the company.
```

**အဓိကအယူအဆ** — `re.sub()` ၏ replacement argument ကို function အဖြစ် ပေးခြင်းဖြင့် match တိုင်း
အပေါ် state ကို မှီခိုသော ဆုံးဖြတ်ချက် ချနိုင်သည်။ Name pattern ကို `re.escape` ဖြင့် ကာကွယ်ခြင်းသည်
name ထဲတွင် regex metacharacter ပါဝင်ပါက pattern ပျက်ခြင်းကို တားသည်။ Gender heuristic သည်
`they` (gender-neutral) နှင့် `it` (inanimate) အတွက် မမှန်သဖြင့် production တွင် mention-ranking
model လိုအပ်သည်။

---

## Exercise 6 — Precision / Recall / F1 evaluation

```python
GOLD_TRIPLES = {
    ("Sundar Pichai", "CEO_OF", "Google"),
    ("Larry Page", "FOUNDED", "Google"),
    ("Satya Nadella", "CEO_OF", "Microsoft"),
}
PRED_TRIPLES = {
    ("Sundar Pichai", "CEO_OF", "Google"),
    ("Larry Page", "FOUNDED", "Google"),
    ("Sundar Pichai", "CEO_OF", "Alphabet"),
}


def prf1(gold, predicted):
    true_positive = len(gold & predicted)
    false_positive = len(predicted - gold)
    false_negative = len(gold - predicted)
    precision = (true_positive / (true_positive + false_positive)
                 if (true_positive + false_positive) else 0.0)
    recall = (true_positive / (true_positive + false_negative)
              if (true_positive + false_negative) else 0.0)
    f1 = (2 * precision * recall / (precision + recall)
          if (precision + recall) else 0.0)
    return precision, recall, f1, true_positive, false_positive, false_negative


precision, recall, f1, tp, fp, fn = prf1(GOLD_TRIPLES, PRED_TRIPLES)
print("tp=%d fp=%d fn=%d" % (tp, fp, fn))
print("precision=%.4f recall=%.4f f1=%.4f" % (precision, recall, f1))
# Expected output:
# tp=2 fp=1 fn=1
# precision=0.6667 recall=0.6667 f1=0.6667
```

**အဓိကအယူအဆ** — Triple ကို tuple အဖြစ် set ထဲ ထည့်ခြင်းဖြင့် exact-match evaluation ကို set
operation ဖြင့် တိုတိုရှင်းရှင်း တွက်နိုင်သည်။ `Sundar Pichai, CEO_OF, Alphabet` သည် gold ထဲ
မပါသဖြင့် FP ဖြစ်ပြီး `Satya Nadella, CEO_OF, Microsoft` ကို လွတ်သွားသဖြင့် FN ဖြစ်သည် — error
တစ်ခုတည်းမှ metric နှစ်ခုလုံးကို သက်ရောက်စေသည်။ Denominator သုည ဖြစ်နိုင်သော case
(`precision` — predicted set အလွတ်၊ `recall` — gold set အလွတ်၊ `f1` — precision+recall=0) ကို
handle လုပ်ထားခြင်းသည် `ZeroDivisionError` ကို ကာကွယ်သည်။

---

## Lab run

```bash
python3 modules/01_traditional_ner_relation_extraction/lab.py
```

Lab သည် exercise ၆ ခုလုံးကို အစဉ်လိုက် run ၍ assert စစ်ဆေးပြီး အောင်မြင်ပါက အောက်ပါ လိုင်းကို print သည် —

```text
# Expected output (final line):
[PASS] All 6/6 exercises passed successfully.
```

Exit code သည် 0 ဖြစ်သည် (`sys.exit(0 if run_all() else 1)`။
