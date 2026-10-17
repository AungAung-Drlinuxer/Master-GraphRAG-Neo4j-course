# Walkthrough 05 — Batch transaction sizing (Exercise 5)

> ဤဖိုင်သည် Module 06 ၏ `solution.md` ထဲက Exercise 5 ကို **Python အခြေခံမှ စ၍**
> အပိုင်းလိုက် ရှင်းပြသည့် walkthrough ဖြစ်သည်။ ဤ Exercise သည် server မခေါ်ဘဲ
> latency model တစ်ခုဖြင့် batch size ကို ရွေးချယ်ခြင်းကို တွက်ချက်သည်။

---

## 0. ဤ Exercise က ဘာကို ဖြေရှင်းပေးသလဲ။

Write path သည် row ၁,၀၀၀ ကို Neo4j သို့ ပို့ရမည်။ ရွေးချယ်နိုင်သည့် နည်းလမ်းများမှာ —

```text
batch_size = 1     → transaction 1000 ခု  → round-trip 1000 ကြိမ်  → နှေး
batch_size = 1000  → transaction    1 ခု  → round-trip    1 ကြိမ်  → မြန်၊ သို့သော်
                                            transaction ကြီးလွန်းလျှင် memory များ၊
                                            ပျက်လျှင် ပြန်လုပ်ရမည့် အလုပ်များ
```

ထို့ကြောင့် batch size သည် **trade-off** ဖြစ်သည်။ ဤ Exercise က latency model တစ်ခုဖြင့်
batch size ငါးမျိုးအတွက် ခန့်မှန်းချိန်ကို တွက်ပြပြီး "ဘယ်နေရာတွင် အကျိုးအမြတ် ပြန်၍
ပြားသလဲ" ကို ပြသည်။

Formula —

```text
T = (ceil(N / B) * t_tx + N * t_row) / pool_size
```

| အမည် | အဓိပ္ပာယ် | တန်ဖိုး (ဤ Exercise) |
| --- | --- | --- |
| `N` | row အရေအတွက် | `1000` |
| `B` | batch size | စမ်းသပ်မည့် တန်ဖိုး |
| `t_tx` | transaction တစ်ခုလျှင် overhead | `4.0` ms |
| `t_row` | row တစ်ခုလျှင် အလုပ် | `0.08` ms |
| `pool_size` | session pool အရေအတွက် | `4` |

ဤ code တွင် လေ့လာရမည့် Python concepts များမှာ —

- `range(start, stop, step)` နှင့် `len(range(...))`
- `min()` ဖြင့် နောက်ဆုံး batch ကို ဖြတ်ခြင်း
- List comprehension ထဲ tuple variable နှစ်ခု
- Integer နှင့် float ရောတွက်ခြင်း၊ integer division (`//`)
- `%` formatting — `%.4f`၊ `%d`၊ `%-5d`
- `assert all(...)` ဖြင့် monotonic စစ်ခြင်း

---
## 1. `chunk_rows()` — `range(start, stop, step)`
`range(0, 1000, 200)` သည် `0, 200, 400, 600, 800` ကို ထုတ်သည် — `1000` မပါပါ (`stop`
သည် exclusive)။ `len(range(...))` သည် loop မလိုဘဲ အရေအတွက်ကို ချက်ချင်း ပေးသည်။
```python
for start in range(0, 10, 3):
    print("range start :", start)
print("range(0, 10, 3) length :", len(range(0, 10, 3)))
print("range(0, 1000, 200) length :", len(range(0, 1000, 200)))
print("range(0, 7, 10) length :", len(range(0, 7, 10)))
```

Output —
```text
range start : 0
range start : 3
range start : 6
range start : 9
range(0, 10, 3) length : 4
range(0, 1000, 200) length : 5
range(0, 7, 10) length : 1
```

`range(0, 7, 10)` သည် အဖွဲ့ဝင် **၁ ခု** (`0`) သာ ထုတ်သည် — `start` သည် `stop` ထက်
ငယ်သရွေ့ အနည်းဆုံး တစ်ကြိမ် ထုတ်သည်။ ဤအခြေအနေသည် row အရေအတွက် နည်းပြီး batch size
ကြီးသည့်အခါ ဖြစ်သည် — batch တစ်ခုတည်း ဖြစ်နိုင်သည်။

### 1.1 `min()` ဖြင့် နောက်ဆုံး batch ကို ဖြတ်ခြင်း
```python
for start in [0, 3, 6, 9]:
    print("start=%-3d start+3=%-4d min=%d" % (start, start + 3, min(start + 3, 10)))
print("short batch at the end :", min(12, 10))
```

