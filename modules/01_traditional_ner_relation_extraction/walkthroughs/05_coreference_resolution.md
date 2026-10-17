# Walkthrough 05 — Rule-based Coreference Resolution (Exercise 5)

> ဤဖိုင်သည် Module 01 ၏ `solution.md` ထဲက Exercise 5 ကို **Python အခြေခံမှ စ၍**
> အပိုင်းလိုက် ရှင်းပြသည့် walkthrough ဖြစ်သည်။

---

## 0. ဤ Exercise က ဘာကို ဖြေရှင်းပေးသလဲ။

စာသားထဲတွင် အမည်တစ်ခုကို အကြိမ်တိုင်း ပြန်ရေးမထားပါ။ ဒုတိယအကြိမ်မှစပြီး
**pronoun** (`He`၊ `She`၊ `They`) သို့မဟုတ် **possessive** (`His`၊ `Her`၊ `Their`)
ကို သုံးသည်။

```text
Sundar Pichai leads Google. He became CEO in 2015. His tenure expanded the company.
```

`He` ဆိုသည်မှာ မည်သူနည်း။ `His` ဆိုသည်မှာ မည်သူ၏ဟာနည်း။ လူတစ်ယောက်သည် `He` က
`Sundar Pichai` ဟု အလိုအလျောက် နားလည်သော်လည်း program သည် ၎င်းကို ရှာရသည်။
Pronoun တစ်ခုသည် မည်သည့် entity ကို ညွှန်နေသည်ကို ဆုံးဖြတ်သည့်အလုပ်ကို **coreference
resolution** ဟု ခေါ်သည်။

Graph တည်ဆောက်သောအခါ ဤအလုပ်သည် အရေးကြီးသည်။ `He` ကို မဖြေရှင်းလျှင် graph ထဲတွင်
`He` ဟူသော node မှားတစ်ခု ဖန်တီးမိမည်၊ သို့မဟုတ် relationship များ
မချိတ်ဆက်နိုင်တော့ပါ။

ဤ code တွင် လေ့လာရမည့် Python concepts များမှာ —

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

## 1. `COREF_PERSONS` — သိထားသော Entity များ

```python
COREF_PERSONS = {"Sundar Pichai": "M", "Larry Page": "M"}
```

Dictionary ၏ key သည် entity အမည်၊ value သည် metadata (`M` = male) ဖြစ်သည်။
ဤ Exercise တွင် `M`/`F` တန်ဖိုးကို တိုက်ရိုက် အသုံးမပြုသော်လည်း လက်တွေ့ system များတွင်
gender အပေါ် မူတည်ပြီး `He`/`She` ကို ခွဲခြားရန် အသုံးပြုသည်။

ဤ dictionary သည် **defaultdict မဟုတ်သော သာမန် dict** ဖြစ်သောကြောင့် မရှိသော အမည်ကို
key အဖြစ် ရှာလျှင် `KeyError` ဖြစ်သည်။

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

`in` သည် dict အတွက် **key** များထဲ ရှိမရှိ စစ်သည်။ ဤစစ်ဆေးချက်ကြောင့်
`KeyError` မဖြစ်အောင် ကာကွယ်နိုင်သည်။

---

## 2. `re.escape()` — အမည်များကို Pattern အဖြစ် သုံးရန် ပြင်ဆင်ခြင်း

```python
name_pattern = "|".join(re.escape(name) for name in persons)
```

