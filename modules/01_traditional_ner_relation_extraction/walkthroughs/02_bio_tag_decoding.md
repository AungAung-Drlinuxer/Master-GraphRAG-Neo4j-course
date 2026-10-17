# Walkthrough 02 — BIO Tag Decoding (Exercise 2)

> ဤဖိုင်သည် Module 01 ၏ `solution.md` ထဲက Exercise 2 ကို **Python အခြေခံမှ စ၍**
> အပိုင်းလိုက် ရှင်းပြသည့် walkthrough ဖြစ်သည်။

---

## 0. ဤ Exercise က ဘာကို ဖြေရှင်းပေးသလဲ။

Exercise 1 မှာ regex နဲ့ anchor လုပ်ထားတဲ့ pattern ဖြင့် entity ရှာခဲ့ပါတယ်။ Model
တွေကတော့ စာသားကို **token** များအဖြစ် ခွဲပြီး token တစ်ခုချင်းစီအတွက် **tag** တစ်ခုစီ
ပြန်ပေးတဲ့ ပုံစံမျိုးနဲ့ အလုပ်လုပ်ပါတယ်။

```text
tokens : Sundar  Pichai  visited  London   on   12  March  2019   .
tags   : B-PER   I-PER   O        B-LOC    O    B-DATE I-DATE I-DATE O
```

ဒီ tag တွေကို ပြန်ဖတ်ပြီး —

- `Sundar Pichai` → `PER` (လူအမည်)
- `London` → `LOC` (နေရာ)
- `12 March 2019` → `DATE` (ရက်စွဲ)

ဆိုတဲ့ **span** များအဖြစ် ပြောင်းပေးတဲ့အလုပ်ကို **decoding** လို့ ခေါ်ပါတယ်။

ဒီ code မှာ လေ့ရမယ့် Python concepts တွေကတော့ —

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

## 1. BIO Scheme ဆိုတာဘာလဲ။

Tag တစ်ခုစီမှာ အပိုင်းနှစ်ခု ရှိပါတယ်။

| အပိုင်း | အဓိပ္ပာယ် |
| --- | --- |
| ရှေ့ဆုံး စာလုံး — `B`၊ `I`၊ `O` | Tag အမျိုးအစား |
| နောက်ဆက် — `PER`၊ `LOC`၊ `DATE` | Entity label |

- **`B-` (Begin)** — entity အသစ်တစ်ခုရဲ့ **ပထမဆုံး** token။
- **`I-` (Inside)** — entity အသစ်ရဲ့ **ဆက်လက်** token။
- **`O` (Outside)** — entity မဟုတ်တဲ့ token။

ဒီ scheme ကြောင့် entity နှစ်ခု ကပ်နေတဲ့အခါ ဘယ်မှာ ခွဲရမလဲ သိနိုင်ပါတယ်။

```text
B-PER I-PER B-PER I-PER
Sundar Pichai Tim  Cook
```

`B-` က entity အသစ်ရဲ့ အစကို အမြဲပြပါတယ်။ `I-` ပဲ ရှိနေရင် entity တစ်ခုတည်း
ဆက်နေတယ်လို့ ဖတ်ပါတယ်။

---

## 2. `tokens` နဲ့ `tags` — Input နှစ်ခု

```python
tokens = ["Sundar", "Pichai", "visited", "London", "on",
          "12", "March", "2019", "."]
tags = ["B-PER", "I-PER", "O", "B-LOC", "O",
        "B-DATE", "I-DATE", "I-DATE", "O"]
```

List နှစ်ခုရဲ့ အရှည် **တူညီရပါတယ်**။ Index တစ်ခုတည်းမှာ `tokens[i]` ရဲ့ tag က
`tags[i]` ဖြစ်ပါတယ်။

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

`zip()` က list နှစ်ခုကို index အလိုက် တွဲပြီး **tuple** များ ထုတ်ပေးပါတယ်။
`for token, tag in zip(tokens, tags):` လို့ ရေးတဲ့အခါ tuple တစ်ခုစီကို variable
နှစ်ခုအဖြစ် အလိုအလျောက် ခွဲလိုက်တာကို **tuple unpacking** လို့ ခေါ်ပါတယ်။

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

