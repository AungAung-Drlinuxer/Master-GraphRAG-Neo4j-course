# Walkthrough 05 — Text-to-Cypher Guardrails (Exercise 5)

> ဤဖိုင်သည် Module 07 ၏ `solution.md` ထဲက Exercise 5 ကို **Python အခြေခံမှ စ၍**
> အပိုင်းလိုက် ရှင်းပြသည့် walkthrough ဖြစ်သည်။ Format သည် Module 01 ၏
> `walkthroughs/01_regex_ner.md` နှင့် `walkthroughs/03_gazetteer_lookup.md` နှင့်
> တူညီသည်။

---

## 0. ဤ Exercise က ဘာကို ဖြေရှင်းပေးသလဲ။

**Text-to-Cypher** တွင် LLM သည် user ၏ natural language မေးခွန်းမှ Cypher query ကို
ထုတ်ပေးသည်။ ပြဿနာမှာ — LLM သည် `MATCH` တစ်ခုတည်း မဟုတ်ဘဲ `CREATE`၊ `MERGE`၊
`DELETE` စသည့် **destructive clause** များကိုလည် ထုတ်နိုင်သည်။ ထို့ကြောင့်
query ကို execute မလုပ်မီ **guardrail** တစ်ခုဖြင့် စစ်ရသည်။

```text
user question
     |
     v
LLM  --->  "MATCH (p:Product) DETACH DELETE p"     <- dangerous
     |
     v
validate_cypher()  --->  (False, "destructive clause rejected: DELETE, DETACH")
     |
     v
execute မလုပ်ပါ ✗
```

ဤ exercise ၏ validator သည် အဆင့် ၅ ခုကို **အစဉ်လိုက်** စစ်သည် —

| အဆင့် | စစ်သည့်အရာ | မအောင်လျှင် reason |
| --- | --- | --- |
| ၁ | အလွတ် မဖြစ်ရ၊ အရှည် `MAX_LENGTH` အတွင်း | `empty query` / `query exceeds 2000 characters` |
| ၂ | statement တစ်ခုတည်း | `multiple statements are not allowed` |
| ၃ | destructive keyword မပါရ | `destructive clause rejected: ...` |
| ၄ | read-only clause ဖြင့် စရ | `query must start with a read-only clause, got ...` |
| ၅ | `RETURN` ပါရ၊ label များ schema အတွင်း | `query must project results with RETURN` / `labels outside the schema allowlist: ...` |

**Security note** — ဤ validator သည် **defense in depth ၏ တစ်ဆင့်သာ** ဖြစ်သည်။
Keyword blacklist ကို obfuscation ဖြင့် ကျော်နိုင်နိုင်သည်။ ထို့ကြောင့် database
user ကို **read-only role** ဖြင့် bind လုပ်ခြင်းနှင့် `LIMIT` ကို server side တွင်
အတင်းသတ်မှတ်ခြင်းကို မဖြစ်မနေ လုပ်ရမည်။

ဤ code မှာ လေ့လာရမည့် Python concepts များမှာ —

- `re.compile()` နှင့် module-level constant regex
- `re.DOTALL` flag
- `Pattern.sub()` (replace) နှင့် method chaining
- Set comprehension + nested comprehension (`{... for ... for ...}`)
- `frozenset`
- `for ... in` တွင် tuple unpacking (candidate `(query, expected)` များ)
- Short-circuit `if not query or not query.strip()`
- `f-string` ဖြင့် reason ထုတ်ခြင်း
- `str.split()[0]`, `str.upper()`, `str.endswith()`
- `raise` မလိုဘဲ `(ok, reason)` tuple ပြန်ခြင်း

---

## 1. Regex Constants — ကြိုတင် compile လုပ်ခြင်း

```python
import re

BLOCK_COMMENT_RE = re.compile(r"/\*.*?\*/", re.DOTALL)
LINE_COMMENT_RE = re.compile(r"//[^\n]*")
STRING_LITERAL_RE = re.compile(r"'(?:[^'\\]|\\.)*'|\"(?:[^\"\\]|\\.)*\"")
REL_DETAIL_RE = re.compile(r"\[[^\]]*\]")
NODE_BLOCK_RE = re.compile(r"\(([^()]*)\)")
LABEL_RE = re.compile(r":\s*([A-Za-z_][A-Za-z0-9_]*)")
```

Regex ကို module level တွင် တစ်ကြိမ် `re.compile()` လုပ်ပြီး constant အဖြစ်
သိမ်းထားသည်။ `re.compile()` သည် pattern ကို parse လုပ်ပြီး pattern object
တစ်ခု ပြန်သည် — အကြိမ်များစွာ သုံးလျှင် compile လုပ်ထားတာ ပိုထိရောက်သည်။

| Constant | Pattern | ရှာသည့်အရာ |
| --- | --- | --- |
| `BLOCK_COMMENT_RE` | `/\*.*?\*/` + `DOTALL` | `/* ... */` block comment |
| `LINE_COMMENT_RE` | `//[^\n]*` | `//` မှ လိုင်းအဆုံးအထိ |
| `STRING_LITERAL_RE` | `'(?:[^'\\]\|\\\\.)*'` (သို့) `"..."` | string literal |
| `REL_DETAIL_RE` | `\[[^\]]*\]` | `[...]` — relationship detail |
| `NODE_BLOCK_RE` | `\(([^()]*)\)` | `(...)` — node block (capture group ပါ) |
| `LABEL_RE` | `:\s*([A-Za-z_][A-Za-z0-9_]*)` | `:Label` |

`.*?` သည် **non-greedy** ဖြစ်သည် — `/*` နှင့် `*/` ကြား အတိုဆုံးအပိုင်းကို ယူသည်။
`re.DOTALL` သည် `.` ကို newline ပါ ကိုက်ညီစေသည် — block comment သည် လိုင်း
အများအပြား ဖြတ်နိုင်သဖြင့် လိုအပ်သည်။

### 1.1 `_strip_inert()` — Comment နှင့် string literal ဖယ်ရှားခြင်း

```python
def _strip_inert(query):
    """Remove comments and string literals: their content cannot mutate anything."""
    query = BLOCK_COMMENT_RE.sub(" ", query)
    return STRING_LITERAL_RE.sub(" '?' ", LINE_COMMENT_RE.sub(" ", query))
```

