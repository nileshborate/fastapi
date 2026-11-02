# Domain errors: the services raise them, main.py turns them into HTTP answers
class NotFoundError(Exception):
    def __init__(self, what: str) -> None:
        super().__init__(f"{what} not found")           # -> 404


class ConflictError(Exception):
    def __init__(self, message: str) -> None:
        super().__init__(message)                       # -> 409
