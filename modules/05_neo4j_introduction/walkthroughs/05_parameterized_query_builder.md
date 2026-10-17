# Walkthrough 05 — Parameterized query builder နှင့် injection defense (Exercise 5)

> ဤဖိုင်သည် Module 05 ၏ `solution.md` ထဲက Exercise 5 ကို **Python အခြေခံမှ စ၍**
> အပိုင်းလိုက် ရှင်းပြသည့် walkthrough ဖြစ်သည်။ tuple return၊ `dict()` copy၊
> `str.upper()`၊ substring `in`၊ regex `match()` နှင့် `bool()`၊ list comprehension
> စသည့် Python concept များကို ဤနေရာတွင် ရှင်းပြသည်။

---

## 0. ဤ Exercise က ဘာကို ဖြေရှင်းပေးသလဲ။

Exercise 2 တွင် value ကို `params` dict ထဲ ထားခဲ့သည်။ ဤ Exercise က **ဘာကြောင့်**
ထိုသို့ လုပ်ရသည်ကို တိုက်ရိုက် ပြသည် — value ကို query text ထဲ ထည့်လျှင် injection
ဖြစ်နိုင်သည်။

```text
parameterized :  query = "MERGE (n:Person {id: $id}) SET n.name = $name RETURN n"
                 params = {"name": "Robert'); MATCH (n) DETACH DELETE n;//"}
                        |  value သည် query text နှင့် လုံးဝ မထိတွေ့
                        v  payload ထဲက ' ; keyword များသည် DATA အဖြစ်သာ ကျန်

naive         :  query = "MERGE (n:Person {id: 'p1'}) SET n.name = 'Robert');
                         MATCH (n) DETACH DELETE n;//' RETURN n"
                        |  payload က query syntax အဖြစ် ရောက်သွား
                        v  literal ကျိုး၊ ; က statement အသစ် စ
```

ဤ code မှာ လေ့လာရမည့် Python concepts — function tuple return၊ `dict(params)` copy၊
`str.upper()`၊ list comprehension၊ substring `in`၊ `re.compile()` ၏ `^...$` anchor၊
`re.match()` နှင့် `bool()`၊ `str.count()` ။

---

## 1. `build_parameterized_query()` — text နှင့် value ကို ခွဲထားခြင်း

Function သည် template ကို **အတိအကျ** ပြန်ပြီး params ကို copy လုပ်သည်။

```python
import re

_INJECTION_MARKERS = (";", "--", "/*", "*/", "DETACH DELETE", "DROP ", "LOAD CSV")
_LABEL_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")


def detect_injection(query_text):
    upper = query_text.upper()
    return [m for m in _INJECTION_MARKERS if m.upper() in upper]


def validate_identifier(name):
    return bool(_LABEL_RE.match(name))


def build_parameterized_query(template, params):
    return template, dict(params)


template = "MERGE (n:Person {id: $id}) SET n.name = $name RETURN n"
source = {"id": "p1", "name": "Aung Aung"}
query, params = build_parameterized_query(template, source)
print("query  :", query)
print("params :", params)
print("query is template      :", query is template)
print("params is source       :", params is source)
source["name"] = "MUTATED"
print("after source mutation  :", params["name"])
```

Output —

```text
query  : MERGE (n:Person {id: $id}) SET n.name = $name RETURN n
params : {'id': 'p1', 'name': 'Aung Aung'}
query is template      : True
params is source       : False
after source mutation  : Aung Aung
```

`return template, dict(params)` သည် **tuple** ပြန်သည်။ `query, params = ...` ဖြင့်
tuple unpacking လုပ်သည်။

- `query is template` → `True` — string သည် immutable ဖြစ်သဖြင့် copy လုပ်စရာ မလိုပါ။
  ထို့ကြောင့် query text သည် template အတိအကျ ဖြစ်သည်ကို identity ဖြင့်ပင် အတည်ပြုနိုင်သည်။
- `params is source` → `False` — `dict(params)` သည် dict အသစ် ဖန်တီးသည်။ နောက်ပိုင်း
  `source` ကို ပြင်လိုက်သော်လည်း `params` မပြောင်းသည်ကို တွေ့ရသည်။

