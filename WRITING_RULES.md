# WRITING_RULES.md — Course အရေးအသား စည်းမျဉ်းများ

ဤဖိုင်သည် `Master Knowledge Graph Retrieval-Augmented Generation with Neo4j` course တစ်ခုလုံးအတွက်
အရေးအသား၊ code နှင့် lab များ၏ တူညီသော စံနှုန်း (standard) ကို သတ်မှတ်သည်။ Module အသစ်တိုင်း
ရေးသားသည့်အခါ ဤစည်းမျဉ်းများကို မဖြစ်မနေ လိုက်နာရမည်။

---

## ၁။ ဘာသာစကားနှင့် အသံ (Language & Register)

1. Prose ကို **မြန်မာဘာသာဖြင့်** ရေးသားရမည်။
2. Technical term များကို **မြန်မာလို တိုက်ရိုက် မပြန်ဆိုရ**။ English အတိုင်း inline ထည့်ရမည်။
   - မှန် — `Entity resolution သည် duplicate nodes များကို ပေါင်းစည်းပေးသည်။`
   - မှား — `အရာဝတ္ထုဖြေရှင်းခြင်းသည် ထပ်နေသော အမှတ်များကို ပေါင်းစည်းပေးသည်။`
3. ထိန်းသိမ်းရမည့် term များ (ဥပမာ — ဤစာရင်းသည် အပြည့်အစုံ မဟုတ်) —
   `Knowledge Graph`, `GraphRAG`, `RAG`, `Neo4j`, `Cypher`, `Property Graph`, `Node`, `Edge`,
   `Entity`, `Relationship`, `Triple`, `Chunk`, `Embedding`, `Vector Search`, `Retrieval`,
   `Prompt`, `Token`, `Context Window`, `Entity Resolution`, `Coreference`, `Schema`,
   `Ingestion`, `Pipeline`, `Idempotency`, `Community Detection`, `Index`, `Query`,
   `LLM`, `Transformer`, `NER`, `SpaCy`, `ALIAS`, `Mutation`, `Traversal`, `Hop`.
4. **စကားပြော particle များ လုံးဝ မသုံးရ** — `နော်`, `လေး`, `ရတယ်နော်`, `မမေ့ပါနဲ့`, `ဖြူစင်တယ်`,
   `ဟုတ်လား`, `ပါလား`, `အားနာ`, `ကြမ်းတမ်း`, `တစိုက်ရိုက်`။
5. Engineering register သုံးရမည် — declarative၊ တိုတိုရှင်းရှင်း၊ အကြောင်းရင်း (rationale) ကို ရှေ့တန်းတင်ပြရမည်။
   "ဒါက ခက်တယ်" မဟုတ်၊ **"ဤချဉ်းကပ်နည်းသည် recall ကို မြှင့်ပေမဲ့ ingestion latency ကို နှစ်ဆ တိုးစေသည်"**
   ကဲ့သို့ တိုင်းတာနိုင်သော ဖော်ပြချက် ဖြစ်ရမည်။
6. Programming အခြေခံသဘောတရားများ (dict, list, function, loop, string ဆိုတာ ဘာလဲ) ကို
   **ရှင်းပြရန် မလိုအပ်**။ Reader သည် engineer တစ်ယောက် ဖြစ်သည်ဟု ယူဆရမည်။
7. နည်းပညာ ဆိုင်ရာ ခေါင်းစဉ်တိုင်းတွင် **ဘာကြောင့် ဤနည်းလမ်း ဖြစ်သနည်း** ဆိုသော engineering rationale
   နှင့် **ဘယ်အချိန်တွင် မသုံးသင့်သနည်း** ဆိုသော trade-off ကို ထည့်သွင်းရမည်။

---

## ၂။ Module file ဖွဲ့စည်းပုံ (အတိအကျ)

Module directory တိုင်းတွင် file **၅ ခု** အတိအကျ ရှိရမည်။ file အမည်များ ပြောင်းလဲခွင့် မရှိ။

