# M05 — Exercise: Introduction to Neo4j

Exercise ၆ ခုလုံးကို `lab.py` အတွင်း implement လုပ်ရမည်။ Neo4j server မလိုအပ် — Property Graph ကို
in-memory adjacency map ဖြင့် simulate လုပ်ပြီး Cypher string များကို generate/validate လုပ်ရမည်။
Exercise တိုင်းတွင် `print(...)` ဖြင့် ရလဒ်ပြရမည်၊ `assert` ဖြင့် စစ်ရမည်၊ အောင်မြင်ပါက `True` return ရမည်။

## Exercise 1 — Property Graph in-memory model

**လုပ်ငန်း** — `Node` (id၊ labels၊ properties) နှင့် `Relationship` (type၊ start၊ end၊ properties)
dataclass နှစ်ခု ဖန်တီးပါ။ `PropertyGraph` class တွင် `add_node`၊ `add_relationship`၊ `out_edges`၊
`degree` ထည့်ပါ။ `build_sample_graph()` ဖြင့် Node ၄ ခု၊ Relationship ၅ ခု ပါသော sample graph တည်ဆောက်ပါ။

**Hints:** `out_adj: dict[str, list[tuple[type, target_id]]]` နှင့် `in_adj` ကို direction အတွက် တွဲထားပါ ·
endpoint မရှိပါက `ValueError` မြှင့်ပါ · `degree` = outgoing + incoming အရေအတွက်။

**Expected behavior:** `len(nodes) == 4`၊ `len(relationships) == 5` · label set သည်
`["Company", "Person", "Technology"]` · `nodes["p1"].properties["name"] == "Aung Aung"` ·
`degree("p1") == 3` နှင့် `degree("c1") == 3` · ပထမ relationship သည် `KNOWS`၊ `("p1", "p2")`။

## Exercise 2 — Cypher `MERGE` generation

**လုပ်ငန်း** — `cypher_merge_node(node)` နှင့် `cypher_merge_relationship(rel, start, end)` ဖန်တီးပါ။
Function တိုင်းသည် `(cypher_string, params_dict)` tuple ပြန်ရမည်။

**Hints:** Node အတွက် `MERGE (n:Label {id: $id})` → `SET` → `RETURN n` · Relationship အတွက် `MATCH`
၂ ခုဖြင့် endpoint ဆွဲ → `MERGE (a)-[r:TYPE]->(b)` → `RETURN r` · property key များကို `sorted()` ဖြင့်
စီပါ · value များကို query string ထဲ မထည့်ရ၊ `params` dict ထဲသာ ထည့်ရမည်။

**Expected behavior:** ပထမလိုင်းသည် `MERGE (n:Person {id: $id})` အတိအကျ · `SET n.age = $age, n.name = $name`
ပါဝင်သည် · `params == {"id": "p1", "name": "Aung Aung", "age": 34}` · `MERGE (a)-[r:KNOWS]->(b)` ပါဝင်ပြီး
`params == {"start_id": "p1", "end_id": "p2", "since": 2019}` · statement များတွင် quote (`'`) မပါဝင်ရ။

## Exercise 3 — Cypher statement parsing နှင့် validation

**လုပ်ငန်း** — `clause_sequence(stmt)` ဖြင့် (token, position) အစဉ်လိုက် ပြန်ပါ။ `validate_cypher(stmt)`
ဖြင့် violation list ပြန်ပါ — (၁) bracket balance၊ (၂) clause order သည် ကြီးလျှင် မကျရ၊
(၃) identity value ကို literal အဖြစ် မထည့်ရ၊ (၄) parameter (`$`) ပါရမည်။

**Hints:** clause order ကို rank dict (`UNWIND`=0၊ `MATCH`=1၊ `WHERE`=2၊ `WITH`=3၊ `CREATE`/`MERGE`=4၊
`SET`=5၊ `DELETE`=6၊ `RETURN`=7) ဖြင့် ကိုယ်စားပြုပါ · regex တွင် `OPTIONAL MATCH` ကို `MATCH` အရင်၊
`DETACH DELETE` ကို `DELETE` အရင် ထားပါ · literal id ကို `\{\s*id\s*:\s*(?:'[^']*'|"[^"]*"|\d+)` ဖြင့် ဖမ်းပါ။

**Expected behavior:** `MATCH (a:Person {id: $id})-[:KNOWS]->(b:Person) RETURN b.name AS name` → violation မရှိ ·
`MATCH (a:Person {id: $id} RETURN a` → `unbalanced_parentheses` ·
`RETURN n MATCH (n:Person {id: $id})` → `illegal_clause_order` ·
`MERGE (n:Person {id: 'p1'}) RETURN n` → `literal_identity_value` ပါဝင်သည်။

