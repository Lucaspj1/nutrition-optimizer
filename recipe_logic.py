import requests
import difflib
from pyomo.environ import *
from collections import defaultdict

USDA_API_KEY = "AwQOO35hr05OR3A6DtOqM1IO6LERLFppuVdpjY2f"
USDA_BASE_URL = "https://api.nal.usda.gov/fdc/v1/foods/search"

NUTRIENT_IDS = {
    "protein": 1003,
    "fat": 1004,
    "carbs": 1005,
    "fiber": 1079,
    "calories": 1008,
    "cholesterol": 1253
}

def get_nutrition(food_name):
    params = {
        "api_key": USDA_API_KEY,
        "query": food_name,
        "pageSize": 1,
        "dataType": ["Foundation"]
    }
    response = requests.get(USDA_BASE_URL, params=params)
    if response.status_code != 200 or not response.json().get("foods"):
        return None

    food = response.json()["foods"][0]
    food_nutrients = {nutrient["nutrientId"]: nutrient["value"] for nutrient in food["foodNutrients"]}

    return {
        "name": food["description"],
        "protein": food_nutrients.get(NUTRIENT_IDS["protein"], 0),
        "fat": food_nutrients.get(NUTRIENT_IDS["fat"], 0),
        "carbs": food_nutrients.get(NUTRIENT_IDS["carbs"], 0),
        "fiber": food_nutrients.get(NUTRIENT_IDS["fiber"], 0),
        "calories": food_nutrients.get(NUTRIENT_IDS["calories"], 0),
        "cholesterol": food_nutrients.get(NUTRIENT_IDS["cholesterol"], 0),
        "Grams": 100  # always assume 100g default reference from USDA
    }

def search_usda_suggestions(query):
    response = requests.get(USDA_BASE_URL, params={
        "query": query,
        "api_key": USDA_API_KEY,
        "pageSize": 25,
        "dataType": ["Foundation"]
    })
    if response.status_code != 200:
        return []

    descriptions = [food["description"] for food in response.json().get("foods", [])]
    return difflib.get_close_matches(query, descriptions, n=5, cutoff=0.1)

def optimize_food_via_api(foods, goal, min_calories=None, max_calories=None):
    model = ConcreteModel()
    model.Foods = range(len(foods))
    model.Quantity = Var(model.Foods, domain=NonNegativeReals)

    def nutrient_sum(nutrient):
        return sum(foods[i][nutrient] * model.Quantity[i] / 100 for i in model.Foods)

    if goal == "maximize_protein":
        model.Objective = Objective(expr=-nutrient_sum("protein"))
    elif goal == "minimize_fat":
        model.Objective = Objective(expr=nutrient_sum("fat"))
    elif goal == "minimize_cholesterol":
        model.Objective = Objective(expr=nutrient_sum("cholesterol"))
    elif goal == "minimize_calories":
        model.Objective = Objective(expr=nutrient_sum("calories"))
    elif goal == "maximize_fiber":
        model.Objective = Objective(expr=-nutrient_sum("fiber"))
    else:
        raise ValueError("Unknown optimization goal")

    if min_calories:
        model.MinCal = Constraint(expr=nutrient_sum("calories") >= min_calories)
    if max_calories:
        model.MaxCal = Constraint(expr=nutrient_sum("calories") <= max_calories)

    for i in model.Foods:
        model.add_component(f"limit_{i}", Constraint(expr=model.Quantity[i] <= foods[i].get("Grams", 0)))

    solver = SolverFactory("glpk", executable="/opt/homebrew/bin/glpsol")
    solver.solve(model)

    servings = {foods[i]["name"]: round(value(model.Quantity[i]), 2) for i in model.Foods}
    macros = {
        nutrient: round(sum(value(model.Quantity[i]) * foods[i][nutrient] / 100 for i in model.Foods), 2)
        for nutrient in ["protein", "carbs", "fat", "fiber", "calories", "cholesterol"]
    }

    return servings, macros

def build_recipe_macros(recipe_dict, selected_ingredients):
    df = []
    for name, ingr_dict in recipe_dict.items():
        total = defaultdict(float)
        for ingr, amount in ingr_dict.items():
            match = next((f for f in selected_ingredients if ingr.lower() in f["name"].lower()), None)
            if match:
                for macro in ["protein", "carbs", "fat", "fiber", "calories", "cholesterol"]:
                    total[macro] += match.get(macro, 0) * (amount / 100)
        total["Recipe"] = name
        df.append(total)
    return df

def optimize_recipe_via_api(df, goal, min_calories=None, max_calories=None):
    model = ConcreteModel()
    model.I = range(len(df))
    model.x = Var(model.I, domain=Binary)

    def macro_sum(macro):
        return sum(df[i][macro] * model.x[i] for i in model.I)

    if goal == "maximize_protein":
        model.obj = Objective(expr=-macro_sum("protein"))
    elif goal == "minimize_fat":
        model.obj = Objective(expr=macro_sum("fat"))
    elif goal == "minimize_cholesterol":
        model.obj = Objective(expr=macro_sum("cholesterol"))
    elif goal == "minimize_calories":
        model.obj = Objective(expr=macro_sum("calories"))
    elif goal == "maximize_fiber":
        model.obj = Objective(expr=-macro_sum("fiber"))

    model.only_one = Constraint(expr=sum(model.x[i] for i in model.I) == 1)
    if min_calories:
        model.min_cals = Constraint(expr=macro_sum("calories") >= min_calories)
    if max_calories:
        model.max_cals = Constraint(expr=macro_sum("calories") <= max_calories)

    solver = SolverFactory("glpk", executable="/opt/homebrew/bin/glpsol")
    solver.solve(model)

    for i in model.I:
        if value(model.x[i]) > 0.5:
            return df[i]
    return None

def recipe_is_makeable(recipe_ingredients, selected_foods):
    selected_names = [f["name"].lower() for f in selected_foods]
    return all(any(ingr.lower() in name for name in selected_names) for ingr in recipe_ingredients)