# Walkthrough 04 — Constraint နှင့် Index definitions (Exercise 4)

> ဤဖိုင်သည် Module 05 ၏ `solution.md` ထဲက Exercise 4 ကို **Python အခြေခံမှ စ၍**
> အပိုင်းလိုက် ရှင်းပြသည့် walkthrough ဖြစ်သည်။ `str.upper()`၊ `str.split()`၊
> `str.join()`၊ `in` operator၊ `str.ljust()`၊ `zip()`၊ `all()` စသည့် Python
> concept များကို ဤနေရာတွင် ရှင်းပြသည်။

---

## 0. ဤ Exercise က ဘာကို ဖြေရှင်းပေးသလဲ။

Exercise 2 တွင် `MERGE (n:Person {id: $id})` လို statement များ ဖန်တီးခဲ့သည်။ သို့သော်
`id` ပေါ်တွင် uniqueness constraint မရှိလျှင် `MERGE` သည် label scan လုပ်ရသဖြင့်
နှေးမည်၊ ပြီးနောက် concurrent write တွင် duplicate ဖြစ်နိုင်သည်။ ဤ Exercise က
**schema DDL** များ (constraint နှင့် index) ကို စာရင်းအဖြစ် သတ်မှတ်ပြီး အမျိုးအစား
ခွဲခြားသည်။

```text
CREATE CONSTRAINT person_id_unique ... REQUIRE n.id IS UNIQUE   -> uniqueness_constraint
CREATE INDEX person_name_range ... ON (n.name)                  -> range_index
CREATE FULLTEXT INDEX entity_fulltext ... ON EACH [n.name, ...] -> fulltext_index
                        |
                        v  classify_schema_ddl()
```

ဤ code မှာ လေ့လာရမည့် Python concepts — string list၊ `str.upper()`၊ `str.split()`၊
`" ".join()`၊ substring `in`၊ `if/elif` အစီအစဉ်၊ `str.ljust()`၊ `zip()`၊
`all()` ။

---

## 1. `SCHEMA_DDL` — DDL statement များ၏ စာရင်း

DDL သုံးခုကို string list အဖြစ် သတ်မှတ်သည်။

```python
SCHEMA_DDL = [
    "CREATE CONSTRAINT person_id_unique IF NOT EXISTS FOR (n:Person) REQUIRE n.id IS UNIQUE",
    "CREATE INDEX person_name_range IF NOT EXISTS FOR (n:Person) ON (n.name)",
    "CREATE FULLTEXT INDEX entity_fulltext IF NOT EXISTS FOR (n:Entity) ON EACH [n.name, n.description]",
]

def classify_schema_ddl(ddl):
    u = " ".join(ddl.upper().split())
    if "CONSTRAINT" in u and "IS UNIQUE" in u:
        return "uniqueness_constraint"
    if "FULLTEXT INDEX" in u:
        return "fulltext_index"
    if "INDEX" in u and " ON " in u:
        return "range_index"
    return "unknown"


for d in SCHEMA_DDL:
    print(len(d), "|", d)
print("count:", len(SCHEMA_DDL))
```

Output —

```text
86 | CREATE CONSTRAINT person_id_unique IF NOT EXISTS FOR (n:Person) REQUIRE n.id IS UNIQUE
71 | CREATE INDEX person_name_range IF NOT EXISTS FOR (n:Person) ON (n.name)
98 | CREATE FULLTEXT INDEX entity_fulltext IF NOT EXISTS FOR (n:Entity) ON EACH [n.name, n.description]
count: 3
```

DDL တိုင်းတွင် **`IF NOT EXISTS`** ပါသည်ကို သတိထားပါ။ Migration script တစ်ခုကို
အကြိမ်ကြိမ် run လျှင် ဒုတိယအကြိမ်တွင် error မဖြစ်စေရန် ဤ clause လိုသည် — ဆိုလိုသည်မှာ
**idempotent** ဖြစ်သည်။ Neo4j 5 syntax ဖြစ်သည်။

ဤ DDL များကို Neo4j 5 တွင် တိုက်ရိုက် run နိုင်သည် —

```cypher
CREATE CONSTRAINT person_id_unique IF NOT EXISTS FOR (n:Person) REQUIRE n.id IS UNIQUE
```

