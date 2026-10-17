# Walkthrough 06 — Idempotent batch runner (Exercise 6)

> ဤဖိုင်သည် Module 03 ၏ `solution.md` ထဲက Exercise 6 ကို **Python အခြေခံမှ စ၍**
> အပိုင်းလိုက် ရှင်းပြသည့် walkthrough ဖြစ်သည်။

---

## 0. ဤ Exercise က ဘာကို ဖြေရှင်းပေးသလဲ။

Chunk ရာနှင့်ချီရှိသော pipeline သည် တစ်ကြိမ်တည်း run လျှင် မကြာခဏ ကျရှုံးမည် (network၊ LLM rate
limit၊ worker crash)။ ထို့ကြောင့် chunk များကို **batch** အဖြစ် စု၍ တစ်ခုချင်း commit လုပ်ရမည်။

ဤ Exercise ၏ သုံးလုံးသော requirement မှာ —

```text
1. Batching     — chunk များကို batch_size=2 ဖြင့် စုသည် (batch ၄ ခု)
2. Retry        — transient failure ဖြစ်လျှင် backoff ဖြင့် ပြန် run သည်
3. Idempotency  — run ပြန်လျှင် committed batch များ skip ဖြစ်ပြီး graph မပြောင်းလဲ
                  (duplicate triple များ မဖြစ်ပေါ်)
```

```text
  chunks (8) -> batches (4) -> [ batch_0 | batch_1 | batch_2 | batch_3 ]
                                   |          |          |          |
                              checkpoint  checkpoint  retry->done  checkpoint
                                   \__________  graph (triple_key -> record)  _________/
                                                  |
                                      run 2: committed batch အားလုံး skip
```

သော့ချက်မှာ **checkpoint ကို write ပြီးမှသာ သတ်မှတ်ခြင်း** ဖြစ်သည်။ early mark လုပ်လျှင်
ကျရှုံးသော batch သည် "committed" ဖြစ်သွားပြီး နောက် run တွင် skip ခံရသဖြင့် data ဆုံးရှုံးမည်။

ဤ code မှာ လေ့လာရမည့် Python concepts များမှာ —

- `class`၊ `__init__()` နှင့် `self`
- Modulo arithmetic ဖြင့် deterministic pseudo-random (`LCG`)
- `range(start, stop, step)` ဖြင့် slice ခွဲခြင်း
- Set of tuples ဖြင့် scripted failure
- `while` loop အတွင်း attempt counter
- `while ... else` နှင့် `break`
- `continue`
- Dict comprehension ဖြင့် snapshot
- `dict.setdefault()` ဖြင့် MERGE semantics

---

## 1. Chunk များကို Batch ခွဲခြင်း

```python
chunks = [[i] for i in range(8)]
batch_size = 2
batches = [chunks[i:i + batch_size] for i in range(0, len(chunks), batch_size)]
print("chunk count :", len(chunks))
print("batch count :", len(batches))
for i, b in enumerate(batches):
    print("  batch_%d -> %s" % (i, b))
```

Output —

```text
chunk count : 8
batch count : 4
  batch_0 -> [[0], [1]]
  batch_1 -> [[2], [3]]
  batch_2 -> [[4], [5]]
  batch_3 -> [[6], [7]]
```

`range(0, len(chunks), batch_size)` သည် `0, 2, 4, 6` ကို ပေးသည် (start၊ stop၊ **step**)။ List
comprehension က `chunks[i:i+2]` ဖြင့် batch တိုင်းကို ဖန်တီးသည်။ `[[i] for i in range(8)]` သည်
chunk တိုင်းကို token တစ်လုံးစီပါသော list အဖြစ် သရုပ်ပြရန် ဖြစ်သည် — အမှန်တွင် chunk
တိုင်း token ၅ လုံးပါသည်။

---

## 2. `class LCG` — Deterministic Pseudo-random

`random` ကို မသုံးရ (WRITING_RULES) ဖြစ်သဖြင့် backoff jitter ကို fixed-seed **LCG** (Linear
Congruential Generator) ဖြင့် ထုတ်သည်။

```python
class LCG:
    def __init__(self, seed=20261017):
        self.state = seed

    def next(self):
        self.state = (1103515245 * self.state + 12345) % (2 ** 31)
        return self.state

    def below(self, n):
        return self.next() % n


rng = LCG()
print("state after 1st next :", rng.next())
print("state after 2nd next :", rng.next())
rng2 = LCG()
print("below(4) x4          :", [rng2.below(4) for _ in range(4)])
rng3 = LCG()
print("backoff candidates   :", [round(0.5 + rng3.below(4) * 0.25, 2) for _ in range(4)])
```

Output —

```text
state after 1st next : 1968641886
state after 2nd next : 1877460799
below(4) x4          : [2, 3, 0, 1]
backoff candidates   : [1.0, 1.25, 0.5, 0.75]
```

### `class` နှင့် `self`

