from flask import Flask, request, jsonify
from pyomo.environ import *
import pandas as pd

app = Flask(__name__)

@app.route("/optimize-recipe", methods=["POST"])
def optimize_recipe():
    data = request.json
    recipes = data["recipes"]
    goal = data["goal"]
    min_cal = data.get("min_calories", 0)
    max_cal = data.get("max_calories", float("inf"))

    model = ConcreteModel()
    n = len(recipes)
    model.x = Var(range(n), domain=Binary)

    model.constraints = ConstraintList()
    model.constraints.add(sum(model.x[i] for i in range(n)) == 1)
    model.constraints.add(sum(model.x[i] * recipes[i]["Calories"] for i in range(n)) >= min_cal)
    model.constraints.add(sum(model.x[i] * recipes[i]["Calories"] for i in range(n)) <= max_cal)

    if goal == "maximize_protein":
        model.obj = Objective(expr=sum(model.x[i] * recipes[i]["Protein"] for i in range(n)), sense=maximize)
    elif goal == "minimize_cholesterol":
        model.obj = Objective(expr=sum(model.x[i] * recipes[i]["Cholesterol"] for i in range(n)), sense=minimize)
    else:
        return jsonify({"error": "Unknown goal"}), 400

    solver = SolverFactory('glpk', executable='/opt/homebrew/bin/glpsol')
    result = solver.solve(model)

    if result.solver.status == SolverStatus.ok and result.solver.termination_condition == TerminationCondition.optimal:
        for i in range(n):
            if model.x[i].value == 1:
                return jsonify({"best": recipes[i]})
    return jsonify({"error": "No optimal solution"}), 400

if __name__ == "__main__":
    app.run(port=5001)