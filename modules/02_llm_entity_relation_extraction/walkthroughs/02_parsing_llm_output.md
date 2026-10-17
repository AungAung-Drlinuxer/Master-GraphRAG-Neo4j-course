# Walkthrough 02 — Parsing Scripted LLM Output (Exercise 2)

> ဤဖိုင်သည် Module 02 ၏ `solution.md` ထဲက Exercise 2 ကို **Python အခြေခံမှ စ၍**
> အပိုင်းလိုက် ရှင်းပြသည့် walkthrough ဖြစ်သည်။

> **မှတ်ချက် — fence token ကို variable အဖြစ် ရေးထားခြင်း။**
> ဤ Exercise သည် code fence (backtick ၃ လုံး) ကို regex ဖြင့် ရှာသည့်အလုပ်ဖြစ်သည်။
> ဤ walkthrough ၏ ကိုယ်ပိုင် markdown fence များ မကွဲစေရန် fence token ကို
> `FENCE = "`" * 3` လို့ variable အဖြစ် သတ်မှတ်ပြီး ရေးထားသည်။ ရရှိသည့် regex သည်
> `solution.md` ရှိ literal pattern နှင့် **byte-identical** ဖြစ်ကြောင်း Section 1 တွင်
> run စစ်ပြထားသည်။

---

## 0. ဤ Exercise က ဘာကို ဖြေရှင်းပေးသလဲ။

Exercise 1 တွင် prompt ကို တည်ဆောက်ပြီးသည်။ သို့သော် model ပြန်ပေးသည့်
စာသားကို တိုက်ရိုက် `json.loads()` ဖြင့် ဖတ်လို့ မရပါ။ Real model များသည်
JSON ကို ပုံစံအမျိုးမျိုးဖြင့် ပြန်ပေးလေ့ ရှိသည်။

```text
model ပြန်ပေးသော စာသားများ
        │
        ├─ code fence (backtick ၃ လုံး) ဖြင့် ပတ်ထား  → JSON အဖြစ် တိုက်ရိုက် မဖတ်နိုင်
        ├─ {... , }  trailing comma ပါ                  → တင်းကျပ် JSON ငြင်းသည်
        └─ {"entities": [{"name": ...  ဖြတ်တောက်ခံရသည်  → truncated
```

ဤ Exercise က အခြေအနေ သုံးမျိုးကို **မတူညီသော နည်းလမ်းဖြင့်** ကိုင်တွယ်သည် —

- Code fence ပါလျှင် → **ဖယ်** (strip) ပြီး parse လုပ်။ ဖယ်ခဲ့ကြောင်း မှတ်တမ်းတင်။
- Trailing comma ပါလျှင် → **ပြင်** (repair) ပြီး parse လုပ်။ ပြင်ခဲ့ကြောင်း မှတ်တမ်းတင်။
- Truncated ဖြစ်လျှင် → **ပြန်မရနိုင်ပါ**။ `None` နှင့် error message ပြန်ပေး။

အဓိကသဘောတရားမှာ — **repair တစ်ခုကို silent မလုပ်ရ**။ ဘာပြင်ခဲ့သည်ကို
`repairs` list ထဲ မှတ်တမ်းတင်ရသည်။ ဤ list သည် provenance (ရလာသည့် လမ်းကြောင်း) ၏
အစိတ်အပိုင်းဖြစ်သည်။

ဤ code မှာ လေ့လာရမည့် Python concepts များမှာ —

- `re.compile()` နှင့် `match.group(n)`
- `re.DOTALL` flag နှင့် `.` ၏ အခန်းကဏ္ဍ
- `(?:...)` non-capturing group နှင့် capturing group ၏ ကွာခြားချက်
- `re.sub(pattern, replacement, text)` နှင့် backreference `\1`
- Tuple ကို နှစ်ခုအဖြစ် ပြန်ခွဲခြင်း (tuple unpacking)
- `try` / `except` / `pass` နှင့် nested `try`
- Exception object ၏ attribute — `.msg`, `.pos`
- f-string အတွင်း `{type(exc).__name__}`
- `list.append()` နှင့် string နှိုင်းယှဉ်ခြင်း

---

## 1. `CODE_FENCE_RE` — Code Fence ရှာသည့် Pattern

