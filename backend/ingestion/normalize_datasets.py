"""
Dataset Normalization & Evaluation Separation Script for FinCheck AI

This script:
1. Normalizes RBI Circular QA dataset into authoritative reference corpus (rbi_corpus.jsonl)
2. Normalizes Indian Financial Inclusion dataset into authoritative reference corpus (indian_finance_corpus.jsonl)
3. Combines both into combined_corpus.jsonl
4. Separates QA pairs into evaluation datasets (rbi_eval.jsonl and indian_finance_eval.jsonl)
"""

import hashlib
import json
import os
import re
from typing import Any, Dict, List, Optional, Tuple
import pandas as pd
import tiktoken

tokenizer = tiktoken.get_encoding("cl100k_base")


def extract_section_heading(text: str) -> Optional[str]:
    """Extract first authentic section heading from markdown text, if present."""
    matches = re.findall(r"^##+\s*(\*\*?[^\*\n]+\*\*?|[^\n]+)$", text, re.MULTILINE)
    for m in matches:
        s = m.replace("**", "").strip()
        lower_s = s.lower()
        if (
            s
            and not lower_s.startswith("reserve bank")
            and not lower_s.startswith("भारतीय")
            and not lower_s.startswith("notification")
            and not lower_s.startswith("mumbai")
        ):
            return s[:250]
    return None


def extract_indian_finance_reference(
    original_prompt: str, enhanced_prompt: str
) -> Tuple[str, str, str]:
    """
    Extracts financial area, subtopic, and pure authoritative reference context.
    Returns: (area, subtopic, reference_context)
    """
    orig_lines = [l.strip() for l in original_prompt.split("\n") if l.strip()]
    area = orig_lines[1] if len(orig_lines) > 1 else "General Finance"
    raw_subtopic = orig_lines[2] if len(orig_lines) > 2 else "Financial Inclusion"

    # If raw_subtopic is actually a long descriptive paragraph (> 100 chars), use it in body
    if len(raw_subtopic) > 100:
        section = raw_subtopic[:60].strip() + "..."
        body_parts = [raw_subtopic]
    else:
        section = raw_subtopic
        body_parts = []

    ref_found = ""
    # Check if enhanced_prompt contains explicit reference section
    if enhanced_prompt:
        for pat in [
            r"# Input Data\s*\n+(.*?)(?=\n# Output|\n# Guidelines|\n# Task|\Z)",
            r"# Reference Information\s*\n+(.*?)(?=\n# Definitions|\n# Output|\n# Guidelines|\n# Task|\Z)",
            r"Below is the source material[^\n]*\n+---\s*\n(.*?)\n---",
            r"## Reference Material[^\n]*\n+(.*?)(?=\n##|\n# Guidelines|\n# Instructions|\n# Task|\Z)"
        ]:
            m = re.search(pat, enhanced_prompt, re.DOTALL | re.IGNORECASE)
            if m:
                cand = m.group(1).strip()
                if len(tokenizer.encode(cand)) >= 50:
                    ref_found = cand
                    break

    # Fallback / primary source: original_prompt lines 3+
    if not ref_found and len(orig_lines) >= 4:
        body_lines = orig_lines[3:]
        last_line_lower = body_lines[-1].lower()
        if any(
            last_line_lower.startswith(prefix)
            for prefix in [
                "user learns", "the user learns", "investor learns", "the investor learns",
                "entrepreneur learns", "the entrepreneur learns", "farmer learns",
                "the farmer learns", "borrower learns", "consumer learns", "the consumer learns",
                "applicant learns", "the applicant learns", "citizen learns", "learns"
            ]
        ):
            body_lines = body_lines[:-1]
        body_parts.extend(body_lines)
        ref_found = "\n".join(body_parts).strip()
    elif not ref_found and body_parts:
        ref_found = "\n".join(body_parts).strip()

    return area, section, ref_found


