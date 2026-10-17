# Walkthrough 04 — Incremental update planner (Exercise 4)

> ဤဖိုင်သည် Module 08 ၏ `solution.md` ထဲက Exercise 4 ကို **Python အခြေခံမှ စ၍**
> အပိုင်းလိုက် ရှင်းပြသည့် walkthrough ဖြစ်သည်။

---

## 0. ဤ Exercise က ဘာကို ဖြေရှင်းပေးသလဲ။

Document အသစ်တစ်ခု ဝင်လာတိုင်း graph တစ်ခုလုံးကို ပြန်တည်ဆောက်ရင် ကုန်ကျစရိတ်
အလွန်မြင့်ပါတယ်။ ပိုကောင်းတဲ့ နည်းက **ကွာခြားချက် (diff) ကိုသာ** ရေးတာပါ။
လက်ရှိ graph နဲ့ triple အသစ်များကို နှိုင်းယှဉ်ပြီး လိုအပ်တဲ့ operation များကို
ထုတ်ပေးပါတယ်။

```text
current edges/nodes + new triples
        |
        v
   diff planner  --->  [ADD_NODE / DELETE_EDGE / ADD_EDGE / NOOP]
        |
        v
   updated graph  --->  signature (hash) ဖြင့် စစ်ဆေး
```

**Idempotency** အရေးကြီးပါတယ် — document တူတူကို နှစ်ခါ ingest လုပ်ရင် graph က
**မပြောင်း** ရပါ။ ဤ code က signature-based verification ဖြင့် ဒါကို စစ်ပါတယ်။

ဒီ Exercise မှာ လေ့လာရမယ့် Python concepts —

- Set (`{"LEADS", "MANAGES"}`) နှင့် `in` membership test
- List of tuples နှင့် tuple indexing (`e[1]`, `e[2]`)
- `json.dumps(..., sort_keys=True)` နှင့် tuple → JSON array
- `hashlib.sha256(...).hexdigest()` နှင့် slicing `[:16]`
- List comprehension ဖြင့် filter
- Tuple concatenation (`("DELETE_EDGE",) + old_edge`)
- `continue` နှင့် early skip
- `list(copy)` နှင့် `set(copy)`

---

## 1. Graph ကို Data အဖြစ် ဖော်ပြခြင်း

```python
base_edges = [
    ("Alice", "MANAGES", "Payments Squad"),
    ("Bob", "SUPPORTS", "Ledger Service"),
    ("Carol", "LEADS", "Payments Squad"),
    ("Ledger Service", "STORES_DATA_IN", "Audit Store"),
    ("Payments Squad", "BUILDS", "Ledger Service"),
]
base_nodes = {"Alice", "Audit Store", "Bob", "Carol", "Ledger Service", "Payments Squad"}

print(base_edges[0])
print(base_edges[0][1])
print(len(base_edges), len(base_nodes))
```

Output —

```text
('Alice', 'MANAGES', 'Payments Squad')
MANAGES
5 6
```

Edge တိုင်းက **tuple သုံးလုံး** — `(subject, relation, object)`။ `base_edges[0][1]` က
ပထမဆုံး edge ၏ **ဒုတိယ item** `MANAGES` ကို ဆွဲထုတ်ပါတယ်။

Node စာရင်းကို **set** အဖြစ် ထားပါတယ်။ Set က duplicate ကို ဖယ်ပေးပြီး membership
စစ်တာ O(1) ဖြစ်ပါတယ် — planner က `endpoint not in nodes` ကို node တိုင်းအတွက်
ခေါ်လို့ အရေးကြီးပါတယ်။

> **သတိ** — set ကို `print()` ဖြင့် တိုက်ရိုက် ပြရင် အစီအစဉ်က run တစ်ခုနှင့်တစ်ခု
> **ကွဲနိုင်သည်** (hash-randomised)။ ထို့ကြောင့် set ကို ပြသည့်အခါ `sorted(...)`
> ဖြင့် ပြပါ။

```python
base_nodes = {"Alice", "Audit Store", "Bob", "Carol", "Ledger Service", "Payments Squad"}
print(sorted(base_nodes))
print("Bob" in base_nodes)
print("Dave" in base_nodes)
```

Output —

```text
['Alice', 'Audit Store', 'Bob', 'Carol', 'Ledger Service', 'Payments Squad']
True
False
```

