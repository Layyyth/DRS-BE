import pandas as pd

def load_allergen_mapping_from_csv(path="scripts/finalAllergens.csv"):
    df = pd.read_csv(path)
    df.columns = df.columns.str.strip().str.lower()
    df['food'] = df['food'].str.strip().str.lower()
    df['allergen'] = df['allergen'].str.strip().str.lower()
    return df.groupby('food')['allergen'].apply(list).to_dict()