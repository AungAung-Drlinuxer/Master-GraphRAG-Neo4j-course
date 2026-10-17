# Walkthrough 02 — BIO Tag Decoding (Exercise 2)

> ဤဖိုင်သည် Module 01 ၏ `solution.md` ထဲက Exercise 2 ကို **Python အခြေခံမှ စ၍**
> အပိုင်းလိုက် ရှင်းပြသည့် walkthrough ဖြစ်သည်။

---

## 0. ဤ Exercise က ဘာကို ဖြေရှင်းပေးသလဲ။

Exercise 1 တွင် regex နှင့် anchor လုပ်ထားသော pattern ဖြင့် entity ရှာခဲ့သည်။ Model
များမှာ စာသားကို **token** များအဖြစ် ခွဲပြီး token တစ်ခုချင်းစီအတွက် **tag** တစ်ခုစီ
ပြန်ပေးသော ပုံစံဖြင့် အလုပ်လုပ်သည်။

```text
tokens : Sundar  Pichai  visited  London   on   12  March  2019   .
tags   : B-PER   I-PER   O        B-LOC    O    B-DATE I-DATE I-DATE O
```

ဤ tag များကို ပြန်ဖတ်ပြီး —

- `Sundar Pichai` → `PER` (လူအမည်)
- `London` → `LOC` (နေရာ)
- `12 March 2019` → `DATE` (ရက်စွဲ)

ဟူသော **span** များအဖြစ် ပြောင်းပေးသောအလုပ်ကို **decoding** ဟု ခေါ်သည်။

ဤ code တွင် လေ့လာရမည့် Python concepts များမှာ —

- `zip()` ဖြင့် list နှစ်ခုကို တွဲခြင်း
- `enumerate()` ဖြင့် index ရယူခြင်း
- Tuple unpacking (`(token, tag)`)
- `str.startswith()` နှင့် string slicing (`tag[2:]`)
- Dictionary ဖန်တီးခြင်းနှင့် ပြင်ခြင်း
- `None` နှင့် `is not None` စစ်ဆေးခြင်း
- `if` / `elif` / `else` ခွဲထွက်ခြင်း
- `list.append()` နှင့် exclusive end index
- List comprehension
- `%` string formatting

---

## 1. BIO Scheme ဆိုသည်မှာ အဘယ်နည်း။

Tag တစ်ခုစီတွင် အပိုင်းနှစ်ခု ရှိသည်။

| အပိုင်း | အဓိပ္ပာယ် |
| --- | --- |
| ရှေ့ဆုံး စာလုံး — `B`၊ `I`၊ `O` | Tag အမျိုးအစား |
| နောက်ဆက် — `PER`၊ `LOC`၊ `DATE` | Entity label |

- **`B-` (Begin)** — entity အသစ်တစ်ခု၏ **ပထမဆုံး** token။
- **`I-` (Inside)** — entity အသစ်၏ **ဆက်လက်** token။
- **`O` (Outside)** — entity မဟုတ်သော token။

ဤ scheme ကြောင့် entity နှစ်ခု ကပ်နေသောအခါ မည်သည့်နေရာတွင် ခွဲရမည်ကို သိနိုင်သည်။

```text
B-PER I-PER B-PER I-PER
Sundar Pichai Tim  Cook
```

`B-` က entity အသစ်၏ အစကို အမြဲပြသည်။ `I-` သာ ရှိနေလျှင် entity တစ်ခုတည်း
ဆက်နေသည်ဟု ဖတ်သည်။

---

## 2. `tokens` နှင့် `tags` — Input နှစ်ခု

```python
tokens = ["Sundar", "Pichai", "visited", "London", "on",
          "12", "March", "2019", "."]
tags = ["B-PER", "I-PER", "O", "B-LOC", "O",
        "B-DATE", "I-DATE", "I-DATE", "O"]
```

List နှစ်ခု၏ အရှည် **တူညီရသည်**။ Index တစ်ခုတည်းတွင် `tokens[i]` ၏ tag က
`tags[i]` ဖြစ်သည်။

```python
print(len(tokens), len(tags))
print("index 0 :", tokens[0], "->", tags[0])
print("index 3 :", tokens[3], "->", tags[3])
```

Output —

```text
9 9
index 0 : Sundar -> B-PER
index 3 : London -> B-LOC
```

---

