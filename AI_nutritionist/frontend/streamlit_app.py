import sys
import os
import ast

# Add model folder to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "model")))

import streamlit as st
from recommend import recommend_recipes

st.set_page_config(page_title="S.N.A.C.C.", page_icon="\U0001F34E", layout="wide")

# --- Session state ---
if "results" not in st.session_state:
    st.session_state.results = None
if "searched" not in st.session_state:
    st.session_state.searched = False
if "page" not in st.session_state:
    st.session_state.page = 0
if "last_tastes" not in st.session_state:
    st.session_state.last_tastes = []

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
            "<div style='text-align:center; color:#5B3A0A; font-family:Georgia,serif; "
            "font-size:2rem; font-weight:bold;'>"
            "Smart Nutrition Assistant Companion & Curator (S.N.A.C.C.)</div>",
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

        sub_col1, sub_col2, sub_col3 = st.columns(3)
        with sub_col1:
            preference = st.selectbox(
                "Dietary preference",
                options=["None", "vegan", "vegetarian", "gluten_free", "dairy_free"],
                key="pref_center"
            )
        with sub_col2:
            top_n = st.slider("Number of recipes", min_value=1, max_value=20, value=5, key="topn_center")

        with sub_col3:
            st.markdown("**Tastes**")
            
            # Use the multiselect as the primary source
            tastes_selected = st.multiselect(
                "Choose up to 2 tastes",
                ["sweet", "sour", "umami", "bitter", "spicy", "savory"],
                max_selections=2,
                key="tastes_multi_center"
            )
            
            # Supporting checkboxes (only add if not already in multiselect and list is < 2)
            c1, c2 = st.columns(2)
            with c1:
                if st.checkbox("Sweet") and "sweet" not in tastes_selected: tastes_selected.append("sweet")
                if st.checkbox("Sour") and "sour" not in tastes_selected: tastes_selected.append("sour")
                if st.checkbox("Umami") and "umami" not in tastes_selected: tastes_selected.append("umami")
            with c2:
                if st.checkbox("Bitter") and "bitter" not in tastes_selected: tastes_selected.append("bitter")
                if st.checkbox("Spicy") and "spicy" not in tastes_selected: tastes_selected.append("spicy")
                if st.checkbox("Savory") and "savory" not in tastes_selected: tastes_selected.append("savory")

            if len(tastes_selected) > 2:
                st.warning("Please select up to 2 tastes only.")
                st.stop()

        if st.button("Get Recommendations", type="primary", use_container_width=True):
            if not ingredients_input.strip():
                st.warning("Please enter at least one ingredient.")
            else:
                ingredients_list = [i.strip() for i in ingredients_input.split(",") if i.strip()]
                pref = None if preference == "None" else preference
                with st.spinner("Finding recipes..."):
                    results = recommend_recipes(ingredients_list, pref, tastes_selected, top_n)
                if results is None or (isinstance(results, list) and len(results) == 0) or (hasattr(results, 'empty') and results.empty):
                    st.info("No recipes found. Try different ingredients or preferences.")
                else:
                    st.session_state.results = results
                    st.session_state.searched = True
                    st.session_state.page = 0
                    st.session_state.last_ingredients = ingredients_input
                    st.session_state.last_pref = preference
                    st.session_state.last_topn = top_n
                    st.session_state.last_tastes = tastes_selected
                    st.rerun()

