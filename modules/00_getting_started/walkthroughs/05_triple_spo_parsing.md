# Walkthrough 05 — Triple (SPO) Parsing (Exercise 5)

> ဤဖိုင်သည် `solution.md` ၏ Exercise 5 ကို **Python အခြေခံမှ စ၍** အပိုင်းလိုက် ရှင်းပြသည့်
> walkthrough ဖြစ်သည်။ Format သည် `walkthroughs/01_pipeline_stage_ordering.md` မှ
> `04_rag_failure_mode_classification.md` အထိ နှင့် တူညီသည်။

---

ဤ Exercise တွင် Python ကို အသုံးပြုပြီး text lines တွေထဲက Subject, Predicate, Object (SPO)
triples တွေကို parse လုပ်ခြင်း၊ သန့်စင်ခြင်း၊ validation လုပ်ခြင်းနှင့် duplicate records တွေကို
ဖယ်ရှားခြင်းကို လေ့လာပါမည်။

ဤ concept က RAG နှင့် GraphRAG system တွေအတွက် အရေးကြီးသည်။ သာမန် Vector Search က text
chunks တွေကို ရှာဖွေရန် အဓိကအသုံးပြုပေမဲ့၊ GraphRAG တွင် entities နှင့် သူတို့အကြား
relationships တွေကို structured triples အနေနှင့် သိမ်းဆည်းနိုင်သည်။

ဥပမာ IT knowledge base ထဲတွင် —

- Application A က Kubernetes Cluster B ပေါ်တွင် run နေသည်။
- Kubernetes Cluster B က Database C ကို ချိတ်ဆက်ထားသည်။
- Alice Chen က Acme Corp တွင် အလုပ်လုပ်သည်။

လို relationship တွေကို triples အနေနှင့် ကိုယ်စားပြုနိုင်သည်။

ဤ Exercise တွင် လေ့လာမည့် Python concepts များသည် `re` module၊ Regular Expressions၊
dataclass၊ `frozen=True`၊ function၊ `enumerate()`၊ tuple unpacking၊ `match.group()`၊
`continue`၊ `set()` နှင့် `sorted()` တို့ ဖြစ်သည်။

---

## 1. SPO Triple ဟူသည် ဘာလဲ။

SPO သည် —

- **S** — Subject: ဘယ်သူ သို့မဟုတ် ဘယ်အရာအကြောင်း ပြောနေလဲ။
- **P** — Predicate: Subject နှင့် Object ကြားက relationship သို့မဟုတ် ဆက်စပ်မှု။
- **O** — Object: Relationship နှင့် ဆက်စပ်နေသော အရာ သို့မဟုတ် entity။

ဥပမာ —

```text
Alice Chen | works_at | Acme Corp | chunk-02
```

ဤ line ကို အောက်ပါအတိုင်း အဓိပ္ပာယ်ဖော်နိုင်သည်။

| အစိတ်အပိုင်း | တန်ဖိုး | အဓိပ္ပာယ် |
| --- | --- | --- |
| Subject | `Alice Chen` | ဘယ်သူ/ဘယ်အရာအကြောင်း |
| Predicate | `works_at` | Relationship အမျိုးအစား |
| Object | `Acme Corp` | ဆက်စပ်နေသော entity |
| Source | `chunk-02` | ဤ triple ကို ထုတ်ယူခဲ့သည့် document chunk |

ဤနေရာတွင် `chunk-02` က SPO triple ၏ အစိတ်အပိုင်းသုံးခုထဲက တစ်ခု မဟုတ်ပါ။ Triple ကို
မည်သည့် source chunk မှ ထုတ်ယူထားသည်ကို မှတ်သားပေးသည့် **provenance information**
ဖြစ်သည်။

GraphRAG တွင် ဤသို့ triples တွေကို graph nodes နှင့် relationships တွေ ဖန်တီးရန်
အသုံးပြုနိုင်သည်။

---

## 2. `import re` နှင့် `from dataclasses import dataclass`

Code ၏ ပထမအပိုင်းက —

```python
import re
from dataclasses import dataclass
```

### `import re`

`re` က Python ၏ Regular Expression module ဖြစ်သည်။ Regular Expression (Regex) သည်
စာသားတွေတွင် သတ်မှတ်ထားသော pattern နှင့် ကိုက်ညီမှုရှိမရှိ ရှာဖွေ၊ စစ်ဆေး၊ ခွဲခြမ်းစိတ်ဖြာရန်
အသုံးပြုသည့် နည်းလမ်းဖြစ်သည်။

ဤ Exercise တွင် Regex ကို အသုံးပြုပြီး line တစ်ကြောင်းတွင် fields ၄ ခုကို `|` နှင့်
မှန်ကန်စွာ ခွဲထားခြင်း ရှိ/မရှိကို စစ်ဆေးပါမည်။

### `dataclass`

`dataclass` က data တွေကို သိမ်းဆည်းရန် ရည်ရွယ်ထားသော class တွေကို ပိုမိုလွယ်ကူစွာ
သတ်မှတ်နိုင်စေသည်။

ဥပမာ SPO triple တစ်ခုစီတွင် Subject၊ Predicate၊ Object နှင့် Source Chunk ဆိုသည့် fields
၄ ခု ပါဝင်သည်။ ထို fields တွေကို Python object အဖြစ် ကိုယ်စားပြုရန် dataclass ကို
အသုံးပြုမည်။

---

## 3. `TRIPLE_PATTERN` — Regex Pattern သတ်မှတ်ခြင်း

သင့်ပေးထားသော code ထဲတွင် Regex အပိုင်းကို Markdown formatting ကြောင့် အနည်းငယ်
ပျက်နေသည်။ Python တွင် အလုပ်လုပ်မည့် ပုံစံက ဤသို့ဖြစ်သည်။