`zip()` က tuple များသာ ပေးပါတယ်။ Index လည်း လိုချင်ရင် `enumerate()` ကို အတွင်းထပ်
သုံးပါတယ်။

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

`enumerate(zip(...))` က `(index, (token, tag))` ဆိုတဲ့ ခွေထားတဲ့ tuple ကို ပေးပါတယ်။
`for index, (token, tag) in ...` လို့ ရေးပြီး အပြင်ခွေ နှစ်ခုကို `index`၊ အတွင်းခွေ
နှစ်ခုကို `token` နဲ့ `tag` အဖြစ် ခွဲယူပါတယ်။

Index က ဘာကြောင့် လိုသလဲဆိုတော့ span တစ်ခုစီရဲ့ **အစနဲ့ အဆုံး token index** ကို
မှတ်ထားချင်လို့ပါ။ ဒီ index တွေကို နောက်ပိုင်း graph node တွေဆီ ပြန်ညွှန်းဖို့
(provenance) အသုံးပြုနိုင်ပါတယ်။

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

- `"B-PER"[2:]` — index 2 ကနေ အဆုံးထိ ဖြတ်ယူပါတယ်။ `B` နဲ့ `-` ကို ကျော်လိုက်တာကြောင့်
  `PER` ကျန်ပါတယ်။ String indexing က **0 ကနေ စ** ပါတယ်။
- `startswith("B-")` က tag က `B-` နဲ့ စမစ စစ်ပါတယ်။ `O` အတွက် `False` ရပါတယ်။

ဒီနှစ်ခုကို တွဲသုံးပြီး —

```python
tag = "I-DATE"
if tag.startswith("I-"):
    print("Inside tag, label =", tag[2:])
```

Output —

```text
Inside tag, label = DATE
```

လို့ label ကို ဆွဲထုတ်နိုင်ပါတယ်။

---

## 6. `decode_bio()` ရဲ့ ဖွဲ့စည်းပုံ

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

Variable နှစ်ခုကို ဒီလို သတ်မှတ်ထားပါတယ်။

- `spans` — ပြီးစီးသွားတဲ့ entity များ စုစည်းရာ list။
- `current` — လက်ရှိ ဖတ်နေဆဲ entity။ မရှိသေးရင် `None`။

Loop တစ်ခုချင်းစီမှာ `current` ကို အသစ်ဖန်တီးခြင်း၊ ဆက်တွဲခြင်း၊ သို့မဟုတ်
`spans` ထဲ ရွှေ့ခြင်း သုံးမျိုးထဲ တစ်မျိုး လုပ်ပါတယ်။

---

## 7. `B-` Case — Entity အသစ် စတင်ခြင်း

```python
if tag.startswith("B-"):
    if current is not None:
        spans.append(current)
    current = {"type": tag[2:], "tokens": [token],
               "start": index, "end": index + 1}
```

အဆင့်နှစ်ဆင့် ရှိပါတယ်။

**ပထမအဆင့်** — `current` မှာ entity တစ်ခု ရှိနေရင် အဲဒါကို `spans` ထဲ ရွှေ့ပါတယ်။
`B-` tag တစ်ခု လာတယ်ဆိုတာ entity အဟောင်း ပြီးသွားပြီလို့ ဆိုလိုလို့ပါ။

**ဒုတိယအဆင့်** — entity အသစ်တစ်ခုကို dictionary အဖြစ် ဖန်တီးပါတယ်။

```python
{"type": tag[2:], "tokens": [token], "start": index, "end": index + 1}
```

| Key | တန်ဖိုး | အဓိပ္ပာယ် |
| --- | --- | --- |
| `type` | `tag[2:]` → `PER` | Entity label |
| `tokens` | `[token]` | စုဆောင်းထားတဲ့ token စာရင်း (ပထမဆုံး တစ်လုံးသာ) |
| `start` | `index` | အစ token index |
| `end` | `index + 1` | အဆုံး index — **exclusive** |

`end` က `index + 1` ဖြစ်တာက Python ရဲ့ slice အလေ့အကျင့်နဲ့ ကိုက်ညီအောင်ပါ။

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

