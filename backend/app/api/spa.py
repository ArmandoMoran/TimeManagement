from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from flask import Blueprint, abort, current_app, send_from_directory

if TYPE_CHECKING:
    from flask.wrappers import Response

bp = Blueprint("spa", __name__)


@bp.get("/", defaults={"path": ""})
@bp.get("/<path:path>")
def serve_spa(path: str) -> Response:
    """Serve the built SPA, falling back to ``index.html`` for client routes.

    Real asset paths (``/assets/...``) are served directly so the React bundle
    and CSS load. Anything else hands index.html back to the client router.
    """
    dist_value = current_app.config.get("FRONTEND_DIST_PATH")
    if not dist_value:
        abort(404)

    dist = Path(dist_value)
    if path:
        asset = dist / path
        if asset.is_file():
            return send_from_directory(dist, path)
    return send_from_directory(dist, "index.html")
