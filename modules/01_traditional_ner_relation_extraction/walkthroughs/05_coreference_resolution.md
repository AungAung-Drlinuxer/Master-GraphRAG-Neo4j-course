# Walkthrough 05 — Rule-based Coreference Resolution (Exercise 5)

> ဤဖိုင်သည် Module 01 ၏ `solution.md` ထဲက Exercise 5 ကို **Python အခြေခံမှ စ၍**
> အပိုင်းလိုက် ရှင်းပြသည့် walkthrough ဖြစ်သည်။

---

## 0. ဤ Exercise က ဘာကို ဖြေရှင်းပေးသလဲ။

စာသားထဲမှာ အမည်တစ်ခုကို အကြိမ်တိုင်း ပြန်ရေးမထားပါဘူး။ ဒုတိယအကြိမ်ကစပြီး
**pronoun** (`He`၊ `She`၊ `They`) သို့မဟုတ် **possessive** (`His`၊ `Her`၊ `Their`)
ကို သုံးပါတယ်။

```text
Sundar Pichai leads Google. He became CEO in 2015. His tenure expanded the company.
```

`He` ဆိုတာ ဘယ်သူလဲ။ `His` ဆိုတာ ဘယ်သူ့ဟာလဲ။ လူတစ်ယောက်က `He` က
`Sundar Pichai` လို့ အလိုအလျောက် နားလည်ပေမဲ့ program က ဒါကို ရှာရပါတယ်။
Pronoun တစ်ခုက ဘယ် entity ကို ညွှန်နေလဲ ဆုံးဖြတ်တဲ့အလုပ်ကို **coreference
resolution** လို့ ခေါ်ပါတယ်။

Graph တည်ဆောက်တဲ့အခါ ဒီအလုပ်က အရေးကြီးပါတယ်။ `He` ကို မဖြေရှင်းရင် graph ထဲမှာ
`He` ဆိုတဲ့ node မှားတစ်ခု ဖန်တီးမိမယ်၊ ဒါမှမဟုတ် relationship တွေ
မချိတ်ဆက်နိုင်တော့ပါဘူး။

ဒီ code မှာ လေ့လာရမယ့် Python concepts တွေကတော့ —

- `dict` (persons) နှင့် `.join()` ဖြင့် pattern ဖန်တီးခြင်း
- Generator expression (`for name in persons`)
- `re.escape()`
- `re.sub()` — string အစားထိုးခြင်း
- **`re.sub()` ကို function ဖြင့် ခေါ်ခြင်း (callback)**
- Nested function (function အတွင်း function) နှင့် closure
- `state` dictionary ဖြင့် state ထိန်းသိမ်းခြင်း
- `set` membership test (`in {...}`)
- `str.lower()`

---

## 1. `COREF_PERSONS` — သိထားတဲ့ Entity များ

```python
COREF_PERSONS = {"Sundar Pichai": "M", "Larry Page": "M"}
```

Dictionary ၏ key က entity အမည်၊ value က metadata (`M` = male) ဖြစ်ပါတယ်။
ဒီ Exercise မှာ `M`/`F` တန်ဖိုးကို တိုက်ရိုက် အသုံးမပြုပေမဲ့ လက်တွေ့ system တွေမှာ
gender အပေါ် မူတည်ပြီး `He`/`She` ကို ခွဲခြားဖို့ အသုံးပြုပါတယ်။

ဒီ dictionary က **defaultdict မဟုတ်တဲ့ သာမန် dict** ဖြစ်တဲ့အတွက် မရှိတဲ့ အမည်ကို
key အဖြစ် ရှာရင် `KeyError` ဖြစ်ပါတယ်။

```python
COREF_PERSONS = {"Sundar Pichai": "M", "Larry Page": "M"}

print("Sundar Pichai" in COREF_PERSONS)
print("Satya Nadella" in COREF_PERSONS)
```

Output —

```text
True
False
```

`in` က dict အတွက် **key** များထဲ ရှိမရှိ စစ်ပါတယ်။ ဒီစစ်ဆေးချက်ကြောင့်
`KeyError` မဖြစ်အောင် ကာကွယ်နိုင်ပါတယ်။

