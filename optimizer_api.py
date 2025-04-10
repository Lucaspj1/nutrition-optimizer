from flask import Flask, request, jsonify
from pyomo.environ import *

app = Flask(__name__)

@app.route("/optimize-foods", methods=["POST"])
def optimize_foods():
    data = request.json
    foods = data["foods"]
    goal = data["goal"]

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

    macro, sense = goal_map[goal]
    model.obj = Objective(expr=sum(model.x[f] * next(item[macro] for item in foods if item["Food"] == f) / 100 for f in F), sense=sense)
    model.total_weight = Constraint(expr=sum(model.x[f] for f in F) <= 500)

    solver = SolverFactory("glpk", executable="/usr/bin/glpsol")
    solver.solve(model)

    result = {f: model.x[f].value for f in F if model.x[f].value and model.x[f].value > 0}
    return jsonify(result)


@app.route("/optimize-recipe", methods=["POST"])
def optimize_recipe():
    data = request.json
    df = data["df"]
    goal = data["goal"]

    model = ConcreteModel()
    R = [row["Recipe"] for row in df]
    model.R = Set(initialize=R)
    model.x = Var(model.R, domain=Binary)
    model.only_one = Constraint(expr=sum(model.x[r] for r in R) == 1)

    goal_map = {
        "maximize_protein": ("Protein", maximize),
        "minimize_carbs": ("Carbs", minimize),
        "minimize_calories": ("Calories", minimize),
        "maximize_fiber": ("Fiber", maximize)
    }

    macro, sense = goal_map[goal]
    recipe_macros = {row["Recipe"]: row[macro] for row in df}

    model.obj = Objective(expr=sum(model.x[r] * recipe_macros[r] for r in R), sense=sense)
    solver = SolverFactory("glpk", executable="/usr/bin/glpsol")
    solver.solve(model)

    selected = [r for r in R if model.x[r].value == 1]
    return jsonify({"recipe": selected[0]})


if __name__ == "__main__":
    app.run(port=5001)