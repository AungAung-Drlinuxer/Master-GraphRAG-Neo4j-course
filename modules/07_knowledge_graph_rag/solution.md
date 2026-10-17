# M07 — Reference Solution

Code အားလုံးသည် `lab.py` နှင့် algorithm အရ တူညီသည်။ Fixture (NODES, EDGES, CHUNKS, ADJ) သည်
module တစ်လျှောက်လုံး တူညီသည် —

```python
# node id -> (label, name, aliases, summary)
NODES = {
    "co:neo4j": ("Company", "Neo4j", ("Neo4j Inc", "Neo4j, Inc."), "Graph database vendor."),
    "prod:aura": ("Product", "AuraDB", ("Neo4j AuraDB", "Aura"), "Managed cloud graph database service."),
    "tech:cypher": ("Technology", "Cypher", ("openCypher", "Cypher Query Language"), "Declarative graph query language."),
    "tech:louvain": ("Technology", "Louvain", ("Louvain method",), "Greedy modularity optimisation for community detection."),
    "org:cnrs": ("Organization", "CNRS", (), "Research organisation of the Louvain authors."),
    "person:eifrem": ("Person", "Vincent Blondel", ("Blondel",), "Lead author of the Louvain method."),
    "tech:graphrag": ("Technology", "GraphRAG", ("Graph RAG", "Microsoft GraphRAG"), "Retrieval pattern grounded in a knowledge graph."),
    "tech:vectorindex": ("Technology", "Vector Index", ("vector search index", "HNSW index"), "Approximate nearest neighbour index over embeddings."),
    "org:neo4jeng": ("Team", "Neo4j Engineering", (), "Engineering team maintaining Cypher."),
    "paper:louvain": ("Paper", "Fast unfolding of communities in large networks", (), "The 2008 Louvain method paper."),
}
# (src, rel, dst, provenance chunk id of the passage it was extracted from)
EDGES = (
    ("co:neo4j", "DEVELOPS", "prod:aura", "c1"),
    ("co:neo4j", "CREATES", "tech:cypher", "c2"),
    ("co:neo4j", "EMPLOYS", "org:neo4jeng", "c2"),
    ("prod:aura", "USES", "tech:vectorindex", "c1"),
    ("tech:cypher", "MAINTAINED_BY", "org:neo4jeng", "c2"),
    ("tech:graphrag", "USES", "tech:cypher", "c3"),
    ("co:neo4j", "PUBLISHES", "tech:graphrag", "c3"),
    ("tech:graphrag", "RUNS_ON", "prod:aura", "c3"),
    ("person:eifrem", "AFFILIATED_WITH", "org:cnrs", "c4"),
    ("person:eifrem", "PROPOSED", "tech:louvain", "c4"),
    ("org:cnrs", "PUBLISHES", "tech:louvain", "c4"),
    ("tech:louvain", "DOCUMENTED_IN", "paper:louvain", "c4"),
)
ALLOWED_LABELS = frozenset(node[0] for node in NODES.values())
ADJ = {}
for _src, _rel, _dst, _chunk in EDGES:
    ADJ.setdefault(_src, set()).add(_dst)
    ADJ.setdefault(_dst, set()).add(_src)
ADJ = {node: set(sorted(nb)) for node, nb in ADJ.items()}
```

---

## Exercise 1 — Entity Linking

```python
import re
import unicodedata
from difflib import SequenceMatcher


def _fold(text):
    return unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode().casefold()


def tokenize(text):
    return re.findall(r"[a-z0-9]+", _fold(text))


def fuzzy_score(surface, query):
    """Surface-form match score in [0, 1] between a node name/alias and a query."""
    s, q = " ".join(tokenize(surface)), " ".join(tokenize(query))
    if not s:
        return 0.0
    if s in q:                      # query ထဲ တိုက်ရိုက် ပါဝင်နေသည် — strong signal
        return 1.0
    words = set(tokenize(surface))
    if not words:
        return 0.0
    overlap = len(words & set(tokenize(query))) / len(words)
    return round(max(overlap * 0.95, SequenceMatcher(None, s, q).ratio() * 0.6), 4)


def link_query(query, threshold=0.7):
    """Return [(node_id, score, matched_surface)] sorted by score desc, id asc."""
    hits = []
    for node_id in sorted(NODES):
        label, name, aliases, summary = NODES[node_id]
        scored = [(fuzzy_score(s, query), s) for s in (name,) + tuple(aliases)]
        best_score, best_surface = max(scored)
        if best_score >= threshold:
            hits.append((node_id, best_score, best_surface))
    return sorted(hits, key=lambda h: (-h[1], h[0]))
```

