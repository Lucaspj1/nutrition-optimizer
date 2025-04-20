import streamlit as st
st.cache_data.clear()
from recipe_logic import (
    get_nutrition, build_recipe_macros,
    optimize_recipe_via_api, optimize_food_via_api,
    search_usda_suggestions, recipe_is_makeable,
    extract_base_food_name, find_best_match_for_ingredient
)
from recipes_data import recipes, ingredients
import pandas as pd
import traceback

st.set_page_config(page_title="Nutrition Optimizer", layout="wide")
st.title("🍽️ Nutrition Optimizer")
st.write("Search for foods, specify the amount you have, and optimize your diet!")

# Session initialization
if "selected_foods" not in st.session_state:
    st.session_state.selected_foods = []

# Sidebar navigation
st.sidebar.title("Navigation")
page = st.sidebar.radio("Go to", ["Food Optimizer", "Available Recipes"])

# Debug option
debug_mode = st.sidebar.checkbox("Debug Mode", value=False)

if page == "Food Optimizer":
    # Clear foods button
    col1, col2 = st.columns([4, 1])
    with col1:
        st.write("### Add Foods")
    with col2:
        if st.button("🗑️ Clear All Foods"):
            st.session_state.selected_foods = []
            st.rerun()

    # Food search and selection
    food_input = st.text_input("Search for a food (Foundation Foods only)")
    suggestions = search_usda_suggestions(food_input) if food_input else []

    if suggestions:
        selected = st.selectbox("Suggestions", suggestions, format_func=lambda x: x["name"])
        grams = st.number_input("How many grams of this food do you have?", min_value=1, value=100)
        
        if st.button("Add Food"):
            with st.spinner("Fetching nutrition data..."):
                nutrition = get_nutrition(selected["fdcId"])
                if nutrition:
                    nutrition["Grams"] = grams
                    st.session_state.selected_foods.append(nutrition)
                    st.success(f"Added {nutrition['name']} to your foods!")
                    st.rerun()
                else:
                    st.error("Could not fetch nutrition data for this food.")

    # Display selected foods
    if st.session_state.selected_foods:
        st.write("### Selected Foods")
        
        # Convert keys to display format
        display_foods = []
        for food in st.session_state.selected_foods:
            display_food = {
                "Food": food.get("name", "Unknown"),
                "Grams": food.get("Grams", 0),
                "Calories": food.get("calories", 0),
                "Protein (g)": food.get("protein", 0),
                "Carbs (g)": food.get("carbs", 0),
                "Fat (g)": food.get("fat", 0),
                "Fiber (g)": food.get("fiber", 0),
                "Cholesterol (mg)": food.get("cholesterol", 0)
            }
            display_foods.append(display_food)
        
        df = pd.DataFrame(display_foods)
        st.dataframe(df)
        
        # Show base food names in debug mode
        if debug_mode:
            st.write("### Base Food Names (for matching)")
            base_names = []
            for food in st.session_state.selected_foods:
                base_names.append({
                    "Food": food.get("name", "Unknown"),
                    "Base Name": extract_base_food_name(food.get("name", "Unknown"))
                })
            st.dataframe(pd.DataFrame(base_names))
        
        # Allow removing foods
        if st.button("Remove Last Food"):
            if st.session_state.selected_foods:
                removed = st.session_state.selected_foods.pop()
                st.success(f"Removed {removed['name']} from your foods!")
                st.rerun()

    # Optimization settings
    st.write("### Optimization Settings")
    goal = st.selectbox("Choose optimization goal", [
        "maximize_protein", "minimize_fat", 
        "minimize_cholesterol", "maximize_fiber"
    ])

    # Added calorie constraint inputs before optimization
    col1, col2 = st.columns(2)
    with col1:
        min_cal = st.number_input("Minimum calories", min_value=0, value=0)
    with col2:
        max_cal = st.number_input("Maximum calories", min_value=0, value=2000)

    # Create two columns for optimization buttons
    col1, col2 = st.columns(2)

    # Food optimization
    with col1:
        if st.button("Optimize Foods"):
            if st.session_state.selected_foods:
                with st.spinner("Calculating optimal food combination..."):
                    try:
                        result = optimize_food_via_api(st.session_state.selected_foods, goal, min_cal, max_cal)
                        
                        if debug_mode:
                            st.write("Debug: Optimization Result")
                            st.write(result)
                        
                        if result:
                            servings, macros = result
                            
                            st.write("### Optimal Food Combination")
                            
                            # Display servings
                            data = []
                            for food_name, grams in servings.items():
                                data.append({"Food": food_name, "Grams": grams})
                            
                            st.dataframe(pd.DataFrame(data))
                            
                            # Display macros in a more readable format
                            st.write("### Total Macros")
                            macro_data = [{
                                "Calories": round(macros["calories"], 1),
                                "Protein (g)": round(macros["protein"], 1),
                                "Carbs (g)": round(macros["carbs"], 1),
                                "Fat (g)": round(macros["fat"], 1),
                                "Fiber (g)": round(macros["fiber"], 1),
                                "Cholesterol (mg)": round(macros["cholesterol"], 1)
                            }]
                            st.dataframe(pd.DataFrame(macro_data))
                        else:
                            st.error("Optimization failed. Check your constraints.")
                    except Exception as e:
                        st.error(f"An error occurred: {str(e)}")
                        if debug_mode:
                            st.code(traceback.format_exc())
            else:
                st.warning("Please add some foods first.")

    # Recipe optimization
    with col2:
        if st.button("Optimize Recipes"):
            if st.session_state.selected_foods:
                with st.spinner("Finding the best recipe..."):
                    try:
                        # Find makeable recipes
                        makeable_recipes = {}
                        for name, recipe_ingredients in ingredients.items():
                            if recipe_is_makeable(recipe_ingredients, st.session_state.selected_foods):
                                makeable_recipes[name] = recipes[name]
                        
                        if debug_mode:
                            st.write("Debug: Makeable Recipes")
                            st.write(makeable_recipes)
                        
                        if makeable_recipes:
                            # Build recipe macros
                            recipe_macros = build_recipe_macros(makeable_recipes, st.session_state.selected_foods)
                            
                            if debug_mode:
                                st.write("Debug: Recipe Macros")
                                st.write(recipe_macros)
                            
                            if recipe_macros:
                                # Optimize recipes
                                result = optimize_recipe_via_api(recipe_macros, goal, min_cal, max_cal)
                                
                                if result:
                                    best_recipe, totals = result
                                    
                                    st.write(f"### Best Recipe: {best_recipe}")
                                    
                                    # Show ingredients
                                    st.write("#### Ingredients")
                                    ingredients_data = []
                                    for ingredient, amount in recipes[best_recipe].items():
                                        # Show the matched ingredient from user's foods
                                        best_match = find_best_match_for_ingredient(ingredient, st.session_state.selected_foods)
                                        matched_food = best_match["name"] if best_match else "Not found"
                                        
                                        ingredients_data.append({
                                            "Recipe Ingredient": ingredient, 
                                            "Amount (g)": amount,
                                            "Matched With": matched_food
                                        })
                                    
                                    st.dataframe(pd.DataFrame(ingredients_data))
                                    
                                    # Show macros
                                    st.write("#### Nutrition Information")
                                    macro_data = [{
                                        "Calories": round(totals.get("calories", 0), 1),
                                        "Protein (g)": round(totals.get("protein", 0), 1),
                                        "Carbs (g)": round(totals.get("carbs", 0), 1),
                                        "Fat (g)": round(totals.get("fat", 0), 1),
                                        "Fiber (g)": round(totals.get("fiber", 0), 1),
                                        "Cholesterol (mg)": round(totals.get("cholesterol", 0), 1)
                                    }]
                                    st.dataframe(pd.DataFrame(macro_data))
                                else:
                                    st.error("Could not find optimal recipe with given constraints.")
                            else:
                                st.warning("Could not calculate recipe macros. Try adding more ingredients.")
                        else:
                            st.warning("No recipes can be made with your selected ingredients. Try adding different foods.")
                    except Exception as e:
                        st.error(f"An error occurred: {str(e)}")
                        if debug_mode:
                            st.code(traceback.format_exc())
            else:
                st.warning("Please add some foods first.")

