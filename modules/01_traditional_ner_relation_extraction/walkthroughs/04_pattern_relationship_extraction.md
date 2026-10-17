# Walkthrough 04 — Pattern-based Relationship Extraction (Exercise 4)

> ဤဖိုင်သည် Module 01 ၏ `solution.md` ထဲက Exercise 4 ကို **Python အခြေခံမှ စ၍**
> အပိုင်းလိုက် ရှင်းပြသည့် walkthrough ဖြစ်သည်။

---

## 0. ဤ Exercise က ဘာကို ဖြေရှင်းပေးသလဲ။

Exercise 1–3 တွင် entity များကို ရှာထုတ်ခဲ့သည်။ Graph တစ်ခု တည်ဆောက်ရန်
entity များ တစ်ခုတည်းနှင့် မလုံလောက်ပါ — ၎င်းတို့အကြားက **relationship** လည်း
လိုသည်။

```text
Sundar Pichai is the CEO of Google. Larry Page founded Google.
```

ဤစာသားမှ အောက်ပါ **triples** များ ထုတ်ယူလိုသည်။

```text
(Sundar Pichai, CEO_OF, Google)
(Larry Page, FOUNDED, Google)
```

Triple တစ်ခုစီတွင် **subject**၊ **relation** နှင့် **object** ပါသည်။ ဤဖိုင်တွင်
relationship များကို **regex pattern** ဖြင့် ထုတ်ယူပုံကို လေ့လာမည်။

ဤ code တွင် လေ့လာရမည့် Python concepts များမှာ —

- Regex pattern ကို **string** အဖြစ် သိမ်းပြီး pattern အသစ် ဖန်တီးခြင်း
- `%s` ဖြင့် pattern ထဲ pattern ထည့်ခြင်း (nested pattern)
- Capturing group `(...)`
- `findall()` နှင့် `finditer()` ကွာခြားချက်
- `match.group(n)` နှင့် `match.groups()`
- List of tuples (`REL_RULES`)
- Nested list comprehension (`for` နှစ်ခု)
- Tuple unpacking (`pattern, relation` / `m.group(1), relation, m.group(2)`)
- `%` formatting

---

## 1. `PERSON` — Pattern ကို String အဖြစ် သိမ်းခြင်း

```python
PERSON = r"\b[A-Z][a-z]+ [A-Z][a-z]+\b"
```

Exercise 1 တွင် `re.compile()` လုပ်ထားသော pattern object တစ်ခုကို သိမ်းခဲ့သည်။
ဤ Exercise တွင်မူ **စာသား (string)** အဖြစ်သာ သိမ်းထားသည်။ အကြောင်းရင်းမှာ
ဤ pattern ကို pattern **အသစ်များထဲ ထည့်ရန်** လိုခြင်းကြောင့်ဖြစ်သည်။

`re.compile()` လုပ်ထားသော object ကို `%s` ဖြင့် ထည့်လျှင် အလုပ်လုပ်သည်၊ သို့သော်
ဤအဆင့်တွင် ရည်ရွယ်သည့်အလုပ်သည် စာသားအဆင့်တွင် ဆက်စပ်ခြင်းဖြစ်သောကြောင့် string အဖြစ်ထားခြင်းက
ပိုရှင်းသည်။

```python
print(PERSON)
print(type(PERSON))
```

Output —

```text
\b[A-Z][a-z]+ [A-Z][a-z]+\b
<class 'str'>
```

---

## 2. `REL_RULES` — Rule များစာရင်း

```python
REL_RULES = [
    (re.compile(r"(%s) is the CEO of ([A-Z][A-Za-z]+)" % PERSON), "CEO_OF"),
    (re.compile(r"(%s) founded ([A-Z][A-Za-z]+)" % PERSON), "FOUNDED"),
]
```

၎င်းသည် **list of tuples** ဖြစ်သည်။ Tuple တစ်ခုစီတွင် —

