# Nutrition Optimizer

A Streamlit application that helps you optimize your nutrition based on the foods you have available. The app can recommend the best combination of foods to meet your nutritional goals or suggest recipes that can be made from your available ingredients.

## Features

- Search for foods in the USDA database
- Specify how much of each food you have
- Choose optimization goals (maximize protein, minimize fat, etc.)
- Set calorie constraints
- Get optimal food combinations
- Find recipes that can be made with your ingredients
- Browse all available recipes to see what you can make

## Installation & Setup

### Prerequisites

- Python 3.8 or higher
- GLPK (GNU Linear Programming Kit) for optimization
- Virtual environment (recommended)

### Installing GLPK

#### macOS:
```bash
brew install glpk
```

#### Linux:
```bash
sudo apt-get install glpk-utils libglpk-dev
```

#### Windows:
Download from [GLPK for Windows](https://sourceforge.net/projects/winglpk/) and add the executable to your PATH.

### Setup Instructions

1. Clone the repository:
```bash
git clone https://github.com/your-username/nutrition-optimizer.git
cd nutrition-optimizer
```

2. Create and activate a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows, use: venv\Scripts\activate
```

3. Install the required packages:
```bash
pip install -r requirements.txt
```

4. Run the application (this requires two terminal windows):

Terminal 1 - Start the Flask API:
```bash
python optimizer_api.py
```

Terminal 2 - Start the Streamlit app:
```bash
streamlit run app.py
```

5. Open your browser and navigate to:
```
http://localhost:8501
```

## How to Use

### Adding Foods
1. Search for foods using the search bar
2. Select a food from the suggestions
3. Specify how many grams you have
4. Click "Add Food"

### Optimizing Foods
1. Add all the foods you have available
2. Select an optimization goal (e.g., maximize protein)
3. Set minimum and maximum calories if desired
4. Click "Optimize Foods"

### Finding Recipes
1. Add all the foods you have available
2. Click "Optimize Recipes" to find the best recipe
3. The app will show you the best recipe based on your optimization goal

### Browsing Recipes
1. Navigate to the "Available Recipes" page
2. Browse all recipes to see what you can make
3. Filter recipes by category

## Ingredient Matching

The app intelligently matches similar ingredients. For example, if a recipe calls for "tomatoes, cherry" and you have "tomatoes, roma", the app will recognize them as compatible.

## Troubleshooting

- If you don't see any search results, try general terms like "chicken", "rice", etc.
- If optimization fails, try relaxing your calorie constraints
- If recipes aren't showing up, try adding more varied ingredients
- If you get a solver error, make sure GLPK is installed correctly and the path is correct in recipe_logic.py

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- USDA Food Data Central API for nutrition information
- Streamlit for the web interface
- Pyomo for optimization modeling
