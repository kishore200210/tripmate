"""
train.py

Generates synthetic destination data, trains a NearestNeighbors recommendation model,
and logs it to MLflow.
"""

import os
import random

import mlflow
import mlflow.sklearn
import numpy as np
import pandas as pd
from sklearn.neighbors import NearestNeighbors
from sklearn.preprocessing import StandardScaler


def generate_synthetic_data(num_samples=100) -> pd.DataFrame:
    """Generates a realistic synthetic destination dataset."""
    destinations = [
        "Paris, France", "Tokyo, Japan", "Bali, Indonesia", "New York, USA",
        "Rome, Italy", "Sydney, Australia", "Cape Town, South Africa", 
        "Rio de Janeiro, Brazil", "Kyoto, Japan", "London, UK",
        "Bangkok, Thailand", "Dubai, UAE", "Machu Picchu, Peru", "Santorini, Greece"
    ]
    
    data = []
    for i in range(num_samples):
        dest = destinations[i % len(destinations)]
        
        # budget: 1 (cheap) to 5 (luxury)
        # climate: 1 (cold) to 5 (hot)
        # activity: 1 (relaxed) to 5 (intense)
        data.append({
            "destination_id": f"dest_{i}",
            "name": f"{dest} - Variant {i}",
            "budget": random.randint(1, 5),
            "climate": random.randint(1, 5),
            "activity_level": random.randint(1, 5)
        })
        
    return pd.DataFrame(data)


def main():
    mlflow.set_tracking_uri("sqlite:///mlflow.db")
    mlflow.set_experiment("Destination_Recommendation")
    
    with mlflow.start_run():
        print("Generating data...")
        df = generate_synthetic_data(100)
        
        # Features for KNN
        features = df[["budget", "climate", "activity_level"]]
        
        # Scale features
        scaler = StandardScaler()
        scaled_features = scaler.fit_transform(features)
        
        # Train model
        n_neighbors = 5
        model = NearestNeighbors(n_neighbors=n_neighbors, algorithm="auto")
        model.fit(scaled_features)
        
        # Log params
        mlflow.log_param("n_neighbors", n_neighbors)
        mlflow.log_param("num_samples", len(df))
        
        # Log models
        mlflow.sklearn.log_model(model, "model", serialization_format=mlflow.sklearn.SERIALIZATION_FORMAT_CLOUDPICKLE)
        mlflow.sklearn.log_model(scaler, "scaler", serialization_format=mlflow.sklearn.SERIALIZATION_FORMAT_CLOUDPICKLE)
        
        # Save dataset mapping locally for the API to use
        df.to_csv("destination_mapping.csv", index=False)
        mlflow.log_artifact("destination_mapping.csv")
        
        print(f"Model trained and logged to MLflow successfully. Run ID: {mlflow.active_run().info.run_id}")


if __name__ == "__main__":
    main()