else:
    # ---- TOP INPUT + COOKBOOK RESULTS VIEW ----
    st.markdown("""
        <style>
        input[type="checkbox"] {
            accent-color: #8B6914;
            transform: scale(1.2);
            border-radius: 50%;
        }
        .stCheckbox { margin-bottom: 6px; }
        label { color: #5B3A0A !important; font-weight: 500; }
        </style>
        """, unsafe_allow_html=True)

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
                # Ensure we pass the previously selected tastes
                current_tastes = st.session_state.get("last_tastes", [])
                with st.spinner("Finding recipes..."):
                    results = recommend_recipes(ingredients_list, pref, current_tastes, top_n)
                if results is None or (isinstance(results, list) and len(results) == 0) or (hasattr(results, 'empty') and results.empty):
                    st.info("No recipes found. Try different ingredients or preferences.")
                else:
                    st.session_state.results = results
                    st.session_state.page = 0
                    st.session_state.last_ingredients = ingredients_input
                    st.session_state.last_pref = preference
                    st.session_state.last_topn = top_n
                    st.rerun()

    st.markdown("<hr style='border-color:#c4a97d; margin:0.5rem 0 1rem 0;'>", unsafe_allow_html=True)

    # --- Cookbook results ---
    results = st.session_state.results
    total_recipes = len(results)
    total_spreads = (total_recipes + 1) // 2

    if st.session_state.page >= total_spreads:
        st.session_state.page = total_spreads - 1
    if st.session_state.page < 0:
        st.session_state.page = 0

    spread = st.session_state.page
    left_idx = spread * 2
    right_idx = spread * 2 + 1

    st.markdown(
        '<style>'
        '.small-arrow button {font-size: 0.7rem !important; padding: 0.15rem 0.5rem !important;'
        'min-height: 0 !important; height: auto !important; line-height: 1 !important;}'
        '</style>',
        unsafe_allow_html=True
    )

    def parse_recipe(idx):
        row = results.iloc[idx]
        title = row["recipe_title"]
        raw = row["ingredients"]
        try:
            parsed = ast.literal_eval(raw)
            ing = "".join(f"<li>{x}</li>" for x in parsed) if isinstance(parsed, list) else f"<li>{raw}</li>"
        except: ing = f"<li>{raw}</li>"
        
        raw_d = row["directions"]
        try:
            parsed_d = ast.literal_eval(raw_d)
            dirs = "".join(f"<li>{s}</li>" for s in parsed_d) if isinstance(parsed_d, list) else f"<li>{raw_d}</li>"
        except: dirs = f"<li>{raw_d}</li>"
        return title, ing, dirs

    def build_page_html(title, ing_html, dir_html, page_num, side):
        border_radius = "12px 0 0 12px" if side == "left" else "0 12px 12px 0"
        border_right = "border-right: 1px solid #8B6914;" if side == "left" else ""
        grad = "to left" if side == "left" else "to right"
        spine = f'<div style="position:absolute; {"right" if side=="left" else "left"}:0; top:0; bottom:0; width:18px; background:linear-gradient({grad}, #8B6914, #b8956a, transparent);"></div>'

        return (
            f'<div style="flex:1; background: linear-gradient(135deg, #d2b48c 0%, #c4a97d 15%, #f5e6c8 30%, #e6d2a8 50%, #c9a96e 70%, #b8956a 85%, #d2b48c 100%); '
            f'border: 3px solid #8B6914; {border_right} border-radius: {border_radius}; padding: 2rem 2.5rem; box-shadow: inset 0 0 30px rgba(255,255,255,0.15); '
            f"font-family: Georgia, serif; position: relative; min-height: 600px; overflow: auto;\">"
            f'{spine}'
            f'<h2 style="text-align:center; color:#5B3A0A; border-bottom:2px solid #8B6914; padding-bottom:0.5rem; margin-bottom:1rem; font-style:italic; font-size:1.4rem;">{title}</h2>'
            f'<h4 style="color:#6B4F12; border-bottom:1px dashed #a08050; padding-bottom:4px;">Ingredients</h4>'
            f'<ul style="color:#4a3520; line-height:1.7; padding-left:1.2rem; list-style-type:disc; font-size:0.9rem;">{ing_html}</ul>'
            f'<h4 style="color:#6B4F12; border-bottom:1px dashed #a08050; padding-bottom:4px; margin-top:1rem;">Instructions</h4>'
            f'<ol style="color:#4a3520; line-height:1.8; padding-left:1.2rem; font-size:0.9rem;">{dir_html}</ol>'
            f'<p style="text-align:center; color:#8B6914; margin-top:1rem; font-style:italic; font-size:0.85rem;">&mdash; {page_num} &mdash;</p></div>'
        )

    l_title, l_ing, l_dir = parse_recipe(left_idx)
    left_page = build_page_html(l_title, l_ing, l_dir, left_idx + 1, "left")

    if right_idx < total_recipes:
        r_title, r_ing, r_dir = parse_recipe(right_idx)
        right_page = build_page_html(r_title, r_ing, r_dir, right_idx + 1, "right")
    else:
        right_page = '<div style="flex:1; background: linear-gradient(135deg, #d2b48c 0%, #f5e6c8 100%); border: 3px solid #8B6914; border-radius: 0 12px 12px 0; min-height: 600px; display: flex; align-items: center; justify-content: center;"><p style="color:#8B6914; font-style:italic;">End of recipes</p></div>'

    # Navigation
    arrow_l, arrow_spacer, arrow_r = st.columns([1, 6, 1])
    with arrow_l:
        if spread > 0 and st.button("\u25C0", key="prev_page"):
            st.session_state.page -= 1
            st.rerun()
    with arrow_spacer:
        st.markdown(f'<p style="text-align:center; color:#5B3A0A;">Pages {left_idx+1}–{min(right_idx+1, total_recipes)} of {total_recipes}</p>', unsafe_allow_html=True)
    with arrow_r:
        if spread < total_spreads - 1 and st.button("\u25B6", key="next_page"):
            st.session_state.page += 1
            st.rerun()

    book_html = f'<div style="display:flex; gap:0; margin:0 auto; max-width:1200px; box-shadow: 4px 4px 20px rgba(90,58,10,0.3);">{left_page}{right_page}</div>'
    st.markdown(book_html, unsafe_allow_html=True)

    st.markdown("<div style='height: 1rem;'></div>", unsafe_allow_html=True)
    if st.button("Start Over", use_container_width=True):
        st.session_state.results = None
        st.session_state.searched = False
        st.session_state.page = 0
        st.rerun()