Output —
```text
start=0   start+3=3    min=3
start=3   start+3=6    min=6
start=6   start+3=9    min=9
start=9   start+3=12   min=10
short batch at the end : 10
```

နောက်ဆုံး batch သည် `start + batch_size` က `row_count` ထက် ကျော်နိုင်သည်။
`min(start + batch_size, row_count)` သည် ကျော်လျှင် `row_count` ကို ယူသည်။
`min(12, 10)` → `10`။ ဤအချက်ကြောင့် နောက်ဆုံး batch သည် အပြည့် မဖြစ်နိုင်ပါ။

### 1.2 Function တစ်ခုလုံး
```python
def chunk_rows(row_count, batch_size):
    return [(start, min(start + batch_size, row_count))
            for start in range(0, row_count, batch_size)]


def estimate_seconds(row_count, batch_size, tx_overhead_ms=4.0, row_ms=0.08,
                     pool_size=4):
    """T = (ceil(N / B) * t_tx + N * t_row) / pool_size"""
    batches = len(chunk_rows(row_count, batch_size))
    return (batches * tx_overhead_ms + row_count * row_ms) / 1000.0 / pool_size

for row_count, batch_size in [(10, 3), (1000, 200), (5, 10)]:
    print("row_count=%-5d batch_size=%-4d batches=%s"
          % (row_count, batch_size, chunk_rows(row_count, batch_size)))
```

Output —
```text
row_count=10    batch_size=3    batches=[(0, 3), (3, 6), (6, 9), (9, 10)]
row_count=1000  batch_size=200  batches=[(0, 200), (200, 400), (400, 600), (600, 800), (800, 1000)]
row_count=5     batch_size=10   batches=[(0, 5)]
```

Return သည် `(start, end)` tuple များ၏ list ဖြစ်သည်။ List comprehension ထဲက
`[(start, min(...)) for start in range(...)]` သည် tuple တစ်ခုချင်း ထုတ်သည်။
Caller က `for start, end in bounds:` လို့ ခွဲယူနိုင်သည်။

Batch များသည် row အားလုံးကို **တစ်ကြိမ်စီသာ** ဖုံးရသည် — ထပ်ခြင်း မရှိ၊ ကွက်လပ်
မရှိ။ ဤအချက်ကို အောက်တွင် စစ်ပြသည်။
```python
def chunk_rows(row_count, batch_size):
    return [(start, min(start + batch_size, row_count))
            for start in range(0, row_count, batch_size)]


def estimate_seconds(row_count, batch_size, tx_overhead_ms=4.0, row_ms=0.08,
                     pool_size=4):
    """T = (ceil(N / B) * t_tx + N * t_row) / pool_size"""
    batches = len(chunk_rows(row_count, batch_size))
    return (batches * tx_overhead_ms + row_count * row_ms) / 1000.0 / pool_size

batch_size = 3
row_count = 10
bounds = chunk_rows(row_count, batch_size)
covered = []
for start, end in bounds:
    covered.extend(range(start, end))
print("bounds      :", bounds)
print("covered     :", covered)
print("total rows  :", sum(end - start for start, end in bounds))
print("no gaps/overlaps :", covered == list(range(row_count)))
```

Output —
```text
bounds      : [(0, 3), (3, 6), (6, 9), (9, 10)]
covered     : [0, 1, 2, 3, 4, 5, 6, 7, 8, 9]
total rows  : 10
no gaps/overlaps : True
```

`covered == list(range(row_count))` စစ်ဆေးချက်က `True` ဖြစ်သည် — bound များသည်
အတိအကျ row အားလုံးကို ဖုံးပြီး ထပ်ခြင်း မရှိပါ။ ဤစစ်ဆေးချက်သည် production တွင်
**data loss ကို ကာကွယ်သည့် guard** ဖြစ်သည်: bound တွက်ချက်မှု တစ်နေရာတွင် မှားလျှင်
row တစ်ချို့ လုံးဝ မပို့ဘဲ ကျန်ခဲ့နိုင်သည်။

---
## 2. `estimate_seconds()` — Formula ကို float ဖြင့် တွက်ခြင်း
```python
batches = len(chunk_rows(row_count, batch_size))
return (batches * tx_overhead_ms + row_count * row_ms) / 1000.0 / pool_size
```

အဆင့်လိုက် —