Span တစ်ခုက `start=0`၊ `end=2` ဖြစ်ရင် `tokens[0:2]` နဲ့ တိုက်ရိုက် ဖြတ်ယူနိုင်ပါတယ်။

---

## 8. `I-` Case — Entity ဆက်လက်ခြင်း

```python
elif tag.startswith("I-") and current is not None and tag[2:] == current["type"]:
    current["tokens"].append(token)
    current["end"] = index + 1
```

ဒီ `elif` က **condition သုံးခု** ကို `and` နဲ့ ဆက်ထားပါတယ်။ သုံးခုလုံး မှန်မှ
ဒီ branch ထဲ ဝင်ပါတယ်။

1. `tag.startswith("I-")` — tag က `I-` နဲ့ စတယ်။
2. `current is not None` — လက်ရှိ entity တစ်ခု ရှိနေတယ်။
3. `tag[2:] == current["type"]` — tag ရဲ့ label က `current` ရဲ့ label နဲ့ တူတူဖြစ်တယ်။

ဒီအလုပ်ကို လုပ်တဲ့အခါ —

- `current["tokens"].append(token)` — token အသစ်ကို စာရင်းထဲ ထည့်။
- `current["end"] = index + 1` — အဆုံး index ကို အသစ်ပြန်။

စုစည်းတဲ့အပိုင်းကို ကြည့်ပါ။

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

`" ".join(...)` က list ထဲက စာသားများကို space ခြားပြီး စာသားတစ်ခုတည်း ပြန်ပေးပါတယ်။

### Condition နံပါတ် ၃ က ဘာကြောင့် လိုသလဲ။

Label မစစ်ဘဲ ရေးကြည့်ရအောင် —

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

`I-LOC` က `PER` entity ထဲ ရောက်သွားတဲ့အခါ label မစစ်ရင် `London` က လူအမည်ထဲ
ပါသွားပါတယ်။ Condition နံပါတ် ၃ က ဒီလို မှားယွင်းတဲ့ ရောစပ်ခြင်းကို တားပေးပါတယ်။

Tag sequence မှားနေရင်လည်း `else` branch ထဲ ရောက်ပြီး `current` ကို ရှင်းလိုက်ပါတယ်။
ဒီအခြေအနေမှာ `London` ရဲ့ LOC span က ဆုံးရှုံးသွားပါတယ် — ဒါက data အရည်အသွေး
ပြဿနာဖြစ်ကြောင်း **တိတ်တဆိတ် ဖျောက်ထားခြင်းမဟုတ်ဘဲ** ဒီ code ရဲ့ ကန့်သတ်ချက်ပါ။
Production pipeline တစ်ခုမှာ ဒီလို မကိုက်ညီမှုကို log ထုတ်ဖို့ လိုအပ်ပါတယ်။

---

## 9. `else` Case — Entity ပြီးဆုံးခြင်း

```python
else:
    if current is not None:
        spans.append(current)
    current = None
```

`O` tag တွေနဲ့ အထက်က condition နှစ်ခုလုံး မကိုက်တဲ့ အခြေအနေတွေမှာ ဒီ branch ထဲ
ဝင်ပါတယ်။ လုပ်ဆောင်ချက်က `B-` case ရဲ့ ပထမအဆင့်နဲ့ တူပါတယ် — `current` ရှိရင်
`spans` ထဲ ရွှေ့ပြီး `current` ကို `None` ပြန်ထားပါတယ်။

`current = None` ကို **မမေ့ရပါ**။ မထားရင် entity အဟောင်း ဆက်ရှိနေပြီး `O` token
တွေက သူ့ထဲ ရောက်သွားနိုင်ပါတယ်။

---

## 10. Loop ပြီးဆုံးချိန် `if current is not None:` — နောက်ဆုံး Span

Loop ပြီးသွားတဲ့အခါ `current` မှာ entity တစ်ခု ကျန်နေနိုင်ပါတယ်။ အကြောင်းရင်းက
`spans` ထဲ ရွှေ့တာက **tag အသစ် လာတဲ့အခါ** သို့မဟုတ် **`O` လာတဲ့အခါ** သာ
ဖြစ်လို့ပါ။ စာသားက entity နဲ့ပဲ ဆုံးသွားရင် ရွှေ့ဖို့ အခွင့်အရေး မရတော့ပါဘူး။

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

