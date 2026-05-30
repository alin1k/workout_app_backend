from flask import Blueprint, jsonify

from app import store

sets_bp = Blueprint("sets", __name__, url_prefix="/api/sets")


@sets_bp.delete("/<int:set_id>")
def delete_set(set_id: int):
    if set_id not in store.sets:
        return jsonify({"error": "set not found"}), 404
    store.sets.pop(set_id, None)
    return "", 204
