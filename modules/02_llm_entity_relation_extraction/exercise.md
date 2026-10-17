# M02 — Exercise များ

Exercise တိုင်းကို `lab.py` အတွင်း implement လုပ်ပြီး `python3 modules/02_llm_entity_relation_extraction/lab.py`
ဖြင့် run ရသည်။ Lab သည် **offline နှင့် deterministic** ဖြစ်ရမည် — LLM API ခေါ်ခြင်း၊ `random` သုံးခြင်း
လုံးဝ မပြုရ။ Model output ကို scripted mock (`MOCK_LLM_RESPONSES`) အဖြစ် သတ်မှတ်ပြီး real parsing /
validation / resolution / filtering logic ကိုသာ ရေးရသည်။

---

## Exercise 1 — Extraction prompt template

**လုပ်ငန်း:** Entity type list၊ relationship type list၊ JSON Schema နှင့် delimited input text ပါဝင်သော
prompt template တစ်ခု တည်ဆောက်ပါ။ တူညီသော input အတွက် byte-identical prompt ထွက်ကြောင်း hash ဖြင့် စစ်ပါ။
Untrusted text အတွင်းရှိ prompt injection pattern များကို regex ဖြင့် flag လုပ်သည့် function ထည့်ပါ။

**Hints:**
- `json.dumps(EXTRACTION_SCHEMA, sort_keys=True)` ဖြင့် schema ကို deterministic ဖြစ်စေပါ
- Input ကို `<<<INPUT` … `INPUT>>>` delimiter အတွင်း ထည့်ပါ
- Pattern စာရင်းတွင် `ignore previous instructions`၊ `you are now`၊ `reveal the system prompt` ပါဝင်ပါစေ

**Expected behavior:** Prompt တွင် entity type ၄ ခုလုံးနှင့် relationship type ၄ ခုလုံး ပါရမည်။
`sha256` hash သည် နှစ်ကြိမ်ခေါ်ချက်တွင် တူရမည်။ Injection စာသားတွင် pattern ≥ ၂ ခု flag ဖြစ်ရမည်။

---

## Exercise 2 — Scripted LLM output ကို parse လုပ်ခြင်း

**လုပ်ငန်း:** Raw model output ကို parse လုပ်သည့် function ရေးပါ။ Code fence ဖယ်ခြင်း၊ trailing comma
repair လုပ်ခြင်း၊ နှင့် ပြန်မရနိုင်သော truncation ကို error အဖြစ် ပြန်ပေးခြင်း — ဤအခြေအနေ ၃ မျိုးကို
ကိုင်တွယ်ရမည်။

**Hints:**
- Code fence အတွက် `re.compile(r"```(?:json)?\s*(.*?)```", re.DOTALL)`
- Trailing comma အတွက် `re.sub(r",(\s*[}\]])", r"\1", text)`
- Repair တိုင်းကို `repairs` list ထဲ မှတ်တမ်းတင်ပါ, မှတ်တမ်းမတင်ဘဲ ဖျောက်ခြင်း မပြုရ

**Expected behavior:** Fence ပါသော response တွင် `repairs == ["stripped_code_fence"]`။ Trailing comma
ပါသော response တွင် `repairs == ["removed_trailing_comma"]`။ Truncated response တွင် payload `None`
ဖြစ်ပြီး error message သည် `JSONDecodeError` ဖြင့် စရမည်။

---

## Exercise 3 — JSON Schema validation နှင့် retry strategy

**လုပ်ငန်း:** `EXTRACTION_SCHEMA` ကို ဖြတ်သွားသော minimal validator (`object`၊ `array`၊ `string`၊
`required`၊ `enum`) ရေးပါ။ Parse + validate ကို ပေါင်းပြီး မအောင်မြင်ပါက mock output ကို `-retry`
key ဖြင့် တစ်ကြိမ် ပြန်ခေါ်သော bounded retry function ရေးပါ။

**Hints:**
- Error path ကို `$.entities[1].type` ကဲ့သို့ JSONPath ပုံစံဖြင့် ပြပါ
- Retry တွင် `MOCK_LLM_RESPONSES.get(f"{chunk_id}-retry")` ကို သုံးပါ; မရှိပါက `no_response` ဟု မှတ်တမ်းတင်ပါ
- `max_attempts` ကို parameter ဖြစ်စေပြီး ပြည့်သွားပါက `None` ပြန်ပေးပါ (ခန့်မှန်းဖြည့်ခြင်း မပြုရ)