elif page == "Available Recipes":
    st.write("## Available Recipes")
    st.write("Browse all available recipes to see what you can make with your ingredients.")
    
    # Create tabs for different recipe categories
    categories = {
        "All Recipes": list(recipes.keys()),
        "Breakfast": ["Oatmeal with Berries", "Greek Yogurt Bowl", "Avocado Toast", "Egg Veggie Scramble"],
        "Lunch & Dinner": ["Grilled Chicken Salad", "Beef Rice Bowl", "Turkey Sandwich", "Tofu Stir Fry", 
                          "Salmon & Sweet Potato", "Quinoa Power Bowl", "Mediterranean Plate", "Tuna Salad"],
        "Snacks & Others": ["Protein Smoothie", "Banana Peanut Butter Wrap", "Cottage Cheese with Fruit"]
    }
    
    selected_category = st.selectbox("Filter by category", list(categories.keys()))
    
    # Get recipes for the selected category
    recipe_list = categories[selected_category]
    
    # Display recipes in a grid (3 columns)
    cols = st.columns(3)
    for i, recipe_name in enumerate(recipe_list):
        col_idx = i % 3
        with cols[col_idx]:
            with st.expander(recipe_name, expanded=True):
                # Recipe ingredients
                st.write("#### Ingredients")
                ingredient_data = []
                for ingredient, amount in recipes[recipe_name].items():
                    ingredient_data.append({
                        "Ingredient": ingredient,
                        "Amount (g)": amount
                    })
                st.dataframe(pd.DataFrame(ingredient_data), hide_index=True)
                
                # Calculate approximate macros (assuming standard values for ingredients)
                # This is a simplified calculation - the actual optimizer is more accurate
                st.write("#### Estimated Nutrition (approximate)")
                
                # Sample nutrition values per 100g for common ingredients
                sample_nutrition = {
                    "Chicken": {"protein": 25, "fat": 3, "carbs": 0, "calories": 165},
                    "Beef": {"protein": 26, "fat": 15, "carbs": 0, "calories": 250},
                    "Fish": {"protein": 22, "fat": 12, "carbs": 0, "calories": 200},
                    "Egg": {"protein": 13, "fat": 11, "carbs": 1, "calories": 155},
                    "Vegetables": {"protein": 2, "fat": 0, "carbs": 5, "calories": 30},
                    "Grain": {"protein": 7, "fat": 1, "carbs": 30, "calories": 150},
                    "Dairy": {"protein": 10, "fat": 8, "carbs": 5, "calories": 120},
                    "Fruit": {"protein": 1, "fat": 0, "carbs": 15, "calories": 60},
                    "Nuts": {"protein": 21, "fat": 55, "carbs": 16, "calories": 607},
                    "Oil": {"protein": 0, "fat": 100, "carbs": 0, "calories": 884}
                }
                
                # Map ingredients to categories (simplified)
                def categorize_ingredient(name):
                    name_lower = name.lower()
                    if any(meat in name_lower for meat in ["chicken", "turkey", "beef", "pork"]):
                        return "Chicken" if "chicken" in name_lower else "Beef"
                    elif any(fish in name_lower for fish in ["fish", "salmon", "tuna"]):
                        return "Fish"
                    elif "egg" in name_lower:
                        return "Egg"
                    elif any(veg in name_lower for veg in ["spinach", "lettuce", "broccoli", "tomato", "vegetable", "celery", "onion", "cucumber", "mushroom"]):
                        return "Vegetables"
                    elif any(grain in name_lower for grain in ["rice", "bread", "quinoa", "oat", "cereal", "tortilla"]):
                        return "Grain"
                    elif any(dairy in name_lower for dairy in ["milk", "yogurt", "cheese", "cottage"]):
                        return "Dairy"
                    elif any(fruit in name_lower for fruit in ["fruit", "banana", "strawberry", "blueberry", "peach", "pineapple"]):
                        return "Fruit"
                    elif any(nut in name_lower for nut in ["nut", "almond", "peanut"]):
                        return "Nuts"
                    elif "oil" in name_lower:
                        return "Oil"
                    else:
                        return "Vegetables"  # Default
                
                # Calculate approximate nutrition
                protein = 0
                fat = 0
                carbs = 0
                calories = 0
                
                for ingredient, amount in recipes[recipe_name].items():
                    category = categorize_ingredient(ingredient)
                    nutrition = sample_nutrition[category]
                    
                    # Calculate nutrition based on amount (convert from 100g)
                    ratio = amount / 100
                    protein += nutrition["protein"] * ratio
                    fat += nutrition["fat"] * ratio
                    carbs += nutrition["carbs"] * ratio
                    calories += nutrition["calories"] * ratio
                
                # Display macros
                st.write(f"**Calories:** {round(calories, 1)} kcal")
                st.write(f"**Protein:** {round(protein, 1)}g | **Carbs:** {round(carbs, 1)}g | **Fat:** {round(fat, 1)}g")
                
                # Display recipe tags
                tags = []
                if protein > 20:
                    tags.append("High Protein")
                if fat < 10:
                    tags.append("Low Fat")
                if carbs < 20:
                    tags.append("Low Carb")
                if "chicken" in recipe_name.lower() or "turkey" in recipe_name.lower():
                    tags.append("Poultry")
                if "beef" in recipe_name.lower():
                    tags.append("Beef")
                if "fish" in recipe_name.lower() or "salmon" in recipe_name.lower() or "tuna" in recipe_name.lower():
                    tags.append("Seafood")
                if "vegetable" in recipe_name.lower() or "veggie" in recipe_name.lower():
                    tags.append("Vegetable-Rich")
                if "tofu" in recipe_name.lower():
                    tags.append("Vegetarian")
                
                st.write("**Tags:** " + ", ".join(tags) if tags else "**Tags:** None")

# Add information section
st.sidebar.markdown("""
## About This App
This app helps you optimize your nutrition based on the foods you have available.

### How to use:
1. Search for foods in the USDA database
2. Add them to your selection
3. Set your optimization goal and constraints
4. Click "Optimize Foods" or "Optimize Recipes"

### Ingredient Matching:
The app intelligently matches similar ingredients. For example, if a recipe calls for "tomatoes, cherry" and you have "tomatoes, roma", the app will recognize them as compatible.

### Troubleshooting:
- If you don't see any search results, try general terms like "chicken", "rice", etc.
- If optimization fails, try relaxing your calorie constraints
- If recipes aren't showing up, try adding more varied ingredients
""")