**အဓိကအယူအဆ** — Linking ကို two-signal ဖြင့် လုပ်သည်။ Substring signal (score 1.0) သည်
အမှား အနည်းဆုံး ဖြစ်သော်လည်း inflection နှင့် spelling variant ကို မဖမ်းနိုင်ပါ။ Token overlap
signal သည် ထို gap ကို ဖြည့်သော်လည်း false positive ဖြစ်နိုင်သည်၊ ထို့ကြောင့် weight ကို
0.95 ဖြင့် လျှော့ပြီး threshold 0.7 ဖြင့် ဖြတ်သည်။ `sorted(NODES)` iteration နှင့်
`(-score, node_id)` sort သည် run တိုင်း output တူညီမှုကို အာမခံသည်။

---

## Exercise 2 — k-hop Subgraph Retrieval

```python
from collections import deque


def k_hop_subgraph(anchor_ids, k, adj=None):
    """Breadth-first expansion up to k hops. Returns (node_ids, edge_indexes)."""
    adj = ADJ if adj is None else adj
    reached = set(anchor_ids)
    frontier = deque(sorted(anchor_ids))
    for _ in range(k):
        nxt = deque()
        while frontier:
            for nb in sorted(adj.get(frontier.popleft(), ())):
                if nb not in reached:
                    reached.add(nb)
                    nxt.append(nb)
        frontier = nxt
        if not frontier:
            break
    idx = [i for i, e in enumerate(EDGES) if e[0] in reached and e[2] in reached]
    return sorted(reached), idx
```

**အဓိကအယူအဆ** — Level-by-level BFS သည် hop budget ကို တိတိကျကျ ထိန်းသည်။ Frontier ကို level
တစ်ခုစီ ပြီးဆုံးအောင် စားသုံးခြင်းဖြင့် hop တစ်ခုထက် ကျော်မသွားပါ။ Edge စုစည်းသည့်အခါ node
နှစ်ခုလုံး ရောက်ရှိပြီးသား ဖြစ်ရမည် — မဟုတ်ပါက dangling triple ဖြစ်ပြီး prompt ထဲတွင်
အဓိပ္ပာယ် မရှိသော relation ကို ထည့်မိမည်။

Neo4j ပေါ်တွင် ထို operation ကို variable-length pattern ဖြင့် ရေးနိုင်သည် —

```cypher
MATCH path = (a)-[r*1..2]-(b)
WHERE a.id IN $anchor_ids
UNWIND relationships(path) AS rel
RETURN DISTINCT startNode(rel).id AS src, type(rel) AS rel_type, endNode(rel).id AS dst
LIMIT $limit
```

`$limit` ကို မဖြစ်မနေ ထည့်ရမည် — degree distribution heavy-tail ဖြစ်ပါက hub node တစ်ခုတည်းမှ
edge ထောင်ချီ ပြန်လာနိုင်သည်။

---

## Exercise 3 — Subgraph → Prompt Context Serialization

```python
import itertools


def serialize_subgraph(node_ids, edge_indexes, max_tokens=4096):
    """Deterministic text block: entity lines first, then relation lines."""
    lines = []
    for node_id in sorted(node_ids):
        label, name, _aliases, summary = NODES[node_id]
        lines.append(f"[ENTITY] id={node_id} | label={label} | name={name} | summary={summary}")
    grouped = sorted((EDGES[i] for i in edge_indexes), key=lambda e: (e[0], e[1], e[2]))
    for src, group in itertools.groupby(grouped, key=lambda e: e[0]):
        lines += [f"[RELATION] {e[0]} -[{e[1]}]-> {e[2]}" for e in group]
    text = "\n".join(lines)
    return text if len(text) // 4 <= max_tokens else text[: max_tokens * 4]
```

တကယ်ရရှိသော output —

```text
[ENTITY] id=co:neo4j | label=Company | name=Neo4j | summary=Graph database vendor.
[ENTITY] id=org:neo4jeng | label=Team | name=Neo4j Engineering | summary=Engineering team maintaining Cypher.
[ENTITY] id=prod:aura | label=Product | name=AuraDB | summary=Managed cloud graph database service.
[ENTITY] id=tech:cypher | label=Technology | name=Cypher | summary=Declarative graph query language.
[ENTITY] id=tech:graphrag | label=Technology | name=GraphRAG | summary=Retrieval pattern grounded in a knowledge graph.
[ENTITY] id=tech:vectorindex | label=Technology | name=Vector Index | summary=Approximate nearest neighbour index over embeddings.
[RELATION] co:neo4j -[CREATES]-> tech:cypher
[RELATION] co:neo4j -[DEVELOPS]-> prod:aura
[RELATION] co:neo4j -[EMPLOYS]-> org:neo4jeng
[RELATION] co:neo4j -[PUBLISHES]-> tech:graphrag
[RELATION] prod:aura -[USES]-> tech:vectorindex
[RELATION] tech:cypher -[MAINTAINED_BY]-> org:neo4jeng
[RELATION] tech:graphrag -[RUNS_ON]-> prod:aura
[RELATION] tech:graphrag -[USES]-> tech:cypher
```

