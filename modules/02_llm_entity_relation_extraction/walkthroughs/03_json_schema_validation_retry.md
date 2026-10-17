# Walkthrough 03 — JSON Schema Validation နှင့် Retry (Exercise 3)

> ဤဖိုင်သည် Module 02 ၏ `solution.md` ထဲက Exercise 3 ကို **Python အခြေခံမှ စ၍**
> အပိုင်းလိုက် ရှင်းပြသည့် walkthrough ဖြစ်သည်။

---

## 0. ဤ Exercise က ဘာကို ဖြေရှင်းပေးသလဲ။

Exercise 2 တွင် parse လုပ်ခဲ့သည်။ သို့သော် **parse အောင်မြင်ခြင်းသည်
"မှန်ကန်ခြင်း" မဟုတ်ပါ**။

```text
chunk-002 ရဲ့ parse ရလဒ်
        │
        ├─ JSON အနေနှင့် တရားဝင် (valid JSON)          ✓
        └─ entity တစ်ခုတွင် "type" မပါ                     ✗ → ဒီအမှားကို parse မဖမ်းနိုင်

Downstream သို့ ရောက်လျှင်
        └─ entity["type"] ကို ခေါ်တိုင်း KeyError / None → graph ထဲ မှားယွင်းသော node
```

ဤ Exercise က **schema validation** နှင့် **bounded retry** နှစ်ခုကို တည်ဆောက်သည်။

- Validator သည် `object`၊ `array`၊ `string`၊ `required`၊ `enum` ကို စစ်သည်။
- Error တိုင်းကို `$.entities[1].type` ကဲ့သို့ **JSONPath** ပုံစံဖြင့် ညွှန်သည်။
- Validation မအောင်မြင်လျှင် mock output ကို `-retry` key ဖြင့် **တစ်ကြိမ်** ပြန်ခေါ်သည်။
- Retry ကုန်လျှင် `None` ပြန်သည် — **ခန့်မှန်း ဖြည့်ခြင်း မပြုပါ**။

ဤ code မှာ လေ့လာရမည့် Python concepts များမှာ —

- Nested `dict` နှင့် nested `list of dict` ဖွဲ့စည်းပုံ
- `isinstance()` စစ်ဆေးခြင်း
- **Recursion** — function က မိမိကိုယ်ကို ခေါ်ခြင်း
- Default argument (`path="$"`) နှင့် loop အလိုက် ပြောင်းလဲခြင်း
- `enumerate()` နှင့် index ဖြင့် path တည်ဆောက်ခြင်း
- `list.extend()` vs `list.append()`
- `in` operator (dict key နှင့် list value)
- `range(1, n + 1)` နှင့် `continue` / `break`
- f-string နှင့် nested quote
- Tuple ထဲက တန်ဖိုးများကို index ဖြင့် ဖတ်ခြင်း

---

## 1. `EXTRACTION_SCHEMA` — Schema ၏ ဖွဲ့စည်းပုံ

```python
EXTRACTION_SCHEMA = {
    "type": "object",
    "required": ["entities", "relationships"],
    "properties": {
        "entities": {
            "type": "array",
            "items": {
                "type": "object",
                "required": ["name", "type"],
                "properties": {
                    "name": {"type": "string"},
                    "type": {"type": "string", "enum": ENTITY_TYPES},
                },
            },
        },
        "relationships": {
            "type": "array",
            "items": {
                "type": "object",
                "required": ["source", "target", "type"],
                "properties": {
                    "source": {"type": "string"},
                    "target": {"type": "string"},
                    "type": {"type": "string", "enum": RELATIONSHIP_TYPES},
                },
            },
        },
    },
}
```

Schema သည် **data မဟုတ်** — data ဖြစ်သင့်သည့် **ပုံစံကို ဖော်ပြသည့် dict** ဖြစ်သည်။
ဖွဲ့စည်းပုံကို ခွဲကြည့်ပါ။

| Key | တန်ဖိုး၏ အမျိုးအစား | အဓိပ္ပာယ် |
| --- | --- | --- |
| `type` | string | ဤအဆင့်သည် ဘာဖြစ်ရမည် (`object` / `array` / `string`) |
| `required` | list of str | မဖြစ်မနေ ပါရမည့် key စာရင်း |
| `properties` | dict | key တိုင်း၏ sub-schema |
| `items` | dict | array ထဲက element တိုင်း၏ sub-schema |
| `enum` | list | ခွင့်ပြုထားသည့် တန်ဖိုး စာရင်း |

`properties` ထဲတွင် `entities` ၏ sub-schema သည် `type: "array"` ဖြစ်ပြီး၊
၎င်း၏ `items` သည် `type: "object"` ဖြစ်သည်။ ဤကဲ့သို့ **အဆင့်ဆင့် nested** ဖွဲ့စည်းပုံ
ကြောင့် validator သည် recursion ကို လိုအပ်သည်။

