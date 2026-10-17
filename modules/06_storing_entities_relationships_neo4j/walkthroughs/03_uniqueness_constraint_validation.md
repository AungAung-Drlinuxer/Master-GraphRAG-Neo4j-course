# Walkthrough 03 — Uniqueness constraint validation (Exercise 3)

> ဤဖိုင်သည် Module 06 ၏ `solution.md` ထဲက Exercise 3 ကို **Python အခြေခံမှ စ၍**
> အပိုင်းလိုက် ရှင်းပြသည့် walkthrough ဖြစ်သည်။ ဤ Exercise သည် Neo4j server ကို
> မခေါ်ဘဲ constraint ၏ အပြုအမူကို **client-side တွင်** simulate လုပ်သည်။

---

## 0. ဤ Exercise က ဘာကို ဖြေရှင်းပေးသလဲ။

Graph ထဲတွင် entity တစ်ခုစီသည် `id` property တစ်ခုတည်းဖြင့် ကိုယ်စားပြုခံရသည်။ ထို `id`
သည် **ထူးခြားရမည်** (unique) နှင့် **အလွတ် မဖြစ်ရ** (not null)။ Neo4j တွင် ဤစည်းမျဉ်းကို
constraint ဖြင့် server ဘက်မှာ ထိန်းသည်။

```text
incoming write set
  Person      id='ada_lovelace'             ok
  Person      id='charles_babbage'          ok
  Person      id='ada_lovelace'  ← ထပ်     REJECT (id_unique)
  Organization id='analytical_engine_project' ok
  Location    id=''              ← အလွတ်    REJECT (id_not_null)
```

ပြဿနာမှာ real server ပေါ်တွင် ဤ violation များသည် **transaction တစ်ခုလုံးကို rollback**
စေခြင်း ဖြစ်သည်။ Row ၁၀,၀၀၀ ပါသော batch ထဲတွင် id ထပ်တစ်ခု ပါလာလျှင် ကျန် row ၉,၉၉၉
လုံး အလုပ်မဖြစ်တော့ပါ။ ထို့ကြောင့် violation ကို **write မတိုင်မီ** ဖမ်းရသည် —
defense-in-depth။

ဤ Exercise က ထို client-side validation ကို `validate_uniqueness_constraint()` ဖြင့်
ရေးပြီး violation တစ်ခုစီအတွက် မည်သည့်စည်းမျဉ်း ချိုးဖောက်သည်ကို ပြန်ပေးသည်။

ဤ code တွင် လေ့လာရမည့် Python concepts များမှာ —

- Function မှ string ပြန်ပေးခြင်းနှင့် `repr()` / `print()` ၏ ကွာခြားချက်
- Truthiness — `not node_id` သည် `""` နှင့် `None` ကို ဘယ်လို ဆက်ဆံသလဲ
- `continue` နှင့် `break` ၏ ကွာခြားချက်
- Tuple key ဖြင့် dictionary lookup
- Dictionary အသစ် ဖန်တီးပြီး list ထဲ ထည့်ခြင်း
- Loop အစီအစဉ်သည် ရလဒ်ကို ဘယ်လို ဆုံးဖြတ်သလဲ

---
## 1. `expected_constraint_ddl()` — Server ဘက်စည်းမျဉ်းကို ဖော်ပြခြင်း
Constraint ကို တည်ဆောက်ရန် DDL statement တစ်ခု လိုသည်။ Function က ထို statement ကို
string အဖြစ် ပြန်ပေးသည်။ `\n` သည် newline ၂ လိုင်းကို ခြားရန် ဖြစ်သည်။
```python
def expected_constraint_ddl():
    return ("CREATE CONSTRAINT entity_id_unique IF NOT EXISTS\n"
            "FOR (n:Entity) REQUIRE n.id IS UNIQUE")
print(expected_constraint_ddl())
print("----")
print(repr(expected_constraint_ddl()))
```

Output —
```text
CREATE CONSTRAINT entity_id_unique IF NOT EXISTS
FOR (n:Entity) REQUIRE n.id IS UNIQUE
----
'CREATE CONSTRAINT entity_id_unique IF NOT EXISTS\nFOR (n:Entity) REQUIRE n.id IS UNIQUE'
```