1. `batches` — transaction အရေအတွက် (= `ceil(N / B)`)။
2. `batches * 4.0` — fixed overhead စုစုပေါင်း (ms)။
3. `row_count * 0.08` — row အလုပ် စုစုပေါင်း (ms)။ **`B` ပေါ် မမှီခိုပါ** —
   row ၁,၀၀၀ လုပ်ရမည့် အလုပ်သည် ဘယ်လို ခွဲခွဲ အတူတူ ဖြစ်သည်။
4. `/ 1000.0` — ms → second။ `1000.0` (float) သုံးခြင်းသည် **true division**
   ဖြစ်စေသည်; `1000` (int) သုံးလျှင်လည်း Python 3 တွင် `/` က true division ဖြစ်သည်။
5. `/ pool_size` — session 4 ခုက တစ်ပြိုင်နက် အလုပ်လုပ်သဖြင့် wall-clock က 4 ဖြင့် စားသည်။

အောက်တွင် batch size 200 အတွက် အဆင့်လိုက် တန်ဖိုးများကို ထုတ်ပြသည်။
```python
row_count, batch_size = 1000, 200
tx_overhead_ms, row_ms, pool_size = 4.0, 0.08, 4

batches = (row_count + batch_size - 1) // batch_size
total_ms = batches * tx_overhead_ms + row_count * row_ms
print("batches        :", batches)
print("total_ms       :", total_ms)
print("total_s        :", total_ms / 1000.0)
print("per session    :", total_ms / 1000.0 / pool_size)
print("rounded 4 dp   : %.4f" % (total_ms / 1000.0 / pool_size))
```

Output —
```text
batches        : 5
total_ms       : 100.0
total_s        : 0.1
per session    : 0.025
rounded 4 dp   : 0.0250
```

`total_ms` သည် `4.0 + 0.08` နှစ်မျိုးရောသဖြင့် float ဖြစ်သည်; print လုပ်သောအခါ
`80.0` လို `.0` ပါလာသည် (`%s` သည် float ကို မူရင်းအတိုင်း ပြသည်)။ နောက်ဆုံးလိုင်းတွင်
`%.4f` ဖြင့် 4 နေရာအထိ ဖြတ်လိုက်သည်။

`%.4f` သည် **round half to even** မဟုတ်၊ C library ၏ rounding ကို သုံးသည်;
binary float တွင် 0.084 ကဲ့သို့ တန်ဖိုးများ အတိအကျ မရှိသဖြင့် နောက်ဆုံးဂဏန်းသည်
တစ်ခါတစ်ရံ မမျှော်လင့်သည့်အတိုင်း ဖြစ်နိုင်သည်။ ထို့ကြောင့် ဤတန်ဖိုးများကို
**ခန့်မှန်းချက်** အဖြစ်သာ သုံးပြီး assert ဖြင့် အတိအကျ တန်ဖိုး မစစ်ရ —
ဤ module က `times[i] > times[i+1]` ကဲ့သို့ ဆက်စပ်မှုကိုသာ စစ်သည်။

---
## 3. `%` Formatting — Row တစ်လိုင်းအတွင်း placeholder များ
```python
print("  batch_size=%-5d transactions=%-6d est_wall=%.4fs" % (size, batches, seconds))
```

Placeholder ၃ ခုရှိပြီး argument ၃ ခု လိုသည်။ `%-5d` သည် integer ကို ဘယ်ဘက်ညှိပြီး
အနည်းဆုံး စာလုံး ၅ နေရာ ယူသည် (ညာဘက်တွင် space ဖြည့်)။ `%.4f` သည် float ကို
ဒဿမ ၄ နေရာဖြင့် ပြသည်။ Column များ တန်းညှိလာစေရန် ဤအချက်ကို သုံးသည်။
```python
value = 0.021
print("est_wall=%.4fs" % value)
print("est_wall=%fs" % value)
print("tx=%d rows=%d" % (5, 1000))

try:
    print("est_wall=%.4fs" % (value, value))
except TypeError as exc:
    print("extra arg ->", type(exc).__name__, exc)
print("est_wall=%.4fs" % value, "value=", value)
```

Output —
```text
est_wall=0.0210s
est_wall=0.021000s
tx=5 rows=1000
extra arg -> TypeError not all arguments converted during string formatting
est_wall=0.0210s value= 0.021
```