- `class LCG:` သည် object ဖန်တီးရန် အစီအစဉ် (blueprint) ဖြစ်သည်။ `LCG()` ဖြင့် instance ဖန်တီးသည်။
- `__init__(self, seed=...)` သည် constructor ဖြစ်သည် — instance ဖန်တီးသည့်အခါ အလိုအလျောက် run သည်။
- `self` သည် **ထို instance ကိုယ်တိုင်** ကို ညွှန်သည်။ `self.state = seed` သည် instance ထဲတွင်
  `state` အမည်ဖြင့် တန်ဖိုးတစ်ခု သိမ်းသည် (instance attribute)။
- `next()` သည် တန်ဖိုးအသစ် တွက်ပြီး `self.state` ကို **ပြောင်းလဲ** သည်။ ဒါကြောင့် အကြိမ်တိုင်း
  ခေါ်လျှင် တန်ဖိုးအသစ် ရသည် (1968641886 ပြီးရင် 1877460799)။
- `below(n)` သည် `next()` ၏ ရလဒ်ကို `n` ဖြင့် စားကြွင်းယူသဖြင့် `0` မှ `n-1` အထိ ရသည်။

LCG သည် **deterministic** ဖြစ်သည် — seed တူညီလျှင် run တိုင်း တန်ဖိုးစဉ် တူညီသည်။ `[2, 3, 0, 1]`
ဆိုသည့် အစဉ်သည် run တိုင်း တူညီသည်။ ဤအချက်ကြောင့် `random` မလိုဘဲ jitter ရနိုင်သည်
(မေးခွန်းကို ထပ်မံ စမ်းသပ်နိုင်ရန် deterministic ဖြစ်ရမည်)။ Backoff သည်
`0.5 + below(4) * 0.25` ဖြစ်သဖြင့် `0.5, 0.75, 1.0, 1.25` အနက် တစ်ခု ဖြစ်သည်။

---

## 3. `fail_plan` — Scripted Failure

```python
fail_plan = {("batch_2", 1)}
print("('batch_2', 1) in fail_plan :", ("batch_2", 1) in fail_plan)
print("('batch_2', 2) in fail_plan :", ("batch_2", 2) in fail_plan)
print("type:", type(fail_plan))
print("element:", sorted(fail_plan))
```

Output —

```text
('batch_2', 1) in fail_plan : True
('batch_2', 2) in fail_plan : False
type: <class 'set'>
element: [('batch_2', 1)]
```

`fail_plan` သည် `(batch_id, attempt)` **tuple** များပါသော **set** ဖြစ်သည်။ `("batch_2", 1)`
ဆိုသည်မှာ "batch_2 ၏ ပထမ attempt ကျရှုံးစေ" ဟု ဆိုလိုသည်။ Test တွင် failure ကို **ကြိုတင်
ရေးထား** (scripted) သဖြင့် ဤဖိုင်သည် offline နှင့် deterministic ဖြစ်သည်။

`in` သည် set အတွင်း tuple ပါမပါ စစ်သည် — ဤစစ်ဆေးမှုသည် retry loop ၏ အူတိုင်ဖြစ်သည်။

---

## 4. `run_batches()` — Signature နှင့် Batch Loop

```python
def run_batches(chunks, fail_plan, checkpoint, graph, batch_size=2,
                max_attempts=3, seed=20261017):
    rng = LCG(seed)
    log = []
    batches = [chunks[i:i + batch_size] for i in range(0, len(chunks), batch_size)]
    for b_idx, batch in enumerate(batches):
        bid = "batch_%d" % b_idx
        if bid in checkpoint:
            log.append((bid, "skip", 0))
            continue
        ...
```

| Argument | အဓိပ္ပာယ် |
| --- | --- |
| `chunks` | chunk များ (token list တိုင်း) |
| `fail_plan` | `(bid, attempt)` ကျရှုံးစေမည့် set |
| `checkpoint` | `bid -> True` — committed batch များ (mutable dict) |
| `graph` | `triple_key -> record` — ရည်မှန်း output store |
| `batch_size` | batch တိုင်း chunk အရေအတွက် (default 2) |
| `max_attempts` | batch တိုင်း အများဆုံး ကြိုးစားအကြိမ် (default 3) |
| `seed` | LCG seed |

`rng = LCG(seed)` သည် run တိုင်း အသစ်ဖန်တီးသဖြင့် ရလဒ်သည် deterministic ဖြစ်သည်။
`checkpoint` နှင့် `graph` ကို **argument အဖြစ်** လက်ခံသဖြင့် caller က run နှစ်ခုကြား ထို
state ကို ထိန်းထားနိုင်သည် (mutable dict များဖြစ်သဖြင့် ပြောင်းလဲမှုသည် ပြင်ပတွင် မြင်ရသည်)။

### Checkpoint Skip

```python
if bid in checkpoint:
    log.append((bid, "skip", 0))
    continue
```

