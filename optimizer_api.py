from flask import Flask, request, jsonify
from pyomo.environ import *
import pandas as pd
import traceback
import os
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# Get port from environment for cloud deployment
port = int(os.environ.get("PORT", 5001))

@app.route('/optimize-foods', methods=['POST'])
def optimize_foods():
    """API endpoint to optimize food combinations"""
    try:
        data = request.json
        foods = data.get("foods", [])
        goal = data.get("goal", "maximize_protein")
        min_cal = data.get("min_calories", 0)
        max_cal = data.get("max_calories", 10000)

        if not foods:
            return jsonify({"error": "No foods provided"}), 400

        # Standardize food keys
        standardized_foods = []
        for food in foods:
            std_food = {
                "name": food.get("name", "Unknown"),
                "calories": float(food.get("calories", 0)),
                "protein": float(food.get("protein", 0)),
                "carbs": float(food.get("carbs", 0)),
                "fat": float(food.get("fat", 0)),
                "fiber": float(food.get("fiber", 0)),
                "cholesterol": float(food.get("cholesterol", 0)),
                "Grams": float(food.get("Grams", 100))
            }
            standardized_foods.append(std_food)

        # Create optimization model
        model = ConcreteModel()
        model.FOODS = range(len(standardized_foods))
        model.x = Var(model.FOODS, domain=NonNegativeReals)

        # Define expressions for each nutrient
        def total_calories(m): 
            return sum(m.x[i] * standardized_foods[i]["calories"] / standardized_foods[i]["Grams"] for i in m.FOODS)
        def total_protein(m): 
            return sum(m.x[i] * standardized_foods[i]["protein"] / standardized_foods[i]["Grams"] for i in m.FOODS)
        def total_fat(m): 
            return sum(m.x[i] * standardized_foods[i]["fat"] / standardized_foods[i]["Grams"] for i in m.FOODS)
        def total_fiber(m): 
            return sum(m.x[i] * standardized_foods[i]["fiber"] / standardized_foods[i]["Grams"] for i in m.FOODS)
        def total_chol(m): 
            return sum(m.x[i] * standardized_foods[i]["cholesterol"] / standardized_foods[i]["Grams"] for i in m.FOODS)

        model.total_calories = Expression(rule=total_calories)
        model.total_protein = Expression(rule=total_protein)
        model.total_fat = Expression(rule=total_fat)
        model.total_fiber = Expression(rule=total_fiber)
        model.total_chol = Expression(rule=total_chol)

        # Calorie constraint
        model.cal_lb = Constraint(expr=model.total_calories >= min_cal)
        model.cal_ub = Constraint(expr=model.total_calories <= max_cal)

        # Food quantity constraints
        for i in model.FOODS:
            model.add_component(
                f'limit_{i}', 
                Constraint(expr=model.x[i] <= standardized_foods[i]["Grams"])
            )

        # Set objective based on goal
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
        else:
            return jsonify({"error": f"Unknown goal: {goal}"}), 400

        # Try different solver paths based on environment
        try:
            # First try without specifying path
            solver = SolverFactory("glpk")
        except:
            # Try with common paths
            paths = [
                "glpsol",                      # PATH environment
                "/usr/bin/glpsol",             # Linux common path
                "/opt/homebrew/bin/glpsol",    # Mac Homebrew
                "/app/.apt/usr/bin/glpsol"     # Heroku apt buildpack
            ]
            
            for path in paths:
                try:
                    solver = SolverFactory("glpk", executable=path)
                    logger.info(f"Found GLPK solver at {path}")
                    break
                except:
                    continue
            else:
                # If we get here, no solver was found
                return jsonify({"error": "Could not find a valid GLPK solver. Make sure it's installed."}), 500

        # Solve the model
        results = solver.solve(model)

        if results.solver.status != SolverStatus.ok:
            return jsonify({"error": f"Solver error: {results.solver.status}"}), 500

        # Collect results
        result = []
        servings = {}
        macros = {
            "calories": 0,
            "protein": 0,
            "carbs": 0,
            "fat": 0,
            "fiber": 0,
            "cholesterol": 0
        }

        for i in model.FOODS:
            grams = value(model.x[i])
            if grams and grams > 0.01:  # Only include meaningful amounts
                food = standardized_foods[i]
                item = food.copy()
                item["Optimized (g)"] = round(grams, 2)
                result.append(item)
                
                # Add to servings dictionary for the response
                servings[food["name"]] = round(grams, 2)
                
                # Calculate contribution to total macros
                ratio = grams / food["Grams"]
                for macro in macros:
                    macros[macro] += food[macro] * ratio

        # Round macro values
        for macro in macros:
            macros[macro] = round(macros[macro], 2)

        return jsonify({
            "result": result,
            "servings": servings,
            "macros": macros
        })
        
    except Exception as e:
        logger.error(f"Error in optimize_foods: {str(e)}")
        logger.error(traceback.format_exc())
        return jsonify({
            "error": str(e),
            "traceback": traceback.format_exc()
        }), 500

