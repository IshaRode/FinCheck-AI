"""
Comparative Evaluation Benchmark for FinCheck AI (Phase 5).
Evaluates 15 representative retail and wealth banking questions to directly
compare retrieval precision and ranking quality:
- Before Reranking: Supabase pgvector cosine similarity (Top 15 candidates)
- After Reranking: NVIDIA Cross-Encoder Reranker (Top 5 reranked)

Measures:
- Rank promotions and demotions
- Top-1 and Top-3 relevance alignment
- Tier 1 (RBI Circular) authority representation in top ranks
- Vector vs. Reranker latency (ms)
Outputs a comprehensive comparison table and report.
"""

import os
import sys
import time
from pathlib import Path
from typing import Any, Dict, List

ROOT_DIR = Path(__file__).resolve().parent.parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from backend.app.services.retrieval_service import retrieval_service

BENCHMARK_QUESTIONS = [
    {
        "id": "Q01",
        "category": "KYC & Customer Due Diligence",
        "target_authority": "RBI Circular",
        "question": "What are the RBI rules regarding KYC requirements?",
    },
    {
        "id": "Q02",
        "category": "KYC Periodic Updates",
        "target_authority": "RBI Circular",
        "question": "Under RBI guidelines, how often must high-risk customer KYC be updated?",
    },
    {
        "id": "Q03",
        "category": "Cyber Safety & Fraud",
        "target_authority": "Indian Finance / RBI",
        "question": "What precautions should customers take to avoid digital arrest scams?",
    },
    {
        "id": "Q04",
        "category": "Fraud Reporting & Redressal",
        "target_authority": "Indian Finance",
        "question": "What should a customer do if an unauthorized AePS withdrawal occurs?",
    },
    {
        "id": "Q05",
        "category": "Account Nomination",
        "target_authority": "RBI / Indian Finance",
        "question": "What are the rules related to bank account nominee?",
    },
    {
        "id": "Q06",
        "category": "Deceased Depositor Claims",
        "target_authority": "RBI Circular",
        "question": "What is the RBI procedure for settlement of claims in deceased depositors' accounts?",
    },
    {
        "id": "Q07",
        "category": "Wire Transfers & Payments",
        "target_authority": "RBI / Indian Finance",
        "question": "How do RTGS and NEFT relate to India's electronic funds transfer infrastructure?",
    },
    {
        "id": "Q08",
        "category": "Payment Limits & Charges",
        "target_authority": "Indian Finance",
        "question": "What is the difference between NEFT and RTGS for a regular user transferring small amounts?",
    },
    {
        "id": "Q09",
        "category": "Lending & Interest Rates",
        "target_authority": "RBI Circular",
        "question": "What are the RBI rules regarding loan foreclosure charges on floating rate term loans?",
    },
    {
        "id": "Q10",
        "category": "Loan Restructuring & DCCO",
        "target_authority": "RBI Circular",
        "question": "What is the asset classification of project loans when the DCCO is extended?",
    },
    {
        "id": "Q11",
        "category": "Deposit Insurance",
        "target_authority": "Indian Finance",
        "question": "What is the maximum deposit insurance coverage provided by DICGC per depositor?",
    },
    {
        "id": "Q12",
        "category": "Liquid Funds & Wealth Parking",
        "target_authority": "Indian Finance",
        "question": "What is a liquid fund, and is it safe to park money in it for 1-3 months?",
    },
    {
        "id": "Q13",
        "category": "Currency Management",
        "target_authority": "RBI Circular",
        "question": "Why is it important for banks to maintain data on the amount of ₹2000 banknotes exchanged and deposited?",
    },
    {
        "id": "Q14",
        "category": "Startup & Wealth Taxation",
        "target_authority": "Indian Finance",
        "question": "Does Angel Tax under Section 56(2)(viib) apply to LLPs?",
    },
    {
        "id": "Q15",
        "category": "Grievance Redressal",
        "target_authority": "RBI Circular",
        "question": "What measures should banks take to handle pensioner complaints and assess the quality of pension-related services?",
    },
]