`sorted(base_nodes)` က set ကို list အဖြစ် စီပြီး ပြသပါတယ် — output က run တိုင်း တူပါတယ်။
`"Dave" in base_nodes` က `False` ရတာက `Dave` ကို နောက်ပိုင်း `ADD_NODE` လုပ်ရမည့်
အကြောင်းရင်း ဖြစ်ပါတယ်။

---

## 2. `graph_signature()` — Content Hash

```python
import json
import hashlib


def graph_signature(edges, nodes):
    payload = json.dumps({"nodes": sorted(nodes), "edges": sorted(edges)}, sort_keys=True)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()[:16]
```

### 2.1 `sorted(nodes)` နှင့် `sorted(edges)`

Node နဲ့ edge ကို **စီ** လိုက်တာက hash ကို **တည်ငြိမ်** စေပါတယ်။ စီမထားရင် set
iteration order က run တိုင်း ကွဲနိုင်လို့ hash လည်း ပြောင်းနိုင်ပါတယ်။

```python
import json

payload = json.dumps({"nodes": ["b", "a"], "edges": [("x", "r", "y")]})
print(payload)
print(repr(json.dumps({"nodes": ["a", "b"], "edges": [("x", "r", "y")]})))
```

Output —

```text
{"nodes": ["b", "a"], "edges": [["x", "r", "y"]]}
'{"nodes": ["a", "b"], "edges": [["x", "r", "y"]]}'
```

Tuple `("x", "r", "y")` ကို JSON မှာ **array** `["x", "r", "y"]` အဖြစ်
ပြောင်းပါတယ်။

### 2.2 `sort_keys=True` — Key များကို စီခြင်း

```python
import json

a = json.dumps({"nodes": ["b", "a"], "edges": [("x", "r", "y")]}, sort_keys=True)
b = json.dumps({"edges": [("x", "r", "y")], "nodes": ["b", "a"]}, sort_keys=True)
print(a)
print(a == b)
```

Output —

```text
{"edges": [["x", "r", "y"]], "nodes": ["b", "a"]}
True
```

`sort_keys=True` က dict ၏ key များကို **alphabetical** စီစေပါတယ် — `"edges"` က
`"nodes"` အရင်။ Dict ကို ရေးတဲ့အစီအစဉ် မတူပေမဲ့ `sort_keys=True` ရှိလို့
string နှစ်ခု **တူညီ** သွားပါတယ်။ ဒါက hash ကို reproducible ဖြစ်စေပါတယ်။

### 2.3 `hashlib.sha256(...).hexdigest()[:16]`

```python
import hashlib

print(hashlib.sha256(b"abc").hexdigest())
print(hashlib.sha256(b"abc").hexdigest()[:8])
print(len(hashlib.sha256(b"abc").hexdigest()))
```

Output —

```text
ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad
ba7816bf
64
```

`sha256` က byte sequence တစ်ခုအတွက် **hexadecimal 64 character** (32 byte) hash
ထုတ်ပါတယ်။ `.encode("utf-8")` က string ကို byte အဖြစ် ပြောင်းပါတယ် — hash
function များက byte ကိုသာ လက်ခံလို့ပါ။ `[:16]` က ပထမ ၁၆ လုံးကိုသာ ယူပါတယ် —
ကျန်တာအားလုံး နှိုင်းယှဉ်စရာ မလိုဘဲ လုံလောက်ပါတယ်။

---

## 3. `plan_incremental_update()` — Function ဖွဲ့စည်းပုံ

```python
SINGLE_VALUED = {"LEADS", "MANAGES"}


def plan_incremental_update(current_edges, current_nodes, new_triples):
    edges = list(current_edges)
    nodes = set(current_nodes)
    ops = []
    for subject, relation, obj in new_triples:
        for endpoint in (subject, obj):
            if endpoint not in nodes:
                nodes.add(endpoint)
                ops.append(("ADD_NODE", endpoint))
        new_edge = (subject, relation, obj)
        if new_edge in edges:
            ops.append(("NOOP", subject, relation, obj))
            continue
        if relation in SINGLE_VALUED:
            stale = [e for e in edges if e[1] == relation and e[2] == obj]
            for old_edge in stale:
                edges.remove(old_edge)
                ops.append(("DELETE_EDGE",) + old_edge)
        edges.append(new_edge)
        ops.append(("ADD_EDGE", subject, relation, obj))
    return ops, edges, nodes
```