```cypher
CREATE INDEX person_name_range IF NOT EXISTS FOR (n:Person) ON (n.name)
```

```cypher
CREATE FULLTEXT INDEX entity_fulltext IF NOT EXISTS FOR (n:Entity) ON EACH [n.name, n.description]
```

> `solution.md` တွင် ဖတ်ရလွယ်စေရန် ဤ DDL များကို လိုင်းနှစ်လိုင်းအဖြစ် ခွဲပြထားသည်။
> Code က ထုတ်လုပ်သည့် string မှာ အထက်ပါအတိုင်း **လိုင်းတစ်လိုင်းတည်း** ဖြစ်သည်။

---

## 2. `ddl.upper()` နှင့် `" ".join(...split())` — နှိုင်းယှဉ်ရန် ပြင်ဆင်ခြင်း

Classification မလုပ်မီ DDL ကို **စံပုံစံ** သို့ ပြောင်းသည် — အက္ခရာအသေးအားလုံးကို
အကြီးပြောင်းပြီး space အပိုများကို ဖျောက်သည်။

```python
ddl = "CREATE FULLTEXT INDEX entity_fulltext IF NOT EXISTS FOR (n:Entity) ON EACH [n.name, n.description]"
print("raw   :", repr(ddl))
print("upper :", repr(ddl.upper()))
print("split :", ddl.upper().split()[:10])
u = " ".join(ddl.upper().split())
print("joined:", repr(u))
print("double spaces left?:", "  " in u)
```

Output —

```text
raw   : 'CREATE FULLTEXT INDEX entity_fulltext IF NOT EXISTS FOR (n:Entity) ON EACH [n.name, n.description]'
upper : 'CREATE FULLTEXT INDEX ENTITY_FULLTEXT IF NOT EXISTS FOR (N:ENTITY) ON EACH [N.NAME, N.DESCRIPTION]'
split : ['CREATE', 'FULLTEXT', 'INDEX', 'ENTITY_FULLTEXT', 'IF', 'NOT', 'EXISTS', 'FOR', '(N:ENTITY)', 'ON']
joined: 'CREATE FULLTEXT INDEX ENTITY_FULLTEXT IF NOT EXISTS FOR (N:ENTITY) ON EACH [N.NAME, N.DESCRIPTION]'
double spaces left?: False
```

`ddl.upper()` သည် စာလုံးအားလုံးကို အကြီးပြောင်းသည် — index အမည်
(`entity_fulltext`) နှင့် node variable (`n`) ပါ အကြီးဖြစ်သွားသည်ကို တွေ့ရသည်။
ဒါက အရေးမကြီးပါ — keyword များကို case-insensitive ဖြင့် စစ်လိုရုံ ဖြစ်သည်။

`split()` သည် whitespace တိုင်းတွင် ခွဲပြီး list ပြန်သည်။ `" ".join(...)` က space
တစ်ခုတည်းဖြင့် ပြန်ပေါင်းသည်။ ရလဒ်မှာ space တစ်ခုတည်း ခြားထားသော စာသားဖြစ်သည် —
`"  " in u` က `False` ဖြစ်သဖြင့် space အပို မကျန်တော့ပါ။ ဒါကြောင့် `" ON "` (space-ON-space)
လို စစ်ဆေးချက်များ ယုံကြည်စိတ်ချစွာ အလုပ်လုပ်သည်။

`split()[:10]` က ပထမ element ၁၀ ခုကို ယူသည် — slicing ဖြစ်သည်။

---

## 3. Substring စစ်ဆေးခြင်း — `in` operator

Classification သည် `in` operator ဖြင့် keyword ရှိမရှိ စစ်သည်။

```python
d = "CREATE CONSTRAINT person_id_unique IF NOT EXISTS FOR (n:Person) REQUIRE n.id IS UNIQUE"
u = " ".join(d.upper().split())
print("CONSTRAINT in u   :", "CONSTRAINT" in u)
print("IS UNIQUE in u    :", "IS UNIQUE" in u)
print("REQUIRE in u      :", "REQUIRE" in u)
print("FULLTEXT INDEX in u:", "FULLTEXT INDEX" in u)

d2 = "CREATE INDEX person_name_range IF NOT EXISTS FOR (n:Person) ON (n.name)"
u2 = " ".join(d2.upper().split())
print("ON (N.NAME) in u2 :", "ON (N.NAME)" in u2)
print("' ON ' in u2      :", " ON " in u2)
```