| ရေးထုံး | ရလဒ် | မှတ်ချက် |
| --- | --- | --- |
| `"%.4fs" % value` | `est_wall=0.0210s` | ဒဿမ ၄ နေရာ |
| `"%fs" % value` | `est_wall=0.021000s` | default ၆ နေရာ |
| `"%d, %d" % (5, 1000)` | `tx=5 rows=1000` | argument အရေအတွက် ကိုက်ရမည် |
| extra argument | `TypeError` | argument ပိုလျှင် error |

နောက်ဆုံးလိုင်းက အဖြစ်များသောအချက်ကို ပြသည် — label တစ်ခုတည်းကို format လုပ်ချင်
သည့်အခါ `"%.4fs" % (value, value)` လို့ **မရေးရ**။ Placeholder တစ်ခုသာ ရှိသဖြင့်
argument နှစ်ခု ပေးလျှင် `TypeError` ဖြစ်သည်။ Argument အရေအတွက်သည် placeholder
အရေအတွက်နှင့် အတိအကျ တူရသည်။ တူညီသောတန်ဖိုးကို နေရာနှစ်ခုတွင် ပြလိုလျှင်
placeholder နှစ်ခု ရေးရသည် — `print("est_wall=%.4fs (%.4f)" % (value, value))`။

---
## 4. Batch size ငါးမျိုးအတွက် ခန့်မှန်းချိန်
```python
def chunk_rows(row_count, batch_size):
    return [(start, min(start + batch_size, row_count))
            for start in range(0, row_count, batch_size)]


def estimate_seconds(row_count, batch_size, tx_overhead_ms=4.0, row_ms=0.08,
                     pool_size=4):
    """T = (ceil(N / B) * t_tx + N * t_row) / pool_size"""
    batches = len(chunk_rows(row_count, batch_size))
    return (batches * tx_overhead_ms + row_count * row_ms) / 1000.0 / pool_size

row_count = 1000
rows = []
for size in (1, 10, 50, 200, 1000):
    batches = len(chunk_rows(row_count, size))
    seconds = estimate_seconds(row_count, size)
    rows.append((size, batches, seconds))
    print("  batch_size=%-5d transactions=%-6d est_wall=%.4fs"
          % (size, batches, seconds))
print("transaction reduction at batch_size=1000: %.0fx"
      % (rows[0][1] / rows[-1][1]))
```

Output —
```text
  batch_size=1     transactions=1000   est_wall=1.0200s
  batch_size=10    transactions=100    est_wall=0.1200s
  batch_size=50    transactions=20     est_wall=0.0400s
  batch_size=200   transactions=5      est_wall=0.0250s
  batch_size=1000  transactions=1      est_wall=0.0210s
transaction reduction at batch_size=1000: 1000x
```

ရလဒ်ကို ဇယားဖြင့် (အထက်က run ၏ အမှန်တကယ် တန်ဖိုးများ) —

| batch_size | transactions | est_wall | ms |
| --- | --- | --- | --- |
| 1 | 1000 | 1.0200 s | 1020.0 ms |
| 10 | 100 | 0.1200 s | 120.0 ms |
| 50 | 20 | 0.0400 s | 40.0 ms |
| 200 | 5 | 0.0250 s | 25.0 ms |
| 1000 | 1 | 0.0210 s | 21.0 ms |

`row_count = 1000` အတွက် transaction အရေအတွက်သည် `{1000, 100, 20, 5, 1}` ဖြစ်သည် —
`N / B` နှင့် တိတိကျကျ ကိုက်ညီသည် (ဤအခြေအနေတွင် အားလုံး ခွဲညီသည်)။
`batch_size = 1` မှ `1000` သို့ ရွှေ့လျှင် round-trip သည် **1000 ဆ** လျော့သည်၊
သို့သော် ခန့်မှန်းချိန်သည် 1.0200s မှ 0.0210s သို့ — **≈ 48.6 ဆ** သာ လျော့သည်။
ဤကွာဟချက်သည် အရေးကြီးသည် — round-trip ကို 1000 ဆ လျှော့ပေမဲ့ wall-clock သည်
1000 ဆ မလျော့ပါ။ အကြောင်းရင်းကို နောက်အပိုင်းတွင် တွက်ပြသည်။

