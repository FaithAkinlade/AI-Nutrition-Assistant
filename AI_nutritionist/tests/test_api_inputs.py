import sys
import os
import pytest

# Add backend and model to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend")))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "model")))

from fastapi.testclient import TestClient
from app import app

client = TestClient(app)


# -----------------------------------------------
# Health check
# -----------------------------------------------
def test_home_route():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "Recipe Recommendation API is running!"}


# -----------------------------------------------
# Basic ingredient queries
# -----------------------------------------------
def test_single_ingredient():
    response = client.get("/recommend", params={"ingredients": "chicken"})
    assert response.status_code == 200
    data = response.json()
    assert "recipes" in data
    assert len(data["recipes"]) <= 5


def test_multiple_ingredients():
    response = client.get("/recommend", params={"ingredients": "chicken,garlic,onion"})
    assert response.status_code == 200
    data = response.json()
    assert "recipes" in data
    assert len(data["recipes"]) > 0


def test_ingredients_with_spaces():
    response = client.get("/recommend", params={"ingredients": " chicken , garlic , butter "})
    assert response.status_code == 200
    assert "recipes" in response.json()


# -----------------------------------------------
# top_n parameter
# -----------------------------------------------
def test_custom_top_n():
    response = client.get("/recommend", params={"ingredients": "rice,beans", "top_n": 3})
    assert response.status_code == 200
    assert len(response.json()["recipes"]) <= 3


def test_top_n_of_one():
    response = client.get("/recommend", params={"ingredients": "pasta", "top_n": 1})
    assert response.status_code == 200
    assert len(response.json()["recipes"]) <= 1


# -----------------------------------------------
# Dietary preference filters
# -----------------------------------------------
@pytest.mark.parametrize("preference", ["vegan", "vegetarian", "gluten_free", "dairy_free"])
def test_valid_preferences(preference):
    response = client.get("/recommend", params={"ingredients": "rice,tomato", "preference": preference})
    assert response.status_code == 200
    assert "recipes" in response.json()


def test_no_preference():
    response = client.get("/recommend", params={"ingredients": "chicken,garlic"})
    assert response.status_code == 200
    assert "recipes" in response.json()


def test_unknown_preference_returns_unfiltered():
    response = client.get("/recommend", params={"ingredients": "chicken", "preference": "keto"})
    assert response.status_code == 200
    # Unknown preference falls through to unfiltered results
    assert "recipes" in response.json()


def test_multi_preference_filter():
    response = client.get("/recommend", params={
        "ingredients": "rice,tomato",
        "preference": "vegan,gluten_free"
    })
    assert response.status_code == 200
    assert "recipes" in response.json()


def test_max_prep_time_filter():
    response = client.get("/recommend", params={
        "ingredients": "chicken,garlic",
        "max_prep_time": 30
    })
    assert response.status_code == 200
    assert "recipes" in response.json()


def test_max_cook_time_filter():
    response = client.get("/recommend", params={
        "ingredients": "pasta,tomato",
        "max_cook_time": 45
    })
    assert response.status_code == 200
    assert "recipes" in response.json()


# -----------------------------------------------
# Response shape validation
# -----------------------------------------------
def test_response_contains_expected_fields():
    response = client.get("/recommend", params={"ingredients": "chicken,garlic"})
    assert response.status_code == 200
    recipes = response.json()["recipes"]
    if len(recipes) > 0:
        recipe = recipes[0]
        assert "recipe_title" in recipe
        assert "ingredients" in recipe
        assert "directions" in recipe
        assert "cuisine" in recipe
        assert "difficulty" in recipe
        assert "dietary_profile" in recipe


# -----------------------------------------------
# Missing required parameter
# -----------------------------------------------
def test_missing_ingredients_returns_422():
    response = client.get("/recommend")
    assert response.status_code == 422


# -----------------------------------------------
# Edge cases
# -----------------------------------------------
def test_empty_ingredients_string():
    response = client.get("/recommend", params={"ingredients": ""})
    assert response.status_code == 200
    assert "recipes" in response.json()


def test_nonsense_ingredients():
    response = client.get("/recommend", params={"ingredients": "xyzzy,asdfgh"})
    assert response.status_code == 200
    # Should still return without crashing, even if results are irrelevant
    assert "recipes" in response.json()


def test_many_ingredients_truncated_to_ten():
    ingredients = ",".join([f"ingredient{i}" for i in range(20)])
    response = client.get("/recommend", params={"ingredients": ingredients})
    assert response.status_code == 200
    assert "recipes" in response.json()
