# Walkthrough 02 — Cost / latency model (Exercise 2)

> ဤဖိုင်သည် Module 08 ၏ `solution.md` ထဲက Exercise 2 ကို **Python အခြေခံမှ စ၍**
> အပိုင်းလိုက် ရှင်းပြသည့် walkthrough ဖြစ်သည်။

---

## 0. ဤ Exercise က ဘာကို ဖြေရှင်းပေးသလဲ။

GraphRAG pipeline တစ်ခုကို production တွင် run မလုပ်မီ \"မည်မျှ ကုန်ကျမည်နည်း\" နှင့်
\"မည်မျှ ကြာမည်နည်း\" ကို **ကြိုတင် ခန့်မှန်း** နိုင်ရသည်။ Corpus အရွယ်အစားနှင့်
LLM unit price ကို သိလျှင် Cost ကို linear formula ဖြင့် တွက်နိုင်သည်။

```text
corpus (chars)
   |  / chunk_chars (ceil)
   v
chunks  ---> x (prompt_overhead + chunk_tokens) ---> input_tokens ---> x price_in  --+
   |                                                                                +--> cost_usd
   +--------> x triples_per_chunk x tokens_per_triple --> output_tokens --> x price_out -+
```

Latency ကို နှစ်ပိုင်း ခွဲသည် —

- **ingestion latency** — chunk တိုင်း LLM ကို ခေါ်ခြင်း၊ worker အရေအတွက်ဖြင့် ချုံ့နိုင်သည်
- **query latency** — graph traversal (ms scale) + generation (token အရေအတွက်ဖြင့် လွှမ်းမိုး)

ဤ Exercise တွင် လေ့လာရမည့် Python concepts —

- `import math` နှင့် `math.ceil()`
- `max(a, b)` ဖြင့် အနိမ့်ဆုံးတန်ဖိုး သတ်မှတ်ခြင်း
- ဂဏန်း အခြေခံ arithmetic နှင့် operator precedence
- Dict return နှင့် key indexing
- `**kwargs` unpacking (`**config`) နှင့် dict merge (`{**config, "k": v}`)
- `%` နှင့် f-string format specifiers (`:.4f`, `%.3f`)
- Float နှိုင်းယှဉ်မှု — `abs(x - y) < 1e-9`

---

## 1. `math.ceil()` — အပေါ်သို့ ကိန်းပြည့်ဖြစ်စေခြင်း

`math.ceil(x)` က `x` ကို **အပေါ်သို့** အနီးဆုံး ကိန်းပြည့်ဖြစ်စေသည်။

```python
import math

print(math.ceil(48000 / 2000))
print(math.ceil(1.2))
print(math.ceil(4.0))
print(math.ceil(0.1))
```

Output —

```text
24
2
4
1
```

| ထည့်သည့် တန်ဖိုး | ရလဒ် | မှတ်ချက် |
| --- | --- | --- |
| `48000 / 2000` = `24.0` | `24` | ကိန်းပြည့် ဖြစ်နေပြီ |
| `1.2` | `2` | အပေါ်သို့ တက်သည် |
| `4.0` | `4` | ပြောင်းလဲမှု မရှိ |
| `0.1` | `1` | `0` မဟုတ်ဘဲ `1` |

Chunk အရေအတွက်တွက်သည့်အခါ `ceil` က မရှိမဖြစ် လိုအပ်သည်။ စာသား ၄၅၀၀ လုံးကို
chunk ၂၀၀၀ လုံးစီ ခွဲလျှင် `2.25` ရသည် — သို့သော် chunk အရေအတွက်က
**ကိန်းပြည့်** ဖြစ်ရန် လိုအပ်သောကြောင့် `3` ဟု တွက်ရသည်။ `round()` က အနီးဆုံးကို ယူသောကြောင့်
ဤနေရာတွင် **မသုံးရ** ပါ။

---

## 2. `max(1, ...)` — အလွတ် Corpus ကာကွယ်ခြင်း

```python
import math

print(max(1, math.ceil(4000 / 2000)))
print(max(1, math.ceil(500 / 2000)))
print(max(1, math.ceil(0 / 2000)))
```

Output —

```text
2
1
1
```

