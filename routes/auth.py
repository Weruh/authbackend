"""Registration and session authentication endpoints."""
from secrets import token_urlsafe

from flask import Blueprint, jsonify, session
from marshmallow import ValidationError
from sqlalchemy.exc import IntegrityError
from werkzeug.exceptions import Conflict

from extensions import db
from models import User
from validation import CredentialsSchema, load_json

auth = Blueprint("auth", __name__)


def start_session(user):
    session.clear()
    session["user_id"] = user.id
    session["csrf_token"] = token_urlsafe(32)
    session.permanent = True
    return {**user.to_dict(), "csrf_token": session["csrf_token"]}


@auth.post("/signup")
def signup():
    data = load_json(CredentialsSchema())
    user = User(username=data["username"])
    try:
        user.password_hash = data["password"]
    except ValueError as error:
        raise ValidationError({"password": [str(error)]}) from error
    db.session.add(user)
    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        raise Conflict("Username is already registered.")
    return jsonify(start_session(user)), 201
