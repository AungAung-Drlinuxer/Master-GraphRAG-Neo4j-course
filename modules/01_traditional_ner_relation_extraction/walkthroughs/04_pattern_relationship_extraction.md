# Walkthrough 04 — Pattern-based Relationship Extraction (Exercise 4)

> ဤဖိုင်သည် Module 01 ၏ `solution.md` ထဲက Exercise 4 ကို **Python အခြေခံမှ စ၍**
> အပိုင်းလိုက် ရှင်းပြသည့် walkthrough ဖြစ်သည်။

---

## 0. ဤ Exercise က ဘာကို ဖြေရှင်းပေးသလဲ။

Exercise 1–3 မှာ entity တွေကို ရှာထုတ်ခဲ့ပါတယ်။ Graph တစ်ခု တည်ဆောက်ဖို့
entity များ တစ်ခုတည်းနဲ့ မလုံလောက်ပါဘူး — သူတို့အကြားက **relationship** လည်း
လိုပါတယ်။

```text
Sundar Pichai is the CEO of Google. Larry Page founded Google.
```

ဒီစာသားကနေ အောက်ပါ **triples** များ ထုတ်ယူချင်ပါတယ်။

```text
(Sundar Pichai, CEO_OF, Google)
(Larry Page, FOUNDED, Google)
```

Triple တစ်ခုစီမှာ **subject**၊ **relation** နဲ့ **object** ပါပါတယ်။ ဒီဖိုင်မှာ
relationship တွေကို **regex pattern** နဲ့ ထုတ်ယူပုံကို လေ့လာပါမယ်။

ဒီ code မှာ လေ့လာရမယ့် Python concepts တွေကတော့ —

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

Exercise 1 မှာ `re.compile()` လုပ်ထားတဲ့ pattern object တစ်ခုကို သိမ်းခဲ့ပါတယ်။
ဒီ Exercise မှာတော့ **စာသား (string)** အဖြစ်သာ သိမ်းထားပါတယ်။ အကြောင်းရင်းက
ဒီ pattern ကို pattern **အသစ်များထဲ ထည့်ဖို့** လိုလို့ပါတယ်။

`re.compile()` လုပ်ထားတဲ့ object ကို `%s` နဲ့ ထည့်ရင် အလုပ်လုပ်ပါတယ်၊ ဒါပေမဲ့
ဒီအဆင့်မှာ ရည်ရွယ်တဲ့အလုပ်က စာသားအဆင့်မှာ ဆက်စပ်တာဖြစ်လို့ string အဖြစ်ထားတာ
ပိုရှင်းပါတယ်။

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

ဒါက **list of tuples** ဖြစ်ပါတယ်။ Tuple တစ်ခုစီမှာ —

- ပထမ item — compile လုပ်ထားတဲ့ regex pattern
- ဒုတိယ item — အဲဒီ pattern က ကိုယ်စားပြုတဲ့ relation label

| Pattern (အတိုချုပ်) | Relation |
| --- | --- |
| `<PERSON> is the CEO of <ORG>` | `CEO_OF` |
| `<PERSON> founded <ORG>` | `FOUNDED` |

Rule တစ်ခုချင်းစီက ဖော်ပြပုံကို ကြည့်ပါ။

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

`%s` နေရာမှာ `PERSON` ၏ အကြောင်းအရာ တိုက်ရိုက် ဝင်သွားပါတယ်။ ဒါကြောင့် person
pattern ကို ပြင်ရင် rule အားလုံး က အလိုအလျောက် အသစ်ဖြစ်သွားပါတယ်။

`PERSON` ကို `(...)` နဲ့ ခွေထားတာကို သတိထားပါ — အဲဒီခွေက **capturing group** ဖြစ်ပါတယ်။
`PERSON` ၏ တန်ဖိုးထဲမှာ ကိုယ်ပိုင် group တွေ မပါဝင်လို့ အပြင်ဘက် `(...)` က
group 1 ဖြစ်ပါတယ်။

---

## 3. Object Pattern — `([A-Z][A-Za-z]+)`

```python
([A-Z][A-Za-z]+)
```

Object အတွက် pattern က လူအမည် pattern ထက် **ပိုခွင့်လွှတ်** ပါတယ်။

