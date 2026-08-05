"""
app/modules/users/enums.py

Domain enums for the Users module.

Why separate from models.py:
    - Enums are domain constants needed by models, schemas, AND services.
    - Co-locating them in models.py causes circular imports as the project grows.
    - Single Responsibility: This file ONLY defines enum types.
"""

import enum


class UserRole(str, enum.Enum):
    """
    Role-Based Access Control roles.
    USER: Standard traveller with access to their own resources.
    ADMIN: Clarity trainer/admin with access to analytics and all data.
    """

    USER = "user"
    ADMIN = "admin"