def normalize_rbi(
    train_parquet_path: str, eval_parquet_path: str
) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]], Dict[str, int]]:
    """
    Normalizes RBI circular records.
    Returns: (rbi_corpus_records, rbi_eval_records, stats)
    """
    print(f"Reading RBI training data from {train_parquet_path}...")
    df_train = pd.read_parquet(train_parquet_path)
    total_train_rows = len(df_train)

    print(f"Reading RBI evaluation data from {eval_parquet_path}...")
    df_eval = pd.read_parquet(eval_parquet_path)
    total_eval_rows = len(df_eval)

    # Group by (document, filename, chunks_text)
    unique_rbi_chunks = df_train.drop_duplicates(subset=["document", "filename", "chunks_text"]).copy()
    unique_docs = df_train["document"].nunique()

    corpus_records = []

    for idx, row in unique_rbi_chunks.iterrows():
        doc_raw = str(row["document"]).strip()
        filename = str(row["filename"]).strip()
        content = str(row["chunks_text"]).strip()

        doc_hash = hashlib.md5(f"{doc_raw}_{filename}".encode("utf-8")).hexdigest()[:8]
        doc_slug = re.sub(r"[^a-zA-Z0-9_\-]+", "_", doc_raw)[:60].strip("_")
        doc_id = f"rbi_{doc_slug}_{doc_hash}"

        section = extract_section_heading(content)

        key_topics = row.get("key_topics")
        if isinstance(key_topics, (list, tuple)):
            topics_list = list(key_topics)
        elif hasattr(key_topics, "tolist"):
            topics_list = key_topics.tolist()
        else:
            topics_list = []

        is_table = bool(row.get("is_table", False))
        issued_on = str(row.get("issued_on", "")).strip() or None
        regulation_area = str(row.get("regulation_area", "")).strip() or None
        applicable_to = str(row.get("applicable_to", "")).strip() or None

        record = {
            "document_id": doc_id,
            "document_name": doc_raw,
            "document_type": "rbi_circular",
            "source": "Reserve Bank of India",
            "source_dataset": "rbi_circular_qa",
            "issued_date": issued_on,
            "regulation_area": regulation_area,
            "applicable_to": applicable_to,
            "section": section,
            "page_number": None,
            "content": content,
            "metadata": {
                "key_topics": topics_list,
                "is_table": is_table,
                "filename": filename
            }
        }
        corpus_records.append(record)

    eval_records = []
    for idx, row in df_eval.iterrows():
        q = str(row.get("question", "")).strip()
        ans = str(row.get("answer", "")).strip()
        doc = str(row.get("document", "")).strip()
        criteria = str(row.get("evaluation_criteria", "")).strip()
        cat = str(row.get("category", "")).strip()
        difficulty = int(row.get("estimated_difficulty", 1))

        if q and ans:
            eval_record = {
                "question": q,
                "expected_answer": ans,
                "document": doc,
                "source_dataset": "rbi",
                "metadata": {
                    "evaluation_criteria": criteria,
                    "category": cat,
                    "estimated_difficulty": difficulty,
                    "rephrased_question": str(row.get("rephrased_question", "")).strip(),
                    "rephrased_answer": str(row.get("rephrased_answer", "")).strip()
                }
            }
            eval_records.append(eval_record)

    stats = {
        "original_rbi_train_rows": total_train_rows,
        "original_rbi_eval_rows": total_eval_rows,
        "normalized_rbi_document_count": unique_docs,
        "normalized_rbi_source_record_count": len(corpus_records),
        "rbi_evaluation_questions_count": len(eval_records)
    }

    return corpus_records, eval_records, stats


