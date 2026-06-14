from datetime import UTC, datetime

from sqlalchemy import Column, Date, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship

from app.database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    nome = Column(String(100), nullable=False)
    email = Column(String(255), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    ruolo = Column(String(20), nullable=False, default="membro")
    attivo = Column(Integer, nullable=False, default=1)

    participations = relationship(
        "Participation", back_populates="user", cascade="all, delete-orphan"
    )
    audit_logs = relationship(
        "AuditLog", back_populates="user", cascade="save-update, merge"
    )


class RaceType(Base):
    __tablename__ = "race_types"

    id = Column(Integer, primary_key=True, index=True)
    codice = Column(String(20), unique=True, nullable=False)
    descrizione = Column(String(200), nullable=True)


class Race(Base):
    __tablename__ = "races"

    id = Column(Integer, primary_key=True, index=True)
    data_inizio = Column(Date, nullable=True)
    data_fine = Column(Date, nullable=True)
    descrizione = Column(String(500), nullable=False)
    tipo_gara = Column(String(20), nullable=True)
    scadenza_conferma = Column(Date, nullable=True)
    stato = Column(String(50), nullable=False, default="In attesa di conferma")
    note_auto = Column(Text, nullable=True)
    created_at = Column(DateTime, nullable=False, default=lambda: datetime.now(UTC))

    participations = relationship(
        "Participation", back_populates="race", cascade="all, delete-orphan"
    )
    audit_logs = relationship(
        "AuditLog", back_populates="race", cascade="save-update, merge"
    )


class Participation(Base):
    __tablename__ = "participations"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    race_id = Column(Integer, ForeignKey("races.id"), nullable=False)
    status = Column(String(20), nullable=False, default="indeciso")
    nota_personale = Column(Text, nullable=True)
    con_macchina = Column(Integer, nullable=False, default=0)
    created_at = Column(DateTime, nullable=False, default=lambda: datetime.now(UTC))
    updated_at = Column(
        DateTime,
        nullable=False,
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
    )

    user = relationship("User", back_populates="participations")
    race = relationship("Race", back_populates="participations")


class InviteToken(Base):
    __tablename__ = "invite_tokens"

    id = Column(Integer, primary_key=True)
    token = Column(String(64), unique=True, nullable=False, index=True)
    created_at = Column(DateTime, nullable=False, default=lambda: datetime.now(UTC))
    expires_at = Column(DateTime, nullable=True)
    used_at = Column(DateTime, nullable=True)
    created_by_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    used_by_id = Column(Integer, ForeignKey("users.id"), nullable=True)


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    race_id = Column(Integer, ForeignKey("races.id"), nullable=True)
    field = Column(String(100), nullable=True)
    old_value = Column(Text, nullable=True)
    new_value = Column(Text, nullable=True)
    timestamp = Column(DateTime, nullable=False, default=lambda: datetime.now(UTC))
    action = Column(String(50), nullable=True)
    entity_type = Column(String(50), nullable=True)
    entity_id = Column(Integer, nullable=True)
    ip_address = Column(String(45), nullable=True)
    user_agent = Column(String(255), nullable=True)
    actor_name = Column(String(100), nullable=True)
    description = Column(String(500), nullable=True)

    user = relationship("User", back_populates="audit_logs")
    race = relationship("Race", back_populates="audit_logs")
