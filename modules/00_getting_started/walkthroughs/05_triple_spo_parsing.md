# Walkthrough 05 — Triple (SPO) Parsing (Exercise 5)

> ဤဖိုင်သည် `solution.md` ၏ Exercise 5 ကို **Python အခြေခံမှ စ၍** အပိုင်းလိုက် ရှင်းပြသည့်
> walkthrough ဖြစ်သည်။ Format သည် `walkthroughs/01_pipeline_stage_ordering.md` မှ
> `04_rag_failure_mode_classification.md` အထိ နှင့် တူညီသည်။

---

ဒီ Exercise မှာ Python ကို အသုံးပြုပြီး text lines တွေထဲက Subject, Predicate, Object (SPO)
triples တွေကို parse လုပ်ခြင်း၊ သန့်စင်ခြင်း၊ validation လုပ်ခြင်းနဲ့ duplicate records တွေကို
ဖယ်ရှားခြင်း ကို လေ့လာပါမယ်။

ဒီ concept က RAG နဲ့ GraphRAG system တွေအတွက် အရေးကြီးပါတယ်။ သာမန် Vector Search က text
chunks တွေကို ရှာဖွေဖို့ အဓိကအသုံးပြုပေမဲ့၊ GraphRAG မှာတော့ entities နဲ့ သူတို့အကြား
relationships တွေကို structured triples အနေနဲ့ သိမ်းဆည်းနိုင်ပါတယ်။

ဥပမာ IT knowledge base ထဲမှာ —

- Application A က Kubernetes Cluster B ပေါ်မှာ run နေတယ်။
- Kubernetes Cluster B က Database C ကို ချိတ်ဆက်ထားတယ်။
- Alice Chen က Acme Corp မှာ အလုပ်လုပ်တယ်။

လို relationship တွေကို triples အနေနဲ့ ကိုယ်စားပြုနိုင်ပါတယ်။

ဒီ Exercise မှာ လေ့လာမယ့် Python concepts တွေကတော့ `re` module၊ Regular Expressions၊
dataclass၊ `frozen=True`၊ function၊ `enumerate()`၊ tuple unpacking၊ `match.group()`၊
`continue`၊ `set()` နဲ့ `sorted()` တို့ ဖြစ်ပါတယ်။

---

## 1. SPO Triple ဆိုတာဘာလဲ။

SPO ဆိုတာ —

- **S** — Subject: ဘယ်သူ သို့မဟုတ် ဘယ်အရာအကြောင်း ပြောနေလဲ။
- **P** — Predicate: Subject နဲ့ Object ကြားက relationship သို့မဟုတ် ဆက်စပ်မှု။
- **O** — Object: Relationship နဲ့ ဆက်စပ်နေတဲ့ အရာ သို့မဟုတ် entity။

ဥပမာ —

```text
Alice Chen | works_at | Acme Corp | chunk-02
```

ဒီ line ကို အောက်ပါအတိုင်း အဓိပ္ပာယ်ဖော်နိုင်ပါတယ်။

| အစိတ်အပိုင်း | တန်ဖိုး | အဓိပ္ပာယ် |
| --- | --- | --- |
| Subject | `Alice Chen` | ဘယ်သူ/ဘယ်အရာအကြောင်း |
| Predicate | `works_at` | Relationship အမျိုးအစား |
| Object | `Acme Corp` | ဆက်စပ်နေတဲ့ entity |
| Source | `chunk-02` | ဤ triple ကို ထုတ်ယူခဲ့တဲ့ document chunk |

ဒီနေရာမှာ `chunk-02` က SPO triple ရဲ့ အစိတ်အပိုင်းသုံးခုထဲက တစ်ခု မဟုတ်ပါဘူး။ Triple ကို
ဘယ် source chunk ကနေ ထုတ်ယူထားသလဲဆိုတာ မှတ်သားပေးတဲ့ **provenance information**
ဖြစ်ပါတယ်။

GraphRAG မှာ ဒီလို triples တွေကို graph nodes နဲ့ relationships တွေ ဖန်တီးဖို့
အသုံးပြုနိုင်ပါတယ်။

---

## 2. `import re` နဲ့ `from dataclasses import dataclass`

Code ရဲ့ ပထမအပိုင်းက —

```python
import re
from dataclasses import dataclass
```

### `import re`

`re` က Python ရဲ့ Regular Expression module ဖြစ်ပါတယ်။ Regular Expression (Regex) ဆိုတာ
စာသားတွေမှာ သတ်မှတ်ထားတဲ့ pattern နဲ့ ကိုက်ညီမှုရှိမရှိ ရှာဖွေ၊ စစ်ဆေး၊ ခွဲခြမ်းစိတ်ဖြာဖို့
အသုံးပြုတဲ့ နည်းလမ်းဖြစ်ပါတယ်။

ဒီ Exercise မှာ Regex ကို အသုံးပြုပြီး line တစ်ကြောင်းမှာ fields လေးခုကို `|` နဲ့
မှန်ကန်စွာ ခွဲထားသလားဆိုတာ စစ်ဆေးပါမယ်။

### `dataclass`