Output —

```text
CONSTRAINT in u   : True
IS UNIQUE in u    : True
REQUIRE in u      : True
FULLTEXT INDEX in u: False
ON (N.NAME) in u2 : True
' ON ' in u2      : True
```

`"CONSTRAINT" in u` သည် substring တစ်ခုလုံး ပါ/မပါ ကို `True`/`False` ဖြင့် ဖြေသည်။
`IS UNIQUE in u` က `True` ဖြစ်သဖြင့် ဤ DDL သည် uniqueness constraint ဖြစ်သည် —
`IS UNIQUE` သည် constraint မှ လာသည်။

`' ON ' in u2` တွင် space နှစ်ဖက်ပါသည်ကို သတိထားပါ။ `ON` (space မပါ) ကို စစ်လျှင်
`CONSTRAINT` ထဲက... မဟုတ်၊ `person_name_range` ထဲက... မဟုတ်၊ သို့သော် `ONLINE`
ကဲ့သို့ စာလုံးတစ်ခုခုထဲ `ON` ပါလျှင် false positive ဖြစ်နိုင်သည်။ Space နှစ်ဖက်ဖြင့်
စစ်ခြင်းက ထို false positive ကို လျှော့သည်။

---

## 4. `classify_schema_ddl()` — အစီအစဉ် အရေးကြီးခြင်း

`if` များ၏ **အစီအစဉ်** သည် ရလဒ်ကို ဆုံးဖြတ်သည်။ `FULLTEXT INDEX` ကို `INDEX` အရင်
စစ်ရမည်။

```python
SCHEMA_DDL = [
    "CREATE CONSTRAINT person_id_unique IF NOT EXISTS FOR (n:Person) REQUIRE n.id IS UNIQUE",
    "CREATE INDEX person_name_range IF NOT EXISTS FOR (n:Person) ON (n.name)",
    "CREATE FULLTEXT INDEX entity_fulltext IF NOT EXISTS FOR (n:Entity) ON EACH [n.name, n.description]",
]

def classify_schema_ddl(ddl):
    u = " ".join(ddl.upper().split())
    if "CONSTRAINT" in u and "IS UNIQUE" in u:
        return "uniqueness_constraint"
    if "FULLTEXT INDEX" in u:
        return "fulltext_index"
    if "INDEX" in u and " ON " in u:
        return "range_index"
    return "unknown"


def classify_wrong(ddl):
    u = " ".join(ddl.upper().split())
    if "CONSTRAINT" in u and "IS UNIQUE" in u:
        return "uniqueness_constraint"
    if "INDEX" in u and " ON " in u:      # FULLTEXT ကို INDEX အရင် စစ်လိုက်သည်
        return "range_index"
    if "FULLTEXT INDEX" in u:
        return "fulltext_index"
    return "unknown"


for d in SCHEMA_DDL:
    print("%-22s -> correct=%-22s wrong=%s"
          % (d.split()[1], classify_schema_ddl(d), classify_wrong(d)))
print("unknown case:", classify_schema_ddl("DROP INDEX x"))
```

Output —

```text
CONSTRAINT             -> correct=uniqueness_constraint  wrong=uniqueness_constraint
INDEX                  -> correct=range_index            wrong=range_index
FULLTEXT               -> correct=fulltext_index         wrong=range_index
unknown case: unknown
```

Full-text DDL သည် `FULLTEXT INDEX` နှင့် ` INDEX` နှစ်ခုလုံးကို ပါသည်။
`'FULLTEXT INDEX'` ထဲတွင် `'INDEX'` substring လည်း ပါသဖြင့် `"INDEX" in u` သည်
`True` ဖြစ်သည်၊ `' ON ' in u` လည်း `True` ဖြစ်သည်။ ဒါကြောင့် `INDEX` ကို အရင်စစ်လျှင်
full-text DDL သည် `range_index` အဖြစ် **အမှားခွဲခြား** ခံရသည်။

| DDL | `FULLTEXT INDEX` အရင် (မှန်) | `INDEX` အရင် (မှား) |
| --- | --- | --- |
| constraint DDL | `uniqueness_constraint` | `uniqueness_constraint` |
| range index DDL | `range_index` | `range_index` |
| full-text DDL | `fulltext_index` | `range_index` |