ထို string ကို Cypher အဖြစ် ဖတ်ရှုရန် —
```cypher
CREATE CONSTRAINT entity_id_unique IF NOT EXISTS
FOR (n:Entity) REQUIRE n.id IS UNIQUE
```

`print()` သည် string ကို မူရင်းအတိုင်း ပြသည် (newline က အစစ်အမှန် လိုင်းခြားခြင်း ဖြစ်သည်)
ပြီး `repr()` သည် Python literal အဖြစ် ပြသည် — `\n` က escape အဖြစ် ပေါ်လာသည်။
Debugging တွင် နှစ်ခုလုံး လိုသည်: `repr()` သည် space ပိုနေခြင်း၊ newline ပါနေခြင်းကို
မျက်စိဖြင့် မြင်စေသည်။

`IF NOT EXISTS` ကို ထည့်ထားခြင်းသည် idempotent DDL ဖြစ်စေသည် — bootstrap script ကို
အကြိမ်များစွာ run လျှင် ဒုတိယအကြိမ်မှစ၍ error မဖြစ်ပါ။

Namespace အပေါ် သတိပေးချက် — ဤ DDL သည် `Entity` label တစ်ခုတည်းအတွက် constraint ဖြစ်သည်။
ဤ module ၏ write path တွင် label များစွာ (`Person`၊ `Organization`၊ `Technology`၊
`Location`) ကို သုံးသဖြင့် `REQUIRE n.id IS UNIQUE` ကို **label တိုင်းအတွက်**
ဖန်တီးရသည် (သို့မဟုတ် label အားလုံးကို ခြုံသည့် `Entity` super-label ကို အသုံးပြုရသည်)။
`variable-length` label expression အတွက် Neo4j 5 တွင် —
```cypher
// label တိုင်းအတွက် constraint (Neo4j 5)
CREATE CONSTRAINT person_id_unique IF NOT EXISTS
FOR (n:Person) REQUIRE n.id IS UNIQUE

CREATE CONSTRAINT organization_id_unique IF NOT EXISTS
FOR (n:Organization) REQUIRE n.id IS UNIQUE

```

Version ကွာခြားချက် — Neo4j 5 တွင် `FOR (n:Entity) REQUIRE n.id IS UNIQUE`။
Neo4j 4.x တွင် syntax မှာ —

```cypher
// Neo4j 4.x — ဤ syntax သည် 5.x တွင် ပယ်ဖျက်ခံရသည်
CREATE CONSTRAINT entity_id_unique IF NOT EXISTS
ON (n:Entity) ASSERT n.id IS UNIQUE
```

`ON ... ASSERT` (4.x) နှင့် `FOR ... REQUIRE` (5.x) သည် တူညီသော အဓိပ္ပာယ် ဖြစ်သည်။
မည်သည့် version တွင်မဆို **constraint သည် index ကိုပါ ဖန်တီးပေးသည်** — ထို့ကြောင့်
`MERGE (n:Person {id: $id})` ၏ lookup သည် index scan ဖြစ်ပြီး graph ကြီးလာသည့်အခါ
O(1) အဆင့်တွင် ရှိသည်။ ဤအချက်သည် Exercise 5 ၏ throughput တွက်ချက်မှုနှင့် တိုက်ရိုက်
ဆက်စပ်သည်။

Security သတိပေးချက် — ဤ DDL ကို Text-to-Cypher လမ်းကြောင်းမှ **block** လုပ်ရသည်။
LLM က user အမေးကို Cypher အဖြစ် ပြောင်းသည့်စနစ်တွင် constraint/schema DDL ကို
allowlist မှ ဖယ်ထားခြင်းဖြင့် schema အလိုလို ပြောင်းလဲခြင်းကို ကာကွယ်သည်။

---
## 2. Truthiness — `not node_id` က ဘာကို စစ်သလဲ။
Validation ၏ ပထမဆုံးစစ်ဆေးချက်မှာ `if not node_id:` ဖြစ်သည်။ Python တွင် `not` သည်
bool အဖြစ် ပြောင်းပြီး စစ်သည် — **falsy** တန်ဖိုးများမှာ `""`၊ `None`၊ `0`၊ `[]`၊ `{}`။
မည်သည့် အခြေအနေတွင် `""` ဖြစ်သည်ကို တိကျစွာ သိရန် စမ်းကြည့်ပါ။
```python
for value in ["", "ada_lovelace", None, 0, "0"]:
    print("%-14r truthy=%-5s not_value=%s" % (value, bool(value), not value))
```

