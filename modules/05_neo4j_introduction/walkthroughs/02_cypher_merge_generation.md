# Walkthrough 02 — Cypher `MERGE` generation (Exercise 2)

> ဤဖိုင်သည် Module 05 ၏ `solution.md` ထဲက Exercise 2 ကို **Python အခြေခံမှ စ၍**
> အပိုင်းလိုက် ရှင်းပြသည့် walkthrough ဖြစ်သည်။ `sorted()`၊ list comprehension၊
> `str.join()`၊ dict `update()` စသည့် Python concept များကို ဤနေရာတွင် ရှင်းပြသည်။

---

## 0. ဤ Exercise က ဘာကို ဖြေရှင်းပေးသလဲ။

Exercise 1 တွင် graph ကို Python object များဖြင့် ကိုယ်စားပြုခဲ့သည်။ သို့သော် Neo4j
ထဲသို့ ထည့်ရန် **Cypher statement** လိုသည်။ ၎င်းကို text အဖြစ် ဖန်တီးရမည်။
ဤ Exercise က node တစ်ခုနှင့် relationship တစ်ခုကို `MERGE` statement အဖြစ် ပြောင်းသည်။

```text
Node("p1", ("Person",), {name:"Aung Aung", age:34})
        |
        v  cypher_merge_node()
MERGE (n:Person {id: $id})           <-- query text
SET n.age = $age, n.name = $name
RETURN n
        +  params = {"id": "p1", "name": "Aung Aung", "age": 34}
```

ဤနေရာတွင် အခြေခံ အချက်နှစ်ချက် ရှိသည်။

1. Statement ကို **deterministic** ဖြစ်ရမည် — run တိုင်း စာလုံးအစီအစဉ် တူရမည်။
2. Value များကို query text ထဲ **မထည့်ရ** — parameter dict တွင်သာ ထားရမည်။

Function တိုင်းသည် `(cypher_string, params_dict)` **tuple** ပြန်သည်။ ဤ code မှာ
လေ့လာရမည့် Python concepts — `sorted()`၊ list comprehension၊ `str.join()`၊
`str.splitlines()`၊ `dict.update()`၊ tuple return၊ `if sets:` truthiness ။

---

## 1. `sorted()` — property အစီအစဉ်ကို တည်ငြိမ်စေခြင်း

Python dict သည် **insertion order** ကို ထိန်းသည်။ `{"name": ..., "age": ...}` နှင့်
`{"age": ..., "name": ...}` သည် key အစီအစဉ် ကွာသည်။ `sorted()` ဖြင့် key များကို
စီလိုက်လျှင် အစီအစဉ် ကွာခြင်းကို ဖယ်ရှားသည်။

```python
props = {"name": "Aung Aung", "age": 34}
print("insertion order :", list(props))
print("sorted order    :", sorted(props))
print("keys differ?    :", list(props) != sorted(props))

odd = {"zzz": 1, "aaa": 2, "mmm": 3}
print("odd insertion   :", list(odd))
print("odd sorted      :", sorted(odd))
```

Output —

```text
insertion order : ['name', 'age']
sorted order    : ['age', 'name']
keys differ?    : True
odd insertion   : ['zzz', 'aaa', 'mmm']
odd sorted      : ['aaa', 'mmm', 'zzz']
```

`sorted()` သည် dict ကို ထည့်လျှင် **key များ**ကို စီထားသော list ပြန်သည်။ `props` တွင်
insertion order နှင့် sorted order ကွာသည်ကို တွေ့ရသည်။ `odd` တွင်လည်း `zzz` က
အရင်ရေးထားသော်လည်း `sorted` က `aaa` ကို အရင်ပေးသည်။

`sorted()` မသုံးလျှင် graph တည်ဆောက်သည့် အစီအစဉ်ပေါ် မူတည်ပြီး `SET` line က
`n.name = $name, n.age = $age` လည်း ဖြစ်နိုင်၊ `n.age = $age, n.name = $name` လည်း
ဖြစ်နိုင်သည်။ Statement နှစ်ခုလုံး semantic အရ တူပေမဲ့ diff/audit/golden test
များတွင် ကွာခြင်းသည် ပြဿနာ ဖြစ်သည်။ `sorted()` ဤကွာခြင်းကို ဖယ်ရှားသည်။