### 3.1 `list(current_edges)` နှင့် `set(current_nodes)` — Copy

`edges = list(current_edges)` က **copy** တစ်ခု ဖန်တီးပါတယ်။ ဒါကြောင့် function က
`edges.remove(...)` လုပ်လို့ caller ၏ `current_edges` **မပြောင်း** ပါ။ ဒါက
immutability ကို ထိန်းပြီး caller က base graph ကို ပြန်သုံးလို့ ရပါတယ်။

```python
original = [("A", "FRIEND", "B")]
copy = list(original)
copy.append(("C", "FRIEND", "D"))
print(original)
print(copy)
```

Output —

```text
[('A', 'FRIEND', 'B')]
[('A', 'FRIEND', 'B'), ('C', 'FRIEND', 'D')]
```

### 3.2 `SINGLE_VALUED` — Single-valued Relationship များ

```python
SINGLE_VALUED = {"LEADS", "MANAGES"}
print("LEADS" in SINGLE_VALUED)
print("BUILDS" in SINGLE_VALUED)
print(sorted(SINGLE_VALUED))
```

Output —

```text
True
False
['LEADS', 'MANAGES']
```

`LEADS` နဲ့ `MANAGES` က **single-valued** ဖြစ်ပါတယ် — subject တစ်ခုတည်းသာ
object တစ်ခုတည်းကို leads/manages လုပ်နိုင်ပါတယ်။ \"ဘယ်သူက Payments Squad ကို
leads\" ဆိုတဲ့ question မှာ အဖြေ **တစ်ခုတည်း** ဖြစ်ရပါတယ်။ `BUILDS` ကတော့
single-valued မဟုတ်ပါ (service တစ်ခုကို အဖွဲ့အများအပြား build လုပ်နိုင်)။

---

## 4. Endpoint Loop — `ADD_NODE`

```python
nodes = {"Alice", "Payments Squad"}
ops = []
for endpoint in ("Dave", "Payments Squad"):
    if endpoint not in nodes:
        nodes.add(endpoint)
        ops.append(("ADD_NODE", endpoint))
print(ops)
print(sorted(nodes))
```

Output —

```text
[('ADD_NODE', 'Dave')]
['Alice', 'Dave', 'Payments Squad']
```

`for endpoint in (subject, obj):` က subject နဲ့ object **နှစ်ခုလုံး** ကို စစ်ပါတယ်။
မရှိသေးတဲ့ endpoint တိုင်းအတွက် `nodes.add(...)` နဲ့ `("ADD_NODE", endpoint)`
operation ထည့်ပါတယ်။ `"Payments Squad"` က ရှိပြီးလို့ ကျော်သွားပါတယ်။

---

## 5. `NOOP` Branch — `in` နှင့် `continue`

```python
edges = [("A", "FRIEND", "B")]
ops = []
for subject, relation, obj in [("A", "FRIEND", "B")]:
    new_edge = (subject, relation, obj)
    if new_edge in edges:
        ops.append(("NOOP", subject, relation, obj))
        continue
    edges.append(new_edge)
    ops.append(("ADD_EDGE", subject, relation, obj))
print(ops)
print(edges)
```

Output —

```text
[('NOOP', 'A', 'FRIEND', 'B')]
[('A', 'FRIEND', 'B')]
```

`new_edge in edges` က triple က ရှိပြီးသား လား စစ်ပါတယ် — tuple comparison ဖြစ်လို့
item တိုင်း တူညီရပါတယ်။ ရှိပြီးရင် `"NOOP"` (no operation) မှတ်ပြီး `continue` ဖြင့်
loop ၏ ကျန်တာ မလုပ်တော့ပါ။ **`continue` က ဒီ iteration ကို ရပ်ပြီး နောက်
iteration ကို ဆက်သည်**။

```python
for number in [1, 2, 3, 4]:
    if number % 2 == 0:
        continue
    print(number, "is odd")
```

Output —

```text
1 is odd
3 is odd
```

---

## 6. Single-valued အတွက် `DELETE_EDGE` — List Comprehension Filter