Output —
```text
''             truthy=False not_value=True
'ada_lovelace' truthy=True  not_value=False
None           truthy=False not_value=True
0              truthy=False not_value=True
'0'            truthy=True  not_value=False
```

| တန်ဖိုး | `bool(value)` | `not value` | `id_not_null` ဝင်မလား |
| --- | --- | --- | --- |
| `""` | `False` | `True` | ဝင်သည် |
| `"ada_lovelace"` | `True` | `False` | မဝင်ပါ |
| `None` | `False` | `True` | ဝင်သည် |
| `0` | `False` | `True` | ဝင်သည် |
| `"0"` | `True` | `False` | မဝင်ပါ |

သတိပြုရန် — `0` သည် falsy ဖြစ်သည်။ ဤ Exercise မှာ `id` သည် string ဖြစ်သဖြင့် ပြဿနာ
မဖြစ်ပါ။ သို့သော် `id` ကို numeric ဖြစ်စေလိုလျှင် `not node_id` ထက်
`node_id is None or node_id == ""` ကဲ့သို့ အတိအကျ စစ်သည့် စည်းကမ်း လိုအပ်သည်။
ဤသည်မှာ Python ၏ အဖြစ်များသော trap ဖြစ်သည် — ရည်ရွယ်ချက်ကို တိကျစွာ ရေးရသည်။

---
## 3. `continue` — မမှန်သော row ကို ကျော်ခြင်း
```python
if not node_id:
    violations.append({...})
    continue
```

`continue` သည် လက်ရှိ iteration ကို **ထိုနေရာတွင်** အဆုံးသတ်ပြီး နောက် iteration သို့
ဆက်သည်။ `break` နှင့် ကွာခြားသည် — `break` သည် loop တစ်ခုလုံးကို ရပ်သည်။
```python
for cand in [{"id": "a"}, {"id": ""}, {"id": "b"}]:
    if not cand["id"]:
        print("skip  :", cand)
        continue
    print("accept:", cand)
print("loop finished")
```

Output —
```text
accept: {'id': 'a'}
skip  : {'id': ''}
accept: {'id': 'b'}
loop finished
```

`id=""` ဖြစ်သည့် အဖွဲ့ဝင်ကို `skip` ဟု print ပြီး နောက်အဖွဲ့ဝင်သို့ ဆက်သည်။ `break`
ဖြစ်ခဲ့လျှင် `{"id": "b"}` ကို လုံးဝ မစစ်တော့ပါ။

ဤနေရာတွင် `continue` သုံးခြင်းသည် အရေးကြီးသည် — id အလွတ်ဖြစ်သည့် row ကို
duplicate စစ်ဆေးမှုထဲ **မထည့်ရ**။ `""` ကို key အဖြစ် ထည့်လိုက်လျှင် ဒုတိယအကြိမ် `""`
ဝင်လာသည့်အခါ `id_unique` ဟု မှားသတ်မှတ်ပြီး အကြောင်းရင်း နှစ်ခုကို တစ်ခုတည်းနှင့်
ရောစေသည်။ ဤ code က id အလွတ်ကို **အရင်** စစ်သဖြင့် ဤပြဿနာ မဖြစ်ပါ။

---
## 4. `CANDIDATES` — incoming write set
Candidate တစ်ခုစီသည် `label`၊ `id`၊ `name` သုံးခုပါသည့် dictionary ဖြစ်သည်။
Real write path တွင် ဤ list သည် LLM extraction output (သို့) entity resolution output
မှ လာသည်။
```python
def slug(text):
    """Canonical node id — deterministic, lowercase, ASCII-safe."""
    return "".join(ch if ch.isalnum() else "_" for ch in text.lower()).strip("_")


CANDIDATES = [
    {"label": "Person", "id": slug("Ada Lovelace"), "name": "Ada Lovelace"},
    {"label": "Person", "id": slug("Charles Babbage"), "name": "Charles Babbage"},
    {"label": "Person", "id": slug("Ada Lovelace"), "name": "A. Lovelace"},
    {"label": "Organization", "id": slug("Analytical Engine Project"),
     "name": "Analytical Engine Project"},
    {"label": "Location", "id": "", "name": "London"},
]
print("candidate count :", len(CANDIDATES))
for cand in CANDIDATES:
    print("  %-14s id=%-26r name=%s" % (cand["label"], cand["id"], cand["name"]))
print("distinct ids    :", len({(c["label"], c["id"]) for c in CANDIDATES}))
```

