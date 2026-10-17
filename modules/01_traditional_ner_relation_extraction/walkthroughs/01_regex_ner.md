# Walkthrough 01 — Regex-based NER (Exercise 1)

> ဤဖိုင်သည် Module 01 ၏ `solution.md` ထဲက Exercise 1 ကို **Python အခြေခံမှ စ၍**
> အပိုင်းလိုက် ရှင်းပြသည့် walkthrough ဖြစ်သည်။ Format သည် Module 00 ၏
> `walkthroughs/01_pipeline_stage_ordering.md` မှ `06_graphrag_readiness_check.md` အထိ
> နှင့် တူညီသည်။

---

## 0. ဤ Exercise က ဘာကို ဖြေရှင်းပေးသလဲ။

စာသားတစ်ပိုင်းထဲက **လူအမည်** နှင့် **ရက်စွဲ** တွေကို ရှာထုတ်ချင်တယ်ဆိုပါစို့။

```text
Sundar Pichai visited London on 12 March 2019 to open the new Google office.
Satya Nadella met Tim Cook in Paris on 3 January 2020.
```

ဒီစာသားထဲမှာ —

- လူအမည် ၃ ခု — `Sundar Pichai`၊ `Satya Nadella`၊ `Tim Cook`
- ရက်စွဲ ၂ ခု — `12 March 2019`၊ `3 January 2020`

ရှိပါတယ်။ လူတစ်ယောက် လုပ်ရင် ဒါကို အလွယ်တကူ မြင်နိုင်ပေမဲ့ program က ဒါကို
နည်းစနစ်တကျ ရှာထုတ်ရပါတယ်။ ဒီအလုပ်ကို **NER** (Named Entity Recognition) လို့ ခေါ်ပြီး
text ထဲက entity အမည်နှင့် အမျိုးအစားကို ရှာထုတ်ခြင်း ဖြစ်ပါတယ်။

ဒီ Exercise က NER ကို **Regular Expression (regex)** နဲ့ လုပ်ပြပါတယ်။ ဒါကို
**rule-based NER** လို့ ခေါ်ပါတယ်။

ဒီ code မှာ လေ့လာရမယ့် Python concepts တွေကတော့ —

- `import re` နှင့် `re.compile()`
- Adjacent string literal concatenation (စာသားလိုင်းများ ဆက်တွဲခြင်း)
- Regex — `\b`၊ `[A-Z]`၊ `[a-z]`၊ `+`၊ `\d`၊ `{1,2}`၊ `(?:...)`
- `%` string formatting ဖြင့် pattern ထဲ တန်ဖိုး ထည့်ခြင်း
- Dict comprehension
- List of tuples
- Dictionary indexing

---

## 1. `import re`

```python
import re
```

`re` က Python ရဲ့ Regular Expression module ဖြစ်ပါတယ်။ Regex ဆိုတာ စာသားပုံစံ (pattern)
တစ်ခုနဲ့ ကိုက်ညီတဲ့ အပိုင်းတွေကို ရှာဖွေဖို့ အသုံးပြုတဲ့ နည်းလမ်းဖြစ်ပါတယ်။

Module 00 ရဲ့ Exercise 5 မှာ pattern တစ်ခုတည်းကို line တစ်ကြောင်းလုံးနဲ့ ကိုက်ညီမှုစစ်ခဲ့ပါတယ်။
ဒီ Exercise မှာတော့ စာသားအရှည်ကြီးတစ်ခုထဲက **ကိုက်ညီတဲ့ အပိုင်းတွေ အားလုံး**ကို
ရှာထုတ်မှာ ဖြစ်ပါတယ်။

---

## 2. `CORPUS` — စစ်ဆေးမယ့် စာသား

```python
CORPUS = (
    "Sundar Pichai visited London on 12 March 2019 to open the new Google office. "
    "Satya Nadella met Tim Cook in Paris on 3 January 2020."
)
```

ဒီနေရာမှာ စာသားနှစ်လိုင်းကို `(` `)` နဲ့ ခွေပြီး ရေးထားတာကို သတိထားပါ။ Python မှာ
**ကပ်လျက် ရေးထားတဲ့ string literal နှစ်ခုကို အလိုအလျောက် တစ်ခုတည်း ဆက်ပေးပါတယ်**။

```python
part1 = "Sundar Pichai visited London "
part2 = "on 12 March 2019."

print(part1 + part2)
print("Sundar Pichai visited London " "on 12 March 2019.")
```

Output —

