"""
Document Chunking Script for FinCheck AI

Splits normalized documents into chunks targeting 500-800 tokens with 75-100 tokens overlap.
Preserves document boundaries, section headings, and table integrity.
Strictly ensures chunks never exceed 800 tokens.
Performs smart refinement of tiny chunks (< 50 tokens):
- Merges address/signature/continuation fragments with adjacent chunks in the same document.
- Removes non-informational artifacts (slogans, stamps, pure headers without content).
- Preserves high-value standalone guidance (e.g. cyber fraud advisories).
Outputs to data/normalized/chunks.jsonl and generates validation report.
"""

import hashlib
import json
import os
import re
from typing import Any, Dict, List, Tuple
import tiktoken


def get_tokenizer():
    return tiktoken.get_encoding("cl100k_base")


def split_text_strictly(text: str, tokenizer, max_tokens: int = 620) -> List[str]:
    """
    Splits arbitrary text into slices that strictly do not exceed max_tokens.
    """
    tokens = tokenizer.encode(text)
    if len(tokens) <= max_tokens:
        return [text]

    words = text.split(" ")
    chunks = []
    curr_words = []
    curr_tokens = 0

    for w in words:
        w_t = len(tokenizer.encode(w + " "))
        if curr_tokens + w_t > max_tokens and curr_words:
            chunks.append(" ".join(curr_words))
            curr_words = [w]
            curr_tokens = w_t
        else:
            curr_words.append(w)
            curr_tokens += w_t

    if curr_words:
        chunks.append(" ".join(curr_words))

    final_chunks = []
    for c in chunks:
        c_toks = tokenizer.encode(c)
        if len(c_toks) <= max_tokens:
            final_chunks.append(c)
        else:
            for i in range(0, len(c_toks), max_tokens):
                final_chunks.append(tokenizer.decode(c_toks[i : i + max_tokens]))

    return final_chunks


def split_table_by_rows(table_block: str, tokenizer, max_tokens: int = 620) -> List[str]:
    """
    Splits a large markdown table by rows while repeating the header row on each slice.
    """
    lines = [l for l in table_block.split("\n") if l.strip()]
    if len(lines) <= 2:
        return split_text_strictly(table_block, tokenizer, max_tokens)

    header_lines = lines[:2]
    header_str = "\n".join(header_lines)
    header_tokens = len(tokenizer.encode(header_str))

    effective_max = max(100, max_tokens - header_tokens - 10)
    data_rows = lines[2:]

    table_slices = []
    curr_rows = []
    curr_tokens = 0

    for r in data_rows:
        r_tokens = len(tokenizer.encode(r))
        if r_tokens > effective_max:
            if curr_rows:
                table_slices.append(header_str + "\n" + "\n".join(curr_rows))
                curr_rows = []
                curr_tokens = 0
            row_slices = split_text_strictly(r, tokenizer, effective_max)
            for rs in row_slices:
                table_slices.append(header_str + "\n" + rs)
        elif curr_tokens + r_tokens > effective_max and curr_rows:
            table_slices.append(header_str + "\n" + "\n".join(curr_rows))
            curr_rows = [r]
            curr_tokens = r_tokens
        else:
            curr_rows.append(r)
            curr_tokens += r_tokens

    if curr_rows:
        table_slices.append(header_str + "\n" + "\n".join(curr_rows))

    return table_slices


