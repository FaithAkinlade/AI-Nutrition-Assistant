# recommend.py

import ast
import os
import pickle
import sys
import numpy as np
import pandas as pd
from sklearn.metrics.pairwise import cosine_similarity
from dotenv import load_dotenv

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import perishability

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
SIMILARITY_WEIGHT_WITH_PERISH = 0.2
COVERAGE_WEIGHT_WITH_PERISH = 0.3
PERISHABILITY_WEIGHT = 0.5


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
def recommend_recipes(ingredients_list, preference=None, tastes=None, top_n=5, use_first=None):
    # 1. Point to the existing global dataframe (memory efficient)
    filtered_df = df

    # 2. Apply Dietary Filter
    if preference and preference != "None":
        filtered_df = filter_by_preference(filtered_df, preference)

    # 3. Apply Taste Filter (Directly on the 'tastes' column)
    if tastes and 'tastes' in filtered_df.columns:
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
    recipe_blobs = filtered_df['ingredients'].apply(
        lambda r: " ".join(_parse_ingredient_list(r))
    )
    if total_user:
        matched_counts = recipe_blobs.apply(
            lambda blob: _matched_count(user_ings_lower, blob)
        ).to_numpy()
        coverage = matched_counts / total_user
    else:
        matched_counts = np.zeros(len(filtered_df), dtype=int)
        coverage = np.zeros(len(filtered_df))

    if use_first is None:
        perish_items = perishability.suggest_use_first(ingredients_list)
    else:
        perish_items = [u for u in use_first if u and u.strip()]
    perish_items_lower = [p.strip().lower() for p in perish_items]

    if perish_items_lower:
        perish_match = recipe_blobs.apply(
            lambda blob: perishability.perishability_match_count(perish_items_lower, blob)
        ).to_numpy()
        perish_coverage = perish_match / len(perish_items_lower)
        final_scores = (
            SIMILARITY_WEIGHT_WITH_PERISH * similarities
            + COVERAGE_WEIGHT_WITH_PERISH * coverage
            + PERISHABILITY_WEIGHT * perish_coverage
        )
    else:
        perish_match = np.zeros(len(filtered_df), dtype=int)
        perish_coverage = np.zeros(len(filtered_df))
        final_scores = (1 - COVERAGE_WEIGHT) * similarities + COVERAGE_WEIGHT * coverage

    # 11. Get indices of top N highest blended scores (over-fetch to allow dedup)
    over_fetch = min(len(filtered_df), max(top_n * 10, top_n + 20))
    candidate_indices = final_scores.argsort()[-over_fetch:][::-1]

    candidates = filtered_df.iloc[candidate_indices].copy()
    candidates['matched_count'] = matched_counts[candidate_indices]
    candidates['total_user_ingredients'] = total_user
    candidates['coverage'] = coverage[candidate_indices]
    candidates['perish_matched'] = perish_match[candidate_indices]
    candidates['perish_total'] = len(perish_items_lower)
    candidates['perish_coverage'] = perish_coverage[candidate_indices]
    candidates['use_first_items'] = [list(perish_items)] * len(candidates)
    candidates['missing_ingredients'] = candidates['ingredients'].apply(
        lambda r: _missing_ingredients(user_ings_lower, r)
    )

    results = candidates.drop_duplicates(subset=['recipe_title']).head(top_n)
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
            pm = int(row.get('perish_matched', 0))
            pt = int(row.get('perish_total', 0))
            print(f"{i}. {row['recipe_title']}  (uses {matched}/{total} of your ingredients)")
            if pt:
                print(f"   Use-first: consumes {pm}/{pt} perishables")
            print(f"Ingredients: {row['ingredients']}")
            if missing:
                print(f"You'd need: {', '.join(missing)}")
            print(f"Steps: {row['directions']}")
            print("-" * 50)
