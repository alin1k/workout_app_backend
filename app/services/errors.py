"""Domain exceptions raised by the service layer.

Controllers don't catch these individually — they are translated to JSON
HTTP responses by a global handler in `app/controllers/errors.py`.
"""


class ServiceError(Exception):
    """Base for all service-layer domain exceptions."""

    status_code = 500


class NotFoundError(ServiceError):
    """A requested resource does not exist."""

    status_code = 404


class ValidationError(ServiceError):
    """The caller provided invalid input."""

    status_code = 400

    def __init__(self, message: str, field: str | None = None):
        super().__init__(message)
        self.field = field


class ConflictError(ServiceError):
    """The action would violate a uniqueness / integrity constraint."""

    status_code = 409