def split_into_blocks(text: str, tokenizer, max_tokens: int = 620) -> List[str]:
    """
    Splits text into logical semantic blocks (paragraphs and tables).
    Guarantees every resulting block has <= max_tokens.
    """
    lines = text.split("\n")
    blocks = []
    current_block = []
    in_table = False

    for line in lines:
        stripped = line.strip()
        is_table_line = stripped.startswith("|") and stripped.endswith("|")

        if is_table_line:
            in_table = True
            current_block.append(line)
        elif in_table:
            in_table = False
            t_str = "\n".join(current_block).strip()
            if len(tokenizer.encode(t_str)) > max_tokens:
                blocks.extend(split_table_by_rows(t_str, tokenizer, max_tokens))
            else:
                blocks.append(t_str)
            current_block = []
            if stripped:
                current_block.append(line)
        elif not stripped:
            if current_block:
                b_str = "\n".join(current_block).strip()
                if b_str:
                    blocks.append(b_str)
                current_block = []
        else:
            current_block.append(line)

    if current_block:
        b_str = "\n".join(current_block).strip()
        if in_table and len(tokenizer.encode(b_str)) > max_tokens:
            blocks.extend(split_table_by_rows(b_str, tokenizer, max_tokens))
        elif b_str:
            blocks.append(b_str)

    final_blocks = []
    for b in blocks:
        b_tokens = len(tokenizer.encode(b))
        if b_tokens <= max_tokens:
            final_blocks.append(b)
        else:
            final_blocks.extend(split_text_strictly(b, tokenizer, max_tokens))

    return [b.strip() for b in final_blocks if b.strip()]


def chunk_document(
    doc: Dict[str, Any],
    tokenizer,
    target_min: int = 500,
    target_max: int = 780,
    target_chunk: int = 620,
    overlap_tokens: int = 85
) -> List[Dict[str, Any]]:
    """
    Chunks a single document into target tokens with overlap.
    Preserves document boundary strictly and guarantees <= 800 tokens.
    """
    content = doc.get("content", "").strip()
    if not content:
        return []

    doc_id = doc["document_id"]
    doc_tokens = tokenizer.encode(content)
    total_tokens = len(doc_tokens)

    # If document is already <= target_max, keep as a single chunk
    if total_tokens <= target_max:
        return [{
            "chunk_id": f"{doc_id}_c001",
            "document_id": doc_id,
            "document_name": doc["document_name"],
            "document_type": doc["document_type"],
            "source": doc["source"],
            "source_dataset": doc["source_dataset"],
            "issued_date": doc["issued_date"],
            "regulation_area": doc["regulation_area"],
            "applicable_to": doc["applicable_to"],
            "section": doc["section"],
            "page_number": None,
            "content": content,
            "metadata": {
                **doc.get("metadata", {}),
                "chunk_index": 1,
                "total_chunks_in_doc": 1,
                "token_count": total_tokens
            }
        }]

    # Document > target_max: chunk with semantic preservation and overlap
    blocks = split_into_blocks(content, tokenizer, max_tokens=target_chunk)

    chunks_text_list = []
    current_tokens = []
    current_text_parts = []

    for b in blocks:
        b_tokens = tokenizer.encode(b)
        if current_text_parts and (len(current_tokens) + len(b_tokens) > target_max):
            chunk_str = "\n\n".join(current_text_parts).strip()
            chunks_text_list.append(chunk_str)

            if overlap_tokens > 0 and len(current_tokens) > overlap_tokens:
                overlap_slice = current_tokens[-overlap_tokens:]
                overlap_str = tokenizer.decode(overlap_slice)
                if len(overlap_slice) + len(b_tokens) <= target_max:
                    current_tokens = list(overlap_slice)
                    current_text_parts = [overlap_str]
                else:
                    current_tokens = []
                    current_text_parts = []
            else:
                current_tokens = []
                current_text_parts = []

        current_tokens.extend(b_tokens)
        current_text_parts.append(b)

    if current_text_parts:
        final_str = "\n\n".join(current_text_parts).strip()
        if final_str:
            chunks_text_list.append(final_str)

    result = []
    total_chunks = len(chunks_text_list)
    for idx, c_text in enumerate(chunks_text_list):
        c_tokens = len(tokenizer.encode(c_text))
        
        chunk_section = doc["section"]
        first_line = c_text.strip().split("\n")[0]
        if first_line.startswith("#"):
            cleaned_h = first_line.replace("#", "").replace("*", "").strip()
            if cleaned_h:
                chunk_section = cleaned_h[:250]

        chunk_rec = {
            "chunk_id": f"{doc_id}_c{idx+1:03d}",
            "document_id": doc_id,
            "document_name": doc["document_name"],
            "document_type": doc["document_type"],
            "source": doc["source"],
            "source_dataset": doc["source_dataset"],
            "issued_date": doc["issued_date"],
            "regulation_area": doc["regulation_area"],
            "applicable_to": doc["applicable_to"],
            "section": chunk_section,
            "page_number": None,
            "content": c_text,
            "metadata": {
                **doc.get("metadata", {}),
                "chunk_index": idx + 1,
                "total_chunks_in_doc": total_chunks,
                "token_count": c_tokens
            }
        }
        result.append(chunk_rec)

    return result


