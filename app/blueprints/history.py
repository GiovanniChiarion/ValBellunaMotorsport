import json
from datetime import UTC, datetime

from flask import Blueprint, Response, render_template
from sqlalchemy.orm import joinedload

from app.auth import admin_required, superadmin_required
from app.database import get_db
from app.models import AuditLog

history_bp = Blueprint("history", __name__, url_prefix="/history")


@history_bp.route("")
@admin_required
def history_view():
    with get_db() as db:
        logs = (
            db.query(AuditLog)
            .options(joinedload(AuditLog.user), joinedload(AuditLog.race))
            .order_by(AuditLog.timestamp.desc())
            .limit(200)
            .all()
        )

    return render_template("history.html", logs=logs)


@history_bp.route("/export")
@superadmin_required
def export_history():
    with get_db() as db:
        logs = (
            db.query(AuditLog)
            .options(joinedload(AuditLog.user), joinedload(AuditLog.race))
            .order_by(AuditLog.timestamp.desc())
            .all()
        )

    data = {
        "export_date": datetime.now(UTC).isoformat(),
        "data": {
            "audit_logs": [
                {
                    "id": al.id,
                    "user_id": al.user_id,
                    "user_name": al.user.nome if al.user else None,
                    "race_id": al.race_id,
                    "race_description": al.race.descrizione if al.race else None,
                    "field": al.field,
                    "old_value": al.old_value,
                    "new_value": al.new_value,
                    "timestamp": al.timestamp.isoformat() if al.timestamp else None,
                }
                for al in logs
            ],
        },
    }

    return Response(
        json.dumps(data, indent=2, ensure_ascii=False),
        mimetype="application/json",
        headers={
            "Content-Disposition": "attachment; filename=valbellunamotorsport-history.json"
        },
    )
