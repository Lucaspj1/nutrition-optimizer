# Updated recipes with ingredients that match Foundation Foods from USDA API
recipes = {
    "Grilled Chicken Salad": {"Chicken, broiler or fryers, breast, meat only, cooked, roasted": 100, 
                              "Lettuce, iceberg, raw": 50, 
                              "Oil, olive, salad or cooking": 10},
    
    "Beef Rice Bowl": {"Beef, ground, 85% lean meat / 15% fat, crumbles, cooked, pan-browned": 100, 
                       "Rice, white, long-grain, regular, enriched, cooked": 100, 
                       "Egg, whole, raw, fresh": 50},
    
    "Turkey Sandwich": {"Turkey, breast, meat only, roasted": 75, 
                        "Bread, whole-wheat, commercially prepared": 60, 
                        "Lettuce, iceberg, raw": 20},
    
    "Tofu Stir Fry": {"Tofu, raw, regular, prepared with calcium sulfate": 100, 
                      "Broccoli, raw": 75, 
                      "Sauce, soy, made from soy (tamari)": 10},
    
    "Salmon & Sweet Potato": {"Fish, salmon, Atlantic, wild, raw": 100, 
                             "Sweet potato, raw, unprepared": 100, 
                             "Spinach, raw": 50},
    
    "Greek Yogurt Bowl": {"Yogurt, Greek, plain, whole milk": 150, 
                         "Nuts, almonds": 20, 
                         "Blueberries, raw": 50},
    
    "Avocado Toast": {"Avocados, raw, all commercial varieties": 70, 
                     "Bread, whole-wheat, commercially prepared": 60, 
                     "Egg, whole, cooked, fried": 50},
    
    "Protein Smoothie": {"Protein powder, whey based": 30, 
                        "Bananas, raw": 100, 
                        "Peanut butter, smooth style, with salt": 20, 
                        "Beverages, almond milk, unsweetened, shelf stable": 200},
    
    "Egg Veggie Scramble": {"Egg, whole, raw, fresh": 100, 
                           "Spinach, raw": 50, 
                           "Tomatoes, red, ripe, raw, year round average": 50, 
                           "Mushrooms, white, raw": 50},
    
    "Quinoa Power Bowl": {"Quinoa, cooked": 100, 
                         "Beans, black, mature seeds, cooked, boiled, without salt": 75, 
                         "Corn, sweet, yellow, raw": 50, 
                         "Avocados, raw, all commercial varieties": 50},
    
    # New recipes with Foundation Foods
    "Oatmeal with Berries": {"Cereals, oats, regular and quick, not fortified, dry": 40,
                            "Strawberries, raw": 50,
                            "Blueberries, raw": 50,
                            "Honey": 15,
                            "Milk, whole, 3.25% milkfat, with added vitamin D": 100},
    
    "Tuna Salad": {"Fish, tuna, light, canned in water, drained solids": 100,
                  "Mayonnaise, regular": 20,
                  "Celery, raw": 30,
                  "Onions, raw": 20,
                  "Lemon juice, raw": 5},
    
    "Mediterranean Plate": {"Chickpeas (garbanzo beans, bengal gram), mature seeds, cooked, boiled, without salt": 100,
                           "Cucumber, with peel, raw": 75,
                           "Tomatoes, red, ripe, raw, year round average": 75,
                           "Cheese, feta": 30,
                           "Oil, olive, salad or cooking": 15},
    
    "Banana Peanut Butter Wrap": {"Tortillas, ready-to-bake or -fry, flour": 50,
                                 "Bananas, raw": 100,
                                 "Peanut butter, smooth style, with salt": 30},
    
    "Cottage Cheese with Fruit": {"Cheese, cottage, lowfat, 1% milkfat": 150,
                                 "Peaches, raw": 100,
                                 "Pineapple, raw, all varieties": 100,
                                 "Honey": 10}
}

# Extract ingredients from recipes for matching
ingredients = {}
for recipe_name, recipe_ingredients in recipes.items():
    ingredients[recipe_name] = list(recipe_ingredients.keys())