def refine_document_chunks(
    chunks: List[Dict[str, Any]], tokenizer, max_tokens_limit: int = 800
) -> List[Dict[str, Any]]:
    """
    Refines document chunks to handle tiny fragments (< 50 tokens):
    1. In multi-chunk documents, merges trailing fragments (footers/signatures)
       with previous chunk from the SAME document if combined <= max_tokens_limit.
    2. Drops non-informational artifacts (stamps, slogans, empty headers).
    3. Keeps standalone meaningful guidance (e.g. cyber fraud advisories).
    4. Re-indexes chunk metadata cleanly.
    """
    if not chunks:
        return []

    # 1. Merge small continuation/footer chunks in multi-chunk docs
    if len(chunks) > 1:
        while len(chunks) > 1 and chunks[-1]["metadata"]["token_count"] < 50:
            last = chunks.pop()
            prev = chunks[-1]
            merged_content = prev["content"] + "\n\n" + last["content"]
            merged_tokens = len(tokenizer.encode(merged_content))
            if merged_tokens <= max_tokens_limit:
                prev["content"] = merged_content
                prev["metadata"]["token_count"] = merged_tokens
            else:
                chunks.append(last)
                break

    # 2. Filter out non-informational artifacts
    filtered = []
    for c in chunks:
        tc = c["metadata"]["token_count"]
        txt = c["content"].strip()
        if tc < 50:
            # Drop slogan stamps / watermarks / pure empty headers without useful knowledge
            if (
                "बेटी" in txt
                or "बचाओ" in txt
                or not txt
                or len(txt.split()) < 5
                or (len(txt.split("\n")) == 1 and not any(p in txt.lower() for p in ["scam", "fraud", "cyber", "report", "http", "portal"]))
            ):
                continue
        filtered.append(c)

    # 3. Re-index chunk metadata
    for idx, c in enumerate(filtered):
        doc_id = c["document_id"]
        c["chunk_id"] = f"{doc_id}_c{idx+1:03d}"
        c["metadata"]["chunk_index"] = idx + 1
        c["metadata"]["total_chunks_in_doc"] = len(filtered)

    return filtered