`max(1, ...)` က ရလဒ်ကို **အနည်းဆုံး ၁** ဖြစ်စေသည်။ Corpus အလွတ်ဖြစ်လျှင်
`ceil(0 / 2000)` က `0` ရပြီး chunk သုည ဖြစ်သောကြောင့် နောက်ပိုင်း `chunks / workers`
တွက်သည့်အခါ သုညနှင့် စားခြင်းကို ရှောင်၍ ရသည်။ `max(a, b)` က တန်ဖိုးနှစ်ခုထဲက
**ကြီးသောတန်ဖိုး**ကို ပြန်သည်။

```python
print(max(3, 8))
print(max(8, 3))
print(max(-1, 1))
```

Output —

```text
8
8
1
```

---

## 3. `chunk_tokens` — chunk တစ်ခု၏ token ခန့်မှန်း

`CHARS_PER_TOKEN = 4.0` က **character ၄ လုံးလျှင် token ၁ လုံး** ဟု ယူဆသော
rule of thumb ပါ။ ၎င်းသည် course example ဖြစ်သည် — tokenizer တစ်ခုချင်းစီ အလိုက်
အချိုးပြောင်းနိုင်သည်။

```python
import math

CHARS_PER_TOKEN = 4.0
print(math.ceil(2000 / CHARS_PER_TOKEN))
print(math.ceil(1950 / CHARS_PER_TOKEN))
```

Output —

```text
500
488
```

chunk ၂၀၀၀ လုံး၏ token ခန့်မှန်းက `500` ဖြစ်သည်။ `1950 / 4.0 = 487.5` ကို
`ceil` လိုက်သဖြင့် `488` ရသည်။

---

## 4. Token စုစုပေါင်း တွက်ခြင်း

```python
chunks = 24
prompt_overhead_tokens = 300
chunk_tokens = 500
triples_per_chunk = 8
tokens_per_triple = 30

input_tokens = chunks * (prompt_overhead_tokens + chunk_tokens)
output_tokens = chunks * triples_per_chunk * tokens_per_triple
print(input_tokens)
print(output_tokens)
```

Output —

```text
19200
5760
```

**Input tokens** — chunk တိုင်းအတွက် prompt အညွှန်း (`300`) နှင့် chunk ကိုယ်တိုင်
(`500`) ကို ပေါင်းပြီး chunk အရေအတွက်နှင့် မြှောက်သည် —

- `300 + 500 = 800`
- `800 * 24 = 19200`

**Output tokens** — chunk တိုင်းမှ triple `8` ခု ထုတ်ပြီး၊ triple တိုင်းက token `30`
ကုန်သည် —

- `8 * 30 = 240` (chunk တစ်ခုလျှင် output token)
- `240 * 24 = 5760`

`chunks * triples_per_chunk * tokens_per_triple` တွင် `*` က **ဘယ်မှ ညာ** အလုပ်လုပ်သဖြင့်
`(chunks * triples_per_chunk) * tokens_per_triple` ဖြစ်သည်။ `240 * 24` လို ရလဒ်တူသည်။

---

## 5. `cost_usd` — Term တိုင်းကို ခွဲပြခြင်း

Cost က input term နှင့် output term နှစ်ခု ပေါင်းခြင်းပါ။ Term တိုင်းကို
**သီးခြား** တွက်ပြပါမည်။

```python
input_tokens = 19200
output_tokens = 5760
price_in_per_1k = 0.5
price_out_per_1k = 1.5

in_term = (input_tokens / 1000.0) * price_in_per_1k
out_term = (output_tokens / 1000.0) * price_out_per_1k
print("%.4f" % in_term)
print("%.4f" % out_term)
print("%.6f" % (in_term + out_term))
print("%.4f" % (in_term + out_term))
```

Output —

```text
9.6000
8.6400
18.240000
18.2400
```

| Term | တွက်ပုံ | တန်ဖိုး |
| --- | --- | --- |
| input term | `(19200 / 1000) * 0.5` = `19.2 * 0.5` | `9.6000` |
| output term | `(5760 / 1000) * 1.5` = `5.76 * 1.5` | `8.6400` |
| **cost_usd** | `9.6 + 8.64` | `18.2400` |

