# M03 — Chunking for Entity and Relationship Extraction at Scale (Explanation)

LLM-based extraction သည် တစ်ကြိမ် Context Window တစ်ခုအတွင်းရှိ Token များကိုသာ မြင်သည်။ Corpus ကြီးတစ်ခုကို
တစ်ကြိမ်တည်း feed လုပ်၍ မရနိုင်သောကြောင့် document ကို **Chunk** များအဖြစ် ခွဲပြီး chunk တိုင်းကို သီးခြား
extract လုပ်ရသည်။ ထို့ကြောင့် Triple တိုင်း၏ အရည်အသွေးသည် chunk boundary ပေါ်တွင် တိုက်ရိုက် မှီခိုသည်။
ဤအခန်းသည် chunking ကို extraction accuracy နှင့် pipeline throughput နှစ်ခုစလုံးအတွက် parameter အဖြစ်
ချဉ်းကပ်သည်။

## ၁။ Chunk size သည် extraction quality ကို ဘယ်လို သက်ရောက်သည်

Relationship extraction သည် subject နှင့် object ကို တစ်ခုတည်းသော Context Window အတွင်း တွဲမြင်မှ
ထုတ်နိုင်သည်။ Chunk သေးလွန်းပါက ဝါကျတစ်ခုကို ဖြတ်တောက်ပြီး entity pair သည် မတူညီသော chunk နှစ်ခုထဲ
ကျရောက်သည်။ ထို pair ၏ Relationship သည် **map phase တွင် လုံးလုံး ဆုံးရှုံး** သည်။

- Chunk သေးလွန်း → recall ကျသည် (boundary ဖြတ်သော relationship များ ပျောက်သည်)
- Chunk ကြီးလွန်း → precision ကျနိုင်၊ irrelevant context များလာပြီး token cost နှင့် latency တိုးသည်

ဤသည်သည် tunable trade-off ဖြစ်သည်။ တိုင်းတာနိုင်သော သတ်မှတ်ချက်မှာ **boundary-hit rate** —
ခွဲထားသော chunk များအနက် entity pair တစ်စုံ နှစ်ခြမ်းကွဲသွားသော boundary အရေအတွက် ဖြစ်သည်။

```
boundary_hit_rate = split_entity_pairs / total_entity_pairs
```

Chunk size ကို တိုးလိုက်ပါက split_entity_pairs လျော့သော်လည်း chunk အရေအတွက် လျော့သွားသဖြင့်
parallelism လျော့ပြီး ပြန် run ရသော အပိုင်းအရွယ်အစား ကြီးလာသည်။

## ၂။ Chunk size နှင့် overlap — Token budget နှင့် Context Window

Chunk size ကို များသောအားဖြင့် Token အရေအတွက်ဖြင့် တိုင်းတာသည်။ Chunk တစ်ခု၏ prompt budget ကို
အောက်ပါအတိုင်း ခန့်မှန်းရသည်။

```
prompt_tokens = instruction_tokens + schema_tokens + chunk_tokens
chunk_tokens  <= context_window - instruction_tokens - schema_tokens - reserve_tokens
```

`reserve_tokens` သည် output (Triple JSON) အတွက် သီးသန့်ထားသော budget ဖြစ်သည်။ ဤနေရာတွင်
**chunk size သည်သာ စိတ်ကြိုက်ရွေးနိုင်သော variable** ဖြစ်သည် — instruction နှင့် schema ကို မလျှော့နိုင်။

**Overlap** သည် chunk နှစ်ခုအကြား ထပ်နေသော token အရေအတွက် ဖြစ်သည်။ Overlap ထည့်ပါက boundary ဖြတ်သော
ဝါကျသည် အနည်းဆုံး chunk တစ်ခုအတွင်း အပြည့်အစုံ ပါဝင်နိုင်ခြေ တိုးသည်။ ကုန်ကျစရိတ်မှာ token ထပ်ကျခြင်း
ဖြစ်သည်။

```
stride = chunk_size - overlap
chunk_count ≈ ceil((n_tokens - overlap) / stride)
```

Overlap ကြောင့် Triple အချို့သည် chunk နှစ်ခုစလုံးမှ ထွက်လာသည်။ ထိုအခါ **Deduplication မဖြစ်မနေ
လိုအပ်လာ**သည် (အခန်း ၅)။ ဤဒုတိယကုန်ကျစရိတ်ကို သတိပြုရမည်။

Deterministic chunking function (ဤ module တစ်လျှောက် အသုံးပြုသည်):

```python
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

# size=6, overlap=0, n=18 → 3 chunks (chunk sizes [6, 6, 6])
# size=6, overlap=2, n=18 → 4 chunks (chunk sizes [6, 6, 6, 6])
```

`overlap >= size` ဖြစ်ပါက stride ≤ 0 ဖြစ်၍ infinite loop ဖြစ်သည်။ ထို့ကြောင့် guard ကို မဖြစ်မနေ
ထားရမည်။

**ဘယ်အချိန် overlap မသုံးသင့်သလဲ** — ဖွဲ့စည်းပုံတို (FAQ၊ product record) များအတွက် overlap သည် token
ကုန်ကျစရိတ်ကိုသာ တိုးပြီး recall အကျိုးမရှိပါ။

