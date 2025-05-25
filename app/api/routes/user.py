import json
from typing import List
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Request, Query
from sqlalchemy.orm import Session
from jose import jwt, ExpiredSignatureError, JWTError

from app.core.db import get_db
from app.models import user
from app.models import meal
from app.models.user import User
from app.models.meal import Meal
from app.models.user_daily_consumption import UserDailyConsumption
from app.models.user_favorite_meals import UserFavoriteMeal
from app.schemas.consumption import ConsumeMealRequest, DailyConsumptionResponse, MessageResponse
from app.schemas.user import FavoriteMeal, FavoriteToggleRequest, ToggleFavoriteResponse, UserProfile, UserResponse
from app.core.security import SECRET_KEY, get_current_user
from app.services.model_loader import get_model_only
from app.utils.allergen_csv_loader import load_allergen_mapping_from_csv
from app.utils.calorie_calculator import calculate_calories
from app.core.cache import redis_client


from app.utils.helpers import calculate_age
from app.models.meal import Meal
from app.models.user_meals import UserMeal
from datetime import date

from app.logic.predictor import predict_safe_meals


router = APIRouter(tags=["User"])


# ----------- GET /user/me ------------
@router.get("/me", response_model=UserResponse)
def get_user_profile(request: Request, db: Session = Depends(get_db)):
    token = request.headers.get("Authorization", "").replace("Bearer ", "").strip()
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        email = payload.get("sub")

        cached = redis_client.get(f"user_profile:{email}")
        if cached:
            return json.loads(cached)

        user = db.query(User).filter(User.email == email).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        age = user.age() if callable(user.age) else None
        daily_cals, protein, carbs, fats = calculate_calories(user)

        data = {
            "id": user.id,
            "email": user.email,
            "name": user.name,
            "birthdate": user.birthdate.isoformat() if user.birthdate else None,
            "gender": user.gender,
            "weight": user.weight,
            "height": user.height,
            "activity_level": user.activity_level,
            "goal": user.goal,
            "preferred_diet": user.preferred_diet,
            "allergies": user.allergies or [],
            "info_gathered": user.info_gathered,
            "info_gathered_init": user.info_gathered_init,
            "daily_calories": daily_cals,
            "protein": float(protein),
            "carbs": float(carbs),
            "fats": float(fats)
        }

        redis_client.setex(f"user_profile:{email}", 60, json.dumps(data))
        return data

    except ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")



# ----------- PATCH /user/update-health-form ------------
@router.patch("/update-health-form", response_model=UserResponse)
def update_health_form(data: UserProfile, request: Request, db: Session = Depends(get_db)):
    token = request.headers.get("Authorization", "").replace("Bearer ", "").strip()
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid or missing token")

    email = payload.get("sub")
    user = db.query(User).filter(User.email == email).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    for key, value in data.model_dump(exclude_unset=True).items():
        if key == "allergies":
            user.allergies = [a.strip().lower() for a in value]
        elif key == "info_gathered":
            user.info_gathered = value
        else:
            setattr(user, key, value)

    # Set info_gathered_init only once (and never revert)
    if not user.info_gathered_init:
        user.info_gathered_init = True

    db.commit()
    db.refresh(user)

    db.query(UserMeal).filter(UserMeal.user_id == user.id).delete()

    models = get_model_only()
    allergen_mapping = load_allergen_mapping_from_csv()

    if not user.birthdate:
        raise HTTPException(status_code=400, detail="Birthdate is required to calculate age")

    user_input = {
        "allergies": user.allergies or [],
        "diet": user.preferred_diet or [],
        "age": calculate_age(user.birthdate),
        "gender": user.gender,
        "weight": user.weight,
        "height": user.height,
        "activity": user.activity_level,
        "goal": user.goal
    }

    meals = db.query(Meal).all()
    safe_meals = predict_safe_meals(models, allergen_mapping, meals, user_input)

    def matches_diet(meal):
        return not user_input["diet"] or any(d in (meal.diet_type or []) for d in user_input["diet"])

    safe_meals = [meal for meal in safe_meals if matches_diet(meal)]

    for meal in safe_meals:
        db.add(UserMeal(
            user_id=user.id,
            meal_id=meal.id,
            date_shown=date.today(),
            name=meal.name,
            total_calories=meal.total_calories,
            fats=meal.fats,
            carbs=meal.carbs,
            protein=meal.protein,
            instruction=meal.instruction,
            diet_type=meal.diet_type,
            meal_difficulty=meal.meal_difficulty,
            meal_cooking_time=meal.meal_cooking_time,
            meal_cooking_method=meal.meal_cooking_method,
            country_origin=meal.country_origin,
            ingredients=meal.ingredients,
            meal_type=meal.meal_type
        ))

    user.meals_initialized = True
    db.commit()

    print(f"Stored {len(safe_meals)} safe & diet-compatible meals for {user.email}")

    daily_cals, p, c, f = calculate_calories(user)

    try:
        redis_client.delete(f"user_profile:{user.email}")
    except:
        pass

    return {
        **user.__dict__,
        "daily_calories": daily_cals,
        "macronutrients": {
            "protein": p,
            "carbs": c,
            "fats": f
        },
        "meals_generated": len(safe_meals)
    }





