import streamlit as st
from recipe_logic import (
    get_nutrition, build_recipe_macros,
    optimize_recipe_via_api, optimize_food_via_api,
    search_usda_suggestions
)
import pandas as pd

st.title("🍽️ Nutrition Optimizer")
st.write("Select your available ingredients and dietary goal to find the best meal or recipe.")

# User input for ingredients
food_input = st.text_input("Search for a food to add (type slowly for suggestions)")
suggestions = search_usda_suggestions(food_input) if food_input else []

if suggestions:
    st.write("Suggestions:")
    for s in suggestions:
        if st.button(f"Add {s}"):
            nutrition = get_nutrition(search_usda_suggestions(s)[0])
            nutrition["Available (g)"] = 100
            st.session_state.selected_foods.append(nutrition)

# Set up session state
if "selected_foods" not in st.session_state:
    st.session_state.selected_foods = []

st.write("### Selected Foods")
df = pd.DataFrame(st.session_state.selected_foods)
st.dataframe(df)

# Dietary goal
goal = st.selectbox("Choose optimization goal", [
    "maximize_protein", "minimize_calories", "minimize_fat", "minimize_cholesterol", "maximize_fiber"
])

# Calorie constraints
min_cal = st.number_input("Minimum calories", min_value=0, value=0)
max_cal = st.number_input("Maximum calories", min_value=0, value=1000)

if st.button("Optimize Foods"):
    result = optimize_food_via_api(st.session_state.selected_foods, goal, min_cal, max_cal)
    if result:
        st.write("### Optimal Food Combination")
        st.dataframe(pd.DataFrame(result))

# Optimize Recipes
from recipes_data import recipes, ingredients
if st.button("Optimize Recipes"):
    if any(recipe_logic.recipe_is_makeable(ingredients[name], st.session_state.selected_foods) for name in recipes):
        df_macros = build_recipe_macros(recipes, st.session_state.selected_foods)
        result = optimize_recipe_via_api(df_macros, goal, min_cal, max_cal)
        if result:
            st.write("### Optimal Recipe")
            st.json(result)
    else:
        st.write("No recipes are makeable with selected foods.")