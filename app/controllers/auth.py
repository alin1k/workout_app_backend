from flask import Blueprint, jsonify, request
from flask_jwt_extended import get_jwt_identity, jwt_required

from app.services import auth_service
from app.services.errors import AuthenticationError

auth_bp = Blueprint("auth", __name__, url_prefix="/api/auth")


@auth_bp.post("/register")
def register():
    key = request.headers.get("X-Registration-Key", "")
    data = request.get_json(silent=True) or {}
    user, token = auth_service.register(data, key)
    return jsonify({"user": user.to_dict(), "access_token": token}), 201


@auth_bp.post("/login")
def login():
    data = request.get_json(silent=True) or {}
    user, token = auth_service.authenticate(data)
    return jsonify({"user": user.to_dict(), "access_token": token}), 200


@auth_bp.get("/me")
@jwt_required()
def me():
    user = auth_service.get_user_by_id(get_jwt_identity())
    if user is None:
        # Token references a user that no longer exists (deleted out-of-band).
        raise AuthenticationError("user no longer exists")
    return jsonify(user.to_dict())