Output —
```text
candidate count : 5
  Person         id='ada_lovelace'             name=Ada Lovelace
  Person         id='charles_babbage'          name=Charles Babbage
  Person         id='ada_lovelace'             name=A. Lovelace
  Organization   id='analytical_engine_project' name=Analytical Engine Project
  Location       id=''                         name=London
distinct ids    : 4
```

`%-26r` သည် `repr()` ဖြင့် ညှိပြသည် — ဤနေရာတွင် အလွတ် string ကို `''` ဟု မြင်နိုင်ရန်
အရေးကြီးသည်; `print()` ဖြင့်သာ ပြလျှင် လိုင်းအဆုံးတွင် space တစ်လုံးကဲ့သို့ ပေါ်ပြီး
မျက်စိဖြင့် ခွဲရ ခက်သည်။

`{(c["label"], c["id"]) for c in CANDIDATES}` သည် **set comprehension** ဖြစ်သည်။
Candidate ၅ ခုတွင် distinct key ၄ ခုသာ ရှိခြင်းက — `(Person, ada_lovelace)` ကို နှစ်ကြိမ်
ပေးပို့ထားခြင်းကို ညွှန်းသည်။ ဤသည်မှာ client-side validation လိုရခြင်း၏ အကြောင်းရင်း
ဖြစ်သည်။

---
## 5. `seen` Dict — ပထမဆုံး တွေ့ခဲ့သည့် အမည်ကို မှတ်ခြင်း
Duplicate တစ်ခုကို ဖမ်းရုံသာမက **မည်သူနှင့် ထပ်နေသည်** ကို ပြရသည်။ ထို့ကြောင့် `seen`
dict က key → ပထမဆုံး candidate ၏ name ကို သိမ်းထားသည်။
```python
seen = {}
seen[("Person", "ada_lovelace")] = "Ada Lovelace"
print(("Person", "ada_lovelace") in seen)
print(("Person", "ada_lovelace_2") in seen)
print(("organization", "ada_lovelace") in seen)

for cand in [{"label": "Person", "id": "ada_lovelace", "name": "A. Lovelace"},
             {"label": "Person", "id": "charles_babbage", "name": "Charles Babbage"}]:
    key = (cand["label"], cand["id"])
    if key in seen:
        print("duplicate :", key, "first seen as", seen[key])
    else:
        seen[key] = cand["name"]
        print("registered:", key)
```

Output —
```text
True
False
False
duplicate : ('Person', 'ada_lovelace') first seen as Ada Lovelace
registered: ('Person', 'charles_babbage')
```

`("organization", "ada_lovelace")` သည် `seen` ထဲ မရှိပါ — label သည် key ၏ အစိတ်အပိုင်း
ဖြစ်သဖြင့် label ကွာလျှင် entity ကွာသည်ဟု သတ်မှတ်သည်။ ထို့ကြောင့် `Person` နှင့်
`Organization` နှစ်ခုလုံးတွင် `id="london"` ရှိနိုင်သည်။

Uniqueness ကို **label အတွင်းသာ** စစ်ခြင်းသည် Neo4j ၏
`FOR (n:Person) REQUIRE n.id IS UNIQUE` နှင့် ကိုက်ညီသည် — constraint တစ်ခုသည်
label တစ်ခုတည်းအတွက် ဖြစ်သည်။ Multi-tenant graph တွင် tenant id ကို key ထဲ
ပေါင်းထည့်ရမည် — `(tenant_id, label, id)` — မဟုတ်လျှင် tenant နှစ်ခုက တူညီသော `id`
ကို မသုံးနိုင်တော့ပါ။

---
## 6. `validate_uniqueness_constraint()` — Function တစ်ခုလုံး
Function ကို အပိုင်း ၃ ပိုင်း ခွဲဖတ်ပါ —

