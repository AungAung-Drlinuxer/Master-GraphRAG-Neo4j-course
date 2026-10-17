# Walkthrough 06 — Precision, Recall, F1 (Exercise 6)

> ဤဖိုင်သည် Module 01 ၏ `solution.md` ထဲက Exercise 6 ကို **Python အခြေခံမှ စ၍**
> အပိုင်းလိုက် ရှင်းပြသည့် walkthrough ဖြစ်သည်။

---

## 0. ဤ Exercise က ဘာကို ဖြေရှင်းပေးသလဲ။

Exercise 1–5 တွင် entity နှင့် relationship များကို ထုတ်ယူခဲ့သည်။ သို့သော်
**ထုတ်ယူသော ရလဒ်က မည်မျှမှန်သည်** ဆိုသည်ကို မသိရသေးပါ။ ဤ Exercise သည်
ထိုအဖြေကို **Precision**၊ **Recall** နှင့် **F1** ဖြင့် တိုင်းတာပုံကို လုပ်ပြသည်။

စာမေးပွဲတစ်ခုကဲ့သို့ စဉ်းစားပါ။ `GOLD_TRIPLES` သည် **အဖြေစာအုပ်** (လူက ကိုယ်တိုင်
မှတ်ထားသော အဖြေမှန်) ဖြစ်ပြီး `PRED_TRIPLES` သည် **system ၏ အဖြေ** ဖြစ်သည်။

```text
GOLD_TRIPLES :
  (Sundar Pichai, CEO_OF, Google)
  (Larry Page, FOUNDED, Google)
  (Satya Nadella, CEO_OF, Microsoft)

PRED_TRIPLES :
  (Sundar Pichai, CEO_OF, Google)
  (Larry Page, FOUNDED, Google)
  (Sundar Pichai, CEO_OF, Alphabet)
```

ဤ code တွင် လေ့လာရမည့် Python concepts များမှာ —

- `set` နှင့် set operations (`&`၊ `-`)
- `len()`
- Conditional expression ဖြင့် သုည စစ်ဆေးခြင်း
- `ZeroDivisionError`
- Tuple အဖြစ် တန်ဖိုးများစွာ ပြန်ပေးခြင်း
- Tuple unpacking
- `%` formatting နှင့် `%.4f`

---

## 1. `GOLD_TRIPLES` နှင့် `PRED_TRIPLES` — Set နှစ်ခု

```python
GOLD_TRIPLES = {
    ("Sundar Pichai", "CEO_OF", "Google"),
    ("Larry Page", "FOUNDED", "Google"),
    ("Satya Nadella", "CEO_OF", "Microsoft"),
}
PRED_TRIPLES = {
    ("Sundar Pichai", "CEO_OF", "Google"),
    ("Larry Page", "FOUNDED", "Google"),
    ("Sundar Pichai", "CEO_OF", "Alphabet"),
}
```

ဤတစ်ခါ list မဟုတ်ဘဲ **set** ကို သုံးထားသည်။ `{...}` သည် set literal ဖြစ်သည်။

| လက္ခဏာ | List | Set |
| --- | --- | --- |
| အစဉ် (order) | ရှိသည် | မရှိပါ |
| အစိတ်အပိုင်း ထပ်နိုင်ခြင်း | ထပ်နိုင်သည် | မထပ်နိုင်ပါ |
| ပါဝင်မှု စစ်ခြင်း (`in`) | နှေးသည် | မြန်သည် |
| စာရင်းချင်း နှိုင်းယှဉ်ခြင်း | အစဉ် စစ်ရသည် | `&`၊ `-` ဖြင့် လွယ်သည် |

Triple များကို **နှိုင်းယှဉ်** လိုသောကြောင့် set က သင့်တော်သည်။ Triple တစ်ခု
ထပ်ပါလာလျှင် set က အလိုအလျောက် ဖျောက်ပေးသည်။

```python
print(3 == 3.0)
print({("a", "b")} == {("a", "b")})
print(len(GOLD_TRIPLES), len(PRED_TRIPLES))
```

Output —

```text
True
True
3 3
```

---

## 2. Set Operations — TP၊ FP၊ FN

```python
true_positive = len(gold & predicted)
false_positive = len(predicted - gold)
false_negative = len(gold - predicted)
```