```python
print("top type      :", EXTRACTION_SCHEMA["type"])
print("top required  :", EXTRACTION_SCHEMA["required"])
print("entity types  :", EXTRACTION_SCHEMA["properties"]["entities"]["items"]["properties"]["type"]["enum"])
print("entity keys   :", list(EXTRACTION_SCHEMA["properties"]["entities"]["items"]["properties"]))
```

Output —

```text
top type      : object
top required  : ['entities', 'relationships']
entity types  : ['PERSON', 'ORGANIZATION', 'LOCATION', 'PRODUCT']
entity keys   : ['name', 'type']
```

### 1.1 `in` — Dict ထဲ ပါမပါ စစ်ခြင်း

```python
d = {"name": "Neo4j Inc.", "type": "ORGANIZATION"}
print("'name' in d      :", "name" in d)
print("'type' in d      :", "type" in d)
print("'source' in d    :", "source" in d)
print("enum ထဲ ORG ပါမပါ  :", "ORG" in ["PERSON", "ORGANIZATION"])
print("enum ထဲ PERSON ပါမပါ:", "PERSON" in ["PERSON", "ORGANIZATION"])
```

Output —

```text
'name' in d      : True
'type' in d      : True
'source' in d    : False
enum ထဲ ORG ပါမပါ  : False
enum ထဲ PERSON ပါမပါ: True
```

`in` သည် dict တွင် **key** ကို စစ်ပြီး list တွင် **value** ကို စစ်သည်။ `"ORG"` သည်
`"ORGANIZATION"` နှင့် မတူပါ — ဤအချက်သည် **schema drift** ကို ဖမ်းသည့် အဓိကအချက်
ဖြစ်သည် (Section 5.2)။

---

## 2. `validate_against_schema()` — Signature

```python
def validate_against_schema(data, schema, path="$"):
    errors = []
    kind = schema.get("type")
    ...
    return errors
```

Argument သုံးခု —

- `data` — စစ်ဆေးမည့် တန်ဖိုး (ဤ Exercise တွင် parsed payload)။
- `schema` — ထို တန်ဖိုးအတွက် ရည်ညွှန်း schema။
- `path` — **လက်ရှိ နေရာ**။ Default သည် `"$"`။ Recursion တွင် ခေါ်သည့်အခါ
  လမ်းကြောင်းကို ရှည်စေသည် (`$.entities` → `$.entities[1]` → `$.entities[1].type`)။

Function က **error message များ၏ list** ပြန်သည်။ Error မရှိလျှင် `[]` — empty
list ပြန်သည်။ `None` မပြန်ပါ — ဤအချက်သည် caller ကို ရိုးရှင်းစေသည်
(`if not errors:` ဖြင့် စစ်နိုင်)။

`errors = []` ကို function အစတွင် တစ်ခါတည်း ဖန်တီးပြီး branch တိုင်းက ထည့်သည်။

### `schema.get("type")`

```python
print("has type :", EXTRACTION_SCHEMA.get("type"))
print("no items :", EXTRACTION_SCHEMA.get("items"))
print("no items (default) :", EXTRACTION_SCHEMA.get("items", {}))
```

Output —

```text
has type : object
no items : None
no items (default) : {}
```

`schema.get(key)` သည် key မရှိလျှင် `None` ပြန်သည် — `schema[key]` လိုပဲ
`KeyError` မဖြစ်သည်။ Code က `schema.get("required", [])` နှင့်
`schema.get("properties", {})` လို့ default ပေးထားသဖြင့် optional key များ
မရှိလျှင်လည်း error မဖြစ်ပါ။

---

## 3. `object` Branch — Nested Key များကို စစ်ခြင်း

```python
    if kind == "object":
        if not isinstance(data, dict):
            return [f"{path}: expected object, got {type(data).__name__}"]
        for key in schema.get("required", []):
            if key not in data:
                errors.append(f"{path}.{key}: missing required field")
        for key, sub_schema in schema.get("properties", {}).items():
            if key in data:
                errors.extend(validate_against_schema(data[key], sub_schema, f"{path}.{key}"))
```

### 3.1 `isinstance()` — အမျိုးအစား စစ်ခြင်း

```python
print("dict   :", isinstance({}, dict))
print("list   :", isinstance([], dict))
print("str    :", isinstance("a", str))
print("int    :", isinstance(1, str))
print("True   :", isinstance(True, int))
```

Output —

```text
dict   : True
list   : False
str    : True
int    : False
True   : True
```

`isinstance(data, dict)` သည် `data` သည် dict ဖြစ်မဖြစ် စစ်သည်။ ဤ Branch တွင်
`return` ဖြင့် **ချက်ချင်း ရပ်သည်** — data က object မဟုတ်လျှင် ကျန်စစ်ဆေးချက်များ
အဓိပ္ပာယ် မရှိတော့ပါ။

