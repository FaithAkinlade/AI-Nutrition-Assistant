import sys
import os
import ast

# Add model folder to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "model")))

import streamlit as st
from recommend import recommend_recipes

st.set_page_config(page_title="AI Nutrition Assistant", page_icon="\U0001F34E", layout="wide")

# --- Session state ---
if "results" not in st.session_state:
    st.session_state.results = None
if "searched" not in st.session_state:
    st.session_state.searched = False

has_results = st.session_state.searched and st.session_state.results is not None

# --- Global styles ---
st.markdown("""
<style>
    /* Pastel green background */
    .stApp {
        background-color: #d4edda !important;
    }
    /* Hide default header/footer */
    header[data-testid="stHeader"] {
        background-color: #d4edda !important;
    }
    /* Style all buttons */
    .stButton > button[kind="primary"],
    .stButton > button {
        background-color: #8B6914 !important;
        color: #fff !important;
        border: 2px solid #6B4F12 !important;
        border-radius: 8px !important;
        font-weight: bold !important;
    }
    .stButton > button:hover {
        background-color: #6B4F12 !important;
    }
</style>
""", unsafe_allow_html=True)

if not has_results:
    # ---- CENTERED INPUT VIEW ----
    st.markdown("""
    <style>
        .center-input .stVerticalBlock {
            display: flex;
            flex-direction: column;
            align-items: center;
        }
    </style>
    """, unsafe_allow_html=True)

    # Push content to vertical center
    st.markdown("<div style='height: 18vh;'></div>", unsafe_allow_html=True)

    col_left, col_center, col_right = st.columns([1, 2, 1])
    with col_center:
        st.markdown(
            "<h1 style='text-align:center; color:#5B3A0A; font-family:Georgia,serif;'>"
            "\U0001F34E AI Nutrition Assistant</h1>",
            unsafe_allow_html=True
        )
        st.markdown(
            "<p style='text-align:center; color:#6B4F12; font-size:1.1rem;'>"
            "Enter the ingredients you have and get recipe recommendations.</p>",
            unsafe_allow_html=True
        )

        ingredients_input = st.text_input(
            "Ingredients (comma-separated)",
            placeholder="e.g. chicken, garlic, onion, tomato",
            key="ingredients_center"
        )

        sub_col1, sub_col2 = st.columns(2)
        with sub_col1:
            preference = st.selectbox(
                "Dietary preference",
                options=["None", "vegan", "vegetarian", "gluten_free", "dairy_free"],
                key="pref_center"
            )
        with sub_col2:
            top_n = st.slider("Number of recipes", min_value=1, max_value=20, value=5, key="topn_center")

        if st.button("Get Recommendations", type="primary", use_container_width=True):
            if not ingredients_input.strip():
                st.warning("Please enter at least one ingredient.")
            else:
                ingredients_list = [i.strip() for i in ingredients_input.split(",") if i.strip()]
                pref = None if preference == "None" else preference
                with st.spinner("Finding recipes..."):
                    results = recommend_recipes(ingredients_list, pref, top_n)
                if isinstance(results, list) and len(results) == 0:
                    st.info("No recipes found. Try different ingredients or preferences.")
                else:
                    st.session_state.results = results
                    st.session_state.searched = True
                    st.session_state.last_ingredients = ingredients_input
                    st.session_state.last_pref = preference
                    st.session_state.last_topn = top_n
                    st.rerun()

