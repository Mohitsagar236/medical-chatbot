"""
Performance evaluation script for the CS 540 medical chatbot.

Reads the shared dataset Excel, calls all 4 strategy endpoints for every
(session, turn), computes all metrics locally, and writes results to an
output Excel file — one sheet per member.

Usage:
    python eval/run_evaluation.py \\
        --input "reference-folder/Evaluation Dataset - CS 540 Project.xlsx" \\
        --base-url http://localhost:8000 \\
        --output eval/results/evaluation_results.xlsx \\
        [--member 2]          # optional: run only one member's sessions

Output columns per row (one row = one session × turn × strategy):
    session_id, pubid, topic, member, turn, strategy,
    question, answer, reference_answer, ground_truth_label,
    label_accuracy, bert_score_f1,
    hallucination_label, is_hallucination,
    context_recall, coherence,
    latency_ms, prompt_tokens, completion_tokens, cost_usd
"""
from __future__ import annotations

import argparse
import os
import time
import uuid
from pathlib import Path

import httpx
import openpyxl
import pandas as pd

# Metrics are imported here — models load on first call (lazy inside each fn)
import sys
sys.path.insert(0, str(Path(__file__).parent))
from metrics import (
    compute_label_accuracy,
    compute_bert_score,
    compute_hallucination,
    compute_context_recall,
    compute_coherence,
    compute_cost,
)

OUTPUT_COLUMNS = [
    "session_id", "pubid", "topic", "member", "turn", "strategy",
    "question", "answer", "reference_answer", "ground_truth_label",
    "label_accuracy", "bert_score_f1",
    "hallucination_label", "is_hallucination",
    "context_recall", "coherence",
    "latency_ms", "prompt_tokens", "completion_tokens", "cost_usd",
]

STRATEGIES = ["S1", "S2", "S3", "S4"]

# ---------------------------------------------------------------------------
# API helpers
# ---------------------------------------------------------------------------

def _call_s1(client: httpx.Client, base: str, query: str) -> dict:
    t0 = time.perf_counter()
    r = client.post(f"{base}/api/v1/chat/single-llm/", json={"query": query}, timeout=60)
    latency = (time.perf_counter() - t0) * 1000
    r.raise_for_status()
    data = r.json()
    return {
        "answer": data["answer"],
        "prompt_tokens": data.get("prompt_tokens"),
        "completion_tokens": data.get("completion_tokens"),
        "retrieved_chunks": [],
        "latency_ms": round(latency, 1),
    }


def _call_s2(client: httpx.Client, base: str, query: str) -> dict:
    t0 = time.perf_counter()
    r = client.post(f"{base}/api/v1/chat/single-rag/", json={"query": query, "top_k": 5}, timeout=60)
    latency = (time.perf_counter() - t0) * 1000
    r.raise_for_status()
    data = r.json()
    chunks = [c["content"] for c in data.get("retrieved_chunks", [])]
    return {
        "answer": data["answer"],
        "prompt_tokens": data.get("prompt_tokens"),
        "completion_tokens": data.get("completion_tokens"),
        "retrieved_chunks": chunks,
        "latency_ms": round(latency, 1),
    }


def _call_s3(client: httpx.Client, base: str, query: str, session_id: str) -> dict:
    t0 = time.perf_counter()
    r = client.post(
        f"{base}/api/v1/chat/multi-turn-llm/",
        json={"query": query, "session_id": session_id},
        timeout=60,
    )
    latency = (time.perf_counter() - t0) * 1000
    r.raise_for_status()
    data = r.json()
    return {
        "answer": data["answer"],
        "prompt_tokens": data.get("prompt_tokens"),
        "completion_tokens": data.get("completion_tokens"),
        "retrieved_chunks": [],
        "latency_ms": round(latency, 1),
    }


