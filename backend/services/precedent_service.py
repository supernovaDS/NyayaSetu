"""Precedent search using Gemini embeddings + cosine similarity. Zero extra dependencies."""

import os
import math
from google import genai

client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

SEED_CASES = [
    {
        "id": "prec_001",
        "case_name": "State of Karnataka vs. Environmental Protection Group (2023)",
        "category": "Environmental Compliance",
        "summary": "High Court directed the State to shut down a polluting industrial unit within 60 days and pay compensation to affected residents. The State complied by issuing closure orders and disbursing compensation within the stipulated period.",
        "outcome": "compliance",
        "action_taken": "State complied within deadline. Factory shut down, compensation paid.",
    },
    {
        "id": "prec_002",
        "case_name": "Union of India vs. National Highway Contractors Association (2022)",
        "category": "Infrastructure / Contract Dispute",
        "summary": "Supreme Court ordered the Union to release pending payments to highway contractors within 90 days and directed arbitration for disputed claims. The government filed a review petition within the limitation period.",
        "outcome": "review",
        "action_taken": "Government filed review petition within 90 days.",
    },
    {
        "id": "prec_003",
        "case_name": "State of Maharashtra vs. Municipal Workers Union (2023)",
        "category": "Service Matter",
        "summary": "High Court ordered reinstatement of terminated municipal employees with full back wages. The State initially delayed compliance, leading to contempt proceedings, after which the employees were reinstated.",
        "outcome": "compliance",
        "action_taken": "State complied after contempt notice. Employees reinstated with back wages.",
    },
    {
        "id": "prec_004",
        "case_name": "State of Tamil Nadu vs. Revenue Officers Association (2024)",
        "category": "Service Matter / Pay Revision",
        "summary": "High Court directed the State to implement revised pay scales for revenue officers within 120 days. The State filed an appeal in the Supreme Court challenging the financial burden.",
        "outcome": "appeal",
        "action_taken": "State filed appeal within 30 days of order.",
    },
    {
        "id": "prec_005",
        "case_name": "State of Rajasthan vs. Land Acquisition Petitioners (2023)",
        "category": "Land Acquisition",
        "summary": "High Court quashed land acquisition proceedings and directed the State to return acquired land or pay enhanced compensation. The State chose to pay enhanced compensation as returning land was not feasible.",
        "outcome": "compliance",
        "action_taken": "State paid enhanced compensation within 60 days.",
    },
]

_embedding_cache: dict[str, list[float]] = {}


def _cosine_similarity(a: list[float], b: list[float]) -> float:
    dot = sum(x * y for x, y in zip(a, b))
    norm_a = math.sqrt(sum(x * x for x in a))
    norm_b = math.sqrt(sum(x * x for x in b))
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return dot / (norm_a * norm_b)


async def _get_embedding(text: str) -> list[float]:
    response = await client.aio.models.embed_content(
        model="text-embedding-004",
        contents=text,
    )
    return response.embeddings[0].values


async def search_precedents(query: str, top_k: int = 3) -> list[dict]:
    """Search pre-seeded cases by semantic similarity. Returns top-k matches."""
    try:
        query_emb = await _get_embedding(query)
    except Exception:
        return []

    # Lazily compute + cache embeddings for seed cases
    for case in SEED_CASES:
        if case["id"] not in _embedding_cache:
            try:
                _embedding_cache[case["id"]] = await _get_embedding(case["summary"])
            except Exception:
                continue

    results = []
    for case in SEED_CASES:
        if case["id"] not in _embedding_cache:
            continue
        sim = _cosine_similarity(query_emb, _embedding_cache[case["id"]])
        results.append({**case, "similarity": round(sim, 3)})

    results.sort(key=lambda x: x["similarity"], reverse=True)
    return results[:top_k]