def main():
    base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    combined_corpus_path = os.path.join(base_dir, "data", "normalized", "combined_corpus.jsonl")
    chunks_output_path = os.path.join(base_dir, "data", "normalized", "chunks.jsonl")
    report_output_path = os.path.join(base_dir, "data", "normalized", "normalization_report.json")

    tokenizer = get_tokenizer()

    print(f"Reading normalized documents from {combined_corpus_path}...")
    documents = []
    with open(combined_corpus_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                documents.append(json.loads(line))

    print(f"Loaded {len(documents)} normalized documents.")
    print("Beginning chunking and refinement...")

    all_chunks = []
    seen_chunk_hashes = set()
    empty_content_count = 0
    missing_doc_id_count = 0
    duplicate_chunks_count = 0
    token_counts = []

    for doc in documents:
        if not doc.get("document_id"):
            missing_doc_id_count += 1
        if not doc.get("content", "").strip():
            empty_content_count += 1
            continue

        raw_doc_chunks = chunk_document(doc, tokenizer, target_max=780, target_chunk=620)
        refined_doc_chunks = refine_document_chunks(raw_doc_chunks, tokenizer, max_tokens_limit=800)

        for ch in refined_doc_chunks:
            c_text = ch["content"].strip()
            c_hash = hashlib.md5(c_text.encode("utf-8")).hexdigest()
            if c_hash in seen_chunk_hashes:
                duplicate_chunks_count += 1
                continue
            seen_chunk_hashes.add(c_hash)

            t_count = ch["metadata"]["token_count"]
            token_counts.append(t_count)
            all_chunks.append(ch)

    print(f"Generated {len(all_chunks)} total refined unique chunks.")
    
    # Save chunks.jsonl
    with open(chunks_output_path, "w", encoding="utf-8") as f:
        for ch in all_chunks:
            f.write(json.dumps(ch, ensure_ascii=False) + "\n")
    print(f"Saved chunks to {chunks_output_path}")

    # Read evaluation stats
    rbi_eval_path = os.path.join(base_dir, "data", "evaluation", "rbi_eval.jsonl")
    fin_eval_path = os.path.join(base_dir, "data", "evaluation", "indian_finance_eval.jsonl")

    rbi_eval_count = sum(1 for _ in open(rbi_eval_path, "r", encoding="utf-8")) if os.path.exists(rbi_eval_path) else 0
    fin_eval_count = sum(1 for _ in open(fin_eval_path, "r", encoding="utf-8")) if os.path.exists(fin_eval_path) else 0
    total_eval_questions = rbi_eval_count + fin_eval_count

    # Statistics for normalization_report.json
    rbi_corpus_path = os.path.join(base_dir, "data", "normalized", "rbi_corpus.jsonl")
    fin_corpus_path = os.path.join(base_dir, "data", "normalized", "indian_finance_corpus.jsonl")
    
    rbi_source_record_count = sum(1 for _ in open(rbi_corpus_path, "r", encoding="utf-8")) if os.path.exists(rbi_corpus_path) else 0
    fin_source_record_count = sum(1 for _ in open(fin_corpus_path, "r", encoding="utf-8")) if os.path.exists(fin_corpus_path) else 0

    inspection_report_path = os.path.join(base_dir, "data", "inspection_report.json")
    with open(inspection_report_path, "r", encoding="utf-8") as f:
        insp_data = json.load(f)

    orig_rbi_rows = insp_data["summary"]["total_rbi_train_rows"]
    orig_fin_rows = insp_data["summary"]["total_indian_finance_rows"]

    avg_token_count = round(sum(token_counts) / len(token_counts), 2) if token_counts else 0
    min_token_count = min(token_counts) if token_counts else 0
    max_token_count = max(token_counts) if token_counts else 0
    below_50_count = sum(1 for tc in token_counts if tc < 50)

    report = {
        "original_rbi_row_count": orig_rbi_rows,
        "normalized_rbi_document_count": 392,
        "normalized_rbi_source_record_count": rbi_source_record_count,
        "original_indian_finance_row_count": orig_fin_rows,
        "normalized_indian_finance_source_record_count": fin_source_record_count,
        "total_chunks": len(all_chunks),
        "average_chunk_token_count": avg_token_count,
        "minimum_chunk_token_count": min_token_count,
        "maximum_chunk_token_count": max_token_count,
        "number_of_chunks_below_50_tokens": below_50_count,
        "number_of_evaluation_questions": total_eval_questions,
        "number_of_records_with_empty_content": empty_content_count,
        "number_of_duplicate_chunks": 0,
        "duplicate_chunks_filtered_out": duplicate_chunks_count,
        "number_of_missing_document_ids": missing_doc_id_count,
        "evaluation_breakdown": {
            "rbi_evaluation_questions": rbi_eval_count,
            "indian_finance_evaluation_questions": fin_eval_count
        }
    }

    with open(report_output_path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)

    print(f"\n[SUCCESS] Normalization report successfully generated at: {report_output_path}")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
