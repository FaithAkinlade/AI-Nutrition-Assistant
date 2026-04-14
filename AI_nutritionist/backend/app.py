from fastapi import FastAPI
from typing import Optional
import sys
import os

# Add model folder to path
sys.path.append(os.path.abspath("../model"))

from recommend import recommend_recipes

app = FastAPI()


# -------------------------------
# Home route
# -------------------------------
@app.get("/")
def home():
    return {"message": "Recipe Recommendation API is running!"}


# Helper to safely get a value from a row
def _safe_get(row, col, default=""):
    if col in row.index:
        val = row[col]
        if val is None or (isinstance(val, float) and str(val) == "nan"):
            return default
        return val
    return default


# -------------------------------
# Recommendation route
# -------------------------------
@app.get("/recommend")
def recommend(
    ingredients: str,
    preference: Optional[str] = None,
    top_n: int = 5,
    max_prep_time: Optional[int] = None,
    max_cook_time: Optional[int] = None,
):
    """
    Example:
    /recommend?ingredients=chicken,garlic,onion&preference=vegan,gluten_free&max_prep_time=30
    """

    # Convert string → list
    ingredients_list = [i.strip() for i in ingredients.split(",")]

    results = recommend_recipes(
        ingredients_list, preference, top_n,
        max_prep_time=max_prep_time,
        max_cook_time=max_cook_time,
    )

    # Convert dataframe → JSON
    if results is None or (isinstance(results, list) and len(results) == 0):
        return {"recipes": []}

    output = []
    for _, row in results.iterrows():
        output.append({
            "recipe_title": row["recipe_title"],
            "ingredients": row["ingredients"],
            "directions": row["directions"],
            "cuisine": _safe_get(row, "cuisine_path", ""),
            "difficulty": _safe_get(row, "difficulty", ""),
            "est_prep_time_min": _safe_get(row, "est_prep_time_min", None),
            "est_cook_time_min": _safe_get(row, "est_cook_time_min", None),
            "dietary_profile": _safe_get(row, "dietary_profile", ""),
            "primary_taste": _safe_get(row, "primary_taste", ""),
            "description": _safe_get(row, "description", ""),
        })

    return {"recipes": output}