```python
TRIPLE_PATTERN = re.compile(
    r"^(?P<s>[^|]+)\|(?P<p>[^|]+)\|(?P<o>[^|]+)\|(?P<c>[^|]+)$"
)
```

ဤ code က Regex pattern ကို compile လုပ်ပြီး `TRIPLE_PATTERN` variable ထဲတွင် သိမ်းထားခြင်း ဖြစ်သည်။
အခု Regex ကို အပိုင်းလိုက် ရှင်းပြပါမည်။

### 3.1 `r"..."` ဟူသည် ဘာလဲ။

```python
r"^(?P<s>[^|]+)..."
```

ရှေ့က `r` က **raw string** ဖြစ်သည်။ Regex ထဲတွင် `\` လို backslash ပါဝင်သည့် pattern တွေကို
ရေးသည့်အခါ အသုံးဝင်သည်။

ဥပမာ —

```python
r"\s+"
```

သည် Regex အတွက် `\s+` ကို မူရင်းပုံစံအတိုင်း ထိန်းထားပေးခြင်းဖြစ်သည်။

### 3.2 `^` နှင့် `$`

```text
^ ... $
```

ဤနှစ်ခုက စာသား၏ အစနှင့် အဆုံးကို ကိုယ်စားပြုသည်။

- `^` — စာသားအစ။
- `$` — စာသားအဆုံး။

ထို့ကြောင့် Regex တစ်ခုလုံးက line တစ်ကြောင်းလုံးကို သတ်မှတ်ထားသော pattern နှင့် ကိုက်ညီရပါမည်။

### 3.3 `(?P<s>...)` — Named Group

```python
(?P<s>[^|]+)
```

ဤအပိုင်းက စာသားထဲက field တစ်ခုကို match လုပ်ပြီး `s` ဆိုသည့်အမည်နှင့် သိမ်းပေးသည်။
Regex ၏ named group syntax က —

```text
(?P<name>...)
```

ဖြစ်သည်။ ဤ Exercise တွင် —

| Regex group | သိမ်းဆည်းမည့် field |
| --- | --- |
| `(?P<s>...)` | Subject |
| `(?P<p>...)` | Predicate |
| `(?P<o>...)` | Object |
| `(?P<c>...)` | Source chunk |

နောက်ပိုင်းတွင် `match.group("s")` ဟု ရေးပြီး Subject field ကို ပြန်ရယူနိုင်သည်။

### 3.4 `[^|]+` ဟူသည် ဘာလဲ။

```python
[^|]+
```

ဤတွင် Regex syntax နှစ်ခု ပါဝင်သည်။

- `[^|]` — `|` မဟုတ်သည့် character တစ်ခုကို match လုပ်ခြင်း။
- `+` — ထို character တစ်ခု သို့မဟုတ် တစ်ခုထက်ပိုပြီး ပါရမည်ဟု ဆိုလိုခြင်း။

ထို့ကြောင့် `[^|]+` က `|` မပါဝင်သည့် စာသားတစ်ခု သို့မဟုတ် တစ်ခုထက်ပိုသည့် စာသားကို
match လုပ်သည်။

ဥပမာ — `Alice Chen`၊ `works_at`၊ `Acme Corp`၊ `chunk-02` ဤသို့ fields တွေကို
match လုပ်နိုင်သည်။

သို့သော် empty field ဖြစ်နေသောအခါတော့ မကိုက်ညီပါ။

ဥပမာ —

```text
|empty_subject|Acme Corp|chunk-03
```

အစတွင် `|` မတိုင်ခင် subject field အလွတ်ဖြစ်နေသောအတွက် `[^|]+` က match မဖြစ်ပါ။

### 3.5 `\|` — Pipe character ကို match လုပ်ခြင်း

```python
\|
```

Regex တွင် `|` က အခြေအနေတစ်ခု သို့မဟုတ် အခြားတစ်ခု (alternation) ကို ကိုယ်စားပြုနိုင်သည့်
special character ဖြစ်သည်။ တကယ့် pipe symbol `|` ကိုသာ match လုပ်ချင်သည့်အတွက် `\|` ဟု
ရေးထားခြင်း ဖြစ်သည်။

Regex pattern တစ်ခုလုံးက အောက်ပါ field ပုံစံနှင့် ကိုက်ညီရန် စစ်ဆေးသည်။

```text
Subject|Predicate|Object|SourceChunk
```

---

## 4. `@dataclass(frozen=True)` — Triple Class

```python
@dataclass(frozen=True)
class Triple:
    subject: str
    predicate: str
    object: str
    source_chunk: str

    def to_spo(self):
        return "(%s)-[%s]->(%s)" % (
            self.subject,
            self.predicate,
            self.object,
        )
```

ဤ class က SPO triple တစ်ခုကို Python object တစ်ခုအနေနှင့် သိမ်းဆည်းပေးသည်။

### 4.1 `class Triple`

`Triple` ဆိုသည့် class အသစ်တစ်ခုကို သတ်မှတ်ခြင်း ဖြစ်သည်။ Class သည် data နှင့် ထို data တွေအပေါ်
လုပ်ဆောင်နိုင်သည့် methods တွေကို တစ်နေရာတည်းတွင် စုစည်းထားနိုင်သည့် ပုံစံတစ်ခု ဖြစ်သည်။

### 4.2 `subject: str`

```python
subject: str
predicate: str
object: str
source_chunk: str
```

ဤသို့ `: str` နှင့် ရေးထားခြင်းကို **type annotation** ဟု ခေါ်သည်။ ဤ fields တွေတွင်
string values တွေ သိမ်းရန် ရည်ရွယ်ထားကြောင်း ဖော်ပြသည်။

ဥပမာ —

```python
triple = Triple(
    "Alice Chen",
    "works_at",
    "Acme Corp",
    "chunk-02",
)
```

အခု `triple` ထဲတွင် field ၄ ခု ပါဝင်သည့် object တစ်ခု ရရှိသည်။ Field တစ်ခုချင်းစီကို
ဤသို့ ပြန်ဖတ်နိုင်သည်။

```python
triple = Triple(
    "Alice Chen",
    "works_at",
    "Acme Corp",
    "chunk-02",
)

