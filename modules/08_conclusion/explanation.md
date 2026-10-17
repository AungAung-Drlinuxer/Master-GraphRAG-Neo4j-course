# M08 — Conclusion — အဓိက သဘောတရား ရှင်းလင်းချက်

Module ဤခုတွင် သဘောတရားအသစ် မဟုတ်ဘဲ၊ လေ့လာခဲ့သည့် အစိတ်အပိုင်းများကို production အခြေအနေ၊
ဆုံးဖြတ်ချက်၊ ဆက်လက်လေ့လာမှု ဟူသော ရှုထောင့်ဖြင့် ပြန်လည်စုစည်းသည်။ ဤ subtopic ခြောက်ခုသည်
module ၏ သင်ယူရလဒ်များကို တစ်စုတစ်စည်း ဖွဲ့စည်းပေးသည်။

---

## ၁။ Pipeline Recap — M00–M07 map

GraphRAG သည် module တစ်ခုတည်း၏ နည်းပညာ မဟုတ်ဘဲ stage တစ်ခုချင်းစီ၏ output သည် နောက် stage ၏ input
အဖြစ် တိကျစွာ ကတိပေးရသော pipeline တစ်ခု ဖြစ်သည်။ Stage contract မတိကျပါက quality ပြဿနာသည်
အဆုံးတွင် answer ရှိလာသည့်အခါမှ ပေါ်ပေါ်လာပြီး root cause ကို ရှာရ ခက်သည်။

| Stage | Module | Input → Output |
|---|---|---|
| ingest | M00, M04 | raw files → corpus text |
| normalize | M04 | corpus text → normalized text (unicode၊ whitespace၊ encoding) |
| chunk | M03 | normalized text → chunk list (chunk_id၊ text၊ offset) |
| extract | M01, M02 | chunk → raw Triple list (SPO + source chunk_id) |
| resolve | M02 | surface forms → canonical Entity name |
| merge_dedup | M03, M04 | raw triples → deduplicated triples + provenance |
| graph_write | M05, M06 | triples → Neo4j graph (`MERGE`၊ `UNWIND`) |
| entity_link | M07 | question text → anchor Node list |
| retrieve | M07 | anchor + k → subgraph (nodes + Relationship) |
| serialize | M07 | subgraph → Prompt context |
| generate | M07 | question + context → answer |

Stage ordering သည် dependency ပေါ်တွင် အခြေခံသည် — `retrieve` သည် `entity_link` နှင့် `graph_write`
နှစ်ခုလုံး ပြီးမှ စတင်နိုင်သည်၊ သို့သော် ingestion-side stage များနှင့် retrieval-side stage များသည်
တစ်ခုနှင့်တစ်ခု ချက်ချင်း မှီခိုခြင်း မရှိသည်ကို သတိထားရမည်။ ဤအချက်သည် incremental update ၏
အခြေခံ ဖြစ်သည် — graph ကို ပြန်မတည်ဆောက်ဘဲ retrieval side ကို အမြဲ အလုပ်လုပ်နေစေနိုင်သည်။

---

## ၂။ Production Cost Model

Ingestion Cost ကို တွက်ချက်နိုင်သော formula ဖြင့် ခန့်မှန်းရမည်။ ခန့်မှန်းနည်းမရှိပါက budget breakdown
သည် အသုံးမပြုနိုင်သော နံပါတ်များ အစုအဝေး ဖြစ်လာသည်။

```
chunks          = ceil(corpus_chars / chunk_chars)
chunk_tokens    = ceil(chunk_chars / CHARS_PER_TOKEN)      # ခန့်မှန်း 4 chars = 1 token
input_tokens    = chunks * (prompt_overhead_tokens + chunk_tokens)
output_tokens   = chunks * triples_per_chunk * tokens_per_triple
cost_usd        = (input_tokens / 1000) * price_in_per_1k
                + (output_tokens / 1000) * price_out_per_1k
```