---

## 2. `re.escape()` — အမည်များကို Pattern အဖြစ် သုံးရန် ပြင်ဆင်ခြင်း

```python
name_pattern = "|".join(re.escape(name) for name in persons)
```

`re.escape()` က စာသားထဲမှာ regex အတွက် **အထူးအဓိပ္ပာယ်ရှိတဲ့** စာလုံးများရှေ့မှာ
`\` ထည့်ပေးပါတယ်။

```python
import re

print(re.escape("Sundar Pichai"))
print(re.escape("Acme"))
print(re.escape("A.B (C) [D]"))
print(re.escape("Acme+Corp"))
```

Output —

```text
Sundar\ Pichai
Acme
A\.B\ \(C\)\ \[D\]
Acme\+Corp
```

နေရာလွတ် (space) ကို လည်း escape လုပ်ထားတာကို တွေ့နိုင်ပါတယ်။ ဒါက
မလိုအပ်ပေမဲ့ အန္တရာယ်မရှိပါဘူး။

### Escape မလုပ်ရင် ဘာဖြစ်သလဲ။

```python
import re

print(re.findall("St. John", "StX John"))
print(re.findall(re.escape("St. John"), "StX John"))
print(re.findall(re.escape("St. John"), "St. John"))
```

Output —

```text
['StX John']
[]
['St. John']
```

Pattern ထဲက `.` က **"မည်သည့်စာလုံးမဆို"** ကို ဆိုလိုပါတယ်။ ဒါကြောင့် `St. John`
pattern က `StX John` ကိုတောင် ကိုက်ညီသွားပါတယ်။ `re.escape()` က ဒီလို မှားယွင်းတဲ့
ကိုက်ညီမှုကို တားပေးပါတယ်။

User data ကို pattern ထဲ ထည့်တဲ့အခါ **အမြဲ `re.escape()` သုံးရပါတယ်**။ ဒါက
အလိုအလျောက် ကာကွယ်မှုတစ်ခုပါ။

---

## 3. `"|".join(...)` — Generator Expression ဖြင့် Pattern ဖန်တီးခြင်း

```python
name_pattern = "|".join(re.escape(name) for name in persons)
```

ဒီလိုင်းမှာ အပိုင်းနှစ်ခု ရှိပါတယ်။

**ပထမအပိုင်း** — `re.escape(name) for name in persons` က `for` loop ကို
အတိုချုံးထားတဲ့ **generator expression** ဖြစ်ပါတယ်။ Loop လုပ်ပြီး တန်ဖိုးများကို
တစ်ခုချင်း ထုတ်ပေးပါတယ်။ List comprehension နဲ့ တူပေမဲ့ list တစ်ခုလုံးကို
memory မှာ မဖန်တီးဘဲ တန်ဖိုးတစ်ခုချင်း ထုတ်ပါတယ်။ `persons` က dict ဖြစ်တဲ့အတွက်
`for name in persons` က **key** များကို လိုက်ပါတယ်။

**ဒုတိယအပိုင်း** — `"|".join(...)` က ရလဒ် စာသားများကို `|` နဲ့ ဆက်ပေးပါတယ်။

```python
persons = {"Sundar Pichai": "M", "Larry Page": "M"}
import re

names = [re.escape(name) for name in persons]
print(names)
print("|".join(names))
print(re.escape("Sundar Pichai") + "|" + re.escape("Larry Page"))
```

Output —

```text
['Sundar\\ Pichai', 'Larry\\ Page']
Sundar\ Pichai|Larry\ Page
Sundar\ Pichai|Larry\ Page
```

---

## 4. Pattern တည်ဆောက်ခြင်း

```python
pattern = re.compile(r"\b(%s|He|She|They|His|Her|Their)\b" % name_pattern)
```

| အပိုင်း | အဓိပ္ပာယ် |
| --- | --- |
| `\b` | Word boundary |
| `( ... )` | **Capturing group** — ကိုက်ညီတဲ့ pronoun/name ကို `group(1)` ဖြင့် ရယူရန် |
| `%s` | entity အမည်များ |
| `|He|She|They|His|Her|Their` | ရှာမယ့် pronoun များ |
| `\b` | Word boundary |

```python
import re

