"""
Dataset Inspection Script for FinCheck AI
Inspects RBI Circular QA and Indian Financial Inclusion datasets.
Outputs statistics, schemas, samples, and field categorization to data/inspection_report.json.
"""

import json
import os
import sys
from typing import Any, Dict, List
import numpy as np
import pandas as pd


def make_serializable(obj: Any) -> Any:
    """Recursively convert numpy/pandas types to standard python types for JSON serialization."""
    if isinstance(obj, (np.integer, np.int64, np.int32)):
        return int(obj)
    elif isinstance(obj, (np.floating, np.float64, np.float32)):
        return float(obj)
    elif isinstance(obj, (np.bool_, bool)):
        return bool(obj)
    elif isinstance(obj, np.ndarray):
        return obj.tolist()
    elif isinstance(obj, pd.Series):
        return obj.to_dict()
    elif isinstance(obj, dict):
        return {k: make_serializable(v) for k, v in obj.items()}
    elif isinstance(obj, (list, tuple)):
        return [make_serializable(item) for item in obj]
    return obj


def inspect_rbi_dataset(file_path: str) -> Dict[str, Any]:
    print(f"\nLoading RBI dataset from {file_path}...")
    df = pd.read_parquet(file_path)
    
    num_rows = len(df)
    columns = list(df.columns)
    data_types = {col: str(df[col].dtype) for col in columns}
    null_counts = {col: int(df[col].isnull().sum()) for col in columns}
    
    samples = []
    for idx in range(min(3, num_rows)):
        row_dict = df.iloc[idx].to_dict()
        samples.append(make_serializable(row_dict))
    
    unique_documents = int(df["document"].nunique()) if "document" in df.columns else None
    unique_chunks = int(df["chunks_text"].nunique()) if "chunks_text" in df.columns else None
    unique_questions = int(df["question"].nunique()) if "question" in df.columns else None

    # Field categorization
    source_text_fields = ["chunks_text"]
    metadata_fields = [
        "document", "filename", "model_name", "regulation_area",
        "applicable_to", "issued_on", "key_topics", "is_table", "data_source"
    ]
    evaluation_qa_fields = [
        "question", "answer", "evaluation_criteria", "category",
        "estimated_difficulty", "rephrased_question", "rephrased_answer"
    ]
    
    return {
        "file_path": file_path,
        "num_rows": num_rows,
        "unique_documents": unique_documents,
        "unique_chunks_text": unique_chunks,
        "unique_questions": unique_questions,
        "columns": columns,
        "data_types": data_types,
        "null_counts": null_counts,
        "sample_records": samples,
        "field_analysis": {
            "source_text_fields": source_text_fields,
            "metadata_fields": metadata_fields,
            "evaluation_qa_fields": evaluation_qa_fields,
            "notes": (
                "The RBI dataset is primarily a synthetic QA dataset generated over 755 unique "
                "underlying RBI circular chunks (589 unique in eval). The 'chunks_text' field contains "
                "the authentic regulatory circular text with section titles, dates, and circular numbers. "
                "The 'question' and 'answer' fields are QA pairs suitable for evaluation and benchmark testing, "
                "not as primary grounding text for the RAG corpus."
            )
        }
    }


def inspect_indian_finance_dataset(file_path: str) -> Dict[str, Any]:
    print(f"\nLoading Indian Finance dataset from {file_path}...")
    num_rows = 0
    samples = []
    null_counts: Dict[str, int] = {}
    keys_found = []
    data_types: Dict[str, str] = {}
    
    with open(file_path, "r", encoding="utf-8") as f:
        for idx, line in enumerate(f):
            line = line.strip()
            if not line:
                continue
            num_rows += 1
            rec = json.loads(line)
            
            if idx == 0:
                keys_found = list(rec.keys())
                for k in keys_found:
                    null_counts[k] = 0
                    data_types[k] = type(rec[k]).__name__
            
            for k in keys_found:
                val = rec.get(k)
                if val is None or (isinstance(val, str) and not val.strip()):
                    null_counts[k] += 1
            
            if idx < 3:
                samples.append(rec)
    
    # Field categorization
    source_text_fields = [
        "Reference context extracted from 'original_prompt' (lines 3-4+) / 'enhanced_prompt' (# Context section)"
    ]
    metadata_fields = [
        "Domain / Regulation Area (line 1 of original_prompt / '## Reference Material: <Area>')",
        "Subtopic / Section (line 2 of original_prompt / '### <Subtopic>')",
        "Role / Guidelines in 'enhanced_prompt'"
    ]
    evaluation_qa_fields = [
        "Question / Scenario (line 0 of original_prompt)",
        "original_completion (short answer)",
        "enhanced_completion (detailed comprehensive answer)"
    ]
    
    return {
        "file_path": file_path,
        "num_rows": num_rows,
        "columns": keys_found,
        "data_types": data_types,
        "null_counts": null_counts,
        "sample_records": samples,
        "field_analysis": {
            "source_text_fields": source_text_fields,
            "metadata_fields": metadata_fields,
            "evaluation_qa_fields": evaluation_qa_fields,
            "notes": (
                "The Indian Finance dataset consists of 6,487 prompt-completion pairs. "
                "Each record's 'original_prompt' contains a 6-line structure: "
                "Line 0 = User question/scenario; Line 1 = Financial Domain/Area; Line 2 = Subtopic/Section; "
                "Lines 3-4 = Reference source explanation/rules; Line 5 = Learning objective. "
                "'enhanced_prompt' contains the explicit '# Context' block with the reference material. "
                "'original_completion' and 'enhanced_completion' are model-generated answers that must be kept "
                "as evaluation QA pairs rather than authoritative source text."
            )
        }
    }


def main():
    base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    
    rbi_train_path = os.path.join(base_dir, "datasets", "rbi", "train-00000-of-00001.parquet")
    rbi_eval_path = os.path.join(base_dir, "datasets", "rbi", "eval-00000-of-00001.parquet")
    indian_finance_path = os.path.join(base_dir, "datasets", "indian-finance", "train_0.jsonl")
    
    report_output_dir = os.path.join(base_dir, "data")
    os.makedirs(report_output_dir, exist_ok=True)
    report_output_file = os.path.join(report_output_dir, "inspection_report.json")
    
    rbi_train_info = inspect_rbi_dataset(rbi_train_path)
    rbi_eval_info = inspect_rbi_dataset(rbi_eval_path)
    indian_finance_info = inspect_indian_finance_dataset(indian_finance_path)
    
    report = {
        "datasets": {
            "rbi_train": rbi_train_info,
            "rbi_eval": rbi_eval_info,
            "indian_finance": indian_finance_info
        },
        "summary": {
            "total_rbi_train_rows": rbi_train_info["num_rows"],
            "total_rbi_eval_rows": rbi_eval_info["num_rows"],
            "unique_rbi_train_chunks": rbi_train_info["unique_chunks_text"],
            "unique_rbi_eval_chunks": rbi_eval_info["unique_chunks_text"],
            "total_indian_finance_rows": indian_finance_info["num_rows"]
        }
    }
    
    with open(report_output_file, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    
    print(f"\n[SUCCESS] Inspection report successfully generated at: {report_output_file}")


if __name__ == "__main__":
    main()