def _call_s4(client: httpx.Client, base: str, query: str, session_id: str) -> dict:
    t0 = time.perf_counter()
    r = client.post(
        f"{base}/api/v1/chat/multi-turn-rag/",
        json={"query": query, "session_id": session_id, "top_k": 5},
        timeout=60,
    )
    latency = (time.perf_counter() - t0) * 1000
    r.raise_for_status()
    data = r.json()
    chunks = [c["content"] for c in data.get("retrieved_chunks", [])]
    return {
        "answer": data["answer"],
        "prompt_tokens": data.get("prompt_tokens"),
        "completion_tokens": data.get("completion_tokens"),
        "retrieved_chunks": chunks,
        "latency_ms": round(latency, 1),
    }


def _delete_session(client: httpx.Client, base: str, strategy: str, session_id: str) -> None:
    path = "multi-turn-llm" if strategy == "S3" else "multi-turn-rag"
    try:
        client.delete(f"{base}/api/v1/chat/{path}/{session_id}", timeout=10)
    except Exception:
        pass  # best-effort cleanup


# ---------------------------------------------------------------------------
# Dataset loading
# ---------------------------------------------------------------------------

def load_dataset(path: str, member_filter: int | None) -> dict[int, pd.DataFrame]:
    """Returns {member_number: DataFrame} for the requested member(s)."""
    xl = pd.ExcelFile(path)
    sheets = {}
    for sheet in xl.sheet_names:
        if not sheet.startswith("member"):
            continue
        num = int(sheet.replace("member", ""))
        if member_filter is not None and num != member_filter:
            continue
        df = xl.parse(sheet)
        df["turn"] = df["turn"].astype(int)
        df["session_id"] = df["session_id"].astype(int)
        sheets[num] = df
    return sheets


# ---------------------------------------------------------------------------
# Evaluation loop
# ---------------------------------------------------------------------------

