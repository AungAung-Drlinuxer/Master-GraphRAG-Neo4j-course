# Walkthrough 03 — Cypher statement validation (Exercise 3)

> ဤဖိုင်သည် Module 05 ၏ `solution.md` ထဲက Exercise 3 ကို **Python အခြေခံမှ စ၍**
> အပိုင်းလိုက် ရှင်းပြသည့် walkthrough ဖြစ်သည်။ `re.finditer()`၊ `m.group()`၊
> `m.start()`၊ `str.count()`၊ generator နှင့် `any()`၊ `in` operator စသည့်
> Python concept များကို ဤနေရာတွင် ရှင်းပြသည်။

---

## 0. ဤ Exercise က ဘာကို ဖြေရှင်းပေးသလဲ။

Text-to-Cypher လို pipeline တွင် statement များကို LLM မှ generate လုပ်သည်။ မည်သည့်
statement ကို server သို့ မပို့မီ **ကြိုတင် စစ်ဆေးခြင်း** (validation) လိုသည်။
ဤ Exercise က static validator တစ်ခု တည်ဆောက်သည် — server မလိုဘဲ syntax အခြေခံ
အန္တရာယ်များကို ရှာသည်။

```text
statement ဖတ်
     |
     +-- bracket ( ) [ ] ညီ/မညီ?
     +-- clause အစီအစဉ် မှန်?
     +-- identity value literal ဖြစ်နေသလား?   (injection အန္တရာယ်)
     +-- parameter ($) ပါသလား?
     |
     v
violation list  (ဥပမာ ['literal_identity_value', 'missing_parameter'])
```

စစ်ဆေးချက် ၄ ခု ရှိသည်။ ဤ code မှာ လေ့ရှာရမည့် Python concepts —
`re.compile()` နှင့် alternation အစီအစဉ်၊ `re.finditer()`၊ `m.group(1)`၊ `m.start()`၊
`" ".join(...split())` whitespace normalization၊ `str.count()`၊ rank dict၊
generator expression နှင့် `any()`၊ list `.append()`၊ `in` operator ။

---

## 1. `_CLAUSE_RE` — clause keyword များကို ဖမ်းသည့် regex

Cypher clause များကို regex ဖြင့် ရှာသည်။ `\b` က word boundary ဖြစ်သည်။

```python
import re

_CLAUSE_RE = re.compile(
    r"\b(OPTIONAL\s+MATCH|DETACH\s+DELETE|MATCH|WHERE|WITH|CREATE|MERGE|SET"
    r"|DELETE|REMOVE|ORDER\s+BY|SKIP|LIMIT|UNWIND|RETURN)\b"
)
```

Regex မှာ `|` ၏ precedence အလွန်နိမ့်သဖြင့် အစီအစဉ် အရေးကြီးသည်။ `OPTIONAL\s+MATCH`
ကို `MATCH` အရင်၊ `DETACH\s+DELETE` ကို `DELETE` အရင် ထားရသည်။ Regex engine က
alternation ကို **ဘယ်မှ ညာ** စမ်းသပ်သဖြင့် ရှည်သော keyword ကို အရင်ထားမှ တူညီသော
span ကို မှန်ကန်စွာ ဖမ်းသည်။

```python
import re

_CLAUSE_RE = re.compile(
    r"\b(OPTIONAL\s+MATCH|DETACH\s+DELETE|MATCH|WHERE|WITH|CREATE|MERGE|SET"
    r"|DELETE|REMOVE|ORDER\s+BY|SKIP|LIMIT|UNWIND|RETURN)\b"
)

for s in ["OPTIONAL MATCH (a)-[:R]->(b) RETURN a",
          "MATCH (n) DETACH DELETE n",
          "MATCH (n) RETURN n"]:
    print(s)
    print("  matches:", [m.group(1) for m in _CLAUSE_RE.finditer(s)])
```

Output —

```text
OPTIONAL MATCH (a)-[:R]->(b) RETURN a
  matches: ['OPTIONAL MATCH', 'RETURN']
MATCH (n) DETACH DELETE n
  matches: ['MATCH', 'DETACH DELETE']
MATCH (n) RETURN n
  matches: ['MATCH', 'RETURN']
```

