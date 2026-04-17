# recommend.py

import os
import pickle
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
# Step 3: Recommendation function
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

    # 9. Get indices of top N most similar recipes (highest scores first)
    actual_top_n = min(len(filtered_df), top_n)
    top_indices = similarities.argsort()[-actual_top_n:][::-1]

    # Return the top matching recipes from the filtered dataframe
    return filtered_df.iloc[top_indices]


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
