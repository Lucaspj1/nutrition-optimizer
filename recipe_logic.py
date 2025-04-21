import requests
import difflib
from collections import defaultdict
from pyomo.environ import *

USDA_API_KEY = "AwQOO35hr05OR3A6DtOqM1IO6LERLFppuVdpjY2f"
USDA_BASE_URL = "https://api.nal.usda.gov/fdc/v1/foods/search"
USDA_FOOD_URL = "https://api.nal.usda.gov/fdc/v1/food/"

# Updated nutrient IDs 
NUTRIENT_IDS = {
    "protein": 1003,
    "fat": 1004,
    "carbs": 1005,
    "fiber": 1079,
    "calories": 1008,
    "cholesterol": 1253
}

# Standard keys 
STANDARD_KEYS = ["name", "protein", "fat", "carbs", "fiber", "calories", "cholesterol"]

def search_usda_suggestions(query):
    """Search for food suggestions in the USDA database"""
    if not query or len(query.strip()) < 2:
        return []
    
    params = {
        "query": query,
        "api_key": USDA_API_KEY,
        "pageSize": 10,
        "dataType": ["Foundation"]
    }
    
    try:
        response = requests.get(USDA_BASE_URL, params=params)
        response.raise_for_status()  
        foods = response.json().get("foods", [])
        return [{"name": food["description"], "fdcId": food["fdcId"]} for food in foods]
    except Exception as e:
        print(f"Error searching foods: {e}")
        return []

def get_nutrition(fdc_id):
    """Get nutrition info for a specific food by FDC ID"""
    url = f"{USDA_FOOD_URL}{fdc_id}"
    params = {"api_key": USDA_API_KEY}
    
    try:
        r = requests.get(url, params=params)
        r.raise_for_status()
        data = r.json()
    except Exception as e:
        print(f"Error fetching food data: {e}")
        return None
    
    nutrients = {
        "name": data.get("description", "Unknown"),
        "calories": 0,
        "protein": 0,
        "carbs": 0,
        "fat": 0,
        "fiber": 0,
        "cholesterol": 0
    }
    
    #Nutrient mapping
    for n in data.get("foodNutrients", []):
        nutrient_name = n.get("nutrient", {}).get("name", "").lower()
        nutrient_id = n.get("nutrient", {}).get("id")
        amount = n.get("amount", 0)
        
        # Match by nutrient ID first 
        if nutrient_id == NUTRIENT_IDS["calories"]:
            nutrients["calories"] = amount
        elif nutrient_id == NUTRIENT_IDS["protein"]:
            nutrients["protein"] = amount
        elif nutrient_id == NUTRIENT_IDS["carbs"]:
            nutrients["carbs"] = amount
        elif nutrient_id == NUTRIENT_IDS["fat"]:
            nutrients["fat"] = amount
        elif nutrient_id == NUTRIENT_IDS["fiber"]:
            nutrients["fiber"] = amount
        elif nutrient_id == NUTRIENT_IDS["cholesterol"]:
            nutrients["cholesterol"] = amount
        # Fallback to name-based matching
        elif "energy" in nutrient_name and "kcal" in n.get("nutrient", {}).get("unitName", "").lower():
            nutrients["calories"] = amount
        elif "protein" in nutrient_name:
            nutrients["protein"] = amount
        elif "carbohydrate" in nutrient_name and "total" in nutrient_name:
            nutrients["carbs"] = amount
        elif "total lipid" in nutrient_name or ("fat" in nutrient_name and "total" in nutrient_name):
            nutrients["fat"] = amount
        elif "fiber" in nutrient_name:
            nutrients["fiber"] = amount
        elif "cholesterol" in nutrient_name:
            nutrients["cholesterol"] = amount
    
    return nutrients

