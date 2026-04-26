"""Tests for the use-it-up coverage ranking added to recommend.py.

The production module loads pickled artifacts at import time, so we patch
those reads with stub data before importing.
"""
import os
import sys
import importlib
from unittest.mock import patch

import numpy as np
import pandas as pd
import pytest
from sklearn.feature_extraction.text import TfidfVectorizer

MODEL_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "model"))
sys.path.insert(0, MODEL_DIR)


def _build_stub_state():
    rows = [
        {
            "recipe_title": "Chicken Garlic Butter Pasta",
            "ingredients": "['chicken', 'garlic', 'butter', 'pasta']",
            "directions": "['cook pasta', 'mix']",
            "combined_text": "chicken garlic butter pasta",
            "tastes": "savory",
            "is_vegan": 0, "is_vegetarian": 0,
            "is_gluten_free": 0, "is_dairy_free": 0,
        },
        {
            "recipe_title": "Garlic Butter Shrimp",
            "ingredients": "['shrimp', 'garlic', 'butter', 'lemon']",
            "directions": "['saute shrimp']",
            "combined_text": "shrimp garlic butter lemon",
            "tastes": "savory",
            "is_vegan": 0, "is_vegetarian": 0,
            "is_gluten_free": 1, "is_dairy_free": 0,
        },
        {
            "recipe_title": "Plain Rice",
            "ingredients": "['rice', 'water', 'salt']",
            "directions": "['boil rice']",
            "combined_text": "rice water salt",
            "tastes": "savory",
            "is_vegan": 1, "is_vegetarian": 1,
            "is_gluten_free": 1, "is_dairy_free": 1,
        },
        {
            "recipe_title": "Chicken Soup",
            "ingredients": "['chicken', 'celery', 'onion']",
            "directions": "['simmer chicken']",
            "combined_text": "chicken celery onion",
            "tastes": "savory",
            "is_vegan": 0, "is_vegetarian": 0,
            "is_gluten_free": 1, "is_dairy_free": 1,
        },
    ]
    df = pd.DataFrame(rows)
    vectorizer = TfidfVectorizer().fit(df["combined_text"])
    return df, vectorizer


@pytest.fixture
def recommend_module(monkeypatch, tmp_path):
    df, vectorizer = _build_stub_state()
    monkeypatch.setenv("MODEL_DIR", str(tmp_path))

    def fake_open(path, mode="r", *a, **kw):
        # The module only opens the vectorizer pickle this way; return a
        # context-manager stub since pickle.load is patched out anyway.
        class _FH:
            def __enter__(self_inner): return self_inner
            def __exit__(self_inner, *exc): return False
            def read(self_inner): return b""
        return _FH()

    with patch("builtins.open", fake_open), \
         patch("pickle.load", return_value=vectorizer), \
         patch("pandas.read_pickle", return_value=df):
        sys.modules.pop("recommend", None)
        module = importlib.import_module("recommend")
    return module


def test_parse_ingredient_list_handles_stringified_list(recommend_module):
    parsed = recommend_module._parse_ingredient_list("['Chicken', 'Garlic']")
    assert parsed == ["chicken", "garlic"]


def test_parse_ingredient_list_handles_garbage(recommend_module):
    assert recommend_module._parse_ingredient_list("not a list") == ["not a list"]
    assert recommend_module._parse_ingredient_list("") == []


def test_matched_count_counts_substring_hits(recommend_module):
    blob = "chicken garlic butter pasta"
    assert recommend_module._matched_count(["chicken", "garlic", "rice"], blob) == 2


def test_recommend_returns_coverage_columns(recommend_module):
    out = recommend_module.recommend_recipes(["chicken", "garlic", "butter"], top_n=4)
    assert {"matched_count", "total_user_ingredients", "coverage"} <= set(out.columns)
    assert (out["total_user_ingredients"] == 3).all()


def test_recommend_ranks_high_coverage_above_low_coverage(recommend_module):
    out = recommend_module.recommend_recipes(["chicken", "garlic", "butter"], top_n=4)
    titles = list(out["recipe_title"])
    # All three of chicken/garlic/butter appear in "Chicken Garlic Butter Pasta",
    # so it must rank above "Plain Rice" (zero overlap).
    assert titles.index("Chicken Garlic Butter Pasta") < titles.index("Plain Rice")


def test_recommend_top_result_has_full_coverage(recommend_module):
    out = recommend_module.recommend_recipes(["chicken", "garlic", "butter"], top_n=1)
    assert int(out.iloc[0]["matched_count"]) == 3
    assert float(out.iloc[0]["coverage"]) == pytest.approx(1.0)


def test_recommend_empty_ingredients_yields_zero_coverage(recommend_module):
    out = recommend_module.recommend_recipes([], top_n=2)
    assert (out["matched_count"] == 0).all()
    assert (out["coverage"] == 0).all()
    assert (out["total_user_ingredients"] == 0).all()


def test_recommend_dietary_filter_still_applies(recommend_module):
    out = recommend_module.recommend_recipes(["rice"], preference="vegan", top_n=4)
    assert all(t == "Plain Rice" for t in out["recipe_title"])
