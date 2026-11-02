# The "detail" schemas: one object + the objects on the OTHER side of the link table
from app.schemas.course import CourseOut
from app.schemas.student import StudentOut


class StudentDetail(StudentOut):
    courses: list[CourseOut]            # CourseOut has no students -> no endless loop


class CourseDetail(CourseOut):
    students: list[StudentOut]