**အဓိကအယူအဆ** — Entity နှင့် relation ကို နှစ်ပိုင်း ခွဲထားခြင်းဖြင့် LLM သည် "ဤ node များ
တည်ရှိသည်" ဆိုသော အချက်နှင့် "ဤ node များ ဆက်စပ်သည်" ဆိုသော အချက်ကို ခွဲခြားဖတ်နိုင်သည်။
Sort order ကို သတ်မှတ်ထားခြင်းသည် prompt caching (prefix တူညီပါက cache hit) အတွက် အကျိုးရှိသည်။

---

## Exercise 4 — Hybrid Retrieval Fusion

```python
from collections import defaultdict


def reciprocal_rank_fusion(rankings, k=60):
    """RRF: score(item) = sum over lists of 1 / (k + rank). Tie-break by id asc."""
    scores = defaultdict(float)
    for items in rankings.values():
        for rank, item in enumerate(items, start=1):
            scores[item] += 1.0 / (k + rank)
    return sorted(scores.items(), key=lambda kv: (-kv[1], kv[0]))


def provenance_chunk(item):
    return item[4:] if item.startswith("vec:") else EDGES[int(item[6:])][3]


def dedupe_by_provenance(fused):
    """Keep one item per source chunk; on an equal score the graph triple wins."""
    best = {}
    for item, score in fused:
        chunk = provenance_chunk(item)
        prev = best.get(chunk)
        if prev is None or score > prev[1] or (score == prev[1] and item.startswith("graph:")):
            best[chunk] = (item, score)
    keep = {v[0] for v in best.values()}
    return [item for item, _ in fused if item in keep]
```

တကယ်ရရှိသော output —

```text
  graph:0    rrf=0.016393  chunk=c1  Neo4j AuraDB is a managed cloud service that
  vec:c1     rrf=0.016393  chunk=c1  Neo4j AuraDB is a managed cloud service that
  graph:4    rrf=0.016129  chunk=c2  Cypher is the declarative query language cre
  vec:c4     rrf=0.016129  chunk=c4  The Louvain method optimises modularity to d
  graph:6    rrf=0.015873  chunk=c3  GraphRAG grounds generation in knowledge gra
  vec:c2     rrf=0.015873  chunk=c2  Cypher is the declarative query language cre
fused=['graph:0', 'vec:c1', 'graph:4', 'vec:c4', 'graph:6', 'vec:c2']
final=['graph:0', 'graph:4', 'vec:c4', 'graph:6']
```

**အဓိကအယူအဆ** — RRF သည် score scale မလိုဘဲ rank ကိုသာ ယုံသည်၊ ထို့ကြောင့် cosine similarity
နှင့် graph relevance score ကို normalize လုပ်စရာ မလိုပါ။ `graph:0` နှင့် `vec:c1` သည် chunk
`c1` တစ်ခုတည်းမှ ဆင်းသက်သည် — တူညီသော အချက်အလက်ကို နှစ်ကြိမ် ပေးပို့ခြင်း context window ကို
ဖြုန်းတီးသည်၊ ထို့ကြောင့် provenance deduplication လိုအပ်သည်။ Score တူညီသောအခါ graph triple
ကို ဦးစားပေးသည်၊ အဘယ်ကြောင့်ဆိုသော် triple သည် normalized ဖြစ်ပြီး chunk ထက် တိုတောင်းသည်။

---

## Exercise 5 — Text-to-Cypher Guardrails