`re.escape()` သည် စာသားထဲတွင် regex အတွက် **အထူးအဓိပ္ပာယ်ရှိသော** စာလုံးများရှေ့တွင် `\` ထည့်ပေးသည်။

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

နေရာလွတ် (space) ကို လည်း escape လုပ်ထားသည်ကို တွေ့နိုင်သည်။ ၎င်းသည်
မလိုအပ်သော်လည်း အန္တရာယ်မရှိပါ။

### Escape မလုပ်လျှင် မည်သို့ဖြစ်သနည်း။

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

Pattern ထဲက `.` သည် **"မည်သည့်စာလုံးမဆို"** ကို ဆိုလိုသည်။ ထို့ကြောင့် `St. John`
pattern သည် `StX John` ကိုတောင် ကိုက်ညီသွားသည်။ `re.escape()` သည် ဤသို့ မှားယွင်းသော
ကိုက်ညီမှုကို တားပေးသည်။

User data ကို pattern ထဲ ထည့်သောအခါ **အမြဲ `re.escape()` သုံးရသည်**။ ၎င်းသည်
အလိုအလျောက် ကာကွယ်မှုတစ်ခုဖြစ်သည်။

---

## 3. `"|".join(...)` — Generator Expression ဖြင့် Pattern ဖန်တီးခြင်း

```python
name_pattern = "|".join(re.escape(name) for name in persons)
```

ဤလိုင်းတွင် အပိုင်းနှစ်ခု ရှိသည်။

**ပထမအပိုင်း** — `re.escape(name) for name in persons` သည် `for` loop ကို
အတိုချုံးထားသော **generator expression** ဖြစ်သည်။ Loop လုပ်ပြီး တန်ဖိုးများကို
တစ်ခုချင်း ထုတ်ပေးသည်။ List comprehension နှင့် တူသော်လည်း list တစ်ခုလုံးကို
memory တွင် မဖန်တီးဘဲ တန်ဖိုးတစ်ခုချင်း ထုတ်သည်။ `persons` သည် dict ဖြစ်သောကြောင့်
`for name in persons` သည် **key** များကို လိုက်သည်။

**ဒုတိယအပိုင်း** — `"|".join(...)` သည် ရလဒ် စာသားများကို `|` ဖြင့် ဆက်ပေးသည်။

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
| `( ... )` | **Capturing group** — ကိုက်ညီသော pronoun/name ကို `group(1)` ဖြင့် ရယူရန် |
| `%s` | entity အမည်များ |
| `|He|She|They|His|Her|Their` | ရှာမည့် pronoun များ |
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

`findall()` သည် group တစ်ခု ပါလျှင် group ၏ အကြောင်းအရာကို ပြန်ပေးသည်။
ဤတွင် `Sundar Pichai` နှင့် `He` ဟူသော **အစဉ်လိုက် တန်ဖိုးများ** ရသည်။
မည်သည့် pronoun က မည်သူကို ညွှန်သည် ဆိုသည်ကို **pattern က မသိပါ** — ၎င်းကို
Section 6 ၏ callback function က ဆုံးဖြတ်သည်။

`\b` က အဘယ်ကြောင့် လိုအပ်သနည်း။ `\b` မပါလျှင် `He` သည် `The`၊ `weather` တို့၏ အတွင်းပိုင်းကို
ကိုက်ညီသွားနိုင်သည်။

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

ဤ output သည် အချက်နှစ်ချက်ကို ပြသည်။

- **Case** — `He` နှင့် `he` သည် မတူပါ။ `re.IGNORECASE` မပါလျှင် မကိုက်ညီပါ။
- **`\b`** — `The` ထဲမှ `he`၊ `weather` ထဲမှ `he`၊ `here` ထဲမှ `her` တို့သည်
  စာလုံးအတွင်းပိုင်း၌ ရှိသဖြင့် `\b` ဖြင့် ပိတ်လိုက်သောအခါ မကိုက်ညီတော့ပါ။

`\b` မရှိလျှင် `He` ဟူသော pronoun အတွက် `The`၊ `weather` ကဲ့သို့ လုံးဝမသက်ဆိုင်သော
စာလုံးများ ပါဝင်လာပြီး callback က မှားယွင်းသော နေရာများကို အစားထိုးလိမ့်မည်။

---

## 5. `state = {"last": None}` — State ကို Dictionary ဖြင့် ထိန်းခြင်း

```python
state = {"last": None}
```

Callback function သည် **မှတ်ခဲ့သော နောက်ဆုံး entity**ကို သိထားရန် လိုသည်။
ထို့ကြောင့် `state` dictionary တစ်ခု ဖန်တီးပြီး ထိုထဲတွင် သိမ်းသည်။

Dictionary သုံးခြင်းသည် ရည်ရွယ်ချက်ရှိသည်။ Nested function တစ်ခုသည် အပြင်က
variable တစ်ခုကို **ပြင်လိုလျှင်** `nonlocal` လိုသည်။ Dictionary **အတွင်းကို**
ပြင်ခြင်းမှာမူ `nonlocal` မလိုပါ။

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

`inner` ထဲတွင် `last = token` ဟု ရေးလိုက်ခြင်းသည် `last` ကို `inner` ၏ **local
variable** ဖြစ်စေသည်။ ထို့ကြောင့် `last` ကို မသတ်မှတ်မီ ဖတ်သောအခါ error ဖြစ်သည်။
(`token == "NAME"` ဖြစ်လျှင် သတ်မှတ်ပြီးသားဖြစ်သောကြောင့် error မဖြစ်ပါ။)

Dictionary ဖြင့် ရေးလျှင် ဤပြဿနာ မရှိပါ —

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

ဤအလုပ်ကို `nonlocal last` ဖြင့်လည်း လုပ်နိုင်သည်။

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

နည်းလမ်းနှစ်ခုလုံး အလုပ်လုပ်သည်။ Exercise က ရွေးချယ်ထားသည်မှာ dictionary
နည်းလမ်းဖြစ်သည်။ ၎င်းသည် state ကို **ဖော်ထုတ်ပြသနိုင်** (inspect) ခြင်းကြောင့်ဖြစ်သည် —
စမ်းသပ်သောအခါ `state["last"]` ကို တိုက်ရိုက် ကြည့်နိုင်သည်။

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

`replace()` သည် **match object** တစ်ခုကို လက်ခံပြီး **စာသား (string)** တစ်ခု
ပြန်ပေးရသည်။ ပြန်ပေးသော စာသားသည် မူရင်းစာသား၏ နေရာတွင် အစားထိုးခံရသည်။

### Branch ၁ — Entity အမည် တွေ့ခြင်း

```python
if token in persons:
    state["last"] = token
    return token
