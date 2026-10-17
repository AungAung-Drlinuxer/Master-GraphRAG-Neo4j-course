# M06 — Solutions: Reference Implementation

ဤ solution များသည် `lab.py` နှင့် algorithm အရ တူညီသည်။ Output များသည်
`python3 modules/06_storing_entities_relationships_neo4j/lab.py` ကို run ၍ အမှန်တကယ် ရရှိသော
ရလဒ်များ ဖြစ်သည်။

Deterministic input (triple ၆ ခု) —

```python
ENTITY_TYPE_TO_LABEL = {"PERSON": "Person", "ORGANIZATION": "Organization",
                        "TECHNOLOGY": "Technology", "LOCATION": "Location"}

TRIPLES = [
    {"head": "Ada Lovelace", "head_type": "PERSON", "rel": "WORKED_AT",
     "tail": "Analytical Engine Project", "tail_type": "ORGANIZATION",
     "chunk_id": "c01", "confidence": 0.93},
    {"head": "Ada Lovelace", "head_type": "PERSON", "rel": "USES",
     "tail": "Analytical Engine", "tail_type": "TECHNOLOGY",
     "chunk_id": "c01", "confidence": 0.88},
    {"head": "Charles Babbage", "head_type": "PERSON", "rel": "FOUNDED",
     "tail": "Analytical Engine Project", "tail_type": "ORGANIZATION",
     "chunk_id": "c02", "confidence": 0.91},
    {"head": "Analytical Engine Project", "head_type": "ORGANIZATION",
     "rel": "LOCATED_IN", "tail": "London", "tail_type": "LOCATION",
     "chunk_id": "c03", "confidence": 0.76},
    {"head": "Ada Lovelace", "head_type": "PERSON", "rel": "COLLABORATED_WITH",
     "tail": "Charles Babbage", "tail_type": "PERSON",
     "chunk_id": "c02", "confidence": 0.84},
    {"head": "Ada Lovelace", "head_type": "PERSON", "rel": "WORKED_AT",
     "tail": "Analytical Engine Project", "tail_type": "ORGANIZATION",
     "chunk_id": "c04", "confidence": 0.79},
]


def slug(text):
    """Canonical node id — deterministic, lowercase, ASCII-safe."""
    return "".join(ch if ch.isalnum() else "_" for ch in text.lower()).strip("_")
```

## Exercise 1 — Triple → Cypher batch generator (`UNWIND`)

```python
from collections import OrderedDict


def build_batch_statements(triples):
    """Group triples by (head label, rel type, tail label): one UNWIND batch each."""
    groups = OrderedDict()
    for t in triples:
        key = (ENTITY_TYPE_TO_LABEL[t["head_type"]], t["rel"],
               ENTITY_TYPE_TO_LABEL[t["tail_type"]])
        groups.setdefault(key, []).append(t)
    statements = []
    for (head_label, rel_type, tail_label), items in groups.items():
        rows = [OrderedDict([("head_id", slug(t["head"])), ("head_name", t["head"]),
                             ("tail_id", slug(t["tail"])), ("tail_name", t["tail"]),
                             ("chunk_id", t["chunk_id"]),
                             ("confidence", t["confidence"])]) for t in items]
        cypher = (
            "UNWIND $rows AS row\n"
            "MERGE (h:{hl} {{id: row.head_id}})\n"
            "  ON CREATE SET h.name = row.head_name\n"
            "MERGE (t:{tl} {{id: row.tail_id}})\n"
            "  ON CREATE SET t.name = row.tail_name\n"
            "MERGE (h)-[r:{rel} {{chunk_id: row.chunk_id}}]->(t)\n"
            "  ON CREATE SET r.confidence = row.confidence\n"
            "  ON MATCH SET r.confidence = row.confidence"
        ).format(hl=head_label, tl=tail_label, rel=rel_type)
        statements.append({"group": (head_label, rel_type, tail_label),
                           "cypher": cypher, "rows": rows})
    return statements
```

Output —

```
triples=6  batch statements=5
  group=Person->WORKED_AT->Organization            rows=2
  group=Person->USES->Technology                   rows=1
  group=Person->FOUNDED->Organization              rows=1
  group=Organization->LOCATED_IN->Location         rows=1
  group=Person->COLLABORATED_WITH->Person          rows=1
```

