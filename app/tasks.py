"""
Scheduled tasks (APScheduler).
Run reminders, cleanup, etc.

Integration in main.py:
    from app.tasks import start_scheduler
    start_scheduler()
"""

from datetime import date, timedelta

from apscheduler.schedulers.background import BackgroundScheduler

from app.database import SessionLocal
from app.models import Participation, Race, User

scheduler = BackgroundScheduler()


def check_pending_confirmations():
    """Check races with upcoming confirmation deadlines (stub for now)."""
    db = SessionLocal()
    try:
        tomorrow = date.today() + timedelta(days=1)
        races = (
            db.query(Race)
            .filter(
                Race.scadenza_conferma == tomorrow,
                Race.stato == "Confermato",
            )
            .all()
        )
        for race in races:
            users = db.query(User).filter(User.attivo == 1).all()
            pending = []
            for u in users:
                p = (
                    db.query(Participation)
                    .filter(
                        Participation.user_id == u.id,
                        Participation.race_id == race.id,
                    )
                    .first()
                )
                if not p or p.status == "indeciso":
                    pending.append(u.nome)
            if pending:
                print(
                    f"[Reminder] Gara '{race.descrizione}' scade domani. {len(pending)} indecisi: {', '.join(pending)}"
                )
    finally:
        db.close()


def start_scheduler():
    scheduler.add_job(check_pending_confirmations, "cron", hour=9, minute=0)
    scheduler.start()
    print("⏰ Scheduler avviato")


def stop_scheduler():
    scheduler.shutdown()
