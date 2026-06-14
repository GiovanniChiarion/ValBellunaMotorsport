import json
from datetime import UTC, date, datetime

from flask import Blueprint, Response, g, jsonify, render_template, request
from sqlalchemy import func

from app.auth import admin_required, jwt_required, superadmin_required
from app.features import feature_enabled
from app.config import get_settings
from app.database import get_db
from app.models import AuditLog, Participation, Race, RaceType, User

settings = get_settings()
races_bp = Blueprint("races", __name__, url_prefix="/races")


def _parse_date(value):
    if value:
        try:
            return datetime.fromisoformat(value).date()
        except (ValueError, TypeError):
            return None
    return None


@races_bp.route("")
@jwt_required
def calendar_view():
    year = request.args.get("year", type=int) or date.today().year
    with get_db() as db:
        races = (
            db.query(Race)
            .filter(func.strftime("%Y", Race.data_inizio) == str(year))
            .order_by(Race.data_inizio)
            .all()
        )
        years_rows = (
            db.query(func.strftime("%Y", Race.data_inizio))
            .distinct()
            .order_by(func.strftime("%Y", Race.data_inizio))
            .all()
        )
        years = [r[0] for r in years_rows] or [year]

        participations = {
            p.race_id: p
            for p in db.query(Participation)
            .filter(Participation.user_id == g.current_user.id)
            .all()
        }

        macchina_counts = {}
        for race in races:
            macchina_counts[race.id] = (
                db.query(func.count(Participation.id))
                .filter(
                    Participation.race_id == race.id,
                    Participation.con_macchina == 1,
                    Participation.status == "si",
                )
                .scalar()
                or 0
            )

    return render_template(
        "dashboard.html",
        races=races,
        year=year,
        years=years,
        participations=participations,
        macchina_counts=macchina_counts,
        today=date.today(),
        current_user=g.current_user,
        filters_enabled=feature_enabled("calendar_filters", g.current_user.ruolo),
    )


@races_bp.route("/<int:race_id>")
@jwt_required
def race_detail(race_id):
    with get_db() as db:
        race = db.query(Race).filter(Race.id == race_id).first()
        if not race:
            return jsonify({"error": "Gara non trovata"}), 404

        members = (
            db.query(User)
            .filter(User.attivo == 1, User.ruolo != "superadmin")
            .order_by(User.nome)
            .all()
        )
        participations = {
            p.user_id: p
            for p in db.query(Participation)
            .filter(Participation.race_id == race_id)
            .all()
        }

    is_admin = g.current_user.ruolo in ("admin", "superadmin")
    can_change = (
        race.scadenza_conferma is None or date.today() <= race.scadenza_conferma
    ) or is_admin

    si_names = [
        m.nome
        for m in members
        if participations.get(m.id) and participations[m.id].status == "si"
    ]
    si_with_car = [
        f"{m.nome}{' 🚗' if participations.get(m.id) and participations[m.id].con_macchina else ''}"
        for m in members
        if participations.get(m.id) and participations[m.id].status == "si"
    ]

    return render_template(
        "race_detail.html",
        race=race,
        members=members,
        participations=participations,
        is_admin=is_admin,
        can_change=can_change,
        today=date.today(),
        si_names=si_names,
        si_names_json=si_names,
        si_with_car=si_with_car,
        current_user=g.current_user,
    )


@races_bp.route("/<int:race_id>/edit", methods=["GET"])
@admin_required
def edit_race_page(race_id):
    with get_db() as db:
        race = db.query(Race).filter(Race.id == race_id).first()
        if not race:
            return jsonify({"error": "Gara non trovata"}), 404
        types = db.query(RaceType).order_by(RaceType.codice).all()

    return render_template(
        "admin/race_form.html", race=race, race_types=types, current_user=g.current_user
    )


@races_bp.route("/<int:race_id>/edit", methods=["POST"])
@admin_required
def edit_race(race_id):
    data = request.get_json(silent=True) or {}
    with get_db() as db:
        race = db.query(Race).filter(Race.id == race_id).first()
        if not race:
            return jsonify({"error": "Gara non trovata"}), 404

        date_fields = {"data_inizio", "data_fine", "scadenza_conferma"}
        text_fields = {"descrizione", "tipo_gara", "stato", "note_auto"}

        for field in date_fields | text_fields:
            if field not in data:
                continue
            value = _parse_date(data[field]) if field in date_fields else data[field]
            old = getattr(race, field)
            if old != value:
                setattr(race, field, value)
                db.add(
                    AuditLog(
                        user_id=g.current_user.id,
                        race_id=race.id,
                        field=field,
                        old_value=str(old) if old is not None else None,
                        new_value=str(value) if value is not None else None,
                    )
                )

        db.commit()

    return jsonify({"message": "Gara aggiornata"})


