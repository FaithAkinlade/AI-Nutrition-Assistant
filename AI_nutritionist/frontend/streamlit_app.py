import sys
import os
import ast
import streamlit as st

current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, ".."))

# Set the Environment Variable that recommend.py is crying about
if "MODEL_DIR" not in os.environ:
    os.environ["MODEL_DIR"] = os.path.join(project_root, "model")
if "DATA_DIR" not in os.environ:
    os.environ["DATA_DIR"] = os.path.join(project_root, "data")

model_path = os.environ["MODEL_DIR"]

# Add model folder to sys.path
if model_path not in sys.path:
    sys.path.insert(0, model_path)

# --- 2. IMPORT THE MODEL WITH ERROR HANDLING ---
try:
    from recommend import recommend_recipes
except KeyError as e:
    st.error(f"Model Error: Missing Environment Variable {e}")
    st.stop()
except ImportError:
    st.error(f"Import Error: Could not find 'recommend.py' in {model_path}")
    st.stop()
except Exception as e:
    st.error(f"An unexpected error occurred: {e}")
    st.stop()

# --- 2. CONFIG AND STYLES ---
st.set_page_config(page_title="S.N.A.C.C.", page_icon="\U0001F34E", layout="wide")

if "results" not in st.session_state:
    st.session_state.results = None
if "searched" not in st.session_state:
    st.session_state.searched = False
if "page" not in st.session_state:
    st.session_state.page = 0
if "last_tastes" not in st.session_state:
    st.session_state.last_tastes = []

has_results = st.session_state.searched and st.session_state.results is not None

st.markdown("""
<style>
    .stApp { background-color: #d4edda !important; }
    header[data-testid="stHeader"] { background-color: #d4edda !important; }
    .stButton > button {
        background-color: #8B6914 !important;
        color: #fff !important;
        border: 2px solid #6B4F12 !important;
        border-radius: 8px !important;
        font-weight: bold !important;
    }
    .stButton > button:hover { background-color: #6B4F12 !important; }
</style>
""", unsafe_allow_html=True)

# --- NEW: HEADER SECTION  ---
header_container = st.container()
with header_container:
    st.markdown("<div style='text-align:center; color:#5B3A0A; font-family:Georgia,serif; font-size:2.5rem; font-weight:bold; margin-top: 10px;'>S.N.A.C.C.</div>", unsafe_allow_html=True)
    st.markdown("<p style='text-align:center; color:#6B4F12; font-size:1.1rem; margin-bottom: 20px;'>Smart Nutrition Assistant Companion & Curator</p>", unsafe_allow_html=True)

