from __future__ import annotations

from typing import Any

from pydantic import BaseModel
from pydantic import ValidationError as PydanticValidationError

from app.errors import ValidationError


def parse_json[M: BaseModel](model_cls: type[M], payload: Any) -> M:
    """Validate the JSON body into a Pydantic model, translating errors to 422."""
    try:
        return model_cls.model_validate(payload)
    except PydanticValidationError as exc:
        raise ValidationError("invalid request body", details={"errors": exc.errors()}) from exc