`bid` သည် ရှိပြီးသား committed batch ဖြစ်လျှင် လုပ်ဆောင်ခြင်း မရှိဘဲ **skip** ဟု log တင်ပြီး
`continue` ဖြင့် နောက် batch သို့ ဆက်သည်။ ဤလိုင်းနှစ်လိုင်းသည် **Idempotency** ကို
ဖန်တီးပေးသည် — run ပြန်လျှင် commit ပြီးသား batch များသည် ထပ်မံ write မလုပ်တော့ပါ။

---

## 5. Retry Loop — `while` နှင့် `fail_plan`

```python
attempt = 0
while attempt < max_attempts:
    attempt += 1
    if (bid, attempt) in fail_plan:
        log.append((bid, "retry", round(0.5 + rng.below(4) * 0.25, 2)))
        continue
    ...
    checkpoint[bid] = True
    log.append((bid, "done", attempt))
    break
else:
    log.append((bid, "failed", attempt))
```

| အစဉ် | လုပ်ငန်း |
| --- | --- |
| 1 | `attempt` ကို ၀ မှ စ |
| 2 | `attempt += 1` — ဤကြိုးစားမှုကို ရေတွက် |
| 3 | `(bid, attempt)` သည် `fail_plan` ထဲ ပါလျှင် `retry` log တင်ပြီး `continue` (write မလုပ်) |
| 4 | `fail_plan` မပါလျှင် write လုပ်ပြီး `checkpoint[bid] = True` |
| 5 | `break` — ဤ batch ပြီးဆုံး |
| 6 | `while` က `max_attempts` အထိ ပြည့်သွားလျှင် `else` လုပ်ဆောင်ပြီး `failed` log တင် |

`continue` သည် ဤ iteration ကို ချက်ချင်း ရပ်ပြီး loop ၏ နောက် iteration သို့ ခုန်သည်။
failure သည် **write မလုပ်မီ** ဖြစ်သည်ကို သတိထားပါ — ဒါကြောင့် retry သည် ထို unit ကို
အစမှ ပြန် run ပြီး **half-merged state** မဖြစ်ပေါ်ပါ။

### `while ... else`

`for ... else` ကဲ့သို့ `while` တွင်လည်း `else` ရှိသည် — `break` မဖြစ်ခဲ့ရင် (loop က
condition ကြောင့် ဆုံးသွားရင်) `else` လုပ်ဆောင်သည်။ ဤနေရာတွင် `max_attempts` အထိ
ကျရှုံးခဲ့ပါက `break` မဖြစ်သဖြင့် `else` လုပ်ဆောင်ပြီး `failed` ဟု မှတ်တမ်းတင်သည်။

---

## 6. Write Phase — `graph.setdefault()` ဖြင့် MERGE Semantics

```python
for words in batch:
    chash = chunk_hash(words)
    for triple in extract_triples(words):
        entry = graph.setdefault(triple_key(triple), {
            "s": triple[0], "p": triple[1], "o": triple[2],
            "freq": 0, "sources": []})
        entry["freq"] += 1
        if chash not in entry["sources"]:
            entry["sources"].append(chash)
```

Nested loop နှစ်ခုဖြစ်သည် — batch အတွင်းက chunk များ၊ chunk တိုင်းထဲက triple များ။
`graph.setdefault(key, {...})` သည် key ရှိပြီးလျှင် လက်ရှိ entry ကို ပြန်ပေးသည် — ဒါကြောင့်
`freq` သည် **တိုးလာသည်** (အသစ်မဖန်တီး)။ ဤအပြုအမူသည် Neo4j ၏ `MERGE` နှင့် ကိုက်ညီသည် —
`CREATE` မဟုတ်သဖြင့် duplicate relationship မဖြစ်ပါ။

Cypher နှင့် ချိတ်ဆက်ရန် —

```cypher
UNWIND $triples AS t
MERGE (s:Entity {id: t.subject})
MERGE (o:Entity {id: t.object})
MERGE (s)-[r:REL {type: t.predicate}]->(o)
  ON CREATE SET r.freq = 1, r.sources = [t.chunk_hash]
  ON MATCH  SET r.freq = r.freq + 1
```

---

## 7. Run 1 Log