```

`token in persons` သည် dict ၏ key များထဲ ရှိမရှိ စစ်သည်။ တွေ့လျှင် ထိုအမည်ကို
**လက်ရှိ antecedent** အဖြစ် မှတ်လိုက်သည်။ ပြန်ပေးသော တန်ဖိုးသည် မူရင်းအတိုင်း
ဖြစ်သောကြောင့် စာသားတွင် ပြောင်းလဲမှု မရှိပါ။

### Branch ၂ — Antecedent မရှိသေးခြင်း

```python
if state["last"] is None:
    return token
```

Pronoun တစ်ခုသည် entity တစ်ခု၏ အရင်တွင် လာလျှင် မည်သူကို ညွှန်သည်ကို မသိပါ။
ဤအခါ မခန့်မှန်းဘဲ မူရင်းအတိုင်း ထားလိုက်သည်။ **မသိလျှင် မပြင်ခြင်း** သည်
မှန်ကန်သော ဒီဇိုင်းဖြစ်သည် — မှားသော ခန့်မှန်းချက်ထက် မခန့်မှန်းခြင်းက ပိုကောင်းသည်။

### Branch ၃ — Possessive

```python
if token.lower() in {"his", "her", "their"}:
    return state["last"] + "'s"
```

`token.lower()` သည် စာလုံးအသေးပြောင်းသည်။ `{"his", "her", "their"}` သည် **set**
ဖြစ်ပြီး `in` ဖြင့် အမြန်ရှာနိုင်သည်။ `His` → `Sundar Pichai's` ဖြစ်သွားသည်။

