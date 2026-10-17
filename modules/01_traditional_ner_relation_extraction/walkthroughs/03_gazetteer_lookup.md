# Walkthrough 03 — Gazetteer Lookup (Exercise 3)

> ဤဖိုင်သည် Module 01 ၏ `solution.md` ထဲက Exercise 3 ကို **Python အခြေခံမှ စ၍**
> အပိုင်းလိုက် ရှင်းပြသည့် walkthrough ဖြစ်သည်။

---

## 0. ဤ Exercise က ဘာကို ဖြေရှင်းပေးသလဲ။

စာသားထဲမှာ တစ်ခုတည်းသော entity ကို အမည်အမျိုးမျိုးနဲ့ ရေးထားနိုင်ပါတယ်။

```text
Google LLC is a subsidiary of Alphabet. MSFT competes with Google.
```

ဒီစာသားထဲမှာ —

- `Google LLC` နဲ့ `Google` — တူညီတဲ့ အဖွဲ့အစည်း
- `MSFT` — `Microsoft` ၏ ticker အမည်
- `Alphabet` — သီးခြားအဖွဲ့အစည်း

ဒီအမည်တွေကို **တစ်ခုတည်းသော ID** အဖြစ် ပြောင်းပေးမှ graph ထဲမှာ node တစ်ခုတည်း
ဖန်တီးနိုင်ပါတယ်။ ဒီအလုပ်ကို **entity normalization** (သို့) **canonicalization**
လို့ ခေါ်ပါတယ်။

ဒီ Exercise က အဲဒီအလုပ်ကို **gazetteer** (အမည်စာရင်း) တစ်ခုနဲ့ လုပ်ပြပါတယ်။

ဒီ code မှာ လေ့လာရမယ့် Python concepts တွေကတော့ —

- Dictionary ကို alias → metadata အဖြစ် အသုံးပြုခြင်း
- `sorted(..., key=len, reverse=True)`
- `while` loop နှင့် manual index ထိန်းချုပ်ခြင်း
- `str.startswith(search_string, start)`
- `and` chain နှင့် **short-circuit evaluation**
- `for ... else` construct
- `str.isalnum()`
- Dictionary များကို list ထဲ စုဆောင်းခြင်း

---

## 1. `GAZETTEER` — အမည်စာရင်း

```python
GAZETTEER = {
    "Google": ("ORG", "Google"),
    "Google LLC": ("ORG", "Google"),
    "Alphabet": ("ORG", "Alphabet"),
    "MSFT": ("ORG", "Microsoft"),
    "Microsoft": ("ORG", "Microsoft"),
}
```

Dictionary ၏ key က **alias** (စာသားထဲ ပါလာနိုင်တဲ့ အမည်) ဖြစ်ပြီး value က
`(label, canonical_name)` ဆိုတဲ့ tuple ဖြစ်ပါတယ်။

| Alias (key) | Label | Canonical |
| --- | --- | --- |
| `Google` | `ORG` | `Google` |
| `Google LLC` | `ORG` | `Google` |
| `Alphabet` | `ORG` | `Alphabet` |
| `MSFT` | `ORG` | `Microsoft` |
| `Microsoft` | `ORG` | `Microsoft` |

Alias ငါးခုက canonical အမည် **သုံးခု** ဆီ ညွှန်ပါတယ်။ `Google` နဲ့ `Google LLC` က
တူညီတဲ့ node ဖြစ်သွားမယ်၊ `MSFT` နဲ့ `Microsoft` လည်း ထို့အတူပါ။ ဒါက
**many-to-one mapping** ဖြစ်ပါတယ်။

```python
print(GAZETTEER["MSFT"])
print(GAZETTEER["MSFT"][1])
print(GAZETTEER["MSFT"][0])
```

Output —

```text
('ORG', 'Microsoft')
Microsoft
ORG
```