`dataclass` က data တွေကို သိမ်းဆည်းဖို့ ရည်ရွယ်ထားတဲ့ class တွေကို ပိုမိုလွယ်ကူစွာ
သတ်မှတ်နိုင်စေပါတယ်။

ဥပမာ SPO triple တစ်ခုစီမှာ Subject၊ Predicate၊ Object နဲ့ Source Chunk ဆိုတဲ့ fields
လေးခု ပါဝင်ပါတယ်။ အဲဒီ fields တွေကို Python object အဖြစ် ကိုယ်စားပြုဖို့ dataclass ကို
အသုံးပြုမှာပါ။

---

## 3. `TRIPLE_PATTERN` — Regex Pattern သတ်မှတ်ခြင်း

သင့်ပေးထားတဲ့ code ထဲမှာ Regex အပိုင်းကို Markdown formatting ကြောင့် အနည်းငယ်
ပျက်နေပါတယ်။ Python မှာ အလုပ်လုပ်မယ့် ပုံစံက ဒီလိုဖြစ်ပါတယ်။

```python
TRIPLE_PATTERN = re.compile(
    r"^(?P<s>[^|]+)\|(?P<p>[^|]+)\|(?P<o>[^|]+)\|(?P<c>[^|]+)$"
)
```

ဒီ code က Regex pattern ကို compile လုပ်ပြီး `TRIPLE_PATTERN` variable ထဲမှာ သိမ်းထားတာပါ။
အခု Regex ကို အပိုင်းလိုက် ရှင်းပြပါမယ်။

### 3.1 `r"..."` ဆိုတာဘာလဲ။

```python
r"^(?P<s>[^|]+)..."
```

