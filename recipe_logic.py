from pyomo.environ import ConcreteModel, Var, Objective, Constraint, NonNegativeReals, SolverFactory, minimize
import numpy as np
import requests

# USDA Nutrient IDs (as constants)
NUTRIENT_IDS = {
    "protein": "1003",
    "fat": "1004",
    "carbs": "1005",
    "fiber": "1079",
    "calories": "1008",
    "cholesterol": "1253"
}

API_KEY = "AwQOO35hr05OR3A6DtOqM1IO6LERLFppuVdpjY2f"

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

def optimize_recipe_via_api(ingredients, recipes, goal, min_calories=None, max_calories=None):
    model = ConcreteModel()

    recipe_names = list(recipes.keys())
    model.x = Var(recipe_names, domain=NonNegativeReals)

    # Objective
    if goal == "maximize_protein":
        model.obj = Objective(expr=sum(model.x[r] * recipes[r]["protein"] for r in recipe_names), sense=-1 * minimize)
    elif goal == "minimize_calories":
        model.obj = Objective(expr=sum(model.x[r] * recipes[r]["calories"] for r in recipe_names), sense=minimize)
    elif goal == "minimize_cholesterol":
        model.obj = Objective(expr=sum(model.x[r] * recipes[r]["cholesterol"] for r in recipe_names), sense=minimize)

    # Calorie bounds
    if min_calories is not None:
        model.min_cal = Constraint(expr=sum(model.x[r] * recipes[r]["calories"] for r in recipe_names) >= min_calories)
    if max_calories is not None:
        model.max_cal = Constraint(expr=sum(model.x[r] * recipes[r]["calories"] for r in recipe_names) <= max_calories)

    solver = SolverFactory('glpk', executable='/opt/homebrew/bin/glpsol')
    result = solver.solve(model)

    output = {
        "status": str(result.solver.status),
        "objective_value": model.obj(),
        "quantities": {r: model.x[r].value for r in recipe_names if model.x[r].value > 0.01},
    }

    return output

# ✅ THIS was missing!
def optimize_food_via_api(foods, goal, min_calories=None, max_calories=None):
    model = ConcreteModel()

    food_names = list(foods.keys())
    model.x = Var(food_names, domain=NonNegativeReals)

    # Objective
    if goal == "maximize_protein":
        model.obj = Objective(expr=sum(model.x[f] * foods[f]["protein"] for f in food_names), sense=-1 * minimize)
    elif goal == "minimize_calories":
        model.obj = Objective(expr=sum(model.x[f] * foods[f]["calories"] for f in food_names), sense=minimize)
    elif goal == "minimize_cholesterol":
        model.obj = Objective(expr=sum(model.x[f] * foods[f]["cholesterol"] for f in food_names), sense=minimize)

    # Calorie bounds
    if min_calories is not None:
        model.min_cal = Constraint(expr=sum(model.x[f] * foods[f]["calories"] for f in food_names) >= min_calories)
    if max_calories is not None:
        model.max_cal = Constraint(expr=sum(model.x[f] * foods[f]["calories"] for f in food_names) <= max_calories)

    solver = SolverFactory('glpk', executable='/opt/homebrew/bin/glpsol')
    result = solver.solve(model)

    output = {
        "status": str(result.solver.status),
        "objective_value": model.obj(),
        "quantities": {f: model.x[f].value for f in food_names if model.x[f].value > 0.01},
    }

    return output