# API Documentation

TripMate provides a robust, RESTful backend powered by FastAPI. The API relies strictly on JWT (JSON Web Tokens) for authentication.

## 📜 Swagger UI (Interactive Docs)

FastAPI automatically generates interactive OpenAPI documentation. When the backend is running, you can access it via:

- **Swagger UI**: [http://localhost:8000/docs](http://localhost:8000/docs)
- **ReDoc**: [http://localhost:8000/redoc](http://localhost:8000/redoc)

These interfaces allow you to execute requests directly from the browser, making them the primary source of truth for the API schema.

## 🔐 Authentication Flow

All protected endpoints require a Bearer token in the `Authorization` header.

1. **Register**: `POST /api/v1/auth/register`
   - Send `email`, `password`, and `full_name`.
2. **Login**: `POST /api/v1/auth/login`
   - Send `username` (email) and `password` as `application/x-www-form-urlencoded`.
   - Returns an `access_token`.
3. **Protected Requests**: 
   - Add Header: `Authorization: Bearer <your_access_token>`.

## 🌐 Core Endpoints

### AI Concierge (`/api/v1/ai`)
- `POST /chat`: Send a message to the LangGraph AI Agent. It maintains conversation history using SQLite Checkpointers.
- `GET /history/{trip_id}`: Retrieve the chat history for a specific trip.

### Vision (`/api/v1/vision`)
- `POST /analyze`: Upload a travel photo (`multipart/form-data`). The YOLO11 + OpenCV model will process the image, detect landmarks, and return an array of bounding boxes and identified labels.

### Trips & Itineraries (`/api/v1/trips`)
- `GET /`: Retrieve all trips for the authenticated user.
- `POST /`: Create a new trip.
- `POST /{id}/pdf`: Triggers the Celery background worker to compile the trip itinerary into a structured PDF document, returning a URL to download it.

## 📡 ML Service API

The ML Destination Recommendation engine runs on a separate microservice port (`8001`).

- **Swagger UI**: [http://localhost:8001/docs](http://localhost:8001/docs)
- `POST /predict`: Submit user preferences (e.g., budget, preferred climate) to receive a scikit-learn generated list of recommended destination UUIDs.