`Pattern.sub(replacement, string)` သည် ကိုက်ညီသမျှကို replacement ဖြင့်
**အစားထိုး** ပြီး string အသစ် ပြန်သည်။ နောက်ဆုံးလိုင်းသည် method chaining
ဖြစ်သည် — `LINE_COMMENT_RE.sub` ကို အရင် run ပြီး ရလဒ်ကို
`STRING_LITERAL_RE.sub` ထဲ ထည့်သည်။

**အဓိကအယူအဆ** — Comment နှင့် string literal ၏ content သည် database ပေါ်တွင်
**ဘာမှ မလုပ်နိုင်ပါ**။ ထို့ကြောင့် keyword scan မတိုင်မီ ၎င်းတို့ကို ဖယ်ရှားခြင်းသည်
false positive ကို လျှော့သည်။

```python
import re

BLOCK_COMMENT_RE = re.compile(r"/\*.*?\*/", re.DOTALL)
LINE_COMMENT_RE = re.compile(r"//[^\n]*")
STRING_LITERAL_RE = re.compile(r"'(?:[^'\\]|\\.)*'|\"(?:[^\"\\]|\\.)*\"")


def _strip_inert(query):
    query = BLOCK_COMMENT_RE.sub(" ", query)
    return STRING_LITERAL_RE.sub(" '?' ", LINE_COMMENT_RE.sub(" ", query))


for q in ["MATCH (n:Product) RETURN n // harmless trailing note",
          "MATCH (n) /* block CREATE comment */ RETURN n",
          "MATCH (n {name: 'DROP TABLE'}) RETURN n"]:
    print(repr(q))
    print("  ->", repr(_strip_inert(q)))
```

Output —

```text
'MATCH (n:Product) RETURN n // harmless trailing note'
  -> 'MATCH (n:Product) RETURN n  '
'MATCH (n) /* block CREATE comment */ RETURN n'
  -> 'MATCH (n)   RETURN n'
"MATCH (n {name: 'DROP TABLE'}) RETURN n"
  -> "MATCH (n {name:  '?' }) RETURN n"
```

သုံးခုလုံးတွင် keyword ပါသည့် content များ (`CREATE`၊ `DROP`) သည် **ဖယ်ရှား**
ခံရသည်ကို တွေ့နိုင်သည်။ Comment ကို space တစ်လုံးဖြင့်၊ string literal ကို
`'?'` ဖြင့် အစားထိုးသဖြင့် စာသား၏ ကျန်အပိုင်း **အနေအထား မပြောင်း**ပါ —
ဖယ်ရှားလိုက်လျှင် စာလုံးနှစ်လုံး ကပ်သွားပြီး token အသစ် ဖြစ်နိုင်သည်။

---

## 2. `FORBIDDEN_KEYWORDS` နှင့် Token Scan

```python
FORBIDDEN_KEYWORDS = ("CREATE", "MERGE", "DELETE", "DETACH", "SET", "REMOVE", "DROP",
                      "FOREACH", "LOAD", "CALL", "GRANT", "DENY", "REVOKE", "ALTER", "RENAME")
READ_ONLY_START = ("MATCH", "OPTIONAL MATCH", "WITH", "UNWIND")
MAX_LENGTH = 2000
```

Scan သည် **word boundary ဖြင့်** လုပ်သည်၊ substring ဖြင့် မဟုတ်ပါ။ ထို့ကြောင့်
`re.findall(r"[A-Z_]+", body.upper())` ဖြင့် token များကို ရှာပြီး set အဖြစ်
ပြောင်းသည်။

```python
import re

FORBIDDEN_KEYWORDS = ("CREATE", "MERGE", "DELETE", "DETACH", "SET", "REMOVE", "DROP",
                      "FOREACH", "LOAD", "CALL", "GRANT", "DENY", "REVOKE", "ALTER", "RENAME")
words = set(re.findall(r"[A-Z_]+", "MATCH (p:Product) DETACH DELETE p".upper()))
print(sorted(words))
print(sorted(kw for kw in FORBIDDEN_KEYWORDS if kw in words))
```

Output —

```text
['DELETE', 'DETACH', 'MATCH', 'P', 'PRODUCT']
['DELETE', 'DETACH']
```

⚠️ **`print(words)` (sorted မလုပ်ဘဲ) ၏ ပြသအစီအစဉ်သည် run တစ်ခုနှင့်တစ်ခု ကွဲနိုင်သည်** —
`set` ၏ iteration order ကို Python က အာမမခံပါ။ ဤ walkthrough ကို ရေးသည့် run
တစ်ခုတွင် `{'MATCH', 'DETACH', 'PRODUCT', 'DELETE', 'P'}` ဟု ပေါ်ပြီး အခြား run
တွင် `{'P', 'PRODUCT', 'DETACH', 'MATCH', 'DELETE'}` ဟု ပေါ်သည် — နှစ်မျိုးလုံး
တကယ် တွေ့ထားသည်။ ထို့ကြောင့် ပြသရာနှင့် assert လုပ်ရာတွင် **အမြဲ `sorted()`**
ကို သုံးရသည် — ထို့ကြောင့် ဤ snippet သည် `sorted(words)` ကို print သည်။

### 2.1 Keyword scan ၏ ကန့်သတ်ချက် — တကယ် စမ်းကြည့်ခြင်း

`[A-Z_]+` သည် uppercase စာလုံးနှင့် underscore ဆက်နေသည့် အပိုင်းကို **တစ်ခုတည်း**
token အဖြစ် ယူသည်။ ထို့ကြောင့် `set_order` သည် `SET_ORDER` ဖြစ်ပြီး `SET` နှင့်
**မတူပါ**။ သို့သော် property အမည် ကိုယ်တိုင် keyword တစ်လုံးတည်း ဖြစ်လျှင်
false positive ဖြစ်သည်။