```text
Sundar Pichai visited London on 12 March 2019.
Sundar Pichai visited London on 12 March 2019.
```

နှစ်လိုင်းလုံး တူညီတဲ့ ရလဒ်ပေးပါတယ်။ `+` မလိုဘဲ ကပ်ရေးလို့ရတာကြောင့် ရှည်တဲ့စာသားကို
လိုင်းခွဲပြီး ဖတ်ရလွယ်အောင် ရေးနိုင်ပါတယ်။

ဒီနည်းကို `MONTHS` variable မှာလည်း ထပ်တွေ့ရပါမယ်။

---

## 3. `MONTHS` — လအမည်များ စုစည်းခြင်း

```python
MONTHS = (
    "January|February|March|April|May|June|July|August|September|"
    "October|November|December"
)
```

ဒီ variable ထဲမှာ လ ၁၂ လကို `|` နဲ့ ခြားပြီး ရေးထားပါတယ်။ Regex မှာ `|` က
**"ဒါ သို့မဟုတ် ဟို" (alternation)** ကို ဆိုလိုပါတယ်။ ဒါကြောင့် —

```python
import re

MONTHS = "January|February|March"

print(re.findall(MONTHS, "12 March 2019 and 3 January 2020"))
print(re.findall(MONTHS, "12 Jun 2019"))
```

Output —

```text
['March', 'January']
[]
```

`Jun` က အစိတ်အပိုင်း `June` နဲ့ မကိုက်ညီပါဘူး။ Alternation က စာသားအပိုင်းကို
**တိတိကျကျ** ကိုက်ညီရပါတယ်။

`MONTHS` ကို ဒီလို သီးခြား variable အဖြစ် ထုတ်ထားတာကြောင့် လအမည်စာရင်းကို
တစ်နေရာတည်းမှာ ပြင်နိုင်ပြီး pattern တွေ အများအပြားမှာ ပြန်သုံးနိုင်ပါတယ်။

---

## 4. `PERSON_RE` — လူအမည် pattern

```python
PERSON_RE = re.compile(r"\b[A-Z][a-z]+ [A-Z][a-z]+\b")
```

`re.compile()` က pattern ကို ကြိုတင် compile လုပ်ပြီး သိမ်းထားပေးပါတယ်။
Pattern တစ်ခုကို အကြိမ်များစွာ အသုံးပြုမယ်ဆိုရင် compile လုပ်ထားတာ ပိုထိရောက်ပါတယ်။

### `r"..."` — raw string

ရှေ့က `r` က raw string ဖြစ်ပါတယ်။ Regex ထဲမှာ `\` backslash ပါဝင်တဲ့ pattern တွေကို
မူရင်းအတိုင်း ထိန်းထားပေးပါတယ်။

### Pattern ကို အပိုင်းလိုက် ဖတ်ခြင်း

| အပိုင်း | အဓိပ္ပာယ် |
| --- | --- |
| `\b` | Word boundary — စာလုံးတစ်လုံးရဲ့ အစ သို့မဟုတ် အဆုံး |
| `[A-Z]` | အင်္ဂလိပ် စာလုံးကြီး တစ်လုံး |
| `[a-z]+` | စာလုံးအသေး တစ်လုံး သို့မဟုတ် ထို့ထက် ပို |
| `(space)` | Space တစ်လုံး |
| `\b` | နောက်တစ်ဖန် word boundary |

ဒါကြောင့် pattern တစ်ခုလုံးက **"စာလုံးကြီးနဲ့စပြီး စာလုံးအသေးတွေ ဆက်လိုက်တဲ့ စကားလုံးနှစ်လုံး"**
ကို ရှာပါတယ်။ ဥပမာ `Sundar Pichai` လိုပုံစံပါ။

```python
import re

PERSON_RE = re.compile(r"\b[A-Z][a-z]+ [A-Z][a-z]+\b")

print(PERSON_RE.findall("Sundar Pichai met Tim Cook"))
print(PERSON_RE.findall("visited London on Monday"))
```

Output —

```text
['Sundar Pichai', 'Tim Cook']
[]
```

`London` နဲ့ `Monday` တို့က စကားလုံးတစ်လုံးတည်းမို့ မကိုက်ညီပါဘူး။ Pattern က
စကားလုံး **နှစ်လုံး** ကို မျှော်လင့်ထားလို့ပါ။

### `\b` က တကယ် ဘာလုပ်ပေးသလဲ။

`\b` က စာလုံးတစ်လုံးရဲ့ ဘောင်ကို စစ်ပါတယ်။ `\b` မပါရင် pattern က စာလုံးတစ်လုံးရဲ့
**အလယ်ကနေ** စပြီး match လုပ်နိုင်ပါတယ်။ နှစ်ခုကို နှိုင်းယှဉ်ကြည့်ပါ။

```python
import re

