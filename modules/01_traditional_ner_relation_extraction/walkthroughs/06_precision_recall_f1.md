# Walkthrough 06 — Precision, Recall, F1 (Exercise 6)

> ဤဖိုင်သည် Module 01 ၏ `solution.md` ထဲက Exercise 6 ကို **Python အခြေခံမှ စ၍**
> အပိုင်းလိုက် ရှင်းပြသည့် walkthrough ဖြစ်သည်။

---

## 0. ဤ Exercise က ဘာကို ဖြေရှင်းပေးသလဲ။

Exercise 1–5 မှာ entity နှင့် relationship တွေကို ထုတ်ယူခဲ့ပါတယ်။ ဒါပေမဲ့
**ထုတ်ယူတဲ့ ရလဒ်က ဘယ်လောက်မှန်သလဲ** ဆိုတာကို မသိရသေးပါဘူး။ ဒီ Exercise က
အဲဒီအဖြေကို **Precision**၊ **Recall** နဲ့ **F1** နဲ့ တိုင်းတာပုံကို လုပ်ပြပါတယ်။

စာမေးပွဲတစ်ခုလို စဉ်းစားပါ။ `GOLD_TRIPLES` က **အဖြေစာအုပ်** (လူက ကိုယ်တိုင်
မှတ်ထားတဲ့ အဖြေမှန်) ဖြစ်ပြီး `PRED_TRIPLES` က **system ရဲ့ အဖြေ** ဖြစ်ပါတယ်။

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

ဒီ code မှာ လေ့လာရမယ့် Python concepts တွေကတော့ —

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

ဒီတစ်ခါ list မဟုတ်ဘဲ **set** ကို သုံးထားပါတယ်။ `{...}` က set literal ဖြစ်ပါတယ်။

| လက္ခဏာ | List | Set |
| --- | --- | --- |
| အစဉ် (order) | ရှိသည် | မရှိပါ |
| အစိတ်အပိုင်း ထပ်နိုင်ခြင်း | ထပ်နိုင်သည် | မထပ်နိုင်ပါ |
| ပါဝင်မှု စစ်ခြင်း (`in`) | နှေးသည် | မြန်သည် |
| စာရင်းချင်း နှိုင်းယှဉ်ခြင်း | အစဉ် စစ်ရသည် | `&`၊ `-` ဖြင့် လွယ်သည် |

Triple တွေကို **နှိုင်းယှဉ်** လိုတဲ့အတွက် set က သင့်တော်ပါတယ်။ Triple တစ်ခု
ထပ်ပါလာရင် set က အလိုအလျောက် ဖျောက်ပေးပါတယ်။

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
| `&` | Intersection — နှစ်ခုလုံးမှာ ပါဝင်သည် | **TP** (True Positive) |
| `-` | Difference — ရှေ့ကတွင် ပါဝင်ပြီး နောက်တွင် မပါ | **FP** / **FN** |

```python
print("TP :", GOLD_TRIPLES & PRED_TRIPLES)
print("FP :", PRED_TRIPLES - GOLD_TRIPLES)
print("FN :", GOLD_TRIPLES - PRED_TRIPLES)
```

Output —

```text
TP : {('Larry Page', 'FOUNDED', 'Google'), ('Sundar Pichai', 'CEO_OF', 'Google')}
FP : {('Sundar Pichai', 'CEO_OF', 'Alphabet')}
FN : {('Satya Nadella', 'CEO_OF', 'Microsoft')}
```

### အမည်များ၏ အဓိပ္ပာယ်

| အမည် | အတိုကောက် | အဓိပ္ပာယ် | ဤ Exercise တွင် |
| --- | --- | --- | --- |
| True Positive | TP | System က ဆိုတာမှန်ပြီး အဖြေစာအုပ်မှာ ရှိသည် | 2 |
| False Positive | FP | System က ဆိုတာမှားသည် (အဖြေစာအုပ်မှာ မရှိ) | 1 |
| False Negative | FN | အဖြေစာအုပ်မှာ ရှိပေမဲ့ system က လွတ်သွားသည် | 1 |

Set order က အာမမခံပါဘူး — ဒီဖိုင်ထဲက output blocks တွေမှာ element အစဉ် run
တစ်ခုနှင့်တစ်ခု ကွဲနိုင်ပါတယ်။ ဒါကြောင့် နောက်ပိုင်းမှာ **အရေအတွက်** (`len`) ကိုသာ
အသုံးပြုပါတယ်။

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

## 3. Precision — "ဆိုတာ ဘယ်လောက်မှန်သလဲ"

```python
precision = (true_positive / (true_positive + false_positive)
             if (true_positive + false_positive) else 0.0)
```

Precision က မေးတာက —

> System က အဖြေအဖြစ် ပြောလိုက်တဲ့ triple တွေထဲမှာ ဘယ်လောက် မှန်သလဲ။

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

Precision နည်းတာက **စိတ်ချရမှု နည်း** တာပါ — system က မရှိတဲ့ relationship
တွေကို ဖန်တီးနေတယ်လို့ ဆိုလိုပါတယ်။ Graph ထဲမှာ မှားတဲ့ edge တွေ ဝင်လာပါမယ်။

---

## 4. Recall — "ရှိသမျှကို ဘယ်လောက် ဖမ်းမိသလဲ"

```python
recall = (true_positive / (true_positive + false_negative)
          if (true_positive + false_negative) else 0.0)
```

Recall က မေးတာက —

> အဖြေစာအုပ်ထဲမှာ ရှိသမျှ triple တွေထဲက ဘယ်လောက် ရှာတွေ့သလဲ။

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

