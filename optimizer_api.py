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

    # New: food quantity constraints
    model.constraints = ConstraintList()
    for f in F:
        available = next(item["Available (g)"] for item in foods if item["Food"] == f)
        model.constraints.add(model.x[f] <= available)

    solver = SolverFactory("glpk", executable="/usr/bin/glpsol")
    solver.solve(model)

    result = {f: model.x[f].value for f in F if model.x[f].value and model.x[f].value > 0}
    return jsonify(result)