`OPTIONAL MATCH` ကို **တစ်ခုတည်း** အဖြစ် ဖမ်းသည် (`OPTIONAL` နှင့် `MATCH` ခွဲမဖမ်း)။
`DETACH DELETE` လည်း ထို့အတူဖြစ်သည်။ `\s+` က space တစ်ခု သို့မဟုတ် ထို့ထက် ပို ကို
ကိုက်ညီစေသဖြင့် space များစွာ ခြားထားလည်း ဖမ်းသည်။

Alternation အစီအစဉ်ကို ပြောင်းကြည့်ရင် ဘာဖြစ်မလဲ — `MATCH` ကို `OPTIONAL\s+MATCH`
အရင် ထားလျှင် `OPTIONAL MATCH` ထဲက `MATCH` ကို အရင် ကိုက်ညီပြီး `OPTIONAL` သည်
မကိုက်ညီဘဲ ကျန်ခဲ့မည်။ ဤအကြောင်းရင်းဖြင့် ရှည်သော alternative များကို အရင်ထားသည်။

---

## 2. `clause_sequence()` — (token, position) စာရင်း

`re.finditer()` က pattern ကိုက်ညီသည့် အပိုင်းအားလုံးကို iterator အဖြစ် ပြန်သည်။
`m.group(1)` က capture group ရလဒ်၊ `m.start()` က အနေအထား (index) ဖြစ်သည်။

```python
import re

_CLAUSE_RE = re.compile(
    r"\b(OPTIONAL\s+MATCH|DETACH\s+DELETE|MATCH|WHERE|WITH|CREATE|MERGE|SET"
    r"|DELETE|REMOVE|ORDER\s+BY|SKIP|LIMIT|UNWIND|RETURN)\b"
)


def clause_sequence(statement):
    return [(" ".join(m.group(1).split()), m.start())
            for m in _CLAUSE_RE.finditer(statement)]


stmt = "MATCH (n) WHERE n.id = $id RETURN n"
print(clause_sequence(stmt))

s2 = "OPTIONAL   MATCH (a) RETURN a"
m = _CLAUSE_RE.search(s2)
print("raw span    :", repr(m.group(1)))
print("normalized  :", repr(" ".join(m.group(1).split())))
print("sequence    :", clause_sequence(s2))
```

Output —

```text
[('MATCH', 0), ('WHERE', 10), ('RETURN', 27)]
raw span    : 'OPTIONAL   MATCH'
normalized  : 'OPTIONAL MATCH'
sequence    : [('OPTIONAL MATCH', 0), ('RETURN', 21)]
```

### `" ".join(m.group(1).split())` — whitespace ကို တစ်ပြေးညီ စေခြင်း

`m` တွင် space များစွာ ပါလာနိုင်သည် — `'OPTIONAL   MATCH'` လိုပုံစံ။ `_CLAUSE_RANK`
dict ၏ key မှာ `"OPTIONAL MATCH"` (space တစ်ခု) ဖြစ်သဖြင့် တိုက်ရိုက် ရှာလျှင်
`KeyError` ဖြစ်မည်။

`m.group(1).split()` က space အားလုံးကို ဖျောက်ပြီး `['OPTIONAL', 'MATCH']` ပေးသည်။
`" ".join(...)` က ပြန်ပေါင်းပြီး `'OPTIONAL MATCH'` ဖြစ်စေသည်။ ဤ normalization သည်
`OPTIONAL   MATCH` နှင့် `OPTIONAL\nMATCH` နှစ်မျိုးလုံးကို dict key တစ်ခုတည်းသို့
ရောက်စေသည်။

`m.start()` က တိုက်ရိုက် span အစနေရာကို ပြန်သည် — `s2` တွင် `OPTIONAL MATCH` သည်
index 0၊ `RETURN` သည် index 21 တွင် စသည်။ Position ကို ထိန်းထားခြင်းဖြင့် နောက်ပိုင်း
error message တွင် နေရာ ညွှန်နိုင်သည်။

---

## 3. Bracket balance — `str.count()`

`str.count(sub)` က `sub` ပေါ်သည့် အရေအတွက်ကို ပြန်သည်။ ဖွင့်ခြင်း/ပိတ်ခြင်း
အရေအတွက် မတူလျှင် statement သည် syntax အရ ပျက်သည်။