if not has_results:
    # ---- CENTERED INPUT VIEW ----
    st.markdown("<div style='height: 5vh;'></div>", unsafe_allow_html=True)
    col_left, col_center, col_right = st.columns([1, 2, 1])
    
    with col_center:
        ingredients_input = st.text_input("Ingredients (comma-separated)", placeholder="e.g. chicken, garlic, onion", key="ingredients_center")

        sub_col1, sub_col2, sub_col3 = st.columns(3)
        with sub_col1:
            preference = st.selectbox("Dietary preference", options=["None", "vegan", "vegetarian", "gluten_free", "dairy_free"], key="pref_center")
        with sub_col2:
            top_n = st.slider("Number of recipes", 1, 20, 5, key="topn_center")
        with sub_col3:
            st.markdown("**Tastes**")
            tastes_selected = st.multiselect("Choose up to 2", ["sweet", "sour", "umami", "bitter", "spicy", "savory"], max_selections=2, key="tastes_multi_center")

        if st.button("Get Recommendations", type="primary", use_container_width=True):
            if not ingredients_input.strip():
                st.warning("Please enter at least one ingredient.")
            else:
                ingredients_list = [i.strip() for i in ingredients_input.split(",") if i.strip()]
                pref = None if preference == "None" else preference
                with st.spinner("Finding recipes..."):
                    results = recommend_recipes(ingredients_list, pref, tastes_selected, top_n)
                
                if results is None or (hasattr(results, 'empty') and results.empty):
                    st.info("No recipes found. Try different ingredients.")
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
        label { color: #5B3A0A !important; font-weight: 500; }
        </style>
        """, unsafe_allow_html=True)

    # We change the columns to [2, 1, 1, 2, 1] to make room for Tastes
    top_col1, top_col2, top_col3, top_col4, top_col5 = st.columns([2, 1, 1, 2, 1])
    
    with top_col1:
        ingredients_input = st.text_input(
            "Ingredients",
            value=st.session_state.get("last_ingredients", ""),
            key="ingredients_top",
            label_visibility="collapsed"
        )
    with top_col2:
        preference = st.selectbox(
            "Diet",
            options=["None", "vegan", "vegetarian", "gluten_free", "dairy_free"],
            index=["None", "vegan", "vegetarian", "gluten_free", "dairy_free"].index(
                st.session_state.get("last_pref", "None")
            ),
            key="pref_top",
            label_visibility="collapsed"
        )
    with top_col3:
        top_n = st.number_input(
            "Qty", min_value=1, max_value=20,
            value=st.session_state.get("last_topn", 5),
            key="topn_top",
            label_visibility="collapsed"
        )
    with top_col4:
        # ADDING THE TASTE WIDGET BACK HERE
        tastes_selected = st.multiselect(
            "Tastes",
            ["sweet", "sour", "umami", "bitter", "spicy", "savory"],
            default=st.session_state.get("last_tastes", []),
            max_selections=2,
            key="tastes_top",
            label_visibility="collapsed"
        )
    with top_col5:
        if st.button("Search", type="primary", use_container_width=True):
            if not ingredients_input.strip():
                st.warning("Please enter ingredients.")
            else:
                ingredients_list = [i.strip() for i in ingredients_input.split(",") if i.strip()]
                pref = None if preference == "None" else preference
                
                with st.spinner("Updating..."):
                    results = recommend_recipes(ingredients_list, pref, tastes_selected, top_n)
                
                if results is not None:
                    st.session_state.results = results
                    st.session_state.page = 0
                    st.session_state.last_ingredients = ingredients_input
                    st.session_state.last_pref = preference
                    st.session_state.last_topn = top_n
                    st.session_state.last_tastes = tastes_selected # Save the new selection
                    st.rerun()

    st.markdown("<hr style='border-color:#c4a97d; margin:0.5rem 0 1rem 0;'>", unsafe_allow_html=True)

    results = st.session_state.results
    total_recipes = len(results)
    total_spreads = (total_recipes + 1) // 2
    spread = st.session_state.page
    left_idx = spread * 2
    right_idx = spread * 2 + 1

    def parse_recipe(idx):
        row = results.iloc[idx]
        title = row["recipe_title"]
        def fmt(data):
            try:
                p = ast.literal_eval(data)
                return "".join(f"<li>{x}</li>" for x in p) if isinstance(p, list) else f"<li>{data}</li>"
            except: return f"<li>{data}</li>"
        matched = int(row["matched_count"]) if "matched_count" in row else 0
        total = int(row["total_user_ingredients"]) if "total_user_ingredients" in row else 0
        badge = f"Uses {matched} of your {total} ingredients" if total else ""
        missing = row["missing_ingredients"] if "missing_ingredients" in row else []
        if not isinstance(missing, list):
            missing = []
        missing_html = "".join(f"<li>{m}</li>" for m in missing)
        return title, fmt(row["ingredients"]), fmt(row["directions"]), badge, missing_html

    def build_page_html(title, ing_html, dir_html, page_num, side, badge="", missing_html=""):
        radius = "12px 0 0 12px" if side == "left" else "0 12px 12px 0"
        border = "border-right: 1px solid #8B6914;" if side == "left" else ""
        grad = "to left" if side == "left" else "to right"
        spine = f'<div style="position:absolute; {"right" if side=="left" else "left"}:0; top:0; bottom:0; width:18px; background:linear-gradient({grad}, #8B6914, #b8956a, transparent);"></div>'
        badge_html = (
            f'<div style="text-align:center; margin: 0 auto 0.75rem auto; display:inline-block; background:#6B4F12; color:#f5e6c8; padding:4px 12px; border-radius:999px; font-size:0.85rem; font-weight:bold;">{badge}</div>'
            if badge else ""
        )
        badge_wrap = f'<div style="text-align:center;">{badge_html}</div>' if badge else ""
        missing_block = (
            f'<div style="background:#fff8e7; border:1px dashed #8B6914; border-radius:8px; padding:0.5rem 1rem; margin: 0.5rem 0 1rem 0;">'
            f'<h4 style="color:#8B0000; margin:0 0 0.25rem 0;">You\'d need to buy</h4>'
            f'<ul style="margin:0; padding-left:1.25rem; color:#5B3A0A;">{missing_html}</ul></div>'
            if missing_html else ""
        )
        return f'''<div style="flex:1; background: linear-gradient(135deg, #d2b48c 0%, #f5e6c8 50%, #d2b48c 100%); border: 3px solid #8B6914; {border} border-radius: {radius}; padding: 2rem; position: relative; min-height: 600px; overflow: auto; font-family: Georgia, serif;">
            {spine}<h2 style="text-align:center; color:#5B3A0A; border-bottom:2px solid #8B6914;">{title}</h2>
            {badge_wrap}
            {missing_block}
            <h4 style="color:#6B4F12;">Ingredients</h4><ul>{ing_html}</ul>
            <h4 style="color:#6B4F12;">Instructions</h4><ol>{dir_html}</ol>
            <p style="text-align:center; color:#8B6914; font-style:italic;">— {page_num} —</p></div>'''

    l_title, l_ing, l_dir, l_badge, l_missing = parse_recipe(left_idx)
    left_page = build_page_html(l_title, l_ing, l_dir, left_idx + 1, "left", l_badge, l_missing)

    if right_idx < total_recipes:
        r_title, r_ing, r_dir, r_badge, r_missing = parse_recipe(right_idx)
        right_page = build_page_html(r_title, r_ing, r_dir, right_idx + 1, "right", r_badge, r_missing)
    else:
        right_page = '<div style="flex:1; background:#e6d2a8; border:3px solid #8B6914; border-radius:0 12px 12px 0; min-height:600px; display:flex; align-items:center; justify-content:center;">End of recipes</div>'

    n1, n2, n3 = st.columns([1, 6, 1])
    with n1:
        if spread > 0 and st.button("◀"):
            st.session_state.page -= 1
            st.rerun()
    with n3:
        if spread < total_spreads - 1 and st.button("▶"):
            st.session_state.page += 1
            st.rerun()

    st.markdown(f'<div style="display:flex; gap:0; max-width:1100px; margin:auto; box-shadow: 5px 5px 15px rgba(0,0,0,0.2);">{left_page}{right_page}</div>', unsafe_allow_html=True)

    if st.button("Start Over"):
        st.session_state.results = None
        st.session_state.searched = False
        st.rerun()
