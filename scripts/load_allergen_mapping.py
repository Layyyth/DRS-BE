import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import pandas as pd
from sqlalchemy.orm import Session
from app.core.db import SessionLocal
from app.models.allergen_mapping import AllergenMapping

def load_allergens_from_csv(csv_path: str):
    df = pd.read_csv(csv_path)
    df.columns = df.columns.str.strip().str.lower()
    df['food'] = df['food'].str.strip().str.lower().fillna('none')
    df['allergen'] = df['allergen'].str.strip().str.lower().fillna('none')

    db: Session = SessionLocal()
    try:
        for _, row in df.iterrows():
            mapping = AllergenMapping(food=row['food'], allergen=row['allergen'])
            db.add(mapping)
        db.commit()
        print("Allergen mapping inserted into DB successfully.")
    except Exception as e:
        db.rollback()
        print("Failed to insert allergen mappings:", e)
    finally:
        db.close()

if __name__ == "__main__":
    csv_file_path = "scripts/finalAllergens.csv"  
    load_allergens_from_csv(csv_file_path)
