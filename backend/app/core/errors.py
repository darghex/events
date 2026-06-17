from typing import Any


class DomainError(Exception):
    """Excepción de dominio mapeable al shape canónico { error: { code, message, details } }."""

    code: str = "DOMAIN_ERROR"
    status_code: int = 400
    message: str = "Domain error"

    def __init__(self, message: str | None = None, details: dict[str, Any] | None = None) -> None:
        self.message = message or self.message
        self.details = details or {}
        super().__init__(self.message)


# ---------- Auth ----------
class AuthInvalidCredentials(DomainError):
    code = "AUTH_INVALID_CREDENTIALS"
    status_code = 401
    message = "Credenciales inválidas"


class AuthTokenExpired(DomainError):
    code = "AUTH_TOKEN_EXPIRED"
    status_code = 401
    message = "Token inválido o expirado"


class Forbidden(DomainError):
    code = "FORBIDDEN"
    status_code = 403
    message = "Permisos insuficientes"


class NotFound(DomainError):
    code = "NOT_FOUND"
    status_code = 404
    message = "Recurso no encontrado"


class UserAlreadyExists(DomainError):
    code = "USER_ALREADY_EXISTS"
    status_code = 409
    message = "El email ya está registrado"
