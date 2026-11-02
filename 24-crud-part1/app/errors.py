# Domain errors: the SERVICES raise them - no HTTP inside.  main.py turns them into HTTP answers.
class NotFoundError(Exception):
    def __init__(self, what: str) -> None:
        super().__init__(f"{what} not found")            # e.g. "Course not found"


class AlreadyExistsError(Exception):
    def __init__(self, message: str) -> None:
        super().__init__(message)                        # e.g. "Course title already exists"