```python
import re

FORBIDDEN_KEYWORDS = ("CREATE", "MERGE", "DELETE", "DETACH", "SET", "REMOVE", "DROP",
                      "FOREACH", "LOAD", "CALL", "GRANT", "DENY", "REVOKE", "ALTER", "RENAME")


def scan(body):
    words = set(re.findall(r"[A-Z_]+", body.upper()))
    return sorted(kw for kw in FORBIDDEN_KEYWORDS if kw in words)


for q in ["MATCH (n) RETURN n.remove AS r", "MATCH (n) RETURN n.create AS created",
          "MATCH (n) RETURN n.set_order AS s", "MATCH (n) RETURN n.delete_flag AS d",
          "MATCH (n) RETURN n AS set"]:
    print("  %-42s -> %s" % (q, scan(q)))
```

Output —

```text
  MATCH (n) RETURN n.remove AS r             -> ['REMOVE']
  MATCH (n) RETURN n.create AS created       -> ['CREATE']
  MATCH (n) RETURN n.set_order AS s          -> []
  MATCH (n) RETURN n.delete_flag AS d        -> []
  MATCH (n) RETURN n AS set                  -> ['SET']
```

| Query | Scan ရလဒ် | တကယ့် အဓိပ္ပာယ် |
| --- | --- | --- |
| `RETURN n.remove AS r` | `['REMOVE']` | **false positive** — `remove` သည် property အမည် |
| `RETURN n.create AS created` | `['CREATE']` | **false positive** — property အမည် |
| `RETURN n.set_order AS s` | `[]` | token တစ်ခုတည်းမို့ မှန်ကန်စွာ ကျော်သည် |
| `RETURN n.delete_flag AS d` | `[]` | token တစ်ခုတည်းမို့ မှန်ကန်စွာ ကျော်သည် |
| `RETURN n AS set` | `['SET']` | **false positive** — alias အမည် |

ဤဇယားက **token-based blacklist ၏ အားနည်းချက်** ကို ရှင်းရှင်းလင်းလင်း ပြသည် —
property သို့မဟုတ် alias အမည် keyword တစ်လုံးတည်း ဖြစ်လျှင် query အပြစ်မရှိသော်လည်း
reject ခံရမည်။ ဤကဲ့သို့ case အတွက် production တွင် parse tree (AST) ဖြင့်
စစ်ခြင်း လိုအပ်သည်။ ဤ exercise ၏ validator သည် **conservative** ဖြစ်သည် —
မှားမှားမှန်မှန် သံသယဖြစ်လျှင် reject လုပ်သည်။

---

## 3. `validate_cypher()` — Function တစ်ခုလုံး

```python
def validate_cypher(query, allowed_labels=None, max_length=MAX_LENGTH):
    """Return (ok, reason). Read-only enforcement for LLM generated Cypher."""
    if not query or not query.strip():
        return False, "empty query"
    if len(query) > max_length:
        return False, f"query exceeds {max_length} characters"
    body = _strip_inert(query).strip()
    if body.endswith(";"):
        body = body[:-1].strip()
    if ";" in body:
        return False, "multiple statements are not allowed"
    words = set(re.findall(r"[A-Z_]+", body.upper()))
    hit = sorted(kw for kw in FORBIDDEN_KEYWORDS if kw in words)
    if hit:
        return False, f"destructive clause rejected: {', '.join(hit)}"
    first = body.split()[0].upper()
    if first not in READ_ONLY_START:
        return False, f"query must start with a read-only clause, got {first!r}"
    if "RETURN" not in words:
        return False, "query must project results with RETURN"
    if allowed_labels is not None:
        unknown = [lab for lab in node_labels(query) if lab not in allowed_labels]
        if unknown:
            return False, f"labels outside the schema allowlist: {', '.join(unknown)}"
    return True, "read-only query accepted"
```

### 3.1 `(ok, reason)` ပြန်ခြင်း — `raise` မလိုဘဲ

Function သည် **tuple** `(bool, str)` ပြန်သည်။ ဤပုံစံကို **result tuple** ဟု
ခေါ်သည် — caller က `ok, reason = validate_cypher(q)` လို့ ခွဲယူသည်။ Error
ကို exception ဖြင့် မပြဘဲ **ပြန်တန်ဖိုး** အဖြစ် ပြခြင်းသည် batch validation
တွင် အဆင်ပြေသည် — candidate ၁၀၀ ကို run လုပ်ရာတွင် ပထမတစ်ခုက exception
မဖြစ်စေဘဲ အားလုံး၏ reason ကို စုနိုင်သည်။

### 3.2 အဆင့် ၁ — အလွတ် နှင့် အရှည်

```python
if not query or not query.strip():
    return False, "empty query"
```

`not query` သည် empty string အတွက် `True`။ `or` သည် **short-circuit** ဖြစ်သဖြင့်
`query` empty ဖြစ်လျှင် `query.strip()` ကို မခေါ်တော့ပါ။ `"   "` (space သာ)
ဖြစ်လျှင် `not query` သည် `False` ဖြစ်သော်လည်း `not query.strip()` က `True`
ဖြစ်သဖြင့် ဖမ်းမိသည်။

### 3.3 အဆင့် ၂ — statement တစ်ခုတည်း

```python
if body.endswith(";"):
    body = body[:-1].strip()
if ";" in body:
    return False, "multiple statements are not allowed"
```

`body.endswith(";")` သည် နောက်ဆုံးစာလုံးကို စစ်သည်။ `body[:-1]` သည် **နောက်ဆုံး
စာလုံးမှလွဲ၍** အားလုံးကို ယူသည် (negative index slicing)။ ထို့ကြောင့်
`MATCH (n) RETURN n;` သည် accept ခံရသည် — semicolon တစ်ခုတည်း အဆုံးတွင်
ရှိခြင်းသည် အန္တရာယ် မရှိပါ။ ထို့နောက် `;` ကျန်သေးလျှင် statement အများအပြား
ဖြစ်သည်ဟု reject သည်။

### 3.4 အဆင့် ၃ — destructive keyword

```python
words = set(re.findall(r"[A-Z_]+", body.upper()))
hit = sorted(kw for kw in FORBIDDEN_KEYWORDS if kw in words)
if hit:
    return False, f"destructive clause rejected: {', '.join(hit)}"
```

`', '.join(hit)` သည် list ကို `", "` ဖြင့် ဆက်သည် — `DELETE, DETACH`။ `sorted()`
ဖြင့် စီထားသဖြင့် reason စာသား တည်ငြိမ်သည်။