def extract_base_food_name(food_name):
    """Extract the basic/generic food type from a specific food name"""
    if not food_name:
        return ""
        
    # Convert to lowercase
    name = food_name.lower()
    
    # Split by commas and take first part of item
    base_name = name.split(',')[0].strip()
    
    # Expanded list of descriptors to filter out
    descriptors = [
        'raw', 'cooked', 'fresh', 'frozen', 'canned', 'dried', 'ripe', 
        'year', 'round', 'average', 'all', 'varieties', 'unprepared', 'prepared',
        'whole', 'sliced', 'diced', 'chopped', 'minced', 'ground', 'grated',
        'regular', 'light', 'extra', 'virgin', 'commercial', 'wild', 'farmed',
        'mature', 'young', 'seeds', 'seed', 'meat', 'only', 'skin', 'skinless',
        'boneless', 'bone-in', 'bone', 'in', 'with', 'without', 'salt', 'unsalted',
        'salted', 'sweetened', 'unsweetened', 'roasted', 'boiled', 'steamed', 'fried',
        'baked', 'grilled', 'broiled', 'smoked', 'cured', 'pickled', 'fermented',
        'enriched', 'fortified', 'plain', 'flavored', 'seasoned', 'red', 'green', 
        'yellow', 'white', 'black', 'blue', 'purple', 'or', 'and', 'the', 'a', 'an'
    ]
    
    # Remove common prefixes/descriptors
    generic_words = []
    for word in base_name.split():
        if word not in descriptors:
            generic_words.append(word)
    
    # Return base name or original if nothing left
    result = ' '.join(generic_words) if generic_words else base_name
    
    # Handle special cases for common food types
    common_foods = {
        "egg": "egg",
        "eggs": "egg",
        "spinach": "spinach",
        "tomato": "tomato",
        "tomatoes": "tomato",
        "mushroom": "mushroom",
        "mushrooms": "mushroom",
        "potato": "potato",
        "potatoes": "potato",
        "carrot": "carrot",
        "carrots": "carrot",
        "onion": "onion",
        "onions": "onion",
        "garlic": "garlic",
        "chicken": "chicken",
        "beef": "beef",
        "pork": "pork",
        "fish": "fish",
        "rice": "rice",
        "pasta": "pasta",
        "bread": "bread",
        "cheese": "cheese"
    }
    
    # If the result contains a common food word, simplify to just that word
    for word in result.split():
        if word in common_foods:
            return common_foods[word]
    
    return result

def find_best_match_for_ingredient(ingredient, selected_foods):
    """Find the best matching food for a given ingredient"""
    if not selected_foods:
        return None
    
    best_match = None
    highest_score = 0
    
    # get just base name
    ingredient_base = extract_base_food_name(ingredient)
    ingredient_first_word = ingredient_base.split()[0] if ingredient_base.split() else ""
    
    print(f"Finding best match for: {ingredient} (base: {ingredient_base})")
    
    for food in selected_foods:
        food_name = food.get("name", "").lower()
        food_base = extract_base_food_name(food_name)
        food_first_word = food_base.split()[0] if food_base.split() else ""
        
        # Start with base similarity score
        similarity = difflib.SequenceMatcher(None, ingredient_base, food_base).ratio()
        
        # Apply bonus for common food types
        score = similarity
        
        # Bonus for matching first word 
        if ingredient_first_word and food_first_word and ingredient_first_word == food_first_word:
            score += 0.5
            print(f"  First word match bonus for {food_name}: +0.5")
        
        # Exact base name match is most important
        if ingredient_base == food_base:
            score += 1.0
            print(f"  Exact match bonus for {food_name}: +1.0")
        # One name contains the other
        elif ingredient_base in food_base or food_base in ingredient_base:
            score += 0.3
            print(f"  Substring match bonus for {food_name}: +0.3")
        
        print(f"  Score for {food_name}: {score:.2f}")
        
        if score > highest_score:
            highest_score = score
            best_match = food
    
    result = best_match if highest_score > 0.2 else None
    print(f"  Best match: {best_match['name'] if best_match else 'None'} (score: {highest_score:.2f})")
    
    return result

def recipe_is_makeable(recipe_ingredients, selected_foods):
    """Check if a recipe can be made with the selected foods"""
    if not selected_foods or not recipe_ingredients:
        return False
    
    selected_base_names = [extract_base_food_name(f["name"]) for f in selected_foods]
    
    print(f"Recipe ingredients: {recipe_ingredients}")
    print(f"Selected food base names: {selected_base_names}")
    
    # Count how many ingredients to match
    matched_ingredients = 0
    for ingredient in recipe_ingredients:
        ingredient_base = extract_base_food_name(ingredient)
        ingredient_first = ingredient_base.split()[0] if ingredient_base.split() else ""
        ingredient_found = False
        
        print(f"Checking ingredient: {ingredient} (base: {ingredient_base}, first: {ingredient_first})")
        
        for food in selected_foods:
            food_name = food.get("name", "").lower()
            food_base = extract_base_food_name(food_name)
            food_first = food_base.split()[0] if food_base.split() else ""
            
            # Check if the base ingredient names match
            if ingredient_base in food_base or food_base in ingredient_base:
                print(f"  ✓ Base name match: {food_name}")
                ingredient_found = True
                break
                
            # Check for matching first word 
            if ingredient_first and food_first and ingredient_first == food_first:
                print(f"  ✓ First word match: {food_name}")
                ingredient_found = True
                break
                
        if ingredient_found:
            matched_ingredients += 1
            print(f"  ✓ Found match for {ingredient}")
        else:
            print(f"  ✗ No match found for {ingredient}")
    
    match_ratio = matched_ingredients / len(recipe_ingredients) if recipe_ingredients else 0
    is_makeable = match_ratio >= 0.7
    
    print(f"Recipe match ratio: {match_ratio:.2f} ({matched_ingredients}/{len(recipe_ingredients)}) - Makeable: {is_makeable}")
    
    # Recipe is makeable if we can match at least 70% of ingredients
    return is_makeable

