# M03 — Reference Solution

ဤဖိုင်တွင် exercise ၆ ခုအတွက် reference implementation များ ပါဝင်သည်။ Algorithm များသည် `lab.py` နှင့်
တူညီသည် (`lab.py` တွင် `assert` နှင့် `print` ပိုထည့်ထားသည်)။

## Shared helpers

```python
import hashlib
import re
from collections import defaultdict

CORPUS = (
    "Alpha acquired Beta . Beta operates Gamma . Gamma founded Delta . "
    "Delta partners Epsilon . Epsilon supplies Zeta . Zeta acquired Alpha ."
)
VERBS = frozenset({"acquired", "operates", "founded", "partners", "supplies"})
ENTITIES = frozenset({"Alpha", "Beta", "Gamma", "Delta", "Epsilon", "Zeta"})

def tokenize(text):
    return re.findall(r"[A-Za-z]+", text)

def chunk_words(words, size, overlap):
    if not 0 <= overlap < size:
        raise ValueError("require 0 <= overlap < size")
    stride = size - overlap
    n = len(words)
    chunks = []
    start = 0
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

def reconnect_boundary_triples(chunks, verbs=VERBS, entities=ENTITIES):
    recovered = []
    for i in range(len(chunks) - 1):
        left, right = chunks[i], chunks[i + 1]
        if not left or not right:
            continue
        if left[-1] in verbs and len(left) >= 2 and left[-2] in entities and right[0] in entities:
            recovered.append((left[-2], left[-1], right[0]))
        if right[0] in verbs and len(right) >= 2 and left[-1] in entities and right[1] in entities:
            recovered.append((left[-1], right[0], right[1]))
    return recovered

def triple_key(triple):
    return tuple(part.lower() for part in triple)

def merge_triples(records):
    merged = {}
    for rec in records:
        key = triple_key((rec["s"], rec["p"], rec["o"]))
        entry = merged.get(key)
        if entry is None:
            entry = {"s": rec["s"], "p": rec["p"], "o": rec["o"], "sources": [], "freq": 0}
            merged[key] = entry
        if rec["chunk_hash"] not in entry["sources"]:
            entry["sources"].append(rec["chunk_hash"])
        entry["freq"] += 1
    for entry in merged.values():
        entry["sources"].sort()
        entry["confidence"] = round(min(1.0, 0.5 + 0.25 * entry["freq"]), 2)
    return merged
```

**အဓိကအယူအဆ** — `chunk_words` သည် `overlap` ကို token အရေအတွက်ဖြင့် သတ်မှတ်ပြီး `stride = size - overlap`
ဖြင့် ရွေ့သည်။ Guard မရှိပါက `overlap >= size` ဖြစ်သည့်အခါ infinite loop ဖြစ်မည်။

---

## Exercise 1 — Fixed-size chunking

```python
def exercise_1() -> bool:
    words = tokenize(CORPUS)
    chunks = chunk_words(words, size=6, overlap=0)
    print("token count : %d" % len(words))
    print("chunk count : %d" % len(chunks))
    print("chunk sizes : %s" % [len(c) for c in chunks])
    for i, c in enumerate(chunks):
        print("  chunk %d: %s" % (i, " ".join(c)))
    assert len(words) == 18
    assert len(chunks) == 3
    assert [len(c) for c in chunks] == [6, 6, 6]
    assert all(c == words[i * 6:(i + 1) * 6] for i, c in enumerate(chunks))
    return True
```

**အဓိကအယူအဆ** — `overlap=0` ဖြစ်ပါက chunk များသည် ထပ်မနေ၊ လုံးလုံး ဖုံးလွှမ်းသည်။ Token အရေအတွက်ကို
`tokenize` က punctuation ဖယ်၍ တွက်သဖြင့် token count နှင့် word count တူသည်။

---

## Exercise 2 — Overlap ထည့်ခြင်း

