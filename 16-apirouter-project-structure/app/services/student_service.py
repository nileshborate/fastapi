from app.schemas.student import StudentCreate, StudentOut

STUDENTS: dict[int, StudentOut] = {}


def list_students() -> list[StudentOut]:
    return list(STUDENTS.values())


def get_student(student_id: int) -> StudentOut | None:
    return STUDENTS.get(student_id)


def create_student(data: StudentCreate) -> StudentOut:
    new_id = max(STUDENTS, default=0) + 1
    student = StudentOut(id=new_id, **data.model_dump())
    STUDENTS[new_id] = student
    return student
