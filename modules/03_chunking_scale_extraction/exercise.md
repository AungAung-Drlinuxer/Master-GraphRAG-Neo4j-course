# M03 — Lab Exercises

`lab.py` အတွင်း `exercise_1()` … `exercise_6()` ကို implement လုပ်ပါ။ Exercise တိုင်းသည် မိမိရလဒ်ကို
`assert` ဖြင့် စစ်ဆေးရမည်။ ရည်ရွယ်ချက်မှာ chunking နှင့် scale engineering pattern များကို deterministic
ဖြစ်စေရန် ကိုယ်တိုင် ရေးသားခြင်း ဖြစ်သည်။

Fixture — token ၁၈ လုံးပါသော corpus:

```
Alpha acquired Beta . Beta operates Gamma . Gamma founded Delta .
Delta partners Epsilon . Epsilon supplies Zeta . Zeta acquired Alpha .
```

`VERBS = {acquired, operates, founded, partners, supplies}`,
`ENTITIES = {Alpha, Beta, Gamma, Delta, Epsilon, Zeta}`

## Exercise 1 — Fixed-size chunking

**လုပ်ငန်း:** `tokenize()` ဖြင့် corpus ကို word token အဖြစ် ခွဲပြီး `size=6`, `overlap=0` ဖြင့်
fixed-size chunk များ ဖန်တီးပါ။ Chunk အရေအတွက်၊ chunk size များနှင့် chunk တိုင်း၏ content ကို print ပါ။

**Hints:** `stride = size - overlap`။ Chunk အသစ်ကို `start + size >= n` ဖြစ်သည့်အခါ ထပ်မစရ။
punctuation ကို ဖယ်ရှားပါ (`re.findall(r"[A-Za-z]+", text)`)。

**Expected behavior:** token ၁၈ လုံး → chunk ၃ ခု၊ size တိုင်း ၆ လုံး၊ chunk 0 သည်
`Alpha acquired Beta Beta operates Gamma` ဖြစ်သည်။

## Exercise 2 — Overlap ထည့်ခြင်း

**လုပ်ငန်း:** `size=6` အတွက် `overlap=0` နှင့် `overlap=2` ကို နှိုင်းယှဉ်ပါ။ Boundary တိုင်းတွင် overlap
region နှစ်ဖက်တူညီကြောင်း စစ်ဆေးပါ။

**Hints:** `overlap=2` ဖြစ်ပါက `stride=4`။ Boundary တိုင်းအတွက်
`chunks[i][-overlap:] == chunks[i+1][:overlap]` ဖြစ်ရမည်။

**Expected behavior:** `overlap=0` → chunk ၃ ခု၊ `overlap=2` → chunk ၄ ခု (size တိုင်း ၆ လုံး)။
Overlap ကြောင့် chunk အရေအတွက် တိုးလာသည် (token ကုန်ကျစရိတ် တိုးသည်)။

## Exercise 3 — Map-Reduce triple aggregation

**လုပ်ငန်း:** Exercise 1 ၏ chunk များအပေါ် map phase (`extract_triples`) run ပြီး raw Triple record များကို
reduce phase (`merge_triples`) ဖြင့် စုစည်းပါ။ Per-chunk triple count နှင့် unique Triple အရေအတွက်ကို print ပါ။

**Hints:** Triple တစ်ခုကို ထုတ်ရန် subject/verb/object သုံးလုံးစလုံး chunk တစ်ခုတည်းအတွင်း ရှိရမည်။
Record တိုင်းတွင် source `chunk_hash` ထည့်ပါ။

**Expected behavior:** per-chunk counts `[2, 2, 2]` → raw record ၆ ခု → unique Triple ၆ ခု၊ freq တိုင်း ၁။

## Exercise 4 — Cross-chunk relationship ပြန်ချိတ်ခြင်း

**လုပ်ငန်း:** `size=5`, `overlap=0` ဖြင့် chunk ပါ။ Map phase မှ ဆုံးရှုံးသော Triple များကို
`reconnect_boundary_triples()` ဖြင့် ပြန်ရှာပါ။ mapped၊ recovered နှင့် combined unique အရေအတွက်ကို print ပါ။

**Hints:** Pattern A — ဘယ်ဘက် chunk သည် `subject + verb` ဖြင့် ဆုံးသည်။
Pattern B — ညာဘက် chunk သည် `verb + object` ဖြင့် စသည်။

**Expected behavior:** mapped ၄ ခု၊ recovered ၂ ခု (`Beta operates Gamma`, `Delta partners Epsilon`) →
combined unique ၆ ခု။

## Exercise 5 — Triple deduplication နှင့် merge

**လုပ်ငန်း:** `size=5`, `overlap=3` ဖြင့် chunk ပါ။ Raw record များကို `merge_triples()` ဖြင့် deduplicate
လုပ်ပြီး `freq`၊ `sources`၊ `confidence` ကို print ပါ။

**Hints:** Dedup key ကို case-fold ဖြင့် normalize ပါ (`triple_key`)။
`confidence = min(1.0, 0.5 + 0.25 * freq)`။

**Expected behavior:** raw record ၈ ခု → unique ၆ ခု။ `(Gamma, founded, Delta)` နှင့်
`(Epsilon, supplies, Zeta)` နှစ်ခုသည် freq ၂၊ confidence 1.0၊ sources ၂ ခု။

## Exercise 6 — Idempotent batch runner

**လုပ်ငန်း:** Exercise 5 ၏ chunk များကို `batch_size=2` ဖြင့် `run_batches()` ဖြင့် run ပါ။ `batch_2` ကို
attempt 1 တွင် scripted failure ပေးပြီး retry ဖြင့် အောင်မြင်ကြောင်း ပြပါ။ ထို့နောက် run နှစ်ကြိမ်မြောက်ကို
run ၍ Idempotency ကို စစ်ဆေးပါ။

**Hints:** `checkpoint[batch_id] = True` ကို batch commit ပြီးမှသာ သတ်မှတ်ပါ။ Run ၂ ကြိမ်မြောက်တွင် committed
batch အားလုံး `skip` ဖြစ်ရမည်။ Backoff jitter ကို fixed-seed LCG ဖြင့် ထုတ်ပါ။

**Expected behavior:** log တွင် `batch_2 -> retry` ပြီးနောက် `batch_2 -> done 2` ပါသည်။ Committed batch ၄ ခု၊
graph Triple ၆ ခု။ Run ၂ ကြိမ်မြောက် log သည် `skip` အားလုံးဖြစ်ပြီး graph snapshot မပြောင်းလဲ။
Retry headroom မလုံလောက်ပါက batch သည် uncommitted အဖြစ် ကျန်ပြီး partial write မဖြစ်ပေါ်ပါ။