```python
import hashlib
import re

CORPUS = (
    "Alpha acquired Beta . Beta operates Gamma . Gamma founded Delta . "
    "Delta partners Epsilon . Epsilon supplies Zeta . Zeta acquired Alpha ."
)
VERBS = frozenset({"acquired", "operates", "founded", "partners", "supplies"})
ENTITIES = frozenset({"Alpha", "Beta", "Gamma", "Delta", "Epsilon", "Zeta"})


def tokenize(text):
    return re.findall(r"[A-Za-z]+", text)


def chunk_words(words, size, overlap):
    stride = size - overlap
    n, start, chunks = len(words), 0, []
    while start < n:
        chunks.append(words[start:start + size])
        if start + size >= n:
            break
        start += stride
    return chunks


def chunk_hash(words):
    return hashlib.sha1(" ".join(words).encode("utf-8")).hexdigest()[:8]


def extract_triples(words, verbs=VERBS, entities=ENTITIES):
    triples = []
    for i, token in enumerate(words):
        if token in verbs and 0 < i < len(words) - 1:
            subj, obj = words[i - 1], words[i + 1]
            if subj in entities and obj in entities:
                triples.append((subj, token, obj))
    return triples


def triple_key(triple):
    return tuple(part.lower() for part in triple)


class LCG:
    def __init__(self, seed=20261017):
        self.state = seed

    def next(self):
        self.state = (1103515245 * self.state + 12345) % (2 ** 31)
        return self.state

    def below(self, n):
        return self.next() % n


def run_batches(chunks, fail_plan, checkpoint, graph, batch_size=2,
                max_attempts=3, seed=20261017):
    rng = LCG(seed)
    log = []
    batches = [chunks[i:i + batch_size] for i in range(0, len(chunks), batch_size)]
    for b_idx, batch in enumerate(batches):
        bid = "batch_%d" % b_idx
        if bid in checkpoint:
            log.append((bid, "skip", 0))
            continue
        attempt = 0
        while attempt < max_attempts:
            attempt += 1
            if (bid, attempt) in fail_plan:
                log.append((bid, "retry", round(0.5 + rng.below(4) * 0.25, 2)))
                continue
            for words in batch:
                chash = chunk_hash(words)
                for triple in extract_triples(words):
                    entry = graph.setdefault(triple_key(triple), {
                        "s": triple[0], "p": triple[1], "o": triple[2],
                        "freq": 0, "sources": []})
                    entry["freq"] += 1
                    if chash not in entry["sources"]:
                        entry["sources"].append(chash)
            checkpoint[bid] = True
            log.append((bid, "done", attempt))
            break
        else:
            log.append((bid, "failed", attempt))
    return log


words = tokenize(CORPUS)
chunks = chunk_words(words, size=5, overlap=3)
checkpoint, graph = {}, {}
log = run_batches(chunks, {("batch_2", 1)}, checkpoint, graph)
for bid, status, detail in log:
    print("  %s -> %-5s %s" % (bid, status, detail))
print("committed batches:", len(checkpoint))
print("graph triples    :", len(graph))
```

Output —

```text
  batch_0 -> done  1
  batch_1 -> done  1
  batch_2 -> retry 1.0
  batch_2 -> done  2
  batch_3 -> done  1
committed batches: 4
graph triples    : 6
```

`batch_2` သည် attempt 1 တွင် `fail_plan` ကြောင့် `retry 1.0` ဖြစ်ပြီး attempt 2 တွင်
`done 2` ဖြစ်သည်။ Log တွင် batch ငါးခု (batch_2 နှစ်ခါ) ရှိသော်လည်း committed batch
သည် ၄ ခုသာ ဖြစ်သည်။ Graph တွင် triple ၆ ခု (dedup ပြီး) ရှိသည်။

---

## 8. Progress Table — Batch တိုင်း၏ ဖြစ်စဉ်

| batch | chunks | attempt | status | မှတ်ချက် |
| --- | --- | --- | --- | --- |
| `batch_0` | chunks[0:2] | 1 | `done` | checkpoint သတ်မှတ် |
| `batch_1` | chunks[2:4] | 1 | `done` | checkpoint သတ်မှတ် |
| `batch_2` | chunks[4:6] | 1 | `retry` | `fail_plan` ကြောင့် abort |
| `batch_2` | chunks[4:6] | 2 | `done` | ပြန်ကြိုးစားမှု အောင်မြင် |
| `batch_3` | chunks[6:8] | 1 | `done` | checkpoint သတ်မှတ် |

`committed batches = 4` ဖြစ်သည် — batch ၄ ခုလုံး checkpoint တွင် ပါသည်။

---

## 9. Idempotency — Run 2

