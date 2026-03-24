from fastapi import FastAPI
from typing import List, Optional
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


# -------------------------------
# Recommendation route
# -------------------------------
@app.get("/recommend")
def recommend(
    ingredients: str,
    preference: Optional[str] = None,
    top_n: int = 5
):
    """
    Example:
    /recommend?ingredients=chicken,garlic,onion&preference=vegan
    """

    # Convert string → list
    ingredients_list = [i.strip() for i in ingredients.split(",")]

    results = recommend_recipes(ingredients_list, preference, top_n)

    # Convert dataframe → JSON
    if results is None:
        return {"recipes": []}

    output = []
    for _, row in results.iterrows():
        output.append({
            "recipe_title": row["recipe_title"],
            "ingredients": row["ingredients"],
            "directions": row["directions"]
        })

    return {"recipes": output}