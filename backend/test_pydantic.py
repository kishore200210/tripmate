from app.modules.auth.schemas import RegisterRequest
from pydantic import ValidationError

payload = {
    "email": "test@example.com",
    "password": "Password123!",
    "name": "Test User"
}

try:
    req = RegisterRequest(**payload)
    print("SUCCESS")
except ValidationError as e:
    print("VALIDATION ERROR")
    print(e.json())