---

## 2. List comprehension — `SET` assignment များ ဖန်တီးခြင်း

Property တိုင်းအတွက် `n.age = $age` ပုံစံ assignment လိုသည်။ List comprehension
ဖြင့် တစ်လိုင်းတည်း ဖန်တီးသည်။

```python
props = {"name": "Aung Aung", "age": 34}
sets = ["n." + k + " = $" + k for k in sorted(props)]
print(sets)
print(", ".join(sets))

loop_style = []
for k in sorted(props):
    loop_style.append("n." + k + " = $" + k)
print("loop equals comprehension :", loop_style == sets)
```

Output —

```text
['n.age = $age', 'n.name = $name']
n.age = $age, n.name = $name
loop equals comprehension : True
```

`"n." + k + " = $" + k` က property key `k` ကို နေရာနှစ်ခုတွင် ထည့်သည်။ ရှေ့က `n.` က
node variable အမည် ဖြစ်ပြီး နောက်က `$` က parameter reference ဖြစ်သည်။ ဥပမာ `age` အတွက်
`n.age = $age` ရသည်။

**Value ကို ဤနေရာတွင် လုံးဝ မထည့်သည်** ကို သတိထားပါ။ `$age` သည် နေရာကိုင်သာ
(placeholder) ဖြစ်သည်။ တန်ဖိုး `34` သည် `params` dict ထဲသာ ရောက်မည် (Section 4)။
ဤခွဲခြားမှုသည် injection ကာကွယ်ခြင်း၏ အခြေခံ ဖြစ်သည် (Exercise 5 တွင် ထပ်လေ့လာမည်)။

---

## 3. `lines` နှင့် `"\n".join()` — statement အစီအစဉ် တည်ဆောက်ခြင်း

Statement သည် လိုင်းများစွာ ပါသည်။ `lines` list ထဲ အစဉ်လိုက် ထည့်ပြီး `"\n".join()`
ဖြင့် ပေါင်းသည်။ `if sets:` သည် list အလွတ်/မဟုတ် ကို စစ်သည် — empty list က
`False` ဖြစ်သည်။

```python
lines = ["MERGE (n:Person {id: $id})"]
sets = ["n.age = $age", "n.name = $name"]
if sets:
    lines.append("SET " + ", ".join(sets))
lines.append("RETURN n")
print(lines)
print(len(lines))
print("---")
print("\n".join(lines))
```

Output —

```text
['MERGE (n:Person {id: $id})', 'SET n.age = $age, n.name = $name', 'RETURN n']
3
---
MERGE (n:Person {id: $id})
SET n.age = $age, n.name = $name
RETURN n
```

`lines` သည် string ၃ ခုပါသော list ဖြစ်သည်။ `print(lines)` က list repr ကို ပြပြီး
`"\n".join(lines)` က newline ဖြင့် ဆက်ထားသော string ကို ပြသည်။ `append()` က
list ၏ အဆုံးတွင် ထည့်သည် — ဒါကြောင့် အစီအစဉ်သည် ကုဒ်အစီအစဉ်အတိုင်း အာမခံဖြစ်သည်။

`if sets:` တွင် property မရှိလျှင် `sets` က `[]` ဖြစ်ပြီး `SET` line ကို လွှတ်သွားမည်
(Section 7 တွင် တွေ့မည်)။

---

## 4. `params` — value ကို သီးခြားစီ ထိန်းခြင်း

`params` dict ကို identity (`id`) ဖြင့် စပြီး `update()` ဖြင့် property များ ထပ်ဖြည့်သည်။

```python
props = {"name": "Aung Aung", "age": 34}
params = {"id": "p1"}
params.update(props)
print(params)
print("id plus props :", params == {"id": "p1", "name": "Aung Aung", "age": 34})

props["name"] = "MUTATED"
print("after props mutation :", params["name"])
print("same object as props? :", params is props)
```

Output —

```text
{'id': 'p1', 'name': 'Aung Aung', 'age': 34}
id plus props : True
after props mutation : Aung Aung
same object as props? : False
```

