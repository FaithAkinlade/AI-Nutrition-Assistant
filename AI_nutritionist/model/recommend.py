# recommend.py

import ast
import os
import pickle
import numpy as np
import pandas as pd
from sklearn.metrics.pairwise import cosine_similarity
from dotenv import load_dotenv

load_dotenv()

# -------------------------------
# Step 1: Load saved files
# -------------------------------
MODEL_DIR = os.environ["MODEL_DIR"]

model_path = os.path.join(MODEL_DIR, 'nn_model.pkl')   # not used but kept
vectorizer_path = os.path.join(MODEL_DIR, 'tfidf_vectorizer.pkl')
data_path = os.path.join(MODEL_DIR, 'recipes.pkl')

with open(vectorizer_path, 'rb') as f:
    vectorizer = pickle.load(f)

df = pd.read_pickle(data_path)

print("✅ Vectorizer and data loaded!")


# -------------------------------
# Step 2: Dietary filtering
# -------------------------------
def filter_by_preference(df, preference):
    if preference == "vegan":
        return df[df['is_vegan'] == 1]
    elif preference == "vegetarian":
        return df[df['is_vegetarian'] == 1]
    elif preference == "gluten_free":
        return df[df['is_gluten_free'] == 1]
    elif preference == "dairy_free":
        return df[df['is_dairy_free'] == 1]
    else:
        return df


# -------------------------------
# Step 3: Use-it-up coverage scoring
# -------------------------------
# Blends ingredient coverage with cosine similarity so recipes that consume
# more of what the user already has rank higher, reducing household food waste.
COVERAGE_WEIGHT = 0.5


def _parse_raw_ingredients(raw):
    """Parse a stringified ingredient list, preserving original case for display."""
    try:
        parsed = ast.literal_eval(raw) if isinstance(raw, str) else raw
    except (ValueError, SyntaxError):
        return [str(raw)] if raw else []
    if isinstance(parsed, list):
        return [str(x) for x in parsed]
    return [str(parsed)]


def _parse_ingredient_list(raw):
    return [s.lower() for s in _parse_raw_ingredients(raw)]


def _matched_count(user_ingredients_lower, recipe_blob):
    return sum(1 for ing in user_ingredients_lower if ing and ing in recipe_blob)


def _missing_ingredients(user_ingredients_lower, raw_ingredients):
    """Recipe items that don't match any of the user's ingredients (display strings)."""
    items = _parse_raw_ingredients(raw_ingredients)
    user_ings = [u for u in user_ingredients_lower if u]
    return [
        item for item in items
        if not any(u in item.lower() for u in user_ings)
    ]


# -------------------------------
# Step 4: Recommendation function
# -------------------------------
def recommend_recipes(ingredients_list, preference=None, tastes=None, top_n=5):
    # 1. Point to the existing global dataframe (memory efficient)
    filtered_df = df

    # 2. Apply Dietary Filter
    if preference and preference != "None":
        filtered_df = filter_by_preference(filtered_df, preference)

    # 3. Apply Taste Filter (Directly on the 'tastes' column)
    if tastes:
        for taste in tastes:
            filtered_df = filtered_df[filtered_df['tastes'].str.contains(taste, case=False, na=False)]

    # 4. Return early if no matches
    if filtered_df.empty:
        return []

    # 5. Prepare the user's search query
    query = " ".join(ingredients_list[:10])

    # 6. Convert the user query into a TF-IDF vector
    query_vec = vectorizer.transform([query])

    # 7. Convert all candidate recipes into TF-IDF vectors
    filtered_matrix = vectorizer.transform(filtered_df['combined_text'])

    # 8. Compute cosine similarity between query and all recipes
    similarities = cosine_similarity(query_vec, filtered_matrix).flatten()

    # 9. Compute ingredient coverage per recipe (use-it-up score).
    user_ings_lower = [i.strip().lower() for i in ingredients_list if i and i.strip()]
    total_user = len(user_ings_lower)
    if total_user:
        recipe_blobs = filtered_df['ingredients'].apply(
            lambda r: " ".join(_parse_ingredient_list(r))
        )
        matched_counts = recipe_blobs.apply(
            lambda blob: _matched_count(user_ings_lower, blob)
        ).to_numpy()
        coverage = matched_counts / total_user
    else:
        matched_counts = np.zeros(len(filtered_df), dtype=int)
        coverage = np.zeros(len(filtered_df))

    # 10. Blend similarity with coverage so recipes that finish more of the
    #     user's ingredients are preferred over slightly-better text matches.
    final_scores = (1 - COVERAGE_WEIGHT) * similarities + COVERAGE_WEIGHT * coverage

    # 11. Get indices of top N highest blended scores
    actual_top_n = min(len(filtered_df), top_n)
    top_indices = final_scores.argsort()[-actual_top_n:][::-1]

    results = filtered_df.iloc[top_indices].copy()
    results['matched_count'] = matched_counts[top_indices]
    results['total_user_ingredients'] = total_user
    results['coverage'] = coverage[top_indices]
    results['missing_ingredients'] = results['ingredients'].apply(
        lambda r: _missing_ingredients(user_ings_lower, r)
    )
    return results


# -------------------------------
# Step 5: Test locally
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
            matched = int(row.get('matched_count', 0))
            total = int(row.get('total_user_ingredients', len(user_ingredients)))
            missing = row.get('missing_ingredients', [])
            print(f"{i}. {row['recipe_title']}  (uses {matched}/{total} of your ingredients)")
            print(f"Ingredients: {row['ingredients']}")
            if missing:
                print(f"You'd need: {', '.join(missing)}")
            print(f"Steps: {row['directions']}")
            print("-" * 50)
