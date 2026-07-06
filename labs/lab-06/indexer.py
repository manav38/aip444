import json
from pathlib import Path

import requests

from utils import clean_tsv_value, get_embeddings, serialize_product


PRODUCTS_API_URL = "https://dummyjson.com/products?limit=200"

PRODUCTS_FILE = "products.json"
VECTORS_FILE = "vectors.tsv"
METADATA_FILE = "metadata.tsv"


def fetch_products() -> list[dict]:
    print("Fetching products from DummyJSON...")

    response = requests.get(PRODUCTS_API_URL, timeout=60)

    if response.status_code != 200:
        raise RuntimeError(
            f"Failed to fetch products. HTTP {response.status_code}: {response.text}"
        )

    data = response.json()
    products = data.get("products", [])

    if not products:
        raise RuntimeError("No products found in API response.")

    print(f"Fetched {len(products)} products.")

    return products


def save_products(products: list[dict]) -> None:
    Path(PRODUCTS_FILE).write_text(
        json.dumps(products, indent=2),
        encoding="utf-8",
    )

    print(f"Saved {PRODUCTS_FILE}.")


def save_vectors(vectors: list[list[float]]) -> None:
    lines = []

    for vector in vectors:
        lines.append("\t".join(str(value) for value in vector))

    Path(VECTORS_FILE).write_text(
        "\n".join(lines),
        encoding="utf-8",
    )

    print(f"Saved {VECTORS_FILE} with {len(vectors)} rows.")


def save_metadata(products: list[dict]) -> None:
    lines = ["Title\tCategory"]

    for product in products:
        title = clean_tsv_value(product.get("title", ""))
        category = clean_tsv_value(product.get("category", ""))

        lines.append(f"{title}\t{category}")

    Path(METADATA_FILE).write_text(
        "\n".join(lines),
        encoding="utf-8",
    )

    print(f"Saved {METADATA_FILE}.")


def main() -> None:
    products = fetch_products()

    save_products(products)

    serialized_products = [serialize_product(product) for product in products]

    print("Example serialized product:")
    print(serialized_products[0])
    print()

    print("Creating embeddings in one batch...")
    vectors = get_embeddings(serialized_products)

    print(f"Created {len(vectors)} embeddings.")
    print(f"Embedding dimensions: {len(vectors[0])}")

    save_vectors(vectors)
    save_metadata(products)

    print()
    print("Index complete.")
    print("Generated files:")
    print(f"- {PRODUCTS_FILE}")
    print(f"- {VECTORS_FILE}")
    print(f"- {METADATA_FILE}")


if __name__ == "__main__":
    main()