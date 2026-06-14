from datetime import UTC, datetime

from flask import Blueprint, g, jsonify, request

from app.audit import log_action
from app.auth import admin_required, jwt_required
from app.database import get_db
from app.models import Participation, Race

participation_bp = Blueprint("participation", __name__, url_prefix="/participation")


@participation_bp.route("/<int:race_id>", methods=["POST"])
@jwt_required
def set_participation(race_id):
    data = request.get_json(silent=True) or {}
    status = data.get("status", "").strip().lower()

    if status not in ("si", "no", "indeciso"):
        return jsonify({"error": "Status non valido"}), 400

    with get_db() as db:
        race = db.query(Race).filter(Race.id == race_id).first()
        if not race:
            return jsonify({"error": "Gara non trovata"}), 404

        if race.scadenza_conferma and race.scadenza_conferma < datetime.now(UTC).date():
            return jsonify({"error": "Scadenza conferma superata"}), 400

        participation = (
            db.query(Participation)
            .filter(
                Participation.user_id == g.current_user.id,
                Participation.race_id == race_id,
            )
            .first()
        )

        now = datetime.now(UTC)
        if participation:
            old_status = participation.status
            participation.status = status
            participation.updated_at = now
            _log(
                db,
                g.current_user.id,
                race_id,
                "participation.status",
                old_status,
                status,
            )
        else:
            participation = Participation(
                user_id=g.current_user.id,
                race_id=race_id,
                status=status,
                created_at=now,
                updated_at=now,
            )
            db.add(participation)
            _log(db, g.current_user.id, race_id, "participation.status", None, status)

        db.commit()

    return jsonify({"message": "Stato aggiornato"})


@participation_bp.route("/<int:race_id>/nota", methods=["POST"])
@jwt_required
def update_nota(race_id):
    data = request.get_json(silent=True) or {}
    nota = data.get("nota", "")

    with get_db() as db:
        participation = (
            db.query(Participation)
            .filter(
                Participation.user_id == g.current_user.id,
                Participation.race_id == race_id,
            )
            .first()
        )

        if not participation:
            return jsonify({"error": "Partecipazione non trovata"}), 404

        old_nota = participation.nota_personale
        participation.nota_personale = nota
        participation.updated_at = datetime.now(UTC)
        _log(db, g.current_user.id, race_id, "participation.nota", old_nota, nota)
        db.commit()

    return jsonify({"message": "Nota aggiornata"})


@participation_bp.route("/<int:race_id>/macchina", methods=["POST"])
@jwt_required
def toggle_macchina(race_id):
    with get_db() as db:
        participation = (
            db.query(Participation)
            .filter(
                Participation.user_id == g.current_user.id,
                Participation.race_id == race_id,
            )
            .first()
        )

        if not participation:
            return jsonify({"error": "Partecipazione non trovata"}), 404

        old_val = participation.con_macchina
        participation.con_macchina = 1 - participation.con_macchina
        participation.updated_at = datetime.now(UTC)
        _log(
            db,
            g.current_user.id,
            race_id,
            "participation.con_macchina",
            str(old_val),
            str(participation.con_macchina),
        )
        db.commit()

    return jsonify({"message": "Macchina aggiornata"})


@participation_bp.route("/admin/<int:user_id>/<int:race_id>", methods=["POST"])
@admin_required
def admin_set_participation(user_id, race_id):
    data = request.get_json(silent=True) or {}
    status = data.get("status", "").strip().lower()

    if status not in ("si", "no", "indeciso"):
        return jsonify({"error": "Status non valido"}), 400

    with get_db() as db:
        race = db.query(Race).filter(Race.id == race_id).first()
        if not race:
            return jsonify({"error": "Gara non trovata"}), 404

        participation = (
            db.query(Participation)
            .filter(
                Participation.user_id == user_id,
                Participation.race_id == race_id,
            )
            .first()
        )

        now = datetime.now(UTC)
        if participation:
            old_status = participation.status
            participation.status = status
            participation.updated_at = now
            _log(db, user_id, race_id, "participation.status", old_status, status)
        else:
            participation = Participation(
                user_id=user_id,
                race_id=race_id,
                status=status,
                created_at=now,
                updated_at=now,
            )
            db.add(participation)
            _log(db, user_id, race_id, "participation.status", None, status)

        db.commit()

    return jsonify({"message": "Stato aggiornato"}), 200


def _log(db, user_id, race_id, field, old_value, new_value, description=None):
    if description is None:
        race = db.query(Race).filter(Race.id == race_id).first()
        race_name = f" su {race.descrizione}" if race else ""
        if field == "participation.status":
            description = f"Status: {old_value} → {new_value}{race_name}"
        elif field == "participation.con_macchina":
            desc = "Sì" if new_value == "1" else "No"
            description = f"Macchina: {desc}{race_name}"
        else:
            description = f"Nota aggiornata{race_name}"
    log_action(
        db=db,
        action="UPDATE",
        entity_type="participation",
        user_id=user_id,
        race_id=race_id,
        field=field,
        old_value=old_value,
        new_value=new_value,
        description=description,
    )