| Operator | အဓိပ္ပာယ် | ဤ Exercise တွင် |
| --- | --- | --- |
| `&` | Intersection — နှစ်ခုလုံးတွင် ပါဝင်သည် | **TP** (True Positive) |
| `-` | Difference — ရှေ့ကတွင် ပါဝင်ပြီး နောက်တွင် မပါ | **FP** / **FN** |

```python
print("TP :", sorted(GOLD_TRIPLES & PRED_TRIPLES))
print("FP :", sorted(PRED_TRIPLES - GOLD_TRIPLES))
print("FN :", sorted(GOLD_TRIPLES - PRED_TRIPLES))
```

Output —

```text
TP : [('Larry Page', 'FOUNDED', 'Google'), ('Sundar Pichai', 'CEO_OF', 'Google')]
FP : [('Sundar Pichai', 'CEO_OF', 'Alphabet')]
FN : [('Satya Nadella', 'CEO_OF', 'Microsoft')]
```

`set` ၏ repr အစီအစဉ်သည် process တစ်ခုနှင့်တစ်ခု မတူညီနိုင် (Python က hash seed ကို
random ဖြစ်စေသည်)။ ထို့ကြောင့် ရလဒ်ကို ဖတ်ရလွယ်ပြီး run တိုင်း တူညီစေရန် `sorted()` ဖြင့် ပြထားသည်။

### အမည်များ၏ အဓိပ္ပာယ်

| အမည် | အတိုကောက် | အဓိပ္ပာယ် | ဤ Exercise တွင် |
| --- | --- | --- | --- |
| True Positive | TP | System က ဆိုသည်မှာ မှန်ပြီး အဖြေစာအုပ်တွင် ရှိသည် | 2 |
| False Positive | FP | System က ဆိုသည်မှာ မှားသည် (အဖြေစာအုပ်တွင် မရှိ) | 1 |
| False Negative | FN | အဖြေစာအုပ်တွင် ရှိသော်လည်း system က လွတ်သွားသည် | 1 |

Set order ကို အာမမခံပါ — ဤဖိုင်ထဲမှ output blocks များတွင် element အစဉ်သည် run
တစ်ခုနှင့်တစ်ခု ကွဲနိုင်သည်။ ထို့ကြောင့် နောက်ပိုင်းတွင် **အရေအတွက်** (`len`) ကိုသာ
အသုံးပြုသည်။

```python
print(len(GOLD_TRIPLES & PRED_TRIPLES))
print(len(PRED_TRIPLES - GOLD_TRIPLES))
print(len(GOLD_TRIPLES - PRED_TRIPLES))
```

Output —

```text
2
1
1
```

---

## 3. Precision — "မည်မျှ မှန်သလဲ"

```python
precision = (true_positive / (true_positive + false_positive)
             if (true_positive + false_positive) else 0.0)
```

Precision က မေးသည်မှာ —

> System က အဖြေအဖြစ် ပြောလိုက်သော triple များထဲတွင် မည်မျှ မှန်သလဲ။

ဖော်မြူလာ —

```text
precision = TP / (TP + FP)
```

| အပိုင်း | တန်ဖိုး |
| --- | --- |
| TP | 2 |
| FP | 1 |
| TP + FP | 3 (system ပြောခဲ့သမျှ) |
| precision | 2 / 3 = 0.6667 |

Precision နည်းခြင်းသည် **စိတ်ချရမှု နည်း** ခြင်းဖြစ်သည် — system က မရှိသော relationship
များကို ဖန်တီးနေသည်ဟု ဆိုလိုသည်။ Graph ထဲတွင် မှားသော edge များ ဝင်လာမည်။

---

## 4. Recall — "ရှိသမျှကို မည်မျှ ဖမ်းမိသလဲ"

```python
recall = (true_positive / (true_positive + false_negative)
          if (true_positive + false_negative) else 0.0)
```

Recall က မေးသည်မှာ —

> အဖြေစာအုပ်ထဲတွင် ရှိသမျှ triple များထဲမှ မည်မျှ ရှာတွေ့သလဲ။

ဖော်မြူလာ —

```text
recall = TP / (TP + FN)
```

| အပိုင်း | တန်ဖိုး |
| --- | --- |
| TP | 2 |
| FN | 1 |
| TP + FN | 3 (တကယ်ရှိသမျှ) |
| recall | 2 / 3 = 0.6667 |

