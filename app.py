import streamlit as st
from recipe_logic import *
from recipes_data import recipes
import pandas as pd

st.set_page_config(page_title="Nutrition Optimizer", layout="centered")

st.title("🥗 Nutrition Optimizer")

# Search bar
search = st.text_input("Search for a food:", "")
if "selected_foods" not in st.session_state:
    st.session_state.selected_foods = []

# Handle food search and add
if search:
    suggestions = search_usda_suggestions(search)
    selection = st.selectbox("Select from suggestions:", suggestions)
    if st.button("Add Food"):
        matches = search_food(selection)
        if matches:
            nutrients = get_nutrition(matches[0][0])
            nutrients["Available (g)"] = 100
            st.session_state.selected_foods.append(nutrients)

# Show selected foods
if st.session_state.selected_foods:
    df_foods = pd.DataFrame(st.session_state.selected_foods)
    df_foods.set_index("Food", inplace=True)
    edited = st.data_editor(df_foods, num_rows="dynamic")
    st.session_state.selected_foods = edited.reset_index().to_dict(orient="records")

# Goal and calories
goal = st.selectbox("Optimization goal:", ["maximize_protein", "minimize_carbs", "minimize_fat", "minimize_cholesterol"])
min_calories = st.number_input("Min Calories (optional)", value=0)
max_calories = st.number_input("Max Calories (optional)", value=1000)

# Optimize by Recipe
if st.button("Optimize by Recipe"):
    buildable = {
        name: ingredients
        for name, ingredients in recipes.items()
        if recipe_is_makeable(ingredients, st.session_state.selected_foods)
    }
    if not buildable:
        st.warning("❌ No buildable recipes with your selected foods.")
    else:
        df = build_recipe_macros(buildable, st.session_state.selected_foods)
        result = optimize_recipe_via_api(df, goal, min_calories, max_calories)
        if result:
            st.success(f"✅ Best Recipe: {result['Recipe']}")
            st.write(result)
        else:
            st.error("❌ Optimization failed.")

# Optimize by Food
if st.button("Optimize by Food"):
    result = optimize_food_via_api(st.session_state.selected_foods, goal, min_calories, max_calories)
    if result:
        st.success("✅ Optimization Successful")
        st.write(pd.DataFrame(result))
    else:
        st.error("❌ Optimization failed.")