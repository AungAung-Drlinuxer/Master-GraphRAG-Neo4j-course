# Walkthrough 01 — Corpus Normalization (Exercise 1)

> ဤဖိုင်သည် Module 04 ၏ `solution.md` ထဲက Exercise 1 ကို **Python အခြေခံမှ စ၍**
> အပိုင်းလိုက် ရှင်းပြသည့် walkthrough ဖြစ်သည်။ Format သည် Module 01 ၏
> `walkthroughs/01_regex_ner.md` နှင့် `walkthroughs/03_gazetteer_lookup.md` နှင့်
> တူညီသည်။

---

## 0. ဤ Exercise က ဘာကို ဖြေရှင်းပေးသလဲ။

Pipeline ၏ ပထမဆုံး အလုပ်သည် raw text ကို **နောက်အဆင့်အားလုံး မှီခိုနိုင်သည့်
ပုံစံတူ text** အဖြစ် ပြောင်းခြင်း ဖြစ်သည်။ မူရင်း corpus တွင် အောက်ပါ ပြဿနာများ
ရှိနိုင်သည်။

```text
raw text
  -> smart quote ၊ smart dash ၊ ellipsis character
  -> newline / tab / control character
  -> ထပ်နေသော whitespace
  -> Unicode ပုံစံ နှစ်မျိုး (composed / decomposed)

normalize
  -> "clean text" (channel တစ်ခုတည်း)

ရလဒ် မကောင်းပါက —
  * 'graph\u2013database' နှင့် 'graph-database' သည် မတူညီသော string နှစ်ခု ဖြစ်လာသည်
  * 'database.\nNeo4j' ကို newline ဖျက်လိုက်လျှင် 'database.Neo4j' ဖြစ်ပြီး sentence splitting ပျက်သည်
  * sentence splitter ၊ entity matcher ၊ chunker အားလုံး မတူညီသော input ကို ရသည်
```

ဤ Exercise သည် normalization ကို **အဆင့်လိုက် function တစ်ခုတည်း** (`normalize_text`)
ထဲ စုစည်းပြီး၊ အဆင့်တိုင်း၏ အစီအစဉ်ကို မည်သည့်အတွက်ကြောင့် ထိုအစီအစဉ်အတိုင်း
ထားရသည်ကို ပြသသည်။

ဤ code တွင် လေ့လာရမည့် Python concepts များမှာ —

- `import` နှင့် standard library module (`re`၊ `unicodedata`)
- `@dataclass` decorator နှင့် field များ
- List comprehension
- Dict ပေါ်တွင် `.items()` ဖြင့် iteration
- `str.replace()` နှင့် `str.strip()`
- `re.sub()`
- Generator expression နှင့် `"".join(...)`
- `%` string formatting နှင့် `repr()`
- `all()` နှင့် `assert`

---

## 1. `import` — လိုအပ်သည့် module များ

```python
import re
import unicodedata
from dataclasses import dataclass
```

| လိုင်း | အဓိပ္ပာယ် |
| --- | --- |
| `import re` | Regular Expression operation များအတွက် |
| `import unicodedata` | Unicode normalization နှင့် character category စစ်ရန် |
| `from dataclasses import dataclass` | `@dataclass` decorator ကို တိုက်ရိုက် import |

`from X import Y` ပုံစံသည် module တစ်ခုလုံး မယူဘဲ **အမည်တစ်ခုတည်း**ကို ယူသည်။
ထို့ကြောင့် နောက်ပိုင်းတွင် `dataclass` ဟု တိုက်ရိုက် ရေးနိုင်သည် — `dataclasses.dataclass`
ဟု အရှည်ကြီး ရေးရန် မလိုပါ။

---

## 2. `@dataclass` နှင့် `Document` — structure သတ်မှတ်ခြင်း

```python
from dataclasses import dataclass


@dataclass
class Document:
    doc_id: str
    text: str
    char_count: int


doc = Document("doc-001", "Neo4j  is a graph database.", 27)
print(doc)
print(doc.doc_id, doc.char_count)
```

Output —

```text
Document(doc_id='doc-001', text='Neo4j  is a graph database.', char_count=27)
doc-001 27
```

### `@dataclass` က ဘာလုပ်ပေးသလဲ။

ပုံမှန် class ဖြစ်လျှင် `__init__` ကို ကိုယ်တိုင် ရေးရသည်။

```python
class Document:
    def __init__(self, doc_id, text, char_count):
        self.doc_id = doc_id
        self.text = text
        self.char_count = char_count
```