Recall နည်းတာက **လွတ်သွားမှု များ** တာပါ — တကယ်ရှိတဲ့ relationship တွေ
graph ထဲ မဝင်လာပါဘူး။

---

## 5. F1 — နှစ်ခုကို ပေါင်းစည်းခြင်း

```python
f1 = (2 * precision * recall / (precision + recall)
      if (precision + recall) else 0.0)
```

F1 က precision နဲ့ recall ရဲ့ **harmonic mean** ဖြစ်ပါတယ်။

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

### ဘာကြောင့် ရိုးရိုး ပျမ်းမျှ မဟုတ်ဘဲ harmonic mean လဲ။

Precision 1.0 ဖြစ်ပြီး recall 0.0 ဖြစ်တဲ့ system တစ်ခုကို စဉ်းစားပါ —
triple တစ်ခုတည်း ပြောပြီး အဲဒါ မှန်တယ်ဆိုရင် precision = 1.0 ဖြစ်ပါတယ်။ ရိုးရိုး
ပျမ်းမျှ (`(1.0 + 0.0) / 2 = 0.5`) ဆိုရင် ဒီ system က ထက်ဝက်မှန်တယ်လို့ ဆိုသလို
ဖြစ်သွားပါတယ်။ တကယ်တော့ ဒါက အလွန်အသုံးမကျပါဘူး။

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

Harmonic mean က နှစ်ခုထဲက **နည်းတဲ့တန်ဖိုး** ကို အလေးထားပါတယ်။ ဒါကြောင့်
အခြမ်းတစ်ခု ပျက်နေရင် F1 က ပျက်နေမှုကို ထင်ဟပ်ပြပါတယ်။

---

## 6. `if ... else 0.0` — သုညနဲ့ စားခြင်းမှ ကာကွယ်ခြင်း

```python
precision = (true_positive / (true_positive + false_positive)
             if (true_positive + false_positive) else 0.0)
```

ဒီ condition က `true_positive + false_positive` ကို စစ်ပါတယ်။ Python မှာ `0` က
falsy ဖြစ်တဲ့အတွက် —

- တန်ဖိုးက `0` ဖြစ်ရင် → `0.0` ကို သုံးပါတယ်။
- `0` မဟုတ်ရင် → စားခြင်းကို လုပ်ပါတယ်။

မကာကွယ်ရင် ဘာဖြစ်လဲ —

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

ဒါက Module 00 ၏ Exercise 6 မှာ GraphRAG readiness report ကို metric မရှိဘဲ
ခေါ်တာနဲ့ တူညီပါတယ် — **အခြေအနေဆိုးမှာ တိတ်တဆိတ် ပျက်မနေစေဘဲ တန်ဖိုးတစ်ခု
ပြန်ပေးခြင်း** ဖြစ်ပါတယ်။

---

## 7. `return` ဖြင့် တန်ဖိုးများစွာ ပြန်ပေးခြင်း

```python
return precision, recall, f1, true_positive, false_positive, false_negative
```

Python မှာ `return a, b, c` လို့ ရေးရင် **tuple** တစ်ခုအဖြစ် ပြန်ပေးပါတယ်။

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

ခေါ်တဲ့နေရာမှာ `precision, recall, f1, tp, fp, fn = prf1(...)` လို့ tuple unpacking
နဲ့ ပြန်ခွဲယူပါတယ်။

```python
precision, recall, f1, tp, fp, fn = prf1(GOLD_TRIPLES, PRED_TRIPLES)
print("tp=%d fp=%d fn=%d" % (tp, fp, fn))
print("precision=%.4f recall=%.4f f1=%.4f" % (precision, recall, f1))
```

`%.4f` က ဒသမ နောက် ၄ လုံးအထိ ဖော်ပြပါတယ်။

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

ဇယားရဲ့ အောက်ဆုံးလိုင်းသုံးလိုင်းကို စမ်းကြည့်နိုင်ပါတယ်။

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

ဒီ Code ကို ရှင်းလင်းဖို့ `prf1` ကို တိုစေပြီး တန်ဖိုးသုံးခုသာ ပြန်စေထားပါတယ်။
မူရင်း Exercise က ရေတွက်မှု တန်ဖိုးများ (`tp`၊ `fp`၊ `fn`) ကိုပါ ပြန်ပေးပါတယ်။

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
- Recall = 3 / (3 + 0) = **1.0** — အဖြေစာအုပ်ထဲက အားလုံးကို ဖမ်းမိသည်။

ဤ system သည် relationship မလွတ်သော်လည်း မရှိသော relationship တစ်ခုကို
ဖန်တီးထားသည် — precision နည်းသဖြင့် graph ထဲတွင် မှားသော edge ဝင်လာမည်။

</details>

---

**အဓိက မှတ်ထားရန်** —

- `TP`၊ `FP`၊ `FN` ကို **set operations** (`&`၊ `-`) ဖြင့် ရေတွက်နိုင်သည်။
- Precision က "ဆိုတာမှန်သလဲ"၊ Recall က "လွတ်သွားသလား" ကို ဖြေသည်။
- F1 က နှစ်ခုကို ပေါင်းစည်းပြီး **နည်းတဲ့အခြမ်း** ကို အလေးထားသည်။
- Evaluation မလုပ်ဘဲ extraction ကို မြှင့်တင်လို့ မရပါ — Module 02 မှာ model
  ဖြင့် ထုတ်ယူတဲ့အခါ ဒီတိုင်းတာမှုကိုပဲ ပြန်သုံးပါမယ်။