BOUNDED = re.compile(r"\b[A-Z][a-z]+ [A-Z][a-z]+\b")
UNBOUNDED = re.compile(r"[A-Z][a-z]+ [A-Z][a-z]+")

for text in ["Tim Cook", "Tim Cook2", "xTim Cook", "Tim Cook_2"]:
    print("%-12s bounded=%-16s unbounded=%s"
          % (text, BOUNDED.findall(text), UNBOUNDED.findall(text)))
```

Output —

```text
Tim Cook     bounded=['Tim Cook']     unbounded=['Tim Cook']
Tim Cook2    bounded=[]               unbounded=['Tim Cook']
xTim Cook    bounded=[]               unbounded=['Tim Cook']
Tim Cook_2   bounded=[]               unbounded=['Tim Cook']
```

ဒီဇယားက `\b` ရဲ့ အလုပ်ကို ရှင်းရှင်းလင်းလင်း ပြပါတယ်။ စာလုံးတစ်လုံးရဲ့ ဘေးမှာ
**စာလုံး သို့မဟုတ် ဂဏန်း** ကပ်နေရင် `\b` က match ကို ပယ်လိုက်ပါတယ်။ `Cook2` ထဲက
`Cook` ကို လူအမည်အဖြစ် မှတ်မိခြင်းမှ ကာကွယ်ပေးတာ ဖြစ်ပါတယ်။

ဒီ pattern က **ခန့်မှန်းချက် (heuristic)** သာဖြစ်ပါတယ်။ စာလုံးကြီးနှစ်လုံး ဆက်နေရင်
လူအမည်လို့ ယူဆတာပါ။ ဒါကြောင့် လူမဟုတ်တဲ့အရာတွေကိုလည်း လူအမည်အဖြစ်
ပြန်ပေးနိုင်ပါတယ်။

```python
import re

PERSON_RE = re.compile(r"\b[A-Z][a-z]+ [A-Z][a-z]+\b")

print(PERSON_RE.findall("The New York office opened in March."))
print(PERSON_RE.findall("Google Cloud Platform is here."))
```

Output —

```text
['The New']
['Google Cloud']
```

`The New` က ဝါကျအစစကားလုံးနှစ်လုံး ဆက်နေတာကြောင့် လူအမည်အဖြစ် မှားထုတ်လိုက်တာပါ။
`Google Cloud` ကလည်း လူ့အမည် မဟုတ်ဘဲ အဖွဲ့အစည်း/ထုတ်ကုန် အမည်ဖြစ်ပါတယ်။
ဒါက rule-based NER ရဲ့ အဓိက ကန့်သတ်ချက်ပါ။

---

## 5. `DATE_RE` — ရက်စွဲ pattern

```python
DATE_RE = re.compile(r"\b\d{1,2} (?:%s) \d{4}\b" % MONTHS)
```

ဒီတစ်ကြောင်းမှာ အပိုင်းနှစ်ခု ရှိပါတယ်။

### 5.1 `%` ဖြင့် pattern ထဲ တန်ဖိုး ထည့်ခြင်း

`"..." % MONTHS` က `MONTHS` တန်ဖိုးကို `%s` နေရာမှာ အစားထိုးပါတယ်။

```python
MONTHS = "January|February|March"
pattern = r"\b\d{1,2} (?:%s) \d{4}\b" % MONTHS

print(pattern)
```

Output —

```text
\b\d{1,2} (?:January|February|March) \d{4}\b
```

ဒီနည်းကြောင့် လအမည်စာရင်းကို `MONTHS` တစ်နေရာတည်းမှာ ထားပြီး pattern ကို
အလိုအလျောက် ဖန်တီးနိုင်ပါတယ်။

### 5.2 `(?:...)` — non-capturing group

ဒီအပိုင်းက သေးငယ်ပုံရပေမဲ့ မထည့်ရင် **pattern တစ်ခုလုံး ပျက်သွားပါတယ်**။ အကြောင်းရင်းက
regex မှာ `|` ရဲ့ precedence အလွန်နိမ့်လို့ပါ။ `|` က သူ့ဘေး အနီးဆုံးအပိုင်းကိုသာ
မခွဲဘဲ **pattern တစ်ခုလုံး**ကို အပိုင်းများအဖြစ် ခွဲပါတယ်။

```python
import re