@app.route('/optimize-recipe', methods=['POST'])
def optimize_recipe():
    """API endpoint to find the optimal recipe"""
    try:
        data = request.json
        recipes = data.get("recipes", [])
        goal = data.get("goal", "maximize_protein")
        min_cal = data.get("min_calories", 0)
        max_cal = data.get("max_calories", 10000)
        
        if not recipes:
            return jsonify({"error": "No recipes provided"}), 400

        # Convert to DataFrame for easier handling
        df = pd.DataFrame(recipes)
        
        # Create optimization model
        model = ConcreteModel()
        model.I = range(len(df))
        model.x = Var(model.I, domain=Binary)

        # Define nutrient expressions
        def total_calories(m): 
            return sum(m.x[i] * df.iloc[i].get("calories", 0) for i in m.I)
        def total_protein(m): 
            return sum(m.x[i] * df.iloc[i].get("protein", 0) for i in m.I)
        def total_fiber(m): 
            return sum(m.x[i] * df.iloc[i].get("fiber", 0) for i in m.I)
        def total_fat(m): 
            return sum(m.x[i] * df.iloc[i].get("fat", 0) for i in m.I)
        def total_chol(m): 
            return sum(m.x[i] * df.iloc[i].get("cholesterol", 0) for i in m.I)

        model.total_calories = Expression(rule=total_calories)
        model.total_protein = Expression(rule=total_protein)
        model.total_fat = Expression(rule=total_fat)
        model.total_fiber = Expression(rule=total_fiber)
        model.total_chol = Expression(rule=total_chol)

        # Add constraint: only select one recipe
        model.only_one = Constraint(expr=sum(model.x[i] for i in model.I) == 1)
        
        # Add calorie constraints
        model.cal_lb = Constraint(expr=model.total_calories >= min_cal)
        model.cal_ub = Constraint(expr=model.total_calories <= max_cal)

        # Set objective based on goal
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
        else:
            return jsonify({"error": f"Unknown goal: {goal}"}), 400

        # Try different solver paths based on environment
        try:
            # First try without specifying path
            solver = SolverFactory("glpk")
        except:
            # Try with common paths
            paths = [
                "glpsol",                      # PATH environment
                "/usr/bin/glpsol",             # Linux common path
                "/opt/homebrew/bin/glpsol",    # Mac Homebrew
                "/app/.apt/usr/bin/glpsol"     # Heroku apt buildpack
            ]
            
            for path in paths:
                try:
                    solver = SolverFactory("glpk", executable=path)
                    logger.info(f"Found GLPK solver at {path}")
                    break
                except:
                    continue
            else:
                # If we get here, no solver was found
                return jsonify({"error": "Could not find a valid GLPK solver. Make sure it's installed."}), 500

        # Solve the model
        results = solver.solve(model)
        
        if results.solver.status != SolverStatus.ok:
            return jsonify({"error": f"Solver error: {results.solver.status}"}), 500

        # Get selected recipe
        for i in model.I:
            if value(model.x[i]) > 0.5:  # Binary variable > 0.5 means selected
                selected_recipe = df.iloc[i].to_dict()
                return jsonify({
                    "best": selected_recipe,
                    "recipe_name": selected_recipe.get("Recipe"),
                    "macros": {
                        "calories": round(selected_recipe.get("calories", 0), 2),
                        "protein": round(selected_recipe.get("protein", 0), 2),
                        "carbs": round(selected_recipe.get("carbs", 0), 2),
                        "fat": round(selected_recipe.get("fat", 0), 2),
                        "fiber": round(selected_recipe.get("fiber", 0), 2),
                        "cholesterol": round(selected_recipe.get("cholesterol", 0), 2)
                    }
                })

        return jsonify({"error": "No recipe selected"}), 404
        
    except Exception as e:
        logger.error(f"Error in optimize_recipe: {str(e)}")
        logger.error(traceback.format_exc())
        return jsonify({
            "error": str(e),
            "traceback": traceback.format_exc()
        }), 500

@app.route('/health', methods=['GET'])
def health_check():
    """Simple health check endpoint"""
    return jsonify({"status": "UP"})

if __name__ == "__main__":
    # Use host 0.0.0.0 to make the API accessible from other machines
    app.run(host="0.0.0.0", port=port, debug=True)