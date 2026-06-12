from flask_wtf import FlaskForm
from wtforms import (
    DateField,
    PasswordField,
    SelectField,
    StringField,
    TextAreaField,
)
from wtforms.validators import DataRequired, Email, EqualTo, Length, Optional


class LoginForm(FlaskForm):
    email = StringField("Email", validators=[DataRequired(), Email()])
    password = PasswordField("Password", validators=[DataRequired()])


class RegisterForm(FlaskForm):
    nome = StringField("Nome", validators=[DataRequired(), Length(max=100)])
    email = StringField("Email", validators=[DataRequired(), Email()])
    password = PasswordField("Password", validators=[DataRequired(), Length(min=6)])
    token = StringField("Token di registrazione", validators=[DataRequired()])


class RaceForm(FlaskForm):
    descrizione = TextAreaField("Descrizione", validators=[DataRequired()])
    data_inizio = DateField("Data inizio", format="%Y-%m-%d", validators=[Optional()])
    data_fine = DateField("Data fine", format="%Y-%m-%d", validators=[Optional()])
    tipo_gara = SelectField("Tipo gara", coerce=str, validators=[Optional()])
    scadenza_conferma = DateField(
        "Scadenza conferma", format="%Y-%m-%d", validators=[Optional()]
    )
    stato = SelectField(
        "Stato",
        choices=[
            ("In attesa di conferma", "In attesa di conferma"),
            ("Confermato", "Confermato"),
            ("Annullato", "Annullato"),
        ],
    )
    note_auto = TextAreaField("Note automatiche", validators=[Optional()])


class SelfChangePasswordForm(FlaskForm):
    current_password = PasswordField("Password attuale", validators=[DataRequired()])
    new_password = PasswordField(
        "Nuova password", validators=[DataRequired(), Length(min=6)]
    )
    new_password_confirm = PasswordField(
        "Conferma password", validators=[DataRequired(), EqualTo("new_password")]
    )


class SelfChangeEmailForm(FlaskForm):
    password = PasswordField("Password", validators=[DataRequired()])
    new_email = StringField("Nuova email", validators=[DataRequired(), Email()])


class AdminChangePasswordForm(FlaskForm):
    new_password = PasswordField(
        "Nuova password", validators=[DataRequired(), Length(min=6)]
    )
    new_password_confirm = PasswordField(
        "Conferma password", validators=[DataRequired(), EqualTo("new_password")]
    )


class AdminChangeEmailForm(FlaskForm):
    new_email = StringField("Nuova email", validators=[DataRequired(), Email()])


class RaceTypeForm(FlaskForm):
    codice = StringField("Codice", validators=[DataRequired(), Length(max=20)])
    descrizione = StringField("Descrizione", validators=[Optional()])