## ၃။ Map-Reduce extraction pattern

Map-Reduce သည် chunk အရေအတွက် ထောင်ပေါင်းများစွာအတွက် standard pattern ဖြစ်သည်။

- **Map phase** — chunk တိုင်းကို သီးခြား extract လုပ်သည်။ အလုပ်တိုင်း independent ဖြစ်သဖြင့် parallel run
  လုပ်နိုင်သည်။
- **Reduce phase** — Triple အားလုံးကို စုစည်း၊ deduplicate လုပ်၊ provenance (source chunk id) ကို ပေါင်းသည်။

```python
def extract_triples(words, verbs, entities):
    triples = []
    for i, token in enumerate(words):
        if token in verbs and 0 < i < len(words) - 1:
            subj, obj = words[i - 1], words[i + 1]
            if subj in entities and obj in entities:
                triples.append((subj, token, obj))
    return triples

# 3 chunks of 6 tokens → per-chunk counts [2, 2, 2] → 6 raw triples
```

Production တွင် map phase ကို thread/process pool ဖြင့် fan-out လုပ်ပြီး reduce phase ကို deterministic order
(ဥပမာ source chunk hash အလိုက် sort) ဖြင့် run ရသည်။ Determinism မထိန်းပါက run တိုင်း output မတူသဖြင့်
diff စစ်ဆေးခြင်း မပြုနိုင်တော့ပါ။

## ၄။ Cross-chunk relationship များ ပြန်ချိတ်ဆက်ခြင်း

Map phase တွင် ဆုံးရှုံးသွားသော relationship များကို reduce phase တွင် `chunk[i]` ၏ အဆုံးနှင့် `chunk[i+1]`
၏ အစကို ကြည့်၍ ပြန်ချိတ်နိုင်သည်။ ပုံစံ နှစ်မျိုး ရှိသည်။

| ပုံစံ | Boundary အခြေအနေ | ပြန်ချိတ်ရမည့် Triple |
|---|---|---|
| A | ဘယ်ဘက် chunk သည် `subject + verb` ဖြင့် ဆုံး | `(subject, verb, right_head_entity)` |
| B | ညာဘက် chunk သည် `verb + object` ဖြင့် စ | `(left_tail_entity, verb, object)` |

```python
def reconnect_boundary_triples(chunks, verbs, entities):
    recovered = []
    for i in range(len(chunks) - 1):
        left, right = chunks[i], chunks[i + 1]
        if not left or not right:
            continue
        if left[-1] in verbs and len(left) >= 2 and left[-2] in entities and right[0] in entities:
            recovered.append((left[-2], left[-1], right[0]))   # pattern A
        if right[0] in verbs and len(right) >= 2 and left[-1] in entities and right[1] in entities:
            recovered.append((left[-1], right[0], right[1]))   # pattern B
    return recovered

# size=5, overlap=0 → 4 chunks: mapped 4 triples, recovered 2 → combined unique 6
```

Reconnection သည် heuristic ဖြစ်သည်။ False positive ဖြစ်နိုင်သဖြင့် recovered Triple များကို မူရင်း map
Triple များထက် confidence နည်းစွာ သတ်မှတ်ပြီး provenance တွင် `reconnected=True` ဟု မှတ်ရမည်။
**ဘယ်အချိန် မသုံးသင့်သလဲ** — overlap ကို လုံလောက်စွာ ထည့်ထားပြီးဖြစ်ပါက reconnection သည် ထပ်နေသော
အလုပ်သာ ဖြစ်သည်။

## ၅။ Triple deduplication နှင့် merge

Overlap သုံးသည့်အခါလည်းကောင်း၊ document တစ်ခုတည်းကို ပြန် run သည့်အခါလည်းကောင်း Triple များ ထပ်လာသည်။
Deduplication key ကို normalize လုပ်ရမည်။ များသောအားဖြင့် subject နှင့် object ကို case-fold လုပ်ပြီး
predicate ကို schema canonical form သို့ map ရသည်။

```python
def triple_key(triple):
    return tuple(part.lower() for part in triple)
```

Merge တွင် တစ်ခုတည်းသော record အဖြစ် ပေါင်းပြီး — `freq` (အကြိမ်အရေအတွက်)၊ `sources` (chunk hash list)
နှင့် ပေါင်းစည်းထားသော `confidence` ကို သိမ်းရသည်။

```
confidence = min(1.0, base + increment * freq)
```

ဤ module တွင် `base = 0.5`, `increment = 0.25` သုံးသည်။ freq=2 ဖြစ်ပါက confidence=1.0 ရသည်။
Provenance (source chunk hash) ကို မဖျက်ရ — M04 project တွင် triple တိုင်း၏ မူလအရင်းအမြစ်ကို ပြန်ခြေရာခံရမည်။

**သတိ** — predicate မတူညီသော (active/passive) triple များကို case-fold ဖြင့် မပေါင်းမိစေရန် schema
level တွင် canonical predicate list ကို သတ်မှတ်ထားရမည်။

