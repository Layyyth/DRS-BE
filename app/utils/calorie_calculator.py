from datetime import date
from app.models.user import User

def calculate_calories(user: User):
    
    if not user.birthdate or not user.weight or not user.height or not user.gender or not user.activity_level:
        return 0, 0, 0, 0  
    
    today = date.today()
    birthdate = user.birthdate
    age = today.year - birthdate.year - ((today.month, today.day) < (birthdate.month, birthdate.day))

    
    if user.gender.lower() == "male":
        bmr = 10 * user.weight + 6.25 * user.height - 5 * age + 5
    else:
        bmr = 10 * user.weight + 6.25 * user.height - 5 * age - 161

    
    activity_levels = {
        "sedentary": 1.2,
        "lightly_active": 1.375,
        "moderately_active": 1.55,
        "very_active": 1.725,
        "extra_active": 1.9
    }
    tdee = bmr * activity_levels.get(user.activity_level.lower(), 1.2)  

    
    goal_modifiers = {
        "gain weight": 500, "gain": 500,
        "maintain weight": 0, "maintain": 0,
        "lose weight": -500, "lose": -500
    }
    daily_calories = tdee + goal_modifiers.get(user.goal.lower(), 0)

    
    if daily_calories is None or daily_calories <= 0:
        print(f"Error: Invalid daily_calories: {daily_calories}")
        return 0, 0, 0, 0  

    
    protein = (daily_calories * 0.3) / 4  
    carbs = (daily_calories * 0.4) / 4  
    fats = (daily_calories * 0.3) / 9  

    
    print(f"DEBUG - Calculated TDEE: {tdee}")
    print(f"DEBUG - Daily Calories: {daily_calories}")
    print(f"DEBUG - Protein: {protein}, Carbs: {carbs}, Fats: {fats}")

    return daily_calories, protein, carbs, fats

def get_daily_calories(age: int, gender: str, weight: float, height: float, activity: str, goal: str):
    if not all([age, gender, weight, height, activity]):
        return 0, 0, 0, 0

    if gender.lower() == "male":
        bmr = 10 * weight + 6.25 * height - 5 * age + 5
    else:
        bmr = 10 * weight + 6.25 * height - 5 * age - 161

    activity_levels = {
        "sedentary": 1.2,
        "lightly_active": 1.375,
        "moderately_active": 1.55,
        "very_active": 1.725,
        "extra_active": 1.9
    }
    tdee = bmr * activity_levels.get(activity.lower(), 1.2)

    goal_modifiers = {
        "gain weight": 500, "gain": 500,
        "maintain weight": 0, "maintain": 0,
        "lose weight": -500, "lose": -500
    }
    daily_calories = tdee + goal_modifiers.get(goal.lower(), 0)

    protein = (daily_calories * 0.3) / 4
    carbs = (daily_calories * 0.4) / 4
    fats = (daily_calories * 0.3) / 9

    return round(daily_calories), round(protein), round(carbs), round(fats)