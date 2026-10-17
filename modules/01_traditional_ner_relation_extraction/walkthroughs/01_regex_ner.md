# Walkthrough 01 — Regex-based NER (Exercise 1)

> ဤဖိုင်သည် Module 01 ၏ `solution.md` ထဲက Exercise 1 ကို **Python အခြေခံမှ စ၍**
> အပိုင်းလိုက် ရှင်းပြသည့် walkthrough ဖြစ်သည်။ Format သည် Module 00 ၏
> `walkthroughs/01_pipeline_stage_ordering.md` မှ `06_graphrag_readiness_check.md` အထိ
> နှင့် တူညီသည်။

---

## 0. ဤ Exercise က ဘာကို ဖြေရှင်းပေးသလဲ။

စာသားတစ်ပိုင်းထဲက **လူအမည်** နှင့် **ရက်စွဲ** များကို ရှာထုတ်လိုသည်ဟု ဆိုပါစို့။

```text
Sundar Pichai visited London on 12 March 2019 to open the new Google office.
Satya Nadella met Tim Cook in Paris on 3 January 2020.
```

ဤစာသားတွင် —

- လူအမည် ၃ ခု — `Sundar Pichai`၊ `Satya Nadella`၊ `Tim Cook`
- ရက်စွဲ ၂ ခု — `12 March 2019`၊ `3 January 2020`

ရှိပါသည်။ လူတစ်ယောက် လုပ်လျှင် ၎င်းကို အလွယ်တကူ မြင်နိုင်သော်လည်း program သည် ၎င်းကို
နည်းစနစ်တကျ ရှာထုတ်ရသည်။ ဤအလုပ်ကို **NER** (Named Entity Recognition) ဟု ခေါ်ပြီး
text ထဲမှ entity အမည်နှင့် အမျိုးအစားကို ရှာထုတ်ခြင်း ဖြစ်သည်။

ဤ Exercise သည် NER ကို **Regular Expression (regex)** ဖြင့် လုပ်ပြသည်။ ၎င်းကို
**rule-based NER** ဟု ခေါ်သည်။

ဤ code တွင် လေ့လာရမည့် Python concepts များမှာ —

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

`re` သည် Python ၏ Regular Expression module ဖြစ်သည်။ Regex သည် စာသားပုံစံ (pattern)
တစ်ခုနှင့် ကိုက်ညီသော အပိုင်းများကို ရှာဖွေရန် အသုံးပြုသော နည်းလမ်းဖြစ်သည်။

Module 00 ၏ Exercise 5 တွင် pattern တစ်ခုတည်းကို line တစ်ကြောင်းလုံးနှင့် ကိုက်ညီမှုစစ်ခဲ့သည်။
ဤ Exercise တွင်မူ စာသားအရှည်ကြီးတစ်ခုထဲမှ **ကိုက်ညီသော အပိုင်းများ အားလုံး**ကို
ရှာထုတ်မည် ဖြစ်သည်။

---

## 2. `CORPUS` — စစ်ဆေးမည့် စာသား

```python
CORPUS = (
    "Sundar Pichai visited London on 12 March 2019 to open the new Google office. "
    "Satya Nadella met Tim Cook in Paris on 3 January 2020."
)
```

ဤနေရာတွင် စာသားနှစ်လိုင်းကို `(` `)` ဖြင့် ခွေပြီး ရေးထားသည်ကို သတိထားပါ။ Python တွင်
**ကပ်လျက် ရေးထားသော string literal နှစ်ခုကို အလိုအလျောက် တစ်ခုတည်း ဆက်ပေးသည်**။

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

နှစ်လိုင်းလုံး တူညီသော ရလဒ်ပေးသည်။ `+` မလိုဘဲ ကပ်ရေးနိုင်သောကြောင့် ရှည်သောစာသားကို
လိုင်းခွဲပြီး ဖတ်ရလွယ်အောင် ရေးနိုင်သည်။

ဤနည်းကို `MONTHS` variable တွင်လည်း ထပ်တွေ့ရမည်။

---

## 3. `MONTHS` — လအမည်များ စုစည်းခြင်း

```python
MONTHS = (
    "January|February|March|April|May|June|July|August|September|"
    "October|November|December"
)
```

ဤ variable ထဲတွင် လ ၁၂ လကို `|` ဖြင့် ခြားပြီး ရေးထားသည်။ Regex တွင် `|` သည်
**"ဤအရာ သို့မဟုတ် ထိုအရာ" (alternation)** ကို ဆိုလိုသည်။ ထို့ကြောင့် —

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

