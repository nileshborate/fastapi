# Video 4 - mypy catches type mistakes BEFORE you run the program
# Run:  pip install mypy
#       mypy mypy_demo.py
# Expected: error: Argument 1 to "get_course" has incompatible type "str"; expected "int"


def get_course(course_id: int) -> str:
    return f"Course number {course_id}"


print(get_course(7))     # OK
print(get_course("7"))   # mypy reports this line