`isinstance(True, int)` က `True` ဖြစ်တာကို သတိထားပါ — Python တွင် `bool` သည်
`int` ၏ subclass ဖြစ်သည်။ ဤ schema တွင် number type မစစ်သဖြင့် ဤအချက်က
ပြဿနာ မဖြစ်ပါ။

### 3.2 `required` Key စစ်ခြင်း

```python
def missing_keys(data, required):
    return [f"$.{key}: missing required field" for key in required if key not in data]

print(missing_keys({"entities": []}, ["entities", "relationships"]))
print(missing_keys({}, ["entities", "relationships"]))
print(missing_keys({"entities": [], "relationships": []}, ["entities", "relationships"]))
```

Output —

```text
['$.relationships: missing required field']
['$.entities: missing required field', '$.relationships: missing required field']
[]
```

Third line — error မရှိလျှင် **empty list** ပြန်သည်။ `print([])` က `[]` ကို
ပြသည်။ Caller က `if not errors:` ဖြင့် စစ်လျှင် empty list သည် falsy ဖြစ်သဖြင့်
"မှန်ကန်သည်" ဟု ကောက်ချက်ရနိုင်သည်။

### 3.3 Recursion နှင့် Path တည်ဆောက်ခြင်း

`validate_against_schema(data[key], sub_schema, f"{path}.{key}")` —
ဤစာကြောင်းသည် function က မိမိကိုယ်ကို ခေါ်သည်။ Path က `$.entities` ဖြစ်လျှင်
`$.entities.name` ဖြစ်လာသည်။

```python
def walk(data, schema, path="$"):
    kind = schema.get("type")
    if kind == "object":
        out = []
        for key, sub in schema.get("properties", {}).items():
            if key in data:
                out.extend(walk(data[key], sub, f"{path}.{key}"))
        return out
    if kind == "array":
        out = []
        for index, item in enumerate(data):
            out.extend(walk(item, schema.get("items", {}), f"{path}[{index}]"))
        return out
    return [path]

data = {"entities": [{"name": "A"}, {"name": "B"}]}
schema = {"type": "object", "properties": {
    "entities": {"type": "array", "items": {"type": "object", "properties": {
        "name": {"type": "string"}}}}}}
print(walk(data, schema))
```

Output —

```text
['$.entities[0].name', '$.entities[1].name']
```

ဤ snippet သည် `validate_against_schema` ၏ path တည်ဆောက်ပုံကို **ရိုးရှင်းသော
version** ဖြင့် ပြသည် (error အစား နေရာစာရင်း ပြန်သည်)။ `enumerate(data)` က
index ကို `[0]`၊ `[1]` ဖြစ်စေသည် — ဤအချက်ကြောင့် `$.entities[1].type` ကဲ့သို့
တိကျသော ညွှန်ပြချက် ရသည်။

`out.extend(...)` သည် list တစ်ခုလုံးကို ပေါင်းထည့်သည် — `out.append(...)` ဖြစ်လျှင်
list ထဲ list ဝင်သွားမည်။

```python
a = []
a.append([1, 2])
print("append:", a)
b = []
b.extend([1, 2])
print("extend:", b)
```

Output —

```text
append: [[1, 2]]
extend: [1, 2]
```

---

## 4. `array` Branch — Element တိုင်းကို စစ်ခြင်း

```python
    elif kind == "array":
        if not isinstance(data, list):
            return [f"{path}: expected array, got {type(data).__name__}"]
        item_schema = schema.get("items", {})
        for index, item in enumerate(data):
            errors.extend(validate_against_schema(item, item_schema, f"{path}[{index}]"))
```

Array မဟုတ်လျှင် ချက်ချင်း ရပ်သည်။ ဖြစ်လျှင် element တိုင်းကို `items` schema
ဖြင့် စစ်သည်။ `enumerate()` က index နှင့် တန်ဖိုး နှစ်ခုလုံး ပေးသည်။

```python
items = ["a", "b", "c"]
for index, item in enumerate(items):
    print(index, item)
print("---")
for index, item in enumerate(items, start=1):
    print(index, item)
```

Output —

```text
0 a
1 b
2 c
---
1 a
2 b
3 c
```

Default အားဖြင့် index သည် 0 မှ စသည်။ `start=1` ပေးလျှင် 1 မှ စသည်။ ဤ code
တွင် default ကို သုံးသဖြင့် `[0]` မှ စသည့် index ရသည် — JSONPath နှင့် ကိုက်ညီသည်။

---

## 5. `string` Branch နှင့် `enum`

```python
    elif kind == "string":
        if not isinstance(data, str):
            errors.append(f"{path}: expected string, got {type(data).__name__}")
        elif "enum" in schema and data not in schema["enum"]:
            errors.append(f"{path}: '{data}' is not an allowed value {schema['enum']}")
    return errors
```