`/1000.0` က token ကို \"per 1k token\" unit ဖြစ်စေသည် — price များက **1k token
လျှင်** သတ်မှတ်ထားသောကြောင့် ဖြစ်သည်။

### Float သည် အတိအကျ မဟုတ်ပါ

`18.24` ကို `repr()` နှင့် ကြည့်လျှင် အတိအကျ မဟုတ်ခြင်းကို တွေ့ရသည်။

```python
print(repr((19200 / 1000.0) * 0.5 + (5760 / 1000.0) * 1.5))
print("%.4f" % ((19200 / 1000.0) * 0.5 + (5760 / 1000.0) * 1.5))
```

Output —

```text
18.240000000000002
18.2400
```

Float က binary ဖြင့် သိမ်းသဖြင့် ဒသမ တန်ဖိုးတိုင်းကို အတိအကျ မဖော်နိုင်ပါ။
ထို့ကြောင့် output တွင် format specifier (`%.4f`) နှင့် **ပြသသည်**။ နှိုင်းယှဉ်သည့်အခါလည်း
`==` မသုံးဘဲ tolerance နှင့် စစ်သည် (အောက် Section 9 တွင် ကြည့်ပါ)။

---

## 6. `per_chunk_seconds` — Chunk တစ်ခု၏ Latency

```python
base_latency_s = 0.15
tokens_per_second = 120.0

print("%.6f" % ((300 + 500 + 240) / tokens_per_second))
print("%.3f" % (base_latency_s + (300 + 500 + 240) / tokens_per_second))
```

Output —

```text
8.666667
8.817
```

Chunk တစ်ခုအတွက် —

- **network/base overhead** — `0.15` s
- **token ပမာ** — input `300 + 500 = 800`၊ output `240`၊ စုစုပေါင်း `1040`
- **streaming time** — `1040 / 120.0 = 8.666667` s
- **ပေါင်း** — `0.15 + 8.666667 = 8.816667` → `%.3f` ဖြင့် `8.817`

`base_latency_s` က connection setup၊ prompt processing ကဲ့သို့ token အရေအတွက်နှင့်
မတိုက်ရိုက်ဆိုင်သော အချိန် ဖြစ်သည်။

---

## 7. Sequential နှင့် Parallel Latency

```python
import math

chunks = 24
per_chunk_seconds = 8.816666666666666
print("%.3f" % (chunks * per_chunk_seconds))
print(math.ceil(chunks / 4))
print("%.3f" % (math.ceil(chunks / 4) * per_chunk_seconds))
print("%.3f" % (math.ceil(chunks / 8) * per_chunk_seconds))
```

Output —

```text
211.600
6
52.900
26.450
```

| နည်းလမ်း | Formula | ရလဒ် |
| --- | --- | --- |
| sequential | `24 * 8.8166` | `211.600` s |
| parallel (4 workers) | `ceil(24/4) * 8.8166` = `6 * 8.8166` | `52.900` s |
| parallel (8 workers) | `ceil(24/8) * 8.8166` = `3 * 8.8166` | `26.450` s |

Parallel တွက်သည့်အခါ `math.ceil(chunks / workers)` က **လှိုင်း (wave) အရေအတွက်**ကို
ပေးသည်။ chunk ၂၄ ခုကို worker ၄ ဦး ခွဲလျှင် လှိုင်း ၆ ခု ရသည်။ Worker နှစ်ဆ
တိုးလိုက်လျှင် latency က ထက်ဝက် ကျသည် — ဤအချက်ကို Exercise တွင် `assert`
ဖြင့် စစ်သည်။

```python
print(52.9 / 2)
print(abs(26.45 - 52.9 / 2) < 1e-9)
```

Output —

```text
26.45
True
```

---

## 8. `cost_latency_model()` — Function အပြည့်အစုံ