### 3.5 အဆင့် ၄ နှင့် ၅ — read-only clause နှင့် `RETURN`

```python
first = body.split()[0].upper()
if first not in READ_ONLY_START:
    return False, f"query must start with a read-only clause, got {first!r}"
if "RETURN" not in words:
    return False, "query must project results with RETURN"
```

`body.split()[0]` သည် ပထမ **token** ကို ယူသည်။ `{first!r}` သည် `repr()` ဖြင့်
ပြသည် — ထို့ကြောင့် quote ပါလာသည်။ `"RETURN" not in words` သည် set membership
ဖြစ်သည်။

### 3.6 အဆင့် ၅ (နောက်ဆုံး) — label allowlist

```python
if allowed_labels is not None:
    unknown = [lab for lab in node_labels(query) if lab not in allowed_labels]
    if unknown:
        return False, f"labels outside the schema allowlist: {', '.join(unknown)}"
```

`allowed_labels` သည် `frozenset` ဖြစ်သည် (Section 4)။ `allowed_labels is not None`
ဖြစ်လျှင် သာ label စစ်ခြင်းကို လုပ်သည် — caller က null ပေးလျှင် label စစ်ခြင်း
ကို ကျော်သည်။ ဤအချက်က **schema မသိလျှင် schema စစ်၍မရ** ဆိုသည့် အခြေအနေကို
ကိုင်တွယ်သည်။

---

## 4. `node_labels()` — Rel Bracket ကို ကြိုတင် ဖယ်ရှားခြင်း

```python
def node_labels(query):
    """Extract node labels only — relationship types are stripped first."""
    body = REL_DETAIL_RE.sub(" ", _strip_inert(query))
    return sorted({lab for block in NODE_BLOCK_RE.findall(body)
                   for lab in LABEL_RE.findall(block)})
```

Return လိုင်းသည် **nested comprehension** ဖြစ်သည် — အပြင်က set comprehension၊
အတွင်းက list comprehension။

```text
{ lab                                <- set အဖြစ် စု
  for block in NODE_BLOCK_RE.findall(body)     <- node block တိုင်း
  for lab in LABEL_RE.findall(block) }         <- ထို block ထဲက label တိုင်း
```

`NODE_BLOCK_RE` သည် capture group ပါသဖြင့် `findall()` သည် **group ၏ content**
များကို ပြန်သည် (`(...)` အပါ မဟုတ်)။ `REL_DETAIL_RE.sub(" ", ...)` သည် `[...]`
များကို ဖယ်သည်။

```python
import re

BLOCK_COMMENT_RE = re.compile(r"/\*.*?\*/", re.DOTALL)
LINE_COMMENT_RE = re.compile(r"//[^\n]*")
STRING_LITERAL_RE = re.compile(r"'(?:[^'\\]|\\.)*'|\"(?:[^\"\\]|\\.)*\"")
REL_DETAIL_RE = re.compile(r"\[[^\]]*\]")
NODE_BLOCK_RE = re.compile(r"\(([^()]*)\)")
LABEL_RE = re.compile(r":\s*([A-Za-z_][A-Za-z0-9_]*)")


def _strip_inert(query):
    query = BLOCK_COMMENT_RE.sub(" ", query)
    return STRING_LITERAL_RE.sub(" '?' ", LINE_COMMENT_RE.sub(" ", query))


def node_labels(query):
    body = REL_DETAIL_RE.sub(" ", _strip_inert(query))
    return sorted({lab for block in NODE_BLOCK_RE.findall(body)
                   for lab in LABEL_RE.findall(block)})


for q in ["MATCH (c:Company)-[:DEVELOPS]->(p:Product) WHERE c.name = $name RETURN p.name AS product ORDER BY product LIMIT 10",
          "MATCH (x:Secret) RETURN x"]:
    print(repr(q))
    print("  ->", node_labels(q))
```

Output —

```text
'MATCH (c:Company)-[:DEVELOPS]->(p:Product) WHERE c.name = $name RETURN p.name AS product ORDER BY product LIMIT 10'
  -> ['Company', 'Product']
'MATCH (x:Secret) RETURN x'
  -> ['Secret']
```

ပထမ query တွင် `DEVELOPS` သည် relationship type ဖြစ်သော်လည်း ရလဒ်တွင် **မပါပါ** —
node label (`Company`၊ `Product`) နှစ်ခုသာ ပါသည်။ `c.name = $name` ထဲက
`name` လည် label အဖြစ် မမှတ်မိပါ — `LABEL_RE` သည် `:` နှင့် စသည့် pattern ကိုသာ
ရှာသည်။

### 4.1 `REL_DETAIL_RE` ဖယ်ရှားခြင်းက တကယ် လိုသလား

ဤအချက်ကို **စမ်းပြီးမှ** ဆိုရမည်။ ပုံမှန် Cypher တွင် rel detail `[...]` သည်
ကွင်းအတွင်း မရှိပါ — ဥပမာ `(a)-[:DEVELOPS]->(b)` တွင် `[:DEVELOPS]` သည်
`(a)` နှင့် `(b)` ကြား၌ ရှိသည်။ ထို့ကြောင့် `NODE_BLOCK_RE` က ဖမ်းမိမည် မဟုတ်ပါ။

```python
import re

REL_DETAIL_RE = re.compile(r"\[[^\]]*\]")
NODE_BLOCK_RE = re.compile(r"\(([^()]*)\)")
LABEL_RE = re.compile(r":\s*([A-Za-z_][A-Za-z0-9_]*)")

q = "MATCH (n {kinds: [:Product]}) RETURN n"
naive = sorted({lab for block in NODE_BLOCK_RE.findall(q) for lab in LABEL_RE.findall(block)})
stripped = sorted({lab for block in NODE_BLOCK_RE.findall(REL_DETAIL_RE.sub(" ", q))
                   for lab in LABEL_RE.findall(block)})
print("naive   :", naive)
print("stripped:", stripped)
```

Output —

```text
naive   : ['Product']
stripped: []
```