print(triple.subject)
print(triple.predicate)
print(triple.object)
print(triple.source_chunk)
```

Output —

```text
Alice Chen
works_at
Acme Corp
chunk-02
```

`@dataclass` ကြောင့် ဤ fields တွေကို constructor ထဲတွင် သီးခြား `__init__()` method
ရေးစရာမလိုဘဲ သတ်မှတ်ထားသောအစီအစဉ်အတိုင်း arguments တွေပေးပြီး object ဖန်တီးနိုင်သည်။

### 4.3 `frozen=True`

```python
@dataclass(frozen=True)
```

ဤ option က `Triple` object ကို **immutable** အဖြစ် သတ်မှတ်ပေးသည်။ Object ဖန်တီးပြီးနောက်
field တန်ဖိုးတွေကို ပြင်ဆင်နိုင်ခြင်း မရှိတော့ပါ။

ဥပမာ —

```python
triple = Triple(
    "Alice Chen",
    "works_at",
    "Acme Corp",
    "chunk-02",
)
triple.subject = "Bob Ray"
```

ဤသို့ပြင်ဆင်လိုက်လျှင် `FrozenInstanceError` ဖြစ်လာပါမည်။

ဘာကြောင့် ဤသို့သတ်မှတ်ရခြင်းလဲ။ ဤ Exercise တွင် နောက်ပိုင်း `set(triples)` လုပ်ရန်
လိုအပ်သည်။ Default settings တွေနှင့် `@dataclass(frozen=True)` သုံးသည့်အခါ fields တွေက
hashable ဖြစ်နေသရွေ့ `Triple` objects တွေကို `set` ထဲ ထည့်နိုင်သည်။ ၎င်းသည် duplicate
`Triple` objects တွေကို ဖယ်ရှားရန် အသုံးဝင်သည်။

သတိပြုရန် — `frozen=True` က object ကို ပြင်ဆင်နိုင်ခြင်းမရှိအောင် ကန့်သတ်ပေးခြင်းဖြစ်ပြီး၊ fields
တွေထဲတွင် mutable objects တွေ ထည့်ထားလျှင် အတွင်းပိုင်းပြင်ဆင်မှုအားလုံးကို အလိုအလျောက်
ကာကွယ်ပေးခြင်း မဟုတ်ပါ။ ဤဥပမာတွင် fields အားလုံးက string တွေဖြစ်သောကြောင့် သင့်တော်သည်။

### 4.4 `to_spo()` method

```python
def to_spo(self):
    return "(%s)-[%s]->(%s)" % (
        self.subject,
        self.predicate,
        self.object,
    )
```

ဤ method က `Triple` object ကို ဖတ်ရလွယ်သည့် graph relationship format အဖြစ်
ပြောင်းပေးသည်။

ဥပမာ —

```python
triple = Triple(
    "Alice Chen",
    "works_at",
    "Acme Corp",
    "chunk-02",
)
print(triple.to_spo())
```

Output —

```text
(Alice Chen)-[works_at]->(Acme Corp)
```

ဤတွင် —

- `(Alice Chen)` — Subject node။
- `[works_at]` — Relationship။
- `(Acme Corp)` — Object node။

`source_chunk` ကို `to_spo()` ၏ output ထဲတွင် မထည့်ထားပါ။ ဤ method က graph
relationship ကိုသာ ဖော်ပြပေးခြင်း ဖြစ်သည်။

**အရေးကြီးချက်** — သင့်မူရင်း code တွင် `to_spo()` ကို သတ်မှတ်ထားပေမဲ့ နောက်ဆုံး `print()`
ထဲတွင် အသုံးပြုမထားပါ။ ထို့ကြောင့် မူရင်း output က `Triple` objects တွေကို
တိုက်ရိုက်ပြခြင်း မဟုတ်ဘဲ အရေအတွက်သုံးခုကိုသာ ပြသည်။

---

## 5. `_normalize(text)` — Text ကို သန့်စင်ခြင်း

```python
def _normalize(text):
    return re.sub(r"\s+", " ", text).strip()
```

ဤ function က field တစ်ခုချင်းစီ၏ whitespace တွေကို ပုံမှန်ဖြစ်အောင် ပြုပြင်ပေးသည်။

### 5.1 `re.sub()`

```python
re.sub(r"\s+", " ", text)
```

`re.sub()` က Regex pattern နှင့် ကိုက်ညီသည့် စာသားတွေကို သတ်မှတ်ထားသော replacement text နှင့်
အစားထိုးပေးသည်။

ဤတွင် —

- `r"\s+"` — Whitespace တစ်ခု သို့မဟုတ် တစ်ခုထက်ပိုခြင်းကို ရှာဖွေခြင်း။
- `" "` — Single space တစ်လုံးနှင့် အစားထိုးခြင်း။
- `text` — ပြုပြင်ရမည့် မူရင်းစာသား။

Whitespace သည် သာမန် space တင်မကဘဲ tab နှင့် newline လို စာသားကြားလပ်မှုတွေကိုလည်း
ဆိုလိုသည်။

ဥပမာ —

```python
import re