1. `violations, seen = [], {}` — list နှစ်ခုကို တစ်လိုင်းတည်း ဖန်တီးသည်
   (**tuple unpacking**; ညာဘက်က tuple `([], {})` ကို variable နှစ်ခုအဖြစ် ခွဲသည်)။
2. `for cand in candidates:` — အဖွဲ့ဝင်တိုင်းအတွက် `label`, `node_id` ကို ခွဲယူသည်;
   id အလွတ်ဖြစ်လျှင် violation ထည့်ပြီး `continue`။
3. Duplicate စစ်ဆေးခြင်း — key ရှိပြီးသားဖြစ်လျှင် `first_seen` ပါသည့် violation;
   မဟုတ်လျှင် `seen` ထဲ မှတ်သည်။
```python
def slug(text):
    """Canonical node id — deterministic, lowercase, ASCII-safe."""
    return "".join(ch if ch.isalnum() else "_" for ch in text.lower()).strip("_")


CANDIDATES = [
    {"label": "Person", "id": slug("Ada Lovelace"), "name": "Ada Lovelace"},
    {"label": "Person", "id": slug("Charles Babbage"), "name": "Charles Babbage"},
    {"label": "Person", "id": slug("Ada Lovelace"), "name": "A. Lovelace"},
    {"label": "Organization", "id": slug("Analytical Engine Project"),
     "name": "Analytical Engine Project"},
    {"label": "Location", "id": "", "name": "London"},
]

def validate_uniqueness_constraint(candidates):
    """Simulate `REQUIRE n.id IS UNIQUE` over the incoming write set."""
    violations, seen = [], {}
    for cand in candidates:
        label, node_id = cand["label"], cand["id"]
        if not node_id:
            violations.append({"label": label, "id": node_id, "rule": "id_not_null"})
            continue
        key = (label, node_id)
        if key in seen:
            violations.append({"label": label, "id": node_id,
                               "rule": "id_unique", "first_seen": seen[key]})
        else:
            seen[key] = cand["name"]
    return violations

violations = validate_uniqueness_constraint(CANDIDATES)
print("candidates=%d  violations=%d" % (len(CANDIDATES), len(violations)))
for v in violations:
    print("  %s  id=%r  rule=%s" % (v["label"], v["id"], v["rule"]))
print("first duplicate entry :", violations[0])
```

Output —
```text
candidates=5  violations=2
  Person  id='ada_lovelace'  rule=id_unique
  Location  id=''  rule=id_not_null
first duplicate entry : {'label': 'Person', 'id': 'ada_lovelace', 'rule': 'id_unique', 'first_seen': 'Ada Lovelace'}
```

Violation ၂ ခု ထွက်သည်။ ပထမတစ်ခုတွင် `first_seen` ပါသည်ကို သတိပြုပါ — ဒုတိယအကြိမ်
`ada_lovelace` ဝင်လာသည့်အခါ `seen` ထဲက `"Ada Lovelace"` ကို ပြန်ဖတ်ပြီး violation
entry ထဲ ထည့်သည်။ ဤအချက်က operator ကို "LLM က တူညီသော entity ကို အမည်နှစ်မျိုးဖြင့်
နှစ်ကြိမ် ထုတ်လိုက်သည်" ဆိုသည့် အချက်ကို ချက်ချင်း ပြသည်။

`id_not_null` violation တွင် `first_seen` key **မပါ** ပါ — violation အမျိုးအစားနှစ်ခုသည်
field မတူပါ။ ဤသည်မှာ dict ကို flexible record အဖြစ် သုံးခြင်း၏ အားသာချက် ဖြစ်သည်။

Client-side စစ်ဆေးခြင်းသည် server-side constraint ကို **အစားထိုးခြင်း မဟုတ်ပါ** —
နှစ်ခုလုံး လိုသည်။ Client က ဖမ်းနိုင်သည့် violation များမှာ —

- `id` အလွတ်/null
- တူညီသော label အတွင်း `id` ထပ်
- `id` format မမှန် (slug မဖြစ်ခြင်း၊ ရှည်လွန်းခြင်း)

Client က မဖမ်းနိုင်သည့် အခြေအနေမှာ **concurrent writer** နှစ်ခု တစ်ချိန်တည်း ရေးခြင်း
ဖြစ်သည် — ဤနေရာတွင် server-side constraint သာ အာမခံသည်။ Constraint မရှိလျှင်
`MERGE` သည် race condition ကြောင့် duplicate node ဖန်တီးနိုင်သည်။

