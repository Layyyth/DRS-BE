from typing import List
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from uuid import UUID
from datetime import date
from app.core.db import get_db
from app.models import meal
from app.models.user import User
from app.models.meal import Meal
from app.models.user_meals import UserMeal
from app.schemas.predict import MealDetailResponse, MealItem, MealSearchResult, PredictionResponse
from app.services.model_loader import get_model_only
from app.utils.helpers import calculate_age
from app.utils.calorie_calculator import get_daily_calories
from app.schemas.request import PredictRequest

router = APIRouter(tags=["Prediction"])

@router.post("/predict", response_model=PredictionResponse)
def predict_meals(data: PredictRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == data.user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    shown_meals = db.query(UserMeal).filter(UserMeal.user_id == data.user_id).all()
    if not shown_meals:
        raise HTTPException(status_code=404, detail="No meals stored for user.")

    # ---------- FILTER HELPERS ----------
    def matches_meal_cooking_time(meal):
        if not data.meal_cooking_time:
            return True
        try:
            meal_time = int("".join(filter(str.isdigit, str(meal.meal_cooking_time))))
            return meal_time <= int(data.meal_cooking_time)
        except:
            return False

    def excludes_ingredients(meal):
        if not data.excluded_ingredients:
            return True
        ingredients = [i.lower().strip() for i in (meal.ingredients or [])]
        return all(excl.lower().strip() not in ingredients for excl in data.excluded_ingredients)

    def matches_meal_type(meal):
        if not data.meal_type:
            return True
        return meal.meal_type and meal.meal_type.strip().lower() == data.meal_type.strip().lower()

    def matches_meal_cooking_method(meal):
        if not data.meal_cooking_method:
            return True
        return (
            meal.meal_cooking_method and
            any(
                method in [m.strip().lower() for m in meal.meal_cooking_method]
                for method in data.meal_cooking_method
            )
        )

    def matches_diet_type(meal):
        if not data.diet_type:
            return True
        return (
            meal.diet_type and
            any(dt.lower().strip() == data.diet_type.lower().strip() for dt in meal.diet_type)
        )

    # ---------- APPLY FILTERS ----------
    filtered = [
        m for m in shown_meals
        if matches_meal_cooking_time(m)
        and excludes_ingredients(m)
        and matches_meal_type(m)
        and matches_meal_cooking_method(m)
        and matches_diet_type(m)
    ]

    if data.limit:
        filtered = filtered[:data.limit]

    # ---------- CALCULATE MACROS ----------
    age = calculate_age(user.birthdate)
    daily_cals, p, c, f = get_daily_calories(
        age,
        user.gender,
        user.weight,
        user.height,
        user.activity_level,
        user.goal
    )

    # ---------- RESPONSE ----------
    return {
        "daily_calories": daily_cals,
        "macros": {
            "protein": p,
            "carbs": c,
            "fats": f
        },
        "recommended_meals": [
            MealItem(
                id=m.meal_id,
                name=m.name,
                instruction=m.instruction,
                calories=m.total_calories,
                protein=m.protein,
                carbs=m.carbs,
                fats=m.fats,
                diet_type=m.diet_type,
                difficulty=m.meal_difficulty,
                meal_cooking_time=m.meal_cooking_time,
                meal_cooking_method=m.meal_cooking_method,
                cooking_method=m.meal_cooking_method,
                origin=m.country_origin,
                meal_type=m.meal_type,
                ingredients=", ".join(m.ingredients) if m.ingredients else ""
            )
            for m in filtered
        ]
    }



@router.get("/meal/{meal_id}", response_model=MealDetailResponse)
def get_meal_detail(meal_id: int, db: Session = Depends(get_db)):
    meal = db.query(Meal).filter(Meal.id == meal_id).first()
    if not meal:
        raise HTTPException(status_code=404, detail="Meal not found")

    return MealDetailResponse(
        id=meal.id,
        name=meal.name,
        ingredients=", ".join(meal.ingredients) if meal.ingredients else "",
        instruction=meal.instruction,
        calories=meal.total_calories,
        fats=meal.fats,
        carbs=meal.carbs,
        protein=meal.protein,
        diet_type=meal.diet_type,
        difficulty=meal.meal_difficulty,
        meal_cooking_time=meal.meal_cooking_time,
        meal_cooking_method=meal.meal_cooking_method,
        origin=meal.country_origin,
        meal_type=meal.meal_type
    )


@router.get("/search", response_model=List[MealSearchResult])
def search_meals(query: str = Query(..., min_length=2), db: Session = Depends(get_db)):
    meals = db.query(Meal).filter(
        Meal.name.ilike(f"%{query}%") |
        Meal.country_origin.ilike(f"%{query}%") |
        Meal.instruction.ilike(f"%{query}%")
    ).all()
    return [meal.__dict__ for meal in meals]



#------------ auto complete ----------
@router.get("/ingredients/suggest")
def suggest_ingredients(query: str, db: Session = Depends(get_db)):
    # Fetch all distinct ingredients from meals
    all_ingredients = db.query(Meal.ingredients).all()

    # Flatten and normalize all ingredients
    unique_ingredients = set(
        ing.strip().lower()
        for row in all_ingredients
        for ing in (row[0] or [])
    )

    # Filter ingredients that match the query prefix
    suggestions = [
        ing for ing in unique_ingredients
        if ing.startswith(query.strip().lower())
    ]

    return {"suggestions": sorted(suggestions)}