def build_recipe_macros(recipe_dict, selected_foods):
    """Build macros for recipes based on ingredients"""
    if not recipe_dict or not selected_foods:
        return []
    
    result = []
    print(f"\nBuilding recipe macros for {len(recipe_dict)} recipes with {len(selected_foods)} foods")
    
    for name, ingr_dict in recipe_dict.items():
        print(f"\nAnalyzing recipe: {name}")
        total = defaultdict(float)
        ingredients_found = 0
        total_ingredients = len(ingr_dict)
        
        for ingr, amount in ingr_dict.items():
            # Find best match for this ingredient 
            best_match = find_best_match_for_ingredient(ingr, selected_foods)
            
            # Add nutrients from this ingredient
            if best_match:
                ingredients_found += 1
                print(f"  ✓ Found match for {ingr}: {best_match['name']}")
                for macro in ["protein", "fat", "carbs", "fiber", "calories", "cholesterol"]:
                    # Convert from per 100g to the amount used in recipe
                    value = best_match.get(macro, 0) * (amount / 100)
                    total[macro] += value
            else:
                print(f"  ✗ No match found for {ingr}")
        
        min_ingredients_needed = max(1, round(total_ingredients * 0.5))
        
        print(f"  Found {ingredients_found}/{total_ingredients} ingredients (need {min_ingredients_needed})")
        
        if ingredients_found >= min_ingredients_needed:
            print(f"  ✓ Recipe is makeable with available ingredients")
            # Add recipe name to results
            total["Recipe"] = name
            # Add ingredients found info for debugging
            total["ingredients_found"] = ingredients_found
            total["total_ingredients"] = total_ingredients
            result.append(dict(total))
        else:
            print(f"  ✗ Not enough matching ingredients to make this recipe")
    
    print(f"\nFound {len(result)} makeable recipes")
    return result

