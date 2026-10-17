# Walkthrough 03 — Gazetteer Lookup (Exercise 3)

> ဤဖိုင်သည် Module 01 ၏ `solution.md` ထဲက Exercise 3 ကို **Python အခြေခံမှ စ၍**
> အပိုင်းလိုက် ရှင်းပြသည့် walkthrough ဖြစ်သည်။

---

## 0. ဤ Exercise က ဘာကို ဖြေရှင်းပေးသလဲ။

စာသားထဲတွင် တစ်ခုတည်းသော entity ကို အမည်အမျိုးမျိုးဖြင့် ရေးထားနိုင်သည်။

```text
Google LLC is a subsidiary of Alphabet. MSFT competes with Google.
```

ဤစာသားတွင် —

- `Google LLC` နှင့် `Google` — တူညီသော အဖွဲ့အစည်း
- `MSFT` — `Microsoft` ၏ ticker အမည်
- `Alphabet` — သီးခြားအဖွဲ့အစည်း

ဤအမည်များကို **တစ်ခုတည်းသော ID** အဖြစ် ပြောင်းပေးမှ graph ထဲတွင် node တစ်ခုတည်း
ဖန်တီးနိုင်သည်။ ဤအလုပ်ကို **entity normalization** (သို့) **canonicalization**
ဟု ခေါ်သည်။

ဤ Exercise သည် ထိုအလုပ်ကို **gazetteer** (အမည်စာရင်း) တစ်ခုဖြင့် လုပ်ပြသည်။

ဤ code တွင် လေ့လာရမည့် Python concepts များမှာ —

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

Dictionary ၏ key သည် **alias** (စာသားထဲ ပါလာနိုင်သော အမည်) ဖြစ်ပြီး value သည်
`(label, canonical_name)` ဟူသော tuple ဖြစ်သည်။

| Alias (key) | Label | Canonical |
| --- | --- | --- |
| `Google` | `ORG` | `Google` |
| `Google LLC` | `ORG` | `Google` |
| `Alphabet` | `ORG` | `Alphabet` |
| `MSFT` | `ORG` | `Microsoft` |
| `Microsoft` | `ORG` | `Microsoft` |

Alias ငါးခုသည် canonical အမည် **သုံးခု** ဆီ ညွှန်သည်။ `Google` နှင့် `Google LLC` သည်
တူညီသော node ဖြစ်သွားမည်၊ `MSFT` နှင့် `Microsoft` လည်း ထို့အတူဖြစ်သည်။ ၎င်းသည်
**many-to-one mapping** ဖြစ်သည်။

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

Tuple ကို index ဖြင့် ဖတ်နိုင်သည်။ နောက်ပိုင်းတွင် `entity_type, canonical = gazetteer[key]`
ဟု tuple unpacking ဖြင့် ဖတ်မည်။

---

## 2. `GAZETTEER_TEXT` — စစ်ဆေးမည့် စာသား

```python
GAZETTEER_TEXT = ("Google LLC is a subsidiary of Alphabet. "
                  "MSFT competes with Google.")
```

Module 01 ၏ Exercise 1 တွင်ကဲ့သို့ပင် ကပ်လျက် string literal နှစ်ခုကို အလိုအလျောက်
ဆက်ပေးသည်။

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

Dictionary ကို `sorted()` ထဲ ထည့်သောအခါ **key များ**ကို စီသည်။ `key=len` သည်
စီရသည့် အခြေခံကို "စာလုံးအရေအတွက်" ဟု သတ်မှတ်သည်။ `reverse=True` သည်
အကြီးဆုံးမှ အငယ်ဆုံးသို့ စီသည်။

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

Python ၏ `startswith()` သည် **prefix** ကို စစ်ခြင်းဖြစ်သောကြောင့် အတိုသော alias သည်
အရှည်သော alias ၏ အစပိုင်းကို ကိုက်ညီနိုင်သည်။

```python
print("Google LLC is".startswith("Google", 0))
print("Google LLC is".startswith("Google LLC", 0))
```

Output —

```text
True
True
```

`"Google"` သည်လည်း `True` ပြန်သောကြောင့် `"Google"` ကို အရင်စစ်လျှင် `"Google LLC"` ကို
**မည်သည့်အခါမှ ရှာတွေ့တော့မည် မဟုတ်ပါ**။

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

Sorting မလုပ်လျှင် `Google LLC` ၏ အစိတ်အပိုင်း `Google` ကိုသာ ဖမ်းမိပြီး `LLC` က
ကျန်ခဲ့သည်။ ၎င်းသည် **longest match first** strategy ၏ အဓိကအချက်ဖြစ်သည်။

---

## 4. `while index < len(text)` — Manual Scan

