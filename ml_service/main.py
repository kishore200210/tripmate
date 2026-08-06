"""
main.py

FastAPI Microservice for Destination Recommendation utilizing MLflow.
"""

import os
from contextlib import asynccontextmanager

import mlflow
import pandas as pd
from fastapi import FastAPI, HTTPException

from schemas import DestinationItem, RecommendationRequest, RecommendationResponse

# Globals to hold models in memory
model = None
scaler = None
destination_mapping = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifecycle event to load MLflow models into memory at startup."""
    global model, scaler, destination_mapping
    
    # Configure MLflow to point to the local sqlite DB
    mlflow.set_tracking_uri("sqlite:///mlflow.db")
    mlflow.set_experiment("Destination_Recommendation")
    
    # Fetch the latest run
    client = mlflow.tracking.MlflowClient()
    experiment = client.get_experiment_by_name("Destination_Recommendation")
    runs = client.search_runs(experiment.experiment_id, order_by=["start_time DESC"], max_results=1)
    
    if not runs:
        raise RuntimeError("No MLflow runs found. Please run train.py first.")
        
    latest_run_id = runs[0].info.run_id
    print(f"Loading models from MLflow Run ID: {latest_run_id}")
    
    # Load model and scaler
    model_uri = f"runs:/{latest_run_id}/model"
    scaler_uri = f"runs:/{latest_run_id}/scaler"
    
    model = mlflow.sklearn.load_model(model_uri)
    scaler = mlflow.sklearn.load_model(scaler_uri)
    
    # Load destination mapping
    try:
        # Download artifact to temp path
        mapping_path = client.download_artifacts(latest_run_id, "destination_mapping.csv")
        destination_mapping = pd.read_csv(mapping_path)
    except Exception as e:
        raise RuntimeError(f"Failed to load destination_mapping.csv: {e}")
        
    yield
    # Clean up resources if needed on shutdown


app = FastAPI(
    title="Destination Recommendation Service",
    description="ML Microservice for predicting travel destinations.",
    lifespan=lifespan
)


@app.post("/api/v1/predict/destinations", response_model=RecommendationResponse)
async def predict_destinations(payload: RecommendationRequest):
    """
    Takes user preferences (budget, climate, activity_level),
    scales them, and predicts the nearest neighbor destinations.
    """
    if model is None or scaler is None or destination_mapping is None:
        raise HTTPException(status_code=503, detail="Model is currently unavailable.")
        
    try:
        # Format input array
        input_data = [[payload.budget, payload.climate, payload.activity_level]]
        scaled_input = scaler.transform(input_data)
        
        # Find nearest neighbors (top 3)
        distances, indices = model.kneighbors(scaled_input, n_neighbors=3)
        
        recommendations = []
        for idx in indices[0]:
            row = destination_mapping.iloc[idx]
            recommendations.append(
                DestinationItem(
                    id=str(row["destination_id"]),
                    name=str(row["name"])
                )
            )
            
        return RecommendationResponse(recommendations=recommendations)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