---
## 7. ရလဒ်ကို ဇယားဖြင့် ကြည့်ခြင်း
Candidate တိုင်း၏ ဆုံးဖြတ်ချက်ကို ဇယားဖြင့် ဖော်ပြသည် (အထက်က run ၏ အမှန်တကယ်
ရလဒ်မှ ရေးသည်) —

| # | label | id | ဆုံးဖြတ်ချက် | rule |
| --- | --- | --- | --- | --- |
| 1 | `Person` | `ada_lovelace` | accept | — (`seen` ထဲ မှတ်) |
| 2 | `Person` | `charles_babbage` | accept | — (`seen` ထဲ မှတ်) |
| 3 | `Person` | `ada_lovelace` | **reject** | `id_unique`၊ `first_seen='Ada Lovelace'` |
| 4 | `Organization` | `analytical_engine_project` | accept | — |
| 5 | `Location` | `''` | **reject** | `id_not_null` |

ဤဇယားသည် code ၏ branch အစီအစဉ်ကို ပြသည် — row ၃ သည် row ၁ ၏ key နှင့် တူညီသဖြင့်
reject ဖြစ်သည်; row ၅ သည် id အလွတ်ဖြစ်သဖြင့် `id_not_null` အရင် ဝင်သည် (duplicate
စစ်ဆေးခြင်းသို့ မရောက်ပါ)။

Production တွင် ဤဇယားကို quarantine table အဖြစ် ထုတ်ရသည် — reject ဖြစ်သည့် row များကို
မူရင်း extraction record နှင့်တွဲ သိမ်းထားပြီး လူက ပြန်စစ်သည်။ Reject လုပ်ပြီး ပစ်ပယ်
လိုက်ခြင်းသည် data loss ဖြစ်သည်။

---
## 8. Code တစ်ခုလုံး — Run လုပ်နိုင်သော Version
```python
def slug(text):
    """Canonical node id — deterministic, lowercase, ASCII-safe."""
    return "".join(ch if ch.isalnum() else "_" for ch in text.lower()).strip("_")


CANDIDATES = [
    {"label": "Person", "id": slug("Ada Lovelace"), "name": "Ada Lovelace"},
    {"label": "Person", "id": slug("Charles Babbage"), "name": "Charles Babbage"},
    {"label": "Person", "id": slug("Ada Lovelace"), "name": "A. Lovelace"},
    {"label": "Organization", "id": slug("Analytical Engine Project"),
     "name": "Analytical Engine Project"},
    {"label": "Location", "id": "", "name": "London"},
]

def expected_constraint_ddl():
    return ("CREATE CONSTRAINT entity_id_unique IF NOT EXISTS\n"
            "FOR (n:Entity) REQUIRE n.id IS UNIQUE")

def validate_uniqueness_constraint(candidates):
    """Simulate `REQUIRE n.id IS UNIQUE` over the incoming write set."""
    violations, seen = [], {}
    for cand in candidates:
        label, node_id = cand["label"], cand["id"]
        if not node_id:
            violations.append({"label": label, "id": node_id, "rule": "id_not_null"})
            continue
        key = (label, node_id)
        if key in seen:
            violations.append({"label": label, "id": node_id,
                               "rule": "id_unique", "first_seen": seen[key]})
        else:
            seen[key] = cand["name"]
    return violations

violations = validate_uniqueness_constraint(CANDIDATES)
print("constraint DDL:\n" + expected_constraint_ddl())
print("candidates=%d  violations=%d" % (len(CANDIDATES), len(violations)))
for v in violations:
    print("  %s  id=%r  rule=%s" % (v["label"], v["id"], v["rule"]))
print("violation rules: %s" % sorted(v["rule"] for v in violations))
```

Output —
```text
constraint DDL:
CREATE CONSTRAINT entity_id_unique IF NOT EXISTS
FOR (n:Entity) REQUIRE n.id IS UNIQUE
candidates=5  violations=2
  Person  id='ada_lovelace'  rule=id_unique
  Location  id=''  rule=id_not_null
violation rules: ['id_not_null', 'id_unique']
```

---
## 9. ကိုယ်တိုင်လေ့ကျင့်ကြည့်ပါ