persons = {"Sundar Pichai": "M"}
name_pattern = "|".join(re.escape(name) for name in persons)
pattern = re.compile(r"\b(%s|He|She|They|His|Her|Their)\b" % name_pattern)

print(pattern.pattern)
print()
print(pattern.findall("Sundar Pichai leads Google. He became CEO in 2015."))
```

Output —

```text
\b(Sundar\ Pichai|He|She|They|His|Her|Their)\b

['Sundar Pichai', 'He']
```

`findall()` က group တစ်ခု ပါရင် group ၏ အကြောင်းအရာကို ပြန်ပေးပါတယ်။
ဒီမှာ `Sundar Pichai` နဲ့ `He` ဆိုတဲ့ **အစဉ်လိုက် တန်ဖိုးများ** ရပါတယ်။
ဘယ် pronoun က ဘယ်သူကို ညွှန်တာလဲ ဆိုတာကို **pattern က မသိပါဘူး** — ဒါကို
Section 6 ၏ callback function က ဆုံးဖြတ်ပါတယ်။

`\b` က ဘာကြောင့် လိုသလဲ။ `\b` မပါရင် `He` က `The`၊ `weather` တို့၏ အတွင်းပိုင်းကို
ကိုက်ညီသွားနိုင်ပါတယ်။

```python
import re

CASE = re.compile(r"(He|Her)")
IGNORE = re.compile(r"(He|Her)", re.IGNORECASE)
BOUNDED = re.compile(r"\b(He|Her)\b", re.IGNORECASE)

text = "The weather here is fine."
print("case-sensitive     :", CASE.findall(text))
print("ignorecase, no \\b :", IGNORE.findall(text))
print("ignorecase + \\b    :", BOUNDED.findall(text))
```

Output —

```text
case-sensitive     : []
ignorecase, no \b : ['he', 'he', 'he']
ignorecase + \b    : []
```

ဤ output သည် အချက်နှစ်ချက်ကို ပြပါတယ်။

- **Case** — `He` နှင့် `he` သည် မတူပါ။ `re.IGNORECASE` မပါလျှင် မကိုက်ညီပါ။
- **`\b`** — `The` ထဲမှ `he`၊ `weather` ထဲမှ `he`၊ `here` ထဲမှ `her` တို့သည်
  စာလုံးအတွင်းပိုင်း၌ ရှိသဖြင့် `\b` ဖြင့် ပိတ်လိုက်သောအခါ မကိုက်ညီတော့ပါ။

`\b` မရှိလျှင် `He` ဆိုတဲ့ pronoun အတွက် `The`၊ `weather` လို လုံးဝမသက်ဆိုင်တဲ့
စာလုံးများ ပါဝင်လာပြီး callback က မှားယွင်းသော နေရာများကို အစားထိုးလိမ့်မည်။

---

## 5. `state = {"last": None}` — State ကို Dictionary ဖြင့် ထိန်းခြင်း

```python
state = {"last": None}
```

Callback function က **မှတ်ခဲ့တဲ့ နောက်ဆုံး entity**ကို သိထားဖို့ လိုပါတယ်။
ဒါကြောင့် `state` dictionary တစ်ခု ဖန်တီးပြီး အဲဒီထဲမှာ သိမ်းပါတယ်။

Dictionary သုံးတာက ရည်ရွယ်ချက်ရှိပါတယ်။ Nested function တစ်ခုက အပြင်က
variable တစ်ခုကို **ပြင်ချင်** ရင် `nonlocal` လိုပါတယ်။ Dictionary **အတွင်းကို**
ပြင်တာကတော့ `nonlocal` မလိုပါဘူး။

```python
def outer():
    last = None

    def inner(token):
        if token == "NAME":
            last = token
        return last

    return inner


f = outer()
try:
    print(f("He"))
except Exception as exc:
    print("ERROR:", type(exc).__name__, "-", exc)
