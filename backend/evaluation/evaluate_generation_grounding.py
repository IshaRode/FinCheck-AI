"""
Evaluation script for Phase 6 Grounded Answer Generation with Gemini.
Runs across sample wealth management queries to evaluate:
- Factual grounding and citation compliance ([Source N])
- Regulatory hierarchy (RBI priority)
- Insufficient context handling on out-of-corpus queries
- End-to-end latency profiling (Retrieval vs. Generation)
"""

import sys
import time
from pathlib import Path
from typing import Dict, List, Any

# Ensure project root is in sys.path
ROOT_DIR = Path(__file__).resolve().parent.parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from backend.app.services.retrieval_service import retrieval_service
from backend.app.services.generation_service import generation_service
from backend.app.config import settings

BENCHMARK_QUESTIONS = [
    {
        "id": "G01",
        "category": "KYC & CDD",
        "query": "Under RBI guidelines, how often must high-risk customer KYC be updated?",
        "expected_topic": "Periodic KYC Update",
    },
    {
        "id": "G02",
        "category": "Cyber Fraud & Safety",
        "query": "What precautions should customers take to avoid digital arrest scams?",
        "expected_topic": "Digital arrest scam precautions",
    },
    {
        "id": "G03",
        "category": "Deceased Depositor Claims",
        "query": "What is the RBI procedure and timeline for settlement of claims in deceased depositors' accounts?",
        "expected_topic": "15-day settlement / nominee role",
    },
    {
        "id": "G04",
        "category": "Payments & Settlements",
        "query": "What is the difference between NEFT and RTGS for a regular user transferring funds?",
        "expected_topic": "Gross settlement vs DNS batches",
    },
    {
        "id": "G05",
        "category": "Out-of-Corpus / Negative Test",
        "query": "What is the bank policy on cryptocurrency mining hardware leasing in Antarctica?",
        "expected_topic": "Insufficient context detection",
    },
]


def run_grounding_evaluation():
    print("=" * 70)
    print("FINCHECK AI: PHASE 6 GROUNDED GENERATION EVALUATION")
    print(f"Gemini Model: {settings.GEMINI_MODEL}")
    print(f"API Key Configured: {bool(settings.GEMINI_API_KEY)}")
    print("=" * 70)

    results: List[Dict[str, Any]] = []

    for item in BENCHMARK_QUESTIONS:
        qid = item["id"]
        cat = item["category"]
        query = item["query"]

        print(f"\n[{qid}] Category: {cat}")
        print(f"Query: \"{query}\"")

        # Step 1: Two-Stage Retrieval (Top 15 -> Rerank Top 5)
        t_ret_start = time.perf_counter()
        chunks, reranked, total_cands = retrieval_service.retrieve(
            question=query,
            match_count=15,
            final_count=5,
            enable_rerank=True,
            return_metadata=True,
        )
        ret_latency_ms = round((time.perf_counter() - t_ret_start) * 1000, 1)

        # Step 2: Grounded Generation via Gemini
        t_gen_start = time.perf_counter()
        try:
            gen_resp = generation_service.generate_answer(
                question=query,
                chunks=chunks,
                total_candidates=total_cands,
                reranked=reranked,
            )
            gen_latency_ms = round((time.perf_counter() - t_gen_start) * 1000, 1)
        except Exception as e:
            gen_resp = generation_service.create_fallback_response(
                question=query,
                chunks=chunks,
                reason=str(e),
                total_candidates=total_cands,
                reranked=reranked,
            )
            gen_latency_ms = round((time.perf_counter() - t_gen_start) * 1000, 1)

        total_latency_ms = ret_latency_ms + gen_latency_ms

        print(f"   Retrieval: {len(chunks)} chunks in {ret_latency_ms} ms")
        print(f"   Generation: {gen_latency_ms} ms (Total: {total_latency_ms} ms)")
        print(f"   Grounded: {gen_resp.is_grounded} | Insufficient: {gen_resp.is_insufficient_context}")
        print(f"   Citations: {gen_resp.cited_source_ids}")
        print(f"   Answer Snippet: {gen_resp.answer[:140]}...")

        results.append(
            {
                "id": qid,
                "category": cat,
                "query": query,
                "retrieval_latency_ms": ret_latency_ms,
                "generation_latency_ms": gen_latency_ms,
                "total_latency_ms": total_latency_ms,
                "is_grounded": gen_resp.is_grounded,
                "is_insufficient_context": gen_resp.is_insufficient_context,
                "citations_count": len(gen_resp.cited_source_ids),
                "cited_sources": gen_resp.cited_source_ids,
                "answer_preview": gen_resp.answer[:250].replace("\n", " "),
            }
        )

    # Generate Markdown Report
    report_dir = ROOT_DIR / "data" / "evaluation"
    report_dir.mkdir(parents=True, exist_ok=True)
    report_path = report_dir / "generation_grounding_report.md"

    with open(report_path, "w", encoding="utf-8") as f:
        f.write("# FinCheck AI — Phase 6 Grounded Answer Generation Report\n\n")
        f.write(f"- **Evaluated Queries:** {len(results)}\n")
        f.write(f"- **Gemini Model:** `{settings.GEMINI_MODEL}`\n")
        f.write(f"- **GEMINI_API_KEY Present:** `{bool(settings.GEMINI_API_KEY)}`\n\n")
        f.write("## Results Summary\n\n")
        f.write("| ID | Category | Query | Grounded | Insufficient Context | Citations | Latency (Ret / Gen / Total) |\n")
        f.write("|:---|:---|:---|:---:|:---:|:---:|:---|\n")

        for r in results:
            g_icon = "✓" if r["is_grounded"] else "✗"
            i_icon = "⚠️ Yes" if r["is_insufficient_context"] else "No"
            c_str = f"{r['citations_count']} ({r['cited_sources']})" if r["citations_count"] else "0"
            lat_str = f"{r['retrieval_latency_ms']}ms / {r['generation_latency_ms']}ms / {r['total_latency_ms']}ms"
            f.write(
                f"| {r['id']} | {r['category']} | {r['query']} | {g_icon} | {i_icon} | {c_str} | {lat_str} |\n"
            )

        f.write("\n## Detailed Answer Previews\n\n")
        for r in results:
            f.write(f"### [{r['id']}] {r['category']}\n")
            f.write(f"**Query:** *{r['query']}*\n\n")
            f.write(f"**Answer Preview:**\n> {r['answer_preview']}...\n\n")
            f.write("---\n\n")

    print("\n" + "=" * 70)
    print(f"Saved Phase 6 Evaluation Report to: {report_path}")
    print("=" * 70)


if __name__ == "__main__":
    run_grounding_evaluation()