def optimize_food_via_api(foods, goal, min_calories=None, max_calories=None):
    """Optimize food combinations based on goal and constraints"""
    if not foods:
        return None
    
    # Ensure all foods have the required keys
    sanitized_foods = []
    for food in foods:
        if isinstance(food, dict) and "name" in food:
            sanitized_food = {
                "name": food.get("name", "Unknown"),
                "protein": float(food.get("protein", 0)),
                "fat": float(food.get("fat", 0)),
                "carbs": float(food.get("carbs", 0)),
                "fiber": float(food.get("fiber", 0)),
                "calories": float(food.get("calories", 0)),
                "cholesterol": float(food.get("cholesterol", 0)),
                "Grams": float(food.get("Grams", 100))
            }
            sanitized_foods.append(sanitized_food)
    
    if not sanitized_foods:
        print("No valid foods to optimize")
        return None
    
    try:
        model = ConcreteModel()
        model.Foods = range(len(sanitized_foods))
        model.Quantity = Var(model.Foods, domain=NonNegativeReals)
        
        def nutrient_sum(nutrient):
            return sum(sanitized_foods[i][nutrient] * model.Quantity[i] / sanitized_foods[i].get("Grams", 100) for i in model.Foods)
        
        # Fix for objective functions - using clear maximize/minimize sense
        if goal == "maximize_protein":
            model.Objective = Objective(expr=nutrient_sum("protein"), sense=maximize)
        elif goal == "minimize_fat":
            model.Objective = Objective(expr=nutrient_sum("fat"), sense=minimize)
        elif goal == "minimize_cholesterol":
            model.Objective = Objective(expr=nutrient_sum("cholesterol"), sense=minimize)
        elif goal == "minimize_calories":
            model.Objective = Objective(expr=nutrient_sum("calories"), sense=minimize)
        elif goal == "maximize_fiber":
            model.Objective = Objective(expr=nutrient_sum("fiber"), sense=maximize)
        else:
            raise ValueError(f"Unknown goal: {goal}")
        
        # Add calorie constraints if needed
        if min_calories is not None and min_calories > 0:
            model.MinCal = Constraint(expr=nutrient_sum("calories") >= float(min_calories))
        if max_calories is not None and max_calories > 0:
            model.MaxCal = Constraint(expr=nutrient_sum("calories") <= float(max_calories))
        
        # Add constraints for quantities
        for i in model.Foods:
            model.add_component(
                f"limit_{i}",
                Constraint(expr=model.Quantity[i] <= sanitized_foods[i].get("Grams", 100))
            )
        
        # Solve the model
        solver = SolverFactory("glpk", executable="/opt/homebrew/bin/glpsol")
        results = solver.solve(model)
        
        if results.solver.status != SolverStatus.ok:
            print(f"Solver error: {results.solver.status}")
            return None
        
        # Extract results
        servings = {
            sanitized_foods[i]["name"]: round(value(model.Quantity[i]), 2)
            for i in model.Foods
            if value(model.Quantity[i]) > 0.01
        }
        
        # Calculate total macros
        macros = {
            nutrient: round(sum(value(model.Quantity[i]) * sanitized_foods[i][nutrient] / sanitized_foods[i].get("Grams", 100)
                            for i in model.Foods), 2)
            for nutrient in ["protein", "carbs", "fat", "fiber", "calories", "cholesterol"]
        }
        
        return servings, macros
    except Exception as e:
        print(f"Error in optimize_food_via_api: {e}")
        import traceback
        traceback.print_exc()
        return None

def optimize_recipe_via_api(recipe_data, goal, min_calories=None, max_calories=None):
    """Find the optimal recipe based on nutritional goals"""
    if not recipe_data:
        return None
    
    try:
        print(f"Starting recipe optimization with {len(recipe_data)} recipes")
        
        # Create Pyomo model
        model = ConcreteModel()
        model.I = range(len(recipe_data))
        model.x = Var(model.I, domain=Binary)
        
        def macro_sum(macro):
            return sum(recipe_data[i].get(macro, 0) * model.x[i] for i in model.I)
        
        if goal == "maximize_protein":
            model.obj = Objective(expr=macro_sum("protein"), sense=maximize)
        elif goal == "minimize_fat":
            model.obj = Objective(expr=macro_sum("fat"), sense=minimize)
        elif goal == "minimize_cholesterol":
            model.obj = Objective(expr=macro_sum("cholesterol"), sense=minimize)
        elif goal == "minimize_calories":
            model.obj = Objective(expr=macro_sum("calories"), sense=minimize)
        elif goal == "maximize_fiber":
            model.obj = Objective(expr=macro_sum("fiber"), sense=maximize)
        else:
            print(f"Unknown goal: {goal}")
            return None
        
        model.only_one = Constraint(expr=sum(model.x[i] for i in model.I) == 1)
        
        # Add calorie constraints if needed
        if min_calories is not None and min_calories > 0:
            model.min_cals = Constraint(expr=macro_sum("calories") >= float(min_calories))
        if max_calories is not None and max_calories > 0:
            model.max_cals = Constraint(expr=macro_sum("calories") <= float(max_calories))
        
        # Solve the model
        solver = SolverFactory("glpk", executable="/opt/homebrew/bin/glpsol")
        results = solver.solve(model)
        
        if results.solver.status != SolverStatus.ok:
            print(f"Solver error: {results.solver.status}")
            return None
        
        # Get the selected recipe
        for i in model.I:
            if value(model.x[i]) > 0.5:
                selected_recipe = recipe_data[i]
                # round nutrition values
                macro_totals = {
                    k: round(v, 2) for k, v in selected_recipe.items()
                    if k not in ["Recipe", "ingredients_found", "total_ingredients"] and isinstance(v, (int, float))
                }
                print(f"Selected recipe: {selected_recipe['Recipe']}")
                return selected_recipe["Recipe"], macro_totals
        
        print("No recipe selected in optimization result")
        return None
    except Exception as e:
        print(f"Error in optimize_recipe_via_api: {e}")
        import traceback
        traceback.print_exc()
        return None