Copy လုပ်ခြင်း၏ အကျိုးသည် — caller သည် ပြင်ဆင်ပြီးသော query အတွက် parameter များကို
နောက်ပိုင်း မတော်တဆ မပြောင်းနိုင်စေရန် ဖြစ်သည်။

---

## 2. `detect_injection()` — marker ရှာခြင်း

Statement smuggling ကို ညွှန်ပြသော marker များကို ရှာသည်။

```python
_INJECTION_MARKERS = (";", "--", "/*", "*/", "DETACH DELETE", "DROP ", "LOAD CSV")


def detect_injection(query_text):
    upper = query_text.upper()
    return [m for m in _INJECTION_MARKERS if m.upper() in upper]


for q in ["MATCH (n) RETURN n",
          "MERGE (n) DETACH DELETE n",
          "match (n) detach delete n",
          "DROP TABLE x",
          "LOAD CSV FROM 'file:///x'",
          "MERGE (n:Person {id: $id}) SET n.name = $name RETURN n"]:
    print("%-52s -> %s" % (q, detect_injection(q)))
```

Output —

```text
MATCH (n) RETURN n                                   -> []
MERGE (n) DETACH DELETE n                            -> ['DETACH DELETE']
match (n) detach delete n                            -> ['DETACH DELETE']
DROP TABLE x                                         -> ['DROP ']
LOAD CSV FROM 'file:///x'                            -> ['LOAD CSV']
MERGE (n:Person {id: $id}) SET n.name = $name RETURN n -> []
```

`upper = query_text.upper()` က query တစ်ခုလုံးကို အကြီးပြောင်းသည်။ ပြီးနောက် marker
တိုင်းကိုလည်း `m.upper()` ဖြင့် နှိုင်းယှဉ်သည်။ ဒါကြောင့် `match (n) detach delete n`
(အသေး) သည်လည်း `'DETACH DELETE'` ကို မိသည် — case-insensitive ဖြစ်သည်။

`"DROP "` တွင် နောက်ဆုံး space ပါသည်ကို သတိထားပါ — `DROP` သက်သက် မဟုတ်။
ဤ space သည် `DROPDOWN` လို စာလုံးထဲက `DROP` ကို မမိစေရန် ကာကွယ်သည်။ Marker
စာရင်းတွင် `MATCH`/`MERGE`/`SET` များ **မပါ** — legitimate template များတွင် ထို
keyword များ ပါဝင်သဖြင့် marker အဖြစ် သတ်မှတ်လျှင် false positive ဖြစ်မည်။
နောက်ဆုံး query (legitimate) သည် `[]` ပြန်သည်။

`detect_injection()` သည် ရိုးရှင်းသော **heuristic** ဖြစ်သည် — mutation ကို မလုပ်ပါ၊
သတိပေးရန် ညွှန်ပြရုံ ဖြစ်သည်။ Parameterization ကိုယ်တိုင်က အဓိက ကာကွယ်မှု ဖြစ်သည်။

---

## 3. `validate_identifier()` — Label/Relationship type whitelist

Neo4j 5 တွင် Label နှင့် relationship type ကို parameterize လုပ်မရပါ။ ထို့ကြောင့်
ထို identifier များကို whitelist regex ဖြင့် စစ်ရသည်။

