import pandas as pd
import pickle
from sklearn.metrics import accuracy_score, classification_report

# Load the trained model
model_file = 'model/trained-models/mealPredictingModel_2025-03-31_13-58-32.pkl'
with open(model_file, 'rb') as f:
    models = pickle.load(f)

# Load test meals
new_meals_file = 'data/testmeals.csv'
new_meals_df = pd.read_csv(new_meals_file)

# Normalize columns
new_meals_df.columns = new_meals_df.columns.str.strip().str.lower()
new_meals_df['recipename'] = new_meals_df['recipename'].str.strip().str.lower().fillna('none')
new_meals_df['ingredients'] = new_meals_df['ingredients'].str.strip().str.lower().fillna('none')
new_meals_df['ingredients'] = new_meals_df['ingredients'].apply(lambda x: [ingredient.strip() for ingredient in x.split(',')])

# Load allergen mapping
allergens_file_path = 'data/finalAllergens.csv'
allergens_df = pd.read_csv(allergens_file_path)
allergen_mapping = allergens_df.groupby('food')['allergen'].apply(list).to_dict()

# Synonyms & cross-reactions
synonym_mapping = {
    "groundnuts": "peanuts",
    "peanut butter": "peanuts",
    "dairy": "milk",
    "seafood": "fish",
    "prawns": "shrimp",
}

cross_reactivity_mapping = {
    "bananas": ["latex allergy"],
    "avocados": ["latex allergy"],
    "shellfish": ["fish allergy"],
}

# Allergen enrichment
def enhance_allergen_mapping(ingredient):
    if ingredient in synonym_mapping:
        ingredient = synonym_mapping[ingredient]
    allergens = allergen_mapping.get(ingredient, [])
    if ingredient in cross_reactivity_mapping:
        allergens.extend(cross_reactivity_mapping[ingredient])
    return allergens

# Unique allergens
unique_allergens = set(allergen for allergens in allergen_mapping.values() for allergen in allergens)
print(f"Unique allergens: {unique_allergens}")

# Convert ingredients to feature vectors
def create_features(ingredients):
    features = {allergen: 0 for allergen in unique_allergens}
    for ingredient in ingredients:
        for allergen in enhance_allergen_mapping(ingredient):
            if allergen in features:
                features[allergen] = 1
    return features

# Build input matrix
X_new = pd.DataFrame(new_meals_df['ingredients'].apply(create_features).tolist())

# Align columns with model features
for column in models[list(models.keys())[0]]["features"]:
    if column not in X_new.columns:
        X_new[column] = 0

X_new = X_new[models[list(models.keys())[0]]["features"]]

# True labels from the CSV
y_true = pd.DataFrame({
    allergen: new_meals_df['allergen'].str.contains(allergen).fillna(False).astype(int)
    for allergen in unique_allergens
})

# Fill any missing columns
for allergen in unique_allergens:
    if allergen not in y_true.columns:
        y_true[allergen] = 0

# Predict and evaluate
y_pred = {}
accuracy = {}

for allergen in unique_allergens:
    if allergen in models:
        clf = models[allergen]["model"]
        y_pred[allergen] = clf.predict(X_new)
        accuracy[allergen] = accuracy_score(y_true[allergen], y_pred[allergen])
        print(f"Accuracy for {allergen}: {accuracy[allergen]:.2f}")
    else:
        print(f"No model available for {allergen}")

# Overall performance
if accuracy:
    overall_accuracy = sum(accuracy.values()) / len(accuracy)
    print(f"\nOverall model accuracy: {overall_accuracy:.2f}")

# Show full classification reports
for allergen in unique_allergens:
    if allergen in models:
        print(f"\nClassification report for {allergen}:")
        print(classification_report(y_true[allergen], y_pred[allergen], zero_division=1))