`@dataclass` ထည့်လိုက်လျှင် **field အမည်နှင့် type ကို ဖတ်ပြီး `__init__` ကို အလိုအလျောက်
ဖန်တီး** ပေးသည်။ `Document("doc-001", ...)` ဟု ခေါ်နိုင်ပြီး `doc.doc_id` ဟု
attribute ဖြင့် ဖတ်နိုင်သည်။

`repr()` ပြသပုံသည်လည်း အလိုအလျောက် ဖြစ်လာသည် — `print(doc)` သည်
`Document(doc_id='doc-001', ...)` ဟု ပြသည်။ Debugging အတွက် အလွန် အသုံးဝင်သည်။

Pipeline တစ်ခုလုံးတွင် `Document`၊ `Chunk`၊ `Entity`၊ `Triple` စသည့် data structure များကို
`@dataclass` ဖြင့် သတ်မှတ်ထားသောကြောင့် stage တိုင်း လက်ခံသည့် object ပုံစံ တိကျသည်။

---

## 3. `ingest_corpus()` — corpus ကို Document အဖြစ် ဖတ်ခြင်း

```python
from dataclasses import dataclass

SAMPLE_CORPUS = [
    {"doc_id": "doc-001", "raw_text": "Neo4j  is a graph database.\nNeo4j uses Cypher as its query language. "
                                      "GraphRAG is built on a Knowledge Graph. Nous Research develops open models."},
    {"doc_id": "doc-002", "raw_text": "Graph Rag runs on Neo4j. GraphRAG is built on a Knowledge Graph. "
                                      "Neo4j was developed by Neo4j Inc. Neo4j,  GraphRAG and Cypher are widely "
                                      "used in production."},
    {"doc_id": "doc-003", "raw_text": "Entity Resolution merges duplicate nodes. GraphRAG uses Entity Resolution. "
                                      "LLM is a Transformer based model. Entity resolution includes alias mapping."},
]


@dataclass
class Document:
    doc_id: str
    text: str
    char_count: int


def ingest_corpus(corpus):
    return [Document(d["doc_id"], d["raw_text"], len(d["raw_text"])) for d in corpus]


for doc in ingest_corpus(SAMPLE_CORPUS):
    print("%s %3d" % (doc.doc_id, doc.char_count))
```

Output —

```text
doc-001 144
doc-002 157
doc-003 150
```

### List comprehension

```python
[Document(d["doc_id"], d["raw_text"], len(d["raw_text"])) for d in corpus]
```

၎င်းသည် **list comprehension** ဖြစ်သည်။ `corpus` ထဲက dict တစ်ခုချင်းစီကို `d` ဟု
ယူပြီး၊ ထို dict မှ `doc_id` နှင့် `raw_text` ကို ဖတ်ကာ `Document` အသစ် ဖန်တီးသည်။
ရလဒ်များကို list အဖြစ် ပြန်ပေးသည်။

ပုံမှန် `for` loop ဖြင့် ရေးလျှင် —

```python
def ingest_corpus(corpus):
    documents = []
    for d in corpus:
        documents.append(Document(d["doc_id"], d["raw_text"], len(d["raw_text"])))
    return documents
```

ရည်ရွယ်ချက် တူညီသည်။ Comprehension က ပိုတိုပြီး "data တစ်ခုစီကို
ပြောင်းလဲပစ်သည်" ဆိုသည့် ရည်ရွယ်ချက်ကို တိုက်ရိုက် ဖော်ပြသည်။

`char_count` ကို `len(d["raw_text"])` ဖြင့် **raw** text အပေါ် တွက်ထားသည်ကို
သတိထားရမည် — ၎င်းသည် normalization မတိုင်မီ အရေအတွက် ဖြစ်သည်။ ထို့ကြောင့်
`raw_chars` နှင့် `normalized_chars` ကို နှိုင်းယှဉ်နိုင်သည်။

---

## 4. `UNICODE_FOLD` — smart character များ ဖြေခြင်း

```python
UNICODE_FOLD = {"\u2018": "'", "\u2019": "'", "\u201c": '"', "\u201d": '"',
                "\u2013": "-", "\u2014": "-", "\u2026": "...", "\u00a0": " "}

print(len(UNICODE_FOLD))
print("%r" % UNICODE_FOLD["\u201c"])
print("%r" % UNICODE_FOLD["\u00a0"])
```

Output —

```text
8
'"'
' '
```