Tuple ကို index နဲ့ ဖတ်နိုင်ပါတယ်။ နောက်ပိုင်းမှာ `entity_type, canonical = gazetteer[key]`
လို့ tuple unpacking နဲ့ ဖတ်ပါမယ်။

---

## 2. `GAZETTEER_TEXT` — စစ်ဆေးမယ့် စာသား

```python
GAZETTEER_TEXT = ("Google LLC is a subsidiary of Alphabet. "
                  "MSFT competes with Google.")
```

Module 01 ၏ Exercise 1 မှာလိုပဲ ကပ်လျက် string literal နှစ်ခုကို အလိုအလျောက်
ဆက်ပေးပါတယ်။

```python
print(GAZETTEER_TEXT)
```

Output —

```text
Google LLC is a subsidiary of Alphabet. MSFT competes with Google.
```

---

## 3. `sorted(gazetteer, key=len, reverse=True)` — အရှည်ဆုံး အမည်ကို အရင် ရှာခြင်း

```python
keys = sorted(gazetteer, key=len, reverse=True)
```

Dictionary ကို `sorted()` ထဲ ထည့်တဲ့အခါ **key များ**ကို စီပါတယ်။ `key=len` က
စီရတဲ့ အခြေခံကို "စာလုံးအရေအတွက်" လို့ သတ်မှတ်ပါတယ်။ `reverse=True` က
အကြီးဆုံးကနေ အငယ်ဆုံးသို့ စီပါတယ်။

```python
GAZETTEER = {
    "Google": ("ORG", "Google"),
    "Google LLC": ("ORG", "Google"),
    "Alphabet": ("ORG", "Alphabet"),
    "MSFT": ("ORG", "Microsoft"),
    "Microsoft": ("ORG", "Microsoft"),
}

print("dict order        :", list(GAZETTEER))
print("sorted by length  :", sorted(GAZETTEER, key=len, reverse=True))
print("lengths           :", [len(k) for k in sorted(GAZETTEER, key=len, reverse=True)])
```

Output —

```text
dict order        : ['Google', 'Google LLC', 'Alphabet', 'MSFT', 'Microsoft']
sorted by length  : ['Google LLC', 'Microsoft', 'Alphabet', 'Google', 'MSFT']
lengths           : [10, 9, 8, 6, 4]
```

### ဘာကြောင့် အရှည်ဆုံးကို အရင်စစ်ရသလဲ။

Python ၏ `startswith()` က **prefix** ကို စစ်တာဖြစ်လို့ အတိုတဲ့ alias က
အရှည်တဲ့ alias ၏ အစပိုင်းကို ကိုက်ညီနိုင်ပါတယ်။

```python
print("Google LLC is".startswith("Google", 0))
print("Google LLC is".startswith("Google LLC", 0))
```

Output —

```text
True
True
```

`"Google"` ကလည်း `True` ပြန်တဲ့အတွက် `"Google"` ကို အရင်စစ်ရင် `"Google LLC"` ကို
**ဘယ်တော့မှ ရှာတွေ့တော့မှာ မဟုတ်ပါဘူး**။

```python
def lookup(text, keys):
    matches, index = [], 0
    while index < len(text):
        for key in keys:
            end = index + len(key)
            if text.startswith(key, index) \
                    and (index == 0 or not text[index - 1].isalnum()) \
                    and (end == len(text) or not text[end].isalnum()):
                matches.append({"alias": key, "start": index})
                index = end
                break
        else:
            index += 1
    return matches


text = "Google LLC is a subsidiary of Alphabet."

print("dict order (no sorting) :", [(m["alias"], m["start"]) for m in lookup(text, list(GAZETTEER))])
print("sorted longest first    :", [(m["alias"], m["start"]) for m in lookup(text, sorted(GAZETTEER, key=len, reverse=True))])
```

Output —

```text
dict order (no sorting) : [('Google', 0), ('Alphabet', 30)]
sorted longest first    : [('Google LLC', 0), ('Alphabet', 30)]
```

