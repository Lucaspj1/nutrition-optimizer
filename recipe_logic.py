from fuzzywuzzy import process
import pandas as pd
import requests

API_KEY = "AwQOO35hr05OR3A6DtOqM1IO6LERLFppuVdpjY2f"

def search_usda_suggestions(query):
    url = "https://api.nal.usda.gov/fdc/v1/foods/search"
    params = {
        "api_key": API_KEY,
        "query": query,
        "dataType": ["Foundation"],
        "pageSize": 10
    }
    response = requests.get(url, params=params)
    if response.status_code == 200:
        results = response.json().get("foods", [])
        return [food["description"] for food in results]
    return []

def search_food(query):
    url = "https://api.nal.usda.gov/fdc/v1/foods/search"
    params = {"api_key": API_KEY, "query": query, "dataType": ["Foundation"], "pageSize": 10}
    r = requests.get(url, params=params).json()
    return [(item["fdcId"], item["description"]) for item in r.get("foods", [])]

def get_nutrition(fdc_id):
    url = f"https://api.nal.usda.gov/fdc/v1/food/{fdc_id}"
    params = {"api_key": API_KEY}
    r = requests.get(url, params=params).json()

    nutrient_id_map = {
        1008: "Calories",
        1003: "Protein (g)",
        1004: "Fat (g)",
        1005: "Carbs (g)",
        1079: "Fiber (g)",
        1253: "Cholesterol (mg)"
    }

    nutrients = {
        "Food": r.get("description", "Unknown"),
        "Calories": 0,
        "Protein (g)": 0,
        "Carbs": 0,
        "Fat": 0,
        "Fiber": 0,
        "Cholesterol (mg)": 0
    }

    for n in r.get("foodNutrients", []):
        nutrient_id = n.get("nutrient", {}).get("id")
        if nutrient_id in nutrient_id_map:
            key = nutrient_id_map[nutrient_id]
            nutrients[key] = n.get("amount", 0)

    return nutrients

def fuzzy_match(ingredient, selected_foods, threshold=70):
    names = [f["Food"] for f in selected_foods]
    result = process.extractOne(ingredient, names)
    if result is None:
        return None
    match, score = result
    return match if score >= threshold else None

def get_macro(food_name, macro, selected_foods):
    match = fuzzy_match(food_name, selected_foods)
    if match:
        for f in selected_foods:
            if f["Food"] == match:
                return f.get(macro, 0)
    return 0

def recipe_is_makeable(recipe_ingredients, selected_foods, threshold=70):
    available = [f["Food"] for f in selected_foods]
    for ingredient in recipe_ingredients:
        result = process.extractOne(ingredient, available)
        if result is None:
            print(f"❌ Not makeable: {recipe_ingredients} with ingredient {ingredient}")
            return False
        match, score = result
        if score < threshold:
            print(f"❌ Not makeable: {recipe_ingredients} with ingredient {ingredient}")
            return False
    return True

def build_recipe_macros(recipes, selected_foods):
    rows = []
    for name, ingredients in recipes.items():
        m = {"Recipe": name, "Calories": 0, "Protein": 0, "Carbs": 0, "Fat": 0, "Fiber": 0, "Cholesterol": 0}
        for food, grams in ingredients.items():
            m["Calories"] += get_macro(food, "Calories", selected_foods) * grams / 100
            m["Protein"]  += get_macro(food, "Protein (g)", selected_foods) * grams / 100
            m["Carbs"]    += get_macro(food, "Carbs (g)", selected_foods) * grams / 100
            m["Fat"]      += get_macro(food, "Fat (g)", selected_foods) * grams / 100
            m["Fiber"]    += get_macro(food, "Fiber (g)", selected_foods) * grams / 100
            m["Cholesterol"] += get_macro(food, "Cholesterol (mg)", selected_foods) * grams / 100
        rows.append(m)
    return pd.DataFrame(rows)

def optimize_recipe_via_api(df_recipes, goal, min_calories=None, max_calories=None):
    try:
        data = {
            "recipes": df_recipes.to_dict(orient="records"),
            "goal": goal,
            "min_calories": min_calories,
            "max_calories": max_calories
        }
        r = requests.post("http://127.0.0.1:5001/optimize-recipe", json=data)
        if r.status_code == 200:
            return r.json().get("best")
        else:
            print("❌ Error from recipe API:", r.text)
            return None
    except Exception as e:
        print("❌ Exception during recipe optimization API call:", e)
        return None