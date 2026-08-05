"""
app/modules/users/router.py

HTTP Routing Layer — Users Module.

Responsibility:
    - Maps HTTP verbs + paths to controller functions ONLY.
    - No business logic here. No database access here.
    - All route parameters are validated by Pydantic schemas.
    - All routes are prefixed with /api/v1/users (registered in main.py).

MVC Role: This is the Routing Layer.
"""

from fastapi import APIRouter

router = APIRouter(prefix="/users", tags=["Users"])

# Routes will be implemented in Milestone 2.
# Example:
# @router.post("/register", response_model=UserResponse, status_code=201)
# async def register_user(payload: UserCreateRequest, service: UserService = Depends(get_user_service)):
#     return await service.register(payload)