Word processor များသည် စာရိုက်သည့်အခါ quote ကို **smart quote** (curly quote) အဖြစ်
အလိုအလျောက် ပြောင်းသည်။ ၎င်းတို့သည် ASCII `"` နှင့် **မတူညီသည့် character** ဖြစ်သည်။

| Source (code point) | မူရင်း | ပြောင်းလိုက်သည့် တန်ဖိုး |
| --- | --- | --- |
| `\u2018` | `'` (left single) | `'` |
| `\u2019` | `'` (right single) | `'` |
| `\u201c` | `"` (left double) | `"` |
| `\u201d` | `"` (right double) | `"` |
| `\u2013` | en dash | `-` |
| `\u2014` | em dash | `-` |
| `\u2026` | ellipsis `…` | `...` |
| `\u00a0` | non-breaking space | ` ` |

Dictionary ၏ key သည် **မူရင်း character** ဖြစ်ပြီး value သည် ပြောင်းလိုက်သည့် တန်ဖိုး ဖြစ်သည်။
`\u00a0` (non-breaking space) ကို regular space သို့ ပြောင်းခြင်းသည် အထူးအရေးကြီးသည် —
မပြောင်းလျှင် နောက်ပိုင်း `\s+` collapse က `\u00a0` ကို space အဖြစ် အလိုအလျောက်
မမှတ်ဘဲ စာလုံးများ ကပ်နေမည်။

---

## 5. `unicodedata.normalize("NFC", raw)` — Unicode ပုံစံ တစ်ခုတည်းပြုခြင်း

```python
import unicodedata

decomposed = "cafe\u0301"
composed = "caf\u00e9"
print(len(decomposed), len(composed))
print(decomposed == composed)
print(unicodedata.normalize("NFC", decomposed) == composed)
```

Output —

```text
5 4
False
True
```

မျက်စိဖြင့် တူညီစွာ မြင်ရသည့် `café` စာသားကို Unicode တွင် ပုံစံ **နှစ်မျိုး**
ရေးနိုင်သည်။

- `"cafe\u0301"` — `e` နောက်တွင် combining acute accent (`\u0301`) ကပ် (အရှည် ၅)
- `"caf\u00e9"` — `é` character တစ်လုံးတည်း (အရှည် ၄)

နှစ်ခုသည် **မတူညီသော string** ဖြစ်သည် (`False`)။ `normalize("NFC", ...)` သည်
decomposed ပုံစံကို composed ပုံစံသို့ **စုစည်း** (compose) ပေးသည်။ ထို့ကြောင့်
normalize လုပ်ပြီးလျှင် နှစ်ခု တူညီသွားသည် (`True`)။

ဤအဆင့် မလုပ်လျှင် — တူညီသည့် entity အမည်ကို စာသားရင်းမြစ်နှစ်ခုတွင် ပုံစံနှစ်မျိုးဖြင့်
ရေးထားလျှင် byte level တွင် မတူညီဘဲ **duplicate node** နှစ်ခု ဖြစ်လာသည်။ ထို့ကြောင့် NFC
ကို **အပိုင်းလိုက် လုပ်ငန်းစဉ်၏ အစပိုင်းဆုံး** တွင် ထားရသည်။

---

## 6. `for src, dst in UNICODE_FOLD.items(): text = text.replace(...)`

```python
UNICODE_FOLD = {"\u2018": "'", "\u2019": "'", "\u201c": '"', "\u201d": '"',
                "\u2013": "-", "\u2014": "-", "\u2026": "...", "\u00a0": " "}

text = "\u201cGraphRAG\u201d\u00a0\u2013\u00a0Neo4j\u2026"
for src, dst in UNICODE_FOLD.items():
    text = text.replace(src, dst)
print(repr(text))
```

Output —

```text
'"GraphRAG" - Neo4j...'
```

### `.items()` က dict ကို `(key, value)` တွဲအဖြစ် ပြန်ပေးသည်

```python
for src, dst in UNICODE_FOLD.items():
```

`UNICODE_FOLD.items()` သည် `(character, replacement)` tuple များကို list အဖြစ် ပြန်သည်။
`src, dst` ကို **tuple unpacking** ဖြင့် နှစ်ခု ခွဲရယူသည်။

### `text = text.replace(src, dst)` — ထပ်တိုးပြင်ဆင်ခြင်း

`replace()` သည် string အသစ်တစ်ခု ပြန်ပေးသည် — **မူရင်း string ကို မပြောင်းပါ**
(string သည် immutable ဖြစ်သည်)။ ထို့ကြောင့် `text` ကို ပြန်သတ်မှတ်ရသည်။