`elif` သည် အရေးကြီးသည် — string မဟုတ်လျှင် enum ကို မစစ်တော့ပါ။ `data not in
schema["enum"]` ဟု စစ်သည့်အခါ data သည် string ဖြစ်ကြောင်း သေချာပြီးမှ စစ်သည်။

### 5.1 `in` / `not in` နှင့် Exact Match

```python
print("'ORGANIZATION' in list :", "ORGANIZATION" in ["PERSON", "ORGANIZATION"])
print("'ORG' in list          :", "ORG" in ["PERSON", "ORGANIZATION"])
print("'ORG' not in list      :", "ORG" not in ["PERSON", "ORGANIZATION"])
print("'person' in list       :", "person" in ["PERSON", "ORGANIZATION"])
```

Output —

```text
'ORGANIZATION' in list : True
'ORG' in list          : False
'ORG' not in list      : True
'person' in list       : False
```

**အရေးကြီးသည့် တွေ့ရှိချက်** — `'ORG' in ["PERSON", "ORGANIZATION"]` သည်
**`False`** ဖြစ်သည်။ `in` သည် **element တူညီမှု (exact match)** ကို စစ်ပြီး
substring ကို လုံးဝ မစစ်ပါ။ `"ORG"` သည် `"ORGANIZATION"` ၏ prefix ဖြစ်သော်လည်း
element မတူသဖြင့် `False` ဖြစ်သည်။ ဤအချက်ကြောင့်သာ `enum` gate သည်
schema drift ကို ဖမ်းနိုင်သည် — Section 6.1 တွင် ပြထားသည်။

Case ကိုလည်း ခွဲသည် — `"person"` သည် `"PERSON"` နှင့် မတူပါ။ ထို့ကြောင့် model
က case လွဲရေးလျှင် validator က ဖမ်းသည်။

```python
for value in ("ORG", "ORGANIZATION", "person", "PERSON"):
    allowed = value in ["PERSON", "ORGANIZATION"]
    print("%-14s in enum -> %s" % (value, allowed))
```

Output —

```text
ORG            in enum -> False
ORGANIZATION   in enum -> True
person         in enum -> False
PERSON         in enum -> True
```

---

## 6. Validator ကို တကယ် Run ကြည့်ခြင်း

```python
data = {"entities": [{"name": "A", "type": "PERSON"}, {"name": "B"}], "relationships": []}
for error in validate_against_schema(data, EXTRACTION_SCHEMA):
    print(" ", error)
```

Output —

```text
  $.entities[1].type: missing required field
```

Error သည် ပထမ entity ကို မညွှန်ဘဲ **ဒုတိယ entity** ကို ညွှန်သည်ကို သတိထားပါ —
`path` က `$.entities[1].type` ဖြစ်သည်။ ဤကဲ့သို့ တိကျသော ညွှန်ပြချက်သည်
debugging နှင့် automated repair အတွက် အခြေခံဖြစ်သည်။

### 6.1 Schema Drift ကို ဖမ်းခြင်း

```python
drift = {"entities": [{"name": "Neo4j Inc.", "type": "ORG"}], "relationships": []}
for error in validate_against_schema(drift, EXTRACTION_SCHEMA):
    print(" ", error)
```

Output —

```text
  $.entities[0].type: 'ORG' is not an allowed value ['PERSON', 'ORGANIZATION', 'LOCATION', 'PRODUCT']
```

Model များသည် `ORG` သို့မဟုတ် `Organization` ကဲ့သို့ ကိုယ်ပိုင်အတိုကောက်
ရေးလေ့ ရှိသည်။ ဤ gate က ဖမ်းသည်။ Downstream code သည် `"ORGANIZATION"` ကို
မျှော်လင့်ထားလျှင် `"ORG"` သည် silent ဖြစ်စေ၊ later error ဖြစ်စေ ဖြစ်နိုင်သည်။

### 6.2 Type မှားသော အခြေအနေများ

```python
cases = [
    ["not", "an", "object"],
    {"entities": "nope", "relationships": []},
    {"entities": [], "relationships": "nope"},
    {"entities": [42], "relationships": []},
]
for case in cases:
    print(validate_against_schema(case, EXTRACTION_SCHEMA))
```

Output —

```text
['$: expected object, got list']
['$.entities: expected array, got str']
['$.relationships: expected array, got str']
['$.entities[0]: expected object, got int']
```

Message တိုင်းတွင် **path နှင့် ရရှိသည့် အမျိုးအစား** ပါသည် — `type(data).__name__`
ကြောင့် `list`၊ `str`၊ `int` ဟု တိကျပြသည်။

### 6.3 Validator ရလဒ် ဇယား