```python
FENCE = "`" * 3
CODE_FENCE_RE = re.compile(FENCE + r"(?:json)?\s*(.*?)" + FENCE, re.DOTALL)
```

Pattern ကို run စစ်ကြည့်ပါ။ အောက်ပါ snippet သည် ဤ regex ကို literal backtick
pattern နှင့် နှိုင်းယှဉ်စစ်သည်။

```python
import re

FENCE = "`" * 3
BUILT = re.compile(FENCE + r"(?:json)?\s*(.*?)" + FENCE, re.DOTALL)
literal = chr(96) * 3
LITERAL = re.compile(literal + r"(?:json)?\s*(.*?)" + literal, re.DOTALL)

print("FENCE length        :", len(FENCE))
print("built pattern length:", len(BUILT.pattern))
print("equal to literal    :", BUILT.pattern == LITERAL.pattern)
sample = FENCE + "json\n" + '{"a": 1}' + "\n" + FENCE
print("search found        :", bool(BUILT.search(sample)))
print("group(1)            :", repr(BUILT.search(sample).group(1)))
```

Output —

```text
FENCE length        : 3
built pattern length: 23
equal to literal    : True
search found        : True
group(1)            : '{"a": 1}\n'
```

`chr(96)` သည် backtick character ကို ပြန်သည် — backtick တစ်ခုကို ကိုယ်တိုင်
မရေးဘဲ ရရှိသည့် နည်းလမ်းဖြစ်သည်။ `BUILT.pattern == LITERAL.pattern` က `True`
ဖြစ်ခြင်းသည် variable ဖြင့် တည်ဆောက်သည့် pattern နှင့် literal pattern
တူညီကြောင်း အတည်ပြုသည်။

### 1.1 Pattern ကို အပိုင်းလိုက် ဖတ်ခြင်း

| အပိုင်း | အဓိပ္ပာယ် |
| --- | --- |
| `FENCE` | backtick ၃ လုံး — fence အစ |
| `(?:json)?` | "json" စာလုံး — optional (ရှိလည်းရ၊ မရှိလည်းရ) |
| `\s*` | ရှေ့က whitespace (newline အပါ) မည်မျှမဆို |
| `(.*?)` | **group 1** — ဖမ်းယူလိုသည့် JSON အကြောင်းအရာ |
| `FENCE` | backtick ၃ လုံး — fence အဆုံး |

`(?:...)` သည် **non-capturing group** ဖြစ်သည်။ `.groups()` တွင် `json` မပါဝင်တာကို
တွေ့နိုင်သည် — group တစ်ခုတည်း (`(.*?)`) သာ ရှိသည်။ Capturing group ဖြစ်လျှင်
`group(1)` သည် `json` ဖြစ်သွားပြီး JSON အကြောင်းအရာက `group(2)` သို့ ရွေ့သည်။

```python
import re

FENCE = "`" * 3
sample = FENCE + "json\n" + '{"a": 1}' + "\n" + FENCE
CAPTURE = re.compile(FENCE + r"(json)?\s*(.*?)" + FENCE, re.DOTALL)
NON_CAPTURE = re.compile(FENCE + r"(?:json)?\s*(.*?)" + FENCE, re.DOTALL)

print("capturing group(1)   :", repr(CAPTURE.search(sample).group(1)))
print("capturing group(2)   :", repr(CAPTURE.search(sample).group(2)))
print("non-capturing g(1)   :", repr(NON_CAPTURE.search(sample).group(1)))
print("non-capturing groups :", NON_CAPTURE.search(sample).groups())
```

Output —

```text
capturing group(1)   : 'json'
capturing group(2)   : '{"a": 1}\n'
non-capturing g(1)   : '{"a": 1}\n'
non-capturing groups : ('{"a": 1}\n',)
```

ဤကွာခြားချက်သည် အလွန်သေးငယ်ပုံရပေမဲ့ အရေးကြီးသည် — `group(1)` ကို ခေါ်သည့်
code သည် capturing group ဖြစ်လျှင် **မှားယွင်းသော အကြောင်းအရာ** ရမည်။
Capturing group မလိုလျှင် `(?:...)` ကို သုံးခြင်းသည် ရည်ရွယ်ချက်ကို ရှင်းစေသည်။

### 1.2 `re.DOTALL` မလိုဘဲ မရခြင်း

```python
import re