Loop တစ်ကြိမ်ချင်းစီတွင် `text` သည် အစဉ်လိုက် ပြောင်းလဲသွားသည်။

| ကြိမ် | လုပ်ဆောင်ချက် | `text` |
| --- | --- | --- |
| start | — | `"GraphRAG" – Neo4j…` |
| 3 (right double) | `"` → `"` | `"GraphRAG" – Neo4j…` |
| 8 (nbsp) | `\u00a0` → ` ` | `"GraphRAG" – Neo4j…` |
| 5 (en dash) | `–` → `-` | `"GraphRAG" - Neo4j…` |
| 7 (ellipsis) | `…` → `...` | `"GraphRAG" - Neo4j...` |

`repr()` သည် string ကို quote နှင့် တွဲပြပြီး space နှင့် escape character များကို
မြင်သာအောင် ပြသည်။ Debugging တွင် `print(text)` ထက် `print(repr(text))` က
နောက်ဆုံး space ရှိမရှိ စသည်ကို ရှင်းရှင်းလင်းလင်း ပြသည်။

---

## 7. Control character — newline ကို space အဖြစ် (အရေးကြီးသည့် trap)

```python
import re

raw = "Neo4j is a graph database.\nNeo4j uses Cypher as its query language."
print(repr(re.sub(r"[\r\n\t\f\v]+", " ", raw)))
print(repr(raw.replace("\n", "")))
```

Output —

```text
'Neo4j is a graph database. Neo4j uses Cypher as its query language.'
'Neo4j is a graph database.Neo4j uses Cypher as its query language.'
```

ဤနေရာတွင် လွယ်ကူစွာ ကျူးလွန်နိုင်သည့် အမှားကို နှိုင်းယှဉ်ပြထားသည်။

| နည်းလမ်း | ရလဒ် |
| --- | --- |
| `re.sub(r"[\r\n\t\f\v]+", " ", raw)` | `database. Neo4j` (space ရှိ) |
| `raw.replace("\n", "")` | `database.Neo4j` (စာလုံးကပ်) |

Newline ကို **ဖျက်ပစ်** လိုက်လျှင် စာလုံးနှစ်လုံး (`database.` နှင့် `Neo4j`) ကပ်သွားပြီး
နောက်အဆင့်၏ sentence splitter သည် ဤနေရာတွင် sentence boundary ကို မှားဖတ်သည်။
စာသားတစ်ကြောင်းနှင့်တစ်ကြောင်း **ကြားကွက်လပ်** ဖြစ်ရမည့် newline ကို space အဖြစ်
ပြောင်းရသည်။

Pattern ၏ အပိုင်းလိုက် အဓိပ္ပာယ် —

| အပိုင်း | အဓိပ္ပာယ် |
| --- | --- |
| `[\r\n\t\f\v]` | CR၊ LF၊ tab၊ form feed၊ vertical tab |
| `+` | ကပ်နေသည့် တစ်ခု သို့မဟုတ် ထို့ထက် ပို |
| `" "` | အစားထိုးသည့် space တစ်လုံး |

`+` ပါသောကြောင့် `"\n\n"` (လိုင်းခွဲ နှစ်ခု ကပ်) ကို space **တစ်လုံး** အဖြစ်သာ
ပြောင်းသည်။ ထို့ကြောင့် နောက်ဆုံး whitespace collapse သည် အလွန်အကျွံ space များကို
ထပ်ပြီး ဖယ်ရန် မလိုအပ်ပါ။

---

## 8. `unicodedata.category(ch)[0] != "C"` — ကျန် control character ဖယ်ခြင်း

```python
import unicodedata

sample = "a\x00b\x07c\u200bd"
print([unicodedata.category(ch) for ch in sample])
print(repr("".join(ch for ch in sample if unicodedata.category(ch)[0] != "C")))
```

Output —

```text
['Ll', 'Cc', 'Ll', 'Cc', 'Ll', 'Cf', 'Ll']
'abcd'
```

### Unicode category သည် အဘယ်နည်း။

`unicodedata.category(ch)` သည် character တစ်လုံး၏ **အမျိုးအစား** ကို string
နှစ်လုံးဖြင့် ပြန်သည်။ ပထမစာလုံးသည် အဓိကအုပ်စု ဖြစ်သည် —