`Jun` သည် အစိတ်အပိုင်း `June` နှင့် မကိုက်ညီပါ။ Alternation သည် စာသားအပိုင်းကို
**တိတိကျကျ** ကိုက်ညီရသည်။

`MONTHS` ကို ဤသို့ သီးခြား variable အဖြစ် ထုတ်ထားသောကြောင့် လအမည်စာရင်းကို
တစ်နေရာတည်းတွင် ပြင်နိုင်ပြီး pattern များ အများအပြားတွင် ပြန်သုံးနိုင်သည်။

---

## 4. `PERSON_RE` — လူအမည် pattern

```python
PERSON_RE = re.compile(r"\b[A-Z][a-z]+ [A-Z][a-z]+\b")
```

`re.compile()` သည် pattern ကို ကြိုတင် compile လုပ်ပြီး သိမ်းထားပေးသည်။
Pattern တစ်ခုကို အကြိမ်များစွာ အသုံးပြုမည်ဆိုလျှင် compile လုပ်ထားခြင်းက ပိုထိရောက်သည်။

### `r"..."` — raw string

ရှေ့က `r` သည် raw string ဖြစ်သည်။ Regex ထဲတွင် `\` backslash ပါဝင်သော pattern များကို
မူရင်းအတိုင်း ထိန်းထားပေးသည်။

### Pattern ကို အပိုင်းလိုက် ဖတ်ခြင်း

| အပိုင်း | အဓိပ္ပာယ် |
| --- | --- |
| `\b` | Word boundary — စာလုံးတစ်လုံး၏ အစ သို့မဟုတ် အဆုံး |
| `[A-Z]` | အင်္ဂလိပ် စာလုံးကြီး တစ်လုံး |
| `[a-z]+` | စာလုံးအသေး တစ်လုံး သို့မဟုတ် ထို့ထက် ပို |
| `(space)` | Space တစ်လုံး |
| `\b` | နောက်တစ်ဖန် word boundary |

ထို့ကြောင့် pattern တစ်ခုလုံးသည် **"စာလုံးကြီးနှင့်စပြီး စာလုံးအသေးများ ဆက်လိုက်သော စကားလုံးနှစ်လုံး"**
ကို ရှာသည်။ ဥပမာ `Sundar Pichai` ကဲ့သို့ပုံစံဖြစ်သည်။

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

`London` နှင့် `Monday` တို့သည် စကားလုံးတစ်လုံးတည်းဖြစ်သောကြောင့် မကိုက်ညီပါ။ Pattern သည်
စကားလုံး **နှစ်လုံး** ကို မျှော်လင့်ထားခြင်းကြောင့်ဖြစ်သည်။

### `\b` သည် အမှန်တကယ် မည်သည့်အရာကို လုပ်ဆောင်ပေးသနည်း။

`\b` က စာလုံးတစ်လုံး၏ ဘောင်ကို စစ်သည်။ `\b` မပါလျှင် pattern သည် စာလုံးတစ်လုံး၏
**အလယ်မှ** စပြီး match လုပ်နိုင်သည်။ နှစ်ခုကို နှိုင်းယှဉ်ကြည့်ပါ။

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

ဤဇယားသည် `\b` ၏ အလုပ်ကို ရှင်းရှင်းလင်းလင်း ပြသည်။ စာလုံးတစ်လုံး၏ ဘေးတွင်
**စာလုံး သို့မဟုတ် ဂဏန်း** ကပ်နေလျှင် `\b` သည် match ကို ပယ်လိုက်သည်။ `Cook2` ထဲမှ
`Cook` ကို လူအမည်အဖြစ် မှတ်မိခြင်းမှ ကာကွယ်ပေးခြင်း ဖြစ်သည်။

ဤ pattern သည် **ခန့်မှန်းချက် (heuristic)** သာဖြစ်သည်။ စာလုံးကြီးနှစ်လုံး ဆက်နေလျှင်
လူအမည်ဟု ယူဆခြင်းဖြစ်သည်။ ထို့ကြောင့် လူမဟုတ်သောအရာများကိုလည်း လူအမည်အဖြစ်
ပြန်ပေးနိုင်သည်။

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

`The New` သည် ဝါကျအစစကားလုံးနှစ်လုံး ဆက်နေခြင်းကြောင့် လူအမည်အဖြစ် မှားထုတ်လိုက်ခြင်းဖြစ်သည်။
`Google Cloud` သည်လည်း လူ့အမည် မဟုတ်ဘဲ အဖွဲ့အစည်း/ထုတ်ကုန် အမည်ဖြစ်သည်။
၎င်းသည် rule-based NER ၏ အဓိက ကန့်သတ်ချက်ဖြစ်သည်။

---

## 5. `DATE_RE` — ရက်စွဲ pattern

```python
DATE_RE = re.compile(r"\b\d{1,2} (?:%s) \d{4}\b" % MONTHS)
```

ဤတစ်ကြောင်းတွင် အပိုင်းနှစ်ခု ရှိသည်။

### 5.1 `%` ဖြင့် pattern ထဲ တန်ဖိုး ထည့်ခြင်း

`"..." % MONTHS` က `MONTHS` တန်ဖိုးကို `%s` နေရာတွင် အစားထိုးသည်။

```python
MONTHS = "January|February|March"
pattern = r"\b\d{1,2} (?:%s) \d{4}\b" % MONTHS