- ပထမ item — compile လုပ်ထားသော regex pattern
- ဒုတိယ item — ထို pattern က ကိုယ်စားပြုသော relation label

| Pattern (အတိုချုပ်) | Relation |
| --- | --- |
| `<PERSON> is the CEO of <ORG>` | `CEO_OF` |
| `<PERSON> founded <ORG>` | `FOUNDED` |

Rule တစ်ခုချင်းစီ ဖော်ပြပုံကို ကြည့်ပါ။

```python
import re

PERSON = r"\b[A-Z][a-z]+ [A-Z][a-z]+\b"
CEO = re.compile(r"(%s) is the CEO of ([A-Z][A-Za-z]+)" % PERSON)

print(CEO.pattern)
```

Output —

```text
(\b[A-Z][a-z]+ [A-Z][a-z]+\b) is the CEO of ([A-Z][A-Za-z]+)
```

`%s` နေရာတွင် `PERSON` ၏ အကြောင်းအရာ တိုက်ရိုက် ဝင်သွားသည်။ ထို့ကြောင့် person
pattern ကို ပြင်လျှင် rule အားလုံး အလိုအလျောက် အသစ်ဖြစ်သွားသည်။

`PERSON` ကို `(...)` ဖြင့် ခွေထားသည်ကို သတိထားပါ — ထိုခွေက **capturing group** ဖြစ်သည်။
`PERSON` ၏ တန်ဖိုးထဲတွင် ကိုယ်ပိုင် group များ မပါဝင်သောကြောင့် အပြင်ဘက် `(...)` က
group 1 ဖြစ်သည်။

---

## 3. Object Pattern — `([A-Z][A-Za-z]+)`

```python
([A-Z][A-Za-z]+)
```

Object အတွက် pattern သည် လူအမည် pattern ထက် **ပိုခွင့်လွှတ်** သည်။

| အပိုင်း | အဓိပ္ပာယ် |
| --- | --- |
| `[A-Z]` | စာလုံးကြီး တစ်လုံး |
| `[A-Za-z]+` | စာလုံးကြီး သို့မဟုတ် အသေး တစ်လုံး သို့ ထို့ထက် ပို |

`[A-Za-z]` သည် စာလုံးကြီးရော အသေးရော လက်ခံသောကြောင့် `Google`၊ `Microsoft`၊
`AcmeCorp` ကဲ့သို့ စာလုံးကြီးများ ဆက်နေသော အမည်များကို ဖမ်းနိုင်သည်။ Person
pattern သည် စကားလုံးနှစ်လုံး လိုအပ်သော်လည်း object pattern သည် စကားလုံးတစ်လုံးတည်းနှင့်
လုံလောက်သည်။

```python
import re

OBJ = re.compile(r"([A-Z][A-Za-z]+)")

print(OBJ.findall("Google"))
print(OBJ.findall("AcmeCorp"))
print(OBJ.findall("Acme Corp"))
```

Output —

```text
['Google']
['AcmeCorp']
['Acme', 'Corp']
```

နောက်ဆုံးဥပမာတွင် `Acme` နှင့် `Corp` သည် **သီးခြား match နှစ်ခု** ဖြစ်သွားသည်။
Space ပါသော အမည်နှစ်လုံးကို object တစ်ခုတည်းအဖြစ် ဖမ်းလိုလျှင် pattern ကို
ချဲ့ရမည်။ ၎င်းသည် pattern-based extraction ၏ ကန့်သတ်ချက်ဖြစ်သည်။

---

## 4. `.` မပါသော Sentence အဆုံးသတ်

Object pattern တွင် `.` မထည့်ထားသည်ကို သတိထားပါ။ Pattern သည် `Google.` ဟု မဖမ်းဘဲ
`Google` ဟုသာ ဖမ်းသည်။ အကြောင်းရင်းမှာ `[A-Za-z]+` သည် `.` ကို လက်မခံခြင်းကြောင့်ဖြစ်သည်။
ထို့ကြောင့် ရလဒ် triple ထဲတွင် ပိုးတံ (`.`) ပါမလာပါ။