## 3. `zip()` — List နှစ်ခုကို တွဲခြင်း

```python
print(list(zip(tokens, tags)))
```

Output —

```text
[('Sundar', 'B-PER'), ('Pichai', 'I-PER'), ('visited', 'O'), ('London', 'B-LOC'), ('on', 'O'), ('12', 'B-DATE'), ('March', 'I-DATE'), ('2019', 'I-DATE'), ('.', 'O')]
```

`zip()` သည် list နှစ်ခုကို index အလိုက် တွဲပြီး **tuple** များ ထုတ်ပေးသည်။
`for token, tag in zip(tokens, tags):` ဟု ရေးသောအခါ tuple တစ်ခုစီကို variable
နှစ်ခုအဖြစ် အလိုအလျောက် ခွဲလိုက်သည်ကို **tuple unpacking** ဟု ခေါ်သည်။

```python
for token, tag in zip(tokens, tags):
    print(token, "->", tag)
```

Output —

```text
Sundar -> B-PER
Pichai -> I-PER
visited -> O
London -> B-LOC
on -> O
12 -> B-DATE
March -> I-DATE
2019 -> I-DATE
. -> O
```

---

## 4. `enumerate()` — Index ပါ တွဲထုတ်ခြင်း

`zip()` သည် tuple များသာ ပေးသည်။ Index လည်း လိုချင်လျှင် `enumerate()` ကို အတွင်းထပ်
သုံးသည်။

```python
print(list(enumerate(zip(tokens, tags)))[:2])
print()
for index, (token, tag) in enumerate(zip(tokens, tags)):
    print(index, token, tag)
```

Output —

```text
[(0, ('Sundar', 'B-PER')), (1, ('Pichai', 'I-PER'))]

0 Sundar B-PER
1 Pichai I-PER
2 visited O
3 London B-LOC
4 on O
5 12 B-DATE
6 March I-DATE
7 2019 I-DATE
8 . O
```

`enumerate(zip(...))` သည် `(index, (token, tag))` ဟူသော ခွေထားသည့် tuple ကို ပေးသည်။
`for index, (token, tag) in ...` ဟု ရေးပြီး အပြင်ခွေ နှစ်ခုကို `index`၊ အတွင်းခွေ
နှစ်ခုကို `token` နှင့် `tag` အဖြစ် ခွဲယူသည်။

Index ကို အဘယ်ကြောင့် လိုအပ်သနည်းဆိုလျှင် span တစ်ခုစီ၏ **အစနှင့် အဆုံး token index** ကို
မှတ်ထားလိုခြင်းကြောင့်ဖြစ်သည်။ ဤ index များကို နောက်ပိုင်း graph node များဆီ ပြန်ညွှန်းရန်
(provenance) အသုံးပြုနိုင်သည်။

---

## 5. `tag[2:]` နှင့် `startswith()`

```python
print("B-PER"[2:])
print("I-DATE"[2:])
print("B-PER".startswith("B-"), "I-PER".startswith("B-"), "O".startswith("B-"))
```

Output —

```text
PER
DATE
True False False
```

- `"B-PER"[2:]` — index 2 မှ အဆုံးထိ ဖြတ်ယူသည်။ `B` နှင့် `-` ကို ကျော်လိုက်သောကြောင့်
  `PER` ကျန်သည်။ String indexing သည် **0 မှ စ** သည်။
- `startswith("B-")` သည် tag က `B-` နှင့် စမစ စစ်သည်။ `O` အတွက် `False` ရသည်။

ဤနှစ်ခုကို တွဲသုံးပြီး —

```python
tag = "I-DATE"
if tag.startswith("I-"):
    print("Inside tag, label =", tag[2:])
```

Output —

```text
Inside tag, label = DATE
```

ဟု label ကို ဆွဲထုတ်နိုင်သည်။

---

## 6. `decode_bio()` ၏ ဖွဲ့စည်းပုံ

```python
def decode_bio(tokens, tags):
    spans, current = [], None
    for index, (token, tag) in enumerate(zip(tokens, tags)):
        ...
    if current is not None:
        spans.append(current)
    return [{"type": s["type"], "text": " ".join(s["tokens"]),
             "start": s["start"], "end": s["end"]} for s in spans]
```

Variable နှစ်ခုကို ဤသို့ သတ်မှတ်ထားသည်။