မှတ်ချက် — `'s` ထည့်ခြင်းသည် ရိုးရှင်းသော ခန့်မှန်းချက်ဖြစ်သည်။ `Their` အတွက်မူ `'s` သည်
သဒ္ဒါအရ မမှန်ပါ၊ `They` ဟူသော အုပ်စုကို ကိုယ်စားပြုခြင်းကြောင့်ဖြစ်သည်။ ဤ Exercise ၏ ရည်ရွယ်ချက်သည်
callback logic ပြရန်ဖြစ်သောကြောင့် ရိုးရှင်းစွာ ထားထားခြင်းဖြစ်သည်။

### Branch ၄ — ကျန် Pronoun များ

```python
return state["last"]
```

`He`၊ `She`၊ `They` တို့သည် နောက်ဆုံးမှတ်ထားသော entity အမည်နှင့် အစားထိုးခံရသည်။

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

`re.sub()` သည် ပုံမှန်အားဖြင့် စာသားတစ်ခုနှင့် အစားထိုးသည်။

```python
import re

print(re.sub(r"He", "X", "He said. He left."))
```

Output —

```text
X said. X left.
```

သို့သော် ဒုတိယ argument နေရာတွင် **function** ကို ပေးနိုင်သည်။ ထိုအခါ Python သည်
match တစ်ခုတွေ့တိုင်း ထို function ကို ခေါ်ပြီး ၎င်းပြန်ပေးသော စာသားနှင့်
အစားထိုးသည်။

```python
import re

print(re.sub(r"He", lambda m: "<" + m.group(0) + ">", "He said. He left."))
```

Output —

```text
<He> said. <He> left.
```

ဤနည်း၏ အကျိုးကျေးဇူးသည် **match တစ်ခုချင်းစီအတွက် မတူညီသော ဆုံးဖြတ်ချက်**
ချနိုင်ခြင်းဖြစ်သည်။ ဤ Exercise တွင် ပထမ `He` သည် `Sundar Pichai` ဖြစ်ပြီး `His` သည်
`Sundar Pichai's` ဖြစ်ခြင်းမှာ ထိုကြောင့်ဖြစ်သည်။

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

### ဤနည်းလမ်း၏ ကန့်သတ်ချက်

`last` ကို **တစ်ခုတည်း** မှတ်ထားခြင်းကြောင့် entity နှစ်ခုရှိသော စာသားတွင် မှားနိုင်သည်။

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

ဤဥပမာတွင် အလိုအလျောက် မှန်သွားသည်။ သို့သော် စာသားအစဉ် ပြောင်းလျှင် —

```text
Sundar Pichai leads Google. He stepped down. Larry Page took over.
```

ဤအခါ ဒုတိယ `He` သည် `Sundar Pichai` ဖြစ်ဆဲဖြစ်သောကြောင့် မှန်သည်။ သို့သော် —

```text
Larry Page founded Google. Sundar Pichai became the CEO. He expanded the team.
```

တွင် `He` သည် `Sundar Pichai` ဖြစ်သင့်သော်လည်း `last` သည် `Sundar Pichai` ဖြစ်နေသောကြောင့် မှန်သည်။
အမှန်တကယ်တွင် ဤနည်းလမ်းသည် **"နောက်ဆုံး ဖော်ပြခဲ့သော entity"** rule ကိုသာ သုံးခြင်းဖြစ်သည်။
အမှန်တကယ် coreference resolution တွင် လိင်ကိုက်ညီမှု၊ အရေအတွက် (singular/plural)၊
ဝါကျအတွင်း အနေအထား စသော အချက်များကိုပါ စဉ်းစားရသည်။

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

**မေးခွန်း** — အောက်ပါ input အတွက် `resolve_coreference()` သည် မည်သည့်ရလဒ်
ပြန်ပေးမည်နည်း။

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