**မေးခွန်း** — candidate နှစ်ခုလုံးတွင် `id=""` ဖြစ်လျှင် violation မည်မျှ ထွက်မည်၊
မည်သည့် `rule` ဖြစ်မည်နည်း။
```python
def slug(text):
    """Canonical node id — deterministic, lowercase, ASCII-safe."""
    return "".join(ch if ch.isalnum() else "_" for ch in text.lower()).strip("_")


CANDIDATES = [
    {"label": "Person", "id": slug("Ada Lovelace"), "name": "Ada Lovelace"},
    {"label": "Person", "id": slug("Charles Babbage"), "name": "Charles Babbage"},
    {"label": "Person", "id": slug("Ada Lovelace"), "name": "A. Lovelace"},
    {"label": "Organization", "id": slug("Analytical Engine Project"),
     "name": "Analytical Engine Project"},
    {"label": "Location", "id": "", "name": "London"},
]

def validate_uniqueness_constraint(candidates):
    """Simulate `REQUIRE n.id IS UNIQUE` over the incoming write set."""
    violations, seen = [], {}
    for cand in candidates:
        label, node_id = cand["label"], cand["id"]
        if not node_id:
            violations.append({"label": label, "id": node_id, "rule": "id_not_null"})
            continue
        key = (label, node_id)
        if key in seen:
            violations.append({"label": label, "id": node_id,
                               "rule": "id_unique", "first_seen": seen[key]})
        else:
            seen[key] = cand["name"]
    return violations

candidates = [
    {"label": "Person", "id": "", "name": "Ada Lovelace"},
    {"label": "Person", "id": "", "name": "Charles Babbage"},
]
violations = validate_uniqueness_constraint(candidates)
print("count =", len(violations))
for v in violations:
    print("  rule=%s id=%r" % (v["rule"], v["id"]))
```

1. violation ၁ ခု — `id_unique`
2. violation ၂ ခု — `id_not_null` နှင့် `id_unique`
3. violation ၂ ခု — `id_not_null` နှစ်ခု
4. violation ၀ — နှစ်ခုလုံး လက်ခံသည်

<details>
<summary>အဖြေ ကြည့်ရန်</summary>

**အဖြေ — 3. violation ၂ ခု — `id_not_null` နှစ်ခု**

အကြောင်းရင်း — `if not node_id:` စစ်ဆေးချက်က duplicate စစ်ဆေးခြင်းမတိုင်မီ လာသဖြင့်
id အလွတ်တိုင်းသည် `id_not_null` violation ဖြစ်ပြီး `continue` ဖြင့် ကျော်သွားသည်။
`seen` dict ထဲ `""` ကို ဘယ်တော့မှ မထည့်သဖြင့် ဒုတိယအကြိမ် `""` ဝင်လာသည့်အခါလည်း
`id_unique` ဖြစ်ခြင်း မရှိပါ။ အထက်က run ၏ output က ဤအချက်ကို အတည်ပြုသည် —
`count = 2` ပြီး လိုင်းနှစ်လိုင်းစလုံး `rule=id_not_null`။

Branch အစီအစဉ်ကို ပြောင်းလိုက်လျှင် (`id` စစ်ဆေးချက်ကို အောက်သို့ ရွှေ့လျှင်) ဒုတိယ
`""` သည် `id_unique` ဖြစ်လာပြီး operator ကို **မှားသော အကြောင်းရင်း** ပေးလိုက်မည်။

</details>

---

**အဓိက မှတ်ထားရန်** — `REQUIRE n.id IS UNIQUE` သည် correctness အတွက်သာမက
constraint backing index ကို ဖန်တီးပေးသဖြင့် `MERGE` lookup ကို မြန်စေသည်။
Client-side validation သည် defense-in-depth ဖြစ်ပြီး id အလွတ်/null ကို server သို့
မပို့မီ ဖယ်ထုတ်ခြင်းဖြင့် transaction တစ်ခုလုံး rollback ဖြစ်ခြင်းကို ကာကွယ်သည်။
Concurrent writer များကို မဖမ်းနိုင်သဖြင့် server-side constraint သည် မဖြစ်မနေ လိုသည်;
DDL ကို Text-to-Cypher လမ်းကြောင်းမှ block လုပ်ရသည်။
