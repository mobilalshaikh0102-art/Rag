"""
Session 3 - Vector DB & Retrieval
Tasks 1-5

Install dependencies before running:
    pip install faiss-cpu chromadb numpy

Note: chromadb will create a local sqlite folder ("./chroma_db") the first
time you run it — that's expected, no internet needed after install.
"""

import numpy as np


# ===========================================================================
# TASK 1: FAISS index with 5 song embeddings (random 4-D vectors)
# ===========================================================================
def task1_faiss_song_index():
    import faiss

    print("=" * 70)
    print("TASK 1: FAISS index with 5 song embeddings (4-D)")
    print("=" * 70)

    np.random.seed(42)
    song_names = ["Blinding Lights", "Shape of You", "Levitating", "Bad Guy", "Someone Like You"]
    song_embeddings = np.random.rand(5, 4).astype("float32")

    dimension = 4
    index = faiss.IndexFlatL2(dimension)  # L2 (Euclidean) distance index
    index.add(song_embeddings)

    print("Songs indexed:", song_names)
    print("Embeddings:\n", song_embeddings)
    print(f"\nIndex size (index.ntotal): {index.ntotal}")
    print(f"Vector dimension (index.d): {index.d}")

    return index, song_names, song_embeddings


# ===========================================================================
# TASK 2: ChromaDB with 5 restaurant embeddings (random 3-D vectors)
# ===========================================================================
def task2_chromadb_restaurants():
    import chromadb

    print("\n" + "=" * 70)
    print("TASK 2: ChromaDB restaurant similarity search (3-D)")
    print("=" * 70)

    np.random.seed(1)
    restaurant_names = ["Barbeque Nation", "Domino's", "Pizza Hut", "Haldiram's", "Wow! Momo"]
    restaurant_embeddings = np.random.rand(5, 3).tolist()

    client = chromadb.Client()  # in-memory client, no persistence needed for this demo
    # get_or_create avoids an error if this script is re-run in the same session
    collection = client.get_or_create_collection(name="restaurants")

    collection.add(
        ids=[f"rest_{i}" for i in range(len(restaurant_names))],
        embeddings=restaurant_embeddings,
        documents=restaurant_names,
    )

    query_vector = np.random.rand(3).tolist()
    print("Query vector:", query_vector)

    results = collection.query(query_embeddings=[query_vector], n_results=1)

    best_match = results["documents"][0][0]
    best_distance = results["distances"][0][0]
    print(f"\nMost similar restaurant: {best_match}")
    print(f"Distance score: {best_distance:.4f}")

    return collection


# ===========================================================================
# TASK 3: FAISS-based top-2 movie search from a text query
# ===========================================================================
def embed_text(text, dimension=8, seed_from_text=True):
    """
    Placeholder embedding function. Deterministically turns text into a
    vector using a hash-based seed so the same text always maps to the same
    vector (stands in for a real embedding model like sentence-transformers).
    """
    if seed_from_text:
        seed = abs(hash(text)) % (2**32)
        rng = np.random.default_rng(seed)
    else:
        rng = np.random.default_rng()
    return rng.random(dimension).astype("float32")


def find_top_k_similar_movies(user_query, movie_titles, movie_embeddings, k=2):
    """
    Takes a user's search query string and a list of movie embeddings,
    builds a FAISS index, and returns the top-k most similar movie titles.
    """
    import faiss

    dimension = movie_embeddings.shape[1]
    index = faiss.IndexFlatL2(dimension)
    index.add(movie_embeddings)

    query_vector = embed_text(user_query, dimension=dimension).reshape(1, -1)
    distances, indices = index.search(query_vector, k)

    top_movies = [(movie_titles[idx], float(distances[0][i])) for i, idx in enumerate(indices[0])]
    return top_movies


def task3_movie_search_demo():
    print("\n" + "=" * 70)
    print("TASK 3: FAISS top-2 movie search from a text query")
    print("=" * 70)

    movie_titles = ["Mad Max: Fury Road", "The Notebook", "John Wick", "La La Land", "Die Hard"]
    dimension = 8
    # In a real system these would come from an embedding model run over each
    # movie's description; here we use the same deterministic placeholder
    # embedder for consistency with the query embedding.
    movie_embeddings = np.array([embed_text(title, dimension) for title in movie_titles])

    user_query = "action movie"
    top_movies = find_top_k_similar_movies(user_query, movie_titles, movie_embeddings, k=2)

    print(f"Query: {user_query!r}")
    print("Top 2 most similar movies:")
    for rank, (title, dist) in enumerate(top_movies, 1):
        print(f"  {rank}. {title} (distance: {dist:.4f})")


