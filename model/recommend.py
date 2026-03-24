# recommend.py

import pickle
import pandas as pd
from sklearn.metrics.pairwise import cosine_similarity

# -------------------------------
# Step 1: Load saved files
# -------------------------------
model_path = r'C:\Users\kalya\AI_nutritionist\model\nn_model.pkl'   # not used but kept
vectorizer_path = r'C:\Users\kalya\AI_nutritionist\model\tfidf_vectorizer.pkl'
data_path = r'C:\Users\kalya\AI_nutritionist\model\recipes.pkl'

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
# Step 3: Recommendation function
# -------------------------------
def recommend_recipes(ingredients_list, preference=None, top_n=5):

    # Convert list → string
    query = " ".join(ingredients_list[:10])

    # Apply dietary filter
    filtered_df = filter_by_preference(df, preference)

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