Rule — **ပိုတိကျသော (specific) pattern ကို အရင်စစ်ရသည်။** `FULLTEXT INDEX` သည်
`INDEX` ထက် တိကျသည်။ Constraint ကို ပထမဆုံး စစ်ခြင်းကလည်း ထို့အတူပါ — `CONSTRAINT`
နှင့် `IS UNIQUE` တွဲစစ်ခြင်းက သီးခြား pattern ဖြစ်သည်။

`classify_schema_ddl("DROP INDEX x")` က `unknown` ပြန်သည် — `INDEX` ပါသော်လည်း
` ON ` မပါ၊ `DROP` ကို လက်ခံသည့် အမျိုးအစား မရှိပါ။ Fallback ရှိခြင်းသည်
မသိသော input တွင် crash မလုပ်စေရန် အရေးကြီးသည်။

---

## 5. `all()` နှင့် `zip()` — စာရင်းတစ်ခုလုံးကို စစ်ဆေးခြင်း

DDL အားလုံးတွင် `IF NOT EXISTS` ပါမပါ စစ်ရန် `all()` သုံးသည်။

```python
SCHEMA_DDL = [
    "CREATE CONSTRAINT person_id_unique IF NOT EXISTS FOR (n:Person) REQUIRE n.id IS UNIQUE",
    "CREATE INDEX person_name_range IF NOT EXISTS FOR (n:Person) ON (n.name)",
    "CREATE FULLTEXT INDEX entity_fulltext IF NOT EXISTS FOR (n:Entity) ON EACH [n.name, n.description]",
]

def classify_schema_ddl(ddl):
    u = " ".join(ddl.upper().split())
    if "CONSTRAINT" in u and "IS UNIQUE" in u:
        return "uniqueness_constraint"
    if "FULLTEXT INDEX" in u:
        return "fulltext_index"
    if "INDEX" in u and " ON " in u:
        return "range_index"
    return "unknown"


kinds = [classify_schema_ddl(d) for d in SCHEMA_DDL]
print("kinds :", kinds)
print("all IF NOT EXISTS :", all("IF NOT EXISTS" in d for d in SCHEMA_DDL))
print("all has name      :", all(d.split()[2] for d in SCHEMA_DDL))
print("all on empty list :", all([]))

with_short = SCHEMA_DDL[:2] + ["CREATE INDEX x FOR (n:P) ON (n.q)"]
print("short list all IF NOT EXISTS :", all("IF NOT EXISTS" in d for d in with_short))

for kind, ddl in zip(kinds, SCHEMA_DDL):
    print(kind.ljust(22), "|", ddl)
```

Output —

```text
kinds : ['uniqueness_constraint', 'range_index', 'fulltext_index']
all IF NOT EXISTS : True
all has name      : True
all on empty list : True
short list all IF NOT EXISTS : False
uniqueness_constraint  | CREATE CONSTRAINT person_id_unique IF NOT EXISTS FOR (n:Person) REQUIRE n.id IS UNIQUE
range_index            | CREATE INDEX person_name_range IF NOT EXISTS FOR (n:Person) ON (n.name)
fulltext_index         | CREATE FULLTEXT INDEX entity_fulltext IF NOT EXISTS FOR (n:Entity) ON EACH [n.name, n.description]
```

### `all(...)`

`all(iterable)` သည် element အားလုံး `True` (သို့ truthy) ဖြစ်လျှင် `True` ပြန်သည်။
`all(["IF NOT EXISTS" in d for d in SCHEMA_DDL])` သည် DDL အားလုံးတွင် clause ပါလျှင်
`True` ဖြစ်သည်။ `with_short` တွင် `IF NOT EXISTS` မပါသော DDL တစ်ခု ထည့်လိုက်သဖြင့်
`False` ဖြစ်သွားသည်။

`all([])` သည် **`True`** ပြန်သည်ကို သတိထားပါ — "element အားလုံး" ဆိုသည်မှာ
element မရှိလျှင် vacuous truth ဖြစ်သည်။ ဤအချက်ကို မသိလျှင် empty list ကို
`all()` ဖြင့် စစ်သည့်အခါ အံ့အားသင့်စရာ ရလဒ် ရမည်။