ကွင်းအတွင်းက `[:Product]` ကို naive version က **label** အဖြစ် မှားဖတ်သဖြင့်
`Product` ပေါ်လာသည်။ ဤအချက်က ဖယ်ရှားခြင်းသည် **defensive** ဖြစ်သည့်
အကြောင်းရင်း ဖြစ်သည် — ပုံမှန် query တွင် မလိုသော်လည်း edge case တွင်
အကာအကွယ် ဖြစ်သည်။

---

## 5. Candidate ၉ ခုကို တကယ် run ခြင်း

```python
import re

NODES = {
    "co:neo4j": ("Company", "Neo4j", ("Neo4j Inc", "Neo4j, Inc."), "Graph database vendor."),
    "prod:aura": ("Product", "AuraDB", ("Neo4j AuraDB", "Aura"), "Managed cloud service."),
    "tech:cypher": ("Technology", "Cypher", ("openCypher", "Cypher Query Language"), "Declarative graph query language."),
    "org:neo4jeng": ("Team", "Neo4j Engineering", (), "Engineering team."),
}
ALLOWED_LABELS = frozenset(node[0] for node in NODES.values())

BLOCK_COMMENT_RE = re.compile(r"/\*.*?\*/", re.DOTALL)
LINE_COMMENT_RE = re.compile(r"//[^\n]*")
STRING_LITERAL_RE = re.compile(r"'(?:[^'\\]|\\.)*'|\"(?:[^\"\\]|\\.)*\"")
REL_DETAIL_RE = re.compile(r"\[[^\]]*\]")
NODE_BLOCK_RE = re.compile(r"\(([^()]*)\)")
LABEL_RE = re.compile(r":\s*([A-Za-z_][A-Za-z0-9_]*)")
FORBIDDEN_KEYWORDS = ("CREATE", "MERGE", "DELETE", "DETACH", "SET", "REMOVE", "DROP",
                      "FOREACH", "LOAD", "CALL", "GRANT", "DENY", "REVOKE", "ALTER", "RENAME")
READ_ONLY_START = ("MATCH", "OPTIONAL MATCH", "WITH", "UNWIND")
MAX_LENGTH = 2000


def _strip_inert(query):
    query = BLOCK_COMMENT_RE.sub(" ", query)
    return STRING_LITERAL_RE.sub(" '?' ", LINE_COMMENT_RE.sub(" ", query))


def node_labels(query):
    body = REL_DETAIL_RE.sub(" ", _strip_inert(query))
    return sorted({lab for block in NODE_BLOCK_RE.findall(body)
                   for lab in LABEL_RE.findall(block)})


def validate_cypher(query, allowed_labels=None, max_length=MAX_LENGTH):
    if not query or not query.strip():
        return False, "empty query"
    if len(query) > max_length:
        return False, f"query exceeds {max_length} characters"
    body = _strip_inert(query).strip()
    if body.endswith(";"):
        body = body[:-1].strip()
    if ";" in body:
        return False, "multiple statements are not allowed"
    words = set(re.findall(r"[A-Z_]+", body.upper()))
    hit = sorted(kw for kw in FORBIDDEN_KEYWORDS if kw in words)
    if hit:
        return False, f"destructive clause rejected: {', '.join(hit)}"
    first = body.split()[0].upper()
    if first not in READ_ONLY_START:
        return False, f"query must start with a read-only clause, got {first!r}"
    if "RETURN" not in words:
        return False, "query must project results with RETURN"
    if allowed_labels is not None:
        unknown = [lab for lab in node_labels(query) if lab not in allowed_labels]
        if unknown:
            return False, f"labels outside the schema allowlist: {', '.join(unknown)}"
    return True, "read-only query accepted"


candidates = (
    ("MATCH (p:Product {id: $id}) RETURN p.name AS name, p.summary AS summary", True),
    ("MATCH (c:Company)-[:DEVELOPS]->(p:Product) WHERE c.name = $name "
     "RETURN p.name AS product ORDER BY product LIMIT 10", True),
    ("MATCH (p:Product) DETACH DELETE p", False),
    ("MATCH (n) DROP INDEX n", False),
    ("MATCH (n) SET n.owner = $owner RETURN n", False),
    ("CREATE (n:Product {id: $id}) RETURN n", False),
    ("MATCH (n) RETURN n; MATCH (m) DELETE m", False),
    ("MATCH (n:Product) RETURN n // harmless trailing note", True),
    ("MATCH (x:Secret) RETURN x", False),
)
for query, expected_ok in candidates:
    ok, reason = validate_cypher(query, allowed_labels=ALLOWED_LABELS)
    print("  ok=%-5s expected=%-5s %-45s| %s" % (ok, expected_ok, reason, query[:56]))
```

Output —

```text
  ok=True  expected=True  read-only query accepted                     | MATCH (p:Product {id: $id}) RETURN p.name AS name, p.sum
  ok=True  expected=True  read-only query accepted                     | MATCH (c:Company)-[:DEVELOPS]->(p:Product) WHERE c.name 
  ok=False expected=False destructive clause rejected: DELETE, DETACH  | MATCH (p:Product) DETACH DELETE p
  ok=False expected=False destructive clause rejected: DROP            | MATCH (n) DROP INDEX n
  ok=False expected=False destructive clause rejected: SET             | MATCH (n) SET n.owner = $owner RETURN n
  ok=False expected=False destructive clause rejected: CREATE          | CREATE (n:Product {id: $id}) RETURN n
  ok=False expected=False multiple statements are not allowed          | MATCH (n) RETURN n; MATCH (m) DELETE m
  ok=True  expected=True  read-only query accepted                     | MATCH (n:Product) RETURN n // harmless trailing note
  ok=False expected=False labels outside the schema allowlist: Secret  | MATCH (x:Secret) RETURN x
```

ဤ snippet တွင် `query[:56]` ဖြင့် query ကို ၅၆ လုံးအထိ ဖြတ်ပြထားသည် — output
တွင် အလယ်ကော်လံ အနေအထား မပျက်စေရန် ဖြစ်သည်။