```python
import hashlib
import re

CORPUS = (
    "Alpha acquired Beta . Beta operates Gamma . Gamma founded Delta . "
    "Delta partners Epsilon . Epsilon supplies Zeta . Zeta acquired Alpha ."
)
VERBS = frozenset({"acquired", "operates", "founded", "partners", "supplies"})
ENTITIES = frozenset({"Alpha", "Beta", "Gamma", "Delta", "Epsilon", "Zeta"})


def tokenize(text):
    return re.findall(r"[A-Za-z]+", text)


def chunk_words(words, size, overlap):
    stride = size - overlap
    n, start, chunks = len(words), 0, []
    while start < n:
        chunks.append(words[start:start + size])
        if start + size >= n:
            break
        start += stride
    return chunks


def chunk_hash(words):
    return hashlib.sha1(" ".join(words).encode("utf-8")).hexdigest()[:8]


def extract_triples(words, verbs=VERBS, entities=ENTITIES):
    triples = []
    for i, token in enumerate(words):
        if token in verbs and 0 < i < len(words) - 1:
            subj, obj = words[i - 1], words[i + 1]
            if subj in entities and obj in entities:
                triples.append((subj, token, obj))
    return triples


def triple_key(triple):
    return tuple(part.lower() for part in triple)


class LCG:
    def __init__(self, seed=20261017):
        self.state = seed

    def next(self):
        self.state = (1103515245 * self.state + 12345) % (2 ** 31)
        return self.state

    def below(self, n):
        return self.next() % n


def run_batches(chunks, fail_plan, checkpoint, graph, batch_size=2,
                max_attempts=3, seed=20261017):
    rng = LCG(seed)
    log = []
    batches = [chunks[i:i + batch_size] for i in range(0, len(chunks), batch_size)]
    for b_idx, batch in enumerate(batches):
        bid = "batch_%d" % b_idx
        if bid in checkpoint:
            log.append((bid, "skip", 0))
            continue
        attempt = 0
        while attempt < max_attempts:
            attempt += 1
            if (bid, attempt) in fail_plan:
                log.append((bid, "retry", round(0.5 + rng.below(4) * 0.25, 2)))
                continue
            for words in batch:
                chash = chunk_hash(words)
                for triple in extract_triples(words):
                    entry = graph.setdefault(triple_key(triple), {
                        "s": triple[0], "p": triple[1], "o": triple[2],
                        "freq": 0, "sources": []})
                    entry["freq"] += 1
                    if chash not in entry["sources"]:
                        entry["sources"].append(chash)
            checkpoint[bid] = True
            log.append((bid, "done", attempt))
            break
        else:
            log.append((bid, "failed", attempt))
    return log


words = tokenize(CORPUS)
chunks = chunk_words(words, size=5, overlap=3)
checkpoint, graph = {}, {}
run_batches(chunks, {("batch_2", 1)}, checkpoint, graph)
snapshot = {k: (e["freq"], tuple(sorted(e["sources"]))) for k, e in graph.items()}
log2 = run_batches(chunks, {("batch_2", 1)}, checkpoint, graph)
snapshot2 = {k: (e["freq"], tuple(sorted(e["sources"]))) for k, e in graph.items()}
print("run 2 log     :", [(bid, st) for bid, st, _ in log2])
print("snapshot equal:", snapshot == snapshot2)
print("graph triples :", len(graph))
```

Output —

```text
run 2 log     : [('batch_0', 'skip'), ('batch_1', 'skip'), ('batch_2', 'skip'), ('batch_3', 'skip')]
snapshot equal: True
graph triples : 6
```

Run 2 တွင် batch ၄ ခုလုံး `skip` ဖြစ်သည် — checkpoint ကြောင့်ပါ။ `snapshot` သည်
`{key: (freq, sources tuple)}` dict ဖြစ်သည် (dict comprehension)၊ run ၂ ခုကြား တူညီသည်
(`True`) ဆိုသည်မှာ graph လုံးဝ မပြောင်းလဲခဲ့ပါ။ ဤအချက်သည် **Idempotency** ဖြစ်သည်။
`sorted(e["sources"])` ကို tuple သို့ ပြောင်းထားခြင်းသည် comparison အတွက်
order-independent ဖြစ်စေသည်။

---

## 10. Trap — Checkpoint ကို စောစွာ Mark ခြင်း

```python
class LCG:
    def __init__(self, seed=20261017):
        self.state = seed

    def next(self):
        self.state = (1103515245 * self.state + 12345) % (2 ** 31)
        return self.state

    def below(self, n):
        return self.next() % n


def runner(fail_plan, checkpoint, mark_early, max_attempts=3, seed=20261017):
    rng = LCG(seed)
    log = []
    bid = "batch_1"
    if mark_early:
        checkpoint[bid] = True          # commit မပြီးမီ mark
    attempt = 0
    while attempt < max_attempts:
        attempt += 1
        if (bid, attempt) in fail_plan:
            log.append((bid, "retry", round(0.5 + rng.below(4) * 0.25, 2)))
            continue
        checkpoint[bid] = True          # မှန်သည့်နေရာ — write ပြီးမှ
        log.append((bid, "done", attempt))
        break
    else:
        log.append((bid, "failed", attempt))
    return log


fail_all = {("batch_1", 1), ("batch_1", 2), ("batch_1", 3)}
for label, mark_early in [("late (correct)", False), ("early", True)]:
    checkpoint = {}
    log = runner(fail_all, checkpoint, mark_early)
    print("%-15s log=%-42s committed=%s" % (label, log, "batch_1" in checkpoint))
```

Output —