Model ဤခုက ထင်ရှားသော သက်ရောက်မှု သုံးခုကို ဖော်ပြသည်။ ပထမ — Cost သည် corpus size နှင့်
linear တိုးသည်၊ ထို့ကြောင့် corpus နှစ်ဆ ဖြစ်ပါက Cost လည်း အတိအကျ နှစ်ဆ ဖြစ်သည်။ ဒုတိယ —
`prompt_overhead_tokens` သည် chunk တိုင်းတွင် ထပ်ကျခံရသည့် fixed cost ဖြစ်သည်၊ chunk ကို
သေးလွန်းခွဲပါက ဤ overhead သည် စုစုပေါင်း Cost ၏ အဓိက အစိတ်အပိုင်း ဖြစ်လာသည်။ တတိယ —
output token သည် extraction မှ triple မည်မျှ ထွက်သည် ဆိုသည်နှင့် တိုက်ရိုက် အချိုးကျသည်၊
ထို့ကြောင့် extraction prompt ကို ရှည်လျားစွာ ရေးခြင်းသည် output Cost ကို တိုးစေသည်။

Model ကို ကုဒ်အဖြစ် တိကျစွာ ရေးသည့်အခါ —

```python
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
```

`chunk_chars=2000`၊ `prompt_overhead_tokens=300`၊ `triples_per_chunk=8`၊ `tokens_per_triple=30`၊
`price_in_per_1k=0.5`၊ `price_out_per_1k=1.5` ဖြင့် 48000 chars corpus တစ်ခုအတွက်
chunk 24 ခု၊ input token 19200၊ output token 5760၊ Cost `$18.24` ထွက်သည်။

**Trade-off** — chunk ကို ကြီးစေပါက chunk count ကျပြီး overhead Cost ကျသော်လည်း၊ chunk တစ်ခုတွင်
entity များသည်း၍ extraction recall ကျနိုင်သည်။ ထို့ကြောင့် chunk size ကို Cost ဖြင့်သာ
မဆုံးဖြတ်ရ၊ M03 ၏ extraction quality ရလဒ်နှင့် တွဲဖက်ဆုံးဖြတ်ရမည်။

---

## ၃။ Latency Model — ingestion latency နှင့် query latency

Latency ကို ingestion-side နှင့် query-side ဟူ၍ ခွဲ၍ တိုင်းတာရမည်။ နှစ်ခုကို ပေါင်းပြီး ကြည့်ပါက
optimize လုပ်ရမည့် နေရာကို မမြင်ရ။

- Ingestion latency သည် chunk count နှင့် တိုက်ရိုက် အချိုးကျသည်၊ parallel worker အရေအတွက်ဖြင့်
  စားနိုင်သည် — worker 4 မှ 8 သို့ တိုးပါက parallel latency သည် ထက်ဝက် ဖြစ်သည်။
- Query latency သည် entity linking + k-hop traversal + generation ဖြင့် ဖွဲ့စည်းသည်။ In-memory
  traversal သည် node/Relationship အရေအတွက်အပေါ် မှီခိုသော်လည်း millisecond scale သာ ဖြစ်သည်၊
  စစ်မှန်သော ကုန်ကျစရိတ်သည် generation token အရေအတွက် ဖြစ်သည်။

Query-side model ကို ရေးသည့်အခါ —

```python
def retrieval_latency_ms(nodes_scanned, edges_scanned, generation_tokens,
                         generation_tokens_per_second):
    traversal_ms = 4.0 + nodes_scanned * 0.05 + edges_scanned * 0.02
    generation_ms = generation_tokens / generation_tokens_per_second * 1000.0
    return traversal_ms, generation_ms, traversal_ms + generation_ms
```

node 6၊ Relationship 5၊ generation token 80၊ second တစ်ခုလျှင် token 40 ဖြင့် traversal `4.40 ms` နှင့်
total `2004.40 ms` ထွက်သည်။ ဤအချက်က အဓိက engineering လမ်းညွှန်ချက်ကို ပေးသည် — query latency
optimize လုပ်ရန် context ကို တိုလုပ်ရမည်၊ traversal ကို ချုံ့ရန် မလိုအပ်။

**Trade-off** — k ကို တိုးပါက recall တိုးသော်လည်း context token တိုးပြီး query latency နှင့် Cost
နှစ်ခုလုံး တိုးသည်။ ထို့ကြောင့် k ကို empirical အားဖြင့် ဆုံးဖြတ်ရမည်၊ default အဖြစ် မသတ်မှတ်ရ။

---

## ၄။ Incremental Graph Update