```python
matches, index = [], 0
while index < len(text):
    ...
    index += 1
```

`for` loop မသုံးဘဲ `while` သုံးခြင်းသည် **index ကို ကိုယ်တိုင် ထိန်းချုပ်နိုင်ခြင်းကြောင့်** ဖြစ်သည်။
`for` loop သည် index ကို တစ်ခုချင်း တိုးသွားမည်၊ သို့သော် match တစ်ခု တွေ့သောအခါ
`Google LLC` (၁၀ လုံး) ကို ကျော်ပြီး index ကို **၁၀ တိုး** လိုသည်။ ၎င်းကို `while`
ဖြင့်သာ လုပ်နိုင်သည်။

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

`index += 3` ဖြင့် ခုန်သွားသည်ကို ပြသည်။ Gazetteer lookup တွင် ဤသို့ခုန်ခြင်းကို
**overlap မဖြစ်စေရန်** အသုံးပြုသည်။

---

## 5. `text.startswith(key, index)` — Index တစ်နေရာမှ စစ်ခြင်း

```python
end = index + len(key)
if text.startswith(key, index):
```

`startswith(key, index)` သည် `text` ၏ index နေရာမှ `key` နှင့် စမစ စစ်သည်။
စစ်ပြီးလျှင် `end` တွင် alias မည်အထိ ဆွဲသွားသည်ကို မှတ်ထားသည်။

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

Condition သုံးခုကို အစဉ်လိုက် စစ်သည်။

| အစဉ် | Condition | အဓိပ္ပာယ် |
| --- | --- | --- |
| 1 | `text.startswith(key, index)` | ဤနေရာတွင် alias စသည် |
| 2 | `index == 0 or not text[index - 1].isalnum()` | ရှေ့စာလုံးသည် စာလုံး/ဂဏန်း မဟုတ် |
| 3 | `end == len(text) or not text[end].isalnum()` | နောက်စာလုံးသည် စာလုံး/ဂဏန်း မဟုတ် |

### Short-circuit — အစဉ်လိုက် စစ်ခြင်းက အရေးကြီးသည်

Python သည် `and` ကွင်းဆက်တွင် condition တစ်ခု `False` ဖြစ်သွားလျှင် **ကျန်သည်များကို
မစစ်တော့ပါ**။ ၎င်းကို short-circuit evaluation ဟု ခေါ်သည်။

ဤ code တွင် `startswith()` ကို **ပထမဆုံး** စစ်ထားခြင်းသည် မတော်တဆ မဟုတ်ပါ။
`text[end]` ကို စစ်သောအခါ `end` သည် `len(text)` ထက် ကြီးနေလျှင် `IndexError` ဖြစ်သည်။
`startswith()` သည် `False` ပြန်လိုက်လျှင် `text[end]` ကို မစစ်တော့သဖြင့် ဤ error ကို
ရှောင်နိုင်သည်။

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

Condition ကို `and` အစဉ် ပြောင်းပြီး စမ်းကြည့်လျှင် —

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

`end == len(text)` သည် `False` ဖြစ်သောကြောင့် `text[end]` ကို ဆက်စစ်ပြီး error ဖြစ်သည်။
**`and` ကွင်းဆက်တွင် မည်သည့် condition ကို အရင်ထားမည်က အလုပ်လုပ်မလုပ် ဆုံးဖြတ်နိုင်သည်။**

### `isalnum()` သည် မည်သည့်အရာကို စစ်သနည်း။

`isalnum()` သည် စာလုံး သို့မဟုတ် ဂဏန်း ဖြစ်မဖြစ် စစ်သည်။

```python
print("a".isalnum(), "7".isalnum(), "_".isalnum(), " ".isalnum(), "-".isalnum())
```

Output —

```text
True True False False False
```

Space နှင့် `-` သည် `False` ဖြစ်ခြင်းမှာ မျှော်လင့်ထားသည့်အတိုင်းဖြစ်သည်။ `_` (underscore)
သည် `False` ပြန်ခြင်းကို သတိထားပါ — **underscore သည် စာလုံးလည်း မဟုတ်၊ ဂဏန်းလည်း
မဟုတ်ပါ**။ ထို့ကြောင့် ဤ code ၏ boundary check အရ `MSFT_now` ထဲမှ `MSFT` ကို
alias အဖြစ် **ဖမ်းမိမည်**။

### Regex `\b` နှင့် `isalnum()` မတူညီခြင်း

ဤအချက်သည် သေးငယ်ပုံရသော်လည်း အရေးကြီးသည်။ Regex ၏ `\b` သည် word character ကို `[A-Za-z0-9_]` (underscore ပါဝင်သည်) အဖြစ် သတ်မှတ်ပြီး `isalnum()` သည် underscore ကို
မပါဝင်စေပါ။ ထို့ကြောင့် နည်းလမ်းနှစ်ခုသည် underscore နေရာတွင် မတူညီသော ရလဒ် ပေးသည်။

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

