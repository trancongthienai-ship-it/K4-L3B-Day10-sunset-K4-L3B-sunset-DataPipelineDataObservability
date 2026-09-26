from __future__ import annotations

from pathlib import Path
from typing import Any

import pandas as pd

from core.utils import first_sentence, normalize_whitespace, write_json


QUESTION_TYPES = (
    "summary",
    "authors",
    "date",
    "categories",
    "summary",
    "authors",
    "date",
    "categories",
    "summary",
    "authors",
)


def _question_and_answer(question_type: str, row: pd.Series) -> tuple[str, str]:
    title = normalize_whitespace(str(row["title"]))
    if question_type == "summary":
        return (
            f"What is the summary of the paper '{title}'?",
            first_sentence(str(row["summary"])),
        )
    if question_type == "authors":
        return f"Who authored the paper '{title}'?", normalize_whitespace(str(row["authors_joined"]))
    if question_type == "date":
        return f"When was the paper '{title}' published?", normalize_whitespace(str(row["published"]))
    if question_type == "categories":
        return (
            f"What categories does the paper '{title}' belong to?",
            normalize_whitespace(str(row["categories_joined"])),
        )
    raise ValueError(f"Unsupported question type: {question_type}")


def build_test_set(df: pd.DataFrame, output_path) -> list[dict[str, Any]]:
    """Build and persist a deterministic ten-question evaluation set."""
    required_columns = {
        "paper_id",
        "title",
        "summary",
        "authors_joined",
        "published",
        "categories_joined",
    }
    missing_columns = required_columns - set(df.columns)
    if missing_columns:
        raise ValueError(f"Clean dataframe is missing columns: {sorted(missing_columns)}")

    candidates = df.drop_duplicates(subset="paper_id", keep="first").copy()
    candidates = candidates.dropna(subset=list(required_columns))
    for column in required_columns:
        candidates = candidates[candidates[column].astype(str).str.strip().ne("")]
    if len(candidates) < len(QUESTION_TYPES):
        raise ValueError(
            f"At least {len(QUESTION_TYPES)} valid unique papers are required; got {len(candidates)}."
        )

    # Sorting before sampling makes repeated pipeline runs produce the same test set.
    candidates = candidates.sort_values(["published", "paper_id"], ascending=[False, True]).reset_index(drop=True)
    last_position = len(candidates) - 1
    selected_positions = [round(index * last_position / (len(QUESTION_TYPES) - 1)) for index in range(len(QUESTION_TYPES))]

    test_set: list[dict[str, Any]] = []
    for index, (position, question_type) in enumerate(
        zip(selected_positions, QUESTION_TYPES, strict=True), start=1
    ):
        row = candidates.iloc[position]
        question, ground_truth = _question_and_answer(question_type, row)
        test_set.append(
            {
                "id": f"eval_{index:03d}",
                "question_type": question_type,
                "question": question,
                "ground_truth": ground_truth,
                "ground_truth_doc_ids": [normalize_whitespace(str(row["paper_id"])).lower()],
            }
        )

    write_json(Path(output_path), test_set)
    return test_set
