import argparse
import getpass
import sys

from app.auth import hash_password
from app.database import Base, SessionLocal, engine
from app.models import User


def cmd_list_users(args):
    db = SessionLocal()
    try:
        users = db.query(User).order_by(User.id).all()
        if not users:
            print("Nessun utente trovato.")
            return
        print(f"{'ID':<4} {'Nome':<20} {'Email':<35} {'Ruolo':<15} {'Attivo':<7}")
        print("-" * 81)
        for u in users:
            attivo = "SI" if u.attivo else "NO"
            print(f"{u.id:<4} {u.nome:<20} {u.email:<35} {u.ruolo:<15} {attivo:<7}")
    finally:
        db.close()


def cmd_reset_password(args):
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.email == args.email).first()
        if not user:
            print(f"Errore: nessun utente con email '{args.email}'")
            sys.exit(1)
        password = args.password
        if not password:
            password = getpass.getpass("Nuova password: ")
            conferma = getpass.getpass("Conferma password: ")
            if password != conferma:
                print("Errore: le password non coincidono")
                sys.exit(1)
        if len(password) < 6:
            print("Errore: la password deve essere almeno 6 caratteri")
            sys.exit(1)
        user.password_hash = hash_password(password)
        db.commit()
        print(f"Password resettata per {user.nome} ({user.email})")
    finally:
        db.close()


def cmd_make_superadmin(args):
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.email == args.email).first()
        if not user:
            print(f"Errore: nessun utente con email '{args.email}'")
            sys.exit(1)
        old_role = user.ruolo
        user.ruolo = "superadmin"
        db.commit()
        print(
            f"Ruolo cambiato: {user.nome} ({user.email}) da '{old_role}' a 'superadmin'"
        )
    finally:
        db.close()


def cmd_make_admin(args):
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.email == args.email).first()
        if not user:
            print(f"Errore: nessun utente con email '{args.email}'")
            sys.exit(1)
        old_role = user.ruolo
        user.ruolo = "admin"
        db.commit()
        print(f"Ruolo cambiato: {user.nome} ({user.email}) da '{old_role}' a 'admin'")
    finally:
        db.close()


def cmd_create_superadmin(args):
    db = SessionLocal()
    try:
        existing = db.query(User).filter(User.email == args.email).first()
        if existing:
            print(f"Errore: email '{args.email}' già in uso")
            sys.exit(1)
        password = args.password
        if not password:
            password = getpass.getpass("Password per il nuovo SuperAdmin: ")
            conferma = getpass.getpass("Conferma password: ")
            if password != conferma:
                print("Errore: le password non coincidono")
                sys.exit(1)
        if len(password) < 6:
            print("Errore: la password deve essere almeno 6 caratteri")
            sys.exit(1)
        user = User(
            nome=args.nome,
            email=args.email,
            password_hash=hash_password(password),
            ruolo="superadmin",
            attivo=1,
        )
        db.add(user)
        db.commit()
        print(f"SuperAdmin creato: {user.nome} ({user.email})")
    finally:
        db.close()


def cmd_delete_user(args):
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.email == args.email).first()
        if not user:
            print(f"Errore: nessun utente con email '{args.email}'")
            sys.exit(1)
        if not args.yes:
            print(
                f"Stai per eliminare: {user.nome} ({user.email}) — ruolo: {user.ruolo}"
            )
            conferma = input("Confermi? (s/N): ")
            if conferma.lower() not in ("s", "si"):
                print("Annullato.")
                return
        db.delete(user)
        db.commit()
        print(f"Utente eliminato: {user.nome} ({user.email})")
    finally:
        db.close()


def main():
    Base.metadata.create_all(bind=engine)

    parser = argparse.ArgumentParser(
        description="ValBelluna Motorsport — CLI di amministrazione"
    )
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("list-users", help="Elenca tutti gli utenti")

    p_reset = sub.add_parser("reset-password", help="Resetta la password di un utente")
    p_reset.add_argument("email", help="Email dell'utente")
    p_reset.add_argument(
        "--password", help="Nuova password (opzionale, altrimenti prompt)"
    )

    p_mksa = sub.add_parser("make-superadmin", help="Promuovi un utente a superadmin")
    p_mksa.add_argument("email", help="Email dell'utente")

    p_mka = sub.add_parser("make-admin", help="Promuovi un utente ad admin")
    p_mka.add_argument("email", help="Email dell'utente")

    p_csa = sub.add_parser("create-superadmin", help="Crea un nuovo SuperAdmin")
    p_csa.add_argument("email", help="Email")
    p_csa.add_argument("nome", help="Nome completo")
    p_csa.add_argument("--password", help="Password (opzionale, altrimenti prompt)")

    p_del = sub.add_parser("delete-user", help="Elimina un utente")
    p_del.add_argument("email", help="Email dell'utente")
    p_del.add_argument("-y", "--yes", action="store_true", help="Salta conferma")

    args = parser.parse_args()

    commands = {
        "list-users": cmd_list_users,
        "reset-password": cmd_reset_password,
        "make-superadmin": cmd_make_superadmin,
        "make-admin": cmd_make_admin,
        "create-superadmin": cmd_create_superadmin,
        "delete-user": cmd_delete_user,
    }

    commands[args.command](args)


if __name__ == "__main__":
    main()