ရှေ့က `r` က **raw string** ဖြစ်ပါတယ်။ Regex ထဲမှာ `\` လို backslash ပါဝင်တဲ့ pattern တွေကို
ရေးတဲ့အခါ အသုံးဝင်ပါတယ်။

ဥပမာ —

```python
r"\s+"
```

ဆိုတာ Regex အတွက် `\s+` ကို မူရင်းပုံစံအတိုင်း ထိန်းထားပေးတာဖြစ်ပါတယ်။

### 3.2 `^` နဲ့ `$`

```text
^ ... $
```

ဒီနှစ်ခုက စာသားရဲ့ အစနဲ့ အဆုံးကို ကိုယ်စားပြုပါတယ်။

- `^` — စာသားအစ။
- `$` — စာသားအဆုံး။

ဒါကြောင့် Regex တစ်ခုလုံးက line တစ်ကြောင်းလုံးကို သတ်မှတ်ထားတဲ့ pattern နဲ့ ကိုက်ညီရပါမယ်။

### 3.3 `(?P<s>...)` — Named Group

```python
(?P<s>[^|]+)
```

ဒီအပိုင်းက စာသားထဲက field တစ်ခုကို match လုပ်ပြီး `s` ဆိုတဲ့အမည်နဲ့ သိမ်းပေးပါတယ်။
Regex ရဲ့ named group syntax က —

```text
(?P<name>...)
```

ဖြစ်ပါတယ်။ ဒီ Exercise မှာ —

| Regex group | သိမ်းဆည်းမယ့် field |
| --- | --- |
| `(?P<s>...)` | Subject |
| `(?P<p>...)` | Predicate |
| `(?P<o>...)` | Object |
| `(?P<c>...)` | Source chunk |

နောက်ပိုင်းမှာ `match.group("s")` လို့ ရေးပြီး Subject field ကို ပြန်ရယူနိုင်ပါတယ်။

### 3.4 `[^|]+` ဆိုတာဘာလဲ။

```python
[^|]+
```

ဒီမှာ Regex syntax နှစ်ခု ပါဝင်ပါတယ်။

- `[^|]` — `|` မဟုတ်တဲ့ character တစ်ခုကို match လုပ်ခြင်း။
- `+` — အဲဒီ character တစ်ခု သို့မဟုတ် တစ်ခုထက်ပိုပြီး ပါရမယ်လို့ ဆိုလိုခြင်း။

ဒါကြောင့် `[^|]+` က `|` မပါဝင်တဲ့ စာသားတစ်ခု သို့မဟုတ် တစ်ခုထက်ပိုတဲ့ စာသားကို
match လုပ်ပါတယ်။

ဥပမာ — `Alice Chen`၊ `works_at`၊ `Acme Corp`၊ `chunk-02` ဒီလို fields တွေကို
match လုပ်နိုင်ပါတယ်။

ဒါပေမဲ့ empty field ဖြစ်နေတဲ့အခါတော့ မကိုက်ညီပါဘူး။

ဥပမာ —

```text
|empty_subject|Acme Corp|chunk-03
```

အစမှာ `|` မတိုင်ခင် subject field အလွတ်ဖြစ်နေတဲ့အတွက် `[^|]+` က match မဖြစ်ပါဘူး။

### 3.5 `\|` — Pipe character ကို match လုပ်ခြင်း

```python
\|
```

Regex မှာ `|` က အခြေအနေတစ်ခု သို့မဟုတ် အခြားတစ်ခု (alternation) ကို ကိုယ်စားပြုနိုင်တဲ့
special character ဖြစ်ပါတယ်။ တကယ့် pipe symbol `|` ကိုပဲ match လုပ်ချင်တဲ့အတွက် `\|` လို့
ရေးထားတာပါ။

Regex pattern တစ်ခုလုံးက အောက်ပါ field ပုံစံနဲ့ ကိုက်ညီဖို့ စစ်ဆေးပါတယ်။

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

ဒီ class က SPO triple တစ်ခုကို Python object တစ်ခုအနေနဲ့ သိမ်းဆည်းပေးပါတယ်။

### 4.1 `class Triple`

`Triple` ဆိုတဲ့ class အသစ်တစ်ခုကို သတ်မှတ်တာပါ။ Class ဆိုတာ data နဲ့ အဲဒီ data တွေအပေါ်
လုပ်ဆောင်နိုင်တဲ့ methods တွေကို တစ်နေရာတည်းမှာ စုစည်းထားနိုင်တဲ့ ပုံစံတစ်ခု ဖြစ်ပါတယ်။

### 4.2 `subject: str`

```python
subject: str
predicate: str
object: str
source_chunk: str
```

ဒီလို `: str` နဲ့ ရေးထားတာကို **type annotation** လို့ ခေါ်ပါတယ်။ ဒီ fields တွေမှာ
string values တွေ သိမ်းဖို့ ရည်ရွယ်ထားကြောင်း ဖော်ပြပါတယ်။

ဥပမာ —

```python
triple = Triple(
    "Alice Chen",
    "works_at",
    "Acme Corp",
    "chunk-02",
)
```

အခု `triple` ထဲမှာ field လေးခု ပါဝင်တဲ့ object တစ်ခု ရရှိပါတယ်။ Field တစ်ခုချင်းစီကို
ဒီလို ပြန်ဖတ်နိုင်ပါတယ်။

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

`@dataclass` ကြောင့် ဒီ fields တွေကို constructor ထဲမှာ သီးခြား `__init__()` method
ရေးစရာမလိုဘဲ သတ်မှတ်ထားတဲ့အစီအစဉ်အတိုင်း arguments တွေပေးပြီး object ဖန်တီးနိုင်ပါတယ်။

### 4.3 `frozen=True`

```python
@dataclass(frozen=True)
```

ဒီ option က `Triple` object ကို **immutable** အဖြစ် သတ်မှတ်ပေးပါတယ်။ Object ဖန်တီးပြီးနောက်
field တန်ဖိုးတွေကို ပြင်ဆင်လို့ မရတော့ပါဘူး။

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

ဒီလိုပြင်ဆင်လိုက်ရင် `FrozenInstanceError` ဖြစ်လာပါမယ်။

ဘာကြောင့် ဒီလိုသတ်မှတ်ရတာလဲ။ ဒီ Exercise မှာ နောက်ပိုင်း `set(triples)` လုပ်ဖို့
လိုအပ်ပါတယ်။ Default settings တွေနဲ့ `@dataclass(frozen=True)` သုံးတဲ့အခါ fields တွေက
hashable ဖြစ်နေသရွေ့ `Triple` objects တွေကို `set` ထဲ ထည့်နိုင်ပါတယ်။ ဒါက duplicate
`Triple` objects တွေကို ဖယ်ရှားဖို့ အသုံးဝင်ပါတယ်။

သတိပြုရန် — `frozen=True` က object ကို ပြင်ဆင်လို့မရအောင် ကန့်သတ်ပေးတာဖြစ်ပြီး၊ fields
တွေထဲမှာ mutable objects တွေ ထည့်ထားရင် အတွင်းပိုင်းပြင်ဆင်မှုအားလုံးကို အလိုအလျောက်
ကာကွယ်ပေးတာ မဟုတ်ပါဘူး။ ဒီဥပမာမှာ fields အားလုံးက string တွေဖြစ်လို့ သင့်တော်ပါတယ်။

### 4.4 `to_spo()` method

```python
def to_spo(self):
    return "(%s)-[%s]->(%s)" % (
        self.subject,
        self.predicate,
        self.object,
    )
```

ဒီ method က `Triple` object ကို ဖတ်ရလွယ်တဲ့ graph relationship format အဖြစ်
ပြောင်းပေးပါတယ်။

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

ဒီမှာ —

- `(Alice Chen)` — Subject node။
- `[works_at]` — Relationship။
- `(Acme Corp)` — Object node။

`source_chunk` ကို `to_spo()` ရဲ့ output ထဲမှာ မထည့်ထားပါဘူး။ ဒီ method က graph
relationship ကိုသာ ဖော်ပြပေးတာ ဖြစ်ပါတယ်။

**အရေးကြီးချက်** — သင့်မူရင်း code မှာ `to_spo()` ကို သတ်မှတ်ထားပေမဲ့ နောက်ဆုံး `print()`
ထဲမှာ အသုံးပြုမထားပါဘူး။ ဒါကြောင့် မူရင်း output က `Triple` objects တွေကို
တိုက်ရိုက်ပြတာ မဟုတ်ဘဲ အရေအတွက်သုံးခုကိုသာ ပြပါတယ်။

---

## 5. `_normalize(text)` — Text ကို သန့်စင်ခြင်း

```python
def _normalize(text):
    return re.sub(r"\s+", " ", text).strip()