```python
BLOCK_COMMENT_RE = re.compile(r"/\*.*?\*/", re.DOTALL)
LINE_COMMENT_RE = re.compile(r"//[^\n]*")
STRING_LITERAL_RE = re.compile(r"'(?:[^'\\]|\\.)*'|\"(?:[^\"\\]|\\.)*\"")
REL_DETAIL_RE = re.compile(r"\[[^\]]*\]")
NODE_BLOCK_RE = re.compile(r"\(([^()]*)\)")
LABEL_RE = re.compile(r":\s*([A-Za-z_][A-Za-z0-9_]*)")

FORBIDDEN_KEYWORDS = ("CREATE", "MERGE", "DELETE", "DETACH", "SET", "REMOVE", "DROP",
                      "FOREACH", "LOAD", "CALL", "GRANT", "DENY", "REVOKE", "ALTER", "RENAME")
READ_ONLY_START = ("MATCH", "OPTIONAL MATCH", "WITH", "UNWIND")
MAX_LENGTH = 2000


def _strip_inert(query):
    """Remove comments and string literals: their content cannot mutate anything."""
    query = BLOCK_COMMENT_RE.sub(" ", query)
    return STRING_LITERAL_RE.sub(" '?' ", LINE_COMMENT_RE.sub(" ", query))


def node_labels(query):
    """Extract node labels only — relationship types are stripped first."""
    body = REL_DETAIL_RE.sub(" ", _strip_inert(query))
    return sorted({lab for block in NODE_BLOCK_RE.findall(body)
                   for lab in LABEL_RE.findall(block)})


def validate_cypher(query, allowed_labels=None, max_length=MAX_LENGTH):
    """Return (ok, reason). Read-only enforcement for LLM generated Cypher."""
    if not query or not query.strip():
        return False, "empty query"
    if len(query) > max_length:
        return False, f"query exceeds {max_length} characters"
    body = _strip_inert(query).strip()
    if body.endswith(";"):
        body = body[:-1].strip()
    if ";" in body:
        return False, "multiple statements are not allowed"
    words = set(re.findall(r"[A-Z_]+", body.upper()))
    hit = sorted(kw for kw in FORBIDDEN_KEYWORDS if kw in words)
    if hit:
        return False, f"destructive clause rejected: {', '.join(hit)}"
    first = body.split()[0].upper()
    if first not in READ_ONLY_START:
        return False, f"query must start with a read-only clause, got {first!r}"
    if "RETURN" not in words:
        return False, "query must project results with RETURN"
    if allowed_labels is not None:
        unknown = [lab for lab in node_labels(query) if lab not in allowed_labels]
        if unknown:
            return False, f"labels outside the schema allowlist: {', '.join(unknown)}"
    return True, "read-only query accepted"
```

**အဓိကအယူအဆ** — Validation အဆင့် ၅ ခု အစဉ်လိုက် ရှိသည်။ (၁) အလွတ် မဖြစ်ရ၊ အရှည် ကန့်သတ်ရ
(၂) statement တစ်ခုတည်း ဖြစ်ရ (၃) destructive keyword မပါရ (၄) read-only clause ဖြင့် စရ
(၅) ` RETURN` ပါရ၊ label များ schema အတွင်း ဖြစ်ရ။ `_strip_inert` သည် comment နှင့် string
literal ကို ဖယ်ရှားသည် — ထို content သည် database ပေါ်တွင် ဘာမှ မလုပ်နိုင်သောကြောင့် keyword
scan မှ ဖယ်ခြင်းသည် false positive ကို လျှော့သည်။ Relationship type ကို ကြိုတင် ဖယ်ရှားခြင်းဖြင့်
`-[:DEVELOPS]->` ကို node label ဟု မှားဖတ်ခြင်းမှ ကာကွယ်သည်။

**Security** — ဤ validator သည် defense in depth ၏ တစ်ဆင့်သာ ဖြစ်သည်။ Keyword blacklist ကို
obfuscation ဖြင့် ကျော်နိုင်နိုင်သောကြောင့် database user ကို read-only role ဖြင့် bind လုပ်ခြင်းနှင့်
`LIMIT` ကို server side တွင် အတင်းသတ်မှတ်ခြင်းကို မဖြစ်မနေ လုပ်ရမည်။

---

## Exercise 6 — Community Detection