`B-LOC` အတွက် ဖန်တီးထားတဲ့ `current` က `spans` ထဲ မ၀င်လိုက်ရဘဲ ဆုံးရှုံးသွားပါတယ်။
Function ရဲ့ ထိပ်မှာရှိတဲ့ `if current is not None: spans.append(current)` က
ဒီအခြေအနေအတွက် ဖြစ်ပါတယ်။

---

## 11. `return` — ရလဒ်ကို ပြန်ဖွဲ့ခြင်း

```python
return [{"type": s["type"], "text": " ".join(s["tokens"]),
         "start": s["start"], "end": s["end"]} for s in spans]
```

Loop အတွင်း အလုပ်လုပ်တဲ့အခါ `tokens` key ထဲမှာ **token စာရင်း** (`list`) ကို သိမ်းထားပါတယ်။
ပြန်ပေးတဲ့အခါမှာ ဒီ list ကို `" ".join(...)` နဲ့ **စာသားတစ်ခုတည်း** အဖြစ် ပြောင်းပြီး
key အမည်ကိုလည်း `tokens` ကနေ `text` သို့ ပြောင်းပါတယ်။

```python
spans = [{"type": "PER", "tokens": ["Sundar", "Pichai"], "start": 0, "end": 2}]

print([{"type": s["type"], "text": " ".join(s["tokens"]),
        "start": s["start"], "end": s["end"]} for s in spans])
```

Output —

```text
[{'type': 'PER', 'text': 'Sundar Pichai', 'start': 0, 'end': 2}]
```

List comprehension တစ်ခုတည်းနဲ့ dictionary အသစ်များကို ဖန်တီးပါတယ်။ ပုံမှန် loop
နဲ့ ရေးမယ်ဆိုရင် —

```python
results = []
for s in spans:
    results.append({"type": s["type"], "text": " ".join(s["tokens"]),
                    "start": s["start"], "end": s["end"]})
return results
```

ဒီလို ခွဲထားတာကြောင့် **အတွင်းပိုင်း data structure (`tokens` list)** နဲ့
**ပြင်ပသို့ ပေးတဲ့ format (`text` string)** ကို ခွဲထားနိုင်ပါတယ်။

---

## 12. Loop တစ်ခုချင်းစီ အလုပ်လုပ်ပုံ

`tokens` နဲ့ `tags` ကို index အလိုက် လိုက်ကြည့်ပါ။

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

Loop ပြီးတဲ့အခါ `spans` ထဲမှာ span သုံးခု ရှိပြီး `current` က `None` ဖြစ်ပါတယ်။

---

## 13. ရလဒ်ကို ထုတ်ခြင်း

```python
for span in decode_bio(tokens, tags):
    print("%-5s %-15s tokens[%d:%d]"
          % (span["type"], span["text"], span["start"], span["end"]))
```

`%-5s` က စာသားကို ဘယ်ဘက်ညှိပြီး အကျယ် ၅ လုံး ယူပါတယ်။ `%-15s` ကလည်း
အကျယ် ၁၅ လုံးပါ။ ဒီလိုလုပ်ရင် တိုင်တစ်လျှောက် ကော်လံများ တန်းနေပါတယ်။

Expected output —

```text
PER   Sundar Pichai   tokens[0:2]
LOC   London          tokens[3:4]
DATE  12 March 2019   tokens[5:8]
```

`tokens[5:8]` က `["12", "March", "2019"]` ဖြစ်ပါတယ်။ `end` က exclusive ဖြစ်တဲ့အတွက်
index 8 မပါဝင်ပါဘူး။

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

**မေးခွန်း** — အောက်ပါ input အတွက် `decode_bio()` က ဘယ် span မည်မျှ ပြန်ပေးမလဲ။

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
Tag များ၏ ကိုက်ညီမှုကို စစ်ဆေးခြင်း သုံးချက်သည် ဤအလုပ်ရဲ့ အဓိကအချက်များ ဖြစ်သည်။
