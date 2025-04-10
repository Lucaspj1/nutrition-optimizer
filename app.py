import streamlit as st
from recipe_logic import (
    search_usda_suggestions,
    search_food,
    get_nutrition,
    optimize_food_via_api,
    optimize_recipe_via_api,
    recipe_is_makeable,
    build_recipe_macros
)
from recipes_data import recipes
import pandas as pd

st.set_page_config(page_title="Nutrition Optimizer", layout="centered")
st.title("🥗 Nutrition Optimizer")

# --- Session State ---
if "selected_foods" not in st.session_state:
    st.session_state.selected_foods = []

# --- Food Entry Section ---
st.header("Add Foods")
food_input = st.text_input("Search for a food (e.g. chicken, avocado, bread):")
suggestions = search_usda_suggestions(food_input) if food_input else []

if suggestions:
    selected = st.selectbox("Choose a food", suggestions)
    grams = st.number_input("How many grams of this food do you have?", min_value=0, step=10, value=100)

    if st.button("➕ Add Food"):
        fdc_id, name = search_food(selected)
        if fdc_id:
            macros = get_nutrition(fdc_id)
            macros["Available (g)"] = grams
            st.session_state.selected_foods.append(macros)
            st.success(f"✅ Added {name} ({grams}g)")
        else:
            st.warning("❌ Could not fetch food info.")

# --- Show Selected Foods + Macros ---
if st.session_state.selected_foods:
    st.subheader("🧾 Selected Foods")
    df_foods = pd.DataFrame(st.session_state.selected_foods)
    st.dataframe(df_foods)

# --- Optimization Settings ---
st.header("Optimize My Nutrition")
mode = st.radio("Choose optimization mode:", ["Optimize by Food", "Optimize by Recipe"])
goal = st.selectbox("Select your dietary goal:", [
    "maximize_protein",
    "minimize_carbs",
    "minimize_calories",
    "maximize_fiber"
])

# --- Run Optimization ---
if st.session_state.selected_foods and st.button("⚡ Run Optimization"):
    if mode == "Optimize by Recipe":
        makeable = {
            name: ing for name, ing in recipes.items()
            if recipe_is_makeable(ing, st.session_state.selected_foods)
        }

        if not makeable:
            st.warning("❌ No recipes can be made from selected foods.")
        else:
            df = build_recipe_macros(makeable, st.session_state.selected_foods)
            best = optimize_recipe_via_api(df, goal)
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