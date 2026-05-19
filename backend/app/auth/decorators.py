from __future__ import annotations

from collections.abc import Callable
from functools import wraps
from typing import Any, cast

from flask_jwt_extended import current_user, jwt_required

from app.errors import ForbiddenError
from app.models import Role, User


def require_role[F: Callable[..., Any]](*roles: Role) -> Callable[[F], F]:
    """Server-side role gate. Combine with ``@jwt_required()`` upstream.

    Usage:
        @bp.post("/clients")
        @jwt_required()
        @require_role(Role.MANAGER, Role.ADMIN)
        def create_client(): ...
    """
    allowed = {*roles}

    def decorator(func: F) -> F:
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            user: User | None = current_user
            if user is None or user.role not in allowed:
                raise ForbiddenError("requires one of: " + ", ".join(r.value for r in allowed))
            return func(*args, **kwargs)

        return cast("F", wrapper)

    return decorator


def admin_required[F: Callable[..., Any]](func: F) -> F:
    """Convenience alias for the common admin-only case."""
    return cast("F", jwt_required()(require_role(Role.ADMIN)(func)))