```python
import math

CHARS_PER_TOKEN = 4.0


def cost_latency_model(corpus_chars, chunk_chars, prompt_overhead_tokens,
                       tokens_per_triple, triples_per_chunk,
                       price_in_per_1k, price_out_per_1k,
                       base_latency_s, tokens_per_second, workers):
    chunks = max(1, math.ceil(corpus_chars / chunk_chars))
    chunk_tokens = math.ceil(chunk_chars / CHARS_PER_TOKEN)
    input_tokens = chunks * (prompt_overhead_tokens + chunk_tokens)
    output_tokens = chunks * triples_per_chunk * tokens_per_triple
    cost_usd = (input_tokens / 1000.0) * price_in_per_1k + (output_tokens / 1000.0) * price_out_per_1k
    per_chunk_seconds = base_latency_s + (
        prompt_overhead_tokens + chunk_tokens + triples_per_chunk * tokens_per_triple
    ) / tokens_per_second
    sequential_latency_s = chunks * per_chunk_seconds
    parallel_latency_s = math.ceil(chunks / workers) * per_chunk_seconds
    return {
        "chunks": chunks,
        "input_tokens": input_tokens,
        "output_tokens": output_tokens,
        "cost_usd": cost_usd,
        "per_chunk_seconds": per_chunk_seconds,
        "sequential_latency_s": sequential_latency_s,
        "parallel_latency_s": parallel_latency_s,
    }
```

Function က **parameter ၁၀ လုံး** လက်ခံပြီး dict တစ်ခု ပြန်သည်။ Dict ပြန်ခြင်းသည်
field များကို key ဖြင့် ဖတ်နိုင်သောကြောင့် ဖြစ်သည် — positional tuple ပြန်လျှင် ဖတ်ရ ခက်သည်။

Return dict ထဲက key တိုင်းကို —

| Key | အဓိပ္ပာယ် |
| --- | --- |
| `chunks` | chunk အရေအတွက် |
| `input_tokens` | prompt + chunk token စုစုပေါင်း |
| `output_tokens` | triple token စုစုပေါင်း |
| `cost_usd` | USD ဖြင့် Cost |
| `per_chunk_seconds` | chunk တစ်ခု latency |
| `sequential_latency_s` | worker ၁ ဦးဆို စုစုပေါင်း |
| `parallel_latency_s` | လက်ရှိ worker ဖြင့် |

### `**config` — Dict ကို Keyword Argument အဖြစ် ဖြန့်ခြင်း

```python
import math

CHARS_PER_TOKEN = 4.0


def cost_latency_model(corpus_chars, chunk_chars, prompt_overhead_tokens,
                       tokens_per_triple, triples_per_chunk,
                       price_in_per_1k, price_out_per_1k,
                       base_latency_s, tokens_per_second, workers):
    chunks = max(1, math.ceil(corpus_chars / chunk_chars))
    chunk_tokens = math.ceil(chunk_chars / CHARS_PER_TOKEN)
    input_tokens = chunks * (prompt_overhead_tokens + chunk_tokens)
    output_tokens = chunks * triples_per_chunk * tokens_per_triple
    cost_usd = (input_tokens / 1000.0) * price_in_per_1k + (output_tokens / 1000.0) * price_out_per_1k
    per_chunk_seconds = base_latency_s + (
        prompt_overhead_tokens + chunk_tokens + triples_per_chunk * tokens_per_triple
    ) / tokens_per_second
    return {
        "chunks": chunks,
        "input_tokens": input_tokens,
        "output_tokens": output_tokens,
        "cost_usd": cost_usd,
        "per_chunk_seconds": per_chunk_seconds,
        "sequential_latency_s": chunks * per_chunk_seconds,
        "parallel_latency_s": math.ceil(chunks / workers) * per_chunk_seconds,
    }


config = dict(corpus_chars=48000, chunk_chars=2000, prompt_overhead_tokens=300,
              tokens_per_triple=30, triples_per_chunk=8,
              price_in_per_1k=0.5, price_out_per_1k=1.5,
              base_latency_s=0.15, tokens_per_second=120.0, workers=4)
base = cost_latency_model(**config)
print(base["chunks"])
print(base["input_tokens"])
print(base["output_tokens"])
print("%.4f" % base["cost_usd"])
```

Output —

```text
24
19200
5760
18.2400
```

`cost_latency_model(**config)` တွင် `**config` က dict ထဲက key-value တိုင်းကို
`key=value` keyword argument အဖြစ် ဖြန့်ပေးသည်။ `config["corpus_chars"] = 48000`
ဖြစ်သောကြောင့် `corpus_chars=48000` ဟု ခေါ်ခြင်းနှင့် အတူတူ ဖြစ်သည်။

