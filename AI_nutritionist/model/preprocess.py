# preprocess.py

import os
import pandas as pd
import ast
from dotenv import load_dotenv

load_dotenv()

DATA_DIR = os.environ["DATA_DIR"]

INPUT_PATH = os.path.join(DATA_DIR, "recipes_extended.csv")
OUTPUT_PATH = os.path.join(DATA_DIR, "recipes_cleaned.csv")


# Step 4: Clean ingredients and tags
def clean_list_column(col):
    def clean(x):
        if isinstance(x, str):
            try:
                x = ast.literal_eval(x)  # convert string list → actual list
            except:
                return ""
        if isinstance(x, list):
            return ' '.join([str(i).lower() for i in x[:10]])  # max 10 ingredients
        return ""
    return col.apply(clean)


def preprocess():
    # Step 1: Load CSV
    print("Loading dataset...")
    df = pd.read_csv(INPUT_PATH)

    # Step 2: Normalize column names
    print("Normalizing column names...")
    df.columns = df.columns.str.lower().str.strip()

    # Step 3: Select relevant columns
    print("Selecting relevant columns...")
    required_columns = [
        'recipe_title',
        'ingredients',
        'directions',
        'description',
        'is_vegan',
        'is_vegetarian',
        'is_gluten_free',
        'is_dairy_free',
        'dietary_profile'
    ]

    # Keep only available columns
    df = df[[col for col in required_columns if col in df.columns]]

    # Step 4: Clean ingredients and tags
    print("Cleaning ingredients...")
    df['cleaned_ingredients'] = clean_list_column(df['ingredients'])

    # Optional: clean description
    if 'description' in df.columns:
        df['description'] = df['description'].fillna("").str.lower()

    # Step 5: Combine for ML
    print("Combining text for ML...")
    df['combined_text'] = (
        df['cleaned_ingredients'] + " " + df.get('description', "")
    )

    df['combined_text'] = df['combined_text'].fillna("")

    # Step 6: Save cleaned CSV
    print("Saving cleaned dataset...")
    df.to_csv(OUTPUT_PATH, index=False)

    print("✅ Preprocessing complete!")
    print(f"Saved to: {OUTPUT_PATH}")


if __name__ == "__main__":
    preprocess()