text = "Alice    Chen\tworks_at"

print(re.sub(r"\s+", " ", text))
```

Output —

```text
Alice Chen works_at
```

Space အများအပြားနှင့် tab ကို single spaces တွေအဖြစ် ပြောင်းထားသည်။

### 5.2 `.strip()`

```python
.strip()
```

`strip()` က စာသား၏ အစနှင့် အဆုံးတွင်ရှိသည့် whitespace တွေကို ဖယ်ရှားပေးသည်။

ဥပမာ —

```python
text = "   Alice Chen   "

print(text.strip())
```

Output —

```text
Alice Chen
```

ထို့ကြောင့် —

```python
def _normalize(text):
    return re.sub(r"\s+", " ", text).strip()
```

သည် whitespace အများအပြားကို single space ပြောင်းပေးပြီး အစနှင့်အဆုံးက whitespace တွေကို
ဖယ်ရှားပေးသည်။

`_normalize` ၏ ရှေ့တွင် underscore `_` ထည့်ထားခြင်းက ဤ function သည် module အတွင်းသုံးသည့်
helper function ဖြစ်ကြောင်း ဖော်ပြသည့် Python naming convention ဖြစ်သည်။

---

## 6. `parse_triples(lines)` — Main Parsing Function

အခု Exercise ၏ အဓိက function ကို လေ့လာကြည့်ကြပါမည်။

```python
def parse_triples(lines):
    triples = []
    errors = []
    for line_number, raw in enumerate(lines, start=1):
        match = TRIPLE_PATTERN.match(raw.strip())
        if match is None:
            errors.append((line_number, "malformed_field_count"))
            continue
        subject = _normalize(match.group("s"))
        predicate = _normalize(match.group("p")).lower().replace(" ", "_")
        obj = _normalize(match.group("o"))
        chunk = _normalize(match.group("c"))
        if not subject or not predicate or not obj or not chunk:
            errors.append((line_number, "empty_field"))
            continue
        triples.append(Triple(subject, predicate, obj, chunk))
    return triples, errors
```

ဤ function ၏ ရည်ရွယ်ချက်က input lines တွေကို စစ်ဆေးပြီး မှန်ကန်သော triples တွေကို
တစ်စု၊ errors တွေကို တစ်စု ခွဲထုတ်ပေးရန် ဖြစ်သည်။

### 6.1 `triples = []` နှင့် `errors = []`

```python
triples = []
errors = []
```

ဤနေရာတွင် empty lists နှစ်ခု ဖန်တီးထားသည်။

- `triples` — မှန်ကန်သော `Triple` objects တွေကို သိမ်းရန်။
- `errors` — Parse မအောင်မြင်သည့် line တွေကို မှတ်တမ်းတင်ရန်။

ဥပမာ —

```python
triples = []
errors = []

triples.append("valid data")
errors.append((5, "malformed_field_count"))
```

`append()` က list ၏ အဆုံးတွင် item အသစ်ထည့်ပေးသည်။

### 6.2 `enumerate(lines, start=1)`

```python
for line_number, raw in enumerate(lines, start=1):
```

ဤတွင် `enumerate()` ကို အသုံးပြုပြီး line တစ်ခုချင်းစီနှင့် အတူ line number ကိုပါ ရယူသည်။

ဥပမာ —

```python
lines = [
    "First line",
    "Second line",
    "Third line",
]

for line_number, raw in enumerate(lines, start=1):
    print(line_number, raw)
```

Output —

```text
1 First line
2 Second line
3 Third line
```

`start=1` ထည့်ထားခြင်းကြောင့် numbering ကို `1` ကနေ စသည်။ Default အနေနှင့်တော့ `0`
ကနေ စမည်။ ဤ Exercise တွင် line number ကို အသုံးပြုပြီး ဘယ် line တွင် error ဖြစ်ခြင်း
မှတ်တမ်းတင်နိုင်သည်။

### 6.3 `raw.strip()` နှင့် Regex match

```python
match = TRIPLE_PATTERN.match(raw.strip())
```

ပထမဆုံး `raw.strip()` က line ၏ အစနှင့် အဆုံးက whitespace တွေကို ဖယ်ရှားသည်။

ဥပမာ —

```python
raw = "  Acme Corp | founded_in | Cupertino | chunk-01 "

print(raw.strip())
```

Output —

```text
Acme Corp | founded_in | Cupertino | chunk-01
```

ပြီးလျှင် —

```python
TRIPLE_PATTERN.match(...)
```

က Regex pattern နှင့် ကိုက်ညီမှုရှိမရှိ စစ်ဆေးသည်။ Pattern ကိုက်ညီလျှင် match object တစ်ခု
ပြန်ရသည်။ မကိုက်ညီလျှင် `None` ပြန်ရသည်။

### 6.4 `if match is None`

```python
if match is None:
    errors.append((line_number, "malformed_field_count"))
    continue