```python
import re

_INJECTION_MARKERS = (";", "--", "/*", "*/", "DETACH DELETE", "DROP ", "LOAD CSV")
_LABEL_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")


def detect_injection(query_text):
    upper = query_text.upper()
    return [m for m in _INJECTION_MARKERS if m.upper() in upper]


def validate_identifier(name):
    return bool(_LABEL_RE.match(name))


def build_parameterized_query(template, params):
    return template, dict(params)


for name in ["Person", "person", "_x", "Person`) DETACH DELETE (n", "1Person", "Person Name", ""]:
    print("%-30r -> %s" % (name, validate_identifier(name)))
print("match('Person x') is", bool(_LABEL_RE.match("Person x")))
```

Output —

```text
'Person'                       -> True
'person'                       -> True
'_x'                           -> True
'Person`) DETACH DELETE (n'    -> False
'1Person'                      -> False
'Person Name'                  -> False
''                             -> False
match('Person x') is False
```

`_LABEL_RE = r"^[A-Za-z_][A-Za-z0-9_]*$"` ကို အပိုင်းလိုက် ဖတ်ကြည့်ရအောင်။

| အပိုင်း | အဓိပ္ပာယ် |
| --- | --- |
| `^` | စာသားအစ |
| `[A-Za-z_]` | စာလုံး သို့မဟုတ် underscore — ပထမစာလုံး |
| `[A-Za-z0-9_]*` | စာလုံး/ဂဏန်း/underscore — ကျန်တာအားလုံး |
| `$` | စာသားအဆုံး |

ဤ pattern သည် စာသားတစ်ခုလုံးကို ဖုံးရမည်။ `CypherMadness` လို စာလုံးများ ဖြတ်သွားနိုင်ပါက
`DETACH DELETE` ကဲ့သို့ payload များ ဝင်နိုင်သည်။ `bool(...)` က `re.match()` ၏
ရလဒ် (match object သို့ `None`) ကို `True`/`False` အဖြစ် ပြောင်းသည် — function ၏
return type ကို တည်ငြိမ်စေသည်။

`'Person`) DETACH DELETE (n'` သည် `False` ဖြစ်သည် — space နှင့် bracket ပါသဖြင့်
pattern နှင့် မကိုက်ညီပါ။ `'1Person'` လည်း `False` — ဂဏန်းဖြင့် မ​စနိုင်ပါ။ `''` လည်း
`False` — empty string က `[A-Za-z_]` ကို မဖြည့်နိုင်ပါ။

> `^...$` ပါသဖြင့် `_LABEL_RE.match("Person x")` သည်လည်း `False` ပြန်သည်။ `match()`
> သည် ပထမဆုံးမှ စစ်သော်လည်း `$` anchor က အဆုံးထိ ဖုံးရန် တောင်းသဖြင့် trailing
> junk ပါလျှင် မကိုက်ညီပါ။

---

## 4. Parameterized နှင့် naive — တိုက်ရိုက် နှိုင်းယှဉ်ခြင်း

တူညီသော payload ကို နည်းလမ်းနှစ်မျိုးဖြင့် ထည့်ကြည့်သည်။

```python
import re

_INJECTION_MARKERS = (";", "--", "/*", "*/", "DETACH DELETE", "DROP ", "LOAD CSV")
_LABEL_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")


def detect_injection(query_text):
    upper = query_text.upper()
    return [m for m in _INJECTION_MARKERS if m.upper() in upper]


def validate_identifier(name):
    return bool(_LABEL_RE.match(name))


def build_parameterized_query(template, params):
    return template, dict(params)


template = "MERGE (n:Person {id: $id}) SET n.name = $name RETURN n"
payload = "Robert'); MATCH (n) DETACH DELETE n;//"
query, params = build_parameterized_query(template, {"id": "p1", "name": payload})
print("parameterized query :", query)
print("params['name']      :", repr(params["name"]))
print("payload not in query:", payload not in query)
print("markers in query    :", detect_injection(query))
print("---")
naive = "MERGE (n:Person {id: 'p1'}) SET n.name = '" + payload + "' RETURN n"
print("naive query         :", naive)
print("markers in naive    :", detect_injection(naive))
print("round-trip equal    :", params["name"] == payload)
```

Output —

```text
parameterized query : MERGE (n:Person {id: $id}) SET n.name = $name RETURN n
params['name']      : "Robert'); MATCH (n) DETACH DELETE n;//"
payload not in query: True
markers in query    : []
---
naive query         : MERGE (n:Person {id: 'p1'}) SET n.name = 'Robert'); MATCH (n) DETACH DELETE n;//' RETURN n
markers in naive    : [';', 'DETACH DELETE']
round-trip equal    : True
```

Parameterized query text —

```cypher
MERGE (n:Person {id: $id}) SET n.name = $name RETURN n
```

Payload သည် query text ထဲ **လုံးဝ မပါ** (`payload not in query` → `True`)၊ marker
လည်း `[]` ဖြစ်သည်။ Value သည် `params["name"]` တွင် မူရင်းအတိုင်း ရှိပြီး round-trip
တူညီသည် (`True`)။

Naive query text —

```cypher
MERGE (n:Person {id: 'p1'}) SET n.name = 'Robert'); MATCH (n) DETACH DELETE n;//' RETURN n
```

Payload က query syntax ထဲ ရောက်သွားသဖြင့် `;` နှင့် `DETACH DELETE` ပေါ်လာသည်။
Neo4j ၏ parameter သည် query ၏ syntax tree အပြင်ဘက်တွင် value ကို သယ်ဆောင်သဖြင့်
payload ထဲက စာလုံးတိုင်းသည် **data** အဖြစ်သာ ကျန်သည်။ ဤအကြောင်းရင်းဖြင့်
parameterization ကို **နည်းလမ်းမှန်ကန်** (correct defense) အဖြစ် သတ်မှတ်ပြီး marker
scan ကို အပိုစစ်ဆေးမှု အဖြစ်သာ ထားသည်။

---

## 5. Naive string ကျိုးသွားခြင်း — quote နှင့် `$`

Marker မပေါ်သည့် payload များလည်း literal ကို ကျိုးစေနိုင်သည်။

```python
payload = "Robert'); MATCH (n) DETACH DELETE n;//"
naive = "MERGE (n:Person {id: 'p1'}) SET n.name = '" + payload + "' RETURN n"
print("quote count :", naive.count("'"))
print("balanced?   :", naive.count("'") % 2 == 0)
print("---")
value = "O'Brien"
naive2 = "MATCH (n:Person) WHERE n.name = '" + value + "' RETURN n"
print("naive2      :", naive2)
print("quote count :", naive2.count("'"))
print("balanced?   :", naive2.count("'") % 2 == 0)
print("---")
dollar = "$id) DETACH DELETE (n"
naive3 = "MATCH (n:Person {id: $id}) SET n.name = '" + dollar + "' RETURN n"
print("naive3      :", naive3)
print("$ tokens    :", [w for w in naive3.split() if w.startswith("$")])
print("---")
no_marker = "Robert' MATCH (n) RETURN n"
built = "SET n.name = '" + no_marker + "'"
markers = [m for m in (";", "--", "/*", "*/", "DETACH DELETE", "DROP ", "LOAD CSV")
           if m.upper() in built.upper()]