Corpus အသစ် ဝင်လာတိုင်း graph တစ်ခုလုံးကို ပြန်တည်ဆောက်ခြင်းသည် Cost ကို နေ့စဉ် အပြည့်
ကြေးဆပ်ခြင်း ဖြစ်သည်။ Diff-based incremental update သည် အသစ်ဝင်လာသော document မှ triples ကို
ရှိပြီးသား graph နှင့် နှိုင်းယှဉ်၍ operation အနည်းငယ်သာ ရေးသည်။

Operation အမျိုးအစားများ —

- `ADD_NODE` — canonical name အသစ် ပေါ်လာခြင်း
- `ADD_EDGE` — Triple အသစ် (ရှိပြီးသား duplicate ဖြစ်ပါက `NOOP`)
- `DELETE_EDGE` — single-valued Relationship အတွက် အဟောင်း Relationship ဖယ်ရှားခြင်း
- `NOOP` — idempotent ဖြစ်ကြောင်း အထောက်အထား

Idempotency ကို verification လုပ်သည့် နည်းလမ်းမှာ document အသစ်တစ်ခုကို နှစ်ခါ ingest လုပ်ပြီး
graph ၏ content hash ကို နှိုင်းယှဉ်ခြင်း ဖြစ်သည်။ ဒုတိယအကြိမ်တွင် plan သည် `NOOP` သာ ပါရမည်။

```python
def graph_signature(edges, nodes):
    payload = json.dumps({"nodes": sorted(nodes), "edges": sorted(edges)}, sort_keys=True)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()[:16]
```

**Trade-off** — incremental update သည် Cost ကို လျှော့သော်လည်း stale Relationship ကို ရှာထုတ်ရန်
provenance နှင့် single-valued relation စာရင်း လိုအပ်သည်။ M04 ၏ provenance tracking မရှိပါက
"ဤ Triple သည် မည်သည့် document မှ လာသည်၊ ယခု အနုတ်လက္ခဏာ ဖြစ်ပြီလား" ကို ပြန်မဖြေနိုင်တော့ဘဲ
incremental update သည် အလုပ်မဖြစ်။

---

## ၅။ Monitoring — မဖြစ်မနေ တိုင်းတာရမည့် signal များ

Monitoring မရှိသော GraphRAG system သည် quality ကျဆင်းမှုကို အသုံးပြုသူ ညည်းညူမှ သိသည်။
Signal များကို layer လိုက် တိုင်းတာရမည်။

| Layer | Signal | Alert ဖြစ်သည့် အခြေအနေ |
|---|---|---|
| Extraction | triple per chunk၊ schema violation rate | schema violation သုည မဟုတ်ခြင်း |
| Graph | orphan node အရေအတွက်၊ duplicate entity rate | duplicate rate ကျဆင်းခြင်း |
| Retrieval | anchor hit rate၊ empty-subgraph rate | empty subgraph rate တိုးခြင်း |
| Answer | groundedness၊ citation missing rate | answer တွင် provenance မပါခြင်း |
| Cost | corpus char တစ်ခုလျှင် USD | budget သတ်မှတ်ချက် ကျော်လွန်ခြင်း |
| Latency | p95 query latency၊ p95 ingestion latency | SLO ကျော်လွန်ခြင်း |

**Trade-off** — signal တိုင်း တိုင်းတာခြင်းသည် overhead နှင့် storage ကုန်ကျသည်၊ ထို့ကြောင့်
critical path ပေါ်ရှိ signal (anchor hit rate၊ empty-subgraph rate၊ provenance missing rate)
ကို ဦးစားပေးတိုင်းတာပြီး၊ အခြားအရာများကို နမူနာအခြေခံ sample အဖြစ် တိုင်းတာရမည်။

---

## ၆။ GraphRAG သုံးသင့် / မသုံးသင့် ဆုံးဖြတ်သည့် Decision Criteria

GraphRAG သည် ချဉ်းကပ်နည်းအားလုံးထက် ကောင်းသည် မဟုတ်။ Ingestion Cost ကို ကြိုတင်ဆပ်ပြီး
retrieval အချိန်တွင် multi-hop reasoning ကို ရိုင်းစိုင်းစွာ ရယူသည့် ရင်းနှီးမြှုပ်နှံမှု ဖြစ်သည်။
ထို့ကြောင့် သုံးသင့်သည် / မသုံးသင့်သည် ကို ကိုယ်ပိုင်စာသားဖြင့် မဆုံးဖြတ်ရ၊ criteria ခြောက်ခုဖြင့်
ဆုံးဖြတ်ရမည်။