**အဓိကအယူအဆ** — `UNWIND` သည် round-trip အရေအတွက်ကို triple အရေအတွက်မှ distinct group
အရေအတွက်သို့ လျှော့ချသည်။ Cypher သည် label/relationship type အတွက် parameter substitution
ကို မထောက်ပံ့သဖြင့် ၎င်းတို့ကို allowlist mapping မှသာ interpolate လုပ်သည် — LLM output
string ကို တိုက်ရိုက် ထည့်ခြင်းသည် Cypher injection ဖြစ်သည်။ Values အားလုံး `$rows` ဖြင့် လာသည်။

## Exercise 2 — Idempotent merge simulator (`MERGE` vs `CREATE`)

```python
class InMemoryGraph:
    """semantics='merge' dedupes by identity key (MERGE); 'create' appends blindly."""

    def __init__(self, semantics="merge"):
        self.semantics = semantics
        self.node_keys, self.edge_keys = [], []
        self.node_props, self.edge_props = {}, {}
        self.stats = {"nodes_created": 0, "nodes_matched": 0,
                      "edges_created": 0, "edges_matched": 0}

    def write_node(self, label, node_id, name):
        key = (label, node_id)
        if self.semantics == "merge" and key in self.node_props:
            self.stats["nodes_matched"] += 1
            self.node_props[key]["name"] = name
            return
        self.stats["nodes_created"] += 1
        self.node_keys.append(key)
        self.node_props.setdefault(key, {"label": label, "id": node_id, "name": name})

    def write_edge(self, head_label, head_id, rel_type, tail_label, tail_id,
                   chunk_id, confidence):
        key = (head_label, head_id, rel_type, tail_label, tail_id, chunk_id)
        if self.semantics == "merge" and key in self.edge_props:
            self.stats["edges_matched"] += 1
            self.edge_props[key] = confidence
            return
        self.stats["edges_created"] += 1
        self.edge_keys.append(key)
        self.edge_props[key] = confidence

    def node_count(self):
        return len(self.node_keys)

    def edge_count(self):
        return len(self.edge_keys)


def apply_batch(graph, statements):
    for st in statements:
        head_label, rel_type, tail_label = st["group"]
        for row in st["rows"]:
            graph.write_node(head_label, row["head_id"], row["head_name"])
            graph.write_node(tail_label, row["tail_id"], row["tail_name"])
            graph.write_edge(head_label, row["head_id"], rel_type, tail_label,
                             row["tail_id"], row["chunk_id"], row["confidence"])
```

Output —

```
MERGE  pass1 nodes/edges=(5, 6)  pass2=(5, 6)
CREATE pass1 nodes/edges=(12, 6)  pass2=(24, 12)
MERGE counters: {'nodes_created': 5, 'nodes_matched': 19, 'edges_created': 6, 'edges_matched': 6}
```

**အဓိကအယူအဆ** — `MERGE` ၏ counter များသည် observability ပေးသည် — pass ၂ တွင်
`nodes_created=0` ဖြစ်ခြင်းသည် "input အသစ် မရှိ" ကို ဆိုလိုသည်။ `nodes_matched` အလွန်ကြီးခြင်းသည်
input ကို ထပ်ခါတလဲလဲ ပို့နေခြင်း (retry storm) ကို ညွှန်းသည်။ `CREATE` semantics သည်
pass ၂ တွင် node အရေအတွက်ကို နှစ်ဆ ဖြစ်စေသည် — idempotency မရှိသော write path ၏ လက္ခဏာ။

## Exercise 3 — Uniqueness constraint validation

```python
def expected_constraint_ddl():
    return ("CREATE CONSTRAINT entity_id_unique IF NOT EXISTS\n"
            "FOR (n:Entity) REQUIRE n.id IS UNIQUE")


def validate_uniqueness_constraint(candidates):
    """Simulate `REQUIRE n.id IS UNIQUE` over the incoming write set."""
    violations, seen = [], {}
    for cand in candidates:
        label, node_id = cand["label"], cand["id"]
        if not node_id:
            violations.append({"label": label, "id": node_id, "rule": "id_not_null"})
            continue
        key = (label, node_id)
        if key in seen:
            violations.append({"label": label, "id": node_id,
                               "rule": "id_unique", "first_seen": seen[key]})
        else:
            seen[key] = cand["name"]
    return violations
```

Output —

```
candidates=5  violations=2
  Person  id='ada_lovelace'  rule=id_unique
  Location  id=''  rule=id_not_null
```

Neo4j 5 syntax ကို သုံးထားသည်။ Neo4j 4.x တွင်
`CREATE CONSTRAINT entity_id_unique IF NOT EXISTS ON (n:Entity) ASSERT n.id IS UNIQUE`
ဖြစ်သည်။

