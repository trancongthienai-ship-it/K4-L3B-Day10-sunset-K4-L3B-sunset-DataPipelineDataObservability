from __future__ import annotations

from datetime import datetime

import pandas as pd

from ingestion.crossref import PaperRecord


import dataclasses

def build_clean_dataframe(records: list[PaperRecord], run_date: datetime) -> pd.DataFrame:
    if not records:
        return pd.DataFrame()
        
    df = pd.DataFrame([dataclasses.asdict(r) for r in records])
    
    df["title"] = df["title"].str.strip()
    df["summary"] = df["summary"].str.strip()
    
    published_dt = pd.to_datetime(df["published"], errors="coerce")
    updated_dt = pd.to_datetime(df["updated"], errors="coerce")
    
    run_date_obj = pd.to_datetime(run_date).tz_localize(None)
    df["age_days"] = (run_date_obj - published_dt).dt.days
    
    df["published"] = published_dt.dt.strftime('%Y-%m-%d').fillna("")
    df["updated"] = updated_dt.dt.strftime('%Y-%m-%d').fillna("")
    
    df["authors_joined"] = df["authors"].apply(lambda x: ", ".join(x) if isinstance(x, list) else str(x))
    df["categories_joined"] = df["categories"].apply(lambda x: ", ".join(x) if isinstance(x, list) else str(x))
    df["summary_chars"] = df["summary"].str.len()
    
    df["text_for_embedding"] = df.apply(
        lambda row: f"Title: {row['title']}\nAuthors: {row['authors_joined']}\nAbstract: {row['summary']}", 
        axis=1
    )
    
    df = df.drop_duplicates(subset=["paper_id"], keep="first")
    df = df[df["title"].notnull() & (df["title"] != "")]
    
    df = df.sort_values(by="published", ascending=False).reset_index(drop=True)
    
    return df
