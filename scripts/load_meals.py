import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import pandas as pd
from sqlalchemy.orm import Session
from app.core.db import SessionLocal
from app.models.meal import Meal

csv_path = "data/Final_Meals_Dataset_with_Diet_Types.csv"
df = pd.read_csv(csv_path)

db: Session = SessionLocal()
inserted = 0

try:
    for _, row in df.iterrows():
        
        ingredients = [i.strip().lower() for i in row['ingredients'].split(',')] if pd.notna(row['ingredients']) else []

        meal = Meal(
        name=row['name'],
        total_calories=row['total_calories'],
        fats=row['fats'],
        carbs=row['carbs'],
        protein=row['protein'],
        instruction=row['instruction'],
        ingredients=ingredients,
        diet_type=[d.strip().lower() for d in row['diet_type'].strip('{}').split(',')] if pd.notna(row['diet_type']) else [],
        meal_difficulty=row['meal_difficulty'],
        meal_cooking_time=row['meal_cooking_time'],  
        meal_cooking_method=[m.strip().lower() for m in row['meal_cooking_method'].split(',')] if pd.notna(row['meal_cooking_method']) else [],
        country_origin=row['country_origin'],
        meal_type=row['meal_type'],  
        )
        db.add(meal)
        inserted += 1

    db.commit()
    print(f"Successfully inserted {inserted} meals.")
except Exception as e:
    db.rollback()
    print("Failed to insert meals:", e)
finally:
    db.close()