**အဓိကအယူအဆ** — Unique constraint သည် correctness အတွက်သာမက **index** ကိုပါ ဖန်တီးပေးသဖြင့်
`MERGE` ၏ lookup ကို O(1) ဖြစ်စေသည်။ Client-side validation သည် defense-in-depth —
null `id` ကို server သို့ မပို့မီ ဖယ်ထုတ်ခြင်းဖြင့် transaction တစ်ခုလုံး rollback ဖြစ်ခြင်းကို
ကာကွယ်သည်။ Constraint DDL ကို Text-to-Cypher လမ်းကြောင်းမှ block လုပ်ရမည်။

## Exercise 4 — Relationship update/delete diff နှင့် orphan cleanup

```python
def edge_set(triples):
    return {(ENTITY_TYPE_TO_LABEL[t["head_type"]], slug(t["head"]), t["rel"],
             ENTITY_TYPE_TO_LABEL[t["tail_type"]], slug(t["tail"]), t["chunk_id"])
            for t in triples}


def diff_relationships(current_edges, desired_edges):
    return (sorted(desired_edges - current_edges),
            sorted(current_edges - desired_edges))


def node_degree(edges):
    degree = {}
    for head_label, head_id, _rel, tail_label, tail_id, _chunk in edges:
        degree[(head_label, head_id)] = degree.get((head_label, head_id), 0) + 1
        degree[(tail_label, tail_id)] = degree.get((tail_label, tail_id), 0) + 1
    return degree


def orphan_nodes(nodes, edges):
    degree = node_degree(edges)
    return sorted(n for n in nodes if degree.get(n, 0) == 0)


current = edge_set(TRIPLES)
desired = edge_set([t for t in TRIPLES if t["chunk_id"] not in ("c01", "c02")
                    or t["rel"] not in ("USES", "COLLABORATED_WITH")])
to_add, to_delete = diff_relationships(current, desired)
```

Output —

```
current edges=6  desired edges=4
to_add=0  to_delete=2
  DELETE Person(ada_lovelace)-[:COLLABORATED_WITH]->Person(charles_babbage)
  DELETE Person(ada_lovelace)-[:USES]->Technology(analytical_engine)
orphan nodes after delete=['analytical_engine']
DETACH DELETE ada_lovelace -> edges 4 -> 2
```

သက်ဆိုင်ရာ Cypher —

```cypher
// stale relationship ဖယ်ရှားခြင်း
MATCH (h:Person {id: $head_id})-[r:USES {chunk_id: $chunk_id}]->(t:Technology {id: $tail_id})
DELETE r

// orphan node cleanup
MATCH (n:Technology)
WHERE NOT (n)--()
DELETE n

// cascade delete — node နှင့် သူ့ relationship အားလုံး
MATCH (n:Person {id: $id})
DETACH DELETE n
```

**အဓိကအယူအဆ** — Desired-state diff သည် graph ကို corpus နှင့် တစ်သမတ်တည်း ထားရှိရန် လိုအပ်သည်။
`DELETE` (relationship ရှိပါက error) နှင့် `DETACH DELETE` (cascade) ကို ကွဲပြားစွာ သုံးခြင်းသည်
accidental cascade ကို ကာကွယ်သည်။ Cascade delete မတိုင်မီ ဖျက်မည့် relationship အရေအတွက်ကို
count လုပ်ပြီး threshold သတ်မှတ်ရမည်။

## Exercise 5 — Batch transaction sizing

```python
def chunk_rows(row_count, batch_size):
    return [(start, min(start + batch_size, row_count))
            for start in range(0, row_count, batch_size)]


def estimate_seconds(row_count, batch_size, tx_overhead_ms=4.0, row_ms=0.08,
                     pool_size=4):
    """T = (ceil(N / B) * t_tx + N * t_row) / pool_size"""
    batches = len(chunk_rows(row_count, batch_size))
    return (batches * tx_overhead_ms + row_count * row_ms) / 1000.0 / pool_size
```

Output (row_count=1000) —

```
  batch_size=1     transactions=1000   est_wall=1.0200s
  batch_size=10    transactions=100    est_wall=0.1200s
  batch_size=50    transactions=20     est_wall=0.0400s
  batch_size=200   transactions=5      est_wall=0.0250s
  batch_size=1000  transactions=1      est_wall=0.0210s
transaction reduction at batch_size=1000: 1000x
```

**အဓိကအယူအဆ** — Wall-clock သည် `(batches · t_tx + N · t_row) / P` ဖြစ်သည်။ B တိုးလာသည်နှင့်
`batches · t_tx` term ကျသည်၊ သို့သော် `N · t_row` သည် ပုံသေ ကျန်သည် — ထို့ကြောင့် အကျိုးအမြတ်သည်
တစ်နေရာတွင် ပြန်၍ ပြားသည်။ Batch size ကို transaction memory နှင့် failure recovery cost
အပေါ် မူတည်ပြီး ရွေးရသည်၊ session pool size P သည် ဤခန့်မှန်းချက်ကို တိုက်ရိုက် စားသည်။