```python
edges = [
    ("Carol", "LEADS", "Payments Squad"),
    ("Alice", "MANAGES", "Payments Squad"),
    ("Dave", "LEADS", "Other"),
]
relation, obj = "LEADS", "Payments Squad"
stale = [e for e in edges if e[1] == relation and e[2] == obj]
print(stale)
```

Output —

```text
[('Carol', 'LEADS', 'Payments Squad')]
```

`[e for e in edges if e[1] == relation and e[2] == obj]` က **list comprehension**
ဖြစ်ပါတယ်။ `e[1]` က relation၊ `e[2]` က object။ Condition နှစ်ခုလုံး မှန်တဲ့ edge
များကို စုပါတယ် — ဒီနေရာမှာ `("Dave", "LEADS", "Other")` က object မတူလို့ မပါပါ။
အလွတ် list `[]` ရရင်လည်း ရပါတယ် —

```python
edges = [("Alice", "MANAGES", "Payments Squad")]
print([e for e in edges if e[1] == "LEADS" and e[2] == "Payments Squad"])
```

Output —

```text
[]
```

### 6.1 Tuple Concatenation — `("DELETE_EDGE",) + old_edge`

```python
old_edge = ("Carol", "LEADS", "Payments Squad")
op = ("DELETE_EDGE",) + old_edge
print(op)
print(op[0])
print(op[1:])
```

Output —

```text
('DELETE_EDGE', 'Carol', 'LEADS', 'Payments Squad')
DELETE_EDGE
('Carol', 'LEADS', 'Payments Squad')
```

`("DELETE_EDGE",)` မှာ comma ပါတာကို သတိထားပါ — comma မပါရင် `("DELETE_EDGE")`
သည် tuple မဟုတ်ဘဲ **string သက်သက်** ဖြစ်ပါတယ်။ `+` က tuple နှစ်ခုကို
**ဆက်စပ်** ပေးလို့ `("DELETE_EDGE", "Carol", "LEADS", "Payments Squad")`
၄ လုံး tuple ရပါတယ်။

```python
print(("DELETE_EDGE")[0])
print(("DELETE_EDGE",)[0])
print(type(("DELETE_EDGE")))
print(type(("DELETE_EDGE",)))
```

Output —

```text
D
DELETE_EDGE
<class 'str'>
<class 'tuple'>
```

---

## 7. Planner Run — Ops နှင့် Signature

```python
import json
import hashlib

SINGLE_VALUED = {"LEADS", "MANAGES"}


def graph_signature(edges, nodes):
    payload = json.dumps({"nodes": sorted(nodes), "edges": sorted(edges)}, sort_keys=True)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()[:16]


def plan_incremental_update(current_edges, current_nodes, new_triples):
    edges = list(current_edges)
    nodes = set(current_nodes)
    ops = []
    for subject, relation, obj in new_triples:
        for endpoint in (subject, obj):
            if endpoint not in nodes:
                nodes.add(endpoint)
                ops.append(("ADD_NODE", endpoint))
        new_edge = (subject, relation, obj)
        if new_edge in edges:
            ops.append(("NOOP", subject, relation, obj))
            continue
        if relation in SINGLE_VALUED:
            stale = [e for e in edges if e[1] == relation and e[2] == obj]
            for old_edge in stale:
                edges.remove(old_edge)
                ops.append(("DELETE_EDGE",) + old_edge)
        edges.append(new_edge)
        ops.append(("ADD_EDGE", subject, relation, obj))
    return ops, edges, nodes


base_edges = [
    ("Alice", "MANAGES", "Payments Squad"),
    ("Bob", "SUPPORTS", "Ledger Service"),
    ("Carol", "LEADS", "Payments Squad"),
    ("Ledger Service", "STORES_DATA_IN", "Audit Store"),
    ("Payments Squad", "BUILDS", "Ledger Service"),
]
base_nodes = {"Alice", "Audit Store", "Bob", "Carol", "Ledger Service", "Payments Squad"}
before = graph_signature(base_edges, base_nodes)

ops, edges, nodes = plan_incremental_update(base_edges, base_nodes,
                                            [("Dave", "LEADS", "Payments Squad")])
for op in ops:
    print("  " + " ".join(str(part) for part in op))
after = graph_signature(edges, nodes)
print("base signature=%s -> updated signature=%s" % (before, after))
```

