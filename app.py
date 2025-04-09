import streamlit as st
from recipe_logic import *
from recipes_data import recipes

st.set_page_config(page_title="Nutrition Optimizer", layout="centered")
st.title("🥗 Nutrition Optimizer")

# Search
query = st.text_input("Search a food (from USDA API):")
if "selected_foods" not in st.session_state:
    st.session_state.selected_foods = []

if query:
    result = search_food(query)
    if result:
        fdc_id, name = result
        nutrition = get_nutrition(fdc_id)
        st.session_state.selected_foods.append(nutrition)
        st.success(f"✅ Added: {name}")
    else:
        st.error("❌ Food not found.")

# View selected
if st.session_state.selected_foods:
    st.subheader("🧾 Selected Foods")
    st.table(st.session_state.selected_foods)

# Dietary goal
goal = st.selectbox("🎯 Select your dietary goal", [
    "maximize_protein", "minimize_carbs", "minimize_calories", "maximize_fiber"
])

# Filter recipes
makeable_recipes = {
    name: ingredients for name, ingredients in recipes.items()
    if recipe_is_makeable(ingredients, st.session_state.selected_foods)
}

if not makeable_recipes:
    st.warning("❌ No recipes can be made with your selected foods.")
else:
    if st.button("⚡ Optimize!"):
        df = build_recipe_macros(makeable_recipes, st.session_state.selected_foods)
        best = optimize_recipes_by_goal(df, goal)
        st.success(f"🔥 Best Recipe: {best}")

        st.subheader("📋 Ingredients")
        for k, v in makeable_recipes[best].items():
            st.write(f"- {k.title()}: {v}g")

        row = df[df["Recipe"] == best].iloc[0]
        st.subheader("📊 Macros")
        st.write({col: round(row[col], 1) for col in row.index if col != "Recipe"})