`params.update(props)` သည် `props` ၏ key/value များကို `params` ထဲ **copy** လုပ်သည်။
နောက်ပိုင်း `props` ကို ပြင်လိုက်သော်လည်း `params` မပြောင်းသည်ကို output တွင်
တွေ့ရသည်။ `params` သည် `props` နှင့် တူညီသော object မဟုတ်ပါ (`is` → `False`)။

ဤ copy သည် အရေးကြီးသည် — ဖန်တီးပြီးသော statement အတွက် parameter များသည်
နောက်ပိုင်း graph mutation ကြောင့် မတော်တဆ မပြောင်းရပါ။

---

## 5. `cypher_merge_node()` — node statement ဖန်တီးခြင်း

Section 1–4 ၏ အချက်များကို ပေါင်းစည်းလိုက်သော function ဖြစ်သည်။

```python
from dataclasses import dataclass, field
from typing import Dict, Tuple


@dataclass
class Node:
    id: str
    labels: Tuple[str, ...]
    properties: Dict[str, object] = field(default_factory=dict)


@dataclass
class Relationship:
    type: str
    start: str
    end: str
    properties: Dict[str, object] = field(default_factory=dict)


def cypher_merge_node(node):
    lines = ["MERGE (n:" + node.labels[0] + " {id: $id})"]
    sets = ["n." + k + " = $" + k for k in sorted(node.properties)]
    if sets:
        lines.append("SET " + ", ".join(sets))
    lines.append("RETURN n")
    params = {"id": node.id}
    params.update(node.properties)
    return "\n".join(lines), params


node = Node("p1", ("Person",), {"name": "Aung Aung", "age": 34})
stmt, params = cypher_merge_node(node)
print(stmt)
print("---")
print("first line :", repr(stmt.splitlines()[0]))
print("lines      :", len(stmt.splitlines()))
print("params     :", params)
print("has quote  :", "'" in stmt)
```

Output —

```text
MERGE (n:Person {id: $id})
SET n.age = $age, n.name = $name
RETURN n
---
first line : 'MERGE (n:Person {id: $id})'
lines      : 3
params     : {'id': 'p1', 'name': 'Aung Aung', 'age': 34}
has quote  : False
```

Function က ပြန်လိုက်သော statement သည် —

```cypher
MERGE (n:Person {id: $id})
SET n.age = $age, n.name = $name
RETURN n
```

`node.labels[0]` က label ပထမတစ်ခုကို ယူသည် (`("Person",)` မှ `Person`)။ `MERGE` ကို
**identity property `id`** ပေါ်တွင်သာ လုပ်သည် — property များကို `SET` ဖြင့် သီးခြားစီ
update လုပ်သည်။ `MERGE` pattern ကို ကျဉ်းထားခြင်းသည် match လုပ်ရာ လွယ်စေပြီး
`id` index ကို အသုံးပြုစေသည်။

`stmt.splitlines()` က `\n` ဖြင့် ခွဲပြီး list ပြန်သည် — `\n`.join ၏ ပြောင်းပြန် ဖြစ်သည်။
`"'" in stmt` က `False` ဖြစ်သည် — statement ထဲ quote တစ်လုံးမှ မပါ။ Value များသည်
`params` ထဲ ရှိသဖြင့် quote လိုအပ်မှု မရှိပါ။

---

## 6. `cypher_merge_relationship()` — relationship statement ဖန်တီးခြင်း

Relationship သည် endpoint node နှစ်ခုကို `MATCH` နှစ်ခုဖြင့် ဆွဲပြီး `MERGE` လုပ်သည်။