| စစ်ဆေးသည့် data | Error | Path |
| --- | --- | --- |
| `[]` (list) | `expected object, got list` | `$` |
| `{}` (empty) | required နှစ်ခုလုံး ပျောက် | `$.entities`၊ `$.relationships` |
| `{"entities": []}` | `relationships` ပျောက် | `$.relationships` |
| entity တွင် `type` မပါ | missing required field | `$.entities[1].type` |
| `type = "ORG"` | not an allowed value | `$.entities[0].type` |
| relationship `type = "KNOWS"` | not an allowed value | `$.relationships[0].type` |

```python
bad_rel = {"entities": [{"name": "A", "type": "PERSON"}],
           "relationships": [{"source": "A", "target": "A", "type": "KNOWS"}]}
print(validate_against_schema(bad_rel, EXTRACTION_SCHEMA))
```

Output —

```text
["$.relationships[0].type: 'KNOWS' is not an allowed value ['FOUNDED_BY', 'LOCATED_IN', 'WORKS_FOR', 'PRODUCES']"]
```

---

## 7. `extract_with_retry()` — Parse + Validate + Retry

```python
def extract_with_retry(chunk_id, max_attempts=2):
    trace = []
    key = chunk_id
    for attempt in range(1, max_attempts + 1):
        raw = MOCK_LLM_RESPONSES.get(key)
        if raw is None:
            trace.append((attempt, key, "no_response", ["model returned nothing"]))
            break
        payload, meta = parse_llm_json(raw)
        if payload is None:
            trace.append((attempt, key, "parse_error", [meta]))
            key = f"{chunk_id}-retry"
            continue
        errors = validate_against_schema(payload, EXTRACTION_SCHEMA)
        trace.append((attempt, key, "ok" if not errors else "schema_error", errors))
        if not errors:
            return payload, trace
        key = f"{chunk_id}-retry"
    return None, trace
```

### 7.1 `range(1, max_attempts + 1)` နှင့် `trace`

```python
for attempt in range(1, 3):
    print("attempt", attempt)
print("---")
for attempt in range(1, 2 + 1):
    print("attempt", attempt)
```

Output —

```text
attempt 1
attempt 2
---
attempt 1
attempt 2
```

`range(1, n + 1)` သည် 1 မှ `n` အထိ (n ပါဝင်) ပေးသည်။ Attempt နံပါတ်ကို
1 မှ စရန် ဤပုံစံကို သုံးသည် — `range(max_attempts)` ဖြစ်လျှင် 0 မှ စမည်။

`trace` သည် **မှတ်တမ်း** ဖြစ်သည် — attempt တိုင်း၏ (နံပါတ်၊ key၊ status၊ detail)
ကို tuple အဖြစ် သိမ်းသည်။ Attempt တစ်ခု ကျရှုံးတိုင်း ထည့်ပြီး၊ အောင်မြင်လျှင်
`trace` နှင့်အတူ payload ပြန်သည်။ ကျရှုံးလျှင် `None, trace` ပြန်သည်။

### 7.2 Nesting — `trace.append(tuple)`

```python
trace = []
trace.append((1, "chunk-002", "schema_error", ["$.entities[1].type: missing required field"]))
entry = trace[0]
print("entry      :", entry)
print("attempt    :", entry[0])
print("key        :", entry[1])
print("status     :", entry[2])
print("detail     :", entry[3])
```

Output —

```text
entry      : (1, 'chunk-002', 'schema_error', ['$.entities[1].type: missing required field'])
attempt    : 1
key        : chunk-002
status     : schema_error
detail     : ['$.entities[1].type: missing required field']
```

`(1, "chunk-002", ...)` သည် **tuple** ဖြစ်သည် — append လုပ်သည့်အခါ ကွင်းနှစ်ခု
လိုသည် (အပြင်ကွင်း = append ၏ argument၊ အတွင်းကွင်း = tuple)။ တစ်ခုတည်း
ရေးလျှင် syntax အမှားဖြစ်သည်။ Tuple ကို index ဖြင့် ဖတ်သည် — `entry[0]`၊
`entry[1]` စသည်။ Loop တွင် `for attempt, key, status, detail in trace:` လို့
**tuple unpacking** ဖြင့် ဖတ်သည်။

### 7.3 `break` နှင့် `continue` — ကွာခြားချက်

```python
print("--- continue (retry ဆက်) ---")
key = "chunk-002"
for attempt in (1, 2):
    print("attempt", attempt, "key =", key)
    key = "chunk-002-retry"

print("--- break (retry ရပ်) ---")
key = "chunk-003"
for attempt in (1, 2):
    if MOCK_LLM_RESPONSES.get(key) is None:
        print("attempt", attempt, "-> no_response, break")
        break
    key = "chunk-003-retry"
```

Output —

