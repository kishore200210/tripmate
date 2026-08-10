"""
train_model.py
Generates a synthetic history dataset of user preferences and their chosen destinations.
Trains a Random Forest Classifier and exports the joblib pipeline.
"""
import os
import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.metrics import accuracy_score, classification_report
import joblib

# Paths
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CSV_PATH = os.path.join(BASE_DIR, "destinations_dataset.csv")
MODEL_DIR = os.path.join(BASE_DIR, "..", "app", "models")
MODEL_PATH = os.path.join(MODEL_DIR, "recommendation_model.joblib")

def load_destinations():
    return pd.read_csv(CSV_PATH)

def generate_synthetic_user_history(destinations_df, num_samples=10000):
    """
    Simulates historical user data. For each user, we generate random preferences,
    then assign the destination that mathematically matches their preferences best.
    """
    np.random.seed(42)
    
    # Generate random user preferences
    climates = destinations_df["Climate"].unique()
    styles = destinations_df["Travel_Style"].unique()
    seasons = destinations_df["Best_Season"].unique()
    
    synthetic_data = []
    
    for _ in range(num_samples):
        budget = np.random.uniform(30, 300)
        duration = np.random.randint(3, 15)
        travelers = np.random.randint(1, 21)  # 1–20 travelers
        climate = np.random.choice(climates)
        style = np.random.choice(styles)
        season = np.random.choice(seasons)
        
        # Scoring metrics 1-10 (how much they care about it)
        fam_score = np.random.randint(1, 11)
        adv_score = np.random.randint(1, 11)
        lux_score = np.random.randint(1, 11)
        
        # Find the best matching destination for this user to act as the "Chosen Destination"
        best_dest = None
        best_score = -99999
        
        for _, dest in destinations_df.iterrows():
            score = 0
            
            # Budget match (closer is better, but budget >= dest_budget)
            if budget >= dest["Budget_Per_Day_USD"]:
                score += 10 - min((budget - dest["Budget_Per_Day_USD"]) / 10, 10)
            else:
                score -= 20
                
            # Categorical matches
            if climate == dest["Climate"]: score += 15
            if style == dest["Travel_Style"]: score += 15
            if season == dest["Best_Season"]: score += 10
            
            # Metric proximity
            score -= abs(fam_score - dest["Family_Friendly_Score"]) * 1.5
            score -= abs(adv_score - dest["Adventure_Score"]) * 1.5
            score -= abs(lux_score - dest["Luxury_Score"]) * 1.5
            
            # Group-size influence: larger groups favour family-friendly
            # destinations and slightly penalise solo-oriented luxury spots
            if travelers >= 4:
                score += dest["Family_Friendly_Score"] * 0.5
            if travelers >= 8:
                score += dest["Family_Friendly_Score"] * 0.3
            
            if score > best_score:
                best_score = score
                best_dest = dest["Destination"]
        
        synthetic_data.append({
            "budget": budget,
            "duration": duration,
            "travelers": travelers,
            "climate": climate,
            "travel_style": style,
            "season": season,
            "family_friendly": fam_score,
            "adventure": adv_score,
            "luxury": lux_score,
            "target_destination": best_dest
        })
        
    return pd.DataFrame(synthetic_data)


def train_and_export():
    print("1. Loading base destinations...")
    dest_df = load_destinations()
    
    print("2. Generating synthetic user history (10k samples)...")
    df = generate_synthetic_user_history(dest_df, 10000)
    
    X = df.drop("target_destination", axis=1)
    y = df["target_destination"]
    
    # Define features
    categorical_features = ["climate", "travel_style", "season"]
    numerical_features = ["budget", "duration", "travelers", "family_friendly", "adventure", "luxury"]
    
    # Preprocessing
    preprocessor = ColumnTransformer(
        transformers=[
            ("num", StandardScaler(), numerical_features),
            ("cat", OneHotEncoder(handle_unknown="ignore"), categorical_features),
        ]
    )
    
    # Model Pipeline
    pipeline = Pipeline([
        ("preprocessor", preprocessor),
        ("classifier", RandomForestClassifier(n_estimators=100, random_state=42, n_jobs=-1))
    ])
    
    # Train-test split
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    
    print("3. Training Random Forest Classifier...")
    pipeline.fit(X_train, y_train)
    
    print("4. Evaluating Model...")
    y_pred = pipeline.predict(X_test)
    acc = accuracy_score(y_test, y_pred)
    print(f"Accuracy: {acc:.4f}")
    
    # Export Model
    os.makedirs(MODEL_DIR, exist_ok=True)
    joblib.dump(pipeline, MODEL_PATH)
    print(f"5. Model saved successfully to {MODEL_PATH}")

if __name__ == "__main__":
    train_and_export()