@races_bp.route("", methods=["POST"])
@admin_required
def create_race():
    data = request.get_json(silent=True) or {}
    with get_db() as db:
        race = Race(
            data_inizio=_parse_date(data.get("data_inizio")),
            data_fine=_parse_date(data.get("data_fine")),
            descrizione=data.get("descrizione", ""),
            tipo_gara=data.get("tipo_gara"),
            scadenza_conferma=_parse_date(data.get("scadenza_conferma")),
            stato=data.get("stato", "In attesa di conferma"),
            note_auto=data.get("note_auto"),
        )
        db.add(race)
        db.commit()
        db.refresh(race)
        race_id = race.id
        race_desc = race.descrizione
        db.add(
            AuditLog(
                user_id=g.current_user.id,
                race_id=race_id,
                field="descrizione",
                old_value=None,
                new_value=race_desc,
            )
        )
        db.commit()

    return jsonify(
        {"message": "Gara creata", "race": {"id": race_id, "descrizione": race_desc}}
    )


@races_bp.route("/<int:race_id>/delete", methods=["POST"])
@admin_required
def delete_race(race_id):
    with get_db() as db:
        race = db.query(Race).filter(Race.id == race_id).first()
        if not race:
            return jsonify({"error": "Gara non trovata"}), 404
        db.delete(race)
        db.commit()

    return jsonify({"message": "Gara eliminata"})


@races_bp.route("/admin/dashboard")
@admin_required
def admin_dashboard():
    with get_db() as db:
        total_members = db.query(User).filter(User.ruolo != "superadmin").count()
        active_members = (
            db.query(User).filter(User.attivo == 1, User.ruolo != "superadmin").count()
        )
        admin_count = db.query(User).filter(User.ruolo == "admin").count()
        total_races = db.query(Race).count()

    return render_template(
        "admin/dashboard.html",
        total_members=total_members,
        active_members=active_members,
        admin_count=admin_count,
        total_races=total_races,
        current_user=g.current_user,
    )


@races_bp.route("/admin/new")
@admin_required
def new_race_page():
    with get_db() as db:
        types = db.query(RaceType).order_by(RaceType.codice).all()

    return render_template(
        "admin/race_form.html", race=None, race_types=types, current_user=g.current_user
    )


@races_bp.route("/admin/list")
@admin_required
def admin_races_list():
    with get_db() as db:
        races = db.query(Race).order_by(Race.data_inizio).all()

    return render_template("admin/races.html", races=races, current_user=g.current_user)


@races_bp.route("/admin/members")
@admin_required
def admin_members():
    with get_db() as db:
        members = (
            db.query(User).filter(User.ruolo != "superadmin").order_by(User.nome).all()
        )
        race_count = db.query(Race).count()

    return render_template(
        "admin/members.html",
        members=members,
        race_count=race_count,
        current_user=g.current_user,
    )


@races_bp.route("/admin/members/<int:user_id>/role", methods=["POST"])
@admin_required
def admin_set_role(user_id):
    data = request.get_json(silent=True) or {}
    ruolo = data.get("ruolo")
    if ruolo not in ("membro", "admin"):
        return jsonify({"error": "Ruolo non valido"}), 400

    with get_db() as db:
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            return jsonify({"error": "Utente non trovato"}), 404

        old = user.ruolo
        user.ruolo = ruolo
        db.add(
            AuditLog(
                user_id=g.current_user.id,
                field="user.ruolo",
                old_value=old,
                new_value=ruolo,
            )
        )
        db.commit()

    return jsonify({"message": f"Ruolo cambiato da {old} a {ruolo}"})


@races_bp.route("/admin/members/<int:user_id>/toggle", methods=["POST"])
@admin_required
def admin_toggle_user(user_id):
    with get_db() as db:
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            return jsonify({"error": "Utente non trovato"}), 404
        if user.id == g.current_user.id:
            return jsonify({"error": "Non puoi disattivare te stesso"}), 400

        old = "attivo" if user.attivo else "disattivato"
        user.attivo = 0 if user.attivo else 1
        new = "attivo" if user.attivo else "disattivato"
        new_attivo = user.attivo
        db.add(
            AuditLog(
                user_id=g.current_user.id,
                field="user.attivo",
                old_value=old,
                new_value=new,
            )
        )
        db.commit()

    return jsonify({"message": f"Utente {new}", "attivo": new_attivo})