```

ဒီ function က field တစ်ခုချင်းစီရဲ့ whitespace တွေကို ပုံမှန်ဖြစ်အောင် ပြုပြင်ပေးပါတယ်။

### 5.1 `re.sub()`

```python
re.sub(r"\s+", " ", text)
```

`re.sub()` က Regex pattern နဲ့ ကိုက်ညီတဲ့ စာသားတွေကို သတ်မှတ်ထားတဲ့ replacement text နဲ့
အစားထိုးပေးပါတယ်။

ဒီမှာ —

- `r"\s+"` — Whitespace တစ်ခု သို့မဟုတ် တစ်ခုထက်ပိုတာကို ရှာဖွေခြင်း။
- `" "` — Single space တစ်လုံးနဲ့ အစားထိုးခြင်း။
- `text` — ပြုပြင်ရမယ့် မူရင်းစာသား။

Whitespace ဆိုတာ သာမန် space တင်မကဘဲ tab နဲ့ newline လို စာသားကြားလပ်မှုတွေကိုလည်း
ဆိုလိုပါတယ်။

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

Space အများအပြားနဲ့ tab ကို single spaces တွေအဖြစ် ပြောင်းထားပါတယ်။

### 5.2 `.strip()`

```python
.strip()
```

`strip()` က စာသားရဲ့ အစနဲ့ အဆုံးမှာရှိတဲ့ whitespace တွေကို ဖယ်ရှားပေးပါတယ်။

ဥပမာ —

```python
text = "   Alice Chen   "

print(text.strip())
```

Output —

```text
Alice Chen
```

ဒါကြောင့် —

```python
def _normalize(text):
    return re.sub(r"\s+", " ", text).strip()
```

ဟာ whitespace အများအပြားကို single space ပြောင်းပေးပြီး အစနဲ့အဆုံးက whitespace တွေကို
ဖယ်ရှားပေးပါတယ်။

`_normalize` ရဲ့ ရှေ့မှာ underscore `_` ထည့်ထားတာက ဒီ function ဟာ module အတွင်းသုံးတဲ့
helper function ဖြစ်ကြောင်း ဖော်ပြတဲ့ Python naming convention ဖြစ်ပါတယ်။

---

## 6. `parse_triples(lines)` — Main Parsing Function

အခု Exercise ရဲ့ အဓိက function ကို လေ့လာကြည့်ရအောင်။

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

ဒီ function ရဲ့ ရည်ရွယ်ချက်က input lines တွေကို စစ်ဆေးပြီး မှန်ကန်တဲ့ triples တွေကို
တစ်စု၊ errors တွေကို တစ်စု ခွဲထုတ်ပေးဖို့ ဖြစ်ပါတယ်။

### 6.1 `triples = []` နဲ့ `errors = []`

```python
triples = []
errors = []
```

ဒီနေရာမှာ empty lists နှစ်ခု ဖန်တီးထားပါတယ်။

- `triples` — မှန်ကန်တဲ့ `Triple` objects တွေကို သိမ်းဖို့။
- `errors` — Parse မအောင်မြင်တဲ့ line တွေကို မှတ်တမ်းတင်ဖို့။

ဥပမာ —

```python
triples = []
errors = []

triples.append("valid data")
errors.append((5, "malformed_field_count"))
```

`append()` က list ရဲ့ အဆုံးမှာ item အသစ်ထည့်ပေးပါတယ်။

### 6.2 `enumerate(lines, start=1)`

```python
for line_number, raw in enumerate(lines, start=1):
```

ဒီမှာ `enumerate()` ကို အသုံးပြုပြီး line တစ်ခုချင်းစီနဲ့ အတူ line number ကိုပါ ရယူပါတယ်။

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

`start=1` ထည့်ထားတာကြောင့် numbering ကို `1` ကနေ စပါတယ်။ Default အနေနဲ့တော့ `0`
ကနေ စမှာပါ။ ဒီ Exercise မှာ line number ကို အသုံးပြုပြီး ဘယ် line မှာ error ဖြစ်တယ်ဆိုတာ
မှတ်တမ်းတင်နိုင်ပါတယ်။

### 6.3 `raw.strip()` နဲ့ Regex match

```python
match = TRIPLE_PATTERN.match(raw.strip())
```

ပထမဆုံး `raw.strip()` က line ရဲ့ အစနဲ့ အဆုံးက whitespace တွေကို ဖယ်ရှားပါတယ်။

ဥပမာ —

```python
raw = "  Acme Corp | founded_in | Cupertino | chunk-01 "

print(raw.strip())
```

Output —

```text
Acme Corp | founded_in | Cupertino | chunk-01
```

ပြီးရင် —

```python
TRIPLE_PATTERN.match(...)
```

က Regex pattern နဲ့ ကိုက်ညီမှုရှိမရှိ စစ်ဆေးပါတယ်။ Pattern ကိုက်ညီရင် match object တစ်ခု
ပြန်ရပါတယ်။ မကိုက်ညီရင် `None` ပြန်ရပါတယ်။

### 6.4 `if match is None`

```python
if match is None:
    errors.append((line_number, "malformed_field_count"))
    continue