| Category | အစအုပ်စု | အဓိပ္ပာယ် |
| --- | --- | --- |
| `Ll` / `Lu` | `L` | Letter (အသေး / အကြီး) |
| `Nd` | `N` | Number |
| `Cc` | `C` | Control character (`\x00`၊ `\x07`) |
| `Cf` | `C` | Format character (zero-width) |
| `Zs` | `Z` | Space |

`sample` ၏ character ခုနစ်လုံးအတွက် `['Ll', 'Cc', 'Ll', 'Cc', 'Ll', 'Cf', 'Ll']`
ရသည်။ `\u200b` (zero-width space) သည် `Cf` ဖြစ်သည်ကို သတိထားရမည် — မျက်စိဖြင့်
မမြင်ရဘဲ text ကို ခွဲစိတ်နိုင်သည့် အန္တရာယ်ရှိသည့် character ဖြစ်သည်။

### `[0]` ဖြင့် အစအုပ်စုသာ ယူခြင်း

```python
unicodedata.category(ch)[0] != "C"
```

`"Cc"`, `"Cf"`, `"Cn"`, `"Co"`, `"Cs"` — အားလုံးသည် `C` အုပ်စုထဲ ပါသည်။ ထို့ကြောင့်
`C` အုပ်စုတစ်ခုလုံးကို ဖယ်ရန် `[0]` (ပထမစာလုံး) ကို စစ်ရုံသာဖြစ်သည်။ Category တစ်ခုချင်း
စာရင်းလုပ်ရန် မလိုပါ။

### Generator expression နှင့် `"".join(...)`

```python
"".join(ch for ch in sample if unicodedata.category(ch)[0] != "C")
```

`ch for ch in sample if ...` သည် **generator expression** ဖြစ်သည်။ ကွင်းမပါသည့်
comprehension ပုံစံဖြစ်ပြီး၊ `join()` သည် ၎င်းကို ဖတ်ပြီး ကျန်သည့် character များကို
string တစ်ခုတည်း အဖြစ် ပြန်ဆက်သည်။ `"".join(...)` ၏ `""` သည်
**ကြားထည့်ရမည့် separator** ဖြစ်သည် — ဤနေရာတွင် separator မလိုသောကြောင့်
empty string ဖြစ်သည်။

`['Ll', 'Cc', 'Ll', 'Cc', 'Ll', 'Cf', 'Ll']` ထဲက `Cc` နှင့် `Cf` ၄ လုံး
ဖယ်သွားပြီး `'abcd'` ကျန်သည်။

---

## 9. `re.sub(r"\s+", " ", text).strip()` — whitespace ကို တစ်ပြေးညီစေခြင်း

```python
import re

print(repr(re.sub(r"\s+", " ", "  Neo4j  is   a graph database.  ").strip()))
```

Output —

```text
'Neo4j is a graph database.'
```

- `\s+` သည် space၊ tab၊ newline စသည့် whitespace တစ်ခု သို့မဟုတ် ထို့ထက် ပို။
- `" "` ဖြင့် **space တစ်လုံး** အဖြစ် ပြောင်းသည်။
- `.strip()` သည် အစနှင့် အဆုံး ကွက်လပ်များကို ဖယ်သည်။

ဤအဆင့်သည် normalization ၏ **အဆုံးဆုံး** တွင် ရှိသည်။ အရှေ့အဆင့်များက space
အသစ်များ ထည့်လာနိုင်သောကြောင့် (ဥပမာ newline → space) collapse ကို နောက်ဆုံးတွင်
လုပ်ရသည်။

---

## 10. `normalize_text()` — အပိုင်းလိုက် စုစည်းခြင်း

အထက်ပါ အဆင့်များကို function တစ်ခုတည်းထဲ စုစည်းကြည့်ပါ။

```python
import re
import unicodedata

UNICODE_FOLD = {"\u2018": "'", "\u2019": "'", "\u201c": '"', "\u201d": '"',
                "\u2013": "-", "\u2014": "-", "\u2026": "...", "\u00a0": " "}


def normalize_text(raw):
    text = unicodedata.normalize("NFC", raw)
    for src, dst in UNICODE_FOLD.items():
        text = text.replace(src, dst)
    text = re.sub(r"[\r\n\t\f\v]+", " ", text)
    text = "".join(ch for ch in text if unicodedata.category(ch)[0] != "C")
    return re.sub(r"\s+", " ", text).strip()


CASES = [
    ("dirty", "  Neo4j\u00a0 is  a graph\u2013database.\n\n  \u201cGraphRAG\u201d  \u2026  "),
    ("tab", "Neo4j\tuses\tCypher."),
    ("decomposed", "cafe\u0301 data"),
    ("ctrl", "Neo4j\x00ingest\x07done"),
]
for label, raw in CASES:
    print("%-11s %r" % (label, normalize_text(raw)))
```

