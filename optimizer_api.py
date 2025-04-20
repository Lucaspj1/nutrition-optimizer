from flask import Flask, request, jsonify
from pyomo.environ import *
import pandas as pd

app = Flask(__name__)

@app.route('/optimize-foods', methods=['POST'])
def optimize_foods():
    data = request.json
    foods = data["foods"]
    goal = data["goal"]
    min_cal = data.get("min_calories", 0)
    max_cal = data.get("max_calories", 10000)

    model = ConcreteModel()
    model.FOODS = RangeSet(0, len(foods)-1)
    model.x = Var(model.FOODS, domain=NonNegativeReals)

    def total_calories(m): return sum(m.x[i] * foods[i]["Calories"] / 100 for i in m.FOODS)
    def total_protein(m): return sum(m.x[i] * foods[i]["Protein (g)"] / 100 for i in m.FOODS)
    def total_fat(m): return sum(m.x[i] * foods[i]["Fat (g)"] / 100 for i in m.FOODS)
    def total_fiber(m): return sum(m.x[i] * foods[i]["Fiber (g)"] / 100 for i in m.FOODS)
    def total_chol(m): return sum(m.x[i] * foods[i]["Cholesterol (mg)"] / 100 for i in m.FOODS)

    model.total_calories = Expression(rule=total_calories)
    model.total_protein = Expression(rule=total_protein)
    model.total_fat = Expression(rule=total_fat)
    model.total_fiber = Expression(rule=total_fiber)
    model.total_chol = Expression(rule=total_chol)

    # Calorie constraint
    model.cal_lb = Constraint(expr=model.total_calories >= min_cal)
    model.cal_ub = Constraint(expr=model.total_calories <= max_cal)

    for i in model.FOODS:
        model.add_component(f'limit_{i}', Constraint(expr=model.x[i] <= foods[i].get("Grams", 0)))

    if goal == "maximize_protein":
        model.obj = Objective(expr=model.total_protein, sense=maximize)
    elif goal == "minimize_calories":
        model.obj = Objective(expr=model.total_calories, sense=minimize)
    elif goal == "minimize_fat":
        model.obj = Objective(expr=model.total_fat, sense=minimize)
    elif goal == "maximize_fiber":
        model.obj = Objective(expr=model.total_fiber, sense=maximize)
    elif goal == "minimize_cholesterol":
        model.obj = Objective(expr=model.total_chol, sense=minimize)

    solver = SolverFactory('glpk', executable='/opt/homebrew/bin/glpsol')
    results = solver.solve(model)

    result = []
    for i in model.FOODS:
        grams = model.x[i].value
        if grams and grams > 0:
            item = foods[i].copy()
            item["Optimized (g)"] = round(grams, 2)
            result.append(item)

    return jsonify({"result": result})

@app.route('/optimize-recipe', methods=['POST'])
def optimize_recipe():
    data = request.json
    df = pd.DataFrame(data["recipes"])
    goal = data["goal"]
    min_cal = data.get("min_calories", 0)
    max_cal = data.get("max_calories", 10000)

    model = ConcreteModel()
    model.I = RangeSet(0, len(df) - 1)
    model.x = Var(model.I, domain=Binary)

    def total_calories(m): return sum(m.x[i] * df.iloc[i]["Calories"] for i in m.I)
    def total_protein(m): return sum(m.x[i] * df.iloc[i]["Protein"] for i in m.I)
    def total_fiber(m): return sum(m.x[i] * df.iloc[i]["Fiber"] for i in m.I)
    def total_fat(m): return sum(m.x[i] * df.iloc[i]["Fat"] for i in m.I)
    def total_chol(m): return sum(m.x[i] * df.iloc[i]["Cholesterol"] for i in m.I)

    model.total_calories = Expression(rule=total_calories)
    model.total_protein = Expression(rule=total_protein)
    model.total_fat = Expression(rule=total_fat)
    model.total_fiber = Expression(rule=total_fiber)
    model.total_chol = Expression(rule=total_chol)

    model.only_one = Constraint(expr=sum(model.x[i] for i in model.I) == 1)
    model.cal_lb = Constraint(expr=model.total_calories >= min_cal)
    model.cal_ub = Constraint(expr=model.total_calories <= max_cal)

    if goal == "maximize_protein":
        model.obj = Objective(expr=model.total_protein, sense=maximize)
    elif goal == "minimize_calories":
        model.obj = Objective(expr=model.total_calories, sense=minimize)
    elif goal == "minimize_fat":
        model.obj = Objective(expr=model.total_fat, sense=minimize)
    elif goal == "maximize_fiber":
        model.obj = Objective(expr=model.total_fiber, sense=maximize)
    elif goal == "minimize_cholesterol":
        model.obj = Objective(expr=model.total_chol, sense=minimize)

    solver = SolverFactory('glpk', executable='/opt/homebrew/bin/glpsol')
    solver.solve(model)

    for i in model.I:
        if model.x[i].value > 0.5:
            return jsonify({"best": df.iloc[i].to_dict()})

    return jsonify({"error": "No recipe selected"})

if __name__ == "__main__":
    app.run(port=5001)