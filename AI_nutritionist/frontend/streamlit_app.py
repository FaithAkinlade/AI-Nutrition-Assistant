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
if "page" not in st.session_state:
    st.session_state.page = 0

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
            "AI Nutrition Assistant</h1>",
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
                    st.session_state.page = 0
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
                    st.session_state.page = 0
                    st.session_state.last_ingredients = ingredients_input
                    st.session_state.last_pref = preference
                    st.session_state.last_topn = top_n
                    st.rerun()

    st.markdown("<hr style='border-color:#c4a97d; margin:0.5rem 0 1rem 0;'>", unsafe_allow_html=True)

    # --- Cookbook results (two-page spread) ---
    results = st.session_state.results
    total_recipes = len(results)
    total_spreads = (total_recipes + 1) // 2

    # page state stores spread index; ensure always lands on odd-numbered left page (0-based spread)
    if st.session_state.page >= total_spreads:
        st.session_state.page = total_spreads - 1
    if st.session_state.page < 0:
        st.session_state.page = 0

    spread = st.session_state.page
    left_idx = spread * 2       # always odd recipe number (1, 3, 5...) displayed as 1-indexed
    right_idx = spread * 2 + 1

    # --- Remove column gap and small arrow styling ---
    st.markdown(
        '<style>'
        '.small-arrow button {font-size: 0.7rem !important; padding: 0.15rem 0.5rem !important;'
        'min-height: 0 !important; height: auto !important; line-height: 1 !important;}'
        '</style>',
        unsafe_allow_html=True
    )

    # Helper to parse recipe data into HTML
    def parse_recipe(idx):
        row = results.iloc[idx]
        title = row["recipe_title"]
        raw = row["ingredients"]
        try:
            parsed = ast.literal_eval(raw)
            if isinstance(parsed, list):
                ing = "".join(f"<li>{x}</li>" for x in parsed)
            else:
                ing = f"<li>{raw}</li>"
        except (ValueError, SyntaxError):
            ing = f"<li>{raw}</li>"
        raw_d = row["directions"]
        try:
            parsed_d = ast.literal_eval(raw_d)
            if isinstance(parsed_d, list):
                dirs = "".join(f"<li>{s}</li>" for s in parsed_d)
            else:
                dirs = f"<li>{raw_d}</li>"
        except (ValueError, SyntaxError):
            dirs = f"<li>{raw_d}</li>"
        return title, ing, dirs

    # Build both pages HTML, then render together in one markdown block to eliminate gap
    def build_page_html(title, ing_html, dir_html, page_num, side):
        if side == "left":
            border_radius = "12px 0 0 12px"
            spine = (
                '<div style="position:absolute; right:0; top:0; bottom:0; width:18px;'
                'background:linear-gradient(to left, #8B6914, #b8956a, transparent);"></div>'
            )
            border_right = "border-right: 1px solid #8B6914;"
        else:
            border_radius = "0 12px 12px 0"
            spine = (
                '<div style="position:absolute; left:0; top:0; bottom:0; width:18px;'
                'background:linear-gradient(to right, #8B6914, #b8956a, transparent);"></div>'
            )
            border_right = ""

        return (
            f'<div style="'
            f"flex:1;"
            f"background: linear-gradient(135deg, #d2b48c 0%, #c4a97d 15%, #f5e6c8 30%, #e6d2a8 50%, #c9a96e 70%, #b8956a 85%, #d2b48c 100%);"
            f"border: 3px solid #8B6914;"
            f"{border_right}"
            f"border-radius: {border_radius};"
            f"padding: 2rem 2.5rem;"
            f"box-shadow: inset 0 0 30px rgba(255,255,255,0.15);"
            f"font-family: Georgia, 'Times New Roman', serif;"
            f"position: relative;"
            f"min-height: 600px;"
            f"overflow: auto;"
            f'">'
            f'{spine}'
            f'<h2 style="text-align:center; color:#5B3A0A;'
            f'border-bottom:2px solid #8B6914;'
            f'padding-bottom:0.5rem; margin-bottom:1rem;'
            f'font-style:italic; font-size:1.4rem;">{title}</h2>'
            f'<h4 style="color:#6B4F12; border-bottom:1px dashed #a08050; padding-bottom:4px;">Ingredients</h4>'
            f'<ul style="color:#4a3520; line-height:1.7; padding-left:1.2rem; list-style-type:disc; font-size:0.9rem;">{ing_html}</ul>'
            f'<h4 style="color:#6B4F12; border-bottom:1px dashed #a08050; padding-bottom:4px; margin-top:1rem;">Instructions</h4>'
            f'<ol style="color:#4a3520; line-height:1.8; padding-left:1.2rem; font-size:0.9rem;">{dir_html}</ol>'
            f'<p style="text-align:center; color:#8B6914; margin-top:1rem; font-style:italic; font-size:0.85rem;">'
            f'&mdash; {page_num} &mdash;</p>'
            f'</div>'
        )

    def build_empty_page_html():
        return (
            '<div style="'
            "flex:1;"
            "background: linear-gradient(135deg, #d2b48c 0%, #c4a97d 15%, #f5e6c8 30%, #e6d2a8 50%, #c9a96e 70%, #b8956a 85%, #d2b48c 100%);"
            "border: 3px solid #8B6914;"
            "border-radius: 0 12px 12px 0;"
            "padding: 2rem 2.5rem;"
            "box-shadow: inset 0 0 30px rgba(255,255,255,0.15);"
            "font-family: Georgia, 'Times New Roman', serif;"
            "position: relative;"
            "min-height: 600px;"
            "display: flex; align-items: center; justify-content: center;"
            '">'
            '<div style="position:absolute; left:0; top:0; bottom:0; width:18px;'
            'background:linear-gradient(to right, #8B6914, #b8956a, transparent);"></div>'
            '<p style="color:#8B6914; font-style:italic; font-size:1.1rem;">End of recipes</p>'
            '</div>'
        )

    # --- Navigation arrows at top of book ---
    l_title, l_ing, l_dir = parse_recipe(left_idx)
    if right_idx < total_recipes:
        r_title, r_ing, r_dir = parse_recipe(right_idx)
        right_page = build_page_html(r_title, r_ing, r_dir, right_idx + 1, "right")
    else:
        right_page = build_empty_page_html()

    left_page = build_page_html(l_title, l_ing, l_dir, left_idx + 1, "left")

    # Navigation row
    arrow_l, arrow_spacer, arrow_r = st.columns([1, 6, 1])
    with arrow_l:
        st.markdown('<div class="small-arrow">', unsafe_allow_html=True)
        if spread > 0:
            if st.button("\u25C0", key="prev_page"):
                st.session_state.page -= 1
                st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)
    with arrow_spacer:
        left_pn = left_idx + 1
        right_pn = min(right_idx + 1, total_recipes)
        st.markdown(
            f'<p style="text-align:center; color:#5B3A0A; font-family:Georgia,serif;'
            f'font-size:0.9rem; margin:0;">Pages {left_pn}–{right_pn} of {total_recipes}</p>',
            unsafe_allow_html=True
        )
    with arrow_r:
        st.markdown('<div class="small-arrow">', unsafe_allow_html=True)
        if spread < total_spreads - 1:
            if st.button("\u25B6", key="next_page"):
                st.session_state.page += 1
                st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

    # --- Render both pages as a single HTML block (no gap) ---
    book_html = (
        '<div style="display:flex; gap:0; margin:0 auto; max-width:1200px;'
        'box-shadow: 4px 4px 20px rgba(90,58,10,0.3);">'
        f'{left_page}'
        f'{right_page}'
        '</div>'
    )
    st.markdown(book_html, unsafe_allow_html=True)

    # Back button
    st.markdown("<div style='height: 1rem;'></div>", unsafe_allow_html=True)
    bcol1, bcol2, bcol3 = st.columns([1, 1, 1])
    with bcol2:
        if st.button("Start Over", use_container_width=True):
            st.session_state.results = None
            st.session_state.searched = False
            st.session_state.page = 0
            st.rerun()