```python
def exercise_2() -> bool:
    words = tokenize(CORPUS)
    no_overlap = chunk_words(words, size=6, overlap=0)
    with_overlap = chunk_words(words, size=6, overlap=2)
    print("overlap=0 -> %d chunks" % len(no_overlap))
    print("overlap=2 -> %d chunks" % len(with_overlap))
    for i in range(len(with_overlap) - 1):
        assert with_overlap[i][-2:] == with_overlap[i + 1][:2]
    assert len(with_overlap) == 4
    assert all(len(c) == 6 for c in with_overlap)
    assert with_overlap[0][-2:] == ["operates", "Gamma"]
    assert len(with_overlap) > len(no_overlap)
    return True
```

**အဓိကအယူအဆ** — Overlap သည် boundary တိုင်းတွင် တိကျစွာ ထပ်ရမည်။ `overlap=2` ဖြစ်ပါက boundary တိုင်း၏
နောက်ဆုံး/အစ token နှစ်လုံး တူညီကြောင်း assert ဖြင့် စစ်နိုင်သည်။ Chunk အရေအတွက် တိုးခြင်းသည်
token ကုန်ကျစရိတ် တိုးခြင်းကို ဆိုလိုသည်။

---

## Exercise 3 — Map-Reduce triple aggregation

```python
def exercise_3() -> bool:
    words = tokenize(CORPUS)
    chunks = chunk_words(words, size=6, overlap=0)
    records = []
    per_chunk = []
    for c in chunks:
        mapped = extract_triples(c)
        per_chunk.append(len(mapped))
        for triple in mapped:
            records.append({"s": triple[0], "p": triple[1], "o": triple[2],
                            "chunk_hash": chunk_hash(c)})
    print("per-chunk triple counts %s" % per_chunk)
    print("raw records %d" % len(records))
    merged = merge_triples(records)
    print("unique triples %d" % len(merged))
    assert per_chunk == [2, 2, 2]
    assert len(records) == 6
    assert len(merged) == 6
    assert all(e["freq"] == 1 for e in merged.values())
    return True
```

**အဓိကအယူအဆ** — Map phase သည် chunk တိုင်းကို သီးခြား ကိုင်တွယ်သည် (parallel run လုပ်နိုင်သည်)။ Reduce
phase တွင်သာ အားလုံးကို စုစည်းသည်။ Record တိုင်းတွင် source `chunk_hash` ထည့်ခြင်းဖြင့် provenance
ကို ထိန်းသိမ်းသည်။

---

## Exercise 4 — Cross-chunk relationship ပြန်ချိတ်ခြင်း

```python
def exercise_4() -> bool:
    words = tokenize(CORPUS)
    chunks = chunk_words(words, size=5, overlap=0)
    mapped = []
    for c in chunks:
        mapped.extend(extract_triples(c))
    recovered = reconnect_boundary_triples(chunks)
    print("mapped %d, recovered %d" % (len(mapped), len(recovered)))
    combined = list(dict.fromkeys(mapped + recovered))
    assert len(chunks) == 4
    assert len(mapped) == 4
    assert len(recovered) == 2
    assert ("Beta", "operates", "Gamma") in recovered
    assert ("Delta", "partners", "Epsilon") in recovered
    assert len(combined) == 6
    return True
```

**အဓိကအယူအဆ** — `size=5` ဖြစ်ပါက ဝါကျနှစ်ခု boundary တွင် ကွဲသွားသဖြင့် map phase တွင် Triple ၄ ခုသာ
ရသည်။ Reconnection သည် `chunk[i]` ၏ အဆုံးနှင့် `chunk[i+1]` ၏ အစကို ကြည့်၍ ကျန်နှစ်ခုကို ပြန်ချိတ်သည်။
Recovered Triple များကို production တွင် confidence နည်းစွာ သတ်မှတ်ရမည်။

---

## Exercise 5 — Triple deduplication နှင့် merge

```python
def exercise_5() -> bool:
    words = tokenize(CORPUS)
    chunks = chunk_words(words, size=5, overlap=3)
    records = []
    for c in chunks:
        chash = chunk_hash(c)
        for triple in extract_triples(c):
            records.append({"s": triple[0], "p": triple[1], "o": triple[2],
                            "chunk_hash": chash})
    merged = merge_triples(records)
    duplicated = sorted(k for k, e in merged.items() if e["freq"] > 1)
    print("raw %d -> unique %d" % (len(records), len(merged)))
    assert len(records) == 8
    assert len(merged) == 6
    assert len(duplicated) == 2
    assert merged[("gamma", "founded", "delta")]["freq"] == 2
    assert merged[("epsilon", "supplies", "zeta")]["freq"] == 2
    assert merged[("gamma", "founded", "delta")]["confidence"] == 1.0
    return True
```