```python
import re

OBJ = re.compile(r"([A-Z][A-Za-z]+)")

print(OBJ.findall("founded Google."))
print(re.findall(r"([A-Z][A-Za-z.]+)", "founded Google."))
```

Output —

```text
['Google']
['Google.']
```

ဒုတိယ pattern တွင် `.` ကို character class ထဲ ထည့်ထားသောကြောင့် ပိုးတံပါ ပါလာသည်။
Graph ထဲတွင် node အမည်များ သန့်ရှင်းနေရန် ပထမပုံစံက ပိုသင့်တော်သည်။

---

## 5. `finditer()` — Match Object များ ရယူခြင်း

```python
for m in pattern.finditer(text):
```

`findall()` နှင့် `finditer()` ၏ ကွာခြားချက်သည် အရေးကြီးသည်။

```python
import re

CEO = re.compile(r"(\b[A-Z][a-z]+ [A-Z][a-z]+\b) is the CEO of ([A-Z][A-Za-z]+)")
text = "Sundar Pichai is the CEO of Google."

print("findall  :", CEO.findall(text))
print("finditer :", [m.group(0) for m in CEO.finditer(text)])
```

Output —

```text
findall  : [('Sundar Pichai', 'Google')]
finditer : ['Sundar Pichai is the CEO of Google']
```

| Method | ပြန်ပေးသည့်အရာ | သုံးရန် သင့်တော်သည့်အခါ |
| --- | --- | --- |
| `findall()` | Group များ၏ တန်ဖိုးများ (tuple သို့ string) | ရလဒ် စာသားသာ လိုသောအခါ |
| `finditer()` | **Match object** တစ်ခုချင်း | Position၊ group နံပါတ်၊ span လိုသောအခါ |

ဤ Exercise တွင် `finditer()` ကို သုံးခြင်းသည် ရည်ရွယ်ချက်ရှိသည် — triple အတွက်
`m.group(1)` နှင့် `m.group(2)` ကို **သီးခြား** ဆွဲထုတ်လိုခြင်းကြောင့်ဖြစ်သည်။ `findall()`
သည်လည်း ဤအလုပ်ကို လုပ်နိုင်သော်လည်း `finditer()` သည် နောက်ပိုင်းတွင် position (`m.start()`)
ပါ ထည့်လိုသောအခါ ပိုပြောင်းလွယ်သည်။

---

## 6. `match.group(n)` နှင့် `groups()`

```python
import re

CEO = re.compile(r"(\b[A-Z][a-z]+ [A-Z][a-z]+\b) is the CEO of ([A-Z][A-Za-z]+)")
text = "Sundar Pichai is the CEO of Google."
m = CEO.search(text)

print("group(0) :", m.group(0))
print("group(1) :", m.group(1))
print("group(2) :", m.group(2))
print("groups() :", m.groups())
```

Output —

```text
group(0) : Sundar Pichai is the CEO of Google
group(1) : Sundar Pichai
group(2) : Google
groups() : ('Sundar Pichai', 'Google')
```

- `group(0)` — ကိုက်ညီသော **စာသားအပြည့်အစုံ**။ Groups များ မပါဝင်ပါ။
- `group(1)` — ပထမဆုံး group (subject)။
- `group(2)` — ဒုတိယ group (object)။
- `groups()` — group အားလုံးကို tuple အဖြစ်။

Group နံပါတ်သည် **ဘယ်ဘက်မှ ညာဘက်သို့** ဖွင့်ထားသော ကွင်းစဉ်အတိုင်း သတ်မှတ်သည်။
ထို့ကြောင့် subject သည် 1၊ object သည် 2 ဖြစ်သည်။

---

## 7. `extract_relations()` — Nested List Comprehension

```python
def extract_relations(text, rules):
    return [(m.group(1), relation, m.group(2))
            for pattern, relation in rules
            for m in pattern.finditer(text)]
```

