import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.neighbors import NearestNeighbors
import os
import pickle
from dotenv import load_dotenv

load_dotenv()

MODEL_DIR = os.environ["MODEL_DIR"]
DATA_DIR = os.environ["DATA_DIR"]

# -------------------------------
# Step 1: Load cleaned CSV
# -------------------------------
csv_path = os.path.join(DATA_DIR, "recipes_cleaned_no_dups.csv")

if not os.path.exists(csv_path):
    raise FileNotFoundError(f"{csv_path} does not exist. Run preprocess.py first.")

df = pd.read_csv(csv_path)
print(f"Loaded {len(df)} recipes.")

# -------------------------------
# Step 2: TF-IDF Vectorization
# -------------------------------
# IMPORTANT: use combined_text (not 'combined')
vectorizer = TfidfVectorizer(max_features=5000, stop_words='english')
tfidf_matrix = vectorizer.fit_transform(df['combined_text'])

print("TF-IDF matrix created:", tfidf_matrix.shape)

# -------------------------------
# Step 3: Build Nearest Neighbors model
# -------------------------------
nn_model = NearestNeighbors(n_neighbors=5, metric='cosine')
nn_model.fit(tfidf_matrix)

print("Nearest Neighbors model trained!")

# -------------------------------
# Step 4: Save model & vectorizer
# -------------------------------
model_path = os.path.join(MODEL_DIR, 'nn_model.pkl')
vectorizer_path = os.path.join(MODEL_DIR, 'tfidf_vectorizer.pkl')
data_path = os.path.join(MODEL_DIR, 'recipes.pkl')

with open(model_path, 'wb') as f:
    pickle.dump(nn_model, f)

with open(vectorizer_path, 'wb') as f:
    pickle.dump(vectorizer, f)

# Save dataframe for later use (VERY IMPORTANT)
df.to_pickle(data_path)

print(f"Model saved at {model_path}")
print(f"Vectorizer saved at {vectorizer_path}")
print(f"Data saved at {data_path}")

# -------------------------------
# Step 5: Function to get recommendations
# -------------------------------
def recommend_recipes(query_ingredients, preference=None, top_n=5):
    """
    Input:
        query_ingredients: string of ingredients
        preference: dietary filter (vegan, vegetarian, etc.)
        top_n: number of recipes to return

    Output:
        List of recommended recipes
    """

    # Load saved files
    with open(model_path, 'rb') as f:
        model = pickle.load(f)

    with open(vectorizer_path, 'rb') as f:
        vectorizer_loaded = pickle.load(f)

    df_loaded = pd.read_pickle(data_path)

    # -------------------------------
    # Step 5A: Dietary filtering
    # -------------------------------
    if preference == "vegan":
        df_filtered = df_loaded[df_loaded['is_vegan'] == 1]
    elif preference == "vegetarian":
        df_filtered = df_loaded[df_loaded['is_vegetarian'] == 1]
    elif preference == "gluten_free":
        df_filtered = df_loaded[df_loaded['is_gluten_free'] == 1]
    elif preference == "dairy_free":
        df_filtered = df_loaded[df_loaded['is_dairy_free'] == 1]
    else:
        df_filtered = df_loaded

    if len(df_filtered) == 0:
        return ["No recipes found for this preference"]

    # -------------------------------
    # Step 5B: Transform query
    # -------------------------------
    query_vec = vectorizer_loaded.transform([query_ingredients])

    # -------------------------------
    # Step 5C: Get nearest neighbors
    # -------------------------------
    distances, indices = model.kneighbors(query_vec, n_neighbors=top_n)

    # IMPORTANT: map indices correctly
    recommended = df_loaded.iloc[indices[0]]

    return recommended[['recipe_title', 'ingredients', 'directions']]


# -------------------------------
# Example usage
# -------------------------------
if __name__ == "__main__":
    sample_query = "chicken garlic onion"
    preference = "gluten_free"   # change or set None

    recommendations = recommend_recipes(sample_query, preference)

    print("\nRecommendations for query:", sample_query)
    print("Dietary preference:", preference)

    for i, row in recommendations.iterrows():
        print(f"\n{i+1}. {row['recipe_title']}")
        print(f"Ingredients: {row['ingredients']}")
        print(f"Steps: {row['directions']}")