```python
for stmt in ["MATCH (a:Person {id: $id}) RETURN a",
             "MATCH (a:Person {id: $id} RETURN a",
             "MERGE (n:E {id: $id}) ON EACH [n.a RETURN n",
             "MERGE (n:E {id: $id}) ON EACH [n.a] RETURN n"]:
    print("%-44s ( =%d ) =%d  [ =%d ] =%d"
          % (stmt, stmt.count("("), stmt.count(")"),
             stmt.count("["), stmt.count("]")))
```

Output —

```text
MATCH (a:Person {id: $id}) RETURN a          ( =1 ) =1  [ =0 ] =0
MATCH (a:Person {id: $id} RETURN a           ( =1 ) =0  [ =0 ] =0
MERGE (n:E {id: $id}) ON EACH [n.a RETURN n  ( =1 ) =1  [ =1 ] =0
MERGE (n:E {id: $id}) ON EACH [n.a] RETURN n ( =1 ) =1  [ =1 ] =1
```

လိုင်း ၂ တွင် `(` ၁ ခု၊ `)` ၀ ခု — မညီ။ လိုင်း ၃ တွင် `[` ၁ ခု၊ `]` ၀ ခု — မညီ။
လိုင်း ၁ နှင့် ၄ တွင် ညီသည်။ `count()` သည် bracket အစီအစဉ် မှန်/မမှန် (ဥပမာ `)(`) ကို
မစစ်ပါ — အရေအတွက် ညီ/မညီကိုသာ စစ်သည်။ ဤ validator သည် **static** ဖြစ်သဖြင့်
syntax အပြည့်အစုံကို မစစ်ပါ (server-side `EXPLAIN` က ထိုအလုပ်ကို လုပ်သည်)။

---

## 4. Clause order — rank dict နှင့် `any()`

Cypher clause များတွင် တိကျသော အစီအစဉ် ရှိသည် (`MATCH` → `WHERE` → `SET` → `RETURN`)။
Clause တိုင်းကို rank နံပါတ်ဖြင့် ကိုယ်စားပြုပြီး နံပါတ်များ တက်နေရမည်။

```python
import re

_CLAUSE_RE = re.compile(
    r"\b(OPTIONAL\s+MATCH|DETACH\s+DELETE|MATCH|WHERE|WITH|CREATE|MERGE|SET"
    r"|DELETE|REMOVE|ORDER\s+BY|SKIP|LIMIT|UNWIND|RETURN)\b"
)
_CLAUSE_RANK = {
    "UNWIND": 0, "OPTIONAL MATCH": 1, "MATCH": 1, "WHERE": 2, "WITH": 3,
    "CREATE": 4, "MERGE": 4, "SET": 5, "REMOVE": 5, "DETACH DELETE": 6,
    "DELETE": 6, "RETURN": 7, "ORDER BY": 8, "SKIP": 9, "LIMIT": 10,
}


def clause_sequence(statement):
    return [(" ".join(m.group(1).split()), m.start())
            for m in _CLAUSE_RE.finditer(statement)]


for stmt in ["MATCH (n) WHERE n.id = $id RETURN n",
             "RETURN n MATCH (n:Person {id: $id})",
             "MATCH (n) RETURN n"]:
    ranks = [_CLAUSE_RANK[tok] for tok, _ in clause_sequence(stmt)]
    print("%-44s ranks=%-12s out_of_order=%s"
          % (stmt, ranks, any(ranks[i] > ranks[i + 1] for i in range(len(ranks) - 1))))
print("empty ranks :", any(ranks[i] > ranks[i + 1] for i in range(-1)))
```

Output —

```text
MATCH (n) WHERE n.id = $id RETURN n          ranks=[1, 2, 7]    out_of_order=False
RETURN n MATCH (n:Person {id: $id})          ranks=[7, 1]       out_of_order=True
MATCH (n) RETURN n                           ranks=[1, 7]       out_of_order=False
empty ranks : False
```

### `any(...)` နှင့် generator expression

```python
any(ranks[i] > ranks[i + 1] for i in range(len(ranks) - 1))
```