### `zip()`

`zip(kinds, SCHEMA_DDL)` သည် list နှစ်ခုကို တွဲဖက်သည် — ပထမ element နှစ်ခု တွဲ၊
ဒုတိယ element နှစ်ခု တွဲ။ `for kind, ddl in zip(...)` တွင် tuple unpacking ဖြင့်
တစ်ခါတည်း ဖြန့်ယူသည်။ `kind.ljust(22)` က စာလုံး ၂၂ ခု space ဖြည့်ပြီး column
တန်းညှိစေသည်။

---

## 6. `IF NOT EXISTS` — migration ကို idempotent ဖြစ်စေခြင်း

DDL အားလုံးတွင် `IF NOT EXISTS` ပါမပါကို စစ်ကြည့်ခြင်းဖြင့် migration ကို
အကြိမ်ကြိမ် run နိုင်မနိုင် ဆုံးဖြတ်နိုင်သည်။

```python
SCHEMA_DDL = [
    "CREATE CONSTRAINT person_id_unique IF NOT EXISTS FOR (n:Person) REQUIRE n.id IS UNIQUE",
    "CREATE INDEX person_name_range IF NOT EXISTS FOR (n:Person) ON (n.name)",
    "CREATE FULLTEXT INDEX entity_fulltext IF NOT EXISTS FOR (n:Entity) ON EACH [n.name, n.description]",
]
with_clause = [d for d in SCHEMA_DDL if "IF NOT EXISTS" in d]
without_clause = [d for d in SCHEMA_DDL if "IF NOT EXISTS" not in d]
print("DDL total      :", len(SCHEMA_DDL))
print("with clause    :", len(with_clause))
print("without clause :", len(without_clause))
print("re-run safe?   :", len(without_clause) == 0)
```

Output —

```text
DDL total      : 3
with clause    : 3
without clause : 0
re-run safe?   : True
```

`if` clause ပါသော list comprehension နှစ်ခုသည် စာရင်းကို နှစ်ပိုင်း ခွဲသည်။
`without_clause` အလွတ်ဖြစ်ခြင်းသည် DDL အားလုံး idempotent ဖြစ်ကြောင်း ဆိုလိုသည် —
migration ကို ဒုတိယအကြိမ် run လျှင် constraint/index ရှိပြီးဖြစ်သဖြင့် error မဖြစ်ဘဲ
ကျော်သွားမည်။

> Security သတိပေးချက် — Schema DDL သည် `CREATE` သာ ဖြစ်သဖြင့် data ကို မဖျက်ပါ။
> သို့သော် `DROP CONSTRAINT`၊ `DROP INDEX` ကဲ့သို့စာလုံးများကို LLM generate လုပ်သော
> DDL ထဲ ခွင့်မပြုရ — ၎င်းတို့သည် index/constraint ကို ဖျက်ပြီး `MERGE` ၏
> performance နှင့် uniqueness အာမခံချက်ကို ဖျက်ဆီးနိုင်သည်။ Migration script ကို
> **whitelist** (ဤစာရင်းထဲက DDL များသာ) ဖြင့် run ခြင်းသည် အလုံခြုံဆုံး နည်းလမ်း ဖြစ်သည်။

---

## 7. Code တစ်ခုလုံး — Run လုပ်နိုင်သော Version

```python
SCHEMA_DDL = [
    "CREATE CONSTRAINT person_id_unique IF NOT EXISTS FOR (n:Person) REQUIRE n.id IS UNIQUE",
    "CREATE INDEX person_name_range IF NOT EXISTS FOR (n:Person) ON (n.name)",
    "CREATE FULLTEXT INDEX entity_fulltext IF NOT EXISTS FOR (n:Entity) ON EACH [n.name, n.description]",
]

def classify_schema_ddl(ddl):
    u = " ".join(ddl.upper().split())
    if "CONSTRAINT" in u and "IS UNIQUE" in u:
        return "uniqueness_constraint"
    if "FULLTEXT INDEX" in u:
        return "fulltext_index"
    if "INDEX" in u and " ON " in u:
        return "range_index"
    return "unknown"


kinds = [classify_schema_ddl(d) for d in SCHEMA_DDL]
for kind, ddl in zip(kinds, SCHEMA_DDL):
    print(kind.ljust(22), "|", ddl)
print("kinds :", kinds)
```