@races_bp.route("/admin/types")
@admin_required
def admin_race_types_page():
    with get_db() as db:
        types = db.query(RaceType).order_by(RaceType.codice).all()

    return render_template(
        "admin/race_types.html", race_types=types, current_user=g.current_user
    )


@races_bp.route("/admin/types", methods=["POST"])
@admin_required
def create_race_type():
    data = request.get_json(silent=True) or {}
    codice = data.get("codice", "").strip()
    descrizione = data.get("descrizione", "").strip()

    if not codice:
        return jsonify({"error": "Codice richiesto"}), 400

    with get_db() as db:
        existing = db.query(RaceType).filter(RaceType.codice == codice).first()
        if existing:
            return jsonify({"error": "Codice già esistente"}), 400

        rt = RaceType(codice=codice, descrizione=descrizione)
        db.add(rt)
        db.commit()
        db.refresh(rt)

    return jsonify(
        {
            "message": "Tipo gara creato",
            "race_type": {
                "id": rt.id,
                "codice": rt.codice,
                "descrizione": rt.descrizione,
            },
        }
    )


@races_bp.route("/admin/types/<int:type_id>/delete", methods=["POST"])
@admin_required
def delete_race_type(type_id):
    with get_db() as db:
        rt = db.query(RaceType).filter(RaceType.id == type_id).first()
        if not rt:
            return jsonify({"error": "Tipo non trovato"}), 404
        db.delete(rt)
        db.commit()

    return jsonify({"message": "Tipo gara eliminato"})


@races_bp.route("/admin/export")
@superadmin_required
def export_all_data():
    include = request.args.get("include")
    sections = (
        set(s.strip() for s in include.split(","))
        if include
        else {"gare", "utenti", "logs"}
    )

    data_section = {}

    with get_db() as db:
        if "gare" in sections or not include:
            race_types = db.query(RaceType).order_by(RaceType.codice).all()
            races = db.query(Race).order_by(Race.id).all()
            participations = db.query(Participation).order_by(Participation.id).all()

            data_section["race_types"] = [
                {"codice": rt.codice, "descrizione": rt.descrizione}
                for rt in race_types
            ]
            data_section["races"] = [
                {
                    "id": r.id,
                    "data_inizio": r.data_inizio.isoformat() if r.data_inizio else None,
                    "data_fine": r.data_fine.isoformat() if r.data_fine else None,
                    "descrizione": r.descrizione,
                    "tipo_gara": r.tipo_gara,
                    "scadenza_conferma": r.scadenza_conferma.isoformat()
                    if r.scadenza_conferma
                    else None,
                    "stato": r.stato,
                    "note_auto": r.note_auto,
                }
                for r in races
            ]
            data_section["participations"] = [
                {
                    "id": p.id,
                    "user_id": p.user_id,
                    "race_id": p.race_id,
                    "status": p.status,
                    "nota_personale": p.nota_personale,
                    "con_macchina": p.con_macchina,
                }
                for p in participations
            ]

        if "utenti" in sections or not include:
            users = db.query(User).order_by(User.id).all()
            data_section["users"] = [
                {
                    "id": u.id,
                    "nome": u.nome,
                    "email": u.email,
                    "password_hash": u.password_hash,
                    "ruolo": u.ruolo,
                    "attivo": u.attivo,
                }
                for u in users
            ]

        if "logs" in sections or not include:
            audit_logs = db.query(AuditLog).order_by(AuditLog.id).all()
            data_section["audit_logs"] = [
                {
                    "id": al.id,
                    "user_id": al.user_id,
                    "race_id": al.race_id,
                    "field": al.field,
                    "old_value": al.old_value,
                    "new_value": al.new_value,
                    "timestamp": al.timestamp.isoformat() if al.timestamp else None,
                }
                for al in audit_logs
            ]

    data = {
        "export_date": datetime.now(UTC).isoformat(),
        "app_version": settings.app_version,
        "data": data_section,
    }

    return Response(
        json.dumps(data, indent=2, ensure_ascii=False),
        mimetype="application/json",
        headers={
            "Content-Disposition": "attachment; filename=valbellunamotorsport-backup.json"
        },
    )


