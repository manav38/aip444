# Lab 6 - Semantic Search & Vector Spaces

This lab builds a semantic search engine for a product catalog.

The system fetches products from DummyJSON, serializes each product into clean text, creates embeddings, saves a vector index, visualizes the product space, searches with dot product similarity, filters results with a similarity threshold, and reranks candidates using a reranking model.

## Files

- `utils.py`: Shared helper functions for serialization, embeddings, dot product, database loading, search, and reranking.
- `indexer.py`: Fetches products, creates embeddings, and writes the index files.
- `threshold_test.py`: Tests good and bad queries to choose a similarity threshold.
- `search.py`: Interactive semantic search CLI.
- `products.json`: Product database fetched from DummyJSON.
- `vectors.tsv`: Product embeddings for search and visualization.
- `metadata.tsv`: Product title/category metadata for TensorFlow Embedding Projector.

## Models

- Embedding model: `openai/text-embedding-3-small`
- Reranking model: `cohere/rerank-v3.5`

## Setup

Install dependencies:

    pip install openai python-dotenv requests

Make sure the root `.env` file contains:

    OPENROUTER_API_KEY=your_key_here

Do not commit `.env`.

## Step 1 - Build the Index

Run:

    python indexer.py

This creates:

- `products.json`
- `vectors.tsv`
- `metadata.tsv`

## Step 2 - Visualize Embeddings

Open:

    https://projector.tensorflow.org/

Upload:

1. `vectors.tsv` as the vector file.
2. `metadata.tsv` as the metadata file.

Then search for a category such as `fragrances` or `groceries`, enable color by category, and take a screenshot of a cluster.

## Step 3 - Threshold Test

Run:

    python threshold_test.py

This compares a good query and a bad query:

- Good query: `Nice smelling scent`
- Bad query: `A textbook on quantum physics`

Use the score gap to choose `MIN_SIMILARITY_SCORE` in `utils.py`.

## Step 4 - Search

Run:

    python search.py

Example queries:

    I work from home and my back is killing me, what do you recommend?
    I'm going to a fancy gala tonight and need to make my eyes pop.
    I want to cook a healthy, high-protein dinner tonight.
    I need a nice smelling anniversary gift for my wife.
    Do you sell any lawnmowers or gardening tools?
    I want to buy a luxury boat.
    Do you have any vegan cat food?

The app prints both the vector similarity score and the rerank score.

## Submission Evidence

The submission document should include:

1. GitHub URL for `labs/lab-06/`.
2. TensorFlow Embedding Projector screenshot showing a product cluster.
3. Threshold analysis with good-match score, bad-match score, and chosen threshold.
4. Terminal output showing one successful search.
5. Terminal output showing one no-results search.
6. Reflection on context engineering, semantic search, and reranking.