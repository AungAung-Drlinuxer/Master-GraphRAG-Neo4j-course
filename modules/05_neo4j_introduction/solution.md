# M05 — Solution: Introduction to Neo4j

Exercise ၆ ခုအတွက် reference implementation ဖြစ်သည်။ Code သည် `lab.py` နှင့် algorithm အရ တူညီသည် —
`lab.py` တွင် `print` နှင့် `assert` ပိုထည့်ထားသည်။

---

## Exercise 1 — Property Graph in-memory model

```python
from dataclasses import dataclass, field
from typing import Dict, List, Tuple


@dataclass
class Node:
    id: str
    labels: Tuple[str, ...]
    properties: Dict[str, object] = field(default_factory=dict)


@dataclass
class Relationship:
    type: str
    start: str
    end: str
    properties: Dict[str, object] = field(default_factory=dict)


class PropertyGraph:
    def __init__(self) -> None:
        self.nodes: Dict[str, Node] = {}
        self.relationships: List[Relationship] = []
        self.out_adj: Dict[str, List[Tuple[str, str]]] = {}
        self.in_adj: Dict[str, List[Tuple[str, str]]] = {}

    def add_node(self, node_id, labels, **props) -> Node:
        node = Node(node_id, tuple(labels), dict(props))
        self.nodes[node_id] = node
        self.out_adj.setdefault(node_id, [])
        self.in_adj.setdefault(node_id, [])
        return node

    def add_relationship(self, rel_type, start, end, **props) -> Relationship:
        if start not in self.nodes or end not in self.nodes:
            raise ValueError("relationship endpoint မရှိသော node: " + start + " / " + end)
        rel = Relationship(rel_type, start, end, dict(props))
        self.relationships.append(rel)
        self.out_adj[start].append((rel_type, end))
        self.in_adj[end].append((rel_type, start))
        return rel

    def out_edges(self, node_id: str) -> List[Tuple[str, str]]:
        return list(self.out_adj.get(node_id, []))

    def degree(self, node_id: str) -> int:
        return len(self.out_adj.get(node_id, [])) + len(self.in_adj.get(node_id, []))


def build_sample_graph() -> PropertyGraph:
    g = PropertyGraph()
    g.add_node("p1", ("Person",), name="Aung Aung", age=34)
    g.add_node("p2", ("Person",), name="Su Su", age=29)
    g.add_node("c1", ("Company",), name="GraphRAG Labs")
    g.add_node("t1", ("Technology",), name="Neo4j")
    g.add_relationship("KNOWS", "p1", "p2", since=2019)
    g.add_relationship("WORKS_AT", "p1", "c1", role="Data Engineer")
    g.add_relationship("WORKS_AT", "p2", "c1", role="ML Engineer")
    g.add_relationship("USES", "c1", "t1", since=2021)
    g.add_relationship("USES", "p1", "t1", since=2024)
    return g
```

**အဓိကအယူအဆ** — Property Graph ၏ adjacency ကို outgoing နှင့် incoming directory နှစ်ခု အဖြစ် ထားခြင်းသည်
Neo4j ၏ doubly-linked relationship record ကို ပုံစံတူ ကိုယ်စားပြုသည်။ Direction ကို မြှေ့တင်ရန် in_adj
လိုသည် — မဟုတ်ပါက `(a)<-[:R]-(b)` pattern ကို ရှာရန် graph တစ်ခုလုံး scan ရမည်။

---

## Exercise 2 — Cypher `MERGE` generation

```python
def cypher_merge_node(node: Node) -> Tuple[str, Dict[str, object]]:
    lines = ["MERGE (n:" + node.labels[0] + " {id: $id})"]
    sets = ["n." + k + " = $" + k for k in sorted(node.properties)]
    if sets:
        lines.append("SET " + ", ".join(sets))
    lines.append("RETURN n")
    params: Dict[str, object] = {"id": node.id}
    params.update(node.properties)
    return "\n".join(lines), params


def cypher_merge_relationship(rel, start: Node, end: Node):
    lines = [
        "MATCH (a:" + start.labels[0] + " {id: $start_id})",
        "MATCH (b:" + end.labels[0] + " {id: $end_id})",
        "MERGE (a)-[r:" + rel.type + "]->(b)",
    ]
    sets = ["r." + k + " = $" + k for k in sorted(rel.properties)]
    if sets:
        lines.append("SET " + ", ".join(sets))
    lines.append("RETURN r")
    params: Dict[str, object] = {"start_id": rel.start, "end_id": rel.end}
    params.update(rel.properties)
    return "\n".join(lines), params
```