`range(len(ranks) - 1)` က နောက်တစ်ခုနှင့် နှိုင်းယှဉ်နိုင်သော index များပေးသည် —
`ranks` length ၂ အတွက် `range(1)` → `i = 0` တစ်ခုတည်း။ `ranks[i] > ranks[i + 1]` က
"နောက်တစ်ခုထက် ကြီးနေသလား" ကို စစ်သည်။ `any()` က တစ်ခုခု `True` ဖြစ်သည်နှင့်
`True` ပြန်သည်။

`[7, 1]` တွင် `7 > 1` ဖြစ်သဖြင့် `illegal_clause_order` ဖြစ်သည်။ `[1, 7]` တွင်
`1 > 7` မဖြစ်သဖြင့် `False` ဖြစ်သည်။ `any()` ကော `range(-1)` ဖြစ်သည့်အခါ (element
၁ ခုသာ ရှိလျှင်) `range(-1)` က အလွတ်ဖြစ်ပြီး `any([])` သည် `False` ဖြစ်သည် —
error မဖြစ်ပါ။

---

## 5. `_LITERAL_ID_RE` — literal identity value ရှာခြင်း

Identity property (`id`) ကို literal (`'p1'`၊ `"p1"`၊ `42`) ဖြင့် ရေးထားခြင်းသည်
parameterized မဟုတ်သဖြင့် အန္တရာယ်ရှိသည်။ `_LITERAL_ID_RE` က ထို pattern ကို ရှာသည်။

```python
import re

_LITERAL_ID_RE = re.compile(r"\{\s*id\s*:\s*(?:'[^']*'|\"[^\"]*\"|\d+)")

for stmt in ["MERGE (n:Person {id: 'p1'})", 'MERGE (n:Person {id: "p1"})',
             "MERGE (n:Person {id: 42})", "MERGE (n:Person {id: $id})",
             "MERGE (n:Person { id: 'p1' })"]:
    m = _LITERAL_ID_RE.search(stmt)
    print("%-32s -> %s" % (stmt, m.group(0) if m else None))
```

Output —

```text
MERGE (n:Person {id: 'p1'})      -> {id: 'p1'
MERGE (n:Person {id: "p1"})      -> {id: "p1"
MERGE (n:Person {id: 42})        -> {id: 42
MERGE (n:Person {id: $id})       -> None
MERGE (n:Person { id: 'p1' })    -> { id: 'p1'
```

Regex ကို အပိုင်းလိုက် ဖတ်ကြည့်ရအောင်။

| အပိုင်း | အဓိပ္ပာယ် |
| --- | --- |
| `\{` | `{` — literal အကွက်အဖွင့် |
| `\s*id\s*` | `id` — ရှေ့/နောက် space ရှိလည်း ရ |
| `:\s*` | colon နှင့် space |
| `(?:'[^']*'` | single quote အတွင်း စာသား |
| `\|"[^"]*"` | double quote အတွင်း စာသား |
| `\|\d+)` | သို့မဟုတ် ဂဏန်း |

`{ id: 'p1' }` လို space များစွာ ပါလည်း `\s*` ကြောင့် ဖမ်းသည်။ `{id: $id}` က
`None` ဖြစ်သည် — parameter reference ကို regex က မကိုက်ညီပါ။ `(?:...)` က
non-capturing group ဖြစ်သည် — `m.group(0)` က တစ်ခုတည်းသော group ဖြစ်သည်။

`\d+` က `{id: 42}` ကို ဖမ်းသည်ကို သတိထားပါ — ဂဏန်း literal လည်း ဖမ်းသည်။
ဤ validator သည် identifier ကို quote လုပ်ခြင်းနှင့် ဂဏန်း literal နှစ်မျိုးလုံးကို
parameterized မဟုတ်သော အန္တရာယ်အဖြစ် တူညီစွာ သတ်မှတ်သည်။

---

## 6. Parameter ပါ/မပါ — `in` operator

`"$" not in statement` က statement ထဲ parameter reference ရှိမရှိ စစ်သည်။

```python
for stmt in ["MATCH (n:Person {id: $id}) RETURN n",
             "MATCH (n:Person) RETURN n"]:
    print("%-38s '$' present=%-6s missing_parameter=%s"
          % (stmt, "$" in stmt, "$" not in stmt))
```