## ၆။ Scale — Batching၊ concurrency၊ checkpointing၊ idempotency၊ failure recovery

Chunk ထောင်ပေါင်းများစွာကို တစ်ကြိမ်တည်း run ပါက partial failure တစ်ခုကြောင့် အလုပ်အားလုံး ဆုံးရှုံးနိုင်သည်။
အောက်ပါ အင်ဂျင်နီယာ pattern များသည် ဤပြဿနာကို ဖြေရှင်းသည်။

- **Batching** — chunk များကို batch အဖြစ် စုပြီး batch တိုင်းကို atomic unit အဖြစ် ကိုင်တွယ်သည်။
  Batch တစ်ခု ကျရှုံးပါက ထို batch ကိုသာ ပြန် run ရသည်။
- **Checkpointing** — batch တစ်ခု commit ပြီးတိုင်း `checkpoint[batch_id] = True` ကို သိမ်းသည်။
  Pipeline ပြန်စသည့်အခါ committed batch များကို **skip** လုပ်နိုင်သည်။
- **Idempotency** — အလုပ်တူကို နှစ်ကြိမ် run ပါက ရလဒ်မပြောင်းလဲရမည်။ Write ကို `MERGE` semantics
  (triple_key အလိုက် upsert) ဖြင့် ပြုလုပ်သည်။ Cypher တွင်:

  ```cypher
  UNWIND $triples AS t
  MERGE (s:Entity {id: t.subject})
  MERGE (o:Entity {id: t.object})
  MERGE (s)-[r:REL {type: t.predicate}]->(o)
    ON CREATE SET r.freq = 1, r.sources = [t.chunk_hash]
    ON MATCH  SET r.freq = r.freq + 1
  ```

  `MERGE` (CREATE မဟုတ်) သုံးခြင်းကြောင့် ပြန် run လျှင် duplicate relationship မဖြစ်ပေါ်ပါ။
- **Failure recovery** — retry ကို exponential backoff ဖြင့် လုပ်သည်။ Retry သည် **write မလုပ်မီ** ကျရှုံးသော
  unit ကိုသာ ပြန် run ရမည်; ထို့ကြောင့် half-merged state မဖြစ်ပေါ်ပါ။

```python
def run_batches(chunks, fail_plan, checkpoint, graph, batch_size=2, max_attempts=3):
    # checkpoint[batch_id] = True once committed; graph = triple_key -> record
    # fail_plan = {(batch_id, attempt)}; a planned hit aborts BEFORE any write,
    # so the retry re-runs the same unit and never half-writes it.
    ...
```

Determinism အတွက် backoff jitter ကို fixed-seed LCG ဖြင့် ထုတ်ရသည် (`random` module မသုံးရ)။

**ဘယ်အချိန် ဤအရာအားလုံး မလိုသင့်သလဲ** — chunk ရာဂဏန်း အောက်ရှိသော one-off run အတွက် checkpointing နှင့်
batching သည် မလိုအပ်သော complexity ဖြစ်သည်။

## Production Considerations

- Extraction quality ကို boundary-hit rate၊ per-chunk triple count၊ dedup ratio ဖြင့် monitor လုပ်ရမည်။
  Dedup ratio ရုတ်တရက် မြင့်တက်ပါက overlap များလွန်းနေကြောင်း ညွှန်ပြသည်။
- Chunk size ကို တိုင်းတာခန်းမှ ပြောင်းလဲပါက ရလဒ်တစ်ခုလုံး ပြောင်းလဲသဖြင့် pipeline version ကို
  chunking parameter နှင့်တွဲ၍ မှတ်ရမည်။
- Concurrency ကို တိုးပါက LLM rate limit နှင့် token cost ကို တိုက်ရိုက် သက်ရောက်သည်။ Retry သည်
  rate-limit error များအတွက် လိုအပ်သည်။
- Checkpoint store သည် crash-safe ဖြစ်ရမည် (atomic write) — write ပြီးမှ checkpoint သိမ်၊
  သို့မဟုတ် checkpoint တွင် batch hash ကို မှတ်၍ ပြန်စစ်ရမည်။

## Summary Checklist

- [ ] Chunk size ကို `context_window - instruction - schema - reserve` မှ တွက်ချက်ပြီး သတ်မှတ်ထားသည်
- [ ] Overlap သည် `0 <= overlap < size` ဖြစ်ပြီး stride ကို မှန်ကန်စွာ တွက်ထားသည်
- [ ] Map phase နှင့် reduce phase ကို သီးခြား၊ deterministic order ဖြင့် run ထားသည်
- [ ] Boundary ဖြတ်သော relationship များအတွက် reconnection ကို pattern A/B ဖြင့် ကိုင်တွယ်ထားသည်
- [ ] Triple deduplication key ကို normalize လုပ်ပြီး provenance ကို မဖျက်ဘဲ သိမ်းထားသည်
- [ ] Write သည် `MERGE` semantics ဖြစ်သဖြင့် Idempotency ရှိသည်
- [ ] Batch၊ checkpoint နှင့် retry ကို ထည့်သွင်းပြီး partial failure ကို ကာကွယ်ထားသည်
