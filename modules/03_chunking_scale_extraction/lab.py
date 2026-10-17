#!/usr/bin/env python3
"""M03 — Chunking for Entity and Relationship Extraction at Scale.

Deterministic, offline reference lab. Standard library only — no numpy / networkx /
neo4j / requests and no `random` (a fixed-seed LCG supplies pseudo-randomness).
Run: python3 modules/03_chunking_scale_extraction/lab.py
"""
import hashlib
import re
import sys

CORPUS = (
    "Alpha acquired Beta . Beta operates Gamma . Gamma founded Delta . "
    "Delta partners Epsilon . Epsilon supplies Zeta . Zeta acquired Alpha ."
)
VERBS = frozenset({"acquired", "operates", "founded", "partners", "supplies"})
ENTITIES = frozenset({"Alpha", "Beta", "Gamma", "Delta", "Epsilon", "Zeta"})


def tokenize(text):
    """Word tokenization; punctuation is dropped so token count == word count."""
    return re.findall(r"[A-Za-z]+", text)


def chunk_words(words, size, overlap):
    """Fixed-size chunking; stride = size - overlap; no chunk is a subset of the previous."""
    if not 0 <= overlap < size:
        raise ValueError("require 0 <= overlap < size")
    stride = size - overlap
    n = len(words)
    chunks, start = [], 0
    while start < n:
        chunks.append(words[start:start + size])
        if start + size >= n:
            break
        start += stride
    return chunks


def chunk_hash(words):
    """Stable content hash — provenance / checkpoint key."""
    return hashlib.sha1(" ".join(words).encode("utf-8")).hexdigest()[:8]


def extract_triples(words, verbs=VERBS, entities=ENTITIES):
    """Map phase: emit a triple only when subject, verb and object share one chunk."""
    triples = []
    for i, token in enumerate(words):
        if token in verbs and 0 < i < len(words) - 1:
            subj, obj = words[i - 1], words[i + 1]
            if subj in entities and obj in entities:
                triples.append((subj, token, obj))
    return triples


def reconnect_boundary_triples(chunks, verbs=VERBS, entities=ENTITIES):
    """Reduce-side repair for relationships cut by a boundary (pattern A / B)."""
    recovered = []
    for i in range(len(chunks) - 1):
        left, right = chunks[i], chunks[i + 1]
        if not left or not right:
            continue
        if left[-1] in verbs and len(left) >= 2 and left[-2] in entities and right[0] in entities:
            recovered.append((left[-2], left[-1], right[0]))       # pattern A
        if right[0] in verbs and len(right) >= 2 and left[-1] in entities and right[1] in entities:
            recovered.append((left[-1], right[0], right[1]))       # pattern B
    return recovered


def triple_key(triple):
    return tuple(part.lower() for part in triple)


def merge_triples(records):
    """Deduplicate raw triples, folding provenance and confidence into one record per key."""
    merged = {}
    for rec in records:
        key = triple_key((rec["s"], rec["p"], rec["o"]))
        entry = merged.setdefault(key, {"s": rec["s"], "p": rec["p"], "o": rec["o"],
                                        "sources": [], "freq": 0})
        if rec["chunk_hash"] not in entry["sources"]:
            entry["sources"].append(rec["chunk_hash"])
        entry["freq"] += 1
    for entry in merged.values():
        entry["sources"].sort()
        entry["confidence"] = round(min(1.0, 0.5 + 0.25 * entry["freq"]), 2)
    return merged


class LCG:
    """Fixed-seed linear congruential generator — deterministic stand-in for `random`."""

    def __init__(self, seed=20261017):
        self.state = seed

    def next(self):
        self.state = (1103515245 * self.state + 12345) % (2 ** 31)
        return self.state

    def below(self, n):
        return self.next() % n


