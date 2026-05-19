from __future__ import annotations

from typing import TYPE_CHECKING

from flask import Blueprint, jsonify, request, send_file
from flask_jwt_extended import jwt_required

from app.api._helpers import parse_json
from app.auth.decorators import require_role
from app.errors import NotFoundError
from app.extensions import db
from app.models import Invoice, Role
from app.schemas.invoice import (
    InvoiceCreateRequest,
    InvoicePreviewRequest,
    InvoiceResponse,
)
from app.services import invoice_service

if TYPE_CHECKING:
    from uuid import UUID

    from flask.wrappers import Response

bp = Blueprint("invoices", __name__)


def _serialize(invoice: object) -> dict[str, object]:
    return InvoiceResponse.model_validate(invoice).model_dump(mode="json")


def _get_invoice(invoice_id: UUID) -> Invoice:
    invoice: Invoice | None = db.session.get(Invoice, invoice_id)
    if invoice is None:
        raise NotFoundError("invoice not found")
    return invoice


@bp.get("")
@jwt_required()
def list_invoices() -> Response:
    invoices = list(
        db.session.execute(db.select(Invoice).order_by(Invoice.issue_date.desc())).scalars()
    )
    return jsonify({"invoices": [_serialize(i) for i in invoices]})


@bp.get("/<uuid:invoice_id>")
@jwt_required()
def get_invoice(invoice_id: UUID) -> Response:
    invoice = _get_invoice(invoice_id)
    return jsonify(_serialize(invoice))


@bp.post("/preview")
@jwt_required()
@require_role(Role.MANAGER, Role.ADMIN)
def preview() -> Response:
    payload = parse_json(InvoicePreviewRequest, request.get_json(silent=True) or {})
    result = invoice_service.preview(
        client_id=payload.client_id,
        start=payload.start,
        end=payload.end,
        project_ids=payload.project_ids,
    )
    return jsonify(result)


@bp.post("")
@jwt_required()
@require_role(Role.MANAGER, Role.ADMIN)
def create_invoice() -> tuple[Response, int]:
    payload = parse_json(InvoiceCreateRequest, request.get_json(silent=True) or {})
    invoice = invoice_service.create_invoice(
        client_id=payload.client_id,
        start=payload.start,
        end=payload.end,
        issue_date=payload.issue_date,
        due_in_days=payload.due_in_days,
        tax_rate=payload.tax_rate,
        notes=payload.notes,
        project_ids=payload.project_ids,
    )
    invoice_service.render_pdf(invoice)
    db.session.commit()
    return jsonify(_serialize(invoice)), 201


@bp.get("/<uuid:invoice_id>/pdf")
@jwt_required()
def get_pdf(invoice_id: UUID) -> Response:
    invoice = _get_invoice(invoice_id)
    if invoice.pdf_path is None:
        invoice_service.render_pdf(invoice)
        db.session.commit()
    assert invoice.pdf_path is not None
    return send_file(invoice.pdf_path, as_attachment=True, mimetype="application/pdf")


@bp.post("/<uuid:invoice_id>/send")
@jwt_required()
@require_role(Role.MANAGER, Role.ADMIN)
def mark_sent(invoice_id: UUID) -> Response:
    invoice = _get_invoice(invoice_id)
    invoice_service.mark_sent(invoice)
    db.session.commit()
    return jsonify(_serialize(invoice))


@bp.post("/<uuid:invoice_id>/mark-paid")
@jwt_required()
@require_role(Role.MANAGER, Role.ADMIN)
def mark_paid(invoice_id: UUID) -> Response:
    invoice = _get_invoice(invoice_id)
    invoice_service.mark_paid(invoice)
    db.session.commit()
    return jsonify(_serialize(invoice))


@bp.post("/<uuid:invoice_id>/void")
@jwt_required()
@require_role(Role.ADMIN)
def void_invoice(invoice_id: UUID) -> Response:
    invoice = _get_invoice(invoice_id)
    invoice_service.void(invoice)
    db.session.commit()
    return jsonify(_serialize(invoice))