## Exercise 4 — Constraint နှင့် Index definitions

**လုပ်ငန်း** — DDL statement ၃ ခု (uniqueness constraint၊ range index၊ full-text index) ကို စာရင်းအဖြစ်
သတ်မှတ်ပြီး `classify_schema_ddl(ddl)` ဖြင့် `"uniqueness_constraint"`၊ `"range_index"`၊
`"fulltext_index"` အဖြစ် ခွဲခြားပါ။

**Hints:** Neo4j 5 syntax — `CREATE CONSTRAINT ... IF NOT EXISTS FOR (n:Label) REQUIRE n.prop IS UNIQUE` ·
`CREATE INDEX ... IF NOT EXISTS FOR (n:Label) ON (n.prop)` ·
`CREATE FULLTEXT INDEX ... IF NOT EXISTS FOR (n:Label) ON EACH [n.a, n.b]` · classification တွင်
`FULLTEXT INDEX` ကို `INDEX` အရင် စစ်ပါ။

**Expected behavior:** ရလဒ်သည် `["uniqueness_constraint", "range_index", "fulltext_index"]` ·
ပထမတွင် `REQUIRE` နှင့် `IS UNIQUE` ပါဝင်သည် · full-text DDL တွင်
`ON EACH [n.name, n.description]` ပါဝင်သည် · DDL အားလုံးတွင် `IF NOT EXISTS` ပါဝင်သည်။

## Exercise 5 — Parameterized query builder နှင့် injection defense

**လုပ်ငန်း** — `build_parameterized_query(template, params)` ဖြင့် query text နှင့် value ကို သီးခြားစီ ထားပါ။
`detect_injection(query_text)` ဖြင့် marker (`;`၊ `--`၊ `/*`၊ `DETACH DELETE`၊ `DROP `၊ `LOAD CSV`) ရှာပါ။
`validate_identifier(name)` ဖြင့် Label/type ကို whitelist regex စစ်ပါ။ Payload
`Robert'); MATCH (n) DETACH DELETE n;//` ကို parameterized နှင့် naive query နှစ်မျိုးတွင် နှိုင်းယှဉ်ပါ။

**Hints:** clause keyword (`MATCH`၊ `MERGE`၊ `SET`) များကို marker အဖြစ် မထည့်ရ — legitimate template
တွင် ပါဝင်နိုင်သည် · parameterized query text သည် template အတိအကျ ဖြစ်ရမည် · naive query တွင် payload ကို
quote အတွင်း interpolation ဖြင့် ထည့်ပြီး marker ပေါ်လာကြောင်း ပြပါ · whitelist regex သည်
`^[A-Za-z_][A-Za-z0-9_]*$` ဖြစ်သည် (Cypher သည် Label ကို parameterize လုပ်ခွင့် မပြု)။

**Expected behavior:** `detect_injection(parameterized_query) == []` · `params["name"]` သည် payload နှင့်
တူညီသည် (round-trip) · `payload not in parameterized_query` · naive query တွင် `";"` နှင့်
`"DETACH DELETE"` ပေါ်လာသည် · `validate_identifier("Person") is True`၊
`validate_identifier("Person\`) DETACH DELETE (n") is False`။

## Exercise 6 — Index-free adjacency traversal

**လုပ်ငန်း** — `traverse(graph, start_id, max_depth)` ဖြင့် directed BFS လုပ်ပြီး
`(visited, levels, traversals)` ပြန်ပါ။ `shortest_path(graph, src, dst)` ဖြင့် BFS shortest path ပြန်ပါ။
`index_lookups(visited, total_nodes)` ဖြင့် index-based engine ၏ estimated lookup (`visited × ceil(log2 N)`) တွက်ပါ။

**Hints:** BFS တွင် `collections.deque` သုံးပါ · `traversals` သည် ဖြတ်လိုက်သော directed edge တိုင်းကို
ရေတွက်သည် (node အသစ် မဖြစ်လည်း) · index-free adjacency ကို သက်သေပြရန် isolated node ၁၀၀၀ ထည့်ပြီး
ပြန် traverse လုပ်ပါ — `traversals` မပြောင်းရ၊ `index_lookups` မှာသာ ကြီးလာရမည်။

**Expected behavior:** `traverse(g, "p1", 2)` → `visited == {"p1", "p2", "c1", "t1"}`၊ `traversals == 5` ·
level များ `p1`=0၊ `p2`=1၊ `c1`=1၊ `t1`=1 · `shortest_path(g, "p2", "t1") == ["p2", "c1", "t1"]` (hop ၂) ·
isolated ၁၀၀၀ ထည့်ပြီးနောက်လည်း `traversals == 5` · node စုစုပေါင်း `1004` ဖြစ်ပြီး `index_lookups` ကြီးလာသည်။