MONTHS = "January|February|March"
NO_GROUP = r"\b\d{1,2} %s \d{4}\b" % MONTHS

print("pattern တည်ဆောက်ပြီး :", NO_GROUP)
print("`|` ဖြင့် ခွဲထွက်သည့်အပိုင်း :", NO_GROUP.split("|"))
```

Output —

```text
pattern တည်ဆောက်ပြီး : \b\d{1,2} January|February|March \d{4}\b
`|` ဖြင့် ခွဲထွက်သည့်အပိုင်း : ['\\b\\d{1,2} January', 'February', 'March \\d{4}\\b']
```

ဒါကြောင့် regex engine က ဒီ pattern ကို **အပိုင်းသုံးခု** အဖြစ် ဖတ်ပါတယ်။

| အပိုင်း | အဓိပ္ပာယ် |
| --- | --- |
| `\b\d{1,2} January` | ဂဏန်း + `January` — ခုနှစ် မလိုအပ်တော့ပါ |
| `February` | `February` စာလုံးတစ်လုံးတည်း |
| `March \d{4}\b` | `March` + ခုနှစ် — ဂဏန်းအစ မလိုအပ်တော့ပါ |

`(?:...)` က လအမည်များကို **အုပ်စုတစ်ခုအဖြစ် စုစည်း** ပေးပြီး `|` ကို ဒီအုပ်စုအတွင်းမှာသာ
အလုပ်လုပ်စေပါတယ်။ `?:` က ဒီအုပ်စုကို "capturing group" မဖြစ်စေဘဲ စုစည်းမှုသက်သက်
ဖြစ်စေပါတယ်။

အပိုင်းသုံးမျိုးကို နှိုင်းယှဉ်ကြည့်ပါ။

```python
import re

MONTHS = "January|February|March"
NO_GROUP = re.compile(r"\b\d{1,2} %s \d{4}\b" % MONTHS)
CAPTURE = re.compile(r"\b\d{1,2} (%s) \d{4}\b" % MONTHS)
NON_CAPTURE = re.compile(r"\b\d{1,2} (?:%s) \d{4}\b" % MONTHS)

for text in ["on 12 March 2019", "on 12 January 2019", "on 12 February 2019"]:
    print("%-20s no-group=%-20s capture=%-12s non-capture=%s"
          % (text, NO_GROUP.findall(text), CAPTURE.findall(text), NON_CAPTURE.findall(text)))
```

Output —

```text
on 12 March 2019     no-group=['March 2019']       capture=['March']    non-capture=['12 March 2019']
on 12 January 2019   no-group=['12 January']       capture=['January']  non-capture=['12 January 2019']
on 12 February 2019  no-group=['February']         capture=['February'] non-capture=['12 February 2019']
```

ဇယားက ဖြစ်ရပ်နှစ်မျိုးကို ပြပါတယ်။

- **`no-group`** — `|` က pattern တစ်ခုလုံးကို ခွဲလိုက်သဖြင့် ရက်စွဲအပြည့်အစုံ မရတော့ပါ။
  `12 March 2019` အတွက် `March 2019` ကိုသာ ရပြီး၊ `12 January 2019` အတွက်
  `12 January` ကိုသာ ရပါတယ်။ အပိုင်းတစ်ခုချင်းစီမှာ `\b`၊ ဂဏန်းနှင့် ခုနှစ် လိုအပ်ချက်တွေ
  ပျောက်နေလို့ပါ။
- **`capture`** — ရက်စွဲအပြည့်အစုံ ကိုက်ညီပေမဲ့ `findall()` က **group ရဲ့ အကြောင်းအရာ**
  ကိုသာ ပြန်ပေးသဖြင့် လအမည်သာ ရပါတယ်။
- **`non-capture`** — ရက်စွဲအပြည့်အစုံ ရပါတယ်။ ဒါက Exercise မှာ လိုချင်တဲ့ ရလဒ်ပါ။

အတိုချုပ် — regex မှာ `|` နဲ့ တွဲသုံးတဲ့အခါ **အုပ်စုဖွဲ့ရန် လိုအပ်သည်**။ အုပ်စုကို
`findall()` ရလဒ်ထဲ ထည့်မလာစေချင်ရင် `(?:...)` ကို သုံးရသည်။

### 5.3 ကျန် အပိုင်းများ

| အပိုင်း | အဓိပ္ပာယ် |
| --- | --- |
| `\d{1,2}` | ဂဏန်း ၁ လုံး သို့မဟုတ် ၂ လုံး (`12`၊ `3`) |
| `(?:...)` | လအမည် တစ်ခုခု |
| `\d{4}` | ဂဏန်း ၄ လုံး — ခုနှစ် |
| `\b` | Word boundary နှစ်ဖက် |

```python
import re

