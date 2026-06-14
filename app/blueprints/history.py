import json
from datetime import UTC, datetime

from flask import Blueprint, Response, render_template, request
from sqlalchemy import func
from sqlalchemy.orm import joinedload

from app.auth import admin_required, superadmin_required
from app.database import get_db
from app.models import AuditLog, Race, User

history_bp = Blueprint("history", __name__, url_prefix="/history")

ITEMS_PER_PAGE = 50

ACTION_TYPES = [
    "LOGIN", "LOGOUT", "LOGIN_FAILED",
    "CREATE", "UPDATE", "DELETE",
    "VIEW", "EXPORT", "IMPORT",
    "REGISTER", "PASSWORD_CHANGE", "EMAIL_CHANGE",
    "TOKEN_GENERATE", "ROLE_CHANGE", "USER_TOGGLE",
]


def _build_query(*, db, action=None, user_id=None, date_from=None, date_to=None, ip=None, race=None):
    q = db.query(AuditLog).options(joinedload(AuditLog.user), joinedload(AuditLog.race))

    if action:
        q = q.filter(AuditLog.action == action)
    if user_id:
        q = q.filter(AuditLog.user_id == int(user_id))
    if date_from:
        dt_from = datetime.strptime(date_from, "%Y-%m-%d")
        q = q.filter(AuditLog.timestamp >= dt_from)
    if date_to:
        dt_to = datetime.strptime(date_to, "%Y-%m-%d").replace(hour=23, minute=59, second=59)
        q = q.filter(AuditLog.timestamp <= dt_to)
    if ip:
        q = q.filter(AuditLog.ip_address.like(f"%{ip}%"))
    if race:
        q = q.outerjoin(Race, AuditLog.race_id == Race.id).filter(Race.descrizione.like(f"%{race}%"))

    return q.order_by(AuditLog.timestamp.desc())


@history_bp.route("")
@admin_required
def history_view():
    page = request.args.get("page", 1, type=int)
    per_page = request.args.get("per_page", ITEMS_PER_PAGE, type=int)

    action = request.args.get("action") or None
    user_id = request.args.get("user_id") or None
    date_from = request.args.get("date_from") or None
    date_to = request.args.get("date_to") or None
    ip = request.args.get("ip") or None
    race = request.args.get("race") or None

    with get_db() as db:
        base_q = _build_query(
            db=db,
            action=action,
            user_id=user_id,
            date_from=date_from,
            date_to=date_to,
            ip=ip,
            race=race,
        )

        total = base_q.count()
        logs = base_q.offset((page - 1) * per_page).limit(per_page).all()

        users = (
            db.query(User)
            .filter(User.audit_logs.any())
            .order_by(User.nome)
            .all()
        )

    total_pages = max(1, (total + per_page - 1) // per_page)

    return render_template(
        "history.html",
        logs=logs,
        page=page,
        per_page=per_page,
        total=total,
        total_pages=total_pages,
        users=users,
        action_types=ACTION_TYPES,
        filters={
            "action": action,
            "user_id": user_id,
            "date_from": date_from,
            "date_to": date_to,
            "ip": ip,
            "race": race,
        },
    )


@history_bp.route("/export")
@superadmin_required
def export_history():
    action = request.args.get("action") or None
    user_id = request.args.get("user_id") or None
    date_from = request.args.get("date_from") or None
    date_to = request.args.get("date_to") or None
    ip = request.args.get("ip") or None
    race = request.args.get("race") or None

    with get_db() as db:
        q = _build_query(
            db=db,
            action=action,
            user_id=user_id,
            date_from=date_from,
            date_to=date_to,
            ip=ip,
            race=race,
        )
        logs = q.all()

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
                    "action": al.action,
                    "entity_type": al.entity_type,
                    "entity_id": al.entity_id,
                    "field": al.field,
                    "old_value": al.old_value,
                    "new_value": al.new_value,
                    "description": al.description,
                    "ip_address": al.ip_address,
                    "user_agent": al.user_agent,
                    "actor_name": al.actor_name,
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