Output —

```text
dirty       'Neo4j is a graph-database. "GraphRAG" ...'
tab         'Neo4j uses Cypher.'
decomposed  'café data'
ctrl        'Neo4jingestdone'
```

ဤစာရင်းသည် အဆင့်တိုင်း၏ အလုပ်ကို ရှင်းရှင်းလင်းလင်း ပြသည်။

| Input | ဖြေရှင်းသည့် အဆင့် | ရလဒ် |
| --- | --- | --- |
| `dirty` | NFC + fold + newline→space + collapse | `'Neo4j is a graph-database. "GraphRAG" ...'` |
| `tab` | newline→space (`\t` ပါဝင်) + collapse | `'Neo4j uses Cypher.'` |
| `decomposed` | NFC (compose) | `'café data'` |
| `ctrl` | control char ဖယ်ခြင်း | `'Neo4jingestdone'` |

`ctrl` ၏ ရလဒ်ကို သတိထားရမည် — `\x00` နှင့် `\x07` ကို ဖယ်လိုက်သောကြောင့် `Neo4j`
နှင့် `ingest` စာလုံးနှစ်လုံး **ကပ်သွား** သည်။ Control ဖယ်ခြင်းကို newline→space
အဆင့် **နောက်** တွင် ထားထားသောကြောင့် `\n` သည် space အဖြစ် ပြောင်းပြီးသား ဖြစ်သည်။
`\x00` ကဲ့သို့ formatting မဟုတ်သည့် control character များအတွက် ကပ်သွားခြင်းကို
လက်ခံနိုင်သည် — ၎င်းတို့သည် whitespace မဟုတ်ပါ။

အစီအစဉ်၏ rationale —

1. **NFC အရင်** — မတူညီသည့် byte များကို စုစည်းရန်၊ နောက်အဆင့်များ တူညီသည့် form ကို ရရန်။
2. **Fold ဒုတိယ** — character အစားထိုးခြင်းသည် NFC နှင့် မသက်ဆိုင်သောကြောင့် နောက်တွင် ထား။
3. **newline → space တတိယ** — control ဖယ်ခြင်းအရင် လုပ်ရမည်၊ မဟုတ်လျှင် စာလုံးများ ကပ်သွားမည်။
4. **Control ဖယ်ခြင်း စတုတ္ထ** — newline များ space ဖြစ်သွားပြီးမှ ကျန်သည်ကို ဖယ်သည်။
5. **Whitespace collapse နောက်ဆုံး** — အရှေ့အဆင့်များက ထည့်သည့် space များကို တစ်ပြေးညီစေရန်။

---

## 11. `normalize_document()` — Document အသစ်သည် normalized length ကို ယူသည်

```python
import re
import unicodedata
from dataclasses import dataclass

UNICODE_FOLD = {"\u2018": "'", "\u2019": "'", "\u201c": '"', "\u201d": '"',
                "\u2013": "-", "\u2014": "-", "\u2026": "...", "\u00a0": " "}


@dataclass
class Document:
    doc_id: str
    text: str
    char_count: int


def normalize_text(raw):
    text = unicodedata.normalize("NFC", raw)
    for src, dst in UNICODE_FOLD.items():
        text = text.replace(src, dst)
    text = re.sub(r"[\r\n\t\f\v]+", " ", text)
    text = "".join(ch for ch in text if unicodedata.category(ch)[0] != "C")
    return re.sub(r"\s+", " ", text).strip()


def normalize_document(doc):
    text = normalize_text(doc.text)
    return Document(doc.doc_id, text, len(text))


doc = Document("doc-001", "  Neo4j\u00a0 is  a graph\u2013database.  ", 40)
new = normalize_document(doc)
print(new)
```

Output —

```text
Document(doc_id='doc-001', text='Neo4j is a graph-database.', char_count=26)
```

`normalize_document()` သည် **Document အသစ်** ကို ပြန်ပေးသည် — မူရင်း `doc` ကို
မပြောင်းပါ။ `doc_id` ကို ရှိရင်းစွဲအတိုင်း ထိန်းထားပြီး `text` နှင့် `char_count` ကို
normalized တန်ဖိုးများဖြင့် အစားထိုးသည်။