```

Output —

```text
ERROR: UnboundLocalError - cannot access local variable 'last' where it is not associated with a value
```

`inner` ထဲမှာ `last = token` လို့ ရေးလိုက်တာက `last` ကို `inner` ၏ **local
variable** ဖြစ်စေပါတယ်။ ဒါကြောင့် `last` ကို မသတ်မှတ်ခင် ဖတ်တဲ့အခါ error ဖြစ်ပါတယ်။
(`token == "NAME"` ဖြစ်ရင် သတ်မှတ်ပြီးသားဖြစ်လို့ error မဖြစ်ပါ။)

Dictionary နဲ့ ရေးရင် ဒီပြဿနာ မရှိပါဘူး —

```python
def outer():
    state = {"last": None}

    def inner(token):
        if token == "NAME":
            state["last"] = token     # dict ကို ပြင်သည်၊ variable ကို ချိန်ညှိသည်မဟုတ်
        return state["last"]

    return inner


f = outer()
print(f("He"))
print(f("NAME"))
```

Output —

```text
None
NAME
```

ဒီအလုပ်ကို `nonlocal last` နဲ့လည်း လုပ်နိုင်ပါတယ်။

```python
def outer():
    last = None

    def inner(token):
        nonlocal last
        if token == "NAME":
            last = token
        return last

    return inner


f = outer()
print(f("He"))
print(f("NAME"))
print(f("He"))
```

Output —

```text
None
NAME
NAME
```

နည်းလမ်းနှစ်ခုလုံး အလုပ်လုပ်ပါတယ်။ Exercise က ရွေးချယ်ထားတာက dictionary
နည်းလမ်းပါ။ ဒါက state ကို **ဖော်ထုတ်ပြသနိုင်** (inspect) လို့ ရလို့ပါတယ် —
စမ်းသပ်တဲ့အခါ `state["last"]` ကို တိုက်ရိုက် ကြည့်နိုင်ပါတယ်။

---

## 6. `replace()` — Callback Function

```python
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
```

`replace()` က **match object** တစ်ခုကို လက်ခံပြီး **စာသား (string)** တစ်ခု
ပြန်ပေးရပါတယ်။ ပြန်ပေးတဲ့ စာသားက မူရင်းစာသား၏ နေရာမှာ အစားထိုးခံရပါတယ်။

### Branch ၁ — Entity အမည် တွေ့ခြင်း

```python
if token in persons:
    state["last"] = token
    return token
```

`token in persons` က dict ၏ key များထဲ ရှိမရှိ စစ်ပါတယ်။ တွေ့ရင် အဲဒီအမည်ကို
**လက်ရှိ antecedent** အဖြစ် မှတ်လိုက်ပါတယ်။ ပြန်ပေးတဲ့ တန်ဖိုးက မူရင်းအတိုင်း
ဖြစ်တဲ့အတွက် စာသားမှာ ပြောင်းလဲမှု မရှိပါ။

### Branch ၂ — Antecedent မရှိသေးခြင်း

```python
if state["last"] is None:
    return token
```

Pronoun တစ်ခုက entity တစ်ခု၏ အရင်မှာ လာရင် ဘယ်သူကို ညွှန်မှန်း မသိပါဘူး။
ဒီအခါ မခန့်မှန်းဘဲ မူရင်းအတိုင်း ထားလိုက်ပါတယ်။ **မသိရင် မပြင်ခြင်း** က
မှန်ကန်တဲ့ ဒီဇိုင်းပါ — မှားတဲ့ ခန့်မှန်းချက်ထက် မခန့်မှန်းတာ ပိုကောင်းပါတယ်။

### Branch ၃ — Possessive

```python
if token.lower() in {"his", "her", "their"}:
    return state["last"] + "'s"
```

`token.lower()` က စာလုံးအသေးပြောင်းပါတယ်။ `{"his", "her", "their"}` က **set**
ဖြစ်ပြီး `in` ဖြင့် အမြန်ရှာနိုင်ပါတယ်။ `His` → `Sundar Pichai's` ဖြစ်သွားပါတယ်။

