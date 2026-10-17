#!/usr/bin/env python3
"""
Master Knowledge Graph Retrieval-Augmented Generation with Neo4j
Automated lab runner.

Runs every module lab locally and reports deterministic pass/fail per module.

Usage:
    python3 run_all_labs.py
    python3 run_all_labs.py --module 06
    python3 run_all_labs.py --verbose
"""

import argparse
import os
import subprocess
import sys
import time

MODULE_DESCRIPTIONS = {
    "00_getting_started": "Course Architecture & the Path to Graph RAG",
    "01_traditional_ner_relation_extraction": "NER, BIO Tagging & Relationship Extraction",
    "02_llm_entity_relation_extraction": "LLM-based Extraction, Schema & Entity Resolution",
    "03_chunking_scale_extraction": "Chunking Strategy & Map-Reduce Extraction at Scale",
    "04_project_create_knowledge_graph": "Project — End-to-End Knowledge Graph from Text",
    "05_neo4j_introduction": "Neo4j, Property Graph Model & Cypher Fundamentals",
    "06_storing_entities_relationships_neo4j": "Graph Write Path, MERGE/UNWIND & Idempotency",
    "07_knowledge_graph_rag": "GraphRAG Retrieval Patterns, Hybrid Fusion & Text-to-Cypher",
    "08_conclusion": "Production Deployment, Decision Criteria & Capstone Design",
}


def main():
    parser = argparse.ArgumentParser(description="Run the GraphRAG course module labs")
    parser.add_argument("--module", "-m", help="Run a single module (e.g. 06 or 06_storing_entities_relationships_neo4j)")
    parser.add_argument("--verbose", "-v", action="store_true", help="Print full stdout from each lab")
    args = parser.parse_args()

    root_dir = os.path.dirname(os.path.abspath(__file__))
    modules_dir = os.path.join(root_dir, "modules")

    available = sorted(
        m for m in os.listdir(modules_dir)
        if os.path.isdir(os.path.join(modules_dir, m))
        and os.path.exists(os.path.join(modules_dir, m, "lab.py"))
    )

    if args.module:
        selected = [m for m in available if args.module in m]
        if not selected:
            print(f"[ERROR] No module matched '{args.module}'. Available: {', '.join(available)}")
            sys.exit(1)
        available = selected

    print("=" * 84)
    print(" Master Knowledge Graph RAG with Neo4j — Automated Lab Suite")
    print(f" Python: {sys.version.split()[0]}  ({sys.executable})")
    print(f" Modules selected: {len(available)}")
    print("=" * 84)

    summary = []
    t_start = time.time()

    for mod in available:
        lab_path = os.path.join(modules_dir, mod, "lab.py")
        desc = MODULE_DESCRIPTIONS.get(mod, mod)
        print(f"\n[RUNNING] {mod} — {desc}", flush=True)

        t0 = time.time()
        res = subprocess.run([sys.executable, lab_path], capture_output=True, text=True)
        dur = time.time() - t0

        passed = res.returncode == 0
        n_ex = sum(1 for ln in res.stdout.splitlines() if ln.startswith("--- Exercise"))

        summary.append({
            "module": mod,
            "desc": desc,
            "exercises": n_ex,
            "status": "PASS" if passed else "FAIL",
            "duration": dur,
            "stdout": res.stdout,
            "stderr": res.stderr,
        })

        if args.verbose or not passed:
            print(res.stdout)
            if res.stderr:
                print("[STDERR]\n" + res.stderr)
        else:
            n = summary[-1]["exercises"] if n_ex else "?"
            print(f"          Status: [{'PASS' if passed else 'FAIL'}] ({n} exercises in {dur:.3f}s)")

    total = time.time() - t_start

    print("\n" + "=" * 84)
    print(" LAB SUITE EXECUTION SUMMARY")
    print("=" * 84)
    print(f"{'#':<3} | {'Module':<44} | {'Ex':<3} | {'Status':<6} | {'Time':<8}")
    print("-" * 84)

    all_ok = True
    total_ex = 0
    for i, item in enumerate(summary, 1):
        total_ex += item["exercises"]
        if item["status"] != "PASS":
            all_ok = False
        print(f"{i:<3} | {item['module']:<44} | {item['exercises']:<3} | [{item['status']:<4}] | {item['duration']:.3f}s")

    print("-" * 84)
    print(f"TOTAL: {len(summary)} modules, {total_ex} exercises executed in {total:.2f}s")
    print("[SUCCESS] All course labs passed deterministic verification!" if all_ok
          else "[FAILED] At least one lab failed. Re-run with --verbose to inspect.")
    print("=" * 84)

    sys.exit(0 if all_ok else 1)


if __name__ == "__main__":
    main()
