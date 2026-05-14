import os
import sys
import importlib
from unittest.mock import patch

import pandas as pd
import pytest
from sklearn.feature_extraction.text import TfidfVectorizer

MODEL_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "model"))
sys.path.insert(0, MODEL_DIR)

import perishability


def test_classify_highly_perishable():
    assert perishability.classify("shrimp") == "highly_perishable"
    assert perishability.classify("fresh basil") == "highly_perishable"
    assert perishability.classify("raspberries") == "highly_perishable"


def test_classify_perishable():
    assert perishability.classify("chicken breast") == "perishable"
    assert perishability.classify("ground beef") == "perishable"
    assert perishability.classify("spinach leaves") == "perishable"
    assert perishability.classify("ripe tomatoes") == "perishable"


def test_classify_moderate():
    assert perishability.classify("eggs") == "moderate"
    assert perishability.classify("garlic cloves") == "moderate"
    assert perishability.classify("yellow onion") == "moderate"
    assert perishability.classify("sharp cheddar") == "moderate"


def test_classify_pantry_stable():
    assert perishability.classify("white rice") == "pantry_stable"
    assert perishability.classify("olive oil") == "pantry_stable"
    assert perishability.classify("black beans") == "pantry_stable"
    assert perishability.classify("dried oregano") == "pantry_stable"


def test_classify_unknown_returns_none():
    assert perishability.classify("xyzzy") is None
    assert perishability.classify("") is None
    assert perishability.classify(None) is None


def test_classify_prefers_longest_match():
    assert perishability.classify("ground beef") == "perishable"
    assert perishability.classify("canned tomatoes") == "pantry_stable"
    assert perishability.classify("sweet potato") == "moderate"


def test_classify_is_case_insensitive():
    assert perishability.classify("CHICKEN") == "perishable"
    assert perishability.classify("Olive OIL") == "pantry_stable"


def test_shelf_life_days_matches_tier():
    assert perishability.shelf_life_days("shrimp") == 2
    assert perishability.shelf_life_days("chicken") == 5
    assert perishability.shelf_life_days("garlic") == 14
    assert perishability.shelf_life_days("rice") == 365
    assert perishability.shelf_life_days("zzz unknown zzz") is None


def test_annotate_orders_by_priority():
    items = ["rice", "shrimp", "garlic", "chicken"]
    out = perishability.annotate(items)
    tiers = [a["tier"] for a in out]
    assert tiers == ["highly_perishable", "perishable", "moderate", "pantry_stable"]


def test_annotate_includes_label_and_days():
    out = perishability.annotate(["shrimp"])
    assert out[0]["label"] == "Use within 1-3 days"
    assert out[0]["days"] == 2


def test_suggest_use_first_filters_to_perishable_tiers():
    items = ["rice", "shrimp", "garlic", "chicken", "olive oil"]
    suggested = perishability.suggest_use_first(items)
    assert "shrimp" in suggested
    assert "chicken" in suggested
    assert "rice" not in suggested
    assert "olive oil" not in suggested
    assert "garlic" not in suggested
    assert suggested.index("shrimp") < suggested.index("chicken")


def test_suggest_use_first_handles_empty():
    assert perishability.suggest_use_first([]) == []
    assert perishability.suggest_use_first(None) == []


def test_perishability_coverage_fraction():
    blob = "chicken garlic butter pasta"
    assert perishability.perishability_coverage(["chicken", "shrimp"], blob) == 0.5
    assert perishability.perishability_coverage(["chicken"], blob) == 1.0
    assert perishability.perishability_coverage(["shrimp"], blob) == 0.0


def test_perishability_coverage_empty_inputs():
    assert perishability.perishability_coverage([], "chicken garlic") == 0.0
    assert perishability.perishability_coverage(["chicken"], "") == 0.0
    assert perishability.perishability_coverage(["chicken"], None) == 0.0


def test_perishability_match_count():
    blob = "shrimp garlic butter lemon"
    assert perishability.perishability_match_count(["shrimp", "chicken"], blob) == 1
    assert perishability.perishability_match_count(["shrimp", "garlic"], blob) == 2
    assert perishability.perishability_match_count([], blob) == 0


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
            "recipe_title": "Shrimp Scampi",
            "ingredients": "['shrimp', 'garlic', 'butter', 'lemon']",
            "directions": "['saute shrimp']",
            "combined_text": "shrimp garlic butter lemon",
            "tastes": "savory",
            "is_vegan": 0, "is_vegetarian": 0,
            "is_gluten_free": 1, "is_dairy_free": 0,
        },
        {
            "recipe_title": "Pantry Pasta",
            "ingredients": "['pasta', 'olive oil', 'garlic', 'salt']",
            "directions": "['boil pasta']",
            "combined_text": "pasta olive oil garlic salt",
            "tastes": "savory",
            "is_vegan": 1, "is_vegetarian": 1,
            "is_gluten_free": 0, "is_dairy_free": 1,
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


def test_use_first_boost_promotes_perishable_consuming_recipe(recommend_module):
    out = recommend_module.recommend_recipes(
        ["shrimp", "garlic", "pasta", "olive oil", "salt"],
        use_first=["shrimp"],
        top_n=4,
    )
    titles = list(out["recipe_title"])
    assert titles[0] == "Shrimp Scampi"


def test_no_use_first_falls_back_to_coverage_blend(recommend_module):
    out = recommend_module.recommend_recipes(
        ["shrimp", "garlic", "pasta", "olive oil", "salt"],
        use_first=[],
        top_n=4,
    )
    assert "Pantry Pasta" in list(out["recipe_title"])


def test_auto_use_first_detects_perishables_when_not_provided(recommend_module):
    out = recommend_module.recommend_recipes(
        ["shrimp", "garlic", "pasta"],
        top_n=4,
    )
    assert int(out.iloc[0]["perish_total"]) >= 1
    assert "shrimp" in list(out.iloc[0]["use_first_items"])


def test_perish_columns_zero_when_no_perishables(recommend_module):
    out = recommend_module.recommend_recipes(
        ["rice", "salt", "olive oil"],
        use_first=[],
        top_n=4,
    )
    assert int(out.iloc[0]["perish_total"]) == 0
    assert float(out.iloc[0]["perish_coverage"]) == 0.0


def test_use_first_metadata_present(recommend_module):
    out = recommend_module.recommend_recipes(
        ["shrimp", "garlic", "pasta"],
        use_first=["shrimp"],
        top_n=4,
    )
    top = out.iloc[0]
    assert "perish_matched" in out.columns
    assert "perish_total" in out.columns
    assert "perish_coverage" in out.columns
    assert int(top["perish_total"]) == 1
    if top["recipe_title"] == "Shrimp Scampi":
        assert int(top["perish_matched"]) == 1


def test_dietary_filter_still_applies_with_use_first(recommend_module):
    out = recommend_module.recommend_recipes(
        ["shrimp", "garlic", "pasta"],
        preference="vegan",
        use_first=["shrimp"],
        top_n=4,
    )
    titles = list(out["recipe_title"])
    assert titles == ["Pantry Pasta"]
