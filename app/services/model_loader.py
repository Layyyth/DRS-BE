import pickle

MODEL_PATH = "model/trained-models/mealPredictingModel_2025-03-31_16-04-59.pkl"

def get_model_only():
    with open(MODEL_PATH, "rb") as f:
        return pickle.load(f)