**အဓိကအယူအဆ** — Overlap ကြောင့် Triple အချို့ ထပ်ထွက်လာသည်။ `freq` သည် dedup ratio ကို တိုင်းတာရန်
အသုံးဝင်သည်။ `sources` ကို မဖျက်ဘဲ သိမ်းခြင်းဖြင့် triple တိုင်း၏ မူလ chunk ကို ပြန်ခြေရာခံနိုင်သည်။

---

## Exercise 6 — Idempotent batch runner

```python
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
                backoff = round(0.5 + rng.below(4) * 0.25, 2)
                log.append((bid, "retry", backoff))
                continue
            for words in batch:
                chash = chunk_hash(words)
                for triple in extract_triples(words):
                    key = triple_key(triple)
                    entry = graph.get(key)
                    if entry is None:
                        entry = {"s": triple[0], "p": triple[1], "o": triple[2],
                                 "freq": 0, "sources": []}
                        graph[key] = entry
                    entry["freq"] += 1
                    if chash not in entry["sources"]:
                        entry["sources"].append(chash)
            checkpoint[bid] = True
            log.append((bid, "done", attempt))
            break
        else:
            log.append((bid, "failed", attempt))
    return log

def exercise_6() -> bool:
    words = tokenize(CORPUS)
    chunks = chunk_words(words, size=5, overlap=3)
    checkpoint, graph = {}, {}
    log = run_batches(chunks, {("batch_2", 1)}, checkpoint, graph)
    assert len(checkpoint) == 4
    assert len(graph) == 6
    assert ("batch_2", "done", 2) in log

    snapshot = {k: (e["freq"], tuple(sorted(e["sources"]))) for k, e in graph.items()}
    log2 = run_batches(chunks, {("batch_2", 1)}, checkpoint, graph)
    snapshot2 = {k: (e["freq"], tuple(sorted(e["sources"]))) for k, e in graph.items()}
    assert all(st == "skip" for _, st, _ in log2)
    assert snapshot == snapshot2
    assert len(graph) == 6

    checkpoint_b, graph_b = {}, {}
    log_b = run_batches(chunks, {("batch_1", 1), ("batch_1", 2), ("batch_1", 3)},
                        checkpoint_b, graph_b, max_attempts=2)
    assert [bid for bid, st, _ in log_b if st == "failed"] == ["batch_1"]
    assert "batch_1" not in checkpoint_b
    return True
```

**အဓိကအယူအဆ** — Checkpoint ကို batch commit ပြီးမှသာ သတ်မှတ်သဖြင့် run ပြန်သည့်အခါ committed batch များ
skip ဖြစ်ပြီး graph မပြောင်းလဲ (Idempotency)။ `fail_plan` သည် write မလုပ်မီ abort လုပ်သဖြင့် retry သည်
ပြန် run ပြီး half-merged state မဖြစ်ပေါ်ပါ။ `graph` ကို `triple_key` ဖြင့် key လုပ်ခြင်းသည်
Neo4j `MERGE` semantics ကို simulate လုပ်သည် — Cypher နှင့် ချိတ်ဆက်သည့်အခါ:

```cypher
UNWIND $triples AS t
MERGE (s:Entity {id: t.subject})
MERGE (o:Entity {id: t.object})
MERGE (s)-[r:REL {type: t.predicate}]->(o)
  ON CREATE SET r.freq = 1, r.sources = [t.chunk_hash]
  ON MATCH  SET r.freq = r.freq + 1
```

`MERGE` ကို သုံး၍ `CREATE` ကို မသုံးခြင်းသည် Idempotency ၏ အခြေခံဖြစ်သည်။ Backoff jitter ကို fixed-seed
LCG ဖြင့် ထုတ်ခြင်းသည် Determinism ထိန်းသိမ်းသည် (`random` မသုံးရ)။