```text
late (correct)  log=[('batch_1', 'retry', 1.0), ('batch_1', 'retry', 1.25), ('batch_1', 'retry', 0.5), ('batch_1', 'failed', 3)] committed=False
early           log=[('batch_1', 'retry', 1.0), ('batch_1', 'retry', 1.25), ('batch_1', 'retry', 0.5), ('batch_1', 'failed', 3)] committed=True
```

Log သည် နှစ်မျိုးလုံးတွင် တူညီသည် (`failed 3`)။ သို့သော် `committed` တန်ဖိုးမှာ
မတူညီပါ — `early` version တွင် `batch_1` သည် **checkpoint ထဲတွင် ရှိနေသည်**။ ဆိုလိုသည်မှာ
နောက် run တွင် batch_1 သည် `skip` ခံရမည် — သို့သော် ၎င်း၏ triple များ **တစ်ခါမျှ write
မဖြစ်ခဲ့ပါ**။ ဤအချက်သည် silent data loss ဖြစ်သည်။ ဤ code သည် checkpoint ကို write
ပြီးမှသာ သတ်မှတ်သဖြင့် ဤပြဿနာကို ရှောင်နိုင်သည်။

---

## 11. Trap — Checkpoint ကို လုံးဝ မစစ်ခြင်း

Idempotency သည် `MERGE` semantics ကြောင့် **မဟုတ်**၊ **checkpoint skip ကြောင့်** ဖြစ်သည်။

```python
def run_unit(records, graph, checkpoint, bid, check_checkpoint):
    if check_checkpoint and bid in checkpoint:
        return "skip"
    for rec in records:
        entry = graph.setdefault(rec, {"freq": 0})
        entry["freq"] += 1
    checkpoint[bid] = True
    return "done"


records = [("alpha", "acquired", "beta"), ("gamma", "founded", "delta")]

cp, graph = {}, {}
print("with checkpoint  :", run_unit(records, graph, cp, "batch_0", True),
      run_unit(records, graph, cp, "batch_0", True))
print("  freq           :", {k: v["freq"] for k, v in graph.items()})

cp2, graph2 = {}, {}
print("without checkpoint:", run_unit(records, graph2, cp2, "batch_0", False),
      run_unit(records, graph2, cp2, "batch_0", False))
print("  freq            :", {k: v["freq"] for k, v in graph2.items()})
```

Output —

```text
with checkpoint  : done skip
  freq           : {('alpha', 'acquired', 'beta'): 1, ('gamma', 'founded', 'delta'): 1}
without checkpoint: done done
  freq            : {('alpha', 'acquired', 'beta'): 2, ('gamma', 'founded', 'delta'): 2}
```

Checkpoint စစ်လျှင် ဒုတိယ run သည် `skip` ဖြစ်ပြီး `freq` သည် ၁ တွင်ရပ်သည်။ Checkpoint
မစစ်လျှင် ဒုတိယ run သည် ထပ်မံ write လုပ်သဖြင့် `freq` သည် ၂ သို့ **တိုးသွားသည်** — ဤအချက်သည်
မလိုလားအပ်သော double-counting ဖြစ်သည်။ Graph ထဲမှာ triple ထပ်မဖြစ်သော်လည်း `freq` မှားသဖြင့်
confidence သည်လည်း မှားမည်။

---

## 12. Retry Headroom မလုံလောက်ခြင်း

```python
import hashlib
import re

CORPUS = (
    "Alpha acquired Beta . Beta operates Gamma . Gamma founded Delta . "
    "Delta partners Epsilon . Epsilon supplies Zeta . Zeta acquired Alpha ."
)
VERBS = frozenset({"acquired", "operates", "founded", "partners", "supplies"})
ENTITIES = frozenset({"Alpha", "Beta", "Gamma", "Delta", "Epsilon", "Zeta"})


def tokenize(text):
    return re.findall(r"[A-Za-z]+", text)


def chunk_words(words, size, overlap):
    stride = size - overlap
    n, start, chunks = len(words), 0, []
    while start < n:
        chunks.append(words[start:start + size])
        if start + size >= n:
            break
        start += stride
    return chunks


def chunk_hash(words):
    return hashlib.sha1(" ".join(words).encode("utf-8")).hexdigest()[:8]


def extract_triples(words, verbs=VERBS, entities=ENTITIES):
    triples = []
    for i, token in enumerate(words):
        if token in verbs and 0 < i < len(words) - 1:
            subj, obj = words[i - 1], words[i + 1]
            if subj in entities and obj in entities:
                triples.append((subj, token, obj))
    return triples


def triple_key(triple):
    return tuple(part.lower() for part in triple)


class LCG:
    def __init__(self, seed=20261017):
        self.state = seed

    def next(self):
        self.state = (1103515245 * self.state + 12345) % (2 ** 31)
        return self.state

    def below(self, n):
        return self.next() % n


def run_batches(chunks, fail_plan, checkpoint, graph, batch_size=2,
                max_attempts=3, seed=20261017):
    rng = LCG(seed)
    log = []
    batches = [chunks[i:i + batch_size] for i in range(0, len(chunks), batch_size)]
    for b_idx, batch in enumerate(batches):
        bid = "batch_%d" % b_idx
        if bid in checkpoint:
            log.append((bid, "skip", 0))
            continue
        attempt = 0
        while attempt < max_attempts:
            attempt += 1
            if (bid, attempt) in fail_plan:
                log.append((bid, "retry", round(0.5 + rng.below(4) * 0.25, 2)))
                continue
            for words in batch:
                chash = chunk_hash(words)
                for triple in extract_triples(words):
                    entry = graph.setdefault(triple_key(triple), {
                        "s": triple[0], "p": triple[1], "o": triple[2],
                        "freq": 0, "sources": []})
                    entry["freq"] += 1
                    if chash not in entry["sources"]:
                        entry["sources"].append(chash)
            checkpoint[bid] = True
            log.append((bid, "done", attempt))
            break
        else:
            log.append((bid, "failed", attempt))
    return log


words = tokenize(CORPUS)
chunks = chunk_words(words, size=5, overlap=3)
checkpoint_b, graph_b = {}, {}
log_b = run_batches(chunks, {("batch_1", 1), ("batch_1", 2), ("batch_1", 3)},
                    checkpoint_b, graph_b, max_attempts=2)
for bid, status, detail in log_b:
    print("  %s -> %-5s %s" % (bid, status, detail))
print("failed batches   :", [bid for bid, st, _ in log_b if st == "failed"])
print("batch_1 committed:", "batch_1" in checkpoint_b)
```