Output —

```text
  ADD_NODE Dave
  DELETE_EDGE Carol LEADS Payments Squad
  ADD_EDGE Dave LEADS Payments Squad
base signature=5354f4bd285ccbb7 -> updated signature=94ac803b9cd59a9f
```

Operation သုံးခု ထွက်ပါတယ် —

| အစဉ် | Op | အကြောင်းရင်း |
| --- | --- | --- |
| 1 | `ADD_NODE Dave` | `Dave` က node စာရင်းတွင် မရှိ |
| 2 | `DELETE_EDGE Carol LEADS Payments Squad` | `LEADS` က single-valued — အဟောင်း ဖယ်ရှား |
| 3 | `ADD_EDGE Dave LEADS Payments Squad` | edge အသစ် ထည့် |

`" ".join(str(part) for part in op)` က tuple ထဲက item တိုင်းကို string အဖြစ်
ပြောင်းပြီး space နဲ့ ဆက်ပါတယ်။ `str(part)` မလိုဘဲ `" ".join(op)` ရေးရင် item များ
string မဟုတ်လို့ `TypeError` ဖြစ်ပါတယ်။

```python
print(" ".join(str(part) for part in ("ADD_NODE", "Dave")))
```

Output —

```text
ADD_NODE Dave
```

---

## 8. Second Run — Idempotency

```python
import json
import hashlib

SINGLE_VALUED = {"LEADS", "MANAGES"}


def graph_signature(edges, nodes):
    payload = json.dumps({"nodes": sorted(nodes), "edges": sorted(edges)}, sort_keys=True)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()[:16]


def plan_incremental_update(current_edges, current_nodes, new_triples):
    edges = list(current_edges)
    nodes = set(current_nodes)
    ops = []
    for subject, relation, obj in new_triples:
        for endpoint in (subject, obj):
            if endpoint not in nodes:
                nodes.add(endpoint)
                ops.append(("ADD_NODE", endpoint))
        new_edge = (subject, relation, obj)
        if new_edge in edges:
            ops.append(("NOOP", subject, relation, obj))
            continue
        if relation in SINGLE_VALUED:
            stale = [e for e in edges if e[1] == relation and e[2] == obj]
            for old_edge in stale:
                edges.remove(old_edge)
                ops.append(("DELETE_EDGE",) + old_edge)
        edges.append(new_edge)
        ops.append(("ADD_EDGE", subject, relation, obj))
    return ops, edges, nodes


base_edges = [
    ("Alice", "MANAGES", "Payments Squad"),
    ("Bob", "SUPPORTS", "Ledger Service"),
    ("Carol", "LEADS", "Payments Squad"),
    ("Ledger Service", "STORES_DATA_IN", "Audit Store"),
    ("Payments Squad", "BUILDS", "Ledger Service"),
]
base_nodes = {"Alice", "Audit Store", "Bob", "Carol", "Ledger Service", "Payments Squad"}
first_ops, edges, nodes = plan_incremental_update(base_edges, base_nodes,
                                                  [("Dave", "LEADS", "Payments Squad")])
after = graph_signature(edges, nodes)
again_ops, again_edges, again_nodes = plan_incremental_update(edges, nodes,
                                                             [("Dave", "LEADS", "Payments Squad")])
print(again_ops)
print(graph_signature(again_edges, again_nodes) == after)
```

Output —

```text
[('NOOP', 'Dave', 'LEADS', 'Payments Squad')]
True
```

Document တူတူကို ဒုတိယအကြိမ် ingest လုပ်ရင် triple က ရှိပြီးသားဖြစ်လို့ `NOOP` **သာ**
ထွက်ပါတယ်။ Graph မပြောင်းလို့ signature လည်း **တူညီ** နေပါတယ်။ ဒါက
**idempotency** ၏ အထောက်အထားပါ — operation တိုင်းကို diff အဖြစ် ဖော်ခြင်းဖြင့်
ရရှိပါတယ်။

---

## 9. အခြေအနေ တစ်ခုချင်း၏ Operation ရလဒ်

