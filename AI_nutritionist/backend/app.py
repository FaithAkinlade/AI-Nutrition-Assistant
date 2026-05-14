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
    tastes: Optional[str] = None,
    use_first: Optional[str] = None,
    top_n: int = 5
):
    """
    Example:
    /recommend?ingredients=chicken,garlic,onion&preference=vegan&use_first=chicken
    """

    ingredients_list = [i.strip() for i in ingredients.split(",") if i.strip()]
    tastes_list = [t.strip() for t in tastes.split(",")] if tastes else None
    use_first_list = [u.strip() for u in use_first.split(",")] if use_first else None

    results = recommend_recipes(
        ingredients_list,
        preference=preference,
        tastes=tastes_list,
        top_n=top_n,
        use_first=use_first_list,
    )

    # Convert dataframe → JSON
    if results is None or (hasattr(results, "empty") and results.empty) or (isinstance(results, list) and len(results) == 0):
        return {"recipes": []}

    output = []
    for _, row in results.iterrows():
        output.append({
            "recipe_title": row["recipe_title"],
            "ingredients": row["ingredients"],
            "directions": row["directions"],
            "matched_count": int(row.get("matched_count", 0)) if "matched_count" in row else 0,
            "total_user_ingredients": int(row.get("total_user_ingredients", 0)) if "total_user_ingredients" in row else 0,
            "missing_ingredients": list(row.get("missing_ingredients", [])) if "missing_ingredients" in row else [],
            "perish_matched": int(row.get("perish_matched", 0)) if "perish_matched" in row else 0,
            "perish_total": int(row.get("perish_total", 0)) if "perish_total" in row else 0,
        })

    return {"recipes": output}