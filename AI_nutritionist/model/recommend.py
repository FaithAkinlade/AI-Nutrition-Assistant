# recommend.py

import os
import pickle
import functools
import pandas as pd
from sklearn.metrics.pairwise import cosine_similarity
from dotenv import load_dotenv

load_dotenv()

MODEL_DIR = os.environ["MODEL_DIR"]


# -------------------------------
# Step 1: Load saved files (cached)
# -------------------------------
@functools.lru_cache(maxsize=1)
def _load_model():
    vectorizer_path = os.path.join(MODEL_DIR, 'tfidf_vectorizer.pkl')
    data_path = os.path.join(MODEL_DIR, 'recipes.pkl')

    with open(vectorizer_path, 'rb') as f:
        vectorizer = pickle.load(f)

    df = pd.read_pickle(data_path)

    print("✅ Vectorizer and data loaded!")
    return vectorizer, df


# -------------------------------
# Step 2: Dietary filtering
# -------------------------------
DIETARY_COLUMNS = {
    "vegan": "is_vegan",
    "vegetarian": "is_vegetarian",
    "gluten_free": "is_gluten_free",
    "dairy_free": "is_dairy_free",
}


def filter_by_preferences(df, preferences):
    """Filter by one or more dietary preferences."""
    if not preferences:
        return df
    for pref in preferences:
        col = DIETARY_COLUMNS.get(pref)
        if col and col in df.columns:
            df = df[df[col] == 1]
    return df


# -------------------------------
# Step 3: Recommendation function
# -------------------------------
def recommend_recipes(ingredients_list, preference=None, top_n=5,
                      max_prep_time=None, max_cook_time=None):
    vectorizer, df = _load_model()

    # Convert list → string
    query = " ".join(ingredients_list[:10])

    # Normalize preference to a list for multi-filter support
    if isinstance(preference, str):
        preferences = [p.strip() for p in preference.split(",") if p.strip()]
    elif isinstance(preference, list):
        preferences = preference
    else:
        preferences = []

    # Apply dietary filters
    filtered_df = filter_by_preferences(df, preferences)

    # Apply time-based filters
    if max_prep_time is not None and 'est_prep_time_min' in filtered_df.columns:
        filtered_df = filtered_df[filtered_df['est_prep_time_min'] <= max_prep_time]
    if max_cook_time is not None and 'est_cook_time_min' in filtered_df.columns:
        filtered_df = filtered_df[filtered_df['est_cook_time_min'] <= max_cook_time]

    if len(filtered_df) == 0:
        return []

    # Transform query
    query_vec = vectorizer.transform([query])

    # Transform filtered data
    filtered_matrix = vectorizer.transform(filtered_df['combined_text'])

    # Compute similarity
    similarities = cosine_similarity(query_vec, filtered_matrix)

    # Get top matches
    top_indices = similarities.argsort()[0][-top_n:][::-1]

    results = filtered_df.iloc[top_indices]

    return results


# -------------------------------
# Step 4: Test locally
# -------------------------------
if __name__ == "__main__":
    user_ingredients = ["chicken", "garlic", "butter"]
    preference = "gluten_free"

    results = recommend_recipes(user_ingredients, preference)

    print("\n🍽️ Recommended Recipes:\n")

    if len(results) == 0:
        print("No recipes found.")
    else:
        for i, (_, row) in enumerate(results.iterrows(), 1):
            print(f"{i}. {row['recipe_title']}")
            print(f"Ingredients: {row['ingredients']}")
            print(f"Steps: {row['directions']}")
            print("-" * 50)