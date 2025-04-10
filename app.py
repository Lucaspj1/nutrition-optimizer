import streamlit as st
from recipe_logic import *
from recipes_data import recipes

st.set_page_config(page_title="Nutrition Optimizer", layout="centered")
st.title("🥗 Nutrition Optimizer")

if "selected_foods" not in st.session_state:
    st.session_state.selected_foods = []

# ---------------------
# 🔍 Search + Add Food
# ---------------------
st.subheader("🔍 Search and Add Foods (USDA API)")
search_term = st.text_input("Type a food name:")

selected_option = None
if search_term:
    options = search_usda_suggestions(search_term)
    if options:
        selected_option = st.selectbox("Select a food to add:", options)

if selected_option and st.button("➕ Add Food"):
    result = search_food(selected_option)
    if result:
        fdc_id, name = result
        nutrition = get_nutrition(fdc_id)
        st.session_state.selected_foods.append(nutrition)
        st.success(f"✅ Added: {name}")
    else:
        st.error("Food not found.")

# ---------------------
# 📋 Display Selected
# ---------------------
if st.session_state.selected_foods:
    st.subheader("🧾 Selected Foods")
    st.table(st.session_state.selected_foods)

# ---------------------
# 🎯 Goal
# ---------------------
goal = st.selectbox("🎯 Choose your nutrition goal", [
    "maximize_protein", "minimize_carbs", "minimize_calories", "maximize_fiber"
])

# ---------------------
# ⚙️ Optimization Mode
# ---------------------
mode = st.radio("🧠 Choose optimization mode", ["Optimize by Recipe", "Optimize by Foods (no recipes)"])

# ---------------------
# ⚡ Run Optimization
# ---------------------
if st.session_state.selected_foods and st.button("⚡ Optimize Now"):
    if mode == "Optimize by Recipe":
        makeable = {
            name: ing for name, ing in recipes.items()
            if recipe_is_makeable(ing, st.session_state.selected_foods)
        }

        if not makeable:
            st.warning("❌ No recipes can be made from selected foods.")
        else:
            df = build_recipe_macros(makeable, st.session_state.selected_foods)
            best = optimize_recipes_by_goal(df, goal)
            st.success(f"🔥 Best Recipe: {best}")

            st.subheader("📋 Ingredients")
            for k, v in makeable[best].items():
                st.write(f"- {k.title()}: {v}g")

            row = df[df["Recipe"] == best].iloc[0]
            st.subheader("📊 Macros")
            st.write({col: round(row[col], 1) for col in row.index if col != "Recipe"})

    else:
        best_combo = optimize_food_via_api(st.session_state.selected_foods, goal)
        if best_combo:
            st.success("✅ Optimal food plan generated:")
            for food, grams in best_combo.items():
                st.write(f"- {food.title()}: {round(grams, 1)}g")
        else:
            st.warning("❌ No optimal combination found.")