MONTHS = "January|February|March"
DATE_RE = re.compile(r"\b\d{1,2} (?:%s) \d{4}\b" % MONTHS)

print("valid  :", DATE_RE.findall("on 12 March 2019"))
print("partial:", DATE_RE.findall("inside 120 March 2019"))
print("case   :", DATE_RE.findall("on 3 march 2020"))
```

Output —

```text
valid  : ['12 March 2019']
partial: []
case   : []
```

- `120 March 2019` — `\b` ရှေ့က စစ်ဆေးချက်ကြောင့် `20 March 2019` လို
  **ဂဏန်းအပိုင်းအစ** ကို မှားဖမ်းခြင်းမှ ကာကွယ်ပေးပါတယ်။
- `march` — alternation က case-sensitive ဖြစ်တဲ့အတွက် `March` နဲ့သာ ကိုက်ညီပါတယ်။
  Case မခွဲချင်ရင် `re.compile(..., re.IGNORECASE)` ကို သုံးနိုင်ပါတယ်။

ရက်စွဲ pattern က ဖွဲ့စည်းပုံ (ဂဏန်း + လ + ခုနှစ်) တိတိကျကျမို့ person pattern ထက်
**precision ပိုမြင့်** ပါတယ်။

---

## 6. `regex_ner()` — Pattern များကို အလုပ်လုပ်စေခြင်း

```python
def regex_ner(text, patterns):
    return {label: pattern.findall(text) for label, pattern in patterns}
```

ဒီ function က argument နှစ်ခု လက်ခံပါတယ်။

- `text` — စစ်ဆေးမယ့် စာသား။
- `patterns` — `(label, compiled_pattern)` tuple များပါဝင်တဲ့ list။

Function အတွင်းက တစ်လိုင်းတည်းကို ခွဲဖတ်ကြည့်ရအောင်။

```python
{label: pattern.findall(text) for label, pattern in patterns}
```

ဒါက **dict comprehension** ဖြစ်ပါတယ်။ `patterns` ထဲက tuple တစ်ခုချင်းစီကို
`label` နဲ့ `pattern` ဆိုပြီး ခွဲယူပြီး၊ `label` ကို key အဖြစ်၊ ရှာတွေ့တဲ့ စာသားစာရင်းကို
value အဖြစ် ထည့်ပါတယ်။

ပုံမှန် `for` loop နဲ့ ရေးမယ်ဆိုရင် —

```python
def regex_ner(text, patterns):
    result = {}
    for label, pattern in patterns:
        result[label] = pattern.findall(text)
    return result
```

နှစ်ခုလုံးရဲ့ ရည်ရွယ်ချက် တူညီပါတယ်။

### `findall()` က ဘာပြန်ပေးသလဲ။

```python
import re

PERSON_RE = re.compile(r"\b[A-Z][a-z]+ [A-Z][a-z]+\b")
CORPUS = "Sundar Pichai met Tim Cook"

found = PERSON_RE.findall(CORPUS)
print(found)
print(type(found), len(found))
```

Output —

```text
['Sundar Pichai', 'Tim Cook']
<class 'list'> 2
```

`findall()` က ကိုက်ညီတဲ့ အပိုင်းအားလုံးကို **list** အဖြစ် ပြန်ပေးပါတယ်။
မတွေ့ရင် empty list `[]` ပြန်ပါတယ်။ Module 00 ၏ Exercise 5 မှာ သုံးခဲ့တဲ့
`match()` က ပထမဆုံးတစ်ခုတည်းကို စစ်ပြီး `None` သို့မဟုတ် match object ပြန်ပါတယ်။
`findall()` က အားလုံးကို ရှာပါတယ်။

---

## 7. Function ကို ခေါ်ပြီး ရလဒ်ကို ထုတ်ခြင်း

```python
entities = regex_ner(CORPUS, [("PER", PERSON_RE), ("DATE", DATE_RE)])
print("PER  :", entities["PER"])
print("DATE :", entities["DATE"])
```

`[("PER", PERSON_RE), ("DATE", DATE_RE)]` က tuple နှစ်ခုပါတဲ့ list ဖြစ်ပါတယ်။
`regex_ner()` က ဒါကို ဖတ်ပြီး dict တစ်ခု ပြန်ပေးပါတယ်။

```python
entities == {
    "PER": PERSON_RE.findall(CORPUS),
    "DATE": DATE_RE.findall(CORPUS),
}
```

ပြီးရင် `entities["PER"]` လို့ key နဲ့ ဆွဲထုတ်ပါတယ်။ Dictionary indexing ပါ။

Expected output —

```text
PER  : ['Sundar Pichai', 'Satya Nadella', 'Tim Cook']
DATE : ['12 March 2019', '3 January 2020']
```

---

## 8. Code တစ်ခုလုံး — Run လုပ်နိုင်သော Version

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
```