| New triples | Current graph အခြေအနေ | ထွက်သည့် ops |
| --- | --- | --- |
| `("Dave","LEADS","Payments Squad")` | `Dave` မရှိ၊ `Carol` က leads | `ADD_NODE Dave`၊ `DELETE_EDGE Carol LEADS Payments Squad`၊ `ADD_EDGE Dave LEADS Payments Squad` |
| `("Dave","LEADS","Payments Squad")` (ဒုတိယအကြိမ်) | `Dave` က leads ပြီးသား | `NOOP` |
| `("X","LEADS","Y")` | graph အလွတ် | `ADD_NODE X`၊ `ADD_NODE Y`၊ `ADD_EDGE X LEADS Y` |
| `("A","FRIEND","B")` | `("A","FRIEND","B")` ရှိပြီးသား | `NOOP` |

`FRIEND` က `SINGLE_VALUED` မဟုတ်လို့ `ADD_EDGE` လုပ်တဲ့အခါ အဟောင်း မဖယ်ပါ။

---

## 10. Code တစ်ခုလုံး — Run လုပ်နိုင်သော Version

```python
import json
import hashlib

SINGLE_VALUED = {"LEADS", "MANAGES"}


def graph_signature(edges, nodes):
    payload = json.dumps({"nodes": sorted(nodes), "edges": sorted(edges)}, sort_keys=True)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()[:16]


def plan_incremental_update(current_edges, current_nodes, new_triples):
    edges = list(current_edges)
    nodes = set(current_nodes)
    ops = []
    for subject, relation, obj in new_triples:
        for endpoint in (subject, obj):
            if endpoint not in nodes:
                nodes.add(endpoint)
                ops.append(("ADD_NODE", endpoint))
        new_edge = (subject, relation, obj)
        if new_edge in edges:
            ops.append(("NOOP", subject, relation, obj))
            continue
        if relation in SINGLE_VALUED:
            stale = [e for e in edges if e[1] == relation and e[2] == obj]
            for old_edge in stale:
                edges.remove(old_edge)
                ops.append(("DELETE_EDGE",) + old_edge)
        edges.append(new_edge)
        ops.append(("ADD_EDGE", subject, relation, obj))
    return ops, edges, nodes


base_edges = [
    ("Alice", "MANAGES", "Payments Squad"),
    ("Bob", "SUPPORTS", "Ledger Service"),
    ("Carol", "LEADS", "Payments Squad"),
    ("Ledger Service", "STORES_DATA_IN", "Audit Store"),
    ("Payments Squad", "BUILDS", "Ledger Service"),
]
base_nodes = {"Alice", "Audit Store", "Bob", "Carol", "Ledger Service", "Payments Squad"}
before = graph_signature(base_edges, base_nodes)

ops, edges, nodes = plan_incremental_update(base_edges, base_nodes,
                                            [("Dave", "LEADS", "Payments Squad")])
for op in ops:
    print("  " + " ".join(str(part) for part in op))
after = graph_signature(edges, nodes)
print("base signature=%s -> updated signature=%s" % (before, after))

again_ops, again_edges, again_nodes = plan_incremental_update(edges, nodes,
                                                             [("Dave", "LEADS", "Payments Squad")])
print("re-apply ops:", again_ops)
print("idempotent:", graph_signature(again_edges, again_nodes) == after)
```

Output —

```text
  ADD_NODE Dave
  DELETE_EDGE Carol LEADS Payments Squad
  ADD_EDGE Dave LEADS Payments Squad
base signature=5354f4bd285ccbb7 -> updated signature=94ac803b9cd59a9f
re-apply ops: [('NOOP', 'Dave', 'LEADS', 'Payments Squad')]
idempotent: True
```

---

## 11. ရလဒ်ကို ပြန်ကြည့်ခြင်း

| စစ်ဆေးချက် | Code | ရလဒ် |
| --- | --- | --- |
| Carol lead ဖယ်ခံရ | `("Carol","LEADS","Payments Squad") not in edges` | `True` |
| Dave lead ဖြစ်လာ | `("Dave","LEADS","Payments Squad") in edges` | `True` |
| Node အသစ် ထည့် | `len(nodes) == len(base_nodes) + 1` | `True` |
| ဒုတိယအကြိမ် NOOP သာ | `[op[0] for op in again_ops] == ["NOOP"]` | `True` |
| Signature မပြောင်း | `graph_signature(again) == after` | `True` |
| Signature တကယ် ပြောင်း | `after != before` | `True` |