FENCE = "`" * 3
sample = FENCE + "json\n" + '{"a": 1}' + "\n" + FENCE
DOTALL = re.compile(FENCE + r"(?:json)?\s*(.*?)" + FENCE, re.DOTALL)
NODOT = re.compile(FENCE + r"(?:json)?\s*(.*?)" + FENCE)

print("with DOTALL   :", bool(DOTALL.search(sample)))
print("without DOTALL:", NODOT.search(sample))
```

Output —

```text
with DOTALL   : True
without DOTALL: None
```

`.` သည် default အားဖြင့် newline ကို **မကိုက်ညီ**ပါ။ `re.DOTALL` ပေးလျှင် `.` သည်
newline အပါ ကိုက်ညီသည်။ Fence အတွင်းက JSON သည် လိုင်းများစွာ ရှိသဖြင့်
`re.DOTALL` မပါလျှင် match လုံးဝ မဖြစ်ပါ (`None`)။ `if match:` ဖြင့် စစ်ခြင်းသည်
`None` ကို မှန်ကန်စွာ handle လုပ်သည်။

### 1.3 Fence မပါသော အခြေအနေ

```python
import re

FENCE = "`" * 3
CODE_FENCE_RE = re.compile(FENCE + r"(?:json)?\s*(.*?)" + FENCE, re.DOTALL)

print("no fence      :", CODE_FENCE_RE.search('  {"a": 1}  '))
print("without json  :", repr(CODE_FENCE_RE.search(FENCE + '{"a":1}' + FENCE).group(1)))
```

Output —

```text
no fence      : None
without json  : '{"a":1}'
```

`json` စာလုံး မပါသော fence ဖြစ်လျှင်လည်း `(?:json)?` ကြောင့် match ဖြစ်သည်။

---

## 2. `strip_code_fence()` — Fence ဖယ်ခြင်း

```python
def strip_code_fence(raw):
    match = CODE_FENCE_RE.search(raw)
    if match:
        return match.group(1).strip(), True
    return raw.strip(), False
```

Function က **tuple နှစ်ခု** ပြန်သည် — စာသားနှင့် "fence ဖယ်ခဲ့သလား" ဆိုသည့် boolean။
`if match:` သည် match ရှိလျှင် `True`၊ `None` ဖြစ်လျှင် `False` ဖြစ်သည်။

```python
import re

FENCE = "`" * 3
CODE_FENCE_RE = re.compile(FENCE + r"(?:json)?\s*(.*?)" + FENCE, re.DOTALL)

def strip_code_fence(raw):
    match = CODE_FENCE_RE.search(raw)
    if match:
        return match.group(1).strip(), True
    return raw.strip(), False

fenced = FENCE + "json\n" + '{"a": 1}' + "\n" + FENCE
print(strip_code_fence(fenced))
text, fenced_flag = strip_code_fence(fenced)
print("tuple ခွဲထုတ်ပြီး :", repr(text), fenced_flag)
print("plain text      :", strip_code_fence('  {"a": 1}  '))
```

Output —

```text
('{"a": 1}', True)
tuple ခွဲထုတ်ပြီး : '{"a": 1}' True
plain text      : ('{"a": 1}', False)
```

`text, fenced_flag = strip_code_fence(...)` သည် tuple unpacking ဖြစ်သည် —
ပထမတန်ဖိုး `text` ထဲ၊ ဒုတိယတန်ဖိုး `fenced_flag` ထဲ ဝင်သည်။ Fence ပါလျှင် `True`
ပြန်သဖြင့် caller က "fence ဖယ်ခဲ့သည်" ဆိုသည်ကို သိနိုင်သည်။

---

## 3. `TRAILING_COMMA_RE` — Trailing Comma ပြင်ခြင်း

```python
TRAILING_COMMA_RE = re.compile(r",(\s*[}\]])")
```

```python
import re

