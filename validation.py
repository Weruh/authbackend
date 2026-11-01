from flask import request
from marshmallow import Schema, fields, validate, ValidationError
from werkzeug.exceptions import BadRequest, UnsupportedMediaType


class CredentialsSchema(Schema):
    username = fields.String(required=True, validate=validate.Regexp(r"^[a-zA-Z0-9_]{3,32}$"))
    password = fields.String(required=True, validate=validate.Length(min=8, max=72))


class NoteSchema(Schema):
    title = fields.String(required=True, validate=validate.Length(min=1, max=120))
    content = fields.String(required=True, validate=validate.Length(min=1, max=10000))


def load_json(schema, partial=False):
    if not request.is_json:
        raise UnsupportedMediaType("Send a JSON body with Content-Type: application/json.")
    data = request.get_json()
    if not isinstance(data, dict) or not data:
        raise BadRequest("Send a nonempty JSON object.")
    result = schema.load(data, partial=partial)
    for field in ("title", "content"):
        if field in result:
            result[field] = result[field].strip()
            if not result[field]:
                raise ValidationError({field: ["Must not be blank."]})
    return result