| File | ရည်ရွယ်ချက် | ပမာဏ (target) |
|---|---|---|
| `README.md` | Module scope၊ learning objectives၊ file structure၊ prerequisites၊ production use cases၊ references | 40–60 lines |
| `explanation.md` | အဓိက သဘောတရားရှင်းလင်းချက်၊ subtitle များ၊ formula၊ deterministic code example၊ production considerations၊ Summary Checklist | 180–280 lines |
| `exercise.md` | ကိုယ်တိုင် implement လုပ်ရမည့် လေ့ကျင့်ခန်း ၆ ခု — တစ်ခုစီတွင် လုပ်ငန်း၊ `**Hints:**`၊ `**Expected behavior:**` | 50–80 lines |
| `solution.md` | Exercise တိုင်းအတွက် reference implementation (full code) + `**အဓိကအယူအဆ**` ရှင်းလင်းချက် | 200–300 lines |
| `lab.py` | Standard library သာ သုံး၍ run နိုင်သော executable lab (exercise ၆ ခုလုံး၊ `assert` ဖြင့် စစ်ဆေး) | 180–280 lines |

### README.md — မဖြစ်မနေ ပါရမည့် အပိုင်းများ

```
# M<နံပါတ်> — <Module ခေါင်းစဉ်>

<intro paragraph — module က ဘာကို ဖြေရှင်းပေးသည်>

## သင်ယူလေ့လာမည့် အကြောင်းအရာများ
## Module အစိတ်အပိုင်းများ        <- file ၅ ခု table + explanation.md subtopic list
## Prerequisites
## Production Use Cases
## References                    <- တကယ်ရှိသော official docs URL များသာ
```

`lessons/` သို့မဟုတ် အခြား **မရှိသော file များကို ရည်ညွှန်း ရေးသားခြင်း လုံးဝ မပြုရ**။

### `exercise.md` — ခေါင်းစဉ် format (အတိအကျ)

လေ့ကျင့်ခန်း ခေါင်းစဉ်တိုင်းသည် အောက်ပါ format အတိုင်း ဖြစ်ရမည် (module တစ်ခုလုံးတွင် တူညီရမည်) —

```
## Exercise 1 — <ခေါင်းစဉ်>
## Exercise 2 — <ခေါင်းစဉ်>
...
## Exercise 6 — <ခေါင်းစဉ်>
```

- ခေါင်းစဉ်အဆင့်မှာ `##` (H2) ဖြစ်ရမည်။
- နံပါတ်နှင့် ခေါင်းစဉ်အကြား separator မှာ em dash (` — `) ဖြစ်ရမည် (`:` သုံးခွင့် မရှိ)။
- ဤ H2 ၆ ခုသည် `lab.py` ရှိ `def exercise_1()` … `def exercise_6()` နှင့် တစ်လုံးချင်း ကိုက်ညီရမည်။

---

## ၃။ Code Block စည်းမျဉ်းများ