```python
from dataclasses import dataclass, field
from typing import Dict, Tuple


@dataclass
class Node:
    id: str
    labels: Tuple[str, ...]
    properties: Dict[str, object] = field(default_factory=dict)


@dataclass
class Relationship:
    type: str
    start: str
    end: str
    properties: Dict[str, object] = field(default_factory=dict)


def cypher_merge_relationship(rel, start, end):
    lines = [
        "MATCH (a:" + start.labels[0] + " {id: $start_id})",
        "MATCH (b:" + end.labels[0] + " {id: $end_id})",
        "MERGE (a)-[r:" + rel.type + "]->(b)",
    ]
    sets = ["r." + k + " = $" + k for k in sorted(rel.properties)]
    if sets:
        lines.append("SET " + ", ".join(sets))
    lines.append("RETURN r")
    params = {"start_id": rel.start, "end_id": rel.end}
    params.update(rel.properties)
    return "\n".join(lines), params


rel = Relationship("KNOWS", "p1", "p2", {"since": 2019})
stmt, params = cypher_merge_relationship(rel, Node("p1", ("Person",)), Node("p2", ("Person",)))
print(stmt)
print("---")
print("params:", params)
print("lines :", len(stmt.splitlines()))
```

Output —

```text
MATCH (a:Person {id: $start_id})
MATCH (b:Person {id: $end_id})
MERGE (a)-[r:KNOWS]->(b)
SET r.since = $since
RETURN r
---
params: {'start_id': 'p1', 'end_id': 'p2', 'since': 2019}
lines : 5
```

Function က ပြန်လိုက်သော statement သည် —

```cypher
MATCH (a:Person {id: $start_id})
MATCH (b:Person {id: $end_id})
MERGE (a)-[r:KNOWS]->(b)
SET r.since = $since
RETURN r
```

`(a)-[r:KNOWS]->(b)` သည် **directed** pattern ဖြစ်သည် — arrow က လားရာကို ဆုံးဖြတ်သည်။
`MATCH` နှစ်ခုက endpoint node နှစ်ခုကို `id` ဖြင့် ဆွဲသည်၊ ပြီးနောက် `MERGE` က
relationship ကို ရှာ/ဖန်တီးသည်။ `start_id` နှင့် `end_id` ဟူသော parameter အမည်များသည်
node statement ၏ `id` နှင့် မတိုက်ဘဲ သီးခြား ဖြစ်စေသည် — statement တစ်ခုတည်းထဲ
`MATCH` နှစ်ခု ရှိသဖြင့် `$id` နှစ်ခု ထပ်နေလျှင် ရှုပ်မည်။

---

## 7. Property မရှိသော case

`if sets:` သည် empty list အတွက် `False` ဖြစ်သဖြင့် `SET` line ကို လွှတ်သည်။

```python
from dataclasses import dataclass, field
from typing import Dict, Tuple


@dataclass
class Node:
    id: str
    labels: Tuple[str, ...]
    properties: Dict[str, object] = field(default_factory=dict)


def cypher_merge_node(node):
    lines = ["MERGE (n:" + node.labels[0] + " {id: $id})"]
    sets = ["n." + k + " = $" + k for k in sorted(node.properties)]
    if sets:
        lines.append("SET " + ", ".join(sets))
    lines.append("RETURN n")
    params = {"id": node.id}
    params.update(node.properties)
    return "\n".join(lines), params


stmt, params = cypher_merge_node(Node("x1", ("Thing",)))
print(stmt)
print("---")
print("params:", params)
print("has SET line :", "SET" in stmt)
```

Output —

```text
MERGE (n:Thing {id: $id})
RETURN n
---
params: {'id': 'x1'}
has SET line : False
```

Property မရှိလျှင် statement သည် လိုင်း ၂ လိုင်းသာ ဖြစ်သည် —

```cypher
MERGE (n:Thing {id: $id})
RETURN n
```

`has SET line : False` ကို တွေ့ရသည်။ ဤ case ကို မစစ်ဆေးလျှင် `"SET " + ", ".join([])`
သည် `"SET "` (SET နှင့် space သာ) ဖြစ်ပြီး မမှန်သော Cypher statement ထွက်မည်။ `if sets:`
ဤကို ကာကွယ်သည်။

---

## 8. `MERGE` နှင့် `CREATE` — re-run တွင် idempotency

`MERGE` နှင့် `CREATE` ၏ ကွာခြားချက်သည် run ပြီး **ထပ်ခါ** run သည့်အခါ ထင်ရှားသည်။
`MERGE` က `id` ဖြင့် ရှာ၍ မရှိလျှင် ဖန်တီးသည် (upsert)။ `CREATE` က အမြဲ **အသစ်**
ဖန်တီးသည်။