ဤ Exercise ၏ code သည် ကိုယ်ပိုင် boundary rule ကို ရေးထားခြင်းကြောင့်
ဤကွာခြားချက်ကို သိထားရန် လိုသည်။ Entity အမည်များတွင် underscore ပါလာသောအခါ
(ဥပမာ `sg_rag_prd_m1` ကဲ့သို့ cluster အမည်) ရလဒ် ကွာနိုင်သည်။

---

## 7. `for ... else` — Match မတွေ့လျှင် မည်သို့လုပ်မည်နည်း။

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

Python ၏ `for` loop တွင် `else` ကို တွဲရေးနိုင်သည်။ **`break` မဖြစ်ခဲ့လျှင်**
`else` ကို လုပ်ဆောင်သည်။ Loop သည် ပုံမှန်အတိုင်း ဆုံးသွားလျှင်လည်း `else` က
လုပ်ဆောင်သည် — ထို့ကြောင့် "loop က ပြီးဆုံးသွားသည်" ဟု ဖတ်ရသည်။

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

ဤ Exercise တွင် အဓိပ္ပာယ်မှာ —

- **alias တစ်ခုခု ကိုက်ညီခဲ့လျှင်** → `break` ဖြစ်ပြီး `index` ကို `end` သို့ ခုန်လိုက်ပြီ။
  `else` မလုပ်ဆောင်ပါ။
- **မည်သည့် alias မှ မကိုက်ညီလျှင်** → `else` လုပ်ဆောင်ပြီး `index` ကို **၁ လုံး** တိုးသည်။
  နောက်စာလုံးတစ်လုံးကို ဆက်စစ်သည်။

---

## 8. `matches.append(...)` — ရလဒ် စုဆောင်းခြင်း

```python
entity_type, canonical = gazetteer[key]
matches.append({"alias": key, "type": entity_type,
                "canonical": canonical, "start": index})
index = end
break
```

`entity_type, canonical = gazetteer[key]` သည် tuple `("ORG", "Google")` ကို variable
နှစ်ခုအဖြစ် ခွဲယူသည်။ ထို့နောက် dictionary တစ်ခု ဖန်တီးပြီး `matches` list ထဲ
ထည့်သည်။

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

ဒုတိယကော်လံသည် canonical အမည် ဖြစ်သောကြောင့် `Google` (alias—လိုင်း ၄) နှင့်
`Google LLC` (alias—လိုင်း ၁) သည် **တူညီသော canonical** ကို ညွှန်သည်ကို တွေ့နိုင်သည်။
Graph ထဲတွင် ဤနှစ်ခုသည် node တစ်ခုတည်း ဖြစ်သွားမည်။ `MSFT` သည်လည်း `Microsoft`
ဆီ ရောက်သည်။

---

## 10. Boundary Check ၏ အလုပ်ကို နှိုင်းယှဉ်ခြင်း

Condition နံပါတ် ၂ နှင့် ၃ ကို ဖျောက်ကြည့်လျှင် မည်သို့ဖြစ်မည်နည်း။

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

ဤဇယားသည် boundary check ၏ အလုပ်ကို ရှင်းရှင်းလင်းလင်း ပြသည်။

| စာသား | မည်သို့ဖြစ်သွားသနည်း | မည်သည့် check က တားသနည်း |
| --- | --- | --- |
| `Googleplex` | `Google` ကို alias အဖြစ် ဖမ်းမိမည် | **နောက်** check (`text[end] = 'p'`) |
| `SubsidiaryOfGoogle` | `Google` ကို ဖမ်းမိမည် | **ရှေ့** check (`text[index-1] = 'f'`) |
| `MSFTX` | `MSFT` ကို ဖမ်းမိမည် | **နောက်** check (`text[end] = 'X'`) |
| `XMSFT` | `MSFT` ကို ဖမ်းမိမည် | **ရှေ့** check (`text[index-1] = 'X'`) |

ရှေ့နှင့် နောက် check နှစ်ခုလုံး လိုအပ်သည်။ တစ်ခုတည်း ထားလျှင် ကျန်တစ်ဖက်မှ
false positive များ ဝင်လာမည်။

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

**မေးခွန်း** — အောက်ပါ dict ကို အသုံးပြုပြီး `"Apple"` ဟူသော စာသားကို lookup
လုပ်မည်ဆိုပါစို့။ ရလဒ်၏ **alias** နှင့် **canonical** အမည်သည် မည်သို့ဖြစ်မည်နည်း။

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