```python
import math


def connected_components(adj):
    """Level-1 partition: cheap, deterministic, no resolution parameter."""
    labels, seen = {}, set()
    for start in sorted(adj):
        if start in seen:
            continue
        comp = {start}
        queue = deque([start])
        while queue:
            for nb in sorted(adj[queue.popleft()]):
                if nb not in comp:
                    comp.add(nb)
                    queue.append(nb)
        seen |= comp
        for node in comp:
            labels[node] = start
    return labels


def modularity(partition, adj):
    """Newman modularity Q = sum_c [ L_c/m - (k_c / 2m)^2 ]."""
    m = len(EDGES)
    internal, degree = defaultdict(int), defaultdict(int)
    for node in adj:
        degree[partition[node]] += len(adj[node])
    for src, _rel, dst, _chunk in EDGES:
        if partition[src] == partition[dst]:
            internal[partition[src]] += 1
    return round(sum(internal[lab] / m - (degree[lab] / (2 * m)) ** 2 for lab in degree), 10)


def greedy_modularity_partition(adj, init_labels):
    """Louvain-style single-level refinement: accept only improving moves."""
    labels = dict(init_labels)
    improved = True
    while improved:
        improved = False
        for node in sorted(adj):
            base = modularity(labels, adj)
            best_label, best_gain = labels[node], 1e-12
            for cand in sorted({labels[nb] for nb in adj[node]} - {labels[node]}):
                trial = dict(labels)
                trial[node] = cand
                gain = modularity(trial, adj) - base
                if gain > best_gain:
                    best_gain, best_label = gain, cand
            if best_label != labels[node]:
                labels[node] = best_label
                improved = True
    return labels


def canonicalize(labels):
    order = {}
    for node in sorted(labels):
        order.setdefault(labels[node], len(order))
    return {node: order[label] for node, label in labels.items()}


def community_summaries(labels):
    groups = defaultdict(list)
    for node, label in sorted(labels.items()):
        groups[label].append(node)
    return [(label, members, "Community %d covers: %s" % (
        label, ", ".join(sorted(NODES[m][1] for m in members))))
        for label, members in sorted(groups.items())]
```

တကယ်ရရှိသော output —

```text
level 0 (singletons)  communities=10 Q=-0.1145833333
level 1 (components)  communities=2 Q=0.4444444444
level 2 (refinement)  communities=2 Q=0.4444444444
  Community 0 covers: AuraDB, Cypher, GraphRAG, Neo4j, Neo4j Engineering, Vector Index
    members=['co:neo4j', 'org:neo4jeng', 'prod:aura', 'tech:cypher', 'tech:graphrag', 'tech:vectorindex']
  Community 1 covers: CNRS, Fast unfolding of communities in large networks, Louvain, Vincent Blondel
    members=['org:cnrs', 'paper:louvain', 'person:eifrem', 'tech:louvain']
```

**အဓိကအယူအဆ** — Hierarchy ၃ ဆင့်သည် retrieval granularity ၃ မျိုးကို ပေးသည်။ Level 0 (`Q` အနုတ်)
သည် trivial ဖြစ်ပြီး တန်ဖိုး မရှိပါ — ထိုအချက်သည် "community အရေအတွက် များလျှင် ကောင်းသည်"
ဆိုသော အမှားကို ဖော်ပြသည်။ Level 1 သည် parameter မလိုသော ဈေးသက်သာ partition ဖြစ်ပြီး
`Q = 4/9` ရသည်။ Level 2 ၏ greedy refinement သည် ရွှေ့မှု တိုင်းကို `Q` တက်မှသာ လက်ခံသောကြောင့်
`Q` သည် level 1 ထက် လျော့နိုင်မည် မဟုတ်ပါ။ Modularity တွက်ချက်မှုတွင် degree ကို `len(adj[node])`
ဖြင့် ရယူသည်၊ ထို့ကြောင့် `adj` သည် undirected graph ကို ကိုယ်စားပြုရမည်။

Community summary တိုင်းသည် global question အတွက် retrieval unit ဖြစ်လာသည်။ "corpus တစ်ခုလုံး
အကြောင်း ဘာပြောနိုင်သနည်း" မေးခွန်းတွင် level 1 summary နှစ်ခုလုံးကို ပေးရမည်၊ "Neo4j ecosystem
အကြောင်း" မေးခွန်းတွင် community 0 ၏ summary ကို ပေးရမည်။

---

## Evaluation Harness — Vector-only Baseline နှင့် နှိုင်းယှဉ်ခြင်း

```python
def recall_at_k(retrieved_ids, gold_ids, k):
    """Set intersection based recall — external package မလိုအပ်၊ deterministic ဖြစ်သည်။"""
    return len(set(gold_ids) & set(retrieved_ids[:k])) / len(set(gold_ids))


def context_token_cost(text):
    return len(text) // 4
```

**အဓိကအယူအဆ** — နှိုင်းယှဉ်မှုကို question set တစ်ခုတည်းပေါ်တွင် လုပ်ရမည်။ Multi-hop question
တွင် GraphRAG ၏ recall သည် baseline ထက် မြင့်သော်လည်း context token cost လည်း မြင့်သည်။
ထို့ကြောင့် cost ကို တွက်ချက်မှုထဲ ထည့်ရမည် — မဟုတ်ပါက "context window ပြည့်သော ဖြေချက်
ပိုဆိုးသော" စနစ်ကို အောင်မြင်သည်ဟု မှားယွင်း ကောက်ချက်ချနိုင်သည်။