မှတ်ချက် — `'s` ထည့်တာက ရိုးရှင်းတဲ့ ခန့်မှန်းချက်ပါ။ `Their` အတွက်တော့ `'s` က
သဒ္ဒါအရ မမှန်ပါ၊ `They` ဆိုတဲ့ အုပ်စုကို ကိုယ်စားပြုလို့ပါ။ ဒီ Exercise ၏ ရည်ရွယ်ချက်က
callback logic ပြဖို့ဖြစ်လို့ ရိုးရှင်းစွာ ထားထားတာပါ။

### Branch ၄ — ကျန် Pronoun များ

```python
return state["last"]
```

`He`၊ `She`၊ `They` တို့က နောက်ဆုံးမှတ်ထားတဲ့ entity အမည်နဲ့ အစားထိုးခံရပါတယ်။

```python
persons = {"Sundar Pichai": "M"}
state = {"last": "Sundar Pichai"}
tokens = ["He", "His", "She", "They"]

for token in tokens:
    if token in persons:
        print(token, "-> entity")
    elif state["last"] is None:
        print(token, "-> unchanged")
    elif token.lower() in {"his", "her", "their"}:
        print(token, "->", state["last"] + "'s")
    else:
        print(token, "->", state["last"])
```

Output —

```text
He -> Sundar Pichai
His -> Sundar Pichai's
She -> Sundar Pichai
They -> Sundar Pichai
```

---

## 7. `pattern.sub(replace, text)` — Function ဖြင့် အစားထိုးခြင်း

```python
return pattern.sub(replace, text)
```

`re.sub()` က ပုံမှန်အားဖြင့် စာသားတစ်ခုနဲ့ အစားထိုးပါတယ်။

```python
import re

print(re.sub(r"He", "X", "He said. He left."))
```

Output —

```text
X said. X left.
```

ဒါပေမဲ့ ဒုတိယ argument နေရာမှာ **function** ကို ပေးလို့ရပါတယ်။ အဲဒီအခါ Python က
match တစ်ခုတွေ့တိုင်း အဲဒီ function ကို ခေါ်ပြီး သူပြန်ပေးတဲ့ စာသားနဲ့
အစားထိုးပါတယ်။

```python
import re

print(re.sub(r"He", lambda m: "<" + m.group(0) + ">", "He said. He left."))
```

Output —

```text
<He> said. <He> left.
```

ဒီနည်း၏ အကျိုးကျေးဇူးက **match တစ်ခုချင်းစီအတွက် မတူညီတဲ့ ဆုံးဖြတ်ချက်**
ချနိုင်တာပါ။ ဒီ Exercise မှာ ပထမ `He` က `Sundar Pichai` ဖြစ်ပြီး `His` က
`Sundar Pichai's` ဖြစ်တာ အဲဒီကြောင့်ပါ။

---

## 8. ရလဒ်ကို ထုတ်ခြင်း

```python
print("before:", COREF_TEXT)
print("after :", resolve_coreference(COREF_TEXT, COREF_PERSONS))
```

Expected output —

```text
before: Sundar Pichai leads Google. He became CEO in 2015. His tenure expanded the company.
after : Sundar Pichai leads Google. Sundar Pichai became CEO in 2015. Sundar Pichai's tenure expanded the company.
```

| မူရင်း | အစားထိုးပြီး | အကြောင်းရင်း |
| --- | --- | --- |
| `He` | `Sundar Pichai` | နောက်ဆုံး antecedent |
| `His` | `Sundar Pichai's` | Possessive branch |

### ဒီနည်းလမ်း၏ ကန့်သတ်ချက်

`last` ကို **တစ်ခုတည်း** မှတ်ထားတာကြောင့် entity နှစ်ခုရှိတဲ့ စာသားမှာ မှားနိုင်ပါတယ်။

```python
import re

persons = {"Sundar Pichai": "M", "Larry Page": "M"}
name_pattern = "|".join(re.escape(name) for name in persons)
pattern = re.compile(r"\b(%s|He|She|They|His|Her|Their)\b" % name_pattern)

text = "Sundar Pichai leads Google. Larry Page founded it. He stepped down."
state = {"last": None}

def replace(match):
    token = match.group(1)
    if token in persons:
        state["last"] = token
        return token
    if state["last"] is None:
        return token
    return state["last"]

result = pattern.sub(replace, text)
print("after :", result)
print("ကောက်ချက်: 'He' သည် Larry Page ကို ညွှန်သင့်သည်")
```

