import requests
from fuzzywuzzy import process

# === Constants ===
API_KEY = "AwQOO35hr05OR3A6DtOqM1IO6LERLFppuVdpjY2f"
NUTRIENT_IDS = {
    "protein": "1003",
    "fat": "1004",
    "carbs": "1005",
    "fiber": "1079",
    "calories": "1008",
    "cholesterol": "1253"
}

# === Helper to get macros from USDA API ===
def get_nutrition(food_id):
    url = f"https://api.nal.usda.gov/fdc/v1/food/{food_id}?api_key={API_KEY}"
    response = requests.get(url)
    data = response.json()

    nutrients = {key: 0 for key in NUTRIENT_IDS}

    for item in data.get("foodNutrients", []):
        for macro, macro_id in NUTRIENT_IDS.items():
            if str(item.get("nutrient", {}).get("id")) == macro_id:
                nutrients[macro] = item.get("amount", 0)

    return nutrients

# === Macro breakdown builder ===
def build_recipe_macros(recipe, ingredients_data):
    macros = {key: 0 for key in NUTRIENT_IDS}
    for ingredient in recipe["ingredients"]:
        food_id = ingredient["id"]
        quantity = ingredient["grams"]
        food_macros = ingredients_data.get(food_id, {})

        for macro in macros:
            macros[macro] += food_macros.get(macro, 0) * (quantity / 100)

    return macros

# === Recipe optimizer placeholder ===
def optimize_recipe_via_api(ingredients, goal, min_calories=None, max_calories=None):
    # Placeholder for recipe selection logic
    # Returns a hardcoded match for now
    if not ingredients:
        return None

    return {
        "name": "Beef Rice Bowl",
        "ingredients": ingredients
    }

# === Food optimizer placeholder ===
def optimize_food_via_api(ingredients, goal, min_calories=None, max_calories=None):
    # Placeholder for optimization logic
    return ingredients