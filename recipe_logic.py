import requests
import difflib
from pyomo.environ import *

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
    nutrients = {n["nutrientId"]: n["value"] for n in food.get("foodNutrients", [])}

    return {
        "name": food["description"],
        "protein": nutrients.get(NUTRIENT_IDS["protein"], 0),
        "fat": nutrients.get(NUTRIENT_IDS["fat"], 0),
        "carbs": nutrients.get(NUTRIENT_IDS["carbs"], 0),
        "fiber": nutrients.get(NUTRIENT_IDS["fiber"], 0),
        "calories": nutrients.get(NUTRIENT_IDS["calories"], 0),
        "cholesterol": nutrients.get(NUTRIENT_IDS["cholesterol"], 0)
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

    def macro_sum(macro):
        return sum(foods[i][macro] * model.Quantity[i] for i in model.Foods)

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
    else:
        raise ValueError("Unknown goal")

    if min_calories is not None:
        model.min_cal = Constraint(expr=macro_sum("calories") >= min_calories)
    if max_calories is not None:
        model.max_cal = Constraint(expr=macro_sum("calories") <= max_calories)

    for i in model.Foods:
        model.add_component(f"limit_{i}", Constraint(expr=model.Quantity[i] <= foods[i].get("Grams", 100)))

    solver = SolverFactory("glpk", executable="/opt/homebrew/bin/glpsol")
    solver.solve(model)

    servings = {foods[i]["name"]: round(model.Quantity[i].value, 2) for i in model.Foods}
    macros = {
        macro: round(sum(model.Quantity[i].value * foods[i][macro] for i in model.Foods), 2)
        for macro in ["protein", "fat", "carbs", "fiber", "calories", "cholesterol"]
    }

    return servings, macros