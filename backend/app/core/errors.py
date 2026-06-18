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


class ValidationFailed(DomainError):
    code = "VALIDATION_ERROR"
    status_code = 422
    message = "Validación fallida"


class UserAlreadyExists(DomainError):
    code = "USER_ALREADY_EXISTS"
    status_code = 409
    message = "El email ya está registrado"


# ---------- Events ----------
class EventNotMutable(DomainError):
    code = "EVENT_NOT_MUTABLE"
    status_code = 409
    message = "El evento solo puede editarse o eliminarse en estado Draft"


class InvalidTransition(DomainError):
    code = "INVALID_TRANSITION"
    status_code = 409
    message = "Transición de estado no permitida"


# ---------- Event Sessions ----------
class SessionOutOfRange(DomainError):
    code = "SESSION_OUT_OF_RANGE"
    status_code = 409
    message = "Sesión fuera del marco temporal del evento padre"


class SessionOverlap(DomainError):
    code = "SESSION_OVERLAP"
    status_code = 409
    message = "El ponente tiene otra sesión activa que se solapa en el tiempo"


class SessionCapacityExceedsEvent(DomainError):
    code = "SESSION_CAPACITY_EXCEEDS_EVENT"
    status_code = 409
    message = "La capacidad de la sesión no puede exceder la del evento"


class EventCapacityBelowSession(DomainError):
    code = "EVENT_CAPACITY_BELOW_SESSION"
    status_code = 409
    message = "La capacidad del evento no puede ser menor que la de una sesión existente"


# ---------- Registrations ----------
class EventFull(DomainError):
    code = "EVENT_FULL"
    status_code = 409
    message = "El evento alcanzó su capacidad máxima"


class DuplicateRegistration(DomainError):
    code = "DUPLICATE_REGISTRATION"
    status_code = 409
    message = "Ya existe una inscripción activa para este evento"


class SpeakerCannotRegister(DomainError):
    code = "SPEAKER_CANNOT_REGISTER"
    status_code = 409
    message = "Un ponente del evento no puede inscribirse como asistente"


class InvalidRegistrationState(DomainError):
    code = "INVALID_REGISTRATION_STATE"
    status_code = 409
    message = "Las inscripciones solo se aceptan cuando el evento está publicado"