```text
--- continue (retry ဆက်) ---
attempt 1 key = chunk-002
attempt 2 key = chunk-002-retry
--- break (retry ရပ်) ---
attempt 2 -> no_response, break
```

`continue` သည် လက်ရှိ iteration ကို ကျော်ပြီး **နောက် iteration ကို ဆက်**သည် —
ဒါကြောင့် retry လုပ်ခွင့် ရသည်။ `break` သည် loop တစ်ခုလုံးကို **ရပ်သည်** —
retry မလုပ်တော့ပါ။

ဒုတိယ demo တွင် `key` သည် `"chunk-003"` ဖြင့် စသည်။ `MOCK_LLM_RESPONSES` ထဲတွင်
`"chunk-003"` **ရှိသည်** (truncated string)။ ထို့ကြောင့် attempt 1 သည် break
မလုပ်ဘဲ `key` ကို `"chunk-003-retry"` သို့ ပြောင်းလိုက်သည်။ Attempt 2 တွင်မှ
`"chunk-003-retry"` မရှိသဖြင့် `break` ဖြစ်သည်။ ဤအချက်က `break` သည်
**လက်ရှိ key** ကို စစ်ကြောင်း ပြသည် — မူရင်း `chunk_id` ကို မဟုတ်ပါ။

`raw is None` ဖြစ်လျှင် `break` လုပ်ခြင်းသည် **model မှ ဘာမှ မပြန်လျှင်
ထပ်ခေါ်ခြင်းသည် အကျိုးမရှိ** ဆိုသည့် ဆုံးဖြတ်ချက်ဖြစ်သည်။

> **သတိပေးချက်** — `max_attempts=3` ပေးလျှင်လည်း `chunk-003` အတွက် attempt
> **၂ ခုသာ** ရသည် — `no_response` ဖြစ်သည့်အခါ `break` ဖြစ်သဖြင့် ဖြစ်သည်။
> ဤအချက်သည် loop ၏ terminator ကို နားလည်ရန် အရေးကြီးသည်: attempt အရေအတွက်က
> `max_attempts` နှင့် **မတူနိုင်**။

### 7.4 Retry ကို Run ကြည့်ခြင်း

```python
recovered, trace = extract_with_retry("chunk-002")
for attempt, key, status, detail in trace:
    print("  attempt %d [%s] -> %s" % (attempt, key, status))
print("recovered:", recovered is not None)
```

Output —

```text
  attempt 1 [chunk-002] -> schema_error
  attempt 2 [chunk-002-retry] -> ok
recovered: True
```

Attempt ၏ အစဉ်လိုက် အခြေအနေ —

| Attempt | Key | Status | ဖြစ်ပျက်ချက် |
| --- | --- | --- | --- |
| 1 | `chunk-002` | `schema_error` | trailing comma ပြင်ပြီး parse ဖြစ်သည်၊ ဒါပေမဲ့ `type` ပျောက် |
| 2 | `chunk-002-retry` | `ok` | သစ်လွင်သော response၊ schema ဖြတ်သည် |

```python
exhausted, trace_exhausted = extract_with_retry("chunk-003", max_attempts=2)
print(exhausted)
print(len(trace_exhausted), [entry[2] for entry in trace_exhausted])
```

Output —

```text
None
2 ['parse_error', 'no_response']
```

`chunk-003` အတွက် payload မရပါ — attempt 1 သည် `parse_error` (truncation)၊
attempt 2 သည် `no_response` (`chunk-003-retry` key မရှိ)။ `None` ပြန်ခြင်းသည်
**dead-letter** သို့ ပို့သည့် အချက်ဖြစ်သည် — မှားယွင်းသော triple များကို
graph ထဲ ထည့်ခြင်းထက် ရပ်ခြင်း ပိုကောင်းသည်။

`[entry[2] for entry in trace_exhausted]` သည် **list comprehension** ဖြစ်သည် —
tuple တိုင်း၏ index 2 (status) ကို စုစည်းသည်။ `for` loop နှင့် `append` ဖြင့်
ရေးလျှင် တူညီသည်။

---

## 8. Code တစ်ခုလုံး — Run လုပ်နိုင်သော Version

```python
# (assembled 03) Run လုပ်နိုင်သော version — အပိုင်းအားလုံး ပေါင်းစည်းထားသည်
import json
import re

FENCE = "`" * 3
ENTITY_TYPES = ["PERSON", "ORGANIZATION", "LOCATION", "PRODUCT"]
RELATIONSHIP_TYPES = ["FOUNDED_BY", "LOCATED_IN", "WORKS_FOR", "PRODUCES"]