```python
def show(a, b):
    print(a, b)

params = {"a": 1, "b": 2}
show(**params)
```

Output —

```text
1 2
```

### Dict merge ဖြင့် တန်ဖိုးတစ်ခုသာ ပြောင်းခြင်း

```python
config = {"corpus_chars": 48000, "workers": 4}
wider = {**config, "workers": 8}
print(wider)
print(config)
```

Output —

```text
{'corpus_chars': 48000, 'workers': 8}
{'corpus_chars': 48000, 'workers': 4}
```

`{**config, "workers": 8}` က `config` ကို **copy** ပြီး `workers` ကို `8` ဖြင့်
အစားထိုးသည်။ `config` ကိုယ်တိုင် မပြောင်းပါ — ၎င်းသည် **immutability** ကို ထိန်းသည်။

---

## 9. `retrieval_latency_ms()` — Query-side Latency

```python
def retrieval_latency_ms(nodes_scanned, edges_scanned, generation_tokens,
                         generation_tokens_per_second):
    traversal_ms = 4.0 + nodes_scanned * 0.05 + edges_scanned * 0.02
    generation_ms = generation_tokens / generation_tokens_per_second * 1000.0
    return traversal_ms, generation_ms, traversal_ms + generation_ms


traversal_ms, generation_ms, total_ms = retrieval_latency_ms(6, 5, 80, 40.0)
print("%.2f" % traversal_ms)
print("%.2f" % generation_ms)
print("%.2f" % total_ms)
```

Output —

```text
4.40
2000.00
2004.40
```

Return က **tuple သုံးလုံး** — `(traversal_ms, generation_ms, total_ms)`။ Caller က
`traversal_ms, generation_ms, total_ms = ...` ဟူ၍ tuple unpacking ဖြင့် ခွဲယူသည်။

| အပိုင်း | တွက်ပုံ | ရလဒ် |
| --- | --- | --- |
| traversal | `4.0 + 6*0.05 + 5*0.02` = `4.0 + 0.3 + 0.1` | `4.40` ms |
| generation | `80 / 40.0 * 1000` | `2000.00` ms |
| total | `4.4 + 2000.0` | `2004.40` ms |

`4.0` က fixed base၊ node တိုင်း `0.05` ms၊ edge တိုင်း `0.02` ms — ဤတန်ဖိုးများက
course example ဖြစ်သည်။ **Traversal က millisecond အနည်းငယ်သာ ကုန်ပြီး
generation က second နှစ်ခု ကုန်သည်** — ၎င်းသည် အဓိက ရလဒ်ပါ။ Query latency ကို
လျှော့ချင်လျှင် context ကို ချုံ့ခြင်း (generation token လျှော့ခြင်း) က အကျိုးအမြတ်
အများဆုံး ဖြစ်သည်။

---

## 10. Float နှိုင်းယှဉ်မှု — `abs(x - y) < 1e-9`

```python
print(0.1 + 0.2 == 0.3)
print(abs((0.1 + 0.2) - 0.3) < 1e-9)
print(repr(0.1 + 0.2))
```

Output —

```text
False
True
0.30000000000000004
```

`0.1 + 0.2` က `0.3` နှင့် **တိတိကျကျ မညီ** ပါ။ ထို့ကြောင့် code ထဲတွင် —

```python
assert abs(sum(weights.values()) - 1.0) < 1e-9
```

ဟု ရေးခြင်းသည် `==` မသုံးဘဲ **tolerance** (`1e-9` = `0.000000001`) ဖြင့် စစ်ဆေးခြင်း ဖြစ်သည်။ Exercise 2
တွင်လည်း —

```python
bigger = {"cost_usd": 36.480000000000004}
base = {"cost_usd": 18.240000000000002}
print(abs(bigger["cost_usd"] - 2 * base["cost_usd"]) < 1e-9)
```

Output —

```text
True
```

Cost နှစ်ဆ ဖြစ်ကြောင်း float noise ရှိသော်လည်း tolerance ဖြင့် စစ်နိုင်သည်။

---

## 11. Code တစ်ခုလုံး — Run လုပ်နိုင်သော Version