```python
class Store:
    """MERGE = upsert by identity id; CREATE = always append."""

    def __init__(self, mode):
        self.mode = mode
        self.rows = []

    def write(self, node_id, props):
        if self.mode == "MERGE":
            for row in self.rows:
                if row["id"] == node_id:
                    row["props"].update(props)
                    return
            self.rows.append({"id": node_id, "props": dict(props)})
        else:
            self.rows.append({"id": node_id, "props": dict(props)})


NODE_ID = "p1"
PROPS = {"name": "Aung Aung", "age": 34}
for mode in ("MERGE", "CREATE"):
    st = Store(mode)
    for _ in range(3):
        st.write(NODE_ID, PROPS)
    print("%-7s after 3 identical writes -> count=%d rows=%s"
          % (mode, len(st.rows), st.rows))

print("---")
print("MERGE (n:Person {id: $id})")
print("CREATE (n:Person {id: $id})")
```

Output —

```text
MERGE   after 3 identical writes -> count=1 rows=[{'id': 'p1', 'props': {'name': 'Aung Aung', 'age': 34}}]
CREATE  after 3 identical writes -> count=3 rows=[{'id': 'p1', 'props': {'name': 'Aung Aung', 'age': 34}}, {'id': 'p1', 'props': {'name': 'Aung Aung', 'age': 34}}, {'id': 'p1', 'props': {'name': 'Aung Aung', 'age': 34}}]
---
MERGE (n:Person {id: $id})
CREATE (n:Person {id: $id})
```

> ဤ `Store` သည် Neo4j engine မဟုတ်ပါ — `MERGE`/`CREATE` ၏ semantics ကို ရိုးရှင်းစွာ
> simulate လုပ်ထားသော class ဖြစ်သည်။ ဤစာရင်းထဲက output သည် ဤ simulation ၏ ရလဒ်ဖြစ်သည်။

Statement text သည် keyword တစ်လုံးသာ ကွာသည် —

```cypher
MERGE (n:Person {id: $id})
CREATE (n:Person {id: $id})
```

`MERGE` ကို သုံးပါက identical write ၃ ကြိမ်အပြီး node count သည် **၁**၊ `CREATE` ကို
သုံးပါက **၃** ဖြစ်သည်။ LLM မှ ထုတ်လုပ်သော triple များ ထပ်နေခြင်း (M04 ၏ quality gate
ကို မကျော်လွန်နိုင်သော duplicate) များအတွက် `CREATE` သည် duplicate node များ
ပွားစေမည်။ ဤအကြောင်းရင်းဖြင့် ingestion pipeline တွင် `MERGE` ကို identity property
ပေါ်တွင် သုံးသည်။

| Aspect | `MERGE (n:Person {id: $id})` | `CREATE (n:Person {id: $id})` |
| --- | --- | --- |
| ရှိပြီးသား id အတွက် | ရှိပြီးသား node ကို update | node အသစ် ထပ်ဖန်တီး |
| ၃ ကြိမ် identical write အပြီး count | ၁ | ၃ |
| Re-run (idempotency) | စိတ်ချရသည် | မစိတ်ချရ |
| သင့်တော်သည့် အခြေအနေ | Ingestion/upsert | သီးခြား event node ဖန်တီးရန် |

`MERGE` သည် idempotent ဖြစ်စေရန် **identity constraint** လိုသည် — မရှိလျှင် concurrent
run နှစ်ခု တစ်ချိန်တည်း ဆောင်ရွက်သည့်အခါ duplicate ဖြစ်နိုင်သည်။ Section 4 ၏
Exercise တွင် `CREATE CONSTRAINT ... IS UNIQUE` ထည့်မည်။

---

## 9. Naive string interpolation — ဘာကြောင့် မလုံခြုံသလဲ။

Value ကို query text ထဲ တိုက်ရိုက် ထည့်လျှင် ဘာဖြစ်သည်ကို ကြည့်ပါ။