Node တူညီသော Relationship နှစ်ခု ဆက်ရှိနေပါက \"ဘယ်သူက Leads\" ဆိုသည့်
question သည် အဖြေနှစ်ခု ရနိုင်ပြီး generator သည် မှားနိုင်ပါတယ်။ ထို့ကြောင့်
single-valued Relationship ကို အဟောင်း ဖယ်ရှားရပါတယ်။

---

## 12. ကိုယ်တိုင်လေ့ကျင့်ကြည့်ပါ

**မေးခွန်း** — အောက်ပါ code က ဘယ် `ops` ကို ပြန်ပေးမလဲ။

```python
SINGLE_VALUED = {"LEADS", "MANAGES"}

edges = [("Carol", "LEADS", "Payments Squad")]
nodes = {"Carol", "Payments Squad"}
ops = []
for subject, relation, obj in [("Alice", "MANAGES", "Payments Squad")]:
    for endpoint in (subject, obj):
        if endpoint not in nodes:
            nodes.add(endpoint)
            ops.append(("ADD_NODE", endpoint))
    new_edge = (subject, relation, obj)
    if new_edge in edges:
        ops.append(("NOOP", subject, relation, obj))
        continue
    if relation in SINGLE_VALUED:
        stale = [e for e in edges if e[1] == relation and e[2] == obj]
        for old_edge in stale:
            edges.remove(old_edge)
            ops.append(("DELETE_EDGE",) + old_edge)
    edges.append(new_edge)
    ops.append(("ADD_EDGE", subject, relation, obj))
print(ops)
```

1. `[("ADD_NODE", "Alice"), ("DELETE_EDGE", "Carol", "LEADS", "Payments Squad"), ("ADD_EDGE", "Alice", "MANAGES", "Payments Squad")]`
2. `[("ADD_NODE", "Alice"), ("ADD_EDGE", "Alice", "MANAGES", "Payments Squad")]`
3. `[("DELETE_EDGE", "Carol", "LEADS", "Payments Squad"), ("ADD_EDGE", "Alice", "MANAGES", "Payments Squad")]`
4. `[("ADD_NODE", "Alice"), ("NOOP", "Alice", "MANAGES", "Payments Squad")]`

<details>
<summary>အဖြေ ကြည့်ရန်</summary>

**အဖြေ — 2. `[("ADD_NODE", "Alice"), ("ADD_EDGE", "Alice", "MANAGES", "Payments Squad")]`**

အကြောင်းရင်း — `Alice` က `nodes` တွင် မရှိသဖြင့် `ADD_NODE Alice` ထွက်သည်။
`Payments Squad` က ရှိပြီးသားမို့ ကျော်သည်။ `new_edge` က `edges` တွင် မရှိသဖြင့်
`NOOP` မဟုတ်ပါ။

အဓိက — `stale` filter က `e[1] == "MANAGES" and e[2] == "Payments Squad"` ဖြစ်သည်။
လက်ရှိ edge က `("Carol", "LEADS", "Payments Squad")` ဖြစ်လို့ `e[1]` က `"LEADS"` —
`"MANAGES"` နှင့် မကိုက်ညီပါ။ ထို့ကြောင့် `stale` က အလွတ် `[]` ဖြစ်ပြီး
`DELETE_EDGE` **မထွက်** ပါ။ ဆန့်ကျင်ဘက် relation ကို ရှာသဖြင့် Carol မဖယ်ခံရပါ —
graph တွင် `MANAGES` နှင့် `LEADS` သည် relation မတူလို့ နှစ်ခုလုံး ဆက်ရှိသည်။

</details>

---

**အဓိက မှတ်ထားရန်** — Idempotency သည် `MERGE` ကို သုံးခြင်းဖြင့် အလိုအလျောက်
မရနိုင်ဘဲ၊ operation တိုင်းကို diff အဖြစ် ဖော်ခြင်းဖြင့် ရပါတယ်။ Signature-based
verification သည် re-ingestion ကြောင့် graph မပြောင်းကြောင်း test အတွက် တိကျတဲ့
အထောက်အထား ဖြစ်ပါတယ်။ Set display order က run တိုင်း ကွဲနိုင်လို့ output မှာ
`sorted()` ဖြင့် ပြသရန် လိုပါတယ်။
