import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

import pickle
from app.logic.predictor import predict_safe_meals
from app.models.meal import Meal


from app.utils.allergen_csv_loader import load_allergen_mapping_from_csv
allergen_mapping = load_allergen_mapping_from_csv()

# Load trained model
with open("model/trained-models/mealPredictingModel_2025-03-31_16-04-59.pkl", "rb") as f:
    model = pickle.load(f)


# Fake user input
user_input = {
    "allergies": ["soy allergy", "peanut allergy"]
}

# Mock meals
meals = [
    Meal(id=1, name="Chicken Teriyaki", ingredients="chicken, soy sauce, garlic"),
    Meal(id=2, name="Peanut Butter Toast", ingredients="bread, peanut butter"),
    Meal(id=3, name="Grilled Zucchini", ingredients="zucchini, olive oil, herbs")
]

# Run prediction
safe_meals = predict_safe_meals(model, allergen_mapping, meals, user_input)

# Output
print("\n✅ SAFE MEALS:")
for meal in safe_meals:
    print(f"- {meal.name}")