```python
payload = "Robert'); MATCH (n) DETACH DELETE n;//"
naive = "MERGE (n:Person {id: 'p1'}) SET n.name = '" + payload + "' RETURN n"
print(naive)
print("quote count :", naive.count("'"))
print("balanced?   :", naive.count("'") % 2 == 0)

plain = "MERGE (n:Person {id: 'p1'}) SET n.name = 'plain' RETURN n"
print("plain quote count :", plain.count("'"))
print("plain balanced?   :", plain.count("'") % 2 == 0)
```

Output —

```text
MERGE (n:Person {id: 'p1'}) SET n.name = 'Robert'); MATCH (n) DETACH DELETE n;//' RETURN n
quote count : 5
balanced?   : False
plain quote count : 4
plain balanced?   : True
```

Naive query သည် —

```cypher
MERGE (n:Person {id: 'p1'}) SET n.name = 'Robert'); MATCH (n) DETACH DELETE n;//' RETURN n
```

`Robert'); MATCH (n) DETACH DELETE n;//` ထဲက `'` သည် `SET n.name = '...'` ၏
string literal ကို **အလယ်တွင် ပိတ်လိုက်** သည်။ ထို့နောက် `;` က statement အသစ် စတင်ပြီး
`MATCH (n) DETACH DELETE n` က graph တစ်ခုလုံးကို ဖျက်သည့် clause ဖြစ်လာသည်။ `//` က
ကျန်တာကို comment ဖြစ်စေသည်။ Normal value (`plain`) တွင် quote ၄ လုံး (အလုံးစုံ ဖွဲ့/ပိတ်)
ဖြစ်ပြီး payload ပါလျှင် quote ၅ လုံး (odd) ဖြစ်သွားသည်ကို နှိုင်းယှဉ်ကြည့်နိုင်သည် —
quote မညီတော့ခြင်းသည် literal ကျိုးသွားခြင်း၏ အခြေခံ အမှတ်အသား ဖြစ်သည်။

Parameterization (Exercise 5) တွင် value သည် query text ထဲ လုံးဝ မဝင်တော့သဖြင့်
payload ထဲက `'`၊ `;`၊ keyword များသည် **data** အဖြစ်သာ ကျန်သည်။ ဤကွာခြားချက်သည်
Exercise 2 ၏ `params` dict ကို query string နှင့် သီးခြားစီ ထားခြင်း၏ အကြောင်းရင်း ဖြစ်သည်။

> ဤဖိုင်တွင် Neo4j server ကို run မလုပ်ပါ — `lab.py` သည် statement text ကို text အဖြစ်
> generate လုပ်ပြီး validation ကို Python ဖြင့် simulate လုပ်သည်။ Quote-literal ၏
> အပြုအမူသည် general Cypher semantics ဖြစ်သည်။

---

## 10. Node နှင့် Relationship statement — နှိုင်းယှဉ်ဇယား

| အချက် | `cypher_merge_node` | `cypher_merge_relationship` |
| --- | --- | --- |
| ပထမ line | `MERGE (n:Label {id: $id})` | `MATCH (a:Label {id: $start_id})` |
| Endpoint ဆွဲခြင်း | မလိုပါ | `MATCH` ၂ ခု လိုသည် |
| Merge pattern | `(n:Label {id: $id})` | `(a)-[r:TYPE]->(b)` |
| Identity param | `$id` | `$start_id`၊ `$end_id` |
| Property ရှိလျှင် | `SET n.k = $k` | `SET r.k = $k` |
| params | `id` + properties | `start_id`၊ `end_id` + properties |

နှစ်ခုလုံးတွင် ပြည့်မီရမည့် စည်းမျဉ်း တူညီသည် — property key များကို `sorted()` ဖြင့်
စီရမည်၊ value များကို `params` ထဲသာ ထားရမည်၊ `RETURN` ဖြင့် ဆုံးရမည်။

---

## 11. Code တစ်ခုလုံး — Run လုပ်နိုင်သော Version