---
## 5. အကျိုးအမြတ် ပြန်၍ ပြားခြင်း — `N * t_row` term
`N * t_row` term သည် `B` ပေါ် **လုံးဝ မမှီခိုပါ**။ Row ၁,၀၀၀ လုပ်ရမည့် အလုပ်သည်
batch size ဘယ်လိုဖြစ်ဖြစ် အတူတူ ဖြစ်သည်။ ထို့ကြောင့် wall-clock တွင် အနိမ့်ဆုံး
အဆင့် (floor) တစ်ခု ရှိသည်။
```python
def chunk_rows(row_count, batch_size):
    return [(start, min(start + batch_size, row_count))
            for start in range(0, row_count, batch_size)]


def estimate_seconds(row_count, batch_size, tx_overhead_ms=4.0, row_ms=0.08,
                     pool_size=4):
    """T = (ceil(N / B) * t_tx + N * t_row) / pool_size"""
    batches = len(chunk_rows(row_count, batch_size))
    return (batches * tx_overhead_ms + row_count * row_ms) / 1000.0 / pool_size

row_count = 1000
floor = row_count * 0.08 / 1000.0 / 4
print("row term floor   : %.4fs (N * t_row / 1000 / P)" % floor)

previous = None
for size in (1, 10, 50, 200, 1000):
    batches = len(chunk_rows(row_count, size))
    seconds = estimate_seconds(row_count, size)
    gain = "-" if previous is None else "%.4f" % (previous - seconds)
    print("  batch_size=%-5d tx=%-6d est_wall=%.4fs saved_vs_prev=%s"
          % (size, batches, seconds, gain))
    previous = seconds

print("tx overhead term at B=1000 : %.4fs" % (1 * 4.0 / 1000.0 / 4))
print("floor + overhead           : %.4fs" % (floor + 1 * 4.0 / 1000.0 / 4))
```

Output —
```text
row term floor   : 0.0200s (N * t_row / 1000 / P)
  batch_size=1     tx=1000   est_wall=1.0200s saved_vs_prev=-
  batch_size=10    tx=100    est_wall=0.1200s saved_vs_prev=0.9000
  batch_size=50    tx=20     est_wall=0.0400s saved_vs_prev=0.0800
  batch_size=200   tx=5      est_wall=0.0250s saved_vs_prev=0.0150
  batch_size=1000  tx=1      est_wall=0.0210s saved_vs_prev=0.0040
tx overhead term at B=1000 : 0.0010s
floor + overhead           : 0.0210s
```

| ကြည့်ရှုချက် | တန်ဖိုး | အဓိပ္ပာယ် |
| --- | --- | --- |
| `N * t_row / 1000 / P` | `0.0200 s` | batch size မည်သို့ဖြစ်စေ လျှော့လို့မရသည့် အဆင့် |
| `B = 1000` tx overhead | `0.0010 s` | transaction တစ်ခုတည်း၏ overhead |
| floor + overhead | `0.0210 s` | `B = 1000` ၏ ခန့်မှန်းချိန် — တွက်ရလဒ်နှင့် ကိုက် |

`saved_vs_prev` ကော်လံက အကျိုးအမြတ် လျော့လာသည်ကို ပြသည် — `B = 1 → 10` တွင် ရသည့်
အကျိုးအမြတ်သည် ကြီးမားပြီး `B = 200 → 1000` တွင် အနည်းငယ်သာ ရသည်။ `B = 1000` ကျော်
လျှင် ထပ်တိုးလို့ မရတော့ပါ — floor ကို ရောက်ပြီး ဖြစ်သည်။

ဤအချက်မှ ထွက်လာသည့် လက်တွေ့စည်းကမ်း —

- `B` ကို transaction overhead နှင့် row အလုပ်အချိုး (`t_tx / t_row`) ပေါ် မူတည်ပြီး
  ရွေးရသည်; ဤ Exercise ၏ အချိုးမှာ `4.0 / 0.08 = 50` ဖြစ်သဖြင့် `B ≈ 50–200` သည်
  အကျိုးအမြတ်၏ အများစုကို ရပြီး transaction ကြီးလွန်းခြင်းကို ရှောင်နိုင်သည်။
- `pool_size` (P) သည် wall-clock ကို တိုက်ရိုက် စားသည် — P နှစ်ဆဖြစ်လျှင် wall-clock
  ထက်ဝက်။ သို့သော် session အရေအတွက် တိုးခြင်းသည် server-side resource ကို
  စားသဖြင့် အကန့်အသတ်ရှိသည်။
- Model သည် **overhead နှင့် row အလုပ်ကို ခွဲထားခြင်း**၏ တန်ဖိုးကို ပြသည်: transaction
  overhead ကို မလျှော့နိုင်တော့သည့်အခါ အခြား optimization (index၊ query plan) ကို
  ကြည့်ရမည်။