မူရင်း `doc.text` အရှည် ၄၀ မှ normalized အရှည် ၂၆ သို့ လျော့သွားသည်ကို
`char_count=26` က ပြသည်။ Pipeline ထဲတွင် ဤသို့ **immutable-style** အလုပ်လုပ်ခြင်းသည်
မူရင်း raw text ကို ပြန်ကြည့်နိုင်စေသည် — audit အတွက် အရေးကြီးသည်။

---

## 12. Code တစ်ခုလုံး — Run လုပ်နိုင်သော Version

```python
import re
import unicodedata
from dataclasses import dataclass

SAMPLE_CORPUS = [
    {"doc_id": "doc-001", "raw_text": "Neo4j  is a graph database.\nNeo4j uses Cypher as its query language. "
                                      "GraphRAG is built on a Knowledge Graph. Nous Research develops open models."},
    {"doc_id": "doc-002", "raw_text": "Graph Rag runs on Neo4j. GraphRAG is built on a Knowledge Graph. "
                                      "Neo4j was developed by Neo4j Inc. Neo4j,  GraphRAG and Cypher are widely "
                                      "used in production."},
    {"doc_id": "doc-003", "raw_text": "Entity Resolution merges duplicate nodes. GraphRAG uses Entity Resolution. "
                                      "LLM is a Transformer based model. Entity resolution includes alias mapping."},
]
UNICODE_FOLD = {"\u2018": "'", "\u2019": "'", "\u201c": '"', "\u201d": '"',
                "\u2013": "-", "\u2014": "-", "\u2026": "...", "\u00a0": " "}


@dataclass
class Document:
    doc_id: str
    text: str
    char_count: int


def ingest_corpus(corpus):
    return [Document(d["doc_id"], d["raw_text"], len(d["raw_text"])) for d in corpus]


def normalize_text(raw):
    text = unicodedata.normalize("NFC", raw)
    for src, dst in UNICODE_FOLD.items():
        text = text.replace(src, dst)
    text = re.sub(r"[\r\n\t\f\v]+", " ", text)
    text = "".join(ch for ch in text if unicodedata.category(ch)[0] != "C")
    return re.sub(r"\s+", " ", text).strip()


def normalize_document(doc):
    text = normalize_text(doc.text)
    return Document(doc.doc_id, text, len(text))


documents = [normalize_document(doc) for doc in ingest_corpus(SAMPLE_CORPUS)]
for doc in documents:
    raw = [d for d in SAMPLE_CORPUS if d["doc_id"] == doc.doc_id][0]["raw_text"]
    print("%s | raw_chars=%3d | normalized_chars=%3d | %s"
          % (doc.doc_id, len(raw), doc.char_count, doc.text[:56]))

dirty = "  Neo4j\u00a0 is  a graph\u2013database.\n\n  \u201cGraphRAG\u201d  \u2026  "
print("dirty   : %r" % dirty)
print("cleaned : %r" % normalize_text(dirty))
```

Output —

```text
doc-001 | raw_chars=144 | normalized_chars=143 | Neo4j is a graph database. Neo4j uses Cypher as its quer
doc-002 | raw_chars=157 | normalized_chars=156 | Graph Rag runs on Neo4j. GraphRAG is built on a Knowledg
doc-003 | raw_chars=150 | normalized_chars=150 | Entity Resolution merges duplicate nodes. GraphRAG uses 
dirty   : '  Neo4j\xa0 is  a graph–database.\n\n  “GraphRAG”  …  '
cleaned : 'Neo4j is a graph-database. "GraphRAG" ...'
```

### ရလဒ်ကို ပြန်ကြည့်ခြင်း

| Document | raw_chars | normalized_chars | ကွာခြားရသည့် အကြောင်းရင်း |
| --- | --- | --- | --- |
| `doc-001` | 144 | 143 | `\n` → space (အရှည်တူ)၊ ကပ်နေသော space တစ်လုံး ဖယ် (၁ လုံး လျော့) |
| `doc-002` | 157 | 156 | `Neo4j,  GraphRAG` ထဲက ထပ်နေသော space တစ်လုံး ဖယ် |
| `doc-003` | 150 | 150 | ဖယ်စရာ `\n`၊ smart char သို့မဟုတ် ထပ်နေသော space မရှိ |

`doc-003` မပြောင်းလဲခြင်းသည် အရေးကြီးသည် — normalization တွင် ပြင်စရာ မရှိလျှင်
text ကို **ချုပ်တည်း** ထားသည် (idempotent)။