```python
from dataclasses import dataclass, field
from typing import Dict, Tuple


@dataclass
class Node:
    id: str
    labels: Tuple[str, ...]
    properties: Dict[str, object] = field(default_factory=dict)


@dataclass
class Relationship:
    type: str
    start: str
    end: str
    properties: Dict[str, object] = field(default_factory=dict)


def cypher_merge_node(node):
    lines = ["MERGE (n:" + node.labels[0] + " {id: $id})"]
    sets = ["n." + k + " = $" + k for k in sorted(node.properties)]
    if sets:
        lines.append("SET " + ", ".join(sets))
    lines.append("RETURN n")
    params = {"id": node.id}
    params.update(node.properties)
    return "\n".join(lines), params


def cypher_merge_relationship(rel, start, end):
    lines = [
        "MATCH (a:" + start.labels[0] + " {id: $start_id})",
        "MATCH (b:" + end.labels[0] + " {id: $end_id})",
        "MERGE (a)-[r:" + rel.type + "]->(b)",
    ]
    sets = ["r." + k + " = $" + k for k in sorted(rel.properties)]
    if sets:
        lines.append("SET " + ", ".join(sets))
    lines.append("RETURN r")
    params = {"start_id": rel.start, "end_id": rel.end}
    params.update(rel.properties)
    return "\n".join(lines), params


node_stmt, node_params = cypher_merge_node(Node("p1", ("Person",), {"name": "Aung Aung", "age": 34}))
rel_stmt, rel_params = cypher_merge_relationship(
    Relationship("KNOWS", "p1", "p2", {"since": 2019}),
    Node("p1", ("Person",)), Node("p2", ("Person",)))
print(node_stmt)
print("params:", node_params)
print("---")
print(rel_stmt)
print("params:", rel_params)
```

Output —

```text
MERGE (n:Person {id: $id})
SET n.age = $age, n.name = $name
RETURN n
params: {'id': 'p1', 'name': 'Aung Aung', 'age': 34}
---
MATCH (a:Person {id: $start_id})
MATCH (b:Person {id: $end_id})
MERGE (a)-[r:KNOWS]->(b)
SET r.since = $since
RETURN r
params: {'start_id': 'p1', 'end_id': 'p2', 'since': 2019}
```

---

## 12. ကိုယ်တိုင်လေ့ကျင့်ကြည့်ပါ

**မေးခွန်း** — အောက်ပါ code က ဘယ် property assignment line ကို ထုတ်မလဲ။

```python
props = {"role": "ML Engineer", "since": 2022}
sets = ["r." + k + " = $" + k for k in sorted(props)]
print(", ".join(sets))
```

1. `r.role = $role, r.since = $since`
2. `r.since = $since, r.role = $role`
3. `role = $role, since = $since`
4. `r.ML Engineer = $ML Engineer, r.2022 = $2022`

<details>
<summary>အဖြေ ကြည့်ရန်</summary>

**အဖြေ — 1. `r.role = $role, r.since = $since`**

အကြောင်းရင်း — `sorted({"role": ..., "since": ...})` သည် key များကို
`['role', 'since']` အဖြစ် စီသည် (`r` က `s` ထက် အရင်)။ Comprehension က key တိုင်းကို
`r.<key> = $<key>` ပုံစံ ပြောင်းသည်။ `"$" + k` သည် key အမည် **ကိုယ်တိုင်**ကို parameter
အမည်အဖြစ် သုံးသည် — value (`ML Engineer`၊ `2022`) သည် ဤနေရာတွင် ဝင်မလာပါ။
ဤ code ကို run ၍ အတည်ပြုပြီးဖြစ်သည်။

</details>

---

**အဓိက မှတ်ထားရန်** — Cypher generation ၏ အဓိက စည်းမျဉ်းနှစ်ခုမှာ **determinism** နှင့်
**value/syntax ခွဲခြားမှု** ဖြစ်သည်။ `sorted()` က အစီအစဉ်ကို တည်ငြိမ်စေပြီး `params`
dict က value များကို query text အပြင်ဘက်တွင် ထားသည်။ `MERGE` ကို identity property
ပေါ်တွင် သုံးခြင်းသည် re-run တွင် idempotent ဖြစ်စေသည် — ဤအချက်သည် ingestion
pipeline ၏ အခြေခံ ဖြစ်သည်။ Exercise 3 တွင် ဤသို့ generate လုပ်သော statement များကို
server မလိုဘဲ စစ်ဆေးပုံကို လေ့လာမည်။