Function သည် **တစ်လိုင်းတည်း** ပြန်ပေးသော်လည်း အတွင်းတွင် `for` နှစ်ခု ရှိသည်။
၎င်းကို **nested list comprehension** ဟု ခေါ်သည်။

ဤ comprehension ကို ပုံမှန် loop အဖြစ် ချရေးလျှင် —

```python
def extract_relations(text, rules):
    results = []
    for pattern, relation in rules:          # အပြင် loop
        for m in pattern.finditer(text):     # အတွင်း loop
            results.append((m.group(1), relation, m.group(2)))
    return results
```

Nested comprehension တွင် **ပထမ `for` သည် အပြင် loop**၊ **ဒုတိယ `for` သည် အတွင်း loop**
ဖြစ်သည်။ Expression `(m.group(1), relation, m.group(2))` သည် အတွင်း loop ၏
တစ်ကြိမ်စီတွင် တန်ဖိုးတစ်ခု ထုတ်သည်။

Order ကို ရှင်းရှင်းလင်းလင်း ပြပါ —

```python
print([(a, b) for a in [1, 2] for b in ["x", "y"]])
print([(a, b) for b in ["x", "y"] for a in [1, 2]])
```

Output —

```text
[(1, 'x'), (1, 'y'), (2, 'x'), (2, 'y')]
[(1, 'x'), (2, 'x'), (1, 'y'), (2, 'y')]
```

ပထမလိုင်းတွင် `a` သည် အပြင် loop ဖြစ်သောကြောင့် `a` တန်ဖိုးတစ်ခုစီအတွက် `b` အားလုံး
လိုက်သည်။ ဒုတိယလိုင်းတွင် ဆန့်ကျင်ဘက် ဖြစ်သည်။

### ဤ Order သည် ရလဒ်ကို မည်သို့ သက်ရောက်သနည်း။

`rules` သည် အပြင် loop ဖြစ်သောကြောင့် ရလဒ်များသည် **rule အစဉ်လိုက်** ထွက်သည်၊
စာသားထဲမှ တည်နေရာအစဉ်လိုက် မဟုတ်ပါ။

```python
import re

PERSON = r"\b[A-Z][a-z]+ [A-Z][a-z]+\b"
REL_RULES = [
    (re.compile(r"(%s) is the CEO of ([A-Z][A-Za-z]+)" % PERSON), "CEO_OF"),
    (re.compile(r"(%s) founded ([A-Z][A-Za-z]+)" % PERSON), "FOUNDED"),
]


def extract_relations(text, rules):
    return [(m.group(1), relation, m.group(2))
            for pattern, relation in rules
            for m in pattern.finditer(text)]


text = "Larry Page founded Google. Sundar Pichai is the CEO of Google."
for triple in extract_relations(text, REL_RULES):
    print("  (%s, %s, %s)" % triple)
```

Output —

```text
  (Sundar Pichai, CEO_OF, Google)
  (Larry Page, FOUNDED, Google)
```

စာသားထဲတွင် `Larry Page founded Google` သည် **အရင်လာ** သော်လည်း `CEO_OF` rule သည် rule
စာရင်းထဲတွင် အရင်ရှိသောကြောင့် `Sundar Pichai` သည် **အရင်ထွက်** သည်။ ဤအစဉ်ကို ပြောင်းလိုလျှင်
ရလဒ်ကို စာသားထဲမှ တည်နေရာအလိုက် (position အလိုက်) ပြန်စီရမည်။

---

## 8. `%` Formatting ဖြင့် Output

```python
for triple in extract_relations(REL_TEXT, REL_RULES):
    print("  (%s, %s, %s)" % triple)
```

`%` နောက်တွင် **tuple** ကို တိုက်ရိုက် ပေးနိုင်သည်။ Tuple ၏ item တစ်ခုချင်းစီသည်
`%s` တစ်ခုစီတွင် အစဉ်လိုက် ဝင်သည်။