Output —

```text
  batch_0 -> done  1
  batch_1 -> retry 1.0
  batch_1 -> retry 1.25
  batch_1 -> failed 2
  batch_2 -> done  1
  batch_3 -> done  1
failed batches   : ['batch_1']
batch_1 committed: False
```

`fail_plan` သည် attempt ၁ နှင့် ၂ နှစ်ခုလုံးကို ကျရှုံးစေပြီး `max_attempts=2` ဖြစ်သဖြင့်
headroom မလုံလောက်ပါ။ Log က `failed 2` ဖြင့် ရပ်သည်။ `batch_1` သည် checkpoint ထဲ
**မပါ** (`False`) — ဒါကြောင့် နောက် run တွင် ပြန်ကြိုးစားမည်။ Write သည် failure မတိုင်မီ
မဖြစ်ခဲ့သဖြင့် `graph_b` တွင် `batch_1` ၏ triple များ မပါ — **partial write မဖြစ်ပေါ်**။

---

## 13. Code တစ်ခုလုံး — Run လုပ်နိုင်သော Version

```python
import hashlib
import re

CORPUS = (
    "Alpha acquired Beta . Beta operates Gamma . Gamma founded Delta . "
    "Delta partners Epsilon . Epsilon supplies Zeta . Zeta acquired Alpha ."
)
VERBS = frozenset({"acquired", "operates", "founded", "partners", "supplies"})
ENTITIES = frozenset({"Alpha", "Beta", "Gamma", "Delta", "Epsilon", "Zeta"})


def tokenize(text):
    return re.findall(r"[A-Za-z]+", text)


def chunk_words(words, size, overlap):
    stride = size - overlap
    n, start, chunks = len(words), 0, []
    while start < n:
        chunks.append(words[start:start + size])
        if start + size >= n:
            break
        start += stride
    return chunks


def chunk_hash(words):
    return hashlib.sha1(" ".join(words).encode("utf-8")).hexdigest()[:8]


def extract_triples(words, verbs=VERBS, entities=ENTITIES):
    triples = []
    for i, token in enumerate(words):
        if token in verbs and 0 < i < len(words) - 1:
            subj, obj = words[i - 1], words[i + 1]
            if subj in entities and obj in entities:
                triples.append((subj, token, obj))
    return triples


def triple_key(triple):
    return tuple(part.lower() for part in triple)


class LCG:
    def __init__(self, seed=20261017):
        self.state = seed

    def next(self):
        self.state = (1103515245 * self.state + 12345) % (2 ** 31)
        return self.state

    def below(self, n):
        return self.next() % n


def run_batches(chunks, fail_plan, checkpoint, graph, batch_size=2,
                max_attempts=3, seed=20261017):
    rng = LCG(seed)
    log = []
    batches = [chunks[i:i + batch_size] for i in range(0, len(chunks), batch_size)]
    for b_idx, batch in enumerate(batches):
        bid = "batch_%d" % b_idx
        if bid in checkpoint:
            log.append((bid, "skip", 0))
            continue
        attempt = 0
        while attempt < max_attempts:
            attempt += 1
            if (bid, attempt) in fail_plan:
                log.append((bid, "retry", round(0.5 + rng.below(4) * 0.25, 2)))
                continue
            for words in batch:
                chash = chunk_hash(words)
                for triple in extract_triples(words):
                    entry = graph.setdefault(triple_key(triple), {
                        "s": triple[0], "p": triple[1], "o": triple[2],
                        "freq": 0, "sources": []})
                    entry["freq"] += 1
                    if chash not in entry["sources"]:
                        entry["sources"].append(chash)
            checkpoint[bid] = True
            log.append((bid, "done", attempt))
            break
        else:
            log.append((bid, "failed", attempt))
    return log


words = tokenize(CORPUS)
chunks = chunk_words(words, size=5, overlap=3)
print("chunks: %d, batch_size: 2 -> %d batches" % (len(chunks), (len(chunks) + 1) // 2))
checkpoint, graph = {}, {}
log = run_batches(chunks, {("batch_2", 1)}, checkpoint, graph)
print("run 1 log:")
for bid, status, detail in log:
    print("  %s -> %-5s %s" % (bid, status, detail))
print("committed batches: %d" % len(checkpoint))
print("graph triples    : %d" % len(graph))
log2 = run_batches(chunks, {("batch_2", 1)}, checkpoint, graph)
print("run 2 log: %s" % [(bid, st) for bid, st, _ in log2])
checkpoint_b, graph_b = {}, {}
log_b = run_batches(chunks, {("batch_1", 1), ("batch_1", 2), ("batch_1", 3)},
                    checkpoint_b, graph_b, max_attempts=2)
print("no-headroom failing batches: %s" % [bid for bid, st, _ in log_b if st == "failed"])
```