TRAILING_COMMA_RE = re.compile(r",(\s*[}\]])")
broken = '{\n  "x": [\n    1,\n    2,\n  ]\n}'
print("before:", repr(broken))
print("after :", repr(TRAILING_COMMA_RE.sub(r"\1", broken)))
```

Output —

```text
before: '{\n  "x": [\n    1,\n    2,\n  ]\n}'
after : '{\n  "x": [\n    1,\n    2\n  ]\n}'
```

### 3.1 Pattern နှင့် Replacement

| အပိုင်း | အဓိပ္ပာယ် |
| --- | --- |
| `,` | Literal comma |
| `(\s*[}\]])` | **group 1** — whitespace များနှင့် `}` သို့မဟုတ် `]` |

`re.sub(pattern, r"\1", text)` က match တစ်ခုလုံးကို **group 1** ဖြင့် အစားထိုးသည်။
Match တစ်ခုလုံးသည် `,\n  ]` ဖြစ်ပြီး group 1 သည် `\n  ]` ဖြစ်သည်။ ထို့ကြောင့် comma
သာ ဖြတ်သွားသည်။ `\1` သည် raw string (`r"\1"`) ဖြစ်ရမည် — `"\1"` ရေးလျှင် Python က
octal escape အဖြစ် ဖတ်နိုင်သည်။

```python
import re

TRAILING_COMMA_RE = re.compile(r",(\s*[}\]])")
print(TRAILING_COMMA_RE.sub(r"\1", '{"a": 1,}'))
print(TRAILING_COMMA_RE.sub(r"\1", '{"a": [1, 2,]}'))
print(TRAILING_COMMA_RE.sub(r"\1", '{"a": 1}'))
```

Output —

```text
{"a": 1}
{"a": [1, 2]}
{"a": 1}
```

Trailing comma မရှိလျှင် စာသား မပြောင်းပါ — ဤအချက်သည် နောက်ပိုင်း
Section 4.3 ၏ guard အတွက် အရေးကြီးသည်။

### 3.2 Trap — Repair က String အတွင်းက Comma ကို ပြင်နိုင်သည်

Pattern သည် JSON ကို **နားလည်ခြင်း မရှိပါ** — byte ပုံစံဖြင့်သာ ရှာသည်။
ထို့ကြောင့် comma တစ်ခုသည် string value အတွင်း ရှိလျှင်လည်း ဖြတ်နိုင်သည်။

```python
import re

TRAILING_COMMA_RE = re.compile(r",(\s*[}\]])")
evil = '{"note": "see, } done", "n": 1,}'
print("before:", evil)
print("after :", TRAILING_COMMA_RE.sub(r"\1", evil))
```

Output —

```text
before: {"note": "see, } done", "n": 1,}
after : {"note": "see } done", "n": 1}
```

`"see, } done"` ထဲက comma သည် `}` နှင့် space ခြားပြီး ကပ်နေသဖြင့် pattern က
ဖမ်းမိပြီး ဖြတ်လိုက်သည်။ Result — မူရင်း value ပြောင်းသွားသည်။

> **မှတ်ထားရန်** — regex ဖြင့် JSON ကို "ပြင်ခြင်း" သည် value များကို
> မထိခိုက်စေရန် အာမခံချက် မရှိပါ။ Production တွင် repair လုပ်ပြီးသည့်နောက်
> payload ကို schema validate လုပ်ခြင်းသည် မဖြစ်မနေ လိုအပ်သည် — ဤ module ၏
> Exercise 3 က ထိုအလုပ်ကို လုပ်သည်။

ဤ Exercise ၏ mock data တွင် ဤကဲ့သို့ string မပါသဖြင့် ရလဒ်မှာ မှန်ကန်သည်။
သို့သော် pattern ၏ ကန့်သတ်ချက်ကို သိထားရမည်။

---

## 4. `parse_llm_json()` — ပင်မ Function

```python
def parse_llm_json(raw):
    """Return (payload, repairs) on success, or (None, error_message) on failure."""
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
```

### 4.1 Return Value ၏ ပုံစံ

Function သည် အခြေအနေ နှစ်မျိုးအတွက် ပြန်ပေးသည့် ပုံစံ ကွာသည် —

| အခြေအနေ | ပထမ တန်ဖိုး | ဒုတိယ တန်ဖိုး |
| --- | --- | --- |
| အောင်မြင် | `payload` (dict) | `repairs` (list of str) |
| ကျရှုံး | `None` | error message (str) |

Caller က `if payload is None:` ဖြင့် ခွဲနိုင်သည်။ ဒုတိယတန်ဖိုးသည်
အခြေအနေနှစ်မျိုးတွင် အမျိုးအစားမတူ (list vs str) — ဒါကြောင့်
`repairs` ကို မလိုဘဲ မဖတ်ရ။

### 4.2 `try` / `except` နှင့် Exception Attributes

```python
import json