Recall နည်းခြင်းသည် **လွတ်သွားမှု များ** ခြင်းဖြစ်သည် — တကယ်ရှိသော relationship များ
graph ထဲ မဝင်လာပါ။

---

## 5. F1 — နှစ်ခုကို ပေါင်းစည်းခြင်း

```python
f1 = (2 * precision * recall / (precision + recall)
      if (precision + recall) else 0.0)
```

F1 သည် precision နှင့် recall ၏ **harmonic mean** ဖြစ်သည်။

```text
f1 = 2 * (precision * recall) / (precision + recall)
```

| အပိုင်း | တန်ဖိုး |
| --- | --- |
| precision | 0.6667 |
| recall | 0.6667 |
| 2 × p × r | 0.8889 |
| p + r | 1.3333 |
| f1 | 0.8889 / 1.3333 = 0.6667 |

### အဘယ်ကြောင့် ရိုးရိုး ပျမ်းမျှ မဟုတ်ဘဲ harmonic mean ဖြစ်သနည်း။

Precision 1.0 ဖြစ်ပြီး recall 0.0 ဖြစ်သော system တစ်ခုကို စဉ်းစားပါ —
triple တစ်ခုတည်း ပြောပြီး ၎င်း မှန်သည်ဆိုလျှင် precision = 1.0 ဖြစ်သည်။ ရိုးရိုး
ပျမ်းမျှ (`(1.0 + 0.0) / 2 = 0.5`) ဆိုလျှင် ဤ system က ထက်ဝက်မှန်သည်ဟု ဆိုသလို
ဖြစ်သွားသည်။ အမှန်တကယ်တွင် ၎င်းက အလွန်အသုံးမကျပါ။

```python
p, r = 1.0, 0.0

print("ရိုးရိုးပျမ်းမျှ  : %.4f" % ((p + r) / 2))
print("harmonic mean : %.4f" % (2 * p * r / (p + r)))
```

Output —

```text
ရိုးရိုးပျမ်းမျှ  : 0.5000
harmonic mean : 0.0000
```

Harmonic mean သည် နှစ်ခုထဲမှ **နည်းသောတန်ဖိုး** ကို အလေးထားသည်။ ထို့ကြောင့်
အခြမ်းတစ်ခု ပျက်နေလျှင် F1 သည် ပျက်နေမှုကို ထင်ဟပ်ပြသည်။

---

## 6. `if ... else 0.0` — သုညဖြင့် စားခြင်းမှ ကာကွယ်ခြင်း

```python
precision = (true_positive / (true_positive + false_positive)
             if (true_positive + false_positive) else 0.0)
```

ဤ condition သည် `true_positive + false_positive` ကို စစ်သည်။ Python တွင် `0` သည်
falsy ဖြစ်သောကြောင့် —

- တန်ဖိုးက `0` ဖြစ်လျှင် → `0.0` ကို သုံးသည်။
- `0` မဟုတ်လျှင် → စားခြင်းကို လုပ်သည်။

မကာကွယ်လျှင် မည်သို့ဖြစ်မည်နည်း —

```python
tp, fp = 0, 0

try:
    print(tp / (tp + fp))
except ZeroDivisionError as exc:
    print("ZeroDivisionError:", exc)
```

Output —

```text
ZeroDivisionError: division by zero
```

| အခြေအနေ | ကာကွယ်ချက် မရှိရင် | ကာကွယ်ချက် ရှိရင် |
| --- | --- | --- |
| System က triple မပြောခဲ့ (`tp=0, fp=0`) | `ZeroDivisionError` | precision = `0.0` |
| အဖြေစာအုပ် အလွတ် (`tp=0, fn=0`) | `ZeroDivisionError` | recall = `0.0` |
| precision = recall = 0 | `ZeroDivisionError` | f1 = `0.0` |

၎င်းသည် Module 00 ၏ Exercise 6 တွင် GraphRAG readiness report ကို metric မရှိဘဲ
ခေါ်ခြင်းနှင့် တူညီသည် — **အခြေအနေဆိုးတွင် တိတ်တဆိတ် ပျက်မနေစေဘဲ တန်ဖိုးတစ်ခု
ပြန်ပေးခြင်း** ဖြစ်သည်။

---

## 7. `return` ဖြင့် တန်ဖိုးများစွာ ပြန်ပေးခြင်း