print(pattern)
```

Output —

```text
\b\d{1,2} (?:January|February|March) \d{4}\b
```

ဤနည်းကြောင့် လအမည်စာရင်းကို `MONTHS` တစ်နေရာတည်းတွင် ထားပြီး pattern ကို
အလိုအလျောက် ဖန်တီးနိုင်သည်။

### 5.2 `(?:...)` — non-capturing group

ဤအပိုင်းသည် သေးငယ်ပုံရသော်လည်း မထည့်လျှင် **pattern တစ်ခုလုံး ပျက်သွားသည်**။ အကြောင်းရင်းမှာ
regex တွင် `|` ၏ precedence အလွန်နိမ့်ခြင်းကြောင့်ဖြစ်သည်။ `|` သည် မိမိနှင့် အနီးဆုံးအပိုင်းကိုသာ
မခွဲဘဲ **pattern တစ်ခုလုံး**ကို အပိုင်းများအဖြစ် ခွဲသည်။

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

ထို့ကြောင့် regex engine သည် ဤ pattern ကို **အပိုင်းသုံးခု** အဖြစ် ဖတ်သည်။

| အပိုင်း | အဓိပ္ပာယ် |
| --- | --- |
| `\b\d{1,2} January` | ဂဏန်း + `January` — ခုနှစ် မလိုအပ်တော့ပါ |
| `February` | `February` စာလုံးတစ်လုံးတည်း |
| `March \d{4}\b` | `March` + ခုနှစ် — ဂဏန်းအစ မလိုအပ်တော့ပါ |

`(?:...)` သည် လအမည်များကို **အုပ်စုတစ်ခုအဖြစ် စုစည်း** ပေးပြီး `|` ကို ဤအုပ်စုအတွင်းတွင်သာ
အလုပ်လုပ်စေသည်။ `?:` သည် ဤအုပ်စုကို "capturing group" မဖြစ်စေဘဲ စုစည်းမှုသက်သက်
ဖြစ်စေသည်။

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

ဇယားသည် ဖြစ်ရပ်နှစ်မျိုးကို ပြသည်။

- **`no-group`** — `|` သည် pattern တစ်ခုလုံးကို ခွဲလိုက်သဖြင့် ရက်စွဲအပြည့်အစုံ မရတော့ပါ။
  `12 March 2019` အတွက် `March 2019` ကိုသာ ရပြီး၊ `12 January 2019` အတွက်
  `12 January` ကိုသာ ရသည်။ အပိုင်းတစ်ခုချင်းစီတွင် `\b`၊ ဂဏန်းနှင့် ခုနှစ် လိုအပ်ချက်များ
  ပျောက်နေခြင်းကြောင့်ဖြစ်သည်။
- **`capture`** — ရက်စွဲအပြည့်အစုံ ကိုက်ညီသော်လည်း `findall()` သည် **group ၏ အကြောင်းအရာ**
  ကိုသာ ပြန်ပေးသဖြင့် လအမည်သာ ရသည်။
- **`non-capture`** — ရက်စွဲအပြည့်အစုံ ရသည်။ ၎င်းသည် Exercise တွင် လိုချင်သော ရလဒ်ဖြစ်သည်။

အတိုချုပ် — regex တွင် `|` နှင့် တွဲသုံးသောအခါ **အုပ်စုဖွဲ့ရန် လိုအပ်သည်**။ အုပ်စုကို
`findall()` ရလဒ်ထဲ ထည့်မလာစေလိုလျှင် `(?:...)` ကို သုံးရသည်။

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

- `120 March 2019` — `\b` ၏ ရှေ့ပိုင်း စစ်ဆေးချက်ကြောင့် `20 March 2019` ကဲ့သို့
  **ဂဏန်းအပိုင်းအစ** ကို မှားဖမ်းခြင်းမှ ကာကွယ်ပေးသည်။
- `march` — alternation သည် case-sensitive ဖြစ်သောကြောင့် `March` နှင့်သာ ကိုက်ညီသည်။
  Case မခွဲလိုလျှင် `re.compile(..., re.IGNORECASE)` ကို သုံးနိုင်သည်။

ရက်စွဲ pattern သည် ဖွဲ့စည်းပုံ (ဂဏန်း + လ + ခုနှစ်) တိတိကျကျဖြစ်သောကြောင့် person pattern ထက်
**precision ပိုမြင့်** သည်။

---

## 6. `regex_ner()` — Pattern များကို အလုပ်လုပ်စေခြင်း

```python
def regex_ner(text, patterns):
    return {label: pattern.findall(text) for label, pattern in patterns}