EXTRACTION_SCHEMA = {
    "type": "object",
    "required": ["entities", "relationships"],
    "properties": {
        "entities": {
            "type": "array",
            "items": {
                "type": "object",
                "required": ["name", "type"],
                "properties": {
                    "name": {"type": "string"},
                    "type": {"type": "string", "enum": ENTITY_TYPES},
                },
            },
        },
        "relationships": {
            "type": "array",
            "items": {
                "type": "object",
                "required": ["source", "target", "type"],
                "properties": {
                    "source": {"type": "string"},
                    "target": {"type": "string"},
                    "type": {"type": "string", "enum": RELATIONSHIP_TYPES},
                },
            },
        },
    },
}

MOCK_LLM_RESPONSES = {
    "chunk-001": FENCE + "json\n" + json.dumps({
        "entities": [
            {"name": "Neo4j Inc.", "type": "ORGANIZATION"},
            {"name": "Emil Eifrem", "type": "PERSON"},
            {"name": "Sweden", "type": "LOCATION"},
            {"name": "AthenaDB", "type": "ORGANIZATION"},
        ],
        "relationships": [
            {"source": "Neo4j Inc.", "target": "Emil Eifrem", "type": "FOUNDED_BY"},
            {"source": "Emil Eifrem", "target": "Neo4j Inc.", "type": "WORKS_FOR"},
            {"source": "Neo4j Inc.", "target": "Sweden", "type": "LOCATED_IN"},
            {"source": "Neo4j Inc.", "target": "AthenaDB", "type": "PRODUCES"},
        ],
    }, indent=2) + "\n" + FENCE,
    "chunk-002": (
        "{\n"
        '  "entities": [\n'
        '    {"name": "Emil Eifrem", "type": "PERSON"},\n'
        '    {"name": "Neo4j Inc."},\n'
        "  ],\n"
        '  "relationships": [\n'
        '    {"source": "Emil Eifrem", "target": "Neo4j Inc.", "type": "WORKS_FOR"},\n'
        "  ]\n"
        "}"
    ),
    "chunk-002-retry": (
        "{\n"
        '  "entities": [\n'
        '    {"name": "Emil Eifrem", "type": "PERSON"},\n'
        '    {"name": "Neo4j Inc.", "type": "ORGANIZATION"},\n'
        '    {"name": "Sweden", "type": "LOCATION"}\n'
        "  ],\n"
        '  "relationships": [\n'
        '    {"source": "Emil Eifrem", "target": "Neo4j Inc.", "type": "WORKS_FOR"},\n'
        '    {"source": "Neo4j Inc.", "target": "Sweden", "type": "LOCATED_IN"}\n'
        "  ]\n"
        "}"
    ),
    "chunk-003": '{"entities": [{"name": "Neo4j Inc.", "type": "ORGANIZATION"',
}

CODE_FENCE_RE = re.compile(FENCE + r"(?:json)?\s*(.*?)" + FENCE, re.DOTALL)
TRAILING_COMMA_RE = re.compile(r",(\s*[}\]])")


def strip_code_fence(raw):
    match = CODE_FENCE_RE.search(raw)
    if match:
        return match.group(1).strip(), True
    return raw.strip(), False


def repair_trailing_commas(text):
    return TRAILING_COMMA_RE.sub(r"\1", text)


def parse_llm_json(raw):
    repairs = []
    text, fenced = strip_code_fence(raw)
    if fenced:
        repairs.append("stripped_code_fence")
    try:
        return json.loads(text), repairs
    except json.JSONDecodeError as exc:
        repaired = repair_trailing_commas(text)
        if repaired != text:
            try:
                payload = json.loads(repaired)
                repairs.append("removed_trailing_comma")
                return payload, repairs
            except json.JSONDecodeError:
                pass
        return None, f"{type(exc).__name__}: {exc.msg} (pos {exc.pos})"


def validate_against_schema(data, schema, path="$"):
    errors = []
    kind = schema.get("type")
    if kind == "object":
        if not isinstance(data, dict):
            return [f"{path}: expected object, got {type(data).__name__}"]
        for key in schema.get("required", []):
            if key not in data:
                errors.append(f"{path}.{key}: missing required field")
        for key, sub_schema in schema.get("properties", {}).items():
            if key in data:
                errors.extend(validate_against_schema(data[key], sub_schema, f"{path}.{key}"))
    elif kind == "array":
        if not isinstance(data, list):
            return [f"{path}: expected array, got {type(data).__name__}"]
        item_schema = schema.get("items", {})
        for index, item in enumerate(data):
            errors.extend(validate_against_schema(item, item_schema, f"{path}[{index}]"))
    elif kind == "string":
        if not isinstance(data, str):
            errors.append(f"{path}: expected string, got {type(data).__name__}")
        elif "enum" in schema and data not in schema["enum"]:
            errors.append(f"{path}: '{data}' is not an allowed value {schema['enum']}")
    return errors


