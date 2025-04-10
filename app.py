# ⚡ Run Optimization
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