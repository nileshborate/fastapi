# Video 4 - HOMEWORK
# Add the correct type hints to these 3 functions.
# Then run:   mypy --strict homework.py
# Keep fixing until mypy says:  Success: no issues found
# The answer is shared at the start of Video 5.


def full_name(first, last, middle=None):
    if middle:
        return f"{first} {middle} {last}"
    return f"{first} {last}"


def average(marks):
    return sum(marks) / len(marks)


def find_course(courses, course_id):
    for course in courses:
        if course["id"] == course_id:
            return course
    return None