```

Regex pattern နှင့် line တစ်ကြောင်းလုံး ကိုက်ညီမှုမရှိလျှင် error အဖြစ် မှတ်တမ်းတင်သည်။

ဥပမာ —

```text
Broken|line
```

ဤ line တွင် fields နှစ်ခုသာ ရှိသည်။ သို့သော် Regex က field ၄ ခုကို မျှော်လင့်ထားသောအတွက်
match မဖြစ်ပါ။ ထို့ကြောင့် —

```python
errors.append((5, "malformed_field_count"))
```

လို မှတ်တမ်းဝင်သည်။ ဤ tuple တွင် —

- `5` — Error ဖြစ်သည့် line number။
- `"malformed_field_count"` — Error အမျိုးအစား။

`continue` က လက်ရှိ iteration ၏ ကျန်ရှိသည့် code တွေကို ကျော်ပြီး နောက် line ကို
ဆက်စစ်စေသည်။ ထို့ကြောင့် match မဖြစ်သော line တွေကို `Triple` အဖြစ် ဖန်တီးရန်
မကြိုးစားတော့ပါ။

---

## 7. `match.group()` နှင့် Fields တွေကို ထုတ်ယူခြင်း

Regex match အောင်မြင်သွားလျှင် fields တွေကို ထုတ်ယူသည်။

```python
subject = _normalize(match.group("s"))
predicate = _normalize(match.group("p")).lower().replace(" ", "_")
obj = _normalize(match.group("o"))
chunk = _normalize(match.group("c"))
```

`match.group("s")` က Regex ထဲက `s` named group နှင့် match ဖြစ်သည့် စာသားကို ပြန်ပေးသည်။
အလားတူ —

- `match.group("p")` — Predicate။
- `match.group("o")` — Object။
- `match.group("c")` — Source chunk။

### 7.1 Subject ကို Normalize လုပ်ခြင်း

```python
subject = _normalize(match.group("s"))
```

ဥပမာ input ထဲတွင် `"  Acme Corp "` ဆိုလျှင် normalize လုပ်ပြီး `Acme Corp` ဖြစ်လာသည်။

### 7.2 Predicate ကို Normalize လုပ်ခြင်း

```python
predicate = _normalize(match.group("p")).lower().replace(" ", "_")
```

ဤတစ်ကြောင်းတွင် operations သုံးခုကို အစဉ်လိုက် လုပ်သည်။

ပထမ —

```python
_normalize(match.group("p"))
```

Whitespace တွေကို သန့်စင်သည်။

ဒုတိယ —

```python
.lower()
```

စာလုံးတွေကို lowercase ပြောင်းသည်။

```python
print("WORKS_AT".lower())
```

Output —

```text
works_at
```

တတိယ —

```python
.replace(" ", "_")
```

Space တွေကို underscore `_` နှင့် အစားထိုးသည်။

```python
print("reports to".replace(" ", "_"))
```

Output —

```text
reports_to
```

ထို့ကြောင့် Predicate ကို lowercase ဖြစ်အောင်နှင့် spaces တွေကို underscores ပြောင်းပြီး
တစ်သမတ်တည်း ဖြစ်အောင် သန့်စင်ထားခြင်း ဖြစ်သည်။

သတိပြုရန် — `.replace(" ", "_")` က single space character တွေကို အစားထိုးခြင်းဖြစ်သောကြောင့်
ပထမဆုံး `_normalize()` လုပ်ထားခြင်း အရေးကြီးသည်။

### 7.3 Object နှင့် Source Chunk

```python
obj = _normalize(match.group("o"))
chunk = _normalize(match.group("c"))
```

ဤနှစ်ခုလည်း အလားတူ normalization ကို လုပ်ပေးသည်။

ဤ Exercise တွင် Predicate ကို lowercase ပြောင်းပေမဲ့ Subject နှင့် Object ကို lowercase
ပြောင်းမထားပါ။ ထို့ကြောင့် `Acme Corp` က `Acme Corp` အတိုင်းသာ ကျန်နေပါမည်။

---

## 8. Empty Field Validation

```python
if not subject or not predicate or not obj or not chunk:
    errors.append((line_number, "empty_field"))
    continue