**သုံးသင့်သည့် အခြေအနေ**

1. Question များသည် Entity အဆက်အစပ် လိုအပ်သည် — "ဘယ်သူက ဘယ် team မှတဆင့် ဘယ် service ကို
   ထိခိုက်သည်" ကဲ့သို့ 2-hop အထက် လိုသော question။
2. Corpus သည် shared Entity အမည်များကို အများအပြား ထပ်နေပြီး chunk တစ်ခုတည်းတွင် အဖြေ
   မပြည့်စုံခြင်း။
3. Global summarization လိုအပ်၍ community-summary retrieval ကို ထည့်လိုခြင်း။
4. Retrieval တိုင်းတွင် provenance ပြန်လည်ပြရန် လိုအပ်ခြင်း (compliance၊ audit)။
5. Entity အမျိုးအစားနှင့် Relationship type ကို schema အဖြစ် ကြိုတင်သတ်မှတ်နိုင်ခြင်း။
6. Retrieval quality ကို Baseline နှင့် နှိုင်းယှဉ်တိုင်းတာနိုင်သော evaluation set ရှိခြင်း။

**မသုံးသင့်သည့် အခြေအနေ**

1. Question များအားလုံးနီးပါး single-chunk factoid ဖြစ်သည် — Vector Search တစ်ခုတည်းဖြင့် ဖြေနိုင်သည်။
2. Corpus သည် ရက်ပိုင်းအတွင်း ပြောင်းလဲနေပြီး ingestion latency ကို လက်မခံနိုင်ခြင်း။
3. Extraction quality ကို မတိုင်းတာနိုင်သေးဘဲ graph သည် "မသေချာသော" Triple များဖြင့် ပြည့်နေခြင်း —
   ဤအခြေအနေတွင် GraphRAG သည် baseline ထက် ပိုမှားနိုင်သည်။
4. Budget သုညနီးပါး ဖြစ်ပြီး ingestion Cost မရှိခြင်း။

ဆုံးဖြတ်ချက်ကို weight ဖြင့် တွက်သည့်အခါ အချက်နှစ်ချက် ထင်ရှားသည်။ ပထမ —
weight ပြောင်းလိုက်ခြင်းဖြင့် ဆုံးဖြတ်ချက် ပြောင်းနိုင်သည်၊ ထို့ကြောင့် weight ကို
အဖွဲ့အစည်း၏ အစစ်အမှန် ဦးစားပေးအလိုက် ချိန်ရမည်။ ဒုတိယ — "build" နှင့် "buy" ဆိုသည့်
ရွေးချယ်မှုနှစ်ခုလည်း ရှိသည်၊ GraphRAG အတွက် build ဆုံးဖြတ်ချက်သည် engineering capacity နှင့်
တိုက်ရိုက် ဆက်စပ်သည်။

```python
def weighted_score(scores, weights):
    assert abs(sum(weights.values()) - 1.0) < 1e-9, "weights must sum to 1.0"
    return sum(scores[key] * weight for key, weight in weights.items())
```

**Baseline မရှိပါက ဤဆုံးဖြတ်ချက် အားလုံး အဓိပ္ပာယ် မရှိ။** Vector-only retrieval ကို Baseline
အဖြစ် ထားပြီး ကိုယ့် evaluation question set ပေါ်တွင် Precision/Recall နှင့် Cost/Latency ကို
နှစ်ဖက်လုံး တိုင်းတာရမည်။ GraphRAG သည် Baseline ကို retrieval quality အားဖြင့် ကျော်ပြီး၊
တိုးလာသည့် Cost/Latency ကို အဖွဲ့အစည်း လက်ခံနိုင်မှသာ တန်ဖိုးရှိသည်။

---

## ၇။ ဆက်လက်လေ့လာရန် လမ်းကြောင်းများ နှင့် Capstone

**Ontology** — Schema ကို class နှင့် property အဆင့်သို့ တင်ပြီး inference rule ဖြင့် Triple အသစ်
ကောက်ချက်ချနိုင်သည်။ Relationship type ကို လွတ်လပ်စွာ ထည့်နေသည့် project များအတွက် graph ကို
တည်ငြိမ်စေသည်။ စတင်ရန် — OWL 2 overview နှင့် Neo4j semantic layer pattern များ။

