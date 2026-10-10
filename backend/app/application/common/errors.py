class ApplicationError(Exception):
    status_code = 400
    code = "application_error"

    def __init__(self, message: str, *, details: object | None = None) -> None:
        super().__init__(message)
        self.details = details


class ConflictError(ApplicationError):
    status_code = 409
    code = "conflict"


class AuthenticationError(ApplicationError):
    status_code = 401
    code = "authentication_failed"


class AuthorizationError(ApplicationError):
    status_code = 403
    code = "forbidden"


class NotFoundError(ApplicationError):
    status_code = 404
    code = "not_found"


class ValidationError(ApplicationError):
    status_code = 422
    code = "validation_error"