```

ဤ condition က normalize လုပ်ပြီးနောက် fields တစ်ခုခု empty ဖြစ်နေသလား စစ်ဆေးသည်။
Python တွင် empty string `""` က falsy ဖြစ်သည်။

```python
print(bool(""))
print(bool("Alice"))
```

Output —

```text
False
True
```

ထို့ကြောင့် —

```python
if not subject:
```

သည် `subject` က empty string ဖြစ်နေသလား စစ်ခြင်း ဖြစ်သည်။

ဤနေရာတွင် `or` ကို သုံးထားသောအတွက် fields ၄ ခုထဲက တစ်ခုခု empty ဖြစ်လျှင် condition
တစ်ခုလုံး `True` ဖြစ်သည်။ ထိုအခါ —

```python
errors.append((line_number, "empty_field"))
continue
```

နှင့် error ကို မှတ်တမ်းတင်ပြီး နောက် line ကို ဆက်စစ်သည်။

### အရေးကြီးသော Regex အချက်တစ်ခု

သင့်မူရင်း Regex တွင် `[^|]+` ကို သုံးထားသည်။ `+` က field ထဲတွင် အနည်းဆုံး character
တစ်ခု ပါရမည်ဟု သတ်မှတ်ထားသောအတွက် တကယ့် empty field ကို Regex က အစောပိုင်းတွင်သာ
ပယ်ချလိုက်သည်။

ထို့ကြောင့် —

```text
|empty_subject|Acme Corp|chunk-03
```

ဤသို့ line သည် `empty_field` အဆင့်ကို မရောက်ဘဲ `match is None` အပိုင်းတွင်
`malformed_field_count` အဖြစ် မှတ်တမ်းဝင်သည်။

တကယ့် empty fields တွေကို သီးခြား `empty_field` error အဖြစ် ခွဲခြားချင်လျှင် Regex ထဲက
`+` ကို `*` နှင့် ပြောင်းနိုင်သည်။

```python
TRIPLE_PATTERN = re.compile(
    r"^(?P<s>[^|]*)\|(?P<p>[^|]*)\|(?P<o>[^|]*)\|(?P<c>[^|]*)$"
)
```

`*` က character သုညခု သို့မဟုတ် အများကြီးကို ခွင့်ပြုခြင်းကြောင့် empty field ကိုလည်း
match လုပ်နိုင်သည်။ ထို့နောက် `if not subject ...` validation က `empty_field` ကို
ရှာဖွေပေးနိုင်သည်။

ဤပြောင်းလဲမှုက မူရင်း code ၏ စုစုပေါင်း valid records နှင့် error counts ကို
မပြောင်းလဲစေပေမဲ့၊ error အမျိုးအစားအလိုက် မှတ်တမ်းတင်ပုံကို ပြောင်းလဲစေသည်။

---

## 9. `triples.append(Triple(...))`

```python
triples.append(Triple(subject, predicate, obj, chunk))
```

Fields တွေ အားလုံး valid ဖြစ်ပြီဆိုလျှင် `Triple` object တစ်ခု ဖန်တီးပြီး `triples` list ထဲ
ထည့်သည်။

ဥပမာ —

```python
Triple(
    "Acme Corp",
    "founded_in",
    "Cupertino",
    "chunk-01",
)
```

ဤ object က အောက်ပါ information တွေကို သိမ်းထားသည်။

| Field | Value |
| --- | --- |
| `subject` | `Acme Corp` |
| `predicate` | `founded_in` |
| `object` | `Cupertino` |
| `source_chunk` | `chunk-01` |

`triples.append(...)` က ဤ object ကို list ထဲ ထည့်သည်။ ထို့ကြောင့် valid line တစ်ကြောင်းကို
အောင်မြင်စွာ parse လုပ်တိုင်း `triples` list ၏ အရွယ်အစား တစ်ခုတိုးလာသည်။

---

## 10. `return triples, errors`

```python
return triples, errors
```

Function က result နှစ်ခုကို တစ်ပြိုင်နက် ပြန်ပေးသည်။

- `triples` — Parse လုပ်ထားသော valid `Triple` objects။
- `errors` — Parse မအောင်မြင်သည့် lines တွေ၏ error records။

Python တွင် comma ခွဲပြီး values အများအပြားကို `return` လုပ်သည့်အခါ tuple တစ်ခုအဖြစ်
ပြန်ရရှိသည်။ ထို့ကြောင့် —

### Unpacking ဖြင့် လက်ခံခြင်း

```python
triples, errors = parse_triples(TRIPLE_LINES)
```

တွင် function က ပြန်ပေးသည့် tuple ကို variable နှစ်ခုထဲ unpack လုပ်ထားခြင်း ဖြစ်သည်။

- ပထမ value ကို `triples` ထဲ သိမ်းသည်။
- ဒုတိယ value ကို `errors` ထဲ သိမ်းသည်။

ဤသို့ပုံစံကို အရင် Exercises တွေတွင်လည်း တွေ့ခဲ့သည်။ ဥပမာ Exercise 4 တွင် tuple
unpacking ကို အသုံးပြုပြီး `query_id` နှင့် `features` ကို ခွဲယူခဲ့သည်။

---

## 11. `TRIPLE_LINES` — Input Test Data

```python
TRIPLE_LINES = [
    "  Acme Corp | founded_in | Cupertino | chunk-01 ",
    "Acme Corp|founded_in|Cupertino|chunk-01",
    "Alice Chen|works_at|Acme Corp|chunk-02",
    "Alice Chen | reports_to | Bob Ray | chunk-02",
    "Broken|line",
    "|empty_subject|Acme Corp|chunk-03",
]
```

ဤ list ထဲတွင် input lines ခြောက်ကြောင်း ပါဝင်သည်။ တစ်ကြောင်းချင်းစီကို
စစ်ဆေးကြည့်ကြပါမည်။

| Line | စစ်ဆေးချက် | ရလဒ် |
| --- | --- | --- |
| 1 | Field ၄ ခုရှိပြီး normalize လုပ်နိုင်သည် | Valid Triple |
| 2 | Line 1 နှင့် normalize ပြီးနောက် တူညီသည် | Valid Triple၊ နောက်ပိုင်း duplicate ဖြစ်မည် |
| 3 | SPO နှင့် chunk fields မှန်ကန်သည် | Valid Triple |
| 4 | Fields မှန်ကန်ပြီး Predicate ကို normalize လုပ်မည် | Valid Triple |
| 5 | Fields နှစ်ခုသာရှိသည် | Error |
| 6 | Subject field အလွတ်ဖြစ်နေသည် | Regex match မဖြစ်သောကြောင့် Error |

ဤ input တွင် ပထမ line က ရှေ့နောက် spaces အချို့ ပါဝင်ပေမဲ့ normalization လုပ်ပြီးနောက်
ဒုတိယ line နှင့် တူညီသွားသည်။ ထို့ကြောင့် valid `Triple` objects ၄ ခုကို
ဖန်တီးထားပေမဲ့ unique triples အရေအတွက်က သုံးခုသာ ရှိပါမည်။

---

## 12. `unique = sorted(set(triples), key=...)`

```python
unique = sorted(
    set(triples),
    key=lambda t: (
        t.subject,
        t.predicate,
        t.object,
        t.source_chunk,
    ),
)
```

ဤတစ်ကြောင်းက duplicate `Triple` objects တွေကို ဖယ်ရှားပြီး အစီအစဉ်တကျ ပြန်စီပေးသည်။

### 12.1 `set(triples)`

`set()` က unique values တွေကို သိမ်းဆည်းပေးသည့် data structure ဖြစ်သည်။

ဥပမာ —

```python
items = ["apple", "banana", "apple", "orange"]

