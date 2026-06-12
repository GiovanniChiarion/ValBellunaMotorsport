from flask import Blueprint, render_template
from sqlalchemy import case, func

from app.auth import admin_required
from app.database import get_db
from app.models import Participation, Race, User

reports_bp = Blueprint("reports", __name__, url_prefix="/reports")


@reports_bp.route("")
@admin_required
def reports_index():
    with get_db() as db:
        total_members = (
            db.query(User).filter(User.attivo == 1, User.ruolo != "superadmin").count()
        )
        total_races = db.query(Race).count()
        active_races = db.query(Race).filter(Race.stato == "Confermato").count()

        member_stats = (
            db.query(
                User.id,
                User.nome,
                func.count(Participation.id).label("totale"),
                func.sum(case((Participation.status == "si", 1), else_=0)).label(
                    "si_count"
                ),
                func.sum(case((Participation.status == "no", 1), else_=0)).label(
                    "no_count"
                ),
                func.sum(case((Participation.status == "indeciso", 1), else_=0)).label(
                    "indeciso_count"
                ),
            )
            .outerjoin(Participation, User.id == Participation.user_id)
            .filter(User.attivo == 1, User.ruolo != "superadmin")
            .group_by(User.id, User.nome)
            .order_by(User.nome)
            .all()
        )

        race_stats = (
            db.query(
                Race.id,
                Race.descrizione,
                Race.data_inizio,
                Race.stato,
                func.count(Participation.id).label("totale"),
                func.sum(case((Participation.status == "si", 1), else_=0)).label(
                    "si_count"
                ),
                func.sum(case((Participation.status == "no", 1), else_=0)).label(
                    "no_count"
                ),
                func.sum(case((Participation.status == "indeciso", 1), else_=0)).label(
                    "indeciso_count"
                ),
            )
            .outerjoin(Participation, Race.id == Participation.race_id)
            .group_by(Race.id)
            .order_by(Race.data_inizio)
            .all()
        )

    return render_template(
        "reports/index.html",
        total_members=total_members,
        total_races=total_races,
        active_races=active_races,
        member_stats=member_stats,
        race_stats=race_stats,
    )