| အပိုင်း | အဓိပ္ပာယ် |
| --- | --- |
| `[A-Z]` | စာလုံးကြီး တစ်လုံး |
| `[A-Za-z]+` | စာလုံးကြီး သို့မဟုတ် အသေး တစ်လုံး သို့ ထို့ထက် ပို |

`[A-Za-z]` က စာလုံးကြီးရော အသေးရော လက်ခံတဲ့အတွက် `Google`၊ `Microsoft`၊
`AcmeCorp` လို့ စာလုံးကြီးတွေ ဆက်နေတဲ့ အမည်များကို ဖမ်းနိုင်ပါတယ်။ Person
pattern က စကားလုံးနှစ်လုံး လိုအပ်ပေမဲ့ object pattern က စကားလုံးတစ်လုံးတည်းနဲ့
လုံလောက်ပါတယ်။

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

နောက်ဆုံးဥပမာမှာ `Acme` နဲ့ `Corp` က **သီးခြား match နှစ်ခု** ဖြစ်သွားပါတယ်။
Space ပါတဲ့ အမည်နှစ်လုံးကို object တစ်ခုတည်းအဖြစ် ဖမ်းချင်ရင် pattern ကို
ချဲ့ရပါမယ်။ ဒါက pattern-based extraction ၏ ကန့်သတ်ချက်ပါ။

---

## 4. `.` မပါတဲ့ Sentence အဆုံးသတ်

Object pattern မှာ `.` မထည့်ထားတာကို သတိထားပါ။ Pattern က `Google.` လို့ မဖမ်းဘဲ
`Google` လို့သာ ဖမ်းပါတယ်။ အကြောင်းရင်းက `[A-Za-z]+` က `.` ကို လက်မခံလို့ပါ။
ဒါကြောင့် ရလဒ် triple ထဲမှာ ပိုးတံ (`.`) ပါမလာပါဘူး။

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

ဒုတိယ pattern မှာ `.` ကို character class ထဲ ထည့်ထားတဲ့အတွက် ပိုးတံပါ ပါလာပါတယ်။
Graph ထဲမှာ node အမည်တွေ သန့်ရှင်းနေဖို့ ပထမပုံစံက ပိုသင့်တော်ပါတယ်။

---

## 5. `finditer()` — Match Object များ ရယူခြင်း

```python
for m in pattern.finditer(text):
```

`findall()` နဲ့ `finditer()` ၏ ကွာခြားချက်က အရေးကြီးပါတယ်။

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

| Method | ပြန်ပေးတာ | သုံးရန် သင့်တော်တာ |
| --- | --- | --- |
| `findall()` | Group တွေ၏ တန်ဖိုးများ (tuple သို့ string) | ရလဒ် စာသားသာ လိုတဲ့အခါ |
| `finditer()` | **Match object** တစ်ခုချင်း | Position၊ group နံပါတ်၊ span လိုတဲ့အခါ |

ဒီ Exercise မှာ `finditer()` ကို သုံးတာက ရည်ရွယ်ချက်ရှိပါတယ် — triple အတွက်
`m.group(1)` နဲ့ `m.group(2)` ကို **သီးခြား** ဆွဲထုတ်လိုလို့ပါတယ်။ `findall()`
ကလည်း ဒီအလုပ်ကို လုပ်နိုင်ပေမဲ့ `finditer()` က နောက်ပိုင်းမှာ position (`m.start()`)
ပါ ထည့်ချင်တဲ့အခါ ပိုပြောင်းလွယ်ပါတယ်။

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

- `group(0)` — ကိုက်ညီတဲ့ **စာသားအပြည့်အစုံ**။ Groups တွေ မပါဝင်ပါ။
- `group(1)` — ပထမဆုံး group (subject)။
- `group(2)` — ဒုတိယ group (object)။
- `groups()` — group အားလုံးကို tuple အဖြစ်။

Group နံပါတ်က **ဘယ်ဘက်မှ ညာဘက်သို့** ဖွင့်ထားတဲ့ ကွင်းစဉ်အတိုင်း သတ်မှတ်ပါတယ်။
ဒါကြောင့် subject က 1၊ object က 2 ဖြစ်ပါတယ်။

---

## 7. `extract_relations()` — Nested List Comprehension

```python
def extract_relations(text, rules):
    return [(m.group(1), relation, m.group(2))
            for pattern, relation in rules
            for m in pattern.finditer(text)]
```