```

Regex pattern နဲ့ line တစ်ကြောင်းလုံး ကိုက်ညီမှုမရှိရင် error အဖြစ် မှတ်တမ်းတင်ပါတယ်။

ဥပမာ —

```text
Broken|line
```

ဒီ line မှာ fields နှစ်ခုသာ ရှိပါတယ်။ ဒါပေမဲ့ Regex က field လေးခုကို မျှော်လင့်ထားတဲ့အတွက်
match မဖြစ်ပါဘူး။ ဒါကြောင့် —

```python
errors.append((5, "malformed_field_count"))
```

လို မှတ်တမ်းဝင်ပါတယ်။ ဒီ tuple မှာ —

- `5` — Error ဖြစ်တဲ့ line number။
- `"malformed_field_count"` — Error အမျိုးအစား။

`continue` က လက်ရှိ iteration ရဲ့ ကျန်ရှိတဲ့ code တွေကို ကျော်ပြီး နောက် line ကို
ဆက်စစ်စေပါတယ်။ ဒါကြောင့် match မဖြစ်တဲ့ line တွေကို `Triple` အဖြစ် ဖန်တီးဖို့
မကြိုးစားတော့ပါဘူး။

---

## 7. `match.group()` နဲ့ Fields တွေကို ထုတ်ယူခြင်း

Regex match အောင်မြင်သွားရင် fields တွေကို ထုတ်ယူပါတယ်။

```python
subject = _normalize(match.group("s"))
predicate = _normalize(match.group("p")).lower().replace(" ", "_")
obj = _normalize(match.group("o"))
chunk = _normalize(match.group("c"))
```

`match.group("s")` က Regex ထဲက `s` named group နဲ့ match ဖြစ်တဲ့ စာသားကို ပြန်ပေးပါတယ်။
အလားတူ —

- `match.group("p")` — Predicate။
- `match.group("o")` — Object။
- `match.group("c")` — Source chunk။

### 7.1 Subject ကို Normalize လုပ်ခြင်း

```python
subject = _normalize(match.group("s"))
```

ဥပမာ input ထဲမှာ `"  Acme Corp "` ဆိုရင် normalize လုပ်ပြီး `Acme Corp` ဖြစ်လာပါတယ်။

### 7.2 Predicate ကို Normalize လုပ်ခြင်း

```python
predicate = _normalize(match.group("p")).lower().replace(" ", "_")
```

ဒီတစ်ကြောင်းမှာ operations သုံးခုကို အစဉ်လိုက် လုပ်ပါတယ်။

ပထမ —

```python
_normalize(match.group("p"))
```

Whitespace တွေကို သန့်စင်ပါတယ်။

ဒုတိယ —

```python
.lower()
```

စာလုံးတွေကို lowercase ပြောင်းပါတယ်။

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

Space တွေကို underscore `_` နဲ့ အစားထိုးပါတယ်။

```python
print("reports to".replace(" ", "_"))
```

Output —

```text
reports_to
```

ဒါကြောင့် Predicate ကို lowercase ဖြစ်အောင်နဲ့ spaces တွေကို underscores ပြောင်းပြီး
တစ်သမတ်တည်း ဖြစ်အောင် သန့်စင်ထားတာပါ။

သတိပြုရန် — `.replace(" ", "_")` က single space character တွေကို အစားထိုးတာဖြစ်လို့
ပထမဆုံး `_normalize()` လုပ်ထားတာ အရေးကြီးပါတယ်။

### 7.3 Object နဲ့ Source Chunk

```python
obj = _normalize(match.group("o"))
chunk = _normalize(match.group("c"))
```

ဒီနှစ်ခုလည်း အလားတူ normalization ကို လုပ်ပေးပါတယ်။

ဒီ Exercise မှာ Predicate ကို lowercase ပြောင်းပေမဲ့ Subject နဲ့ Object ကို lowercase
ပြောင်းမထားပါဘူး။ ဒါကြောင့် `Acme Corp` က `Acme Corp` အတိုင်းပဲ ကျန်နေပါမယ်။

---

## 8. Empty Field Validation

```python
if not subject or not predicate or not obj or not chunk:
    errors.append((line_number, "empty_field"))
    continue