def run_batches(chunks, fail_plan, checkpoint, graph, batch_size=2,
                max_attempts=3, seed=20261017):
    """Idempotent, checkpointed, retrying batch runner over chunk word-lists.

    fail_plan holds (batch_id, attempt) pairs that abort BEFORE any write, so a retry
    re-runs the same unit and never half-writes it. graph = triple_key -> record
    (freq + sources), i.e. MERGE semantics. checkpoint = batch_id -> True once durable.
    """
    rng = LCG(seed)
    log = []
    batches = [chunks[i:i + batch_size] for i in range(0, len(chunks), batch_size)]
    for b_idx, batch in enumerate(batches):
        bid = "batch_%d" % b_idx
        if bid in checkpoint:
            log.append((bid, "skip", 0))
            continue
        attempt = 0
        while attempt < max_attempts:
            attempt += 1
            if (bid, attempt) in fail_plan:
                log.append((bid, "retry", round(0.5 + rng.below(4) * 0.25, 2)))
                continue
            for words in batch:
                chash = chunk_hash(words)
                for triple in extract_triples(words):
                    entry = graph.setdefault(triple_key(triple), {
                        "s": triple[0], "p": triple[1], "o": triple[2],
                        "freq": 0, "sources": []})
                    entry["freq"] += 1
                    if chash not in entry["sources"]:
                        entry["sources"].append(chash)
            checkpoint[bid] = True
            log.append((bid, "done", attempt))
            break
        else:
            log.append((bid, "failed", attempt))
    return log


def exercise_1() -> bool:
    print("\n--- Exercise 1: Fixed-size chunking ---")
    words = tokenize(CORPUS)
    chunks = chunk_words(words, size=6, overlap=0)
    print("token count : %d" % len(words))
    print("chunk count : %d" % len(chunks))
    print("chunk sizes : %s" % [len(c) for c in chunks])
    for i, c in enumerate(chunks):
        print("  chunk %d: %s" % (i, " ".join(c)))
    assert len(words) == 18
    assert len(chunks) == 3
    assert [len(c) for c in chunks] == [6, 6, 6]
    assert all(c == words[i * 6:(i + 1) * 6] for i, c in enumerate(chunks))
    return True


def exercise_2() -> bool:
    print("\n--- Exercise 2: Overlap selection ---")
    words = tokenize(CORPUS)
    no_overlap = chunk_words(words, size=6, overlap=0)
    with_overlap = chunk_words(words, size=6, overlap=2)
    print("overlap=0 -> %d chunks, sizes %s" % (len(no_overlap), [len(c) for c in no_overlap]))
    print("overlap=2 -> %d chunks, sizes %s" % (len(with_overlap), [len(c) for c in with_overlap]))
    for i, c in enumerate(with_overlap):
        print("  chunk %d: %s" % (i, " ".join(c)))
    for i in range(len(with_overlap) - 1):
        assert with_overlap[i][-2:] == with_overlap[i + 1][:2]
    assert len(with_overlap) == 4
    assert all(len(c) == 6 for c in with_overlap)
    assert with_overlap[0][-2:] == ["operates", "Gamma"]
    assert len(with_overlap) > len(no_overlap)      # overlap costs extra chunks
    return True


def exercise_3() -> bool:
    print("\n--- Exercise 3: Map-reduce triple aggregation ---")
    words = tokenize(CORPUS)
    chunks = chunk_words(words, size=6, overlap=0)
    records, per_chunk = [], []
    for c in chunks:
        mapped = extract_triples(c)
        per_chunk.append(len(mapped))
        for triple in mapped:
            records.append({"s": triple[0], "p": triple[1], "o": triple[2],
                            "chunk_hash": chunk_hash(c)})
    merged = merge_triples(records)
    print("map phase   : per-chunk triple counts %s" % per_chunk)
    print("map phase   : raw records %d" % len(records))
    print("reduce phase: unique triples %d" % len(merged))
    for key in sorted(merged):
        e = merged[key]
        print("  (%s) -[%s]-> (%s) freq=%d" % (e["s"], e["p"], e["o"], e["freq"]))
    assert per_chunk == [2, 2, 2]
    assert len(records) == 6
    assert len(merged) == 6
    assert all(e["freq"] == 1 for e in merged.values())
    return True