Output —

```text
MATCH (n:Person {id: $id}) RETURN n    '$' present=True   missing_parameter=False
MATCH (n:Person) RETURN n              '$' present=False  missing_parameter=True
```

`"$" in stmt` သည် substring ရှိမရှိ စစ်သည် — `True`/`False` ပြန်သည်။ `not in` က
ဆန့်ကျင်ဘက် ဖြစ်သည်။ ဤစစ်ဆေးချက်သည် `$` တစ်လုံး ရှိရုံနှင့် ပြည့်မီသည် — parameter
အရေအတွက် မှန်/မမှန် (query တွင် `$name` ရှိသော်လည်း `params` တွင် `name` မပါခြင်း)
ကို မစစ်ပါ။ ထို mismatch ကို server က runtime တွင် စစ်သည်။

---

## 7. `validate_cypher()` — စစ်ဆေးချက် ၄ ခု ပေါင်းစည်းခြင်း

Section 3–6 ၏ စစ်ဆေးချက်များကို ပေါင်းပြီး violation list ပြန်သည်။

```python
import re

_CLAUSE_RE = re.compile(
    r"\b(OPTIONAL\s+MATCH|DETACH\s+DELETE|MATCH|WHERE|WITH|CREATE|MERGE|SET"
    r"|DELETE|REMOVE|ORDER\s+BY|SKIP|LIMIT|UNWIND|RETURN)\b"
)
_CLAUSE_RANK = {
    "UNWIND": 0, "OPTIONAL MATCH": 1, "MATCH": 1, "WHERE": 2, "WITH": 3,
    "CREATE": 4, "MERGE": 4, "SET": 5, "REMOVE": 5, "DETACH DELETE": 6,
    "DELETE": 6, "RETURN": 7, "ORDER BY": 8, "SKIP": 9, "LIMIT": 10,
}
_LITERAL_ID_RE = re.compile(r"\{\s*id\s*:\s*(?:'[^']*'|\"[^\"]*\"|\d+)")


def clause_sequence(statement):
    return [(" ".join(m.group(1).split()), m.start())
            for m in _CLAUSE_RE.finditer(statement)]


def validate_cypher(statement):
    violations = []
    if statement.count("(") != statement.count(")"):
        violations.append("unbalanced_parentheses")
    if statement.count("[") != statement.count("]"):
        violations.append("unbalanced_brackets")
    ranks = [_CLAUSE_RANK[tok] for tok, _ in clause_sequence(statement)]
    if any(ranks[i] > ranks[i + 1] for i in range(len(ranks) - 1)):
        violations.append("illegal_clause_order")
    if _LITERAL_ID_RE.search(statement):
        violations.append("literal_identity_value")
    if "$" not in statement:
        violations.append("missing_parameter")
    return violations


cases = [
    "MATCH (a:Person {id: $id})-[:KNOWS]->(b:Person) RETURN b.name AS name",
    "MERGE (n:Person {id: $id}) SET n.name = $name RETURN n",
    "MATCH (a:Person {id: $id} RETURN a",
    "RETURN n MATCH (n:Person {id: $id})",
    "MERGE (n:Person {id: 'p1'}) RETURN n",
]
for stmt in cases:
    print("statement :", stmt)
    print("clauses   :", [tok for tok, _ in clause_sequence(stmt)])
    print("violations:", validate_cypher(stmt))
    print("-")
```

Output —

```text
statement : MATCH (a:Person {id: $id})-[:KNOWS]->(b:Person) RETURN b.name AS name
clauses   : ['MATCH', 'RETURN']
violations: []
-
statement : MERGE (n:Person {id: $id}) SET n.name = $name RETURN n
clauses   : ['MERGE', 'SET', 'RETURN']
violations: []
-
statement : MATCH (a:Person {id: $id} RETURN a
clauses   : ['MATCH', 'RETURN']
violations: ['unbalanced_parentheses']
-
statement : RETURN n MATCH (n:Person {id: $id})
clauses   : ['RETURN', 'MATCH']
violations: ['illegal_clause_order']
-
statement : MERGE (n:Person {id: 'p1'}) RETURN n
clauses   : ['MERGE', 'RETURN']
violations: ['literal_identity_value', 'missing_parameter']
-
```

