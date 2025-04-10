from fuzzywuzzy import process
import pandas as pd
import requests
from pyomo.environ import *

API_KEY = "AwQOO35hr05OR3A6DtOqM1IO6LERLFppuVdpjY2f"

def search_food(query):
    url = "https://api.nal.usda.gov/fdc/v1/foods/search"
    params = {"api_key": API_KEY, "query": query, "dataType": ["Foundation"], "pageSize": 1}
    r = requests.get(url, params=params).json()
    if not r.get("foods"):
        return None
    food = r["foods"][0]
    return food["fdcId"], food["description"]

def search_usda_suggestions(query, limit=15):
    url = "https://api.nal.usda.gov/fdc/v1/foods/search"
    params = {
        "api_key": API_KEY,
        "query": query,
        "dataType": ["Foundation"],
        "pageSize": 100
    }
    try:
        r = requests.get(url, params=params).json()
        all_foods = [food["description"] for food in r.get("foods", [])]
        matches = process.extract(query, all_foods, limit=limit)
        return [match[0] for match in matches if match[1] >= 50]
    except:
        return []

def get_nutrition(fdc_id):
    url = f"https://api.nal.usda.gov/fdc/v1/food/{fdc_id}"
    params = {"api_key": API_KEY}
    r = requests.get(url, params=params).json()

    nutrients = {
        "Food": r.get("description", "Unknown"),
        "Calories": 0,
        "Protein (g)": 0,
        "Carbs (g)": 0,
        "Fat (g)": 0,
        "Fiber (g)": 0
    }

    for n in r.get("foodNutrients", []):
        name = n.get("nutrient", {}).get("name", "").lower()
        amt = n.get("amount", 0)
        if "energy" in name:
            nutrients["Calories"] = amt
        elif "protein" in name:
            nutrients["Protein (g)"] = amt
        elif "carbohydrate" in name:
            nutrients["Carbs (g)"] = amt
        elif "fat" in name and "total" in name:
            nutrients["Fat (g)"] = amt
        elif "fiber" in name:
            nutrients["Fiber (g)"] = amt

    return nutrients

def fuzzy_match(ingredient, selected_foods, threshold=70):
    names = [f["Food"] for f in selected_foods]
    match, score = process.extractOne(ingredient, names)
    print(f"Matching '{ingredient}' to → '{match}' (score: {score})")
    return match if score >= threshold else None

def recipe_is_makeable(recipe_ingredients, selected_foods, threshold=70):
    available = [f["Food"] for f in selected_foods]
    for ingredient in recipe_ingredients:
        match, score = process.extractOne(ingredient, available)
        print(f"Matching '{ingredient}' to → '{match}' (score: {score})")
        if score < threshold:
            return False
    return True

def build_recipe_macros(recipes, selected_foods):
    rows = []
    for name, ingredients in recipes.items():
        m = {"Recipe": name, "Calories": 0, "Protein": 0, "Carbs": 0, "Fat": 0, "Fiber": 0}
        for food, grams in ingredients.items():
            m["Calories"] += get_macro(food, "Calories", selected_foods) * grams / 100
            m["Protein"]  += get_macro(food, "Protein (g)", selected_foods) * grams / 100
            m["Carbs"]    += get_macro(food, "Carbs (g)", selected_foods) * grams / 100
            m["Fat"]      += get_macro(food, "Fat (g)", selected_foods) * grams / 100
            m["Fiber"]    += get_macro(food, "Fiber (g)", selected_foods) * grams / 100
        rows.append(m)
    return pd.DataFrame(rows)

def get_macro(food_name, macro, selected_foods):
    match = fuzzy_match(food_name, selected_foods)
    if match:
        for f in selected_foods:
            if f["Food"] == match:
                return f.get(macro, 0)
    return 0

def optimize_recipe_via_api(df, goal):
    try:
        json_rows = df.to_dict(orient="records")
        print("🔄 Sending to API:", json_rows)
        r = requests.post("http://127.0.0.1:5001/optimize-recipe", json={"df": json_rows, "goal": goal})
        print("✅ Response from API:", r.text)
        return r.json().get("recipe") if r.status_code == 200 else None
    except Exception as e:
        print("❌ Recipe API Error:", e)
        return None