Output —

```text
after : Sundar Pichai leads Google. Larry Page founded it. Larry Page stepped down.
ကောက်ချက်: 'He' သည် Larry Page ကို ညွှန်သင့်သည်
```

ဒီဥပမာမှာ အလိုအလျောက် မှန်သွားပါတယ်။ ဒါပေမဲ့ စာသားအစဉ် ပြောင်းရင် —

```text
Sundar Pichai leads Google. He stepped down. Larry Page took over.
```

ဒီအခါ ဒုတိယ `He` က `Sundar Pichai` ဖြစ်ဆဲမို့ မှန်ပါတယ်။ ဒါပေမဲ့ —

```text
Larry Page founded Google. Sundar Pichai became the CEO. He expanded the team.
```

မှာ `He` က `Sundar Pichai` ဖြစ်သင့်ပေမဲ့ `last` က `Sundar Pichai` ဖြစ်နေလို့ မှန်ပါတယ်။
တကယ်တမ်း ဒီနည်းလမ်းက **"နောက်ဆုံး ဖော်ပြခဲ့တဲ့ entity"** rule ကိုသာ သုံးတာပါ။
အမှန်တကယ် coreference resolution မှာ လိင်ကိုက်ညီမှု၊ အရေအတွက် (singular/plural)၊
ဝါကျအတွင်း အနေအထား စတဲ့ အချက်များကိုပါ စဉ်းစားရပါတယ်။

---

## 9. Code တစ်ခုလုံး — Run လုပ်နိုင်သော Version

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
```

Output —

```text
before: Sundar Pichai leads Google. He became CEO in 2015. His tenure expanded the company.
after : Sundar Pichai leads Google. Sundar Pichai became CEO in 2015. Sundar Pichai's tenure expanded the company.
```

---

## 10. ကိုယ်တိုင်လေ့ကျင့်ကြည့်ပါ

**မေးခွန်း** — အောက်ပါ input အတွက် `resolve_coreference()` က ဘယ်ရလဒ်
ပြန်ပေးမလဲ။

```python
persons = {"Sundar Pichai": "M"}
text = "He left the company. Sundar Pichai joined Google."
```

1. `He` က `Sundar Pichai` ဖြစ်သွားမည်
2. `He` က မူရင်းအတိုင်း `He` ကျန်မည်
3. Error ဖြစ်မည်
4. `He` က `None` ဖြစ်သွားမည်

<details>
<summary>အဖြေ ကြည့်ရန်</summary>

**အဖြေ — 2. `He` က မူရင်းအတိုင်း `He` ကျန်မည်**

အကြောင်းရင်း — `He` သည် entity အမည် အရင်မှာ လာသည်။ `state["last"]` သည်
`None` ဖြစ်ဆဲဖြစ်သဖြင့် `replace()` ၏ ဒုတိယ branch
`if state["last"] is None: return token` သို့ ရောက်ပြီး `He` ကို မူရင်းအတိုင်း
ပြန်ပေးသည်။ ထို့ကြောင့် ရလဒ်မှာ —

```text
He left the company. Sundar Pichai joined Google.
```

ဖြစ်သည်။ ဤအချက်သည် "antecedent မရှိလျှင် မခန့်မှန်းခြင်း" ဒီဇိုင်းကို ပြသည်။

</details>

---

**အဓိက မှတ်ထားရန်** — `re.sub()` ကို callback function ဖြင့် ခေါ်ခြင်းသည်
match တစ်ခုချင်းစီအတွက် မတူညီသော ဆုံးဖြတ်ချက် ချနိုင်သည့် နည်းလမ်းဖြစ်သည်။
Callback သည် `state` dictionary ဖြင့် ယခင် match များ၏ အခြေအနေကို မှတ်ထားသည်။
Graph တည်ဆောက်ရာတွင် pronoun များကို ဤသို့ ဖြေရှင်းခြင်းဖြင့် node အပိုများ
မဖြစ်ပေါ်စေဘဲ relationship များကို မှန်ကန်စွာ ချိတ်ဆက်နိုင်သည်။
