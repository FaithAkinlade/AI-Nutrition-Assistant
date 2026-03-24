import os
import pandas as pd
import re
import ast
from sklearn.preprocessing import MultiLabelBinarizer, MinMaxScaler
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.model_selection import train_test_split
import pickle
from dotenv import load_dotenv

load_dotenv()

DATA_DIR = os.environ["DATA_DIR"]

# Load data
df = pd.read_csv(os.path.join(DATA_DIR, "recipes_extended.csv"))

print(df.head())
print(df.isnull().sum())

# Drop critical missing values
df = df.dropna(subset=["ingredients_canonical", "recipe_title"])

# Convert string → list safely
def safe_literal_eval(x):
    try:
        return ast.literal_eval(x)
    except:
        return []

df["ingredients_canonical"] = df["ingredients_canonical"].apply(safe_literal_eval)
df["cuisine_list"] = df["cuisine_list"].apply(safe_literal_eval)
df["course_list"] = df["course_list"].apply(safe_literal_eval)
df["tastes"] = df["tastes"].apply(safe_literal_eval)

# Clean ingredient text
def clean_ingredients(ingredients):
    cleaned = []
    for item in ingredients:
        item = str(item).lower()
        item = re.sub(r"[^\w\s]", "", item)
        cleaned.append(item)
    return cleaned
df["ingredients_clean"] = df["ingredients_canonical"].apply(clean_ingredients)

# Create hashable version of ingredients
df["ingredients_str"] = df["ingredients_canonical"].apply(
    lambda x: " ".join([str(i) for i in x]) if isinstance(x, list) else ""
)

# Removing duplicates
df = df.drop_duplicates(subset=["recipe_title", "ingredients_str"])

# Drop helper column
df = df.drop(columns=["ingredients_str"])

# Reset index after drops
df = df.reset_index(drop=True)

# Safe join function
def safe_join(lst):
    if not isinstance(lst, list):
        return ""
    return " ".join([str(i) for i in lst])

# Combine features
df["combined_features"] = (
    df["ingredients_clean"].apply(safe_join) + " " +
    df["cuisine_list"].apply(safe_join) + " " +
    df["tastes"].apply(safe_join)
)

# Multi-label encoding
mlb_cuisine = MultiLabelBinarizer()
cuisine_encoded = mlb_cuisine.fit_transform(df["cuisine_list"])

mlb_taste = MultiLabelBinarizer()
taste_encoded = mlb_taste.fit_transform(df["tastes"])

# TF-IDF (USE combined features)
tfidf = TfidfVectorizer(stop_words='english')

ingredient_matrix = tfidf.fit_transform(df["combined_features"])

# Normalize numeric features
scaler = MinMaxScaler()

df[["est_prep_time_min", "est_cook_time_min", "healthiness_score"]] = scaler.fit_transform(
    df[["est_prep_time_min", "est_cook_time_min", "healthiness_score"]]
)

# Encode difficulty safely
df["difficulty"] = df["difficulty"].map({
    "easy": 0,
    "medium": 1,
    "hard": 2
}).fillna(1)

# Create dietary filter column
diet_cols = [
    "is_vegan", "is_vegetarian", "is_halal",
    "is_kosher", "is_nut_free", "is_dairy_free", "is_gluten_free"
]

df["dietary_tags"] = df[diet_cols].apply(
    lambda row: [col for col in diet_cols if row[col] == 1],
    axis=1
)

# Sanity checks
print("Sample cleaned ingredients:", df["ingredients_clean"].iloc[0])
print("Sample cuisine:", df["cuisine_list"].iloc[0])
print("Dataset size:", len(df))

# Train-test split
train_df, test_df = train_test_split(df, test_size=0.2, random_state=42)

print("Train size:", len(train_df))
print("Test size:", len(test_df))

# Saving data for later use
pickle.dump(tfidf, open("tfidf.pkl", "wb"))
pickle.dump(ingredient_matrix, open("ingredient_matrix.pkl", "wb"))
pickle.dump(mlb_cuisine, open("mlb_cuisine.pkl", "wb"))
pickle.dump(mlb_taste, open("mlb_taste.pkl", "wb"))

df.to_csv("cleaned_recipes.csv", index=False)