Generate လုပ်လိုက်သော output (node `p1` နှင့် relationship `KNOWS`) —

```cypher
MERGE (n:Person {id: $id})
SET n.age = $age, n.name = $name
RETURN n
```

```cypher
MATCH (a:Person {id: $start_id})
MATCH (b:Person {id: $end_id})
MERGE (a)-[r:KNOWS]->(b)
SET r.since = $since
RETURN r
```

**အဓိကအယူအဆ** — `MERGE` ကို identity property (`id`) ပေါ်တွင် လုပ်ခြင်းသည် idempotency ၏ အခြေခံ ဖြစ်သည်။
Property များကို `SET` ဖြင့် သီးခြားစီ update လုပ်ခြင်းသည် `MERGE` pattern ကို ကျဉ်းစေသည် —
pattern ထဲ property အများကြီး ထည့်ပါက match လုပ်ရာ ခက်ပြီး index ကို ချိုးဖျက်သည်။ `sorted()` သည်
deterministic output အတွက် လိုအပ်သည် (dict ordering ပေါ် မမှီခိုရန်)။ Value များကို string ထဲ မထည့်ဘဲ
`params` dict ထဲ ထားခြင်းသည် injection ကို တစ်ချိန်တည်း ကာကွယ်သည်။

`ON CREATE SET` / `ON MATCH SET` ကို ထည့်သုံးပါက created timestamp ကို ပထမအကြိမ်တွင်သာ သတ်မှတ်နိုင်သည်။

---

## Exercise 3 — Cypher statement validation

```python
import re

_CLAUSE_RE = re.compile(
    r"\b(OPTIONAL\s+MATCH|DETACH\s+DELETE|MATCH|WHERE|WITH|CREATE|MERGE|SET"
    r"|DELETE|REMOVE|ORDER\s+BY|SKIP|LIMIT|UNWIND|RETURN)\b"
)
_CLAUSE_RANK = {
    "UNWIND": 0, "OPTIONAL MATCH": 1, "MATCH": 1, "WHERE": 2, "WITH": 3,
    "CREATE": 4, "MERGE": 4, "SET": 5, "REMOVE": 5, "DETACH DELETE": 6,
    "DELETE": 6, "RETURN": 7, "ORDER BY": 8, "SKIP": 9, "LIMIT": 10,
}
_LITERAL_ID_RE = re.compile(r"\{\s*id\s*:\s*(?:'[^']*'|\"[^\"]*\"|\d+)")


def clause_sequence(statement: str):
    return [(" ".join(m.group(1).split()), m.start())
            for m in _CLAUSE_RE.finditer(statement)]


def validate_cypher(statement: str):
    violations = []
    if statement.count("(") != statement.count(")"):
        violations.append("unbalanced_parentheses")
    if statement.count("[") != statement.count("]"):
        violations.append("unbalanced_brackets")
    ranks = [_CLAUSE_RANK[tok] for tok, _ in clause_sequence(statement)]
    if any(ranks[i] > ranks[i + 1] for i in range(len(ranks) - 1)):
        violations.append("illegal_clause_order")
    if _LITERAL_ID_RE.search(statement):
        violations.append("literal_identity_value")
    if "$" not in statement:
        violations.append("missing_parameter")
    return violations
```

ရလဒ် —

```text
MATCH (a:Person {id: $id})-[:KNOWS]->(b:Person) RETURN b.name AS name  -> []
MERGE (n:Person {id: $id}) SET n.name = $name RETURN n                -> []
MATCH (a:Person {id: $id} RETURN a                                     -> ['unbalanced_parentheses']
RETURN n MATCH (n:Person {id: $id})                                    -> ['illegal_clause_order']
MERGE (n:Person {id: 'p1'}) RETURN n                                   -> ['literal_identity_value', 'missing_parameter']
```