```

ဒီ condition က normalize လုပ်ပြီးနောက် fields တစ်ခုခု empty ဖြစ်နေသလား စစ်ဆေးပါတယ်။
Python မှာ empty string `""` က falsy ဖြစ်ပါတယ်။

```python
print(bool(""))
print(bool("Alice"))
```

Output —

```text
False
True
```

ဒါကြောင့် —

```python
if not subject:
```

ဆိုတာ `subject` က empty string ဖြစ်နေသလား စစ်တာပါ။

ဒီနေရာမှာ `or` ကို သုံးထားတဲ့အတွက် fields လေးခုထဲက တစ်ခုခု empty ဖြစ်ရင် condition
တစ်ခုလုံး `True` ဖြစ်ပါတယ်။ အဲဒီအခါ —

```python
errors.append((line_number, "empty_field"))
continue
```

နဲ့ error ကို မှတ်တမ်းတင်ပြီး နောက် line ကို ဆက်စစ်ပါတယ်။

### အရေးကြီးတဲ့ Regex အချက်တစ်ခု

သင့်မူရင်း Regex မှာ `[^|]+` ကို သုံးထားပါတယ်။ `+` က field ထဲမှာ အနည်းဆုံး character
တစ်ခု ပါရမယ်လို့ သတ်မှတ်ထားတဲ့အတွက် တကယ့် empty field ကို Regex က အစောပိုင်းမှာပဲ
ပယ်ချလိုက်ပါတယ်။

ဒါကြောင့် —

```text
|empty_subject|Acme Corp|chunk-03
```

ဒီလို line ဟာ `empty_field` အဆင့်ကို မရောက်ဘဲ `match is None` အပိုင်းမှာ
`malformed_field_count` အဖြစ် မှတ်တမ်းဝင်ပါတယ်။

တကယ့် empty fields တွေကို သီးခြား `empty_field` error အဖြစ် ခွဲခြားချင်ရင် Regex ထဲက
`+` ကို `*` နဲ့ ပြောင်းနိုင်ပါတယ်။

```python
TRIPLE_PATTERN = re.compile(
    r"^(?P<s>[^|]*)\|(?P<p>[^|]*)\|(?P<o>[^|]*)\|(?P<c>[^|]*)$"
)
```

`*` က character သုညခု သို့မဟုတ် အများကြီးကို ခွင့်ပြုတာကြောင့် empty field ကိုလည်း
match လုပ်နိုင်ပါတယ်။ ထို့နောက် `if not subject ...` validation က `empty_field` ကို
ရှာဖွေပေးနိုင်ပါတယ်။

ဒီပြောင်းလဲမှုက မူရင်း code ရဲ့ စုစုပေါင်း valid records နဲ့ error counts ကို
မပြောင်းလဲစေပေမဲ့၊ error အမျိုးအစားအလိုက် မှတ်တမ်းတင်ပုံကို ပြောင်းလဲစေပါတယ်။

---

## 9. `triples.append(Triple(...))`

```python
triples.append(Triple(subject, predicate, obj, chunk))
```

Fields တွေ အားလုံး valid ဖြစ်ပြီဆိုရင် `Triple` object တစ်ခု ဖန်တီးပြီး `triples` list ထဲ
ထည့်ပါတယ်။

ဥပမာ —

```python
Triple(
    "Acme Corp",
    "founded_in",
    "Cupertino",
    "chunk-01",
)
```

ဒီ object က အောက်ပါ information တွေကို သိမ်းထားပါတယ်။

| Field | Value |
| --- | --- |
| `subject` | `Acme Corp` |
| `predicate` | `founded_in` |
| `object` | `Cupertino` |
| `source_chunk` | `chunk-01` |

`triples.append(...)` က ဒီ object ကို list ထဲ ထည့်ပါတယ်။ ဒါကြောင့် valid line တစ်ကြောင်းကို
အောင်မြင်စွာ parse လုပ်တိုင်း `triples` list ရဲ့ အရွယ်အစား တစ်ခုတိုးလာပါတယ်။

---

## 10. `return triples, errors`

```python
return triples, errors
```

Function က result နှစ်ခုကို တစ်ပြိုင်နက် ပြန်ပေးပါတယ်။

- `triples` — Parse လုပ်ထားတဲ့ valid `Triple` objects။
- `errors` — Parse မအောင်မြင်တဲ့ lines တွေရဲ့ error records။

Python မှာ comma ခွဲပြီး values အများအပြားကို `return` လုပ်တဲ့အခါ tuple တစ်ခုအဖြစ်
ပြန်ရရှိပါတယ်။ ဒါကြောင့် —

```python
triples, errors = parse_triples(TRIPLE_LINES)
```

မှာ function က ပြန်ပေးတဲ့ tuple ကို variable နှစ်ခုထဲ unpack လုပ်ထားတာ ဖြစ်ပါတယ်။

- ပထမ value ကို `triples` ထဲ သိမ်းပါတယ်။
- ဒုတိယ value ကို `errors` ထဲ သိမ်းပါတယ်။

ဒီလိုပုံစံကို အရင် Exercises တွေမှာလည်း တွေ့ခဲ့ပါတယ်။ ဥပမာ Exercise 4 မှာ tuple
unpacking ကို အသုံးပြုပြီး `query_id` နဲ့ `features` ကို ခွဲယူခဲ့ပါတယ်။

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

ဒီ list ထဲမှာ input lines ခြောက်ကြောင်း ပါဝင်ပါတယ်။ တစ်ကြောင်းချင်းစီကို
စစ်ဆေးကြည့်ရအောင်။

| Line | စစ်ဆေးချက် | ရလဒ် |
| --- | --- | --- |
| 1 | Field လေးခုရှိပြီး normalize လုပ်လို့ရတယ် | Valid Triple |
| 2 | Line 1 နဲ့ normalize ပြီးနောက် တူညီတယ် | Valid Triple၊ နောက်ပိုင်း duplicate ဖြစ်မယ် |
| 3 | SPO နဲ့ chunk fields မှန်ကန်တယ် | Valid Triple |
| 4 | Fields မှန်ကန်ပြီး Predicate ကို normalize လုပ်မယ် | Valid Triple |
| 5 | Fields နှစ်ခုပဲရှိတယ် | Error |
| 6 | Subject field အလွတ်ဖြစ်နေတယ် | Regex match မဖြစ်လို့ Error |

ဒီ input မှာ ပထမ line က ရှေ့နောက် spaces အချို့ ပါဝင်ပေမဲ့ normalization လုပ်ပြီးနောက်
ဒုတိယ line နဲ့ တူညီသွားပါတယ်။ ဒါကြောင့် valid `Triple` objects လေးခုကို
ဖန်တီးထားပေမဲ့ unique triples အရေအတွက်က သုံးခုပဲ ရှိပါမယ်။

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

ဒီတစ်ကြောင်းက duplicate `Triple` objects တွေကို ဖယ်ရှားပြီး အစီအစဉ်တကျ ပြန်စီပေးပါတယ်။

### 12.1 `set(triples)`

`set()` က unique values တွေကို သိမ်းဆည်းပေးတဲ့ data structure ဖြစ်ပါတယ်။

ဥပမာ —

```python
items = ["apple", "banana", "apple", "orange"]