Violation list ကို အစဉ်လိုက် စစ်သည်ကို သတိထားပါ — `violations` list ထဲက အစီအစဉ်သည်
`if` အစီအစဉ်အတိုင်း ဖြစ်သည် (parentheses၊ brackets၊ order၊ literal၊ parameter)။
အောက်ဆုံး case တွင် violation နှစ်ခု ပေါ်သည် — `{id: 'p1'}` သည် literal
ဖြစ်သည်၊ ပြီးနောက် statement ထဲ `$` မပါသဖြင့် `missing_parameter` လည်း ဖြစ်သည်။
ဤနှစ်ခုသည် တွဲဖက် ပေါ်တတ်သည် — literal id ကို သုံးလျှင် parameter လည်း
မလိုတော့သဖြင့် ဖြစ်သည်။

---

## 8. Case များကို ဇယားဖြင့် ပြန်ကြည့်ခြင်း

အထက်ပါ run မှ တိုက်ရိုက် ကူးချထားသော ဇယား —

| # | Statement | clauses | ranks | violations |
| --- | --- | --- | --- | --- |
| 1 | `MATCH ... RETURN ...` | MATCH, RETURN | [1, 7] | `[]` |
| 2 | `MERGE ... SET ... RETURN ...` | MERGE, SET, RETURN | [4, 5, 7] | `[]` |
| 3 | `MATCH (a:Person {id: $id} RETURN a` | MATCH, RETURN | [1, 7] | `['unbalanced_parentheses']` |
| 4 | `RETURN n MATCH (n:Person {id: $id})` | RETURN, MATCH | [7, 1] | `['illegal_clause_order']` |
| 5 | `MERGE (n:Person {id: 'p1'}) RETURN n` | MERGE, RETURN | [4, 7] | `['literal_identity_value', 'missing_parameter']` |

Case ၃ တွင် clause အစီအစဉ် မှန်ပေမဲ့ bracket မညီသဖြင့် ဖမ်းမိသည်။ Case ၄ တွင်
bracket ညီပေမဲ့ clause အစီအစဉ် မှားသဖြင့် ဖမ်းမိသည်။ စစ်ဆေးချက် နှစ်ခုသည်
သီးခြားစီ အလုပ်လုပ်သည် — တစ်ခုက ကျန်တစ်ခုကို မဖုံးလွှမ်းပါ။

---

## 9. Code တစ်ခုလုံး — Run လုပ်နိုင်သော Version

```python
import re

_CLAUSE_RE = re.compile(
    r"\b(OPTIONAL\s+MATCH|DETACH\s+DELETE|MATCH|WHERE|WITH|CREATE|MERGE|SET"
    r"|DELETE|REMOVE|ORDER\s+BY|SKIP|LIMIT|UNWIND|RETURN)\b"
)
_CLAUSE_RANK = {
    "UNWIND": 0, "OPTIONAL MATCH": 1, "MATCH": 1, "WHERE": 2, "WITH": 3,
    "CREATE": 4, "MERGE": 4, "SET": 5, "REMOVE": 5, "DETACH DELETE": 6,
    "DELETE": 6, "RETURN": 7, "ORDER BY": 8, "SKIP": 9, "LIMIT": 10,
}
_LITERAL_ID_RE = re.compile(r"\{\s*id\s*:\s*(?:'[^']*'|\"[^\"]*\"|\d+)")


def clause_sequence(statement):
    return [(" ".join(m.group(1).split()), m.start())
            for m in _CLAUSE_RE.finditer(statement)]


def validate_cypher(statement):
    violations = []
    if statement.count("(") != statement.count(")"):
        violations.append("unbalanced_parentheses")
    if statement.count("[") != statement.count("]"):
        violations.append("unbalanced_brackets")
    ranks = [_CLAUSE_RANK[tok] for tok, _ in clause_sequence(statement)]
    if any(ranks[i] > ranks[i + 1] for i in range(len(ranks) - 1)):
        violations.append("illegal_clause_order")
    if _LITERAL_ID_RE.search(statement):
        violations.append("literal_identity_value")
    if "$" not in statement:
        violations.append("missing_parameter")
    return violations


cases = [
    "MATCH (a:Person {id: $id})-[:KNOWS]->(b:Person) RETURN b.name AS name",
    "MERGE (n:Person {id: $id}) SET n.name = $name RETURN n",
    "MATCH (a:Person {id: $id} RETURN a",
    "RETURN n MATCH (n:Person {id: $id})",
    "MERGE (n:Person {id: 'p1'}) RETURN n",
]
for stmt in cases:
    print("statement :", stmt)
    print("clauses   :", [tok for tok, _ in clause_sequence(stmt)])
    print("violations:", validate_cypher(stmt))
    print("-")
```