- `spans` — ပြီးစီးသွားသော entity များ စုစည်းရာ list။
- `current` — လက်ရှိ ဖတ်နေဆဲ entity။ မရှိသေးလျှင် `None`။

Loop တစ်ခုချင်းစီတွင် `current` ကို အသစ်ဖန်တီးခြင်း၊ ဆက်တွဲခြင်း၊ သို့မဟုတ်
`spans` ထဲ ရွှေ့ခြင်း သုံးမျိုးထဲ တစ်မျိုး လုပ်သည်။

---

## 7. `B-` Case — Entity အသစ် စတင်ခြင်း

```python
if tag.startswith("B-"):
    if current is not None:
        spans.append(current)
    current = {"type": tag[2:], "tokens": [token],
               "start": index, "end": index + 1}
```

အဆင့်နှစ်ဆင့် ရှိသည်။

**ပထမအဆင့်** — `current` တွင် entity တစ်ခု ရှိနေလျှင် ၎င်းကို `spans` ထဲ ရွှေ့သည်။
`B-` tag တစ်ခု လာခြင်းသည် entity အဟောင်း ပြီးသွားပြီဟု ဆိုလိုခြင်းကြောင့်ဖြစ်သည်။

**ဒုတိယအဆင့်** — entity အသစ်တစ်ခုကို dictionary အဖြစ် ဖန်တီးသည်။

```python
{"type": tag[2:], "tokens": [token], "start": index, "end": index + 1}
```

| Key | တန်ဖိုး | အဓိပ္ပာယ် |
| --- | --- | --- |
| `type` | `tag[2:]` → `PER` | Entity label |
| `tokens` | `[token]` | စုဆောင်းထားသော token စာရင်း (ပထမဆုံး တစ်လုံးသာ) |
| `start` | `index` | အစ token index |
| `end` | `index + 1` | အဆုံး index — **exclusive** |

`end` သည် `index + 1` ဖြစ်ခြင်းမှာ Python ၏ slice အလေ့အကျင့်နှင့် ကိုက်ညီစေရန်ဖြစ်သည်။

```python
tokens = ["Sundar", "Pichai", "visited", "London"]
print("tokens[0:2] =", tokens[0:2])
print("tokens[3:4] =", tokens[3:4])
```

Output —

```text
tokens[0:2] = ['Sundar', 'Pichai']
tokens[3:4] = ['London']
```

Span တစ်ခုသည် `start=0`၊ `end=2` ဖြစ်လျှင် `tokens[0:2]` ဖြင့် တိုက်ရိုက် ဖြတ်ယူနိုင်သည်။

---

## 8. `I-` Case — Entity ဆက်လက်ခြင်း

```python
elif tag.startswith("I-") and current is not None and tag[2:] == current["type"]:
    current["tokens"].append(token)
    current["end"] = index + 1
```

ဤ `elif` သည် **condition သုံးခု** ကို `and` ဖြင့် ဆက်ထားသည်။ သုံးခုလုံး မှန်မှ
ဤ branch ထဲ ဝင်သည်။

1. `tag.startswith("I-")` — tag သည် `I-` နှင့် စသည်။
2. `current is not None` — လက်ရှိ entity တစ်ခု ရှိနေသည်။
3. `tag[2:] == current["type"]` — tag ၏ label သည် `current` ၏ label နှင့် တူညီသည်။

ဤအလုပ်ကို လုပ်သောအခါ —

- `current["tokens"].append(token)` — token အသစ်ကို စာရင်းထဲ ထည့်။
- `current["end"] = index + 1` — အဆုံး index ကို အသစ်ပြန်။

စုစည်းသည့်အပိုင်းကို ကြည့်ပါ။

```python
tokens = ["12", "March", "2019"]
current = {"type": "DATE", "tokens": ["12"], "start": 0, "end": 1}

for index, token in enumerate(tokens[1:], start=1):
    current["tokens"].append(token)
    current["end"] = index + 1

print(current)
print(" ".join(current["tokens"]))
```

Output —

```text
{'type': 'DATE', 'tokens': ['12', 'March', '2019'], 'start': 0, 'end': 3}
12 March 2019
```

`" ".join(...)` သည် list ထဲမှ စာသားများကို space ခြားပြီး စာသားတစ်ခုတည်း ပြန်ပေးသည်။

