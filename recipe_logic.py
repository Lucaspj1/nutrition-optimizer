from fuzzywuzzy import process
import pandas as pd
import requests
from pyomo.environ import *

API_KEY = "YOUR_USDA_API_KEY"  # Replace with your actual USDA key

# Fuzzy USDA food suggestions (live dropdown)
def search_usda_suggestions(query, limit=15):
    url = "https://api.nal.usda.gov/fdc/v1/foods/search"
    params = {
        "api_key": API_KEY,
        "query": query,
        "dataType": ["Foundation"],
        "pageSize": 50
    }
    try:
        r = requests.get(url, params=params).json()
        all_foods = [food["description"] for food in r.get("foods", [])]
        matches = process.extract(query, all_foods, limit=limit)
        return [match[0] for match in matches if match[1] >= 60]
    except:
        return []

def search_food(query):
    url = "https://api.nal.usda.gov/fdc/v1/foods/search"
    params = {"api_key": API_KEY, "query": query, "dataType": ["Foundation"], "pageSize": 1}
    r = requests.get(url, params=params).json()
    if not r.get("foods"):
        return None
    food = r["foods"][0]
    return food["fdcId"], food["description"]

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
    return match if score >= threshold else None

def get_macro(food_name, macro, selected_foods):
    match = fuzzy_match(food_name, selected_foods)
    if match:
        for f in selected_foods:
            if f["Food"] == match:
                return f.get(macro, 0)
    return 0

def recipe_is_makeable(recipe_ingredients, selected_foods, threshold=70):
    if not selected_foods:
        return False
    available = [f["Food"] for f in selected_foods if "Food" in f]
    for ingredient in recipe_ingredients:
        result = process.extractOne(ingredient, available)
        if not result or result[1] < threshold:
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

def optimize_recipes_by_goal(df, goal_type):
    model = ConcreteModel()
    R = list(df["Recipe"])
    model.R = Set(initialize=R)
    model.x = Var(model.R, domain=Binary)
    model.only_one = Constraint(expr=sum(model.x[r] for r in R) == 1)

    goal_map = {
        "maximize_protein": ("Protein", maximize),
        "minimize_carbs": ("Carbs", minimize),
        "minimize_calories": ("Calories", minimize),
        "maximize_fiber": ("Fiber", maximize)
    }

    macro, sense = goal_map[goal_type]
    model.obj = Objective(expr=sum(model.x[r] * df[df["Recipe"] == r][macro].values[0] for r in R), sense=sense)

    solver = SolverFactory("glpk", executable="/usr/bin/glpsol")
    solver.solve(model)

    selected = [r for r in R if model.x[r].value == 1]
    return selected[0]

def optimize_food_quantities(foods, goal_type):
    if not foods:
        return None

    model = ConcreteModel()
    F = [f["Food"] for f in foods]
    model.F = Set(initialize=F)
    model.x = Var(model.F, domain=NonNegativeReals)

    goal_map = {
        "maximize_protein": ("Protein (g)", maximize),
        "minimize_carbs": ("Carbs (g)", minimize),
        "minimize_calories": ("Calories", minimize),
        "maximize_fiber": ("Fiber (g)", maximize)
    }

    macro, sense = goal_map[goal_type]
    model.obj = Objective(expr=sum(model.x[f] * next(item[macro] for item in foods if item["Food"] == f) / 100 for f in F), sense=sense)

    model.total_weight = Constraint(expr=sum(model.x[f] for f in F) <= 500)  # 500g daily max

    solver = SolverFactory("glpk", executable="/usr/bin/glpsol")
    solver.solve(model)

    return {f: model.x[f].value for f in F if model.x[f].value > 0}