| Candidate | `ok` | Reason | ဘာကို စစ်သလဲ |
| --- | --- | --- | --- |
| parameterized `MATCH` | True | read-only query accepted | baseline |
| `MATCH` + `LIMIT` | True | read-only query accepted | `LIMIT` ပါသော read |
| `DETACH DELETE` | False | destructive clause rejected: DELETE, DETACH | အဆင့် ၃ |
| `DROP INDEX` | False | destructive clause rejected: DROP | အဆင့် ၃ |
| `SET` | False | destructive clause rejected: SET | အဆင့် ၃ |
| `CREATE` | False | destructive clause rejected: CREATE | အဆင့် ၄ (first) မတိုင်မီ ဖမ်းမိ |
| multiple statement | False | multiple statements are not allowed | အဆင့် ၂ |
| trailing `//` comment | True | read-only query accepted | ဖယ်ရှားမှု အလုပ်လုပ်သည် |
| unknown label `Secret` | False | labels outside the schema allowlist: Secret | အဆင့် ၅ |

Candidate ၉ ခုအနက် **၆ ခု** reject ခံရသည် — exercise ၏ expected behavior နှင့်
ကိုက်ညီသည်။ `CREATE (n:Product {id: $id}) RETURN n` တွင် `CREATE` သည်
အဆင့် ၄ (first token) မတိုင်မီ **အဆင့် ၃** တွင် ဖမ်းမိသည်ကို သတိထားပါ —
reason သည် `destructive clause rejected` ဖြစ်ပြီး `query must start with ...`
**မဖြစ်ပါ**။ အစဉ်လိုက်စစ်ခြင်း၏ အကျိုးဆက်ကို ဤအချက်က ပြသည်။

---

## 6. Boundary Cases — တကယ် စမ်းထားသည့် ဇယား

Validator ၏ အစွန်းအဖျား အပြုအမူများကို တိုက်ရိုက် run ကြည့်ပါ။ ဤ snippet သည်
`validate_cypher()` ၏ core အစိတ်အပိုင်းများကို အတိုချုပ်ထားသည် (label
allowlist မပါ)။

```python
import re

READ_ONLY_START = ("MATCH", "OPTIONAL MATCH", "WITH", "UNWIND")
FORBIDDEN_KEYWORDS = ("CREATE", "MERGE", "DELETE", "DETACH", "SET", "REMOVE", "DROP")


def validate_cypher(query):
    if not query or not query.strip():
        return False, "empty query"
    body = query.strip()
    if body.endswith(";"):
        body = body[:-1].strip()
    if ";" in body:
        return False, "multiple statements are not allowed"
    words = set(re.findall(r"[A-Z_]+", body.upper()))
    hit = sorted(kw for kw in FORBIDDEN_KEYWORDS if kw in words)
    if hit:
        return False, f"destructive clause rejected: {', '.join(hit)}"
    first = body.split()[0].upper()
    if first not in READ_ONLY_START:
        return False, f"query must start with a read-only clause, got {first!r}"
    if "RETURN" not in words:
        return False, "query must project results with RETURN"
    return True, "read-only query accepted"


for q in ["", "   ", "MATCH (n) RETURN n;", "MATCH (n)", "MATCH (n) MATCH (m) RETURN n",
          "OPTIONAL MATCH (n) RETURN n"]:
    print("  ok=%-5s %-52s| %r" % (validate_cypher(q) + (q,)))
```

Output —

```text
  ok=False empty query                                         | ''
  ok=False empty query                                         | '   '
  ok=True  read-only query accepted                            | 'MATCH (n) RETURN n;'
  ok=False query must project results with RETURN              | 'MATCH (n)'
  ok=True  read-only query accepted                            | 'MATCH (n) MATCH (m) RETURN n'
  ok=False query must start with a read-only clause, got 'OPTIONAL'| 'OPTIONAL MATCH (n) RETURN n'
```

| Case | `ok` | Reason | အဓိပ္ပာယ် |
| --- | --- | --- | --- |
| `""` | False | empty query | အလွတ် |
| `"   "` | False | empty query | space သာ |
| `MATCH (n) RETURN n;` | True | read-only accepted | တစ်လုံးတည်း semicolon ခွင့်ပြု |
| `MATCH (n)` | False | must project results with RETURN | `RETURN` မပါ |
| `MATCH (n) MATCH (m) RETURN n` | True | read-only accepted | `MATCH` နှစ်ခုက အဆင့် ၄ မဖမ်း (first သည် `MATCH`) |
| `OPTIONAL MATCH (n) RETURN n` | False | got `'OPTIONAL'` | **ကန့်သတ်ချက်** — အောက်တွင် ရှင်းလင်း |

### 6.1 `OPTIONAL MATCH` သည် အမြဲ reject ခံရသည်

ဤအချက်သည် ဤ validator ၏ **တကယ့် ကန့်သတ်ချက်** ဖြစ်သည်။

```python
READ_ONLY_START = ("MATCH", "OPTIONAL MATCH", "WITH", "UNWIND")
body = "OPTIONAL MATCH (n) RETURN n"
print("first token =", repr(body.split()[0].upper()))
print("in READ_ONLY_START ->", body.split()[0].upper() in READ_ONLY_START)
```

Output —

```text
first token = 'OPTIONAL'
in READ_ONLY_START -> False
```

`READ_ONLY_START` တွင် `"OPTIONAL MATCH"` ဟု စာလုံးနှစ်လုံး ပါသည်ကို
သတိထားပါ။ သို့သော် `body.split()[0]` သည် **token တစ်လုံးတည်း** ဖြစ်သည့်
`'OPTIONAL'` ကို ပြန်သည်။ `'OPTIONAL' == 'OPTIONAL MATCH'` သည် `False` ဖြစ်သဖြင့်
**`OPTIONAL MATCH` ဖြင့် စသည့် query သည် ဘယ်တော့မှ accept မခံရပါ**။ ဤအချက်သည်
တကယ့် production bug တစ်ခု ဖြစ်သည် — read-only query ဖြစ်သော်လည်း reject
ခံရသဖြင့် **over-blocking** ဖြစ်သည် (security အရ အန္တရာယ် မရှိသော်လည်း
functionality ကျသည်)။ Fix မှာ `first_two = " ".join(body.split()[:2])` ဖြစ်သည်။