def evaluate_session(
    client: httpx.Client,
    base: str,
    turns: pd.DataFrame,
) -> list[dict]:
    """Run all 4 strategies across 3 turns for one session. Returns list of result rows."""
    rows = []
    session_id_s3 = str(uuid.uuid4())
    session_id_s4 = str(uuid.uuid4())
    prev_answer: dict[str, str] = {}  # strategy -> previous turn answer

    for _, turn_row in turns.sort_values("turn").iterrows():
        turn_num  = int(turn_row["turn"])
        question  = str(turn_row["question"])
        ref_ans   = str(turn_row["reference_answer"])
        gt_label  = str(turn_row["ground_truth_label"]).strip() if turn_row["ground_truth_label"] else ""
        contexts  = str(turn_row["contexts"])

        for strategy in STRATEGIES:
            print(f"      [{strategy}] turn {turn_num} … ", end="", flush=True)
            try:
                if strategy == "S1":
                    api = _call_s1(client, base, question)
                    time.sleep(0.5)  # avoid Groq rate limits between per-strategy calls
                elif strategy == "S2":
                    api = _call_s2(client, base, question)
                    time.sleep(0.5)  # avoid Groq rate limits between per-strategy calls
                elif strategy == "S3":
                    api = _call_s3(client, base, question, session_id_s3)
                    time.sleep(0.5)  # avoid Groq rate limits between per-strategy calls
                else:
                    api = _call_s4(client, base, question, session_id_s4)
                    time.sleep(0.5)  # avoid Groq rate limits between per-strategy calls
            except Exception as exc:
                print(f"ERROR: {exc}")
                api = {"answer": "", "prompt_tokens": None, "completion_tokens": None,
                       "retrieved_chunks": [], "latency_ms": None}

            answer = api["answer"]
            print(f"{api['latency_ms']:.0f}ms" if api["latency_ms"] else "failed")

            # --- metrics ---
            label_acc = compute_label_accuracy(answer, gt_label) if turn_num == 1 else None

            bert_f1 = compute_bert_score(answer, ref_ans) if answer else None

            if answer and contexts:
                hall_label, is_hall = compute_hallucination(answer, contexts)
            else:
                hall_label, is_hall = None, None

            ctx_recall = None
            if strategy in ("S2", "S4") and api["retrieved_chunks"] and contexts:
                ctx_recall = compute_context_recall(api["retrieved_chunks"], contexts)

            coherence = None
            if turn_num > 1 and strategy in ("S3", "S4") and answer and prev_answer.get(strategy):
                coherence = compute_coherence(answer, prev_answer[strategy])

            cost = compute_cost(api["prompt_tokens"], api["completion_tokens"])

            rows.append({
                "session_id":         int(turn_row["session_id"]),
                "pubid":              turn_row["pubid"],
                "topic":              turn_row["topic"],
                "member":             int(turn_row["member"]),
                "turn":               turn_num,
                "strategy":           strategy,
                "question":           question,
                "answer":             answer,
                "reference_answer":   ref_ans,
                "ground_truth_label": gt_label or None,
                "label_accuracy":     label_acc,
                "bert_score_f1":      bert_f1,
                "hallucination_label": hall_label,
                "is_hallucination":   is_hall,
                "context_recall":     ctx_recall,
                "coherence":          coherence,
                "latency_ms":         api["latency_ms"],
                "prompt_tokens":      api["prompt_tokens"],
                "completion_tokens":  api["completion_tokens"],
                "cost_usd":           cost,
            })

            prev_answer[strategy] = answer

    # Clean up stateful sessions
    _delete_session(client, base, "S3", session_id_s3)
    _delete_session(client, base, "S4", session_id_s4)
    return rows


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(description="Run medical chatbot performance evaluation")
    parser.add_argument("--input",    required=True, help="Path to dataset Excel file")
    parser.add_argument("--base-url", default="http://localhost:8000", help="FastAPI base URL")
    parser.add_argument("--output",   required=True, help="Path for output Excel file")
    parser.add_argument("--member",   type=int, default=None, help="Run only this member number (1-5)")
    args = parser.parse_args()

    print(f"Loading dataset from: {args.input}")
    sheets = load_dataset(args.input, args.member)
    if not sheets:
        print("No matching member sheets found. Check --member value.")
        return

    print("Loading evaluation models (first run downloads ~500MB) …")
    # Trigger lazy loads now so we don't pay during timed API calls
    from metrics import _get_bert_scorer, _get_embedder, _get_nli
    _get_bert_scorer(); _get_embedder(); _get_nli()
    print("Models ready.\n")

    all_results: dict[int, list[dict]] = {}

    with httpx.Client() as client:
        # Verify server is up
        try:
            client.get(f"{args.base_url}/health", timeout=5).raise_for_status()
        except Exception as exc:
            print(f"ERROR: Cannot reach backend at {args.base_url} — {exc}")
            return

        for member_num, df in sorted(sheets.items()):
            print(f"\n=== Member {member_num} ===")
            member_rows: list[dict] = []
            session_groups = df.groupby("session_id")
            total = len(session_groups)
            for i, (sid, grp) in enumerate(session_groups, 1):
                print(f"  Session {sid} ({i}/{total})")
                member_rows.extend(evaluate_session(client, args.base_url, grp))
                # small delay to respect Groq rate limits
                time.sleep(1)
            all_results[member_num] = member_rows

    # Write output Excel
    out_path = Path(args.output)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    wb = openpyxl.Workbook()
    wb.remove(wb.active)  # remove default sheet

    for member_num, rows in sorted(all_results.items()):
        ws = wb.create_sheet(title=f"member{member_num}")
        ws.append(OUTPUT_COLUMNS)
        for row in rows:
            ws.append([row.get(col) for col in OUTPUT_COLUMNS])

    wb.save(out_path)
    total_rows = sum(len(r) for r in all_results.values())
    print(f"\nDone. {total_rows} rows written to {out_path}")


if __name__ == "__main__":
    main()