```python
return precision, recall, f1, true_positive, false_positive, false_negative
```

Python တွင် `return a, b, c` ဟု ရေးလျှင် **tuple** တစ်ခုအဖြစ် ပြန်ပေးသည်။

```python
def demo():
    return 1, 2, 3

print(demo())
print(type(demo()))

a, b, c = demo()
print(a, b, c)
```

Output —

```text
(1, 2, 3)
<class 'tuple'>
1 2 3
```

ခေါ်သည့်နေရာတွင် `precision, recall, f1, tp, fp, fn = prf1(...)` ဟု tuple unpacking
ဖြင့် ပြန်ခွဲယူသည်။

```python
precision, recall, f1, tp, fp, fn = prf1(GOLD_TRIPLES, PRED_TRIPLES)
print("tp=%d fp=%d fn=%d" % (tp, fp, fn))
print("precision=%.4f recall=%.4f f1=%.4f" % (precision, recall, f1))
```

`%.4f` သည် ဒသမ နောက် ၄ လုံးအထိ ဖော်ပြသည်။

```python
value = 0.6666666666666666

print("default :", value)
print("2 digits: %.2f" % value)
print("4 digits: %.4f" % value)
print("rounded :", round(value, 4))
```

Output —

```text
default : 0.6666666666666666
2 digits: 0.67
4 digits: 0.6667
rounded : 0.6667
```

Expected output (တစ်ခုလုံး) —

```text
tp=2 fp=1 fn=1
precision=0.6667 recall=0.6667 f1=0.6667
```

---

## 8. ရလဒ် အားလုံးကို ဇယားဖြင့် ကြည့်ခြင်း

| အခြေအနေ | TP | FP | FN | Precision | Recall | F1 |
| --- | --- | --- | --- | --- | --- | --- |
| ဤ Exercise (`GOLD` vs `PRED`) | 2 | 1 | 1 | 0.6667 | 0.6667 | 0.6667 |
| အဖြေ အားလုံးမှန် | 3 | 0 | 0 | 1.0000 | 1.0000 | 1.0000 |
| System က triple မပြောခဲ့ | 0 | 0 | 3 | 0.0000 | 0.0000 | 0.0000 |
| အဖြေစာအုပ် အလွတ် | 0 | 3 | 0 | 0.0000 | 0.0000 | 0.0000 |
| နှစ်ခုလုံး အလွတ် | 0 | 0 | 0 | 0.0000 | 0.0000 | 0.0000 |

ဇယား၏ အောက်ဆုံးလိုင်းသုံးလိုင်းကို စမ်းကြည့်နိုင်သည်။

```python
GOLD_TRIPLES = {
    ("Sundar Pichai", "CEO_OF", "Google"),
    ("Larry Page", "FOUNDED", "Google"),
    ("Satya Nadella", "CEO_OF", "Microsoft"),
}
PRED_TRIPLES = {
    ("Sundar Pichai", "CEO_OF", "Google"),
    ("Larry Page", "FOUNDED", "Google"),
    ("Sundar Pichai", "CEO_OF", "Alphabet"),
}


def prf1(gold, predicted):
    tp = len(gold & predicted)
    fp = len(predicted - gold)
    fn = len(gold - predicted)
    p = (tp / (tp + fp)) if (tp + fp) else 0.0
    r = (tp / (tp + fn)) if (tp + fn) else 0.0
    f = (2 * p * r / (p + r)) if (p + r) else 0.0
    return p, r, f


print("perfect      : %.4f %.4f %.4f" % prf1(GOLD_TRIPLES, set(GOLD_TRIPLES)))
print("empty pred   : %.4f %.4f %.4f" % prf1(GOLD_TRIPLES, set()))
print("empty gold   : %.4f %.4f %.4f" % prf1(set(), PRED_TRIPLES))
print("both empty   : %.4f %.4f %.4f" % prf1(set(), set()))
```

Output —

```text
perfect      : 1.0000 1.0000 1.0000
empty pred   : 0.0000 0.0000 0.0000
empty gold   : 0.0000 0.0000 0.0000
both empty   : 0.0000 0.0000 0.0000
```

