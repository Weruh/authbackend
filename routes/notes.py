"""Private note endpoints; every query is scoped to the signed-in user."""
from flask import Blueprint, g, jsonify, request
from werkzeug.exceptions import BadRequest, NotFound

from extensions import db
from models import Note
from security import login_required
from validation import NoteSchema, load_json

notes = Blueprint("notes", __name__)


def positive_integer(name, default, maximum=None):
    raw = request.args.get(name, str(default))
    if not raw.isascii() or not raw.isdecimal() or len(raw) > 9:
        raise BadRequest(f"{name} must be a positive integer.")
    value = int(raw)
    if value < 1 or (maximum is not None and value > maximum):
        raise BadRequest(f"{name} must be between 1 and {maximum}." if maximum else f"{name} must be positive.")
    return value


@notes.get("/notes")
@login_required
def index():
    page = positive_integer("page", 1)
    per_page = positive_integer("per_page", 10, 100)
    result = db.paginate(
        db.select(Note).filter_by(user_id=g.user.id).order_by(Note.id.desc()),
        page=page, per_page=per_page, error_out=False,
    )
    return jsonify(
        notes=[note.to_dict() for note in result.items],
        page=result.page, per_page=result.per_page, total=result.total,
        pages=result.pages, has_next=result.has_next, has_prev=result.has_prev,
    )


@notes.post("/notes")
@login_required
def create_note():
    data = load_json(NoteSchema())
    note = Note(**data, user_id=g.user.id)
    db.session.add(note)
    db.session.commit()
    response = jsonify(note.to_dict())
    response.status_code = 201
    response.headers["Location"] = f"/notes/{note.id}"
    return response


def owned_note(note_id):
    note = db.session.execute(
        db.select(Note).filter_by(id=note_id, user_id=g.user.id)
    ).scalar_one_or_none()
    if note is None:
        # Match missing IDs so another user's records cannot be enumerated.
        raise NotFound("Note not found.")
    return note


@notes.get("/notes/<int:note_id>")
@login_required
def show_note(note_id):
    return jsonify(owned_note(note_id).to_dict())