## Exercise 6 — Driver call sequence simulation

```python
class FakeResult:
    def __init__(self, counters):
        self._counters = counters

    def consume(self):
        return {"counters": self._counters}

    def data(self):
        return []


class FakeSession:
    def __init__(self, graph, calls, database="neo4j", fetch_size=1000):
        self.graph, self.calls = graph, calls
        self.database, self.fetch_size = database, fetch_size
        self.closed = False

    def run(self, query, **params):
        self.calls.append({"query_head": query.splitlines()[0],
                           "param_keys": sorted(params.keys()),
                           "row_count": len(params.get("rows", []))})
        self._execute(query, params)
        return FakeResult({"nodes_created": 0,
                           "relationships_created": len(params.get("rows", []))})

    def _execute(self, query, params):
        head_label = tail_label = rel_type = None
        for line in query.splitlines():
            if line.startswith("MERGE (h:") and "{" in line:
                head_label = line.split("MERGE (h:", 1)[1].split()[0]
            elif line.startswith("MERGE (t:") and "{" in line:
                tail_label = line.split("MERGE (t:", 1)[1].split()[0]
            elif line.startswith("MERGE (h)-[r:"):
                rel_type = line.split("MERGE (h)-[r:", 1)[1].split()[0]
        for row in params.get("rows", []):
            self.graph.write_node(head_label, row["head_id"], row["head_name"])
            self.graph.write_node(tail_label, row["tail_id"], row["tail_name"])
            self.graph.write_edge(head_label, row["head_id"], rel_type, tail_label,
                                  row["tail_id"], row["chunk_id"], row["confidence"])

    def close(self):
        self.closed = True

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        self.close()
        return False


class FakeDriver:
    def __init__(self, uri, auth, graph=None, calls=None):
        self.uri, self.auth, self.graph = uri, auth, graph
        self.calls = calls if calls is not None else []
        self.verified = 0
        self.closed = False

    def verify_connectivity(self):
        self.verified += 1

    def session(self, database=None, **kwargs):
        return FakeSession(self.graph, self.calls, database=database or "neo4j")

    def close(self):
        self.closed = True


def run_write_transaction(driver, statements):
    """Mirrors GraphDatabase.driver -> session(database) -> run(query, **params)."""
    driver.verify_connectivity()
    with driver.session(database="neo4j") as session:
        for st in statements:
            session.run(st["cypher"], rows=st["rows"])
    driver.close()
    return driver
```

Output —

```
uri=bolt://localhost:7687  auth=(neo4j, ***)
verify_connectivity calls=1
session.run calls=5
  1) UNWIND $rows AS row params=['rows'] rows=2
  2) UNWIND $rows AS row params=['rows'] rows=1
  3) UNWIND $rows AS row params=['rows'] rows=1
  4) UNWIND $rows AS row params=['rows'] rows=1
  5) UNWIND $rows AS row params=['rows'] rows=1
batched run calls=5 vs per-triple run calls=6
```

Live driver အတွက် တူညီသော sequence (ဤ code ကို `lab.py` ထဲ မထည့်ရ — `neo4j` package လိုအပ်သည်) —

```python
from neo4j import GraphDatabase

driver = GraphDatabase.driver("bolt://localhost:7687", auth=("neo4j", "graphrag123"))
driver.verify_connectivity()

with driver.session(database="neo4j") as session:
    for statement in statements:
        summary = session.run(statement["cypher"], rows=statement["rows"]).consume()
        print(summary.counters.nodes_created, summary.counters.relationships_created)

driver.close()
```

**အဓိကအယူအဆ** — Offline simulation သည် call sequence၊ parameter name နှင့် Cypher generation
ကို အာမခံသည်။ Server-side behavior (syntax validation၊ constraint enforcement၊ index query plan၊
transaction isolation) ကို အာမခံသည့်အခါ repo ၏ `docker-compose.yml` ဖြင့် Neo4j 5 Community
(Bolt `7687`၊ Browser `7474`၊ `neo4j` / `graphrag123`) တင်ပြီး ဤ live code ကို run ရမည်။
Credential ကို environment variable မှ ဖတ်ရမည်၊ driver ကို application lifecycle တစ်ခုလုံးအတွက်
တစ်ခုတည်း ထားရှိရမည်။