**Graph Neural Network** — node embedding ကို graph structure မှ သင်ယူပြီး Vector Search ကို
graph-aware ဖြစ်စေသည်။ Entity resolution ကို pairwise similarity learning အဖြစ် ဖော်နိုင်သည်။
စတင်ရန် — PyTorch Geometric နှင့် Open Graph Benchmark။

**Agentic RAG** — Retrieval တစ်ခုတည်း မဟုတ်ဘဲ agent သည် retrieve → inspect → re-query လုပ်သည်။
GraphRAG ၏ tool (entity lookup၊ k-hop၊ Text-to-Cypher) များသည် agent ၏ tool set ဖြစ်လာသည်။
Guardrail သည် ပို၍ အရေးကြီးလာသည် — destructive Cypher clause များကို block လုပ်ရမည်။

**Evaluation framework** — RAGAS ကဲ့သို့ framework ဖြင့် faithfulness၊ answer relevance၊
context precision ကို စံချိန်တင်တိုင်းတာနိုင်သည်။ GraphRAG အတွက် graph-specific metric
(anchor hit rate၊ empty-subgraph rate၊ hop coverage) ကို ကိုယ်တိုင် ထည့်ရမည်။

**Capstone design exercise** — ကိုယ်ပိုင် corpus တစ်ခုကို ရွေးပြီး အောက်ပါ မေးခွန်းများကို
စာဖြင့် ဖြေရမည် —

1. Corpus size၊ update frequency၊ Entity type နှင့် Relationship type စာရင်း
2. Extraction ကို scripted/LLM မည်သည့်နည်းဖြင့် လုပ်မည်၊ chunk size နှင့် overlap ရွေးချယ်မှု
3. Node label၊ Relationship type၊ uniqueness constraint နှင့် index ဒီဇိုင်း
4. Retrieval pattern — entity-anchored subgraph၊ Text-to-Cypher၊ community-summary မည်သည့်ကို
   ဘယ် question အမျိုးအစားအတွက် သုံးမည်
5. Incremental update strategy နှင့် provenance schema
6. Evaluation set၊ Baseline၊ အောင်မြင်မှု တိုင်းတာသည့် metric နှင့် သတ်မှတ်ချက်
7. Cost/Latency ခန့်မှန်းချက်နှင့် build-vs-buy ဆုံးဖြတ်ချက်

**Course wrap-up** — ဤ course ၏ file အားလုံးသည် `modules/<module_name>/` အောက်တွင် ရှိသည်။
Module တိုင်းတွင် `README.md`၊ `explanation.md`၊ `exercise.md`၊ `solution.md`၊ `lab.py` ဟူသော
file ငါးခု အတိအကျ ရှိသည်။ Lab တိုင်းကို —

```bash
python3 modules/08_conclusion/lab.py
```

ကဲ့သို့ working directory ကို repository root မှ ထားပြီး run နိုင်သည်။ Lab များသည် Neo4j server
မလိုဘဲ run နိုင်သည်၊ Neo4j driver လိုအပ်သော code ကို `lab.py` အတွင်း မထည့်ရ။

---

## Summary Checklist

- [ ] M00–M07 ကို stage contract အဖြစ် (input → output) ဖော်ပြနိုင်သည်
- [ ] Cost formula ဖြင့် corpus တစ်ခုအတွက် ingestion Cost ကို တွက်နိုင်သည်
- [ ] Ingestion latency နှင့် query latency ကို သီးခြား တိုင်းတာနိုင်သည်
- [ ] Incremental update plan (`ADD_NODE`၊ `ADD_EDGE`၊ `DELETE_EDGE`၊ `NOOP`) ကို ရေးနိုင်သည်
- [ ] Re-ingestion ပြီးနောက် graph signature မပြောင်းကြောင်း သက်သေပြနိုင်သည်
- [ ] Extraction၊ graph၊ retrieval၊ Cost၊ Latency layer အလိုက် monitoring signal ရွေးနိုင်သည်
- [ ] GraphRAG သုံးသင့်/မသုံးသင့် criteria ဖြင့် ဆုံးဖြတ်နိုင်ပြီး Baseline နှင့် နှိုင်းယှဉ်နိုင်သည်
- [ ] ကိုယ်ပိုင် corpus အတွက် Capstone design ကို အပိုင်း ၇ ပိုင်းဖြင့် ရေးနိုင်သည်