Output —

```text
PER  : ['Sundar Pichai', 'Satya Nadella', 'Tim Cook']
DATE : ['12 March 2019', '3 January 2020']
```

---

## 9. ရလဒ်ကို ပြန်ကြည့်ခြင်း

| Label | Pattern အခြေခံ | ရလဒ် | မှတ်ချက် |
| --- | --- | --- | --- |
| `PER` | စာလုံးကြီး + စာလုံးအသေး နှစ်လုံး | `Sundar Pichai`၊ `Satya Nadella`၊ `Tim Cook` | `London`၊ `Paris`၊ `Google` တို့က စကားလုံးတစ်လုံးမို့ မပါ |
| `DATE` | ဂဏန်း + လ + ခုနှစ် | `12 March 2019`၊ `3 January 2020` | ဖွဲ့စည်းပုံတိကျသဖြင့် precision မြင့် |

`London`၊ `Paris` တို့ဟာ **ပထဝီနေရာ (LOC)** ဖြစ်ပါတယ်။ ဒီ Exercise မှာ `LOC` label
မသတ်မှတ်ထားလို့ ရလဒ်ထဲ မပါဝင်ပါဘူး။ ဒါက **label set** ကန့်သတ်ချက်ပါ — pattern မှန်ပေမဲ့
သတ်မှတ်ထားတဲ့ label မရှိရင် ထည့်စရာနေရာ မရှိပါဘူး။

---

## 10. ကိုယ်တိုင်လေ့ကျင့်ကြည့်ပါ

**မေးခွန်း** — အောက်ပါ code က ဘယ်ရလဒ် ပြန်ပေးမလဲ။

```python
import re

PATTERN = re.compile(r"\b[A-Z][a-z]+\b")
print(PATTERN.findall("Sundar Pichai visited London."))
```

1. `['Sundar Pichai']` — စကားလုံးနှစ်လုံး ဆက်နေတာကို ဖမ်းမယ်
2. `['Sundar', 'Pichai', 'London']` — စာလုံးကြီးနဲ့စတဲ့ စကားလုံးတစ်လုံးစီ
3. `[]` — စကားလုံးနှစ်လုံး လိုအပ်တယ်
4. `['Sundar', 'Pichai']` — လူအမည်သာ

<details>
<summary>အဖြေ ကြည့်ရန်</summary>

**အဖြေ — 2. `['Sundar', 'Pichai', 'London']`**

အကြောင်းရင်း — ဤ pattern တွင် **space မပါ** တော့ပါ။ `\b[A-Z][a-z]+\b` သည်
စာလုံးကြီးတစ်လုံးနှင့် စပြီး စာလုံးအသေးများ ဆက်လိုက်သည့် **စကားလုံးတစ်လုံး**ကို
ရှာသည်။ `visited` သည် စာလုံးအသေးနှင့် စသဖြင့် မကိုက်ညီပါ။

Exercise 1 ၏ `PERSON_RE` တွင် space ပါသဖြင့် စကားလုံးနှစ်လုံး လိုအပ်သည် —
ထို့ကြောင့် `London` ကဲ့သို့ စကားလုံးတစ်လုံးတည်း လူအမည်များ မပါဝင်ပါ။

</details>

---

**အဓိက မှတ်ထားရန်** — Rule-based NER သည် pattern တိကျလေလေ precision မြင့်လေလေ
ဖြစ်သည်။ သို့သော် pattern များကို လက်ဖြင့် ရေးရသဖြင့် coverage ကန့်သတ်ချက် ရှိသည် —
အမည်အသစ်၊ စာလုံးပုံစံအသစ် တိုင်းအတွက် pattern အသစ် ရေးရမည်။ Module 02 တွင်
train လုပ်ထားသော model ဖြင့် ဤအလုပ်ကို လုပ်ပုံကို လေ့လာမည်။