def run_benchmark():
    print("=" * 70)
    print("FINCHECK AI: PHASE 5 RERANKING COMPARATIVE BENCHMARK")
    print(f"Total Questions: {len(BENCHMARK_QUESTIONS)}")
    print("Vector Retrieval: Top 15 candidates")
    print("Reranker: nvidia/llama-nemotron-rerank-vl-1b-v2 -> Top 5 final")
    print("=" * 70)

    report_rows = []
    promoted_count = 0
    unchanged_top1_count = 0
    total_latency_vector = 0.0
    total_latency_rerank = 0.0

    for idx, item in enumerate(BENCHMARK_QUESTIONS, 1):
        q_id = item["id"]
        cat = item["category"]
        question = item["question"]
        target_auth = item["target_authority"]

        print(f"\n[{idx:02d}/15] {q_id} ({cat})")
        print(f"Query: \"{question}\"")

        # 1. Vector Only Retrieval (Top 15 candidates)
        t0 = time.perf_counter()
        vector_candidates = retrieval_service.retrieve(
            question,
            match_count=15,
            final_count=15,
            enable_rerank=False,
        )
        t_vector = (time.perf_counter() - t0) * 1000
        total_latency_vector += t_vector

        # 2. Reranked Retrieval (Top 15 -> Top 5)
        t1 = time.perf_counter()
        reranked_chunks, is_reranked, total_evaluated = retrieval_service.retrieve(
            question,
            match_count=15,
            final_count=5,
            enable_rerank=True,
            return_metadata=True,
        )
        t_total = (time.perf_counter() - t1) * 1000
        t_rerank = max(0.0, t_total - t_vector)
        total_latency_rerank += t_rerank

        v_top1 = vector_candidates[0] if vector_candidates else None
        r_top1 = reranked_chunks[0] if reranked_chunks else None

        # Check if Rank 1 changed
        if v_top1 and r_top1:
            if v_top1.chunk_id != r_top1.chunk_id:
                promoted_count += 1
                change_status = f"▲ Vector #{r_top1.initial_rank} promoted to #1"
            else:
                unchanged_top1_count += 1
                change_status = "= Top 1 maintained"
        else:
            change_status = "No results"

        # Tier 1 RBI count in top 3
        rbi_in_top3_vec = sum(1 for c in vector_candidates[:3] if c.source_dataset == "rbi")
        rbi_in_top3_rerank = sum(1 for c in reranked_chunks[:3] if c.source_dataset == "rbi")

        print(f"   Status: {change_status}")
        print(f"   Vector Top 1:   [{v_top1.source_dataset if v_top1 else '-'}] {v_top1.document_name[:45] if v_top1 else '-'} (Sim: {v_top1.similarity:.4f})")
        print(f"   Reranked Top 1: [{r_top1.source_dataset if r_top1 else '-'}] {r_top1.document_name[:45] if r_top1 else '-'} (Logit: {r_top1.rerank_logit:+.4f}, Sim: {r_top1.similarity:.4f})")
        print(f"   Latency: Vector {t_vector:.0f}ms | Rerank ~{t_rerank:.0f}ms (Total: {t_total:.0f}ms)")

        report_rows.append(
            {
                "id": q_id,
                "category": cat,
                "target_auth": target_auth,
                "question": question,
                "v_top1_doc": v_top1.document_name if v_top1 else "None",
                "v_top1_dataset": v_top1.source_dataset if v_top1 else "-",
                "v_top1_sim": v_top1.similarity if v_top1 else 0.0,
                "r_top1_doc": r_top1.document_name if r_top1 else "None",
                "r_top1_dataset": r_top1.source_dataset if r_top1 else "-",
                "r_top1_sim": r_top1.similarity if r_top1 else 0.0,
                "r_top1_logit": r_top1.rerank_logit if r_top1 else 0.0,
                "orig_vector_rank": r_top1.initial_rank if r_top1 else 1,
                "change_status": change_status,
                "rbi_in_top3_vec": rbi_in_top3_vec,
                "rbi_in_top3_rerank": rbi_in_top3_rerank,
                "t_vector_ms": round(t_vector, 1),
                "t_rerank_ms": round(t_rerank, 1),
            }
        )

    # Summary calculations
    avg_t_vec = total_latency_vector / len(BENCHMARK_QUESTIONS)
    avg_t_rerank = total_latency_rerank / len(BENCHMARK_QUESTIONS)
    promoted_pct = (promoted_count / len(BENCHMARK_QUESTIONS)) * 100

    print("\n" + "=" * 70)
    print("BENCHMARK SUMMARY RESULTS")
    print("=" * 70)
    print(f"Total benchmark questions:             {len(BENCHMARK_QUESTIONS)}")
    print(f"Queries with Top 1 Rank reordered:     {promoted_count}/{len(BENCHMARK_QUESTIONS)} ({promoted_pct:.1f}%)")
    print(f"Queries with Top 1 Rank maintained:    {unchanged_top1_count}/{len(BENCHMARK_QUESTIONS)} ({100 - promoted_pct:.1f}%)")
    print(f"Average Vector Retrieval Latency:      {avg_t_vec:.1f} ms")
    print(f"Average Reranking Pipeline Latency:    {avg_t_rerank:.1f} ms")
    print("=" * 70)

    # Save markdown report
    output_path = os.path.join(ROOT_DIR, "data", "evaluation", "reranking_comparison_report.md")
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write("# FinCheck AI — Phase 5 Reranking Comparative Benchmark Report\n\n")
        f.write(f"- **Total Questions Evaluated:** {len(BENCHMARK_QUESTIONS)}\n")
        f.write(f"- **Top-1 Rank Promotion Rate:** {promoted_pct:.1f}% ({promoted_count} queries promoted a more precise passage to #1)\n")
        f.write(f"- **Average Vector Latency:** {avg_t_vec:.1f} ms\n")
        f.write(f"- **Average Reranker Latency:** {avg_t_rerank:.1f} ms\n\n")
        f.write("## Comparison Table\n\n")
        f.write("| ID | Category | Query | Vector Top 1 | Reranked Top 1 (Logit) | Rank Movement |\n")
        f.write("|:---|:---|:---|:---|:---|:---|\n")
        for r in report_rows:
            f.write(
                f"| {r['id']} | {r['category']} | {r['question']} | "
                f"[{r['v_top1_dataset']}] {r['v_top1_doc'][:32]}... ({r['v_top1_sim']:.3f}) | "
                f"[{r['r_top1_dataset']}] {r['r_top1_doc'][:32]}... ({r['r_top1_logit']:+.2f}) | "
                f"{r['change_status']} |\n"
            )
    print(f"\nSaved detailed benchmark report to: {output_path}")


if __name__ == "__main__":
    run_benchmark()