Function က **တစ်လိုင်းတည်း** ပြန်ပေးပေမဲ့ အတွင်းမှာ `for` နှစ်ခု ရှိပါတယ်။
ဒါကို **nested list comprehension** လို့ ခေါ်ပါတယ်။

ဒီ comprehension ကို ပုံမှန် loop အဖြစ် ချရေးရင် —

```python
def extract_relations(text, rules):
    results = []
    for pattern, relation in rules:          # အပြင် loop
        for m in pattern.finditer(text):     # အတွင်း loop
            results.append((m.group(1), relation, m.group(2)))
    return results
```

Nested comprehension မှာ **ပထမ `for` က အပြင် loop**၊ **ဒုတိယ `for` က အတွင်း loop**
ဖြစ်ပါတယ်။ Expression `(m.group(1), relation, m.group(2))` က အတွင်း loop ၏
တစ်ကြိမ်စီတွင် တန်ဖိုးတစ်ခု ထုတ်ပါတယ်။

Order ကို ရှင်းရှင်းလင်းလင်း ပြရအောင် —

```python
print([(a, b) for a in [1, 2] for b in ["x", "y"]])
print([(a, b) for b in ["x", "y"] for a in [1, 2]])
```

Output —

```text
[(1, 'x'), (1, 'y'), (2, 'x'), (2, 'y')]
[(1, 'x'), (2, 'x'), (1, 'y'), (2, 'y')]
```

ပထမလိုင်းမှာ `a` က အပြင် loop ဖြစ်တဲ့အတွက် `a` တန်ဖိုးတစ်ခုစီအတွက် `b` အားလုံး
လိုက်ပါတယ်။ ဒုတိယလိုင်းမှာ ဆန့်ကျင်ဘက် ဖြစ်ပါတယ်။

### ဒီ Order က ရလဒ်ကို ဘယ်လို သက်ရောက်သလဲ။

`rules` က အပြင် loop ဖြစ်တဲ့အတွက် ရလဒ်တွေက **rule အစဉ်လိုက်** ထွက်ပါတယ်၊
စာသားထဲက တည်နေရာအစဉ်လိုက် မဟုတ်ပါဘူး။

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

စာသားထဲမှာ `Larry Page founded Google` က **အရင်လာ** ပေမဲ့ `CEO_OF` rule က rule
စာရင်းထဲမှာ အရင်ရှိလို့ `Sundar Pichai` က **အရင်ထွက်** ပါတယ်။ ဒီအစဉ်ကို ပြောင်းချင်ရင်
ရလဒ်ကို စာသားထဲက တည်နေရာအလိုက် (position အလိုက်) ပြန်စီရပါမယ်။

---

## 8. `%` Formatting ဖြင့် Output

```python
for triple in extract_relations(REL_TEXT, REL_RULES):
    print("  (%s, %s, %s)" % triple)
```

`%` နောက်မှာ **tuple** ကို တိုက်ရိုက် ပေးနိုင်ပါတယ်။ Tuple ၏ item တစ်ခုချင်းစီက
`%s` တစ်ခုစီမှာ အစဉ်လိုက် ဝင်ပါတယ်။

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

နှစ်လိုင်းလုံး တူညီပါတယ်။ ဒီအရေးအသားက Module 00 ၏ Exercise 2 မှာ သုံးခဲ့တဲ့
`%-5s` padding format နဲ့ တူညီတဲ့ နည်းလမ်းပါ။

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

ဒီ triple များကို Module 05–06 ၏ Cypher ဖြင့် graph ထဲ ထည့်တဲ့အခါ —

```cypher
MERGE (s:Entity {id: $subject})
MERGE (o:Entity {id: $object})
MERGE (s)-[:CEO_OF]->(o)
```

လို့ ပြောင်းနိုင်ပါတယ်။ Relation label က `CEO_OF`၊ `FOUNDED` တို့အတွက် relationship
type ဖြစ်လာပါတယ်။

---

## 10. ကိုယ်တိုင်လေ့ကျင့်ကြည့်ပါ

**မေးခွန်း** — အောက်ပါ text နှင့် rules အတွက် `extract_relations()` က triple
မည်မျှ ပြန်ပေးမလဲ။

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