`MATCH` နှစ်ခုပါသည့် query သည် ဘာကြောင့် accept ဖြစ်သနည်း — အဆင့် ၄ သည်
**ပထမ token ကိုသာ** စစ်ပြီး ကျန်ကို မစစ်ပါ။ `first` သည် `MATCH` ဖြစ်သဖြင့်
ကျော်သည်။ ထို့ကြောင့် `MATCH (n) MATCH (m) RETURN n` သည် accept ခံရသည် —
ဤအချက်က **validator သည် syntax အပြည့်အစုံကို မစစ်ပါ**၊ clause အစဉ်ကိုသာ
ကြည့်သည့် အချက်ကို ပြသည်။

---

## 7. Code တစ်ခုလုံး — Run လုပ်နိုင်သော Version

```python
# end-to-end: exercise_5
import re

NODES = {
    "co:neo4j": ("Company", "Neo4j", ("Neo4j Inc", "Neo4j, Inc."), "Graph database vendor."),
    "prod:aura": ("Product", "AuraDB", ("Neo4j AuraDB", "Aura"), "Managed cloud graph database service."),
    "tech:cypher": ("Technology", "Cypher", ("openCypher", "Cypher Query Language"), "Declarative graph query language."),
    "tech:louvain": ("Technology", "Louvain", ("Louvain method",), "Greedy modularity optimisation."),
    "org:cnrs": ("Organization", "CNRS", (), "Research organisation of the Louvain authors."),
    "person:eifrem": ("Person", "Vincent Blondel", ("Blondel",), "Lead author of the Louvain method."),
    "tech:graphrag": ("Technology", "GraphRAG", ("Graph RAG", "Microsoft GraphRAG"), "Retrieval pattern."),
    "tech:vectorindex": ("Technology", "Vector Index", ("vector search index", "HNSW index"), "Approximate index."),
    "org:neo4jeng": ("Team", "Neo4j Engineering", (), "Engineering team maintaining Cypher."),
    "paper:louvain": ("Paper", "Fast unfolding of communities in large networks", (), "The 2008 paper."),
}
ALLOWED_LABELS = frozenset(node[0] for node in NODES.values())

BLOCK_COMMENT_RE = re.compile(r"/\*.*?\*/", re.DOTALL)
LINE_COMMENT_RE = re.compile(r"//[^\n]*")
STRING_LITERAL_RE = re.compile(r"'(?:[^'\\]|\\.)*'|\"(?:[^\"\\]|\\.)*\"")
REL_DETAIL_RE = re.compile(r"\[[^\]]*\]")
NODE_BLOCK_RE = re.compile(r"\(([^()]*)\)")
LABEL_RE = re.compile(r":\s*([A-Za-z_][A-Za-z0-9_]*)")

FORBIDDEN_KEYWORDS = ("CREATE", "MERGE", "DELETE", "DETACH", "SET", "REMOVE", "DROP",
                      "FOREACH", "LOAD", "CALL", "GRANT", "DENY", "REVOKE", "ALTER", "RENAME")
READ_ONLY_START = ("MATCH", "OPTIONAL MATCH", "WITH", "UNWIND")
MAX_LENGTH = 2000


def _strip_inert(query):
    query = BLOCK_COMMENT_RE.sub(" ", query)
    return STRING_LITERAL_RE.sub(" '?' ", LINE_COMMENT_RE.sub(" ", query))


def node_labels(query):
    body = REL_DETAIL_RE.sub(" ", _strip_inert(query))
    return sorted({lab for block in NODE_BLOCK_RE.findall(body)
                   for lab in LABEL_RE.findall(block)})


def validate_cypher(query, allowed_labels=None, max_length=MAX_LENGTH):
    if not query or not query.strip():
        return False, "empty query"
    if len(query) > max_length:
        return False, f"query exceeds {max_length} characters"
    body = _strip_inert(query).strip()
    if body.endswith(";"):
        body = body[:-1].strip()
    if ";" in body:
        return False, "multiple statements are not allowed"
    words = set(re.findall(r"[A-Z_]+", body.upper()))
    hit = sorted(kw for kw in FORBIDDEN_KEYWORDS if kw in words)
    if hit:
        return False, f"destructive clause rejected: {', '.join(hit)}"
    first = body.split()[0].upper()
    if first not in READ_ONLY_START:
        return False, f"query must start with a read-only clause, got {first!r}"
    if "RETURN" not in words:
        return False, "query must project results with RETURN"
    if allowed_labels is not None:
        unknown = [lab for lab in node_labels(query) if lab not in allowed_labels]
        if unknown:
            return False, f"labels outside the schema allowlist: {', '.join(unknown)}"
    return True, "read-only query accepted"


candidates = (
    ("MATCH (p:Product {id: $id}) RETURN p.name AS name, p.summary AS summary", True),
    ("MATCH (c:Company)-[:DEVELOPS]->(p:Product) WHERE c.name = $name "
     "RETURN p.name AS product ORDER BY product LIMIT 10", True),
    ("MATCH (p:Product) DETACH DELETE p", False),
    ("MATCH (n) DROP INDEX n", False),
    ("MATCH (n) SET n.owner = $owner RETURN n", False),
    ("CREATE (n:Product {id: $id}) RETURN n", False),
    ("MATCH (n) RETURN n; MATCH (m) DELETE m", False),
    ("MATCH (n:Product) RETURN n // harmless trailing note", True),
    ("MATCH (x:Secret) RETURN x", False),
)
for query, expected_ok in candidates:
    ok, reason = validate_cypher(query, allowed_labels=ALLOWED_LABELS)
    print(f"  ok={str(ok):<5} expected={str(expected_ok):<5} {reason:<45}| {query[:56]}")
    assert ok is expected_ok, f"guardrail mismatch for: {query}"

rejected = sum(1 for q, _ in candidates if not validate_cypher(q, ALLOWED_LABELS)[0])
assert rejected == 6, rejected
print(f"[ok] {rejected}/{len(candidates)} candidates blocked before execution")
```

Output —

