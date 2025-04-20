from pyomo.environ import ConcreteModel, Var, Objective, Constraint, NonNegativeReals, SolverFactory, minimize
import numpy as np

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