1. Code block တိုင်းတွင် language tag ထည့်ရမည် (```python, ```cypher, ```sql, ```json, ```bash)။
2. Code သည် **ကိုယ်တိုင် run စမ်းပြီး ရရှိသော output အပေါ် အခြေခံရမည်**။ ဖန်တီး (fabricate) ခြင်း မပြုရ။
3. `# Expected output:` comment ထည့်သည့်အခါ **တကယ် ရရှိသော output အတိအကျ** ဖြစ်ရမည်။
4. Code block များကို `solution.md` နှင့် `lab.py` အကြား **တူညီအောင်** ထားရမည် (algorithm အတူ၊
   lab.py တွင် `assert` နှင့် `print` ပိုထည့်နိုင်)။
5. External package လိုအပ်သော code (ဥပမာ `neo4j` driver) ကို `lab.py` အတွင်း မထည့်ရ။
   ထို code များကို `live_neo4j_test.py` (optional) ထဲတွင်သာ ထည့်ရမည်။

---

## ၄။ Lab စည်းမျဉ်းများ (`lab.py`)

1. **Python standard library သာ** — `re`, `json`, `hashlib`, `math`, `collections`, `itertools`,
   `unicodedata`, `dataclasses`, `difflib`, `statistics`, `textwrap` စသည်။
   `numpy`, `pandas`, `networkx`, `neo4j`, `requests` စသည့် external package များ **မသုံးရ**။
2. **Deterministic** ဖြစ်ရမည် — `random` မသုံးရ (လိုအပ်ပါက fixed-seed LCG ကို ကိုယ်တိုင်
   implement လုပ်ပါ)၊ system clock ပေါ် မမှီခိုရ။ run တိုင်း output တူရမည်။
3. **Offline** — network access လုံးဝ မပြုရ။
4. `def exercise_1() -> bool:` … `def exercise_6() -> bool:` ပုံစံ အတိအကျ သုံးရမည်။
5. Exercise တိုင်း —
   - `print("\n--- Exercise N: <ခေါင်းစဉ်> ---")` ဖြင့် စရမည်
   - ရလဒ်များကို `print` ဖြင့် ပြရမည် (ဆုံးဖြတ်ချက်များကို မျက်စိဖြင့် တွေ့နိုင်ရမည်)
   - **`assert` ဖြင့် စစ်ဆေးရမည်** — မှားပါက `AssertionError` ဖြင့် ကျရှုံးရမည်
   - အောင်မြင်ပါက `True` return ပြန်ရမည်
6. ဖိုင်အဆုံးတွင် `run_all()` နှင့် —
   ```python
   if __name__ == "__main__":
       sys.exit(0 if run_all() else 1)
   ```
7. အောင်မြင်ပါက နောက်ဆုံး လိုင်းတွင် `[PASS] All 6/6 exercises passed successfully.` ကို print ရမည်။
8. **တင်ပြီးမီ** `python3 modules/<module>/lab.py` ကို run ၍ `exit 0` ဖြစ်ကြောင်း အတည်ပြုရမည်။

---

## ၅။ Neo4j နှင့် ပတ်သက်သော Module များအတွက် အပိုစည်းမျဉ်း

1. `lab.py` သည် Neo4j server မလိုဘဲ run နိုင်ရမည် — Cypher statement generation၊ in-memory graph
   traversal၊ query validation များကို Python ဖြင့် simulate လုပ်ရမည်။
2. Cypher code block များကို ```cypher fence ဖြင့် ရေးရမည်။ **Cypher syntax မှန်ကန်ရမည်** —
   `MERGE (n:Label {id: $id})`၊ `MATCH (a)-[:REL]->(b)`၊ parameter သုံးရမည် (`$param`)။
3. Neo4j version အပေါ် မှီခိုသော claim များ (ဥပမာ `$param` အစား `{param}` သုံးသော version များ)
   ရေးသားပါက version ကို တိကျစွာ ဖော်ပြရမည်။
4. Constraint၊ index၊ multi-tenancy pattern များတွင် **security ဆိုင်ရာ သတိပေးချက်** ထည့်ရမည်
   (ဥပမာ Text-to-Cypher တွင် destructive clause များကို block လုပ်ခြင်း)။

---

## ၆။ Walkthrough ဖိုင်များ (`walkthroughs/` — optional)

`solution.md` ရှိ code ကို **Python အခြေခံမှ စတင်၍** လိုင်းတစ်လိုင်းချင်း ရှင်းပြသည့် ဖတ်စာ
အပိုဖြစ်သည်။ Module တိုင်းတွင် မဖြစ်မနေ မလိုအပ် — exercise တစ်ခုအတွက် ရေးသားလိုပါက —

1. နေရာ — `modules/<module>/walkthroughs/NN_<exercise_slug>.md` (NN သည် exercise နံပါတ်နှင့် ကိုက်ရမည်)။
2. Register — ဤဖိုင်များသည် `explanation.md` ၏ "basic concept မရှင်းပြရ" စည်းမျဉ်းမှ **ကင်းလွတ်သည်**။
   ဤနေရာတွင် dictionary၊ tuple၊ set၊ loop၊ list comprehension၊ `all()`, `assert` စသည့်
   Python concept များကို **ရှင်းပြရမည်** — ဖတ်သူသည် ထို exercise ကို ပထမဆုံး ဖတ်သူ ဖြစ်သည်။
3. ဖွဲ့စည်းပုံ — (က) code က ဘာကို ဖြေရှင်းပေးသည်၊ (ခ) ဤ code တွင် လေ့လာရမည့် Python concepts စာရင်း၊
   (ဂ) နောက်ခံသဘောတရား (ဥပမာ pipeline၊ dependency)၊ (ဃ) code ကို အပိုင်းလိုက် — အပိုင်းတိုင်းတွင်
   **code block → ရှင်းလင်းချက် → ဥပမာ → output**၊ (င) loop/progress table၊ (ဆ) ကိုယ်တိုင်လေ့ကျင့်ရန်
   မေးခွန်း + အဖြေ (`<details>` block ဖြင့် ဖုံးထားနိုင်သည်)။
4. **Code snippet တိုင်းသည် တကယ် run နိုင်ရမည် သို့မဟုတ် run နိုင်သော snippet တစ်ခုမှ ကောက်ထုတ်ထားသည်
   ဖြစ်ရမည်။** Function ကို အပိုင်းလိုက် ရှင်းပြပါက အစိတ်အပိုင်းအားလုံး ပေါင်းစည်းထားသော
   **runnable version တစ်ခုကို အဆုံးတွင် ထည့်ပြီး ထို script ကို run ၍ ရလဒ်ကို စစ်ဆေးရမည်** —
   ခေါင်းစီး + docstring သာ ပြထားသော function block သည် `None` ပြန်သဖြင့် ဖတ်သူ run ကြည့်ပါက
   ဖော်ပြထားသော output မရနိုင်ပါ။
5. ဖော်ပြထားသော output တိုင်းသည် run ရလဒ်နှင့် ကိုက်ရမည်။ `set` ၏ ပြသအစီအစဉ်ကဲ့သို့
   run တစ်ခုနှင့်တစ်ခု ကွဲနိုင်သော output များအတွက် သတိပေးချက် comment ထည့်ရမည်။
6. Module ၏ `README.md` တွင် walkthrough ရှိကြောင်း ဖော်ပြပြီး ဇယားတစ်ခုဖြင့်
   walkthrough ↔ exercise ကို ချိတ်ဆက်ရမည်။

---

## ၇။ စစ်ဆေးရမည့် အချက်များ (Self-check — module တစ်ခု ပြီးတိုင်း)

- [ ] file ၅ ခု အတိအကျ ရှိပြီး အမည် မှန်ကန်သည်
- [ ] `README.md` ထဲတွင် မရှိသော file ကို ရည်ညွှန်းထားခြင်း မရှိ
- [ ] `explanation.md` တွင် subtopic ၅–၆ ခု၊ တစ်ခုစီတွင် engineering rationale ပါသည်
- [ ] `exercise.md` တွင် လေ့ကျင့်ခန်း ၆ ခု၊ တစ်ခုစီတွင် Hints + Expected behavior ပါသည်
- [ ] `solution.md` code block များသည် `lab.py` နှင့် algorithm အရ ကိုက်ညီသည်
- [ ] `lab.py` တွင် external import မရှိ၊ `random` မသုံး၊ network call မရှိ
- [ ] `python3 modules/<module>/lab.py` → `exit 0` နှင့် `[PASS] All 6/6 exercises passed successfully.`
- [ ] စကားပြော particle (`နော်`, `လေး`, `မမေ့ပါနဲ့`, `အားနာ`) မပါရှိ
- [ ] technical term များကို မြန်မာလို တိုက်ရိုက် မပြန်ထားခြင်း