Output —

```text
chunks: 8, batch_size: 2 -> 4 batches
run 1 log:
  batch_0 -> done  1
  batch_1 -> done  1
  batch_2 -> retry 1.0
  batch_2 -> done  2
  batch_3 -> done  1
committed batches: 4
graph triples    : 6
run 2 log: [('batch_0', 'skip'), ('batch_1', 'skip'), ('batch_2', 'skip'), ('batch_3', 'skip')]
no-headroom failing batches: ['batch_1']
```

---

## 14. ကိုယ်တိုင်လေ့ကျင့်ကြည့်ပါ

**မေးခွန်း** — `fail_plan = {("batch_2", 1)}` ဖြင့် run လျှင် `batch_2` ၏ ပထမ attempt တွင်
log ထည့်မည့် backoff တန်ဖိုးသည် ဘာဖြစ်မလဲ။ (LCG seed = 20261017)

1. 0.50
2. 0.75
3. 1.00
4. 1.25

<details>
<summary>အဖြေ ကြည့်ရန်</summary>

**အဖြေ — 3. 1.00**

```python
class LCG:
    def __init__(self, seed=20261017):
        self.state = seed

    def next(self):
        self.state = (1103515245 * self.state + 12345) % (2 ** 31)
        return self.state

    def below(self, n):
        return self.next() % n


rng = LCG(20261017)
drawn = rng.below(4)
print("below(4)          :", drawn)
print("backoff           :", round(0.5 + drawn * 0.25, 2))
rng2 = LCG(20261017)
print("repeatable        :", [rng2.below(4) for _ in range(3)])
```

Output —

```text
below(4)          : 2
backoff           : 1.0
repeatable        : [2, 3, 0]
```

အကြောင်းရင်း — LCG ၏ ပထမ `below(4)` သည် `2` ဖြစ်သည်။ ထို့ကြောင့် backoff
`= round(0.5 + 2 * 0.25, 2) = round(1.0, 2) = 1.0` ဖြစ်သည်။ Seed ပြောင်းလျှင် ဤတန်ဖိုး
ပြောင်းမည် — ဒါကြောင့် `seed` သည် output ၏ တစ်စိတ်တစ်ပိုင်းဖြစ်သည်။

</details>

---

**အဓိက မှတ်ထားရန်** — Idempotent batch runner ၏ သော့ချက် သုံးခုမှာ — (၁) chunk များကို
batch အဖြစ် စု၍ တစ်ခုချင်း run ခြင်း၊ (၂) failure ကို write မလုပ်မီ abort လုပ်၍ backoff
ဖြင့် retry လုပ်ခြင်း၊ (၃) **checkpoint ကို write ပြီးမှသာ သတ်မှတ်ခြင်း**။ Checkpoint ကို
စောစွာ mark လျှင် silent data loss ဖြစ်ပြီး၊ checkpoint ကို လုံးဝ မစစ်လျှင် `freq`
double-counting ဖြစ်သည်။ Graph ကို `dict.setdefault` (Neo4j တွင် `MERGE`) ဖြင့်
update လုပ်ခြင်းသည် duplicate relationship ကို တားပေမဲ့ Idempotency ကို **တစ်ခုတည်း
မပေးနိုင်ပါ** — checkpoint skip နှင့် တွဲမှသာ ပြည့်စုံသည်။ Backoff jitter ကို fixed-seed
LCG ဖြင့် ထုတ်ခြင်းသည် Determinism ကို ထိန်းသိမ်းသည်။
