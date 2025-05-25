import pandas as pd

def predict_safe_meals(models, allergen_mapping, meals, user_input):
    safe_meals = []

    for meal in meals:
        ingredients = meal.ingredients if isinstance(meal.ingredients, list) else meal.ingredients.split(',')
        ingredients = [i.strip().lower() for i in ingredients]

        # Create allergen feature vector
        feature_vector = {allergen: 0 for allergen in models}
        for ingredient in ingredients:
            found_allergens = allergen_mapping.get(ingredient, [])
            for allergen in found_allergens:
                if allergen in feature_vector:
                    feature_vector[allergen] = 1

        # Check predictions
        is_safe = True
        for allergen in user_input["allergies"]:
            if allergen in models:
                clf = models[allergen]
                prediction = clf.predict(pd.DataFrame([feature_vector]))[0]
                if prediction == 1:
                    is_safe = False
                    break

        if is_safe:
            safe_meals.append(meal)

    return safe_meals