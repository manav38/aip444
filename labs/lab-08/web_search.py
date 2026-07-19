import os
from typing import Any, Dict, List

from dotenv import find_dotenv, load_dotenv
from tavily import TavilyClient


def load_tavily_client() -> TavilyClient:
    load_dotenv(find_dotenv())

    api_key = os.getenv("TAVILY_API_KEY")

    if not api_key:
        raise RuntimeError("TAVILY_API_KEY not found in .env file.")

    return TavilyClient(api_key=api_key)


def lookup_error(query: str) -> Dict[str, Any]:
    client = load_tavily_client()

    response = client.search(
        query=query,
        search_depth="advanced",
        max_results=5,
        include_answer=True,
    )

    results = response.get("results", [])

    cleaned_results: List[Dict[str, str]] = []

    for result in results:
        cleaned_results.append(
            {
                "title": result.get("title", ""),
                "url": result.get("url", ""),
                "content": result.get("content", ""),
            }
        )

    return {
        "query": query,
        "answer": response.get("answer", ""),
        "results": cleaned_results,
    }