print(set(items))
```

Output တွင် `"apple"` ကို တစ်ခုသာ ထားပါမည်။

```text
{'apple', 'orange', 'banana'}
```

Set က insertion order ကို အခြေခံထားသော display order ကို အာမမခံပါ — အပေါ်က
အစီအစဉ်သည် run တစ်ခုနှင့်တစ်ခု ကွဲနိုင်သည်။

ဤ Exercise တွင် `Triple` ကို `@dataclass(frozen=True)` နှင့် ဖန်တီးထားသောအတွက် fields
တန်ဖိုးအားလုံး တူညီသော objects တွေကို `set` က duplicate အဖြစ် သတ်မှတ်နိုင်သည်။

ပထမနှင့် ဒုတိယ line တွေကို normalization လုပ်ပြီးသည့်အခါ object နှစ်ခုစလုံး၏ fields တွေက —

```python
Triple(
    "Acme Corp",
    "founded_in",
    "Cupertino",
    "chunk-01",
)
```

အတိုင်း တူညီနေသည်။ ထို့ကြောင့် `set(triples)` လုပ်သည့်အခါ ထို duplicate နှစ်ခုထဲက
တစ်ခုသာ ကျန်သည်။

သတိပြုရန် — ဤ code က Subject၊ Predicate၊ Object နှင့် `source_chunk` ၄ ခုစလုံး
တူညီသော `Triple` objects တွေကိုသာ duplicate အဖြစ် သတ်မှတ်သည်။ SPO သုံးခုတူပေမဲ့
source chunk မတူလျှင် objects တွေက မတူညီသေးသည့်အတွက် နှစ်ခုစလုံးကို ထိန်းထားပါမည်။

### 12.2 `sorted(...)`

Set ထဲတွင် unique `Triple` objects တွေ ကျန်ပြီဆိုလျှင် `sorted()` နှင့် စီစဉ်သည်။

```python
key=lambda t: (
    t.subject,
    t.predicate,
    t.object,
    t.source_chunk,
)
```

ဤ lambda function က `Triple` object တစ်ခုချင်းစီအတွက် sorting key ကို ပြန်ပေးသည်။
Sorting အတွက် အစဉ်လိုက် ကြည့်မည့် fields တွေက —

- `t.subject`
- `t.predicate`
- `t.object`
- `t.source_chunk`

ဥပမာ Subject တူညီသော triples နှစ်ခုရှိလျှင် Predicate ကို ထပ်စစ်မည်။ Predicate လည်း
တူလျှင် Object ကို ထပ်စစ်မည်။ ထိုနောက် Source chunk ကို စစ်သည်။

ဤသို့လုပ်ထားခြင်းကြောင့် input lines တွေကို အစဉ်မတူအောင် ပေးထားလည်း sorting key တူညီသော
data တွေအတွက် ရလဒ်ကို တစ်သမတ်တည်း ထိန်းသိမ်းနိုင်သည်။

ဤ Exercise အတွက် ရရှိလာသည့် အစီအစဉ်က —

```text
(Acme Corp)-[founded_in]->(Cupertino) | chunk-01
(Alice Chen)-[reports_to]->(Bob Ray) | chunk-02
(Alice Chen)-[works_at]->(Acme Corp) | chunk-02
```

ဖြစ်သည် — `reports_to` သည် `works_at` ထက် alphabetical order အရ အရင်ရောက်သည်။

---

## 13. နောက်ဆုံး `print()` ကို နားလည်ခြင်း

```python
print(len(triples), len(errors), len(triples) - len(unique))
```

ဤတစ်ကြောင်းက ကိန်းဂဏန်းသုံးခုကို ပြသသည်။

### ပထမတန်ဖိုး — `len(triples)`

`triples` list ထဲတွင် valid `Triple` objects မည်မျှ ရှိသည်ကို ပြန်ပေးသည်။ Line 1၊ 2၊
3၊ 4 တို့က valid ဖြစ်သည့်အတွက် `4` ဖြစ်သည်။

### ဒုတိယတန်ဖိုး — `len(errors)`

`errors` list ထဲတွင် invalid lines မည်မျှ ရှိသည်ကို ပြန်ပေးသည်။ Line 5 နှင့် 6 တို့တွင်
Regex match မဖြစ်သောအတွက် `2` ဖြစ်သည်။

### တတိယတန်ဖိုး — `len(triples) - len(unique)`

Valid `Triple` objects အရေအတွက်ထဲက unique objects အရေအတွက်ကို နုတ်ထားသည်။

```text
Valid triples  = 4
Unique triples = 3
```

ထို့ကြောင့် `4 - 3 = 1` ဆိုပြီး duplicate အဖြစ် ဖယ်ရှားလိုက်သည့် extra record အရေအတွက်ကို
ပြသည်။

ဤတန်ဖိုးက duplicate records အားလုံးကို စုစုပေါင်းဖယ်ရှားလိုက်သည့် အရေအတွက် ဖြစ်သည်။ ဥပမာ
record တစ်ခုက သုံးကြိမ်ပါနေလျှင် ထို record အတွက် duplicate အပိုနှစ်ခုကို ဖယ်ရှားတွင်
ဖြစ်သည်။

### Expected Output

```text
4 2 1
```

အဓိပ္ပာယ်က —

- `4` — Valid records ၄ ခုကို parse လုပ်နိုင်ခဲ့သည်။
- `2` — Invalid lines နှစ်ကြောင်းကို error အဖြစ် မှတ်တမ်းတင်ခဲ့သည်။
- `1` — Duplicate record တစ်ခုကို ဖယ်ရှားနိုင်ခဲ့သည်။

---

## 14. Code တစ်ခုလုံး — သန့်စင်ပြီး Run လုပ်နိုင်သော Version

အောက်တွင် ဤ Exercise ၏ runnable version ကို စုစည်းပေးထားသည်။ မူရင်း logic ကို
ထိန်းထားပြီး code formatting ကို ပြင်ဆင်ထားသည်။

```python
import re
from dataclasses import dataclass