print("no-marker payload markers :", markers)
print("built       :", built)
print("quote count :", built.count("'"))
print("balanced?   :", built.count("'") % 2 == 0)
```

Output —

```text
quote count : 5
balanced?   : False
---
naive2      : MATCH (n:Person) WHERE n.name = 'O'Brien' RETURN n
quote count : 3
balanced?   : False
---
naive3      : MATCH (n:Person {id: $id}) SET n.name = '$id) DETACH DELETE (n' RETURN n
$ tokens    : ['$id})']
---
no-marker payload markers : []
built       : SET n.name = 'Robert' MATCH (n) RETURN n'
quote count : 3
balanced?   : False
```

### Quote

Normal literal တစ်ခုတွင် quote သည် ဖွင့်/ပိတ် စုံဖြစ်ရမည်။ ဤ payload ပါလျှင် quote ၅ လုံး
(odd) ဖြစ်သွားသည် — payload ထဲက `'` တစ်လုံးက literal တစ်ခုကို အလယ်တွင်
ပိတ်လိုက်သဖြင့် ဖြစ်သည်။ `O'Brien` ကဲ့သို့ အမည်တွင်လည်း `'` ပါလျှင် quote ၃ လုံး
(odd) ဖြစ်သည် — literal တစ်ခုကို အလယ်တွင် ပိတ်လိုက်သည်။

```cypher
MATCH (n:Person) WHERE n.name = 'O'Brien' RETURN n
```