Output —

```text
statement : MATCH (a:Person {id: $id})-[:KNOWS]->(b:Person) RETURN b.name AS name
clauses   : ['MATCH', 'RETURN']
violations: []
-
statement : MERGE (n:Person {id: $id}) SET n.name = $name RETURN n
clauses   : ['MERGE', 'SET', 'RETURN']
violations: []
-
statement : MATCH (a:Person {id: $id} RETURN a
clauses   : ['MATCH', 'RETURN']
violations: ['unbalanced_parentheses']
-
statement : RETURN n MATCH (n:Person {id: $id})
clauses   : ['RETURN', 'MATCH']
violations: ['illegal_clause_order']
-
statement : MERGE (n:Person {id: 'p1'}) RETURN n
clauses   : ['MERGE', 'RETURN']
violations: ['literal_identity_value', 'missing_parameter']
-
```

---

## 10. ကိုယ်တိုင်လေ့ကျင့်ကြည့်ပါ

**မေးခွန်း** — အောက်ပါ code က ဘယ်စာရင်းကို ပြန်မလဲ။

```python
import re

_CLAUSE_RE = re.compile(
    r"\b(OPTIONAL\s+MATCH|DETACH\s+DELETE|MATCH|WHERE|WITH|CREATE|MERGE|SET"
    r"|DELETE|REMOVE|ORDER\s+BY|SKIP|LIMIT|UNWIND|RETURN)\b"
)

s = "MATCH (n) DETACH DELETE n"
print([m.group(1) for m in _CLAUSE_RE.finditer(s)])
```

1. `['MATCH', 'DETACH', 'DELETE']`
2. `['MATCH', 'DETACH DELETE']`
3. `['MATCH', 'DELETE']`
4. `['DETACH DELETE']`

<details>
<summary>အဖြေ ကြည့်ရန်</summary>

**အဖြေ — 2. `['MATCH', 'DETACH DELETE']`**

အကြောင်းရင်း — alternation တွင် `DETACH\s+DELETE` ကို `DELETE` အရင် ထားသည်။
Regex engine က ဘယ်မှ ညာ စမ်းသပ်သဖြင့် `DETACH DELETE` ကို **တစ်ခုတည်း** ဖမ်းသည်။
`MATCH` သည် ရှေ့ဆုံး ပေါ်သဖြင့် ပထမဆုံး ဖမ်းခံရသည်။ `DETACH` ကို သီးခြား
မဖမ်းပါ — `_CLAUSE_RE` ၏ alternative ထဲ `DETACH` တစ်ခုတည်း မပါပါ။
ဤ code ကို run ၍ အတည်ပြုပြီးဖြစ်သည်။

</details>

---

**အဓိက မှတ်ထားရန်** — Static validator သည် server သို့ မပို့မီ အန္တရာယ်ကို ရှာသည် —
bracket balance၊ clause order၊ literal identity၊ parameter usage ၄ ခု ဖြစ်သည်။
Regex ဖြင့် clause ဖမ်းသည့်အခါ alternation အစီအစဉ် (ရှည်သော keyword အရင်) သည်
အရေးကြီးပြီး `" ".join(...split())` normalization က whitespace ကြောင့် `KeyError`
မဖြစ်စေရန် လိုသည်။ ဤ validator သည် syntax အပြည့်အစုံကို မစစ်ပါ — server-side
`EXPLAIN` ဖြင့် ထပ်တွဲရမည်။ Exercise 4 တွင် `MERGE` ကို အမြန်စေသည့်
constraint/index DDL များကို လေ့လာမည်။
