import sys
import os
import ast

# Add model folder to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "model")))

import streamlit as st
from recommend import recommend_recipes

st.set_page_config(page_title="AI Nutrition Assistant", page_icon="\U0001F34E")

st.title("\U0001F34E AI Nutrition Assistant")
st.write("Enter the ingredients you have and get recipe recommendations.")

# --- Inputs ---
ingredients_input = st.text_input(
    "Ingredients (comma-separated)",
    placeholder="e.g. chicken, garlic, onion, tomato"
)

col1, col2 = st.columns(2)

with col1:
    preference = st.selectbox(
        "Dietary preference",
        options=["None", "vegan", "vegetarian", "gluten_free", "dairy_free"]
    )

with col2:
    top_n = st.slider("Number of recipes", min_value=1, max_value=20, value=5)

# --- Recommend ---
if st.button("Get Recommendations", type="primary"):
    if not ingredients_input.strip():
        st.warning("Please enter at least one ingredient.")
    else:
        ingredients_list = [i.strip() for i in ingredients_input.split(",") if i.strip()]
        pref = None if preference == "None" else preference

        with st.spinner("Finding recipes..."):
            results = recommend_recipes(ingredients_list, pref, top_n)

        if isinstance(results, list) and len(results) == 0:
            st.info("No recipes found for this combination. Try different ingredients or preferences.")
        else:
            st.success(f"Found {len(results)} recipe(s)!")
            for i, (_, row) in enumerate(results.iterrows(), 1):
                with st.expander(f"{i}. {row['recipe_title']}"):
                    # Parse ingredients if stored as string representation of list
                    ingredients_raw = row["ingredients"]
                    try:
                        ingredients_parsed = ast.literal_eval(ingredients_raw)
                        if isinstance(ingredients_parsed, list):
                            st.markdown("**Ingredients:**")
                            for ing in ingredients_parsed:
                                st.markdown(f"- {ing}")
                        else:
                            st.markdown(f"**Ingredients:** {ingredients_raw}")
                    except (ValueError, SyntaxError):
                        st.markdown(f"**Ingredients:** {ingredients_raw}")

                    # Parse directions if stored as string representation of list
                    directions_raw = row["directions"]
                    try:
                        directions_parsed = ast.literal_eval(directions_raw)
                        if isinstance(directions_parsed, list):
                            st.markdown("**Directions:**")
                            for step_num, step in enumerate(directions_parsed, 1):
                                st.markdown(f"{step_num}. {step}")
                        else:
                            st.markdown(f"**Directions:** {directions_raw}")
                    except (ValueError, SyntaxError):
                        st.markdown(f"**Directions:** {directions_raw}")
