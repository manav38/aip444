from utils import MIN_SIMILARITY_SCORE, load_database, search_products


def print_result(index: int, product: dict) -> None:
    title = product.get("title", "Unknown Product")
    price = product.get("price", 0)
    category = product.get("category", "unknown")

    vector_score = product.get("vector_score", 0)
    rerank_score = product.get("rerank_score", 0)

    print(
        f"{index}. [Rerank: {rerank_score:.4f} | "
        f"Vector: {vector_score:.4f}] "
        f"{title} - ${price} ({category})"
    )


def main() -> None:
    print("Loading semantic search database...")
    products = load_database()

    print(f"Loaded {len(products)} products.")
    print(f"Minimum similarity threshold: {MIN_SIMILARITY_SCORE}")
    print()
    print("Type 'exit' or 'quit' to stop.")
    print()

    while True:
        query = input("What are you looking for? ").strip()

        if query.lower() in {"exit", "quit"}:
            print("Goodbye.")
            break

        if not query:
            continue

        try:
            results = search_products(query, products)
        except Exception as error:
            print(f"Search failed: {error}")
            continue

        print()

        if not results:
            print("I'm sorry, we don't have anything like that in stock.")
            print()
            continue

        print(f"Found {len(results)} matches:")

        for index, product in enumerate(results, start=1):
            print_result(index, product)

        print()


if __name__ == "__main__":
    main()