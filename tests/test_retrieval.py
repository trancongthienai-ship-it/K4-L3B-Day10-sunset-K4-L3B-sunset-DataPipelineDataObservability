from __future__ import annotations

import importlib.util
from pathlib import Path
import sys
import types

import pandas as pd


ROOT = Path(__file__).parents[1]


def _load_module(monkeypatch, name: str, relative_path: str, stubs: dict[str, types.ModuleType]):
    for module_name, module in stubs.items():
        monkeypatch.setitem(sys.modules, module_name, module)
    spec = importlib.util.spec_from_file_location(name, ROOT / relative_path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    monkeypatch.setitem(sys.modules, name, module)
    spec.loader.exec_module(module)
    return module


def _index_module(monkeypatch):
    chromadb = types.ModuleType("chromadb")
    chromadb.PersistentClient = object

    embeddings = types.ModuleType("retrieval.embeddings")
    embeddings.MiniLMEmbeddings = object

    return _load_module(
        monkeypatch,
        "retrieval_index_under_test",
        "src/retrieval/index.py",
        {"chromadb": chromadb, "retrieval.embeddings": embeddings},
    )


def test_build_documents_normalizes_chromadb_metadata_values(monkeypatch) -> None:
    index_module = _index_module(monkeypatch)
    frame = pd.DataFrame(
        [
            {
                "paper_id": "10.1000/example",
                "title": "Reliable RAG",
                "text_for_embedding": "Reliable RAG summary",
                "published": pd.Timestamp("2026-07-22"),
                "authors_joined": None,
                "categories_joined": float("nan"),
                "summary": "A paper about reliable retrieval.",
                "abs_url": pd.NA,
                "pdf_url": "https://example.org/paper.pdf",
            }
        ]
    )

    [document] = index_module.LocalEmbeddingIndex._build_documents(frame)

    assert document["metadata"] == {
        "paper_id": "10.1000/example",
        "title": "Reliable RAG",
        "published": "2026-07-22",
        "authors_joined": "",
        "categories_joined": "",
        "summary": "A paper about reliable retrieval.",
        "abs_url": "",
        "pdf_url": "https://example.org/paper.pdf",
    }


def test_format_search_results_explains_empty_result(monkeypatch) -> None:
    langchain_agents = types.ModuleType("langchain.agents")
    langchain_agents.create_agent = object
    langchain_tools = types.ModuleType("langchain.tools")
    langchain_tools.tool = lambda function: function
    retrieval_index = types.ModuleType("retrieval.index")
    retrieval_index.LocalEmbeddingIndex = object
    retrieval_llm = types.ModuleType("retrieval.llm")
    retrieval_llm.build_llm = object

    agent_module = _load_module(
        monkeypatch,
        "retrieval_agent_under_test",
        "src/retrieval/agent.py",
        {
            "langchain.agents": langchain_agents,
            "langchain.tools": langchain_tools,
            "retrieval.index": retrieval_index,
            "retrieval.llm": retrieval_llm,
        },
    )

    assert agent_module._format_search_results([]) == "No relevant papers found in the indexed corpus."
