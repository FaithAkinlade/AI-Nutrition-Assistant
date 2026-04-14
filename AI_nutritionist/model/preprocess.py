# preprocess.py
# Consolidated preprocessing pipeline for recipe data.
# Combines cleaning, feature engineering, and text preparation for ML.

import os
import re
import ast
import pandas as pd
from dotenv import load_dotenv

load_dotenv()

DATA_DIR = os.environ["DATA_DIR"]

INPUT_PATH = os.path.join(DATA_DIR, "recipes_extended.csv")
OUTPUT_PATH = os.path.join(DATA_DIR, "recipes_cleaned.csv")


def safe_literal_eval(x):
    """Safely convert string representations of lists to actual lists."""
    if isinstance(x, list):
        return x
    try:
        return ast.literal_eval(x)
    except (ValueError, SyntaxError):
        return []


def clean_list_column(col, max_items=10):
    """Parse and clean a column containing string-encoded lists."""
    def clean(x):
        items = safe_literal_eval(x) if isinstance(x, str) else x
        if isinstance(items, list):
            cleaned = []
            for item in items[:max_items]:
                item = str(item).lower()
                item = re.sub(r"[^\w\s]", "", item)
                cleaned.append(item.strip())
            return " ".join(cleaned)
        return ""
    return col.apply(clean)


def preprocess():
    # Step 1: Load CSV
    print("Loading dataset...")
    df = pd.read_csv(INPUT_PATH)

    # Step 2: Normalize column names
    print("Normalizing column names...")
    df.columns = df.columns.str.lower().str.strip()

    # Step 3: Drop rows missing critical fields
    df = df.dropna(subset=["ingredients", "recipe_title"])

    # Step 4: Select relevant columns (keep all available)
    desired_columns = [
        'recipe_title',
        'ingredients',
        'directions',
        'description',
        'is_vegan',
        'is_vegetarian',
        'is_gluten_free',
        'is_dairy_free',
        'dietary_profile',
        'tastes',
        'primary_taste',
        'secondary_taste',
        'cuisine_path',
        'est_prep_time_min',
        'est_cook_time_min',
        'difficulty',
    ]
    df = df[[col for col in desired_columns if col in df.columns]]

    # Step 5: Clean ingredients
    print("Cleaning ingredients...")
    df['cleaned_ingredients'] = clean_list_column(df['ingredients'])

    # Step 6: Clean taste columns
    if 'tastes' in df.columns:
        df['cleaned_tastes'] = clean_list_column(df['tastes'])
    else:
        df['cleaned_tastes'] = ""

    # Step 7: Clean description
    if 'description' in df.columns:
        df['description'] = df['description'].fillna("").str.lower()

    # Step 8: Combine text features for ML
    print("Combining text features for ML...")
    df['combined_text'] = (
        df['cleaned_ingredients'] + " " +
        df.get('description', pd.Series([""] * len(df))) + " " +
        df['cleaned_tastes']
    ).str.strip()
    df['combined_text'] = df['combined_text'].fillna("")

    # Step 9: Remove duplicates
    print("Removing duplicates...")
    before = len(df)
    df = df.drop_duplicates(subset=["recipe_title", "cleaned_ingredients"])
    df = df.reset_index(drop=True)
    print(f"Removed {before - len(df)} duplicate rows.")

    # Step 10: Save cleaned CSV
    print("Saving cleaned dataset...")
    df.to_csv(OUTPUT_PATH, index=False)

    print(f"✅ Preprocessing complete! {len(df)} recipes saved to {OUTPUT_PATH}")


if __name__ == "__main__":
    preprocess()
