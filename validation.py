from flask import request
from marshmallow import Schema, fields, validate, ValidationError
from werkzeug.exceptions import BadRequest, UnsupportedMediaType


class UTF8String(fields.String):
    """JSON escapes can contain lone surrogates that cannot be stored as UTF-8."""

    def _deserialize(self, value, attr, data, **kwargs):
        value = super()._deserialize(value, attr, data, **kwargs)
        try:
            value.encode("utf-8")
        except UnicodeEncodeError as error:
            raise ValidationError("Must contain valid Unicode text.") from error
        return value


def password_length(value):
    if not 8 <= len(value.encode("utf-8")) <= 72:
        raise ValidationError("Password must contain between 8 and 72 UTF-8 bytes.")


class CredentialsSchema(Schema):
    username = UTF8String(required=True, validate=validate.Regexp(r"\A[a-zA-Z0-9_]{3,32}\Z"))
    password = UTF8String(required=True, validate=password_length)


class NoteSchema(Schema):
    title = UTF8String(required=True, validate=validate.Length(min=1, max=120))
    content = UTF8String(required=True, validate=validate.Length(min=1, max=10000))


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
