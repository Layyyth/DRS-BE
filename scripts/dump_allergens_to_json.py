import json
from sqlalchemy.orm import Session
from app.core.db import SessionLocal
from app.models.allergen_mapping import AllergenMapping

def dump_allergen_mapping():
    db: Session = SessionLocal()
    rows = db.query(AllergenMapping).all()
    db.close()

    mapping = {}
    for row in rows:
        food = row.food.strip().lower()
        allergen = row.allergen.strip().lower()
        mapping.setdefault(food, []).append(allergen)

    with open("model/allergen_mapping.json", "w") as f:
        json.dump(mapping, f, indent=2)
    print("Allergen mapping saved to model/allergen_mapping.json")

if __name__ == "__main__":
    dump_allergen_mapping()