Sorting မလုပ်ရင် `Google LLC` ၏ အစိတ်အပိုင်း `Google` ကိုသာ ဖမ်းမိပြီး `LLC` က
ကျန်ခဲ့ပါတယ်။ ဒါက **longest match first** strategy ၏ အဓိကအချက်ပါ။

---

## 4. `while index < len(text)` — Manual Scan

```python
matches, index = [], 0
while index < len(text):
    ...
    index += 1
```

`for` loop မသုံးဘဲ `while` သုံးတာက **index ကို ကိုယ်တိုင် ထိန်းချုပ်လို့** ဖြစ်ပါတယ်။
`for` loop က index ကို တစ်ခုချင်း တိုးသွားမယ်၊ ဒါပေမဲ့ match တစ်ခု တွေ့တဲ့အခါ
`Google LLC` (၁၀ လုံး) ကို ကျော်ပြီး index ကို **၁၀ တိုး** လိုပါတယ်။ ဒါကို `while`
နဲ့သာ လုပ်နိုင်ပါတယ်။

```python
text = "abcdef"
index = 0
while index < len(text):
    print(index, text[index])
    index += 3
```

Output —

```text
0 a
3 d
```

`index += 3` ဖြင့် ခုန်သွားတာကို ပြပါတယ်။ Gazetteer lookup မှာ ဒီလိုခုန်တာက
**overlap မဖြစ်စေရန်** အသုံးပြုပါတယ်။

---

## 5. `text.startswith(key, index)` — Index တစ်နေရာမှ စစ်ခြင်း

```python
end = index + len(key)
if text.startswith(key, index):
```

`startswith(key, index)` က `text` ၏ index နေရာကနေ `key` နဲ့ စမစ စစ်ပါတယ်။
စစ်ပြီးရင် `end` မှာ alias ဘယ်အထိ ဆွဲသွားလဲ မှတ်ထားပါတယ်။

```python
text = "MSFT competes"
index = 0
key = "MSFT"

print(text.startswith(key, index))
print(index + len(key))
print(text[index:index + len(key)])
```

Output —

```text
True
4
MSFT
```

---

## 6. Condition သုံးခုနှင့် Short-circuit Evaluation

```python
if text.startswith(key, index) \
        and (index == 0 or not text[index - 1].isalnum()) \
        and (end == len(text) or not text[end].isalnum()):
```

Condition သုံးခုကို အစဉ်လိုက် စစ်ပါတယ်။

| အစဉ် | Condition | အဓိပ္ပာယ် |
| --- | --- | --- |
| 1 | `text.startswith(key, index)` | ဒီနေရာမှာ alias စတယ် |
| 2 | `index == 0 or not text[index - 1].isalnum()` | ရှေ့စာလုံးက စာလုံး/ဂဏန်း မဟုတ် |
| 3 | `end == len(text) or not text[end].isalnum()` | နောက်စာလုံးက စာလုံး/ဂဏန်း မဟုတ် |

### Short-circuit — အစဉ်လိုက် စစ်ခြင်းက အရေးကြီးသည်

Python က `and` ကွင်းဆက်မှာ condition တစ်ခု `False` ဖြစ်သွားရင် **ကျန်တာတွေကို
မစစ်တော့ပါဘူး**။ ဒါကို short-circuit evaluation လို့ ခေါ်ပါတယ်။

ဒီ code မှာ `startswith()` ကို **ပထမဆုံး** စစ်ထားတာ မတော်တဆ မဟုတ်ပါဘူး။
`text[end]` ကို စစ်တဲ့အခါ `end` က `len(text)` ထက် ကြီးနေရင် `IndexError` ဖြစ်ပါတယ်။
`startswith()` က `False` ပြန်လိုက်ရင် `text[end]` ကို မစစ်တော့လို့ ဒီ error ကို
ရှောင်နိုင်ပါတယ်။