# ===========================================================================
# TASK 4: ChromaDB - Instagram captions similarity search
# ===========================================================================
def task4_instagram_captions():
    import chromadb

    print("\n" + "=" * 70)
    print("TASK 4: ChromaDB Instagram caption similarity search")
    print("=" * 70)

    captions = [
        "Weekend getaway with friends",
        "Chasing sunsets and good vibes",
        "Coffee, calm, and Sunday mornings",
        "Grinding through Monday like a boss",
        "Beach hair, don't care",
        "Late night city lights",
        "Brunch and blessings",
    ]

    np.random.seed(7)
    dimension = 5
    caption_embeddings = np.random.rand(len(captions), dimension).tolist()

    client = chromadb.Client()
    collection = client.get_or_create_collection(name="ig_captions")
    collection.add(
        ids=[f"cap_{i}" for i in range(len(captions))],
        embeddings=caption_embeddings,
        documents=captions,
    )

    # Simulate the query "Weekend vibes" -> in a real pipeline this would be
    # passed through the same embedding model used above; here we use a
    # random vector as the hint suggests.
    query_text = "Weekend vibes"
    query_vector = np.random.rand(dimension).tolist()

    results = collection.query(query_embeddings=[query_vector], n_results=3)

    print(f"Query: {query_text!r}")
    print("Top 3 most similar captions:")
    for doc, dist in zip(results["documents"][0], results["distances"][0]):
        print(f"  - {doc}  (distance: {dist:.4f})")

    print(
        "\nHow retrieval works here: ChromaDB compares the query's vector "
        "against every stored caption vector and returns the captions whose "
        "vectors sit closest to it in embedding space, i.e. the ones "
        "'meaning' something similar to the query."
    )


# ===========================================================================
# TASK 5: FAISS - Flipkart-style product search
# ===========================================================================
def task5_flipkart_products():
    import faiss

    print("\n" + "=" * 70)
    print("TASK 5: FAISS Flipkart-style product similarity search")
    print("=" * 70)

    # --- ChatGPT prompt used to generate these (paste this in your submission) ---
    # Prompt: "Generate 5 short Flipkart-style product descriptions for
    # different electronics/accessories, one line each."
    product_descriptions = [
        "boAt Rockerz 450 Wireless Bluetooth Headphones with 15H Playback",
        "Samsung Galaxy M14 5G Smartphone, 128GB Storage, 6000mAh Battery",
        "Prestige Electric Kettle 1.5L with Auto Shut-Off, Stainless Steel",
        "HP 15s Laptop, Intel i5 12th Gen, 8GB RAM, 512GB SSD",
        "Fastrack Reflex Smartwatch with Heart Rate Monitor and SpO2 Tracking",
    ]

    dimension = 10
    # Placeholder embeddings — swap embed_text() for a real embedding API
    # (e.g. OpenAI, sentence-transformers) to use actual semantic vectors.
    product_embeddings = np.array(
        [embed_text(desc, dimension) for desc in product_descriptions]
    )

    index = faiss.IndexFlatL2(dimension)
    index.add(product_embeddings)

    query = "wireless headphones"
    query_vector = embed_text(query, dimension).reshape(1, -1)

    k = 1
    distances, indices = index.search(query_vector, k)

    print("Product catalog:")
    for desc in product_descriptions:
        print(f"  - {desc}")

    print(f"\nQuery: {query!r}")
    print(f"Most similar product: {product_descriptions[indices[0][0]]}")
    print(f"Distance: {distances[0][0]:.4f}")


# ===========================================================================
if __name__ == "__main__":
    try:
        task1_faiss_song_index()
    except ImportError as e:
        print(f"\n[!] Task 1 skipped — missing dependency: {e}")
        print("Install with: pip install faiss-cpu")

    try:
        task2_chromadb_restaurants()
    except ImportError as e:
        print(f"\n[!] Task 2 skipped — missing dependency: {e}")
        print("Install with: pip install chromadb")

    try:
        task3_movie_search_demo()
    except ImportError as e:
        print(f"\n[!] Task 3 skipped — missing dependency: {e}")
        print("Install with: pip install faiss-cpu")

    try:
        task4_instagram_captions()
    except ImportError as e:
        print(f"\n[!] Task 4 skipped — missing dependency: {e}")
        print("Install with: pip install chromadb")

    try:
        task5_flipkart_products()
    except ImportError as e:
        print(f"\n[!] Task 5 skipped — missing dependency: {e}")
        print("Install with: pip install faiss-cpu")