```

ဤ function သည် argument နှစ်ခု လက်ခံသည်။

- `text` — စစ်ဆေးမည့် စာသား။
- `patterns` — `(label, compiled_pattern)` tuple များပါဝင်သော list။

Function အတွင်းရှိ တစ်လိုင်းတည်းကို ခွဲဖတ်ကြည့်ပါ။

```python
{label: pattern.findall(text) for label, pattern in patterns}
```

၎င်းသည် **dict comprehension** ဖြစ်သည်။ `patterns` ထဲမှ tuple တစ်ခုချင်းစီကို
`label` နှင့် `pattern` ဟု ခွဲယူပြီး၊ `label` ကို key အဖြစ်၊ ရှာတွေ့သော စာသားစာရင်းကို
value အဖြစ် ထည့်သည်။

ပုံမှန် `for` loop ဖြင့် ရေးမည်ဆိုလျှင် —

```python
def regex_ner(text, patterns):
    result = {}
    for label, pattern in patterns:
        result[label] = pattern.findall(text)
    return result
```

နှစ်ခုလုံး၏ ရည်ရွယ်ချက် တူညီသည်။

### `findall()` သည် မည်သည့်အရာကို ပြန်ပေးသနည်း။

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

`findall()` သည် ကိုက်ညီသော အပိုင်းအားလုံးကို **list** အဖြစ် ပြန်ပေးသည်။
မတွေ့လျှင် empty list `[]` ပြန်သည်။ Module 00 ၏ Exercise 5 တွင် သုံးခဲ့သော
`match()` သည် ပထမဆုံးတစ်ခုတည်းကို စစ်ပြီး `None` သို့မဟုတ် match object ပြန်သည်။
`findall()` သည် အားလုံးကို ရှာသည်။

---

## 7. Function ကို ခေါ်ပြီး ရလဒ်ကို ထုတ်ခြင်း

```python
entities = regex_ner(CORPUS, [("PER", PERSON_RE), ("DATE", DATE_RE)])
print("PER  :", entities["PER"])
print("DATE :", entities["DATE"])
```

`[("PER", PERSON_RE), ("DATE", DATE_RE)]` က tuple နှစ်ခုပါသော list ဖြစ်သည်။
`regex_ner()` သည် ၎င်းကို ဖတ်ပြီး dict တစ်ခု ပြန်ပေးသည်။

```python
print(entities == {
    "PER": PERSON_RE.findall(CORPUS),
    "DATE": DATE_RE.findall(CORPUS),
})
```

Output —

```text
True
```

ထို့နောက် `entities["PER"]` ဟု key ဖြင့် ဆွဲထုတ်သည်။ Dictionary indexing ဖြစ်သည်။

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

`London`၊ `Paris` တို့သည် **ပထဝီနေရာ (LOC)** ဖြစ်သည်။ ဤ Exercise တွင် `LOC` label
မသတ်မှတ်ထားသောကြောင့် ရလဒ်ထဲ မပါဝင်ပါ။ ၎င်းသည် **label set** ကန့်သတ်ချက်ဖြစ်သည် — pattern မှန်သော်လည်း
သတ်မှတ်ထားသော label မရှိလျှင် ထည့်စရာနေရာ မရှိပါ။

---

## 10. ကိုယ်တိုင်လေ့ကျင့်ကြည့်ပါ

**မေးခွန်း** — အောက်ပါ code သည် မည်သည့်ရလဒ် ပြန်ပေးမည်နည်း။

```python
import re

PATTERN = re.compile(r"\b[A-Z][a-z]+\b")
print(PATTERN.findall("Sundar Pichai visited London."))
```

1. `['Sundar Pichai']` — စကားလုံးနှစ်လုံး ဆက်နေသည်ကို ဖမ်းမည်
2. `['Sundar', 'Pichai', 'London']` — စာလုံးကြီးနှင့်စသော စကားလုံးတစ်လုံးစီ
3. `[]` — စကားလုံးနှစ်လုံး လိုအပ်သည်
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