```python
import math

CHARS_PER_TOKEN = 4.0


def cost_latency_model(corpus_chars, chunk_chars, prompt_overhead_tokens,
                       tokens_per_triple, triples_per_chunk,
                       price_in_per_1k, price_out_per_1k,
                       base_latency_s, tokens_per_second, workers):
    chunks = max(1, math.ceil(corpus_chars / chunk_chars))
    chunk_tokens = math.ceil(chunk_chars / CHARS_PER_TOKEN)
    input_tokens = chunks * (prompt_overhead_tokens + chunk_tokens)
    output_tokens = chunks * triples_per_chunk * tokens_per_triple
    cost_usd = (input_tokens / 1000.0) * price_in_per_1k + (output_tokens / 1000.0) * price_out_per_1k
    per_chunk_seconds = base_latency_s + (
        prompt_overhead_tokens + chunk_tokens + triples_per_chunk * tokens_per_triple
    ) / tokens_per_second
    return {
        "chunks": chunks,
        "input_tokens": input_tokens,
        "output_tokens": output_tokens,
        "cost_usd": cost_usd,
        "per_chunk_seconds": per_chunk_seconds,
        "sequential_latency_s": chunks * per_chunk_seconds,
        "parallel_latency_s": math.ceil(chunks / workers) * per_chunk_seconds,
    }


def retrieval_latency_ms(nodes_scanned, edges_scanned, generation_tokens,
                         generation_tokens_per_second):
    traversal_ms = 4.0 + nodes_scanned * 0.05 + edges_scanned * 0.02
    generation_ms = generation_tokens / generation_tokens_per_second * 1000.0
    return traversal_ms, generation_ms, traversal_ms + generation_ms


config = dict(corpus_chars=48000, chunk_chars=2000, prompt_overhead_tokens=300,
              tokens_per_triple=30, triples_per_chunk=8,
              price_in_per_1k=0.5, price_out_per_1k=1.5,
              base_latency_s=0.15, tokens_per_second=120.0, workers=4)
base = cost_latency_model(**config)
print(f"corpus={config['corpus_chars']} chars -> chunks={base['chunks']}")
print(f"  input tokens  = {base['input_tokens']}")
print(f"  output tokens = {base['output_tokens']}")
print(f"  ingestion cost = ${base['cost_usd']:.4f}")
print(f"  per-chunk latency = {base['per_chunk_seconds']:.3f} s")
print(f"  sequential latency = {base['sequential_latency_s']:.3f} s")
print(f"  parallel latency   = {base['parallel_latency_s']:.3f} s")

bigger = cost_latency_model(**{**config, "corpus_chars": config["corpus_chars"] * 2})
print("  corpus x2 -> chunks=%d cost=$%.4f (doubled=%s)"
      % (bigger["chunks"], bigger["cost_usd"],
         abs(bigger["cost_usd"] - 2 * base["cost_usd"]) < 1e-9))
wider = cost_latency_model(**{**config, "workers": 8})
print("  workers 4 -> 8: parallel %.3f s -> %.3f s"
      % (base["parallel_latency_s"], wider["parallel_latency_s"]))

traversal_ms, generation_ms, total_ms = retrieval_latency_ms(6, 5, 80, 40.0)
print(f"  query traversal = {traversal_ms:.2f} ms, generation = {generation_ms:.2f} ms")
print(f"  query total     = {total_ms:.2f} ms")
```

Output —

```text
corpus=48000 chars -> chunks=24
  input tokens  = 19200
  output tokens = 5760
  ingestion cost = $18.2400
  per-chunk latency = 8.817 s
  sequential latency = 211.600 s
  parallel latency   = 52.900 s
  corpus x2 -> chunks=48 cost=$36.4800 (doubled=True)
  workers 4 -> 8: parallel 52.900 s -> 26.450 s
  query traversal = 4.40 ms, generation = 2000.00 ms
  query total     = 2004.40 ms
```

---

## 12. Rerun တစ်ခုတွင် ရလဒ် ကွာနိုင်သည့် အချက် — မရှိပါ

