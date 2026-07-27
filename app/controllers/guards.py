"""HTTP-layer authorization guards.

`admin_required` stacks under the `@jwt_required()` line that every
protected route already carries:

    @some_bp.delete("/<int:x>")
    @jwt_required()
    @admin_required
    def handler(x): ...

Decorators apply bottom-up, so the effective wrapping is
jwt_required(admin_required(handler)) — the token is verified first, then
the flag. `admin_required` re-runs `verify_jwt_in_request()` itself (cheap
and idempotent) so it still fails closed with a proper 401 if the
`@jwt_required()` line is ever forgotten. The authorization decision itself
lives in the service layer; this module is only the Flask adapter.
"""

from functools import wraps

from flask_jwt_extended import get_jwt_identity, verify_jwt_in_request

from app.services import auth_service


def admin_required(fn):
    # @wraps matters: Flask keys view functions by __name__, and two
    # `wrapper`-named views on one blueprint collide at registration.
    @wraps(fn)
    def wrapper(*args, **kwargs):
        verify_jwt_in_request()
        auth_service.require_admin(get_jwt_identity())
        return fn(*args, **kwargs)

    return wrapper
