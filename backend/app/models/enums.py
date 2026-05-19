from __future__ import annotations

from enum import StrEnum


class Role(StrEnum):
    EMPLOYEE = "employee"
    MANAGER = "manager"
    ADMIN = "admin"


class EntryStatus(StrEnum):
    DRAFT = "draft"
    SUBMITTED = "submitted"
    APPROVED = "approved"
    INVOICED = "invoiced"


class TimerEventType(StrEnum):
    START = "start"
    PAUSE = "pause"
    RESUME = "resume"
    STOP = "stop"


class InvoiceStatus(StrEnum):
    DRAFT = "draft"
    SENT = "sent"
    PAID = "paid"
    VOID = "void"