**အဓိကအယူအဆ** — Regex ဖြင့် clause များကို ဖမ်းသည့်အခါ alternation အစဉ် အရေးပါသည် — `OPTIONAL MATCH`
ကို `MATCH` အရင်၊ `DETACH DELETE` ကို `DELETE` အရင် ထားမှ တူညီသော span ကို မှန်ကန်စွာ ဖမ်းသည်။
Clause order ကို rank အဖြစ် ကိုယ်စားပြုခြင်းသည် Cypher ၏ strict pipeline semantics ကို ရိုးရှင်းစွာ
စစ်ဆေးနိုင်သည်။ ဤ validator သည် **static** ဖြစ်သည် — syntax အပြည့်အစုံကို စစ်သည်မဟုတ်၊ injection
နှင့် structure ဆိုင်ရာ အန္တရာယ်ကို စစ်သည်။ Production တွင် `EXPLAIN` ဖြင့် server-side syntax စစ်ဆေးမှု
ကို ထပ်တွဲရမည်။

---

## Exercise 4 — Constraint နှင့် Index definitions

```python
SCHEMA_DDL = [
    "CREATE CONSTRAINT person_id_unique IF NOT EXISTS FOR (n:Person) REQUIRE n.id IS UNIQUE",
    "CREATE INDEX person_name_range IF NOT EXISTS FOR (n:Person) ON (n.name)",
    "CREATE FULLTEXT INDEX entity_fulltext IF NOT EXISTS FOR (n:Entity) ON EACH [n.name, n.description]",
]


def classify_schema_ddl(ddl: str) -> str:
    u = " ".join(ddl.upper().split())
    if "CONSTRAINT" in u and "IS UNIQUE" in u:
        return "uniqueness_constraint"
    if "FULLTEXT INDEX" in u:
        return "fulltext_index"
    if "INDEX" in u and " ON " in u:
        return "range_index"
    return "unknown"
```

Generated DDL များကို Neo4j 5 တွင် တိုက်ရိုက် run နိုင်သည် —

```cypher
CREATE CONSTRAINT person_id_unique IF NOT EXISTS
FOR (n:Person) REQUIRE n.id IS UNIQUE
```

```cypher
CREATE INDEX person_name_range IF NOT EXISTS
FOR (n:Person) ON (n.name)
```

```cypher
CREATE FULLTEXT INDEX entity_fulltext IF NOT EXISTS
FOR (n:Entity) ON EACH [n.name, n.description]
```

**အဓိကအယူအဆ** — Classification တွင် `FULLTEXT INDEX` ကို `INDEX` အရင် စစ်ရသည် — မဟုတ်ပါက
full-text index သည် range index အဖြစ် အမှားခွဲခြားခံရမည်။ `IF NOT EXISTS` သည် migration script
များကို idempotent ဖြစ်စေသည်။ Uniqueness constraint သည် backing index ဖန်တီးပေးသောကြောင့်
`MERGE (n:Person {id: $id})` သည် `NodeByLabelScan` အစား `NodeIndexSeek` ဖြစ်လာသည်။

---

## Exercise 5 — Parameterized query builder နှင့် injection defense

```python
_INJECTION_MARKERS = (";", "--", "/*", "*/", "DETACH DELETE", "DROP ", "LOAD CSV")
_LABEL_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")


def detect_injection(query_text: str):
    upper = query_text.upper()
    return [m for m in _INJECTION_MARKERS if m.upper() in upper]


def validate_identifier(name: str) -> bool:
    return bool(_LABEL_RE.match(name))


def build_parameterized_query(template: str, params):
    return template, dict(params)
```

```python
template = "MERGE (n:Person {id: $id}) SET n.name = $name RETURN n"
payload_name = "Robert'); MATCH (n) DETACH DELETE n;//"

query, params = build_parameterized_query(template, {"id": "p1", "name": payload_name})
# query -> "MERGE (n:Person {id: $id}) SET n.name = $name RETURN n"
# detect_injection(query) -> []

naive = "MERGE (n:Person {id: 'p1'}) SET n.name = '" + payload_name + "' RETURN n"
# detect_injection(naive) -> [';', 'DETACH DELETE']
```