def exercise_4() -> bool:
    print("\n--- Exercise 4: Cross-chunk relationship reconnection ---")
    words = tokenize(CORPUS)
    chunks = chunk_words(words, size=5, overlap=0)
    print("chunk sizes: %s" % [len(c) for c in chunks])
    mapped = []
    for c in chunks:
        mapped.extend(extract_triples(c))
    recovered = reconnect_boundary_triples(chunks)
    print("mapped triples    : %d" % len(mapped))
    print("recovered triples : %d" % len(recovered))
    for t in recovered:
        print("  recovered: (%s) -[%s]-> (%s)" % t)
    combined = list(dict.fromkeys(mapped + recovered))
    print("combined unique   : %d" % len(combined))
    assert len(chunks) == 4
    assert len(mapped) == 4            # two sentences were split by a boundary
    assert len(recovered) == 2
    assert ("Beta", "operates", "Gamma") in recovered
    assert ("Delta", "partners", "Epsilon") in recovered
    assert len(combined) == 6
    return True


def exercise_5() -> bool:
    print("\n--- Exercise 5: Triple deduplication and merge ---")
    words = tokenize(CORPUS)
    chunks = chunk_words(words, size=5, overlap=3)
    records = []
    for c in chunks:
        chash = chunk_hash(c)
        for triple in extract_triples(c):
            records.append({"s": triple[0], "p": triple[1], "o": triple[2],
                            "chunk_hash": chash})
    merged = merge_triples(records)
    print("chunks %d -> raw records %d" % (len(chunks), len(records)))
    print("unique triples after dedup: %d" % len(merged))
    duplicated = sorted(k for k, e in merged.items() if e["freq"] > 1)
    for key in duplicated:
        e = merged[key]
        print("  dup (%s) -[%s]-> (%s) freq=%d confidence=%.2f sources=%d"
              % (e["s"], e["p"], e["o"], e["freq"], e["confidence"], len(e["sources"])))
    assert len(records) == 8
    assert len(merged) == 6
    assert len(duplicated) == 2
    assert merged[("gamma", "founded", "delta")]["freq"] == 2
    assert merged[("epsilon", "supplies", "zeta")]["freq"] == 2
    assert merged[("gamma", "founded", "delta")]["confidence"] == 1.0
    return True


def exercise_6() -> bool:
    print("\n--- Exercise 6: Idempotent batch runner ---")
    words = tokenize(CORPUS)
    chunks = chunk_words(words, size=5, overlap=3)
    print("chunks: %d, batch_size: 2 -> %d batches"
          % (len(chunks), (len(chunks) + 1) // 2))
    checkpoint, graph = {}, {}
    fail_plan = {("batch_2", 1)}
    log = run_batches(chunks, fail_plan, checkpoint, graph)
    print("run 1 log:")
    for bid, status, detail in log:
        print("  %s -> %-5s %s" % (bid, status, detail))
    print("committed batches: %d" % len(checkpoint))
    print("graph triples    : %d" % len(graph))
    assert len(checkpoint) == 4
    assert len(graph) == 6
    assert ("batch_2", "done", 2) in log     # succeeded on the second attempt
    assert ("batch_0", "done", 1) in log

    # Idempotency: a second run skips every committed batch and changes nothing.
    snapshot = {k: (e["freq"], tuple(sorted(e["sources"]))) for k, e in graph.items()}
    log2 = run_batches(chunks, fail_plan, checkpoint, graph)
    print("run 2 log: %s" % [(bid, st) for bid, st, _ in log2])
    snapshot2 = {k: (e["freq"], tuple(sorted(e["sources"]))) for k, e in graph.items()}
    assert all(st == "skip" for _, st, _ in log2)
    assert snapshot == snapshot2
    assert len(graph) == 6

    # Failure recovery: no retry headroom -> the batch stays uncommitted, no partial write.
    checkpoint_b, graph_b = {}, {}
    log_b = run_batches(chunks, {("batch_1", 1), ("batch_1", 2), ("batch_1", 3)},
                        checkpoint_b, graph_b, max_attempts=2)
    failed = [bid for bid, st, _ in log_b if st == "failed"]
    print("no-headroom failing batches: %s" % failed)
    assert failed == ["batch_1"]
    assert "batch_1" not in checkpoint_b
    return True


def run_all() -> bool:
    results = [
        exercise_1(),
        exercise_2(),
        exercise_3(),
        exercise_4(),
        exercise_5(),
        exercise_6(),
    ]
    if all(results):
        print("\n[PASS] All 6/6 exercises passed successfully.")
        return True
    return False


if __name__ == "__main__":
    sys.exit(0 if run_all() else 1)
