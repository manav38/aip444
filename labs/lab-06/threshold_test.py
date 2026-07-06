from utils import dot_product, get_embedding, load_database


def print_top_matches(query: str, products: list[dict], top_n: int = 3) -> None:
    print("=" * 80)
    print(f"Query: {query}")
    print("=" * 80)

    query_embedding = get_embedding(query)

    scored = []

    for product in products:
        score = dot_product(query_embedding, product["embedding"])
        scored.append(
            {
                "title": product.get("title", ""),
                "category": product.get("category", ""),
                "price": product.get("price", 0),
                "score": score,
            }
        )

    scored.sort(key=lambda item: item["score"], reverse=True)

    for index, item in enumerate(scored[:top_n], start=1):
        print(
            f"{index}. {item['title']} "
            f"({item['category']}) - ${item['price']} "
            f"| Score: {item['score']:.4f}"
        )

    print()


def main() -> None:
    products = load_database()

    print(f"Loaded {len(products)} products.")
    print()

    print_top_matches(
        query="Nice smelling scent",
        products=products,
    )

    print_top_matches(
        query="A textbook on quantum physics",
        products=products,
    )

    print("Threshold guidance:")
    print("- Pick a value below the good-match scores.")
    print("- Pick a value above the bad-match scores if possible.")
    print("- Update MIN_SIMILARITY_SCORE in utils.py if needed.")


if __name__ == "__main__":
    main()