raw = '{"entities": [{"name": "Neo4j Inc.", "type": "ORGANIZATION"'
try:
    json.loads(raw)
except json.JSONDecodeError as exc:
    print("type    :", type(exc).__name__)
    print("msg     :", exc.msg)
    print("pos     :", exc.pos)
    print("lineno  :", exc.lineno)
    print("colno   :", exc.colno)
```

Output —

```text
type    : JSONDecodeError
msg     : Expecting ',' delimiter
pos     : 59
lineno  : 1
colno   : 60
```

`json.JSONDecodeError` သည် `ValueError` ၏ subclass ဖြစ်သည်။ Attribute များမှာ —

- `.msg` — အတိုဆုံး error အကြောင်းရင်း။
- `.pos` — error ဖြစ်သည့် **character index** (0 မှ စသည်)။
- `.lineno` / `.colno` — လိုင်းနှင့် Column (1 မှ စသည်)။

`.msg` နှင့် `.pos` ပေါင်းလျှင် လုံလောက်သည် — ဖြတ်တောက်ခံရသည့် chunk တစ်ခုကို
debug လုပ်ရန် `pos` က နေရာကို တိကျစွာ ညွှန်ပေးသည်။

```python
exc_msg = "Expecting ',' delimiter"
exc_pos = 59
print(f"JSONDecodeError: {exc_msg} (pos {exc_pos})")
```

Output —

```text
JSONDecodeError: Expecting ',' delimiter (pos 59)
```

`type(exc).__name__` က class အမည်ကို စာသားအဖြစ် ရသည် — exception အမျိုးအစား
များစွာ ဖြစ်နိုင်သည့် code တွင် အသုံးဝင်သည်။ Error message ကို
`{type(exc).__name__}: {exc.msg} (pos {exc.pos})` ပုံစံဖြင့် တည်ဆောက်သည်။

### 4.3 `repaired != text` Guard

```python
import re

TRAILING_COMMA_RE = re.compile(r",(\s*[}\]])")

def repair_trailing_commas(text):
    return TRAILING_COMMA_RE.sub(r"\1", text)

clean = '{"a": [1, 2]}'
dirty = '{"a": [1, 2,]}'
print("clean changed?:", repair_trailing_commas(clean) != clean)
print("dirty changed?:", repair_trailing_commas(dirty) != dirty)
```

Output —

```text
clean changed?: False
dirty changed?: True
```

ဤ guard သည် အရေးကြီးသည် — repair လုပ်ထားသည့် စာသားသည် **မူရင်းနှင့် တူညီနေလျှင်**
`json.loads()` ကို ထပ်မခေါ်ရ။ မူရင်းက ကျရှုံးခဲ့ပြီးသား ဖြစ်သည်။ ဒုတိယ `try`
ထဲက `json.loads(repaired)` က မလိုအပ်သော အလုပ်ဖြစ်ပြီး၊ ထပ်ကျရှုံးလျှင်
`pass` ဖြင့် ကျော်ပြီး မူရင်း error ကို ပြန်သည်။

### 4.4 `repairs.append()` — Provenance မှတ်တမ်း

```python
repairs = []
repairs.append("stripped_code_fence")
print(repairs)
print("length:", len(repairs))
```

Output —

```text
['stripped_code_fence']
length: 1
```

`repairs` သည် list ဖြစ်သည်။ ဤ Exercise တွင် string တစ်ခုသာ ထည့်သည်သော်လည်း
list အဖြစ် ထားခြင်းက sequence ကို ထိန်းသည် — repair နှစ်ခု
တစ်ဆက်တည်း ဖြစ်လျှင် အစဉ်လိုက် မှတ်တမ်းတင်ရန် နေရာရှိသည်။ မှတ်တမ်းမတင်ဘဲ
ဖျောက်ခြင်းသည် နောက်ပိုင်း quality audit ကို မဖြစ်နိုင်စေပါ။

---

## 5. ရလဒ်ကို Run လုပ်ကြည့်ခြင်း

Mock response သုံးခုကို parse လုပ်ပြီး ရလဒ်ကို ပြပါ။

```python
for chunk_id in ("chunk-001", "chunk-002", "chunk-003"):
    payload, meta = parse_llm_json(MOCK_LLM_RESPONSES[chunk_id])
    if payload is None:
        print(f"{chunk_id}: FAILED to parse -> {meta}")
    else:
        print(
            f"{chunk_id}: parsed OK | entities={len(payload['entities'])} "
            f"relationships={len(payload['relationships'])} | repairs={meta}"
        )
