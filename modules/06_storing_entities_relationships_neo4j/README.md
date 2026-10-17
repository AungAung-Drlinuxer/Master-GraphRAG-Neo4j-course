# M06 — Storing LLM-extracted Entities and Relationships in Neo4j

M02–M04 မှ ထွက်လာသော Triple များသည် JSON list အဖြစ် ရှိနေသရွေ့ Knowledge Graph မဟုတ်ပါ။ ဤ module သည် ထို
Triple များကို Neo4j ထဲသို့ **idempotent** ဖြစ်စွာ ရေးသွင်းသည့် write path ကို တည်ဆောက်သည် — batch `MERGE`၊
`UNWIND` bulk insert၊ uniqueness constraint၊ update/delete semantics နှင့် transaction sizing ပါဝင်သည်။
ရေးသွင်းမှု တစ်ဝက် ပြတ်သွားပါက ပြန် run လိုက်ရုံဖြင့် graph မပျက်စီးစေရန် ဒီဇိုင်းကို ဦးစားပေးသည်။

## သင်ယူလေ့လာမည့် အကြောင်းအရာများ

- Triple set တစ်ခုကို parameterized `UNWIND $rows AS row` batch statement အဖြစ် ပြောင်းလဲခြင်း
- `MERGE` နှင့် `CREATE` ၏ semantics ကွာခြားချက်နှင့် duplicate node ကာကွယ်ခြင်း
- `REQUIRE n.id IS UNIQUE` constraint ကို write မတိုင်မီ စစ်ဆေးခြင်း၏ အခန်းကဏ္ဍ
- Stale relationship ဖယ်ရှားခြင်း၊ orphan node cleanup နှင့် cascade delete ၏ ဘေးထွက်သက်ရောက်မှု
- Transaction batching၊ session pool နှင့် index သည် write throughput ကို မည်သို့ ပြောင်းလဲစေသည်
- Python driver (`GraphDatabase.driver`၊ `session.run(query, **params)`) နှင့် offline simulation ဆက်စပ်မှု

## Module အစိတ်အပိုင်းများ

| File | အကြောင်းအရာ |
|---|---|
| `README.md` | Module scope၊ objectives၊ prerequisites၊ references |
| `explanation.md` | Subtopic ၆ ခု၏ သဘောတရားနှင့် engineering rationale |
| `exercise.md` | ကိုယ်တိုင် implement လုပ်ရမည့် လေ့ကျင့်ခန်း ၆ ခု |
| `solution.md` | Reference implementation အပြည့်အစုံ |
| `lab.py` | Standard library သာ သုံးသော executable lab (Neo4j server မလိုအပ်) |
| `walkthroughs/` | Exercise တိုင်းအတွက် Python အခြေခံမှစ၍ အပိုင်းလိုက် ရှင်းပြသည့် ဖတ်စာ |

`explanation.md` subtopics —

1. Triple မှ graph write အထိ — batch `MERGE` နှင့် `UNWIND` bulk insert
2. Idempotent graph write — `MERGE` နှင့် `CREATE` ၏ ကွာခြားချက်
3. Constraint ဖြင့် entity uniqueness ထိန်းချုပ်ခြင်း — `REQUIRE n.id IS UNIQUE`
4. Update နှင့် delete semantics — stale relationship၊ orphan node၊ cascade delete
5. Batch performance — transaction batching၊ session pool၊ index အရေးပါမှု
6. Python driver အခြေခံ — offline simulation နှင့် live driver call ဆက်စပ်မှု

### Walkthroughs

`solution.md` ရှိ code များကို Python အခြေခံမှ စတင်၍ အပိုင်းလိုက် လိုက်ဖတ်လိုပါက
`walkthroughs/` folder ကို ကြည့်ပါ။ Walkthrough တစ်ခုစီသည် exercise တစ်ခုစီအတွက် ဖြစ်ပြီး —
concept အသစ်များ (`set` နှင့် tuple key၊ set difference၊ `dict.setdefault()`၊
`dict.get()` counting pattern၊ list comprehension၊ `str.format` ၏ `{{` `}}` escape၊
`continue`၊ `%` formatting၊ `**params`၊ context manager `__enter__`/`__exit__`၊
`splitlines`/`split(sep, 1)`) ကို ဥပမာနှင့် တွဲဖက် ရှင်းပြသည်။ Code snippet တိုင်း၏ output
သည် အမှန်တကယ် run ၍ ရရှိသည့် ရလဒ် ဖြစ်သည်။

| Walkthrough | Exercise |
|---|---|
| `walkthroughs/01_unwind_batch_generator.md` | Exercise 1 — Triple → Cypher batch generator (`UNWIND`) |
| `walkthroughs/02_idempotent_merge_simulation.md` | Exercise 2 — Idempotent merge simulator (`MERGE` vs `CREATE`) |
| `walkthroughs/03_uniqueness_constraint_validation.md` | Exercise 3 — Uniqueness constraint validation |
| `walkthroughs/04_relationship_diff_orphan_cleanup.md` | Exercise 4 — Relationship update/delete diff နှင့် orphan cleanup |
| `walkthroughs/05_batch_transaction_sizing.md` | Exercise 5 — Batch transaction sizing |
| `walkthroughs/06_driver_call_sequence.md` | Exercise 6 — Driver call sequence simulation |

## Prerequisites

- M05 — Property Graph Model၊ Cypher `MATCH`/`MERGE`/`CREATE`/`DELETE`၊ constraint အခြေခံ
- M02–M03 — LLM extraction output schema၊ triple deduplication၊ Python standard library၊ Docker

## Production Use Cases

- Nightly re-extraction run တစ်ခုကို တူညီသော corpus အပေါ် ထပ်ခါတလဲလဲ run ခြင်း (idempotency မရှိပါက node များ ပွားလာသည်)
- Re-extraction ပြီးနောက် မထောက်ပံ့တော့သော relationship များကို prune လုပ်ခြင်း၊ chunk အသစ် တစ်ခုချင်း ဝင်လာသည့် incremental ingestion
- Multi-tenant graph write တွင် tenant id ကို constraint key အဖြစ် ပေါင်းထည့်ခြင်း

## Running against a real Neo4j

Repo ၏ `docker-compose.yml` ဖြင့် Neo4j 5 Community instance ကို စတင်နိုင်သည် — Bolt port `7687`၊
HTTP Browser port `7474`၊ credentials `neo4j` / `graphrag123`။ `explanation.md` ရှိ Python driver code
ကို ထို instance အပေါ် တိုက်ရိုက် run နိုင်သည်။ `lab.py` မှာမူ Neo4j server မလိုဘဲ offline
run နိုင်ရန် in-memory graph ကို အသုံးပြုသည်။

## References

- Cypher `MERGE` — https://neo4j.com/docs/cypher-manual/current/clauses/merge/
- Cypher `UNWIND` — https://neo4j.com/docs/cypher-manual/current/clauses/unwind/
- Cypher `DELETE` — https://neo4j.com/docs/cypher-manual/current/clauses/delete/
- Constraints — https://neo4j.com/docs/cypher-manual/current/constraints/managing-constraints/
- Neo4j Python driver နှင့် transactions — https://neo4j.com/docs/python-manual/current/transactions/