```python
triple = ("Sundar Pichai", "CEO_OF", "Google")
print("  (%s, %s, %s)" % triple)
print("  (%s, %s, %s)" % (triple[0], triple[1], triple[2]))
```

Output —

```text
  (Sundar Pichai, CEO_OF, Google)
  (Sundar Pichai, CEO_OF, Google)
```

နှစ်လိုင်းလုံး တူညီသည်။ ဤအရေးအသားသည် Module 00 ၏ Exercise 2 တွင် သုံးခဲ့သော
`%-5s` padding format နှင့် တူညီသော နည်းလမ်းဖြစ်သည်။

---

## 9. Code တစ်ခုလုံး — Run လုပ်နိုင်သော Version

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
```

Output —

```text
  (Sundar Pichai, CEO_OF, Google)
  (Larry Page, FOUNDED, Google)
```

ဤ triple များကို Module 05–06 ၏ Cypher ဖြင့် graph ထဲ ထည့်သောအခါ —

```cypher
MERGE (s:Entity {id: $subject})
MERGE (o:Entity {id: $object})
MERGE (s)-[:CEO_OF]->(o)
```

ဟု ပြောင်းနိုင်သည်။ Relation label သည် `CEO_OF`၊ `FOUNDED` တို့အတွက် relationship
type ဖြစ်လာသည်။

---

## 10. ကိုယ်တိုင်လေ့ကျင့်ကြည့်ပါ

**မေးခွန်း** — အောက်ပါ text နှင့် rules အတွက် `extract_relations()` သည် triple
မည်မျှ ပြန်ပေးမည်နည်း။

```python
REL_TEXT = "Tim Cook is the CEO of Apple. Steve Jobs founded Apple."
REL_RULES = [
    (re.compile(r"(%s) is the CEO of ([A-Z][A-Za-z]+)" % PERSON), "CEO_OF"),
    (re.compile(r"(%s) founded ([A-Z][A-Za-z]+)" % PERSON), "FOUNDED"),
]
```

1. 1 triple
2. 2 triple — `(Tim Cook, CEO_OF, Apple)` နှင့် `(Steve Jobs, FOUNDED, Apple)`
3. 3 triple
4. 0 triple — `Apple.` တွင် ပိုးတံ ပါသဖြင့် မကိုက်ညီပါ

<details>
<summary>အဖြေ ကြည့်ရန်</summary>

**အဖြေ — 2. 2 triple**

အကြောင်းရင်း — `CEO_OF` rule သည် `Tim Cook is the CEO of Apple` ကို ဖမ်းပြီး
`FOUNDED` rule သည် `Steve Jobs founded Apple` ကို ဖမ်းသည်။ Object pattern
`([A-Z][A-Za-z]+)` တွင် `.` မပါသဖြင့် `Apple.` မှ `Apple` သာ ဖမ်းမိပြီး
ပိုးတံ မပါဝင်ပါ။

ရလဒ်အစဉ်မှာ rule အစဉ်လိုက် ဖြစ်သဖြင့် —

```text
  (Tim Cook, CEO_OF, Apple)
  (Steve Jobs, FOUNDED, Apple)
```

</details>

---

**အဓိက မှတ်ထားရန်** — Pattern-based relation extraction သည် ရှင်းလင်းပြီး
ရလဒ်ကို ခန့်မှန်းရလွယ်သည်။ သို့သော် စာသားအတွင်းရှိ ရေးပုံတိုင်းအတွက် pattern
အသစ် ရေးရသဖြင့် scale မလွယ်ပါ — "is the CEO of"၊ "serves as CEO of"၊
"leads" စသဖြင့် ရေးပုံတိုင်း rule တစ်ခု လိုသည်။ Module 02 တွင် LLM ဖြင့် ဤအလုပ်ကို
pattern မရေးဘဲ လုပ်ပုံကို လေ့လာမည်။