Output —

```text
uniqueness_constraint  | CREATE CONSTRAINT person_id_unique IF NOT EXISTS FOR (n:Person) REQUIRE n.id IS UNIQUE
range_index            | CREATE INDEX person_name_range IF NOT EXISTS FOR (n:Person) ON (n.name)
fulltext_index         | CREATE FULLTEXT INDEX entity_fulltext IF NOT EXISTS FOR (n:Entity) ON EACH [n.name, n.description]
kinds : ['uniqueness_constraint', 'range_index', 'fulltext_index']
```

Constraint သည် **backing index** ကို အလိုအလျောက် ဖန်တီးပေးသည် — ဤအကြောင်းရင်းဖြင့်
`MERGE (n:Person {id: $id})` သည် `NodeByLabelScan` အစား `NodeIndexSeek` ဖြစ်လာသည်။
Range index သည် `WHERE n.name = ...` လို equality/range lookup အတွက်၊ full-text index
သည် `db.index.fulltext.queryNodes` လို text search အတွက် ဖြစ်သည်။ Index များသည်
read ကို အမြန်စေပြီး write ကို အနည်းငယ် နှေးစေသည် — ဒါကြောင့် query pattern အပေါ်
မူတည်၍ ရွေးရသည်။

---

## 8. ကိုယ်တိုင်လေ့ကျင့်ကြည့်ပါ

**မေးခွန်း** — အောက်ပါ code က ဘယ်ရလဒ် ပြန်မလဲ။

```python
d = "CREATE FULLTEXT INDEX entity_fulltext IF NOT EXISTS FOR (n:Entity) ON EACH [n.name, n.description]"
u = " ".join(d.upper().split())
result = []
if "INDEX" in u and " ON " in u:
    result.append("range_index")
if "FULLTEXT INDEX" in u:
    result.append("fulltext_index")
print(result)
```

1. `['range_index']`
2. `['fulltext_index']`
3. `['range_index', 'fulltext_index']`
4. `[]`

<details>
<summary>အဖြေ ကြည့်ရန်</summary>

**အဖြေ — 3. `['range_index', 'fulltext_index']`**

အကြောင်းရင်း — full-text DDL သည် `'FULLTEXT INDEX'` နှင့် `' ON '` နှစ်ခုလုံးကို
ပါသည်။ `'INDEX'` သည် `'FULLTEXT INDEX'` ၏ substring ဖြစ်သဖြင့် `"INDEX" in u` သည်
`True` ဖြစ်သည်။ ဤ code သည် `if` နှစ်ခုလုံးကို သီးခြားစစ်သဖြင့် (elif မဟုတ်)
`range_index` နှင့် `fulltext_index` နှစ်ခုလုံး ဝင်လာသည်။
`solution.md` ၏ `classify_schema_ddl()` သည် **return** ဖြင့် ရပ်သဖြင့် ပထမဆုံး
ကိုက်ညီသော အမျိုးအစားကိုသာ ရသည် — ထို့ကြောင့် `FULLTEXT INDEX` ကို `INDEX` အရင်
စစ်ခြင်းသည် မဖြစ်မနေ လိုသည်။ ဤ code ကို run ၍ အတည်ပြုပြီးဖြစ်သည်။

</details>

---

**အဓိက မှတ်ထားရန်** — Constraint နှင့် index သည် graph ၏ **performance နှင့်
integrity** ကို ဆုံးဖြတ်သည်။ Uniqueness constraint က `MERGE` ၏ identity ကို
အာမခံပြီး backing index ဖြင့် lookup ကို အမြန်စေသည်။ Full-text index က entity
linking အတွက် text search ကို ဖြစ်စေသည်။ Classification လုပ်ရာတွင် **specific
pattern အရင်** (FULLTEXT INDEX ကို INDEX အရင်) ဆိုသည့် အစီအစဉ်သည် အမှားခွဲခြားမှုကို
ရှောင်စေသည်။ `IF NOT EXISTS` က migration ကို idempotent ဖြစ်စေသည်။ Exercise 5 တွင်
parameterization ဖြင့် injection ကာကွယ်ပုံကို လေ့လာမည်။
