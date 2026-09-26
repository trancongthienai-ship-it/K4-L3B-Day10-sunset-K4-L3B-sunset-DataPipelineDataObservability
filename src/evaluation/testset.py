from __future__ import annotations

from typing import Any

import pandas as pd


import json
from pathlib import Path

def build_test_set(df: pd.DataFrame, output_path) -> list[dict[str, Any]]:
    if df.empty:
        return []
        
    test_set = []
    
    # 1. & 2. Chon 4 paper dai dien hoac it hon neu khong du
    sample_size = min(4, len(df))
    sampled_df = df.head(sample_size)
    
    for idx, row in sampled_df.iterrows():
        paper_id = row['paper_id']
        title = row['title']
        authors = row['authors_joined']
        published = str(row['published'])
        categories = row['categories_joined']
        summary = row['summary']
        
        # summary question
        test_set.append({
            "id": f"{paper_id}_summary",
            "question_type": "summary",
            "question": f"What is the summary of the paper '{title}'?",
            "ground_truth": summary,
            "ground_truth_doc_ids": [paper_id]
        })
        
        # authors question
        test_set.append({
            "id": f"{paper_id}_authors",
            "question_type": "authors",
            "question": f"Who are the authors of '{title}'?",
            "ground_truth": authors,
            "ground_truth_doc_ids": [paper_id]
        })
        
        # date question
        test_set.append({
            "id": f"{paper_id}_date",
            "question_type": "date",
            "question": f"When was '{title}' published?",
            "ground_truth": published,
            "ground_truth_doc_ids": [paper_id]
        })
        
        # categories question
        test_set.append({
            "id": f"{paper_id}_categories",
            "question_type": "categories",
            "question": f"What are the categories of '{title}'?",
            "ground_truth": categories,
            "ground_truth_doc_ids": [paper_id]
        })
        
    path_obj = Path(output_path)
    path_obj.parent.mkdir(parents=True, exist_ok=True)
    with open(path_obj, "w", encoding="utf-8") as f:
        json.dump(test_set, f, indent=2, ensure_ascii=False)
        
    return test_set
