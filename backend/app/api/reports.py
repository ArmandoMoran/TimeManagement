from __future__ import annotations

from datetime import date, timedelta
from typing import TYPE_CHECKING
from uuid import UUID

from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required

from app.services import report_service

if TYPE_CHECKING:
    from flask.wrappers import Response

bp = Blueprint("reports", __name__)


def _parse_date(value: str | None, *, default: date) -> date:
    return date.fromisoformat(value) if value else default


@bp.get("/utilization")
@jwt_required()
def utilization() -> Response:
    today = date.today()  # noqa: DTZ011 — reports operate on calendar dates
    start = _parse_date(request.args.get("start"), default=today - timedelta(days=30))
    end = _parse_date(request.args.get("end"), default=today)
    raw_user = request.args.get("user_id")
    rows = report_service.utilization(
        start=start, end=end, user_id=UUID(raw_user) if raw_user else None
    )
    return jsonify({"rows": rows, "start": start.isoformat(), "end": end.isoformat()})


@bp.get("/revenue")
@jwt_required()
def revenue() -> Response:
    today = date.today()  # noqa: DTZ011
    start = _parse_date(request.args.get("start"), default=today - timedelta(days=90))
    end = _parse_date(request.args.get("end"), default=today)
    raw_client = request.args.get("client_id")
    rows = report_service.revenue(
        start=start, end=end, client_id=UUID(raw_client) if raw_client else None
    )
    return jsonify({"rows": rows, "start": start.isoformat(), "end": end.isoformat()})


@bp.get("/outstanding")
@jwt_required()
def outstanding() -> Response:
    return jsonify(report_service.outstanding())