```

Output —

```text
chunk-001: parsed OK | entities=4 relationships=4 | repairs=['stripped_code_fence']
chunk-002: parsed OK | entities=2 relationships=1 | repairs=['removed_trailing_comma']
chunk-003: FAILED to parse -> JSONDecodeError: Expecting ',' delimiter (pos 59)
```

### ရလဒ် နှိုင်းယှဉ်ဇယား

| Chunk | Defect | ကိုင်တွယ်ပုံ | `repairs` | ရလဒ် |
| --- | --- | --- | --- | --- |
| `chunk-001` | code fence | ဖယ်လိုက်သည် | `['stripped_code_fence']` | entity 4၊ relationship 4 |
| `chunk-002` | trailing comma + type ပျောက် | comma ပြင်လိုက်သည် | `['removed_trailing_comma']` | entity 2၊ relationship 1 |
| `chunk-003` | truncation | မပြင်နိုင် | — | `None` + error |

`chunk-002` သည် parse အောင်မြင်သော်လည်း **schema မမှန်ကန်** ကြောင်း သတိထားပါ —
ဒုတိယ entity (`{"name": "Neo4j Inc."}`) တွင် `type` မပါပါ။ ဤအမှားကို parse stage က
မဖမ်းနိုင်ပါ — Exercise 3 ၏ schema validation က ဖမ်းသည်။ **Stage တိုင်းသည်
မိမိတာဝန်သာ စစ်သည်။**

`chunk-003` သည် entity တစ်ခုစပါပြီး ဖြတ်တောက်ခံရသည်။ ဤကဲ့သို့ case ကို
"ခန့်မှန်း ဖြည့်" ခြင်းသည် မှားယွင်းသော triple များကို graph ထဲ ထည့်စေနိုင်သည်။
ထို့ကြောင့် error အဖြစ် တိတိကျကျ ပြန်ပေးသည်။

---

## 6. Code တစ်ခုလုံး — Run လုပ်နိုင်သော Version

```python
# (assembled 02) Run လုပ်နိုင်သော version — အပိုင်းအားလုံး ပေါင်းစည်းထားသည်
import json
import re

FENCE = "`" * 3