Neo4j သည် `'O'` ဟု literal ကို ပိတ်ပြီး `Brien'` ကို ဆက်ဖတ်မည် — syntax error ဖြစ်မည်။

### `$`

`$id) DETACH DELETE (n` လို value ကို ထည့်လျှင် text ထဲ `$` အသစ် ပေါ်လာသည်။ Parameter
သည် `$` နှင့် စသော စာလုံးဖြစ်သဖြင့် naively ထည့်လိုက်သော value ထဲက `$...` သည်
parameter reference တစ်ခုအဖြစ် **ဖတ်ခံနိုင်** သည်။ ဤ case တွင် driver သို့မဟုတ် server သည်
မပေးထားသော parameter ကို ရှာတတ်သည် ("Expected parameter(s)" error)။ ဤအကြောင်းရင်းဖြင့်
value ကို text ထဲ လုံးဝ မထည့်ရန် စည်းမျဉ်း လိုသည်။

### Marker scan ၏ ကန့်သတ်ချက်

နောက်ဆုံး case က အရေးကြီးသည် — `Robert' MATCH (n) RETURN n` ဟူသော payload သည်
marker (`;`၊ `DETACH DELETE` စသည်) တစ်ခုမှ မပါသဖြင့် `detect_injection()` က `[]`
ပြန်သည်။ သို့သော် build လုပ်လိုက်သော text တွင် quote ၃ လုံး (odd) ဖြစ်ပြီး literal
ကျိုးနေသည်။

```cypher
SET n.name = 'Robert' MATCH (n) RETURN n'
```

ဤအချက်က **marker scan သည် ကာကွယ်မှု မဟုတ်** ကြောင်း ပြသည် — marker မပါသော
quote-break ကို မမိပါ။ တစ်ခုတည်းသော ယုံကြည်စိတ်ချရသော ကာကွယ်မှုမှာ
**parameterization** ဖြစ်သည် — value သည် query text ထဲ လုံးဝ မဝင်သဖြင့် quote လည်း
မလို၊ escape လည်း မလိုပါ။ Marker scan ကို audit/log တွင် အပိုအလွှာအဖြစ်သာ ထားရသည်။

---

## 6. Marker နှင့် နည်းလမ်းနှစ်မျိုး — နှိုင်းယှဉ်ဇယား

| Query | ဖွဲ့စည်းပုံ | `detect_injection()` | payload ပါသလား | ကာကွယ်မှု |
| --- | --- | --- | --- | --- |
| parameterized | template + `params` | `[]` | မပါ | လုံးဝ ကာကွယ် |
| naive (payload) | value ကို interpolate | `[';', 'DETACH DELETE']` | ပါ | မကာကွယ် |
| naive (`O'Brien`) | value ကို interpolate | `[]` | ပါ | မကာကွယ် — marker မမိ |
| naive (`no_marker`) | value ကို interpolate | `[]` | ပါ | မကာကွယ် — marker မမိ |

ဇယားက ရှင်းရှင်းလင်းလင်း ပြသည် — naive လမ်းကြောင်းသုံးခုထဲက **နှစ်ခုတွင်**
`detect_injection()` က `[]` ပြန်သည်။ ဆိုလိုသည်မှာ marker scan တစ်ခုတည်းဖြင့်
အန္တရာယ်ကို မဖမ်းနိုင်ပါ။

---

## 7. Code တစ်ခုလုံး — Run လုပ်နိုင်သော Version