Function ကို run ကြည့်လျှင် မှားယွင်းမှု ရှိမရှိ စစ်ရန် `assert` ထည့်သည်။

```python
import re
import unicodedata

UNICODE_FOLD = {"\u2018": "'", "\u2019": "'", "\u201c": '"', "\u201d": '"',
                "\u2013": "-", "\u2014": "-", "\u2026": "...", "\u00a0": " "}


def normalize_text(raw):
    text = unicodedata.normalize("NFC", raw)
    for src, dst in UNICODE_FOLD.items():
        text = text.replace(src, dst)
    text = re.sub(r"[\r\n\t\f\v]+", " ", text)
    text = "".join(ch for ch in text if unicodedata.category(ch)[0] != "C")
    return re.sub(r"\s+", " ", text).strip()


dirty = "  Neo4j\u00a0 is  a graph\u2013database.\n\n  \u201cGraphRAG\u201d  \u2026  "
cleaned = normalize_text(dirty)
assert cleaned == 'Neo4j is a graph-database. "GraphRAG" ...'
assert "  " not in cleaned and "\n" not in cleaned
print("assertion passed")
```

Output —

```text
assertion passed
```

`assert` သည် condition `False` ဖြစ်လျှင် `AssertionError` ဖြင့် ကျရှုံးသည်။
မှန်လျှင် ဘာမှ မလုပ်ဘဲ ဆက်သွားသည်။ ထို့ကြောင့် pipeline ၏ normalization ရလဒ်ကို
run တိုင်း စစ်နိုင်သည်။

---

## 13. ကိုယ်တိုင်လေ့ကျင့်ကြည့်ပါ

**မေးခွန်း** — အောက်ပါ code သည် မည်သည့်ရလဒ် ပြန်ပေးမည်နည်း။

```python
import re


def strip_markup(raw):
    text = re.sub(r"[\r\n\t]+", "", raw)
    return re.sub(r"\s+", " ", text).strip()


print(repr(strip_markup("Neo4j uses\nCypher")))
```

1. `'Neo4j uses Cypher'` — newline က space အဖြစ် ပြောင်းပြီး collapse လုပ်လိုက်သည်
2. `'Neo4jusesCypher'` — newline ဖယ်ပြီး space မကျန်
3. `'Neo4j uses\nCypher'` — ဘာမှ မပြောင်း
4. `'Neo4j usesCypher'` — newline ဖယ်လိုက်သဖြင့် စာလုံးကပ်

<details>
<summary>အဖြေ ကြည့်ရန်</summary>

**အဖြေ — 4. `'Neo4j usesCypher'`**

အကြောင်းရင်း — ဤ variant တွင် replacement string သည် `""` (empty) ဖြစ်သည်။
`re.sub(r"[\r\n\t]+", "", raw)` သည် newline ကို **ဖျက်ပစ်** လိုက်သဖြင့်
`"Neo4j uses"` နှင့် `"Cypher"` ကပ်သွားသည် — `'Neo4j usesCypher'`။ ထို့နောက်
`\s+` collapse သည် ကျန်နေသည့် space ကို ပြင်သော်လည်း **ဖျက်ပြီးသား space ကို ပြန်မဖန်တီး**
နိုင်ပါ။ ထို့ကြောင့် Exercise 1 ၏ `normalize_text` သည် `" "` (space) ဖြင့် အစားထိုးသည့်
အဆင့်ကို control char ဖယ်ခြင်းအရင် ထားထားသည်။

</details>

---

**အဓိက မှတ်ထားရန်** — Normalization သည် ပထမဆုံး မလိုအပ်လှဟု ထင်ရပေမဲ့ pipeline
တစ်ခုလုံး၏ **determinism** ကို သတ်မှတ်ပေးသည်။ NFC မလုပ်ပါက တူညီသော entity
နှစ်ခု byte level တွင် ကွဲသွားပြီး duplicate node ဖြစ်လာသည်။ Newline ကို ဖျက်ပစ်ပါက
sentence boundary ပျက်ပြီး chunker နှင့် extractor မှားသည်။ အဆင့်အစီအစဉ်သည်လည်း
အရေးကြီးသည် — NFC → fold → newline→space → control ဖယ်ခြင်း → whitespace collapse။
ဤ function သည် idempotent ဖြစ်သဖြင့် နှစ်ကြိမ် run လုပ်လျှင် ရလဒ် မပြောင်းလဲပါ။