### Condition နံပါတ် ၃ သည် အဘယ်ကြောင့် လိုအပ်သနည်း။

Label မစစ်ဘဲ ရေးကြည့်ပါ —

```python
def decode(tokens, tags, strict):
    spans, current = [], None
    for index, (token, tag) in enumerate(zip(tokens, tags)):
        if tag.startswith("B-"):
            if current is not None:
                spans.append(current)
            current = {"type": tag[2:], "tokens": [token], "start": index, "end": index + 1}
        elif tag.startswith("I-") and current is not None \
                and (not strict or tag[2:] == current["type"]):
            current["tokens"].append(token)
            current["end"] = index + 1
        else:
            if current is not None:
                spans.append(current)
            current = None
    if current is not None:
        spans.append(current)
    return [(s["type"], " ".join(s["tokens"]), s["start"], s["end"]) for s in spans]


tokens = ["Sundar", "Pichai", "London"]
tags = ["B-PER", "I-PER", "I-LOC"]

print("strict (with type check)  :", decode(tokens, tags, True))
print("loose  (without type check):", decode(tokens, tags, False))
```

Output —

```text
strict (with type check)  : [('PER', 'Sundar Pichai', 0, 2)]
loose  (without type check): [('PER', 'Sundar Pichai London', 0, 3)]
```

`I-LOC` သည် `PER` entity ထဲ ရောက်သွားသောအခါ label မစစ်လျှင် `London` သည် လူအမည်ထဲ
ပါသွားသည်။ Condition နံပါတ် ၃ သည် ဤသို့ မှားယွင်းသော ရောစပ်ခြင်းကို တားပေးသည်။

Tag sequence မှားနေလျှင်လည်း `else` branch ထဲ ရောက်ပြီး `current` ကို ရှင်းလိုက်သည်။
ဤအခြေအနေတွင် `London` ၏ LOC span သည် ဆုံးရှုံးသွားသည် — ၎င်းသည် data အရည်အသွေး
ပြဿနာဖြစ်ကြောင်း **တိတ်တဆိတ် ဖျောက်ထားခြင်းမဟုတ်ဘဲ** ဤ code ၏ ကန့်သတ်ချက်ဖြစ်သည်။
Production pipeline တစ်ခုတွင် ဤသို့ မကိုက်ညီမှုကို log ထုတ်ရန် လိုအပ်သည်။

---

## 9. `else` Case — Entity ပြီးဆုံးခြင်း

```python
else:
    if current is not None:
        spans.append(current)
    current = None
```

`O` tag များနှင့် အထက်က condition နှစ်ခုလုံး မကိုက်သော အခြေအနေများတွင် ဤ branch ထဲ
ဝင်သည်။ လုပ်ဆောင်ချက်သည် `B-` case ၏ ပထမအဆင့်နှင့် တူသည် — `current` ရှိလျှင်
`spans` ထဲ ရွှေ့ပြီး `current` ကို `None` ပြန်ထားသည်။

`current = None` ကို **မမေ့ရပါ**။ မထားလျှင် entity အဟောင်း ဆက်ရှိနေပြီး `O` token
များက ၎င်းထဲ ရောက်သွားနိုင်သည်။

---

## 10. Loop ပြီးဆုံးချိန် `if current is not None:` — နောက်ဆုံး Span

Loop ပြီးသွားသောအခါ `current` တွင် entity တစ်ခု ကျန်နေနိုင်သည်။ အကြောင်းရင်းမှာ
`spans` ထဲ ရွှေ့ခြင်းသည် **tag အသစ် လာသောအခါ** သို့မဟုတ် **`O` လာသောအခါ** သာ
ဖြစ်ခြင်းကြောင့်ဖြစ်သည်။ စာသားသည် entity နှင့်သာ ဆုံးသွားလျှင် ရွှေ့ရန် အခွင့်အရေး မရတော့ပါ။

```python
def decode_no_flush(tokens, tags):
    spans, current = [], None
    for index, (token, tag) in enumerate(zip(tokens, tags)):
        if tag.startswith("B-"):
            if current is not None:
                spans.append(current)
            current = {"type": tag[2:], "tokens": [token], "start": index, "end": index + 1}
        elif tag.startswith("I-") and current is not None and tag[2:] == current["type"]:
            current["tokens"].append(token)
            current["end"] = index + 1
        else:
            if current is not None:
                spans.append(current)
            current = None
    return [(s["type"], " ".join(s["tokens"])) for s in spans]


print(decode_no_flush(["Sundar", "Pichai", "visited", "London"],
                      ["B-PER", "I-PER", "O", "B-LOC"]))
```

