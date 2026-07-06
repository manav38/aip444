import json
import os
from pathlib import Path
from typing import Any

import requests
from dotenv import find_dotenv, load_dotenv
from openai import OpenAI


EMBEDDING_MODEL = "openai/text-embedding-3-small"
RERANK_MODEL = "cohere/rerank-v3.5"

PRODUCTS_FILE = "products.json"
VECTORS_FILE = "vectors.tsv"

MIN_SIMILARITY_SCORE = 0.30


def load_api_key() -> str:
    load_dotenv(find_dotenv())

    api_key = os.getenv("OPENROUTER_API_KEY")

    if not api_key:
        raise RuntimeError("OPENROUTER_API_KEY not found in .env file.")

    return api_key


def get_openrouter_client() -> OpenAI:
    return OpenAI(
        base_url="https://openrouter.ai/api/v1",
        api_key=load_api_key(),
    )


def clean_tsv_value(value: Any) -> str:
    return str(value).replace("\t", " ").replace("\n", " ").replace("\r", " ").strip()


def serialize_product(product: dict[str, Any]) -> str:
    title = product.get("title", "")
    category = product.get("category", "")
    description = product.get("description", "")
    tags = product.get("tags", [])
    brand = product.get("brand", "")

    if isinstance(tags, list):
        tags_text = ", ".join(str(tag) for tag in tags)
    else:
        tags_text = str(tags)

    parts = [
        f"Title: {title}",
        f"Category: {category}",
        f"Description: {description}",
        f"Tags: {tags_text}",
    ]

    if brand:
        parts.append(f"Brand: {brand}")

    return " | ".join(clean_tsv_value(part) for part in parts)


def get_embeddings(texts: list[str]) -> list[list[float]]:
    client = get_openrouter_client()

    response = client.embeddings.create(
        model=EMBEDDING_MODEL,
        input=texts,
    )

    return [item.embedding for item in response.data]


def get_embedding(text: str) -> list[float]:
    return get_embeddings([text])[0]


def dot_product(vec_a: list[float], vec_b: list[float]) -> float:
    return sum(a * b for a, b in zip(vec_a, vec_b))


def load_database() -> list[dict[str, Any]]:
    products_path = Path(PRODUCTS_FILE)
    vectors_path = Path(VECTORS_FILE)

    if not products_path.exists():
        raise FileNotFoundError(
            "products.json not found. Run `python indexer.py` first."
        )

    if not vectors_path.exists():
        raise FileNotFoundError(
            "vectors.tsv not found. Run `python indexer.py` first."
        )

    products = json.loads(products_path.read_text(encoding="utf-8"))

    vectors_data = vectors_path.read_text(encoding="utf-8")
    vector_lines = vectors_data.strip().split("\n")

    if len(products) != len(vector_lines):
        raise ValueError(
            f"Index alignment error: {len(products)} products but "
            f"{len(vector_lines)} vector rows."
        )

    products_with_embeddings = []

    for product, line in zip(products, vector_lines):
        vector = [float(value) for value in line.split("\t")]
        products_with_embeddings.append(
            {
                **product,
                "embedding": vector,
            }
        )

    return products_with_embeddings


def vector_search_candidates(
    query: str,
    products: list[dict[str, Any]],
    min_score: float = MIN_SIMILARITY_SCORE,
    top_k: int = 20,
) -> list[dict[str, Any]]:
    query_embedding = get_embedding(query)

    scored_products = []

    for product in products:
        score = dot_product(query_embedding, product["embedding"])

        if score >= min_score:
            scored_products.append(
                {
                    **product,
                    "vector_score": score,
                }
            )

    scored_products.sort(key=lambda item: item["vector_score"], reverse=True)

    return scored_products[:top_k]


def rerank_results(
    query: str,
    candidates: list[dict[str, Any]],
    top_n: int = 5,
) -> list[dict[str, Any]]:
    if not candidates:
        return []

    api_key = load_api_key()

    documents = [serialize_product(candidate) for candidate in candidates]

    response = requests.post(
        "https://openrouter.ai/api/v1/rerank",
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        json={
            "model": RERANK_MODEL,
            "query": query,
            "documents": documents,
            "top_n": min(top_n, len(documents)),
        },
        timeout=60,
    )

    if response.status_code != 200:
        raise RuntimeError(
            f"Rerank API failed with HTTP {response.status_code}: {response.text}"
        )

    data = response.json()

    reranked = []

    for result in data.get("results", []):
        index = result["index"]
        reranked.append(
            {
                **candidates[index],
                "rerank_score": result["relevance_score"],
            }
        )

    return reranked


def search_products(
    query: str,
    products: list[dict[str, Any]],
    min_score: float = MIN_SIMILARITY_SCORE,
) -> list[dict[str, Any]]:
    candidates = vector_search_candidates(
        query=query,
        products=products,
        min_score=min_score,
        top_k=20,
    )

    if not candidates:
        return []

    return rerank_results(
        query=query,
        candidates=candidates,
        top_n=5,
    )