**Expected behavior:** Clean payload တွင် error ၀ ခု။ Defective payload တွင်
`["$.entities[1].type: missing required field"]`။ Retry ပြီးနောက် payload ပြန်ရပြီး trace သည်
`[schema_error, ok]` ဖြစ်ရမည်။ Retry ကုန်သော chunk တွင် `None` ပြန်ရမည်။

---

## Exercise 4 — Entity resolution (alias + fuzzy matching)

**လုပ်ငန်း:** Surface form စာရင်း (name, type, frequency) ကို alias map ဖြင့် အရင် ပေါင်းပြီး၊ ကျန်သည်များကို
normalized `difflib.SequenceMatcher` ratio ≥ 0.85 ဖြင့် fuzzy match လုပ်သော resolver ရေးပါ။ Canonical
name ကို frequency အများဆုံးဖြင့် ရွေးပါ။

**Hints:**
- Normalization အစဉ် — `unicodedata.normalize("NFKC")` → `casefold()` → punctuation ဖြတ် → space စုစည်း
- Alias lookup ကို fuzzy matching အရင် လုပ်ပါ (precision ပိုမြင့်သည်)
- Canonical name ရွေးရာတွင် `max(names, key=lambda n: (freq, len(n), n))` ကဲ့သို့ deterministic tie-break သုံးပါ

**Expected behavior:** Surface form ၇ ခုမှ entity ၃ ခု ထွက်ရမည်။ `Neo4j Inc.` cluster တွင် form ၃ ခု၊
total frequency ၁၂။ `E. Eifrem` သည် alias ဖြင့် `Emil Eifrem` ထဲ ဝင်ရမည်။ `Sweeden` သည် fuzzy ဖြင့်
`Sweden` ထဲ ဝင်ရမည် (ratio ≈ 0.923)။

---

## Exercise 5 — Hallucination filter (grounding check)

**လုပ်ငန်း:** Extraction payload တစ်ခုကို source corpus သို့ ပြန်ညွှန်း၍ စစ်သော grounding filter ရေးပါ။
Gate ၂ ခု — (၁) entity surface form သည် corpus တွင် တွေ့ရသလား၊ (၂) relationship type သည် allowed
list အတွင်းရှိပြီး endpoint နှစ်ခုလုံး gate ၁ ကို ဖြတ်သလား။ ဖယ်ရှားခဲ့သော အကြောင်းရင်းကို ပြရမည်။

**Hints:**
- Corpus ကို normalize လုပ်ပြီး string တစ်ခုအဖြစ် သိမ်းပါ (substring attestation အတွက်)
- Drop reason ကို `type_not_allowed` / `endpoint_not_grounded` ဖြင့် ခွဲပါ
- Relationship precision = `kept_relationships / total_relationships` ကို တွက်ပြပါ

**Expected behavior:** Entities ၄ ခုထဲမှ `AthenaDB` ဖယ်ခံရမည်။ Relationships ၄ ခုထဲမှ
`(Neo4j Inc.)-[:PRODUCES]->(AthenaDB)` သည် `endpoint_not_grounded` ဖြင့် ဖယ်ခံရမည်။
Grounded relationship precision သည် 0.75 ဖြစ်ရမည်။

---

## Exercise 6 — Token cost နှင့် latency ခန့်မှန်းခြင်း

**လုပ်ငန်း:** Character အခြေခံ token estimator (~4 char/token)၊ prompt/output နှစ်မျိုးအတွက် cost model၊
နှင့် output token အပေါ် linear latency model တည်ဆောက်ပါ။ Chunk batch တစ်ခုအတွက် total cost၊ retry
overhead နှင့် total latency ကို print လုပ်ပါ။

**Hints:**
- `math.ceil(len(text) / 4)` သုံးပါ; `max(1, ...)` ဖြင့် ၀ မဖြစ်စေပါ
- Input/output အတွက် price ကို constant နှစ်ခုအဖြစ် ထားပါ (per 1M tokens)
- Latency ကို `base + output_tokens * ms_per_token` ဖြင့် model လုပ်ပါ

**Expected behavior:** `total_prompt_tokens > total_output_tokens`။ Cost > 0 ဖြစ်ပြီး retry overhead
> cost။ Batch latency သည် 1724 ms ဖြစ်ရမည်။

---

## Self-check

- [ ] LLM API ခေါ်ခြင်း၊ `random` သုံးခြင်း၊ network access မရှိ
- [ ] Exercise တိုင်းတွင် `print("\\n--- Exercise N: ... ---")` နှင့် `assert` ပါသည်
- [ ] `run_all()` နောက်ဆုံးတွင် `[PASS] All 6/6 exercises passed successfully.` ဖြစ်ပြီး exit code 0