```python
text = "abc"
key = "abcdefgh"
index = 0
end = index + len(key)

print("text length =", len(text), "| end =", end)
print("startswith =", text.startswith(key, index))
print("-> False ဖြစ်သဖြင့် and chain သည် ဤနေရာတွင် ရပ်တန့်သည်၊ text[end] ကို မစစ်တော့ပါ")
```

Output —

```text
text length = 3 | end = 8
startswith = False
-> False ဖြစ်သဖြင့် and chain သည် ဤနေရာတွင် ရပ်တန့်သည်၊ text[end] ကို မစစ်တော့ပါ
```

Condition ကို `and` အစဉ် ပြောင်းပြီး စမ်းကြည့်ရင် —

```python
text = "abc"
key = "abcdefgh"
index = 0
end = index + len(key)

try:
    ok = (end == len(text) or not text[end].isalnum()) and text.startswith(key, index)
    print("reordered ->", ok)
except IndexError as exc:
    print("reordered -> IndexError:", exc)
```

Output —

```text
reordered -> IndexError: string index out of range
```

`end == len(text)` က `False` ဖြစ်တဲ့အတွက် `text[end]` ကို ဆက်စစ်ပြီး error ဖြစ်ပါတယ်။
**`and` ကွင်းဆက်မှာ ဘယ် condition ကို အရင်ထားမလဲ ဆိုတာ အလုပ်လုပ်မလုပ် ဆုံးဖြတ်နိုင်ပါတယ်။**

### `isalnum()` က ဘာစစ်သလဲ။

`isalnum()` က စာလုံး သို့မဟုတ် ဂဏန်း ဖြစ်မဖြစ် စစ်ပါတယ်။

```python
print("a".isalnum(), "7".isalnum(), "_".isalnum(), " ".isalnum(), "-".isalnum())
```

Output —

```text
True True False False False
```

Space နဲ့ `-` က `False` ဖြစ်တာက မျှော်လင့်ထားသည့်အတိုင်းပါ။ `_` (underscore)
က `False` ပြန်တာကို သတိထားပါ — **underscore က စာလုံးလည်း မဟုတ်၊ ဂဏန်းလည်း
မဟုတ်ပါ**။ ဒါကြောင့် ဤ code ၏ boundary check အရ `MSFT_now` ထဲက `MSFT` ကို
alias အဖြစ် **ဖမ်းမိပါမယ်**။

### Regex `\b` နှင့် `isalnum()` မတူညီခြင်း

ဒီအချက်က သေးငယ်ပုံရပေမဲ့ အရေးကြီးပါတယ်။ Regex ၏ `\b` က word character ကို
`[A-Za-z0-9_]` (underscore ပါဝင်သည်) အဖြစ် သတ်မှတ်ပြီး `isalnum()` က underscore ကို
မပါဝင်စေပါဘူး။ ဒါကြောင့် နည်းလမ်းနှစ်ခုက underscore နေရာမှာ မတူညီတဲ့ ရလဒ် ပေးပါတယ်။

```python
import re

GAZETTEER = {"MSFT": ("ORG", "Microsoft")}


def gazetteer_lookup(text, gazetteer):
    keys = sorted(gazetteer, key=len, reverse=True)
    matches, index = [], 0
    while index < len(text):
        for key in keys:
            end = index + len(key)
            if text.startswith(key, index) \
                    and (index == 0 or not text[index - 1].isalnum()) \
                    and (end == len(text) or not text[end].isalnum()):
                matches.append(key)
                index = end
                break
        else:
            index += 1
    return matches


for text in ["MSFT_now", "MSFT-now", "MSFT now", "MSFT2"]:
    print("%-10s gazetteer=%-12s regex_boundary=%s"
          % (text, gazetteer_lookup(text, GAZETTEER), re.findall(r"\bMSFT\b", text)))
```

Output —

```text
MSFT_now   gazetteer=['MSFT']     regex_boundary=[]
MSFT-now   gazetteer=['MSFT']     regex_boundary=['MSFT']
MSFT now   gazetteer=['MSFT']     regex_boundary=['MSFT']
MSFT2      gazetteer=[]           regex_boundary=[]
```