MOCK_LLM_RESPONSES = {
    "chunk-001": (
        FENCE + "json\n"
        "{\n"
        '  "entities": [\n'
        '    {"name": "Neo4j Inc.", "type": "ORGANIZATION"},\n'
        '    {"name": "Emil Eifrem", "type": "PERSON"},\n'
        '    {"name": "Sweden", "type": "LOCATION"},\n'
        '    {"name": "AthenaDB", "type": "ORGANIZATION"}\n'
        "  ],\n"
        '  "relationships": [\n'
        '    {"source": "Neo4j Inc.", "target": "Emil Eifrem", "type": "FOUNDED_BY"},\n'
        '    {"source": "Emil Eifrem", "target": "Neo4j Inc.", "type": "WORKS_FOR"},\n'
        '    {"source": "Neo4j Inc.", "target": "Sweden", "type": "LOCATED_IN"},\n'
        '    {"source": "Neo4j Inc.", "target": "AthenaDB", "type": "PRODUCES"}\n'
        "  ]\n"
        "}\n"
        + FENCE
    ),
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
    """Return (payload, repairs) on success, or (None, error_message) on failure."""
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


for chunk_id in ("chunk-001", "chunk-002", "chunk-003"):
    payload, meta = parse_llm_json(MOCK_LLM_RESPONSES[chunk_id])
    if payload is None:
        print(f"{chunk_id}: FAILED to parse -> {meta}")
    else:
        print(
            f"{chunk_id}: parsed OK | entities={len(payload['entities'])} "
            f"relationships={len(payload['relationships'])} | repairs={meta}"
        )
```

Output —

```text
chunk-001: parsed OK | entities=4 relationships=4 | repairs=['stripped_code_fence']
chunk-002: parsed OK | entities=2 relationships=1 | repairs=['removed_trailing_comma']
chunk-003: FAILED to parse -> JSONDecodeError: Expecting ',' delimiter (pos 59)
```

ဤ output သည် `lab.py` ၏ Exercise 2 output နှင့် တူညီသည်။ `FENCE` variable ကြောင့်
regex နှင့် mock response များသည် `solution.md` ရှိ literal backtick version နှင့်
တူညီသော ရလဒ် ပေးသည်။

---

## 7. ကိုယ်တိုင်လေ့ကျင့်ကြည့်ပါ

**မေးခွန်း** — အောက်ပါ code က ဘယ်ရလဒ် ပြန်ပေးမလဲ။

```python
import re

FENCE = "`" * 3
REGEX = re.compile(FENCE + r"(?:json)?\s*(.*?)" + FENCE, re.DOTALL)
text = FENCE + "\n" + '{"n": 1}' + "\n" + FENCE
match = REGEX.search(text)
print(bool(match))
print(repr(match.group(1)))
```

1. `True` နှင့် `'{"n": 1}'`
2. `True` နှင့် `'{"n": 1}\n'`
3. `False` — fence ထဲတွင် "json" မပါသဖြင့် မကိုက်
4. `False` — `\s*` က newline အားလုံးကို ဖြတ်သဖြင့် group 1 ကွက်လပ် ဖြစ်သည်

<details>
<summary>အဖြေ ကြည့်ရန်</summary>

**အဖြေ — 2. `True` နှင့် `'{"n": 1}\n'`**

အကြောင်းရင်း — `(?:json)?` သည် optional ဖြစ်သဖြင့် `json` မပါသော fence ကိုလည်း
ကိုက်ညီသည်။ `\s*` သည် fence နောက်က newline **တစ်လုံး** ကို ဖြတ်သည် (`*` သည်
greedy ဖြစ်သော်လည်း `(.*?)` က lazy ဖြစ်သဖြင့် အနည်းဆုံး ဖမ်းသည်)။ ထို့ကြောင့်
group(1) သည် `{"n": 1}\n` ဖြစ်သည် — နောက်ဆုံး newline သည် **ပါဝင်သည်**။

`strip_code_fence()` ကသာ `.strip()` ကို နောက်ဆုံးတွင် ခေါ်သဖြင့် trailing
newline ဖြတ်ခံရသည် — `CODE_FENCE_RE` ကိုယ်တိုင် မဖြတ်ပါ။

</details>

---

**အဓိက မှတ်ထားရန်** — LLM output ကို parse လုပ်ရာတွင် **defect အမျိုးအစားက
ကိုင်တွယ်ပုံကို သတ်မှတ်သည်**။ Fence နှင့် trailing comma သည် deterministic
ပြင်နိုင်သည်; truncation က မပြင်နိုင်ပါ — `None` ပြန်ပေးခြင်းသည် မှန်ကန်သော
အပြုအမူဖြစ်သည်။ Repair တိုင်းကို `repairs` list ဖြင့် မှတ်တမ်းတင်ခြင်းသည်
provenance ကို ထိန်းသည်။ `re.sub` ဖြင့် ပြင်ခြင်းသည် string အတွင်းက စာသားကို
မထိခိုက်စေရန် အာမခံချက် မရှိသဖြင့် repair ပြီးသည့်နောက် schema validation
မဖြစ်မနေ လိုအပ်သည်။ နောက်ဆုံးတွင် parse အောင်မြင်ခြင်းသည် **schema မှန်ကန်ခြင်းနှင့်
မတူ** ကြောင်း သတိထားရမည် — stage တိုင်းက မိမိတာဝန်သာ စစ်သည်။