ဤ Exercise ၏ output အားလုံးသည် **deterministic** ဖြစ်သည် — `random` မသုံးဘဲ
formula သာ သုံးသဖြင့် rerun တိုင်း ထပ်တူ ရသည်။ သတိထားရမည့် အချက်က float
noise ကို **format specifier ဖြင့် ဖုံးထား** ရခြင်းပါ။ `%.4f` မပါဘဲ `print(base["cost_usd"])`
ဟု ရေးလျှင် `18.240000000000002` လို ရှည်လျားသော output ကို တွေ့ရပါမည်။

---

## 13. ရလဒ်ကို ပြန်ကြည့်ခြင်း

| စစ်ဆေးချက် | Code | ရလဒ် |
| --- | --- | --- |
| Corpus နှစ်ဆ → Cost နှစ်ဆ | `abs(bigger - 2*base) < 1e-9` | `True` |
| Corpus နှစ်ဆ → chunks နှစ်ဆ | `bigger["chunks"] == 48` | `True` |
| Worker ၄ → ၈ → parallel ထက်ဝက် | `26.45 == 52.9 / 2` | `True` |
| Parallel < Sequential | `52.9 < 211.6` | `True` |
| Query total < ingestion | `2004.4 < 211600` | `True` |
| Query ကို generation လွှမ်း | `2000.0 > 4.4` | `True` |

ဤဇယားက **ဘယ် optimization က တန်ဖိုးရှိသည်** ဆိုသည်ကို ပြသည်။ Traversal ကို
optimize လုပ်လျှင် millisecond အနည်းငယ်သာ ရပြီး၊ generation token (context size) ကို
ချုံ့လျှင် second အများအပြား ရနိုင်သည်။ Cost မှာ corpus size နှင့် linear ဆက်စပ်သဖြင့်
**ကြိုတင် ခန့်မှန်းနိုင်သည်**။

---

## 14. ကိုယ်တိုင်လေ့ကျင့်ကြည့်ပါ

**မေးခွန်း** — အောက်ပါ code က ဘယ်ရလဒ် ပြန်ပေးမလဲ။

```python
import math

chunks = 24
per_chunk_seconds = 10.0
workers = 5
print(math.ceil(chunks / workers) * per_chunk_seconds)
```

1. `40.0` — `ceil(24/5) = 5`၊ `5 * 10`
2. `48.0` — `24 * 10 / 5`
3. `50.0` — `ceil(24/5) = 5` မဟုတ်ဘဲ round-up
4. `240.0` — sequential latency

<details>
<summary>အဖြေ ကြည့်ရန်</summary>

**အဖြေ — 3. `50.0`**

အကြောင်းရင်း — `24 / 5 = 4.8` ဖြစ်သည်။ `math.ceil(4.8) = 5` ရသည် (အပေါ်သို့
ကိန်းပြည့်)။ ထို့ကြောင့် `5 * 10.0 = 50.0` ဖြစ်သည်။

ရွေးချယ်စရာ ၁ ၏ `ceil(24/5) = 5` မှာ မှန်သည်၊ သို့သော် ရလဒ်ကို `40.0`
ဟု ရေးထားခြင်းမှာ မှားသည် — `5 * 10 = 50` ဖြစ်သည်။ ရွေးချယ်စရာ ၂ က
`ceil` ကို လုံးလုံး မသုံးဘဲ float ဖြင့် စားသဖြင့် မှားသည် — latency ကို
လှိုင်း (wave) အရေအတွက်ဖြင့် တွက်ရသည်၊ chunk တိုင်း တစ်ပြိုင်နက် ပြီးမည် မဟုတ်ပါ။

</details>

---

**အဓိက မှတ်ထားရန်** — Cost သည် corpus size နှင့် linear ဖြစ်၍ ခန့်မှန်းနိုင်သည်၊
သို့သော် query latency ကို generation token အရေအတွက်ဖြင့် ထိန်းရမည်။ Traversal
ကို optimize လုပ်ရန် ကြိုးစားခြင်းသည် millisecond အနည်းငယ် ရရှိပြီး၊ context ကို
ချုံ့ခြင်းက second များစွာ ရရှိသည်။ Formula ထဲက price နှင့် latency coefficient များက
course example ဖြစ်သည် — production တွင် သင့် provider ၏ တကယ့် rate ဖြင့်
အစားထိုးရမည်။