| စာသား | Gazetteer (`isalnum`) | Regex `\b` |
| --- | --- | --- |
| `MSFT_now` | ဖမ်းမိသည် | မဖမ်းမိပါ |
| `MSFT-now` | ဖမ်းမိသည် | ဖမ်းမိသည် |
| `MSFT2` | မဖမ်းမိပါ | မဖမ်းမိပါ |

ဒီ Exercise ၏ code ကိုယ်တိုင် ကိုယ်ပိုင် boundary rule ကို ရေးထားတာကြောင့်
ဒီကွာခြားချက်ကို သိထားဖို့ လိုပါတယ်။ Entity အမည်တွေမှာ underscore ပါလာတဲ့အခါ
(ဥပမာ `sg_rag_prd_m1` လို cluster အမည်) ရလဒ် ကွာနိုင်ပါတယ်။

---

## 7. `for ... else` — Match မတွေ့ရင် ဘာလုပ်မလဲ။

```python
for key in keys:
    end = index + len(key)
    if ...:
        matches.append(...)
        index = end
        break
else:
    index += 1
```

Python ၏ `for` loop မှာ `else` ကို တွဲရေးနိုင်ပါတယ်။ **`break` မဖြစ်ခဲ့ရင်**
`else` ကို လုပ်ဆောင်ပါတယ်။ Loop က ပုံမှန်အတိုင်း ဆုံးသွားရင်လည်း `else` က
လုပ်ဆောင်ပါတယ် — ဒါကြောင့် "loop က ပြီးဆုံးသွားတယ်" လို့ ဖတ်ရပါတယ်။

```python
items = ["b", "c"]
for x in items:
    if x == "z":
        print("found z, break")
        break
else:
    print("no break happened -> else runs")

for x in ["z", "b"]:
    if x == "z":
        print("found z, break")
        break
else:
    print("(this will not print)")
```

Output —

```text
no break happened -> else runs
found z, break
```

ဒီ Exercise မှာ အဓိပ္ပာယ်က —

- **alias တစ်ခုခု ကိုက်ညီခဲ့ရင်** → `break` ဖြစ်ပြီး `index` ကို `end` သို့ ခုန်လိုက်ပြီ။
  `else` မလုပ်ဆောင်ပါ။
- **ဘယ် alias မှ မကိုက်ညီရင်** → `else` လုပ်ဆောင်ပြီး `index` ကို **၁ လုံး** တိုးပါတယ်။
  နောက်စာလုံးတစ်လုံးကို ဆက်စစ်ပါတယ်။

---

## 8. `matches.append(...)` — ရလဒ် စုဆောင်းခြင်း

```python
entity_type, canonical = gazetteer[key]
matches.append({"alias": key, "type": entity_type,
                "canonical": canonical, "start": index})
index = end
break
```

`entity_type, canonical = gazetteer[key]` က tuple `("ORG", "Google")` ကို variable
နှစ်ခုအဖြစ် ခွဲယူပါတယ်။ ပြီးရင် dictionary တစ်ခု ဖန်တီးပြီး `matches` list ထဲ
ထည့်ပါတယ်။

```python
entry = {"alias": "MSFT", "type": "ORG", "canonical": "Microsoft", "start": 40}
print(entry["alias"], "->", entry["canonical"], "(", entry["type"], ")")
```

Output —

```text
MSFT -> Microsoft ( ORG )
```

---

## 9. ရလဒ်ကို ထုတ်ခြင်း

```python
for match in gazetteer_lookup(GAZETTEER_TEXT, GAZETTEER):
    print("  %-10s -> %-10s (%s)"
          % (match["alias"], match["canonical"], match["type"]))
```

Expected output —

```text
  Google LLC -> Google     (ORG)
  Alphabet   -> Alphabet   (ORG)
  MSFT       -> Microsoft  (ORG)
  Google     -> Google     (ORG)
```