Output —

```text
[('PER', 'Sundar Pichai')]
```

`B-LOC` အတွက် ဖန်တီးထားသော `current` သည် `spans` ထဲ မ၀င်လိုက်ရဘဲ ဆုံးရှုံးသွားသည်။
Function ၏ ထိပ်တွင်ရှိသော `if current is not None: spans.append(current)` သည်
ဤအခြေအနေအတွက် ဖြစ်သည်။

---

## 11. `return` — ရလဒ်ကို ပြန်ဖွဲ့ခြင်း

```python
return [{"type": s["type"], "text": " ".join(s["tokens"]),
         "start": s["start"], "end": s["end"]} for s in spans]
```

Loop အတွင်း အလုပ်လုပ်သောအခါ `tokens` key ထဲတွင် **token စာရင်း** (`list`) ကို သိမ်းထားသည်။
ပြန်ပေးသောအခါတွင် ဤ list ကို `" ".join(...)` ဖြင့် **စာသားတစ်ခုတည်း** အဖြစ် ပြောင်းပြီး
key အမည်ကိုလည်း `tokens` မှ `text` သို့ ပြောင်းသည်။

```python
spans = [{"type": "PER", "tokens": ["Sundar", "Pichai"], "start": 0, "end": 2}]

print([{"type": s["type"], "text": " ".join(s["tokens"]),
        "start": s["start"], "end": s["end"]} for s in spans])
```

Output —

```text
[{'type': 'PER', 'text': 'Sundar Pichai', 'start': 0, 'end': 2}]
```

List comprehension တစ်ခုတည်းဖြင့် dictionary အသစ်များကို ဖန်တီးသည်။ ပုံမှန် loop
ဖြင့် ရေးမည်ဆိုလျှင် —

```python
results = []
for s in spans:
    results.append({"type": s["type"], "text": " ".join(s["tokens"]),
                    "start": s["start"], "end": s["end"]})
return results
```

ဤသို့ ခွဲထားခြင်းကြောင့် **အတွင်းပိုင်း data structure (`tokens` list)** နှင့်
**ပြင်ပသို့ ပေးသော format (`text` string)** ကို ခွဲထားနိုင်သည်။

---

## 12. Loop တစ်ခုချင်းစီ အလုပ်လုပ်ပုံ

`tokens` နှင့် `tags` ကို index အလိုက် လိုက်ကြည့်ပါ။

| index | token | tag | Branch | `current` (ပြီးနောက်) | `spans` အရေအတွက် |
| --- | --- | --- | --- | --- | --- |
| 0 | `Sundar` | `B-PER` | B- | `PER: Sundar` | 0 |
| 1 | `Pichai` | `I-PER` | I- | `PER: Sundar Pichai` | 0 |
| 2 | `visited` | `O` | else | `None` | 1 |
| 3 | `London` | `B-LOC` | B- | `LOC: London` | 1 |
| 4 | `on` | `O` | else | `None` | 2 |
| 5 | `12` | `B-DATE` | B- | `DATE: 12` | 2 |
| 6 | `March` | `I-DATE` | I- | `DATE: 12 March` | 2 |
| 7 | `2019` | `I-DATE` | I- | `DATE: 12 March 2019` | 2 |
| 8 | `.` | `O` | else | `None` | 3 |

Loop ပြီးသောအခါ `spans` ထဲတွင် span သုံးခု ရှိပြီး `current` သည် `None` ဖြစ်သည်။

---

## 13. ရလဒ်ကို ထုတ်ခြင်း

```python
for span in decode_bio(tokens, tags):
    print("%-5s %-15s tokens[%d:%d]"
          % (span["type"], span["text"], span["start"], span["end"]))
```

`%-5s` သည် စာသားကို ဘယ်ဘက်ညှိပြီး အကျယ် ၅ လုံး ယူသည်။ `%-15s` သည်လည်း
အကျယ် ၁၅ လုံးဖြစ်သည်။ ဤသို့လုပ်လျှင် တိုင်တစ်လျှောက် ကော်လံများ တန်းနေသည်။

Expected output —

