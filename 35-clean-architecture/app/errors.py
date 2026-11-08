# Domain errors: the service speaks the language of the business - not HTTP.
class DomainError(Exception):
    status_code = 400                      # main.py turns it into an HTTP answer

    def __init__(self, message: str) -> None:
        super().__init__(message)
        self.message = message


class NotFoundError(DomainError):
    status_code = 404


class ConflictError(DomainError):
    status_code = 409


class RuleError(DomainError):              # a business rule says no
    status_code = 422