```text
  ok=True  expected=True  read-only query accepted                     | MATCH (p:Product {id: $id}) RETURN p.name AS name, p.sum
  ok=True  expected=True  read-only query accepted                     | MATCH (c:Company)-[:DEVELOPS]->(p:Product) WHERE c.name 
  ok=False expected=False destructive clause rejected: DELETE, DETACH  | MATCH (p:Product) DETACH DELETE p
  ok=False expected=False destructive clause rejected: DROP            | MATCH (n) DROP INDEX n
  ok=False expected=False destructive clause rejected: SET             | MATCH (n) SET n.owner = $owner RETURN n
  ok=False expected=False destructive clause rejected: CREATE          | CREATE (n:Product {id: $id}) RETURN n
  ok=False expected=False multiple statements are not allowed          | MATCH (n) RETURN n; MATCH (m) DELETE m
  ok=True  expected=True  read-only query accepted                     | MATCH (n:Product) RETURN n // harmless trailing note
  ok=False expected=False labels outside the schema allowlist: Secret  | MATCH (x:Secret) RETURN x
[ok] 6/9 candidates blocked before execution
```

`assert ok is expected_ok` သည် **identity** (`is`) ဖြင့် စစ်သည်ကို သတိထားပါ —
``bool` တန်ဖိုးများအတွက် `is` သည် အလုပ်လုပ်သည် (Python တွင် `True`/`False` သည်
singleton ဖြစ်သည်)။ `123 == True` လို အခြေအနေကို ဤနေရာတွင် မကြုံပါ။
`rejected = sum(1 for q, _ in candidates if not validate_cypher(q, ALLOWED_LABELS)[0])`
သည် **generator** ပေါ်တွင် `sum()` ခေါ်ခြင်း ဖြစ်သည် — `True` ကို `1` အဖြစ်၊
`False` ကို `0` အဖြစ် ရေတွက်သည်။ `validate_cypher(q, ALLOWED_LABELS)[0]` သည်
`(ok, reason)` tuple ၏ **ပထမ** element ကို ယူသည်။

---

## 8. ကိုယ်တိုင်လေ့ကျင့်ကြည့်ပါ

**မေးခွန်း** — အောက်ပါ candidate ၄ ခုအနက် `validate_cypher()` က **accept** လုပ်
(the `ok` သည် `True` ဖြစ်) သည့် တစ်ခုက ဘယ်ဟာလဲ။

```python
import re

FORBIDDEN_KEYWORDS = ("CREATE", "MERGE", "DELETE", "DETACH", "SET", "REMOVE", "DROP")
READ_ONLY_START = ("MATCH", "OPTIONAL MATCH", "WITH", "UNWIND")


def validate_cypher(query):
    if not query or not query.strip():
        return False, "empty query"
    body = query.strip()
    if body.endswith(";"):
        body = body[:-1].strip()
    if ";" in body:
        return False, "multiple statements are not allowed"
    words = set(re.findall(r"[A-Z_]+", body.upper()))
    hit = sorted(kw for kw in FORBIDDEN_KEYWORDS if kw in words)
    if hit:
        return False, f"destructive clause rejected: {', '.join(hit)}"
    first = body.split()[0].upper()
    if first not in READ_ONLY_START:
        return False, f"query must start with a read-only clause, got {first!r}"
    if "RETURN" not in words:
        return False, "query must project results with RETURN"
    return True, "read-only query accepted"


for q in ["MATCH (n) DETACH DELETE n RETURN n", "MATCH (p:Product) RETURN p.name",
          "MATCH (n) RETURN n.remove AS r", "MERGE (n:Product {id: $id}) RETURN n"]:
    print("  %-40s -> %s" % (q, validate_cypher(q)))
```

1. `MATCH (n) DETACH DELETE n RETURN n`
2. `MATCH (p:Product) RETURN p.name`
3. `MATCH (n) RETURN n.remove AS r`
4. `MERGE (n:Product {id: $id}) RETURN n`

<details>
<summary>အဖြေ ကြည့်ရန်</summary>

**အဖြေ — 2. `MATCH (p:Product) RETURN p.name`**

အကြောင်းရင်း —

- ၁။ `DETACH` နှင့် `DELETE` နှစ်ခုလုံး token scan တွင် ဖမ်းမိသဖြင့် reject။
- ၂။ `MATCH` ဖြင့် စသည်၊ forbidden keyword မပါ၊ `RETURN` ပါသဖြင့် **accept**။
- ၃။ `n.remove` သည် token `REMOVE` ကို ထုတ်သဖြင့် reject — ဤအချက်သည်
  Section 2.1 တွင် ရှင်းပြထားသည့် **false positive** ဖြစ်သည် (property အမည်သာ
  ဖြစ်ပြီး query သည် အပြစ်မရှိပါ)။
- ၄။ `MERGE` သည် forbidden keyword ဖြစ်သဖြင့် reject။

ဤမေးခွန်း၏ သင်ခန်းစာမှာ **token-based blacklist သည် အပြစ်မရှိသည့် query ကို
reject နိုင်သည်** ဆိုသည့် အချက်ပါ — ထို့ကြောင့် validator ကို database role
permission နှင့် တွဲသုံးရသည်။

</details>

---

**အဓိက မှတ်ထားရန်** — Text-to-Cypher guardrail သည် **defense in depth ၏ တစ်ဆင့်
သာ** ဖြစ်သည်။ ဤ validator သည် အဆင့် ၅ ခုကို အစဉ်လိုက် စစ်သည် — အလွတ်/အရှည်၊
statement တစ်ခုတည်း၊ destructive keyword၊ read-only clause၊ `RETURN` နှင့် label
allowlist။ `_strip_inert()` သည် comment နှင့် string literal ကို ကြိုတင်
ဖယ်ရှားသဖြင့် false positive ကို လျှော့သည်၊ သို့သော် **token-based scan သည်
property/alias အမည်ကို keyword နှင့် မခွဲနိုင်သေးပါ** (Section 2.1)။ `first =
body.split()[0]` သည် token တစ်လုံးတည်း ဖြစ်သဖြင့် `OPTIONAL MATCH` သည်
**ဘယ်တော့မှ accept မခံရပါ** (Section 6.1) — ဤအချက်ကို fix လုပ်ရန် `" ".join(
body.split()[:2])` ကို သုံးရမည်။ Keyword blacklist ကို obfuscation ဖြင့်
ကျော်နိုင်နိုင်သဖြင့် database user ကို **read-only role** ဖြင့် bind လုပ်ခြင်းနှင့်
`LIMIT` ကို server side တွင် အတင်းသတ်မှတ်ခြင်းကို **မဖြစ်မနေ** လုပ်ရမည်။