```python
import re

_INJECTION_MARKERS = (";", "--", "/*", "*/", "DETACH DELETE", "DROP ", "LOAD CSV")
_LABEL_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")


def detect_injection(query_text):
    upper = query_text.upper()
    return [m for m in _INJECTION_MARKERS if m.upper() in upper]


def validate_identifier(name):
    return bool(_LABEL_RE.match(name))


def build_parameterized_query(template, params):
    return template, dict(params)


template = "MERGE (n:Person {id: $id}) SET n.name = $name RETURN n"
payload = "Robert'); MATCH (n) DETACH DELETE n;//"
query, params = build_parameterized_query(template, {"id": "p1", "name": payload})
naive = "MERGE (n:Person {id: 'p1'}) SET n.name = '" + payload + "' RETURN n"
print("parameterized query :", query)
print("markers in query    :", detect_injection(query))
print("naive query         :", naive)
print("markers in naive    :", detect_injection(naive))
print("label whitelist     :", validate_identifier("Person"), validate_identifier("Person`) DETACH DELETE (n"))
```

Output —

```text
parameterized query : MERGE (n:Person {id: $id}) SET n.name = $name RETURN n
markers in query    : []
naive query         : MERGE (n:Person {id: 'p1'}) SET n.name = 'Robert'); MATCH (n) DETACH DELETE n;//' RETURN n
markers in naive    : [';', 'DETACH DELETE']
label whitelist     : True False
```

Security အချက် — parameterization သည် **authorization ကို အစားထိုးမပေးပါ**။
read-only role၊ tenant filter နှင့် destructive clause block များကို သီးခြား ထည့်ရမည်။
Text-to-Cypher တွင် LLM က generate လုပ်သော statement များအတွက် Exercise 3 ၏ static
validator နှင့် `DETACH DELETE` ကဲ့သို့ clause များကို ပိတ်ခြင်းကို တွဲသုံးရသည်။

---

## 8. ကိုယ်တိုင်လေ့ကျင့်ကြည့်ပါ

**မေးခွန်း** — အောက်ပါ code က ဘယ်ရလဒ် ပြန်မလဲ။

```python
import re

_INJECTION_MARKERS = (";", "--", "/*", "*/", "DETACH DELETE", "DROP ", "LOAD CSV")


def detect_injection(query_text):
    upper = query_text.upper()
    return [m for m in _INJECTION_MARKERS if m.upper() in upper]


payload = "O'Brien"
reason = "MATCH (n:Person) WHERE n.name = '" + payload + "'"
print(detect_injection(reason), reason.count("'"))
```

1. `[] 5`
2. `[] 3`
3. `[';'] 3`
4. `[] 4`

<details>
<summary>အဖြေ ကြည့်ရန်</summary>

**အဖြေ — 2. `[] 3`**

အကြောင်းရင်း — `reason` သည် `MATCH (n:Person) WHERE n.name = 'O'Brien'` ဖြစ်သည်။
Marker စာရင်းထဲက တစ်ခုမှ မပါသဖြင့် `detect_injection()` က `[]` ပြန်သည်။
Quote သည် — WHERE literal အဖွင့် ၁၊ payload ၏ `'` ၁၊ literal အပိတ် ၁ — စုစုပေါင်း
**၃** ဖြစ်သည် (odd)။ ဆိုလိုသည်မှာ marker scan က ဤ payload ကို မမိသော်လည်း literal
သည် ကျိုးနေသည် — `parameterization` သာ ကာကွယ်မှု ဖြစ်သည်။ ဤ code ကို run ၍
အတည်ပြုပြီးဖြစ်သည်။

</details>

---

**အဓိက မှတ်ထားရန်** — Parameterized query builder သည် query text နှင့် value ကို
**သီးခြားစီ** ထားသည်။ Value သည် syntax tree အပြင်ဘက်တွင် သယ်ဆောင်ခံရသဖြင့် payload
ထဲက quote၊ `;`၊ `$` နှင့် keyword များသည် data အဖြစ်သာ ကျန်သည်။ `detect_injection()`
ကဲ့သို့ marker scan သည် အပိုအလွှာသာဖြစ်ပြီး marker မပါသော quote-break ကို မမိနိုင်ပါ —
ထို့ကြောင့် ကာကွယ်မှုအဖြစ် မမှီခိုရ။ Label/type ကို parameterize မလုပ်နိုင်သဖြင့်
whitelist regex (`^[A-Za-z_][A-Za-z0-9_]*$`) ဖြင့် စစ်ရသည်။ Exercise 6 တွင် index-free
adjacency traversal ကို လေ့လာမည်။