else:
    # ---- TOP INPUT + COOKBOOK RESULTS VIEW ----

    # --- Compact input bar at top ---
    st.markdown(
        "<h3 style='text-align:center; color:#5B3A0A; font-family:Georgia,serif; margin-bottom:0;'>"
        "\U0001F34E AI Nutrition Assistant</h3>",
        unsafe_allow_html=True
    )

    top_col1, top_col2, top_col3, top_col4 = st.columns([3, 2, 1, 1])
    with top_col1:
        ingredients_input = st.text_input(
            "Ingredients",
            value=st.session_state.get("last_ingredients", ""),
            placeholder="e.g. chicken, garlic, onion, tomato",
            key="ingredients_top",
            label_visibility="collapsed"
        )
    with top_col2:
        preference = st.selectbox(
            "Dietary preference",
            options=["None", "vegan", "vegetarian", "gluten_free", "dairy_free"],
            index=["None", "vegan", "vegetarian", "gluten_free", "dairy_free"].index(
                st.session_state.get("last_pref", "None")
            ),
            key="pref_top",
            label_visibility="collapsed"
        )
    with top_col3:
        top_n = st.slider(
            "Recipes", min_value=1, max_value=20,
            value=st.session_state.get("last_topn", 5),
            key="topn_top",
            label_visibility="collapsed"
        )
    with top_col4:
        if st.button("Search", type="primary", use_container_width=True):
            if not ingredients_input.strip():
                st.warning("Please enter at least one ingredient.")
            else:
                ingredients_list = [i.strip() for i in ingredients_input.split(",") if i.strip()]
                pref = None if preference == "None" else preference
                with st.spinner("Finding recipes..."):
                    results = recommend_recipes(ingredients_list, pref, top_n)
                if isinstance(results, list) and len(results) == 0:
                    st.info("No recipes found. Try different ingredients or preferences.")
                    st.session_state.results = None
                    st.session_state.searched = False
                else:
                    st.session_state.results = results
                    st.session_state.last_ingredients = ingredients_input
                    st.session_state.last_pref = preference
                    st.session_state.last_topn = top_n
                    st.rerun()

    st.markdown("<hr style='border-color:#c4a97d; margin:0.5rem 0 1rem 0;'>", unsafe_allow_html=True)

    # --- Cookbook results ---
    results = st.session_state.results
    st.markdown(
        f"<p style='text-align:center; color:#5B3A0A; font-family:Georgia,serif; font-size:1rem;'>"
        f"Found {len(results)} recipe(s)</p>",
        unsafe_allow_html=True
    )

    for i, (_, row) in enumerate(results.iterrows(), 1):
        # Parse ingredients
        ingredients_raw = row["ingredients"]
        try:
            ingredients_parsed = ast.literal_eval(ingredients_raw)
            if isinstance(ingredients_parsed, list):
                ing_html = "".join(f"<li>{ing}</li>" for ing in ingredients_parsed)
            else:
                ing_html = f"<li>{ingredients_raw}</li>"
        except (ValueError, SyntaxError):
            ing_html = f"<li>{ingredients_raw}</li>"

        # Parse directions
        directions_raw = row["directions"]
        try:
            directions_parsed = ast.literal_eval(directions_raw)
            if isinstance(directions_parsed, list):
                dir_html = "".join(
                    f"<li>{step}</li>" for step in directions_parsed
                )
            else:
                dir_html = f"<li>{directions_raw}</li>"
        except (ValueError, SyntaxError):
            dir_html = f"<li>{directions_raw}</li>"

        recipe_title = row["recipe_title"]

        # Cookbook card
        book_col_l, book_col_c, book_col_r = st.columns([1, 3, 1])
        with book_col_c:
            card_html = (
                '<div style="'
                "background: linear-gradient(135deg, #d2b48c 0%, #c4a97d 15%, #f5e6c8 30%, #e6d2a8 50%, #c9a96e 70%, #b8956a 85%, #d2b48c 100%);"
                "border: 3px solid #8B6914;"
                "border-radius: 12px;"
                "padding: 2.5rem 3rem;"
                "margin: 1rem auto;"
                "max-width: 750px;"
                "box-shadow: 4px 4px 15px rgba(90,58,10,0.25), inset 0 0 30px rgba(255,255,255,0.15);"
                "font-family: Georgia, 'Times New Roman', serif;"
                "position: relative;"
                '">'
                '<div style="position: absolute; left: 0; top: 0; bottom: 0; width: 18px;'
                "background: linear-gradient(to right, #8B6914, #b8956a, transparent);"
                'border-radius: 12px 0 0 12px;"></div>'
                f'<h2 style="text-align: center; color: #5B3A0A;'
                f"border-bottom: 2px solid #8B6914;"
                f"padding-bottom: 0.6rem; margin-bottom: 1.2rem;"
                f'font-style: italic; font-size: 1.6rem;">{recipe_title}</h2>'
                '<div style="display: flex; gap: 2rem; flex-wrap: wrap;">'
                '<div style="flex: 1; min-width: 200px;">'
                '<h4 style="color: #6B4F12; border-bottom: 1px dashed #a08050; padding-bottom: 4px;">Ingredients</h4>'
                f'<ul style="color: #4a3520; line-height: 1.8; padding-left: 1.2rem; list-style-type: disc;">{ing_html}</ul>'
                '</div>'
                '<div style="flex: 2; min-width: 280px;">'
                '<h4 style="color: #6B4F12; border-bottom: 1px dashed #a08050; padding-bottom: 4px;">Instructions</h4>'
                f'<ol style="color: #4a3520; line-height: 1.9; padding-left: 1.2rem;">{dir_html}</ol>'
                '</div>'
                '</div>'
                f'<p style="text-align: center; color: #8B6914; margin-top: 1.2rem; font-style: italic; font-size: 0.9rem;">'
                f'&mdash; {i} &mdash;</p>'
                '</div>'
            )
            st.markdown(card_html, unsafe_allow_html=True)

    # Back button
    st.markdown("<div style='height: 1rem;'></div>", unsafe_allow_html=True)
    bcol1, bcol2, bcol3 = st.columns([1, 1, 1])
    with bcol2:
        if st.button("Start Over", use_container_width=True):
            st.session_state.results = None
            st.session_state.searched = False
            st.rerun()