---
## 6. Code တစ်ခုလုံး — Run လုပ်နိုင်သော Version
```python
def chunk_rows(row_count, batch_size):
    return [(start, min(start + batch_size, row_count))
            for start in range(0, row_count, batch_size)]


def estimate_seconds(row_count, batch_size, tx_overhead_ms=4.0, row_ms=0.08,
                     pool_size=4):
    """T = (ceil(N / B) * t_tx + N * t_row) / pool_size"""
    batches = len(chunk_rows(row_count, batch_size))
    return (batches * tx_overhead_ms + row_count * row_ms) / 1000.0 / pool_size

row_count = 1000
rows = []
for size in (1, 10, 50, 200, 1000):
    batches = len(chunk_rows(row_count, size))
    seconds = estimate_seconds(row_count, size)
    rows.append((size, batches, seconds))
    print("  batch_size=%-5d transactions=%-6d est_wall=%.4fs"
          % (size, batches, seconds))
counts = [r[1] for r in rows]
times = [r[2] for r in rows]
print("transaction reduction at batch_size=1000: %.0fx"
      % (rows[0][1] / rows[-1][1]))
print("monotonically decreasing :",
      all(times[i] > times[i + 1] for i in range(len(times) - 1)))
```

Output —
```text
  batch_size=1     transactions=1000   est_wall=1.0200s
  batch_size=10    transactions=100    est_wall=0.1200s
  batch_size=50    transactions=20     est_wall=0.0400s
  batch_size=200   transactions=5      est_wall=0.0250s
  batch_size=1000  transactions=1      est_wall=0.0210s
transaction reduction at batch_size=1000: 1000x
monotonically decreasing : True
```

---
## 7. ကိုယ်တိုင်လေ့ကျင့်ကြည့်ပါ

**မေးခွန်း** — `chunk_rows(7, 4)` က batch မည်မျှ ပြန်မည်၊ row အားလုံး ဖုံးမဖုံး ဘယ်လို
သိနိုင်မည်နည်း။
```python
def chunk_rows(row_count, batch_size):
    return [(start, min(start + batch_size, row_count))
            for start in range(0, row_count, batch_size)]


print(chunk_rows(7, 4))
print("batches =", len(chunk_rows(7, 4)))
print("rows    =", sum(end - start for start, end in chunk_rows(7, 4)))
```

1. batch ၁ ခု — `[(0, 7)]`
2. batch ၂ ခု — `[(0, 4), (4, 7)]`
3. batch ၂ ခု — `[(0, 4), (4, 8)]`
4. batch ၃ ခု — `[(0, 4), (4, 7), (7, 7)]`

<details>
<summary>အဖြေ ကြည့်ရန်</summary>

**အဖြေ — 2. batch ၂ ခု — `[(0, 4), (4, 7)]`**

အကြောင်းရင်း — `range(0, 7, 4)` သည် `0` နှင့် `4` ကို ထုတ်သည် (`8 > 7` ဖြစ်သဖြင့်
ရပ်သည်)။ ပထမ batch က `(0, min(0 + 4, 7)) = (0, 4)`၊ ဒုတိယက `(4, min(4 + 4, 7)) = (4, 7)`။
`min()` ကြောင့် `(4, 8)` မဖြစ်ပါ — row ၇ လုံးသာ ရှိသည်။ အလွတ် batch `(7, 7)`
**မဖြစ်ပါ** — `range` က `7` ကို မထုတ်ပါ။

Row အားလုံး ဖုံးမဖုံး စစ်ရန် `sum(end - start for start, end in chunk_rows(7, 4))` က
`row_count` နှင့် တူမတူ နှိုင်းယှဉ်သည်။ အထက်က run ၏ output က `batches = 2`၊ `rows = 7` ကို
အတည်ပြုသည်။

</details>

---

**အဓိက မှတ်ထားရန်** — Wall-clock သည် `(batches · t_tx + N · t_row) / P` ဖြစ်သဖြင့်
batch size တိုးလာသည်နှင့် transaction အရေအတွက် ကျသော်လည်း `N · t_row` term သည်
ပုံသေ ကျန်သည် — ထို့ကြောင့် အကျိုးအမြတ်သည် တစ်နေရာတွင် ပြန်၍ ပြားသည်။ Batch များလွန်းလျှင်
transaction memory နှင့် failure recovery cost တိုးသည်။ Model တစ်ခုကို အသုံးပြု၍
batch size ကို **တိုင်းတာပြီး** ရွေးရသည်; round-trip အရေအတွက်ကို ကြည့်ရုံဖြင့်
wall-clock ကို ခန့်မှန်းလို့ မရပါ။
