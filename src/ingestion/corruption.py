from __future__ import annotations

import pandas as pd


import json
from pathlib import Path

def corrupt_clean_dataframe(df: pd.DataFrame, output_log_path) -> pd.DataFrame:
    df = df.copy()
    
    if len(df) > 5:
        df = df.sort_values(by="published", ascending=False).iloc[2:].reset_index(drop=True)
    
    if len(df) > 0:
        df.loc[0, "summary"] = ""
        
    if len(df) > 1:
        df.loc[1, "summary"] = str(df.loc[1, "summary"]) + " NOISE NOISE NOISE"
        
    if len(df) > 2:
        df.loc[2, "title"] = str(df.loc[2, "title"])[:5]
        
    if len(df) > 3:
        df.loc[3, "age_days"] = 9999
        
    if len(df) > 4:
        df = pd.concat([df, df.iloc[[4]]], ignore_index=True)
        
    df["text_for_embedding"] = df.apply(
        lambda row: f"Title: {row['title']}\nAuthors: {row['authors_joined']}\nAbstract: {row['summary']}", 
        axis=1
    )
    
    log = {
        "dropped_latest": 2,
        "blank_summary": 1,
        "injected_noise": 1,
        "truncated_title": 1,
        "old_date": 1,
        "duplicate_rows": 1,
        "total_rows": len(df)
    }
    
    path_obj = Path(output_log_path)
    path_obj.parent.mkdir(parents=True, exist_ok=True)
    with open(path_obj, "w", encoding="utf-8") as f:
        json.dump(log, f, indent=2)
        
    return df