# ----------- POST /user/profile ------------
@router.post("/profile", response_model=UserResponse)
async def update_user_profile(
    user_data: UserProfile,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    email = current_user.get("sub")
    user = db.query(User).filter(User.email == email).first()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    user.name = user_data.name
    user.age = user_data.age
    user.gender = user_data.gender
    user.weight = user_data.weight
    user.height = user_data.height
    user.activity_level = user_data.activity_level
    user.goal = user_data.goal
    user.preferred_diet = user_data.preferred_diet

    if user_data.allergies is not None:
        user.allergies = user_data.allergies

    db.commit()
    db.refresh(user)

    return UserResponse(**user.__dict__)


# ----------- GET /user/profile ------------
@router.get("/profile", response_model=UserResponse)
async def get_user_profile_by_token(
    current_user: dict = Depends(get_current_user), 
    db: Session = Depends(get_db)
):
    email = current_user.get("sub")
    user = db.query(User).filter(User.email == email).first()
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    return UserResponse(**user.__dict__)


# ----------- POST /user/favorite ------------
@router.post("/favorite", response_model=ToggleFavoriteResponse)
def toggle_favorite(data: FavoriteToggleRequest, db: Session = Depends(get_db)):
    user_id = data.user_id
    meal_id = data.meal_id

    user = db.query(User).filter(User.id == user_id).first()
    meal = db.query(Meal).filter(Meal.id == meal_id).first()

    if not user or not meal:
        raise HTTPException(status_code=404, detail="User or meal not found")

    existing = db.query(UserFavoriteMeal).filter_by(user_id=user_id, meal_id=meal_id).first()

    if existing:
        db.delete(existing)
        db.commit()
        return {"message": "Meal removed from favorites"}
    else:
        db.add(UserFavoriteMeal(user_id=user_id, meal_id=meal_id))
        db.commit()
        return {"message": "Meal added to favorites"}


# ----------- GET /user/favorites ------------
@router.get("/favorites", response_model=List[FavoriteMeal])
def get_favorite_meals(user_id: int, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    meals = (
        db.query(Meal)
        .join(UserFavoriteMeal, Meal.id == UserFavoriteMeal.meal_id)
        .filter(UserFavoriteMeal.user_id == user_id)
        .all()
    )

    return [
        FavoriteMeal(
            id=meal.id,
            name=meal.name,
            instruction=meal.instruction,
            calories=meal.total_calories,
            fats=meal.fats,
            carbs=meal.carbs,
            protein=meal.protein,
            diet_type=meal.diet_type,
            difficulty=meal.meal_difficulty,
            meal_cooking_time=meal.meal_cooking_time,
            cooking_method=meal.meal_cooking_method,
            origin=meal.country_origin,
            meal_type=meal.meal_type,
            ingredients=", ".join(meal.ingredients) if meal.ingredients else ""
        )
        for meal in meals
    ]


#------------------------ user consume ---------- 
@router.post("/user/consume", response_model=MessageResponse)
def consume_meal(data: ConsumeMealRequest, db: Session = Depends(get_db)):
    user_id = data.user_id
    meal_id = data.meal_id

    
    user = db.query(User).filter(User.id == user_id).first()
    meal = db.query(Meal).filter(Meal.id == meal_id).first()

    if not user or not meal:
        raise HTTPException(status_code=404, detail="User or Meal not found")

    today = date.today()
    consumption = (
        db.query(UserDailyConsumption)
        .filter(UserDailyConsumption.user_id == user_id, UserDailyConsumption.date == today)
        .first()
    )

    if not consumption:
        consumption = UserDailyConsumption(
            user_id=user_id,
            date=today,
            calories=meal.total_calories or 0,
            protein=meal.protein or 0,
            carbs=meal.carbs or 0,
            fats=meal.fats or 0,
        )
        db.add(consumption)
    else:
        consumption.calories += meal.total_calories or 0
        consumption.protein += meal.protein or 0
        consumption.carbs += meal.carbs or 0
        consumption.fats += meal.fats or 0

    db.commit()
    return {"message": "Meal consumed and stats updated successfully"}



@router.get("/user/consumption", response_model=DailyConsumptionResponse)
def get_consumption(user_id: int, db: Session = Depends(get_db)):
    today = date.today()
    consumption = (
        db.query(UserDailyConsumption)
        .filter(UserDailyConsumption.user_id == user_id, UserDailyConsumption.date == today)
        .first()
    )

    if not consumption:
        return DailyConsumptionResponse(
            date=today,
            total_calories=0,
            protein=0,
            carbs=0,
            fats=0
        )

    return DailyConsumptionResponse(
        date=consumption.date,
        total_calories=consumption.calories,
        protein=consumption.protein,
        carbs=consumption.carbs,
        fats=consumption.fats
    )