TRIPLE_PATTERN = re.compile(
    r"^(?P<s>[^|]+)\|(?P<p>[^|]+)\|(?P<o>[^|]+)\|(?P<c>[^|]+)$"
)

@dataclass(frozen=True)
class Triple:
    subject: str
    predicate: str
    object: str
    source_chunk: str

    def to_spo(self):
        return "(%s)-[%s]->(%s)" % (
            self.subject,
            self.predicate,
            self.object,
        )

def _normalize(text):
    return re.sub(r"\s+", " ", text).strip()

def parse_triples(lines):
    triples = []
    errors = []
    for line_number, raw in enumerate(lines, start=1):
        match = TRIPLE_PATTERN.match(raw.strip())
        if match is None:
            errors.append((line_number, "malformed_field_count"))
            continue
        subject = _normalize(match.group("s"))
        predicate = _normalize(match.group("p")).lower().replace(" ", "_")
        obj = _normalize(match.group("o"))
        chunk = _normalize(match.group("c"))
        if not subject or not predicate or not obj or not chunk:
            errors.append((line_number, "empty_field"))
            continue
        triples.append(Triple(subject, predicate, obj, chunk))
    return triples, errors

TRIPLE_LINES = [
    "  Acme Corp | founded_in | Cupertino | chunk-01 ",
    "Acme Corp|founded_in|Cupertino|chunk-01",
    "Alice Chen|works_at|Acme Corp|chunk-02",
    "Alice Chen | reports_to | Bob Ray | chunk-02",
    "Broken|line",
    "|empty_subject|Acme Corp|chunk-03",
]

triples, errors = parse_triples(TRIPLE_LINES)
unique = sorted(set(triples), key=lambda t: (t.subject, t.predicate, t.object, t.source_chunk))

print(len(triples), len(errors), len(triples) - len(unique))
```

Output —

```text
4 2 1
```

---

## 15. ဤ Exercise က RAG / GraphRAG တွင် ဘယ်လိုအသုံးဝင်သလား။

ဤ Exercise က text chunks တွေထဲက relationship information ကို structured data အဖြစ်
ပြောင်းရန် အခြေခံပုံစံတစ်ခုကို ပြသထားသည်။

1. **Raw documents** — Knowledge base ထဲက မူရင်းစာသားများ
2. **Triple extraction** — Subject၊ Predicate၊ Object နှင့် source chunk ကို ခွဲထုတ်ခြင်း
3. **Normalization + Validation** — Whitespace သန့်စင်ခြင်း၊ fields စစ်ဆေးခြင်း
4. **Deduplication** — တူညီသော `Triple` objects များကို ဖယ်ရှားခြင်း
5. **Knowledge Graph** — Validated triples များဖြင့် entities နှင့် relationships ကို တည်ဆောက်ခြင်း

ဤ code က triple parsing နှင့် validation ကိုသာ လုပ်ဆောင်ထားခြင်းဖြစ်ပြီး Graph database
ထဲကို တကယ်သိမ်းဆည်းခြင်း မလုပ်သေးပါ။ Production GraphRAG pipeline တွင် entity
resolution၊ relation validation၊ source tracking နှင့် database writes တွေကို ထပ်မံ
တည်ဆောက်ရန် လိုအပ်သည်။

### ကိုယ်တိုင်လေ့ကျင့်ကြည့်ပါ

**မေးခွန်း** — အောက်ပါ line ကို `parse_triples()` ထဲ ထည့်လိုက်လျှင် ဘယ် list ထဲ
ရောက်မလဲ။

```text
Network Team|manages|Core Switch 01
```

1. `triples` — Valid Triple အဖြစ်
2. `errors` — `malformed_field_count` အဖြစ်
3. `errors` — `empty_field` အဖြစ်
4. Field ၄ ခုရှိသောကြောင့် နှစ်ခုလုံးထဲ ရောက်မည်

<details>
<summary>အဖြေ ကြည့်ရန်</summary>

**အဖြေ — 2. `errors` — `malformed_field_count` အဖြစ်**

အကြောင်းရင်း — Regex သည် `Subject|Predicate|Object|SourceChunk` ဆိုသည့် field
**၄ ခု**ကို မျှော်လင့်သည်။ ဤ line တွင် field သုံးခုသာ ရှိသဖြင့် — `|` သုံးခု
(`Network Team`၊ `manages`၊ `Core Switch 01`) — `TRIPLE_PATTERN.match()` သည်
`None` ပြန်သည်။ ထို့ကြောင့် `match is None` branch သို့ ရောက်ပြီး
`malformed_field_count` အဖြစ် မှတ်တမ်းဝင်သည်။

Source chunk အပိုင်း ထည့်လိုက်ပါက valid `Triple` ဖြစ်သွားမည် —

```text
Network Team|manages|Core Switch 01|chunk-04
```

</details>

**အဓိက မှတ်ထားရန်** — ဤ Exercise တွင် Regex က line format ကို စစ်ဆေးသည်။
`Triple` dataclass က SPO data ကို object အဖြစ် သိမ်းဆည်းသည်။ `_normalize()` က
whitespace နှင့် predicate စာလုံးပုံစံကို တစ်သမတ်တည်း ပြုပြင်ပေးသည်။
`parse_triples()` က valid records နှင့် errors တွေကို ခွဲထုတ်သည်။ နောက်ဆုံး `set()` နှင့်
`sorted()` ကို သုံးပြီး duplicate records တွေကို ဖယ်ရှားကာ unique triples တွေကို
အစီအစဉ်တကျ ပြင်ဆင်ပေးသည်။