**အဓိကအယူအဆ** — Parameterization သည် value ကို query ၏ syntax tree အပြင်ဘက်တွင် သယ်ဆောင်သည်။
ထို့ကြောင့် payload ထဲရှိ `'`၊ `;`၊ clause keyword များသည် data အဖြစ်သာ ကျန်သည် — injection
ဖြစ်မလာတော့ပါ။ Marker စာရင်းတွင် clause keyword များကို မထည့်ရ — legitimate template တွင်
`MATCH`/`MERGE` ပါဝင်နိုင်သည်။ Label နှင့် Relationship type ကို Cypher တွင် parameterize လုပ်မရ
(Neo4j 5)၊ ထို့ကြောင့် whitelist regex ဖြင့် စစ်ဆေးရသည်။ Parameterization သည် authorization ကို
အစားထိုးမပေးပါ — read-only role နှင့် tenant filter ကို သီးခြား ထည့်ရမည်။

---

## Exercise 6 — Index-free adjacency traversal

```python
import math
from collections import deque


def traverse(graph, start_id: str, max_depth: int):
    visited = {start_id}
    levels = {start_id: 0}
    traversals = 0
    queue = deque([start_id])
    while queue:
        cur = queue.popleft()
        depth = levels[cur]
        if depth == max_depth:
            continue
        for _rtype, nxt in graph.out_edges(cur):
            traversals += 1
            if nxt not in visited:
                visited.add(nxt)
                levels[nxt] = depth + 1
                queue.append(nxt)
    return visited, levels, traversals


def shortest_path(graph, src: str, dst: str):
    prev = {}
    seen = {src}
    queue = deque([src])
    while queue:
        cur = queue.popleft()
        if cur == dst:
            path = [cur]
            while path[-1] != src:
                path.append(prev[path[-1]])
            return list(reversed(path))
        for _rtype, nxt in graph.out_edges(cur):
            if nxt not in seen:
                seen.add(nxt)
                prev[nxt] = cur
                queue.append(nxt)
    return []


def index_lookups(visited: int, total_nodes: int) -> int:
    if total_nodes <= 1:
        return visited
    return visited * max(1, int(math.ceil(math.log(total_nodes, 2))))
```

ရလဒ် —

```text
traverse(g, "p1", 2)                -> visited={'p1','p2','c1','t1'}, traversals=5
levels                              -> {'p1': 0, 'p2': 1, 'c1': 1, 't1': 1}
shortest_path(g, "p2", "t1")        -> ['p2', 'c1', 't1']  (hops = 2)
isolated 1000 node ထည့်ပြီးနောက်      -> edge traversals 5 -> 5, index lookups 8 -> 40
```

**အဓိကအယူအဆ** — `traversals` သည် node အသစ် ဖြစ်သည်/မဖြစ်သည် မခွဲဘဲ ဖြတ်လိုက်သော directed edge
တိုင်းကို ရေတွက်သည် — ၎င်းသည် index-free adjacency ၏ စစ်မှန်သော cost ဖြစ်သည်။ Isolated node ၁၀၀၀
ထည့်သော်လည်း `traversals` သည် ၅ တွင် ဆက်ရှိနေသည် — traversal cost သည် graph အရွယ်အစား (N) ပေါ်တွင်
မမှီခိုကြောင်း သက်သေပြသည်။ `index_lookups` မှာမူ `N` နှင့်အတူ ကြီးလာသည် (`O(visited × log N)`)။
ဤကွာခြားချက်သည်ပင် Neo4j ကို GraphRAG retrieval အတွက် ရွေးချယ်ရသည့် အဓိကအကြောင်းရင်း ဖြစ်သည်။

---

## Verification

```bash
python3 modules/05_neo4j_introduction/lab.py
# Expected output (နောက်ဆုံးလိုင်း):
# [PASS] All 6/6 exercises passed successfully.
# exit code 0
```