```text
PER   Sundar Pichai   tokens[0:2]
LOC   London          tokens[3:4]
DATE  12 March 2019   tokens[5:8]
```

`tokens[5:8]` သည် `["12", "March", "2019"]` ဖြစ်သည်။ `end` သည် exclusive ဖြစ်သောကြောင့်
index 8 မပါဝင်ပါ။

---

## 14. Code တစ်ခုလုံး — Run လုပ်နိုင်သော Version

```python
def decode_bio(tokens, tags):
    spans, current = [], None
    for index, (token, tag) in enumerate(zip(tokens, tags)):
        if tag.startswith("B-"):
            if current is not None:
                spans.append(current)
            current = {"type": tag[2:], "tokens": [token],
                       "start": index, "end": index + 1}
        elif tag.startswith("I-") and current is not None and tag[2:] == current["type"]:
            current["tokens"].append(token)
            current["end"] = index + 1
        else:
            if current is not None:
                spans.append(current)
            current = None
    if current is not None:
        spans.append(current)
    return [{"type": s["type"], "text": " ".join(s["tokens"]),
             "start": s["start"], "end": s["end"]} for s in spans]


tokens = ["Sundar", "Pichai", "visited", "London", "on",
          "12", "March", "2019", "."]
tags = ["B-PER", "I-PER", "O", "B-LOC", "O",
        "B-DATE", "I-DATE", "I-DATE", "O"]

for span in decode_bio(tokens, tags):
    print("%-5s %-15s tokens[%d:%d]"
          % (span["type"], span["text"], span["start"], span["end"]))
```

Output —

```text
PER   Sundar Pichai   tokens[0:2]
LOC   London          tokens[3:4]
DATE  12 March 2019   tokens[5:8]
```

---

## 15. ကိုယ်တိုင်လေ့ကျင့်ကြည့်ပါ

**မေးခွန်း** — အောက်ပါ input အတွက် `decode_bio()` သည် span မည်မျှ ပြန်ပေးမည်နည်း။

```python
tokens = ["Alice", "Chen", "founded", "Acme", "Corp"]
tags = ["B-PER", "I-PER", "O", "B-ORG", "I-ORG"]
```

1. 1 span
2. 2 span — `PER` နှင့် `ORG`
3. 3 span
4. 0 span — နောက်ဆုံး entity ဆုံးရှုံးမည်

<details>
<summary>အဖြေ ကြည့်ရန်</summary>

**အဖြေ — 2. 2 span — `PER` နှင့် `ORG`**

အကြောင်းရင်း — index 0 မှ `B-PER` ဖြင့် `current` စတင်သည်။ index 1 ၏ `I-PER` သည်
label တူသဖြင့် `Alice Chen` ဖြစ်လာသည်။ index 2 ၏ `O` သည် else branch သို့ ရောက်ပြီး
`PER` span ကို `spans` ထဲ ရွှေ့သည်။ index 3 မှ `B-ORG` ဖြင့် `current` အသစ် စသည်။
index 4 ၏ `I-ORG` သည် ဆက်တွဲသည်။

စာသားသည် entity နှင့် ဆုံးသည်ဖြစ်သဖြင့် loop ပြီးချိန် `current` တွင် `ORG` span
ကျန်နေသည်။ Loop အပြင် Section 10 ၏ `if current is not None: spans.append(current)`
မရှိပါက နောက်ဆုံး span ဆုံးရှုံးမည် — ထို့ကြောင့် ဤစစ်ဆေးချက် လိုအပ်သည်။

ရလဒ် — `[{'type': 'PER', 'text': 'Alice Chen', ...}, {'type': 'ORG', 'text': 'Acme Corp', ...}]`

</details>

---

**အဓိက မှတ်ထားရန်** — Token-level tag များမှ span-level entity များသို့ ပြောင်းသည့်
ဤ decoding အဆင့်သည် NER pipeline တိုင်းတွင် ရှိသည်။ State variable (`current`) ကို
Loop အတွင်း ထိန်းသိမ်းခြင်း၊ Loop အပြင် နောက်ဆုံးအကြိမ် flush လုပ်ခြင်း နှင့်
Tag များ၏ ကိုက်ညီမှုကို စစ်ဆေးခြင်း သုံးချက်သည် ဤအလုပ်၏ အဓိကအချက်များ ဖြစ်သည်။