def normalize_indian_finance(
    jsonl_path: str
) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]], Dict[str, int]]:
    """
    Normalizes Indian Financial Inclusion dataset.
    Returns: (finance_corpus_records, finance_eval_records, stats)
    """
    print(f"Reading Indian Finance data from {jsonl_path}...")
    corpus_records = []
    eval_records = []
    seen_content_hashes = set()
    total_rows = 0

    with open(jsonl_path, "r", encoding="utf-8") as f:
        for idx, line in enumerate(f):
            line = line.strip()
            if not line:
                continue
            total_rows += 1
            data = json.loads(line)

            original_prompt = data.get("original_prompt", "")
            original_completion = data.get("original_completion", "")
            enhanced_prompt = data.get("enhanced_prompt", "")
            enhanced_completion = data.get("enhanced_completion", "")

            area, subtopic, ref_context = extract_indian_finance_reference(
                original_prompt, enhanced_prompt
            )

            # Deduplicate identical reference content under the same subtopic
            content_hash = hashlib.md5(f"{area}_{subtopic}_{ref_context}".encode("utf-8")).hexdigest()

            if content_hash not in seen_content_hashes and ref_context:
                seen_content_hashes.add(content_hash)
                doc_id = f"indfin_{content_hash[:12]}"
                doc_name = f"{subtopic} ({area})"

                corpus_record = {
                    "document_id": doc_id,
                    "document_name": doc_name,
                    "document_type": "financial_guidance",
                    "source": "Indian Financial Inclusion / Reference",
                    "source_dataset": "indian_finance",
                    "issued_date": None,
                    "regulation_area": area,
                    "applicable_to": None,
                    "section": subtopic,
                    "page_number": None,
                    "content": ref_context,
                    "metadata": {
                        "financial_area": area,
                        "subtopic": subtopic
                    }
                }
                corpus_records.append(corpus_record)

            orig_lines = [l.strip() for l in original_prompt.split("\n") if l.strip()]
            question = orig_lines[0] if orig_lines else ""
            expected_answer = original_completion.strip() or enhanced_completion.strip()

            if question and expected_answer:
                eval_record = {
                    "question": question,
                    "expected_answer": expected_answer,
                    "source_dataset": "indian_finance",
                    "metadata": {
                        "financial_area": area,
                        "subtopic": subtopic
                    }
                }
                eval_records.append(eval_record)

    stats = {
        "original_indian_finance_rows": total_rows,
        "normalized_indian_finance_source_record_count": len(corpus_records),
        "indian_finance_evaluation_questions_count": len(eval_records)
    }

    return corpus_records, eval_records, stats


def save_jsonl(records: List[Dict[str, Any]], file_path: str):
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    with open(file_path, "w", encoding="utf-8") as f:
        for r in records:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    print(f"Saved {len(records)} records to {file_path}")


def main():
    base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    
    rbi_train_p = os.path.join(base_dir, "datasets", "rbi", "train-00000-of-00001.parquet")
    rbi_eval_p = os.path.join(base_dir, "datasets", "rbi", "eval-00000-of-00001.parquet")
    fin_p = os.path.join(base_dir, "datasets", "indian-finance", "train_0.jsonl")

    norm_dir = os.path.join(base_dir, "data", "normalized")
    eval_dir = os.path.join(base_dir, "data", "evaluation")
    os.makedirs(norm_dir, exist_ok=True)
    os.makedirs(eval_dir, exist_ok=True)

    rbi_corpus, rbi_eval, rbi_stats = normalize_rbi(rbi_train_p, rbi_eval_p)
    save_jsonl(rbi_corpus, os.path.join(norm_dir, "rbi_corpus.jsonl"))
    save_jsonl(rbi_eval, os.path.join(eval_dir, "rbi_eval.jsonl"))

    fin_corpus, fin_eval, fin_stats = normalize_indian_finance(fin_p)
    save_jsonl(fin_corpus, os.path.join(norm_dir, "indian_finance_corpus.jsonl"))
    save_jsonl(fin_eval, os.path.join(eval_dir, "indian_finance_eval.jsonl"))

    combined_corpus = rbi_corpus + fin_corpus
    save_jsonl(combined_corpus, os.path.join(norm_dir, "combined_corpus.jsonl"))

    print("\nNormalization Complete:")
    print(f"  RBI Source Records: {len(rbi_corpus)}")
    print(f"  Indian Finance Source Records: {len(fin_corpus)}")
    print(f"  Combined Corpus Records: {len(combined_corpus)}")
    print(f"  RBI Eval Pairs: {len(rbi_eval)}")
    print(f"  Indian Finance Eval Pairs: {len(fin_eval)}")


if __name__ == "__main__":
    main()