@races_bp.route("/admin/import", methods=["POST"])
@superadmin_required
def import_all_data():
    file = request.files.get("file")
    if not file:
        return jsonify({"error": "File richiesto"}), 400

    try:
        backup = json.loads(file.read())
    except (json.JSONDecodeError, UnicodeDecodeError) as e:
        return jsonify({"error": f"File JSON non valido: {e}"}), 400

    data = backup.get("data")
    if not data:
        return jsonify({"error": "JSON non valido: manca 'data'"}), 400

    with get_db() as db:
        try:
            for rt in data.get("race_types", []):
                existing = (
                    db.query(RaceType).filter(RaceType.codice == rt["codice"]).first()
                )
                if existing:
                    existing.descrizione = rt.get("descrizione")
                else:
                    db.add(
                        RaceType(codice=rt["codice"], descrizione=rt.get("descrizione"))
                    )
            db.flush()

            for u in data.get("users", []):
                existing = db.query(User).filter(User.id == u["id"]).first()
                if existing:
                    existing.nome = u["nome"]
                    existing.email = u["email"]
                    existing.password_hash = u.get(
                        "password_hash", existing.password_hash
                    )
                    existing.ruolo = u.get("ruolo", existing.ruolo)
                    existing.attivo = u.get("attivo", existing.attivo)
                else:
                    db.add(
                        User(
                            id=u["id"],
                            nome=u["nome"],
                            email=u["email"],
                            password_hash=u.get("password_hash", ""),
                            ruolo=u.get("ruolo", "membro"),
                            attivo=u.get("attivo", 1),
                        )
                    )
            db.flush()

            for r in data.get("races", []):
                existing = db.query(Race).filter(Race.id == r["id"]).first()
                if existing:
                    existing.data_inizio = _parse_date(r.get("data_inizio"))
                    existing.data_fine = _parse_date(r.get("data_fine"))
                    existing.descrizione = r["descrizione"]
                    existing.tipo_gara = r.get("tipo_gara")
                    existing.scadenza_conferma = _parse_date(r.get("scadenza_conferma"))
                    existing.stato = r.get("stato", "In attesa di conferma")
                    existing.note_auto = r.get("note_auto")
                else:
                    db.add(
                        Race(
                            id=r["id"],
                            data_inizio=_parse_date(r.get("data_inizio")),
                            data_fine=_parse_date(r.get("data_fine")),
                            descrizione=r["descrizione"],
                            tipo_gara=r.get("tipo_gara"),
                            scadenza_conferma=_parse_date(r.get("scadenza_conferma")),
                            stato=r.get("stato", "In attesa di conferma"),
                            note_auto=r.get("note_auto"),
                        )
                    )
            db.flush()

            for p in data.get("participations", []):
                existing = (
                    db.query(Participation).filter(Participation.id == p["id"]).first()
                )
                if existing:
                    existing.user_id = p["user_id"]
                    existing.race_id = p["race_id"]
                    existing.status = p.get("status", existing.status)
                    existing.nota_personale = p.get("nota_personale")
                    existing.con_macchina = p.get("con_macchina", existing.con_macchina)
                else:
                    db.add(
                        Participation(
                            id=p["id"],
                            user_id=p["user_id"],
                            race_id=p["race_id"],
                            status=p.get("status", "indeciso"),
                            nota_personale=p.get("nota_personale"),
                            con_macchina=p.get("con_macchina", 0),
                        )
                    )
            db.flush()

            for al in data.get("audit_logs", []):
                existing = db.query(AuditLog).filter(AuditLog.id == al["id"]).first()
                if existing:
                    existing.user_id = al.get("user_id")
                    existing.race_id = al.get("race_id")
                    existing.field = al["field"]
                    existing.old_value = al.get("old_value")
                    existing.new_value = al.get("new_value")
                else:
                    db.add(
                        AuditLog(
                            id=al["id"],
                            user_id=al.get("user_id"),
                            race_id=al.get("race_id"),
                            field=al["field"],
                            old_value=al.get("old_value"),
                            new_value=al.get("new_value"),
                            timestamp=datetime.fromisoformat(al["timestamp"])
                            if al.get("timestamp")
                            else datetime.now(UTC),
                        )
                    )

            db.commit()

        except Exception as e:
            db.rollback()
            return jsonify({"error": f"Errore durante l'import: {e}"}), 400

    return jsonify({"message": "Backup ripristinato con successo"})