def extract_with_retry(chunk_id, max_attempts=2):
    trace = []
    key = chunk_id
    for attempt in range(1, max_attempts + 1):
        raw = MOCK_LLM_RESPONSES.get(key)
        if raw is None:
            trace.append((attempt, key, "no_response", ["model returned nothing"]))
            break
        payload, meta = parse_llm_json(raw)
        if payload is None:
            trace.append((attempt, key, "parse_error", [meta]))
            key = f"{chunk_id}-retry"
            continue
        errors = validate_against_schema(payload, EXTRACTION_SCHEMA)
        trace.append((attempt, key, "ok" if not errors else "schema_error", errors))
        if not errors:
            return payload, trace
        key = f"{chunk_id}-retry"
    return None, trace


clean_payload, _ = parse_llm_json(MOCK_LLM_RESPONSES["chunk-001"])
clean_errors = validate_against_schema(clean_payload, EXTRACTION_SCHEMA)
print(f"chunk-001 schema errors  : {len(clean_errors)}")

first_payload, first_meta = parse_llm_json(MOCK_LLM_RESPONSES["chunk-002"])
first_errors = validate_against_schema(first_payload, EXTRACTION_SCHEMA)
print(f"chunk-002 schema errors  : {len(first_errors)}")
for error in first_errors:
    print(f"  - {error}")

recovered, trace = extract_with_retry("chunk-002")
for attempt, key, status, detail in trace:
    print(f"  attempt {attempt} [{key}] -> {status}")
print(f"recovered after retry    : {recovered is not None}")

exhausted, trace_exhausted = extract_with_retry("chunk-003", max_attempts=2)
print(f"chunk-003 attempts       : {len(trace_exhausted)} -> "
      f"{[entry[2] for entry in trace_exhausted]} (no payload accepted)")
```

Output —

```text
chunk-001 schema errors  : 0
chunk-002 schema errors  : 1
  - $.entities[1].type: missing required field
  attempt 1 [chunk-002] -> schema_error
  attempt 2 [chunk-002-retry] -> ok
recovered after retry    : True
chunk-003 attempts       : 2 -> ['parse_error', 'no_response'] (no payload accepted)
```

ဤ output သည် `lab.py` ၏ Exercise 3 output နှင့် တူညီသည်။

---

## 9. ကိုယ်တိုင်လေ့ကျင့်ကြည့်ပါ

**မေးခွန်း** — အောက်ပါ code က ဘယ်ရလဒ် ပြန်ပေးမလဲ။

```python
data = {"entities": [{"name": "A", "type": "PERSON"}], "relationships": []}
for error in validate_against_schema(data, EXTRACTION_SCHEMA):
    print(" ", error)
print("errors:", len(validate_against_schema(data, EXTRACTION_SCHEMA)))
```

1. error တစ်ခု — `$.type: missing required field`
2. error တစ်ခု — `$.entities[0].type: 'PERSON' is not an allowed value`
3. error မရှိ — `errors: 0`
4. error နှစ်ခု

<details>
<summary>အဖြေ ကြည့်ရန်</summary>

**အဖြေ — 3. error မရှိ — `errors: 0`**

အကြောင်းရင်း — `entities` နှင့် `relationships` နှစ်ခုလုံး ပါသည် (`required` ဖြတ်)။
Entity တွင် `name` နှင့် `type` နှစ်ခုလုံး ပါသည်။ `type` သည် `"PERSON"` ဖြစ်ပြီး
`ENTITY_TYPES` ၏ `enum` ထဲတွင် ရှိသည်။ Relationship list ကွက်လပ်ဖြစ်သဖြင့်
element တစ်ခုမှ မစစ်ရ။ ထို့ကြောင့် `validate_against_schema` က `[]`
ပြန်သည် — `print(" ", error)` loop က ဘာမှ မရိုက်။ `len([])` က `0`။

`"PERSON"` သည် ဥပမာတွင် `"A"` entity ၏ type အနေနှင့် တရားဝင်သည်။

</details>

---

**အဓိက မှတ်ထားရန်** — Validator သည် `enum` ကို စစ်ခြင်းဖြင့် schema drift
(`ORG` vs `ORGANIZATION`) ကို ဖမ်းသည်။ Error တိုင်းကို JSONPath ဖြင့်
ညွှန်ခြင်းသည် debugging နှင့် repair အတွက် အခြေခံဖြစ်သည်။ Retry သည်
**bounded** ဖြစ်သည် — attempt ၂ ခုပြီးနောက် `None` ဖြစ်ပြီး chunk သည် dead-letter
list သို့ ရောက်သည်။ ဤအပြုအမူသည် cost ကို ခန့်မှန်းနိုင်စေသည်။ `break` နှင့်
`continue` ၏ ကွာခြားချက်သည် loop ၏ attempt အရေအတွက်ကို ဆုံးဖြတ်သဖြင့်
`max_attempts` ပေးသည့် အရေအတွက်နှင့် အမှန် ရရှိသည့် အရေအတွက် ကွာနိုင်သည်။