print(set(items))
```

Output မှာ `"apple"` ကို တစ်ခုပဲ ထားပါမယ်။

```text
{'apple', 'orange', 'banana'}
```

Set က insertion order ကို အခြေခံထားတဲ့ display order ကို အာမမခံပါဘူး — အပေါ်က
အစီအစဉ်သည် run တစ်ခုနှင့်တစ်ခု ကွဲနိုင်ပါတယ်။

ဒီ Exercise မှာ `Triple` ကို `@dataclass(frozen=True)` နဲ့ ဖန်တီးထားတဲ့အတွက် fields
တန်ဖိုးအားလုံး တူညီတဲ့ objects တွေကို `set` က duplicate အဖြစ် သတ်မှတ်နိုင်ပါတယ်။

ပထမနဲ့ ဒုတိယ line တွေကို normalization လုပ်ပြီးတဲ့အခါ object နှစ်ခုစလုံးရဲ့ fields တွေက —

```python
Triple(
    "Acme Corp",
    "founded_in",
    "Cupertino",
    "chunk-01",
)
```

အတိုင်း တူညီနေပါတယ်။ ဒါကြောင့် `set(triples)` လုပ်တဲ့အခါ အဲဒီ duplicate နှစ်ခုထဲက
တစ်ခုသာ ကျန်ပါတယ်။

သတိပြုရန် — ဒီ code က Subject၊ Predicate၊ Object နဲ့ `source_chunk` လေးခုစလုံး
တူညီတဲ့ `Triple` objects တွေကိုပဲ duplicate အဖြစ် သတ်မှတ်ပါတယ်။ SPO သုံးခုတူပေမဲ့
source chunk မတူရင် objects တွေက မတူညီသေးတဲ့အတွက် နှစ်ခုစလုံးကို ထိန်းထားပါမယ်။

### 12.2 `sorted(...)`

Set ထဲမှာ unique `Triple` objects တွေ ကျန်ပြီဆိုရင် `sorted()` နဲ့ စီစဉ်ပါတယ်။

```python
key=lambda t: (
    t.subject,
    t.predicate,
    t.object,
    t.source_chunk,
)
```

ဒီ lambda function က `Triple` object တစ်ခုချင်းစီအတွက် sorting key ကို ပြန်ပေးပါတယ်။
Sorting အတွက် အစဉ်လိုက် ကြည့်မယ့် fields တွေက —

- `t.subject`
- `t.predicate`
- `t.object`
- `t.source_chunk`

ဥပမာ Subject တူညီတဲ့ triples နှစ်ခုရှိရင် Predicate ကို ထပ်စစ်မယ်။ Predicate လည်း
တူရင် Object ကို ထပ်စစ်မယ်။ အဲဒီနောက် Source chunk ကို စစ်ပါတယ်။

ဒီလိုလုပ်ထားတာကြောင့် input lines တွေကို အစဉ်မတူအောင် ပေးထားလည်း sorting key တူညီတဲ့
data တွေအတွက် ရလဒ်ကို တစ်သမတ်တည်း ထိန်းသိမ်းနိုင်ပါတယ်။

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

ဒီတစ်ကြောင်းက ကိန်းဂဏန်းသုံးခုကို ပြသပါတယ်။

### ပထမတန်ဖိုး — `len(triples)`

`triples` list ထဲမှာ valid `Triple` objects ဘယ်နှခုရှိသလဲဆိုတာ ပြန်ပေးပါတယ်။ Line 1၊ 2၊
3၊ 4 တို့က valid ဖြစ်တဲ့အတွက် `4` ဖြစ်ပါတယ်။

### ဒုတိယတန်ဖိုး — `len(errors)`

`errors` list ထဲမှာ invalid lines ဘယ်နှခုရှိသလဲဆိုတာ ပြန်ပေးပါတယ်။ Line 5 နဲ့ 6 တို့မှာ
Regex match မဖြစ်တဲ့အတွက် `2` ဖြစ်ပါတယ်။

### တတိယတန်ဖိုး — `len(triples) - len(unique)`

Valid `Triple` objects အရေအတွက်ထဲက unique objects အရေအတွက်ကို နုတ်ထားပါတယ်။

```text
Valid triples  = 4
Unique triples = 3
```

ဒါကြောင့် `4 - 3 = 1` ဆိုပြီး duplicate အဖြစ် ဖယ်ရှားလိုက်တဲ့ extra record အရေအတွက်ကို
ပြပါတယ်။

ဒီတန်ဖိုးက duplicate records အားလုံးကို စုစုပေါင်းဖယ်ရှားလိုက်တဲ့ အရေအတွက်ပါ။ ဥပမာ
record တစ်ခုက သုံးကြိမ်ပါနေရင် အဲဒီ record အတွက် duplicate အပိုနှစ်ခုကို ဖယ်ရှားမှာ
ဖြစ်ပါတယ်။

### Expected Output

```text
4 2 1
```

အဓိပ္ပာယ်က —

- `4` — Valid records လေးခုကို parse လုပ်နိုင်ခဲ့တယ်။
- `2` — Invalid lines နှစ်ကြောင်းကို error အဖြစ် မှတ်တမ်းတင်ခဲ့တယ်။
- `1` — Duplicate record တစ်ခုကို ဖယ်ရှားနိုင်ခဲ့တယ်။

---

## 14. Code တစ်ခုလုံး — သန့်စင်ပြီး Run လုပ်နိုင်သော Version

အောက်မှာ ဒီ Exercise ရဲ့ runnable version ကို စုစည်းပေးထားပါတယ်။ မူရင်း logic ကို
ထိန်းထားပြီး code formatting ကို ပြင်ဆင်ထားပါတယ်။

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

## 15. ဒီ Exercise က RAG / GraphRAG မှာ ဘယ်လိုအသုံးဝင်သလဲ။

ဒီ Exercise က text chunks တွေထဲက relationship information ကို structured data အဖြစ်
ပြောင်းဖို့ အခြေခံပုံစံတစ်ခုကို ပြသထားပါတယ်။

1. **Raw documents** — Knowledge base ထဲက မူရင်းစာသားများ
2. **Triple extraction** — Subject၊ Predicate၊ Object နဲ့ source chunk ကို ခွဲထုတ်ခြင်း
3. **Normalization + Validation** — Whitespace သန့်စင်ခြင်း၊ fields စစ်ဆေးခြင်း
4. **Deduplication** — တူညီသော `Triple` objects များကို ဖယ်ရှားခြင်း
5. **Knowledge Graph** — Validated triples များဖြင့် entities နဲ့ relationships ကို တည်ဆောက်ခြင်း

ဒီ code က triple parsing နဲ့ validation ကိုသာ လုပ်ဆောင်ထားတာဖြစ်ပြီး Graph database
ထဲကို တကယ်သိမ်းဆည်းခြင်း မလုပ်သေးပါဘူး။ Production GraphRAG pipeline မှာ entity
resolution၊ relation validation၊ source tracking နဲ့ database writes တွေကို ထပ်မံ
တည်ဆောက်ဖို့ လိုအပ်ပါတယ်။

### ကိုယ်တိုင်လေ့ကျင့်ကြည့်ပါ

**မေးခွန်း** — အောက်ပါ line ကို `parse_triples()` ထဲ ထည့်လိုက်ရင် ဘယ် list ထဲ
ရောက်မလဲ။

```text
Network Team|manages|Core Switch 01
```

1. `triples` — Valid Triple အဖြစ်
2. `errors` — `malformed_field_count` အဖြစ်
3. `errors` — `empty_field` အဖြစ်
4. Field လေးခုရှိလို့ နှစ်ခုလုံးထဲ ရောက်မယ်

<details>
<summary>အဖြေ ကြည့်ရန်</summary>

**အဖြေ — 2. `errors` — `malformed_field_count` အဖြစ်**

အကြောင်းရင်း — Regex သည် `Subject|Predicate|Object|SourceChunk` ဆိုသည့် field
**လေးခု**ကို မျှော်လင့်သည်။ ဤ line တွင် field သုံးခုသာ ရှိသဖြင့် — `|` သုံးခု
(`Network Team`၊ `manages`၊ `Core Switch 01`) — `TRIPLE_PATTERN.match()` သည်
`None` ပြန်သည်။ ထို့ကြောင့် `match is None` branch သို့ ရောက်ပြီး
`malformed_field_count` အဖြစ် မှတ်တမ်းဝင်သည်။

Source chunk အပိုင်း ထည့်လိုက်ပါက valid `Triple` ဖြစ်သွားမည် —

```text
Network Team|manages|Core Switch 01|chunk-04
```

</details>

**အဓိက မှတ်ထားရန်** — ဒီ Exercise မှာ Regex က line format ကို စစ်ဆေးပါတယ်။
`Triple` dataclass က SPO data ကို object အဖြစ် သိမ်းဆည်းပါတယ်။ `_normalize()` က
whitespace နဲ့ predicate စာလုံးပုံစံကို တစ်သမတ်တည်း ပြုပြင်ပေးပါတယ်။
`parse_triples()` က valid records နဲ့ errors တွေကို ခွဲထုတ်ပါတယ်။ နောက်ဆုံး `set()` နဲ့
`sorted()` ကို သုံးပြီး duplicate records တွေကို ဖယ်ရှားကာ unique triples တွေကို
အစီအစဉ်တကျ ပြင်ဆင်ပေးပါတယ်။