ဒုတိယကော်လံက canonical အမည် ဖြစ်တဲ့အတွက် `Google` (alias—လိုင်း ၄) နဲ့
`Google LLC` (alias—လိုင်း ၁) က **တူညီတဲ့ canonical** ကို ညွှန်တာကို တွေ့နိုင်ပါတယ်။
Graph ထဲမှာ ဒီနှစ်ခုက node တစ်ခုတည်း ဖြစ်သွားမှာပါ။ `MSFT` ကလည်း `Microsoft`
ဆီ ရောက်ပါတယ်။

---

## 10. Boundary Check ၏ အလုပ်ကို နှိုင်းယှဉ်ခြင်း

Condition နံပါတ် ၂ နဲ့ ၃ ကို ဖျောက်ကြည့်ရင် ဘာဖြစ်လဲ။

```python
def lookup(text, gazetteer, check_before=True, check_after=True):
    keys = sorted(gazetteer, key=len, reverse=True)
    matches, index = [], 0
    while index < len(text):
        for key in keys:
            end = index + len(key)
            if text.startswith(key, index) \
                    and (not check_before or index == 0 or not text[index - 1].isalnum()) \
                    and (not check_after or end == len(text) or not text[end].isalnum()):
                matches.append({"alias": key, "start": index})
                index = end
                break
        else:
            index += 1
    return matches


GAZETTEER = {
    "Google": ("ORG", "Google"),
    "Google LLC": ("ORG", "Google"),
    "Alphabet": ("ORG", "Alphabet"),
    "MSFT": ("ORG", "Microsoft"),
    "Microsoft": ("ORG", "Microsoft"),
}

for text in ["Googleplex owned by Alphabet", "SubsidiaryOfGoogle", "MSFTX", "XMSFT"]:
    both = [m["alias"] for m in lookup(text, GAZETTEER)]
    none = [m["alias"] for m in lookup(text, GAZETTEER, False, False)]
    print("%-30s with boundary=%-24s without=%s" % (text, both, none))
```

Output —

```text
Googleplex owned by Alphabet   with boundary=['Alphabet']             without=['Google', 'Alphabet']
SubsidiaryOfGoogle             with boundary=[]                       without=['Google']
MSFTX                          with boundary=[]                       without=['MSFT']
XMSFT                          with boundary=[]                       without=['MSFT']
```

ဒီဇယားက boundary check ၏ အလုပ်ကို ရှင်းရှင်းလင်းလင်း ပြပါတယ်။

| စာသား | ဘာဖြစ်သွားသနည်း | ဘယ် check က တားသနည်း |
| --- | --- | --- |
| `Googleplex` | `Google` ကို alias အဖြစ် ဖမ်းမိမည် | **နောက်** check (`text[end] = 'p'`) |
| `SubsidiaryOfGoogle` | `Google` ကို ဖမ်းမိမည် | **ရှေ့** check (`text[index-1] = 'f'`) |
| `MSFTX` | `MSFT` ကို ဖမ်းမိမည် | **နောက်** check (`text[end] = 'X'`) |
| `XMSFT` | `MSFT` ကို ဖမ်းမိမည် | **ရှေ့** check (`text[index-1] = 'X'`) |

ရှေ့နဲ့ နောက် check နှစ်ခုလုံး လိုအပ်ပါတယ်။ တစ်ခုတည်း ထားရင် ကျန်တစ်ဖက်က
false positive တွေ ဝင်လာပါမယ်။

---

## 11. Code တစ်ခုလုံး — Run လုပ်နိုင်သော Version