ဤ Code ကို ရှင်းလင်းရန် `prf1` ကို တိုစေပြီး တန်ဖိုးသုံးခုသာ ပြန်စေထားသည်။
မူရင်း Exercise က ရေတွက်မှု တန်ဖိုးများ (`tp`၊ `fp`၊ `fn`) ကိုပါ ပြန်ပေးသည်။

---

## 9. Code တစ်ခုလုံး — Run လုပ်နိုင်သော Version

```python
GOLD_TRIPLES = {
    ("Sundar Pichai", "CEO_OF", "Google"),
    ("Larry Page", "FOUNDED", "Google"),
    ("Satya Nadella", "CEO_OF", "Microsoft"),
}
PRED_TRIPLES = {
    ("Sundar Pichai", "CEO_OF", "Google"),
    ("Larry Page", "FOUNDED", "Google"),
    ("Sundar Pichai", "CEO_OF", "Alphabet"),
}


def prf1(gold, predicted):
    true_positive = len(gold & predicted)
    false_positive = len(predicted - gold)
    false_negative = len(gold - predicted)
    precision = (true_positive / (true_positive + false_positive)
                 if (true_positive + false_positive) else 0.0)
    recall = (true_positive / (true_positive + false_negative)
              if (true_positive + false_negative) else 0.0)
    f1 = (2 * precision * recall / (precision + recall)
          if (precision + recall) else 0.0)
    return precision, recall, f1, true_positive, false_positive, false_negative


precision, recall, f1, tp, fp, fn = prf1(GOLD_TRIPLES, PRED_TRIPLES)
print("tp=%d fp=%d fn=%d" % (tp, fp, fn))
print("precision=%.4f recall=%.4f f1=%.4f" % (precision, recall, f1))
```

Output —

```text
tp=2 fp=1 fn=1
precision=0.6667 recall=0.6667 f1=0.6667
```

---

## 10. ကိုယ်တိုင်လေ့ကျင့်ကြည့်ပါ

**မေးခွန်း** — အောက်ပါ set နှစ်ခုအတွက် Precision နှင့် Recall ကို
တွက်ကြည့်ပါ။

```python
gold = {("A", "R1", "B"), ("C", "R2", "D"), ("E", "R3", "F")}
predicted = {("A", "R1", "B"), ("C", "R2", "D"), ("E", "R3", "F"),
             ("G", "R4", "H")}
```

1. Precision = 1.0၊ Recall = 1.0
2. Precision = 0.75၊ Recall = 1.0
3. Precision = 1.0၊ Recall = 0.75
4. Precision = 0.75၊ Recall = 0.75

<details>
<summary>အဖြေ ကြည့်ရန်</summary>

**အဖြေ — 2. Precision = 0.75၊ Recall = 1.0**

အကြောင်းရင်း —

| တန်ဖိုး | ရေတွက်မှု | အဖြေ |
| --- | --- | --- |
| TP (`gold & predicted`) | ပထမသုံးခုလုံး | 3 |
| FP (`predicted - gold`) | `("G", "R4", "H")` | 1 |
| FN (`gold - predicted`) | မရှိ | 0 |

- Precision = 3 / (3 + 1) = **0.75** — system က ပြောသမျှ ၄ ခုထဲ ၃ ခု မှန်သည်။
- Recall = 3 / (3 + 0) = **1.0** — အဖြေစာအုပ်ထဲမှ အားလုံးကို ဖမ်းမိသည်။

ဤ system သည် relationship မလွတ်သော်လည်း မရှိသော relationship တစ်ခုကို
ဖန်တီးထားသည် — precision နည်းသဖြင့် graph ထဲတွင် မှားသော edge ဝင်လာမည်။

</details>

---

**အဓိက မှတ်ထားရန်** —

- `TP`၊ `FP`၊ `FN` ကို **set operations** (`&`၊ `-`) ဖြင့် ရေတွက်နိုင်သည်။
- Precision သည် "မှန်သလဲ"၊ Recall သည် "လွတ်သွားသလား" ကို ဖြေသည်။
- F1 သည် နှစ်ခုကို ပေါင်းစည်းပြီး **နည်းသောအခြမ်း** ကို အလေးထားသည်။
- Evaluation မလုပ်ဘဲ extraction ကို မြှင့်တင်နိုင်မည် မဟုတ်ပါ — Module 02 တွင် model  ဖြင့် ထုတ်ယူသောအခါ ဤတိုင်းတာမှုကိုသာ ပြန်သုံးမည်။