```python
GAZETTEER = {
    "Google": ("ORG", "Google"),
    "Google LLC": ("ORG", "Google"),
    "Alphabet": ("ORG", "Alphabet"),
    "MSFT": ("ORG", "Microsoft"),
    "Microsoft": ("ORG", "Microsoft"),
}
GAZETTEER_TEXT = ("Google LLC is a subsidiary of Alphabet. "
                  "MSFT competes with Google.")


def gazetteer_lookup(text, gazetteer):
    keys = sorted(gazetteer, key=len, reverse=True)   # longest match first
    matches, index = [], 0
    while index < len(text):
        for key in keys:
            end = index + len(key)
            if text.startswith(key, index) \
                    and (index == 0 or not text[index - 1].isalnum()) \
                    and (end == len(text) or not text[end].isalnum()):
                entity_type, canonical = gazetteer[key]
                matches.append({"alias": key, "type": entity_type,
                                "canonical": canonical, "start": index})
                index = end
                break
        else:
            index += 1
    return matches


for match in gazetteer_lookup(GAZETTEER_TEXT, GAZETTEER):
    print("  %-10s -> %-10s (%s)"
          % (match["alias"], match["canonical"], match["type"]))
```

Output —

```text
  Google LLC -> Google     (ORG)
  Alphabet   -> Alphabet   (ORG)
  MSFT       -> Microsoft  (ORG)
  Google     -> Google     (ORG)
```

---

## 12. ကိုယ်တိုင်လေ့ကျင့်ကြည့်ပါ

**မေးခွန်း** — အောက်ပါ dict ကို အသုံးပြုပြီး `"Apple"` ဆိုတဲ့ စာသားကို lookup
လုပ်မည်ဆိုပါစို့။ ရလဒ်၏ **alias** နှင့် **canonical** အမည်က ဘာဖြစ်မလဲ။

```python
GAZETTEER = {
    "Apple": ("ORG", "Apple Inc"),
    "Apple Inc": ("ORG", "Apple Inc"),
}
text = "Apple is a technology company."
```

1. `alias = 'Apple'`၊ `canonical = 'Apple Inc'`
2. `alias = 'Apple Inc'`၊ `canonical = 'Apple Inc'`
3. `alias = 'Apple'`၊ `canonical = 'Apple'`
4. ရလဒ် မရပါ

<details>
<summary>အဖြေ ကြည့်ရန်</summary>

**အဖြေ — 1. `alias = 'Apple'`၊ `canonical = 'Apple Inc'`**

အကြောင်းရင်း — `sorted(..., key=len, reverse=True)` က `Apple Inc` (၉ လုံး) ကို
`Apple` (၅ လုံး) ထက် အရင်စစ်သည်။ သို့သော် `"Apple is a technology company."`
တွင် `Apple` နောက်တွင် space ရှိသဖြင့် `Apple Inc` နှင့် မကိုက်ညီပါ။ ထို့ကြောင့်
`Apple` alias ကို ဖမ်းမိပြီး canonical အမည် `Apple Inc` သို့ အလိုအလျောက်
ပုံနှိပ်ခံရမည်။

ဤအချက်သည် gazetteer ၏ အကျိုးကျေးဇူးကို ပြသည် — စာသားထဲတွင် `Apple` ဟု
ရေးထားသော်လည်း graph node အမည်မှာ `Apple Inc` အဖြစ် တစ်ပြေးညီ ဖြစ်သည်။

</details>

---

**အဓိက မှတ်ထားရန်** — Gazetteer-based extraction သည် မြန်ဆန်ပြီး ရလဒ်ကို ခန့်မှန်းရ
လွယ်သည်။ သို့သော် alias စာရင်း လက်ဖြင့် ထည့်ရသဖြင့် မသိသေးသော entity များကို
ရှာမတွေ့ပါ။ Alias အသစ်များ ပေါ်လာလျှင် အစဉ် update လုပ်ရမည်ဖြစ်ပြီး၊ alias
နှစ်ခု တိုက်နေလျှင် ဘယ်တစ်ခုကို ဦးစားပေးမည်ကို (ဤ code မှာ အရှည်ဆုံးကို) စည်းမျဉ်း
သတ်မှတ်ထားရသည်။ အမှန်တကယ် graph တွင် ဤအလုပ်ကို entity resolution အဖြစ်
ပိုမို ရှုပ်ထွေးစွာ လုပ်ဆောင်ရသည်။
