from app.schemas.student import StudentCreate, StudentOut

STUDENTS: dict[int, StudentOut] = {}


def list_students(skip: int = 0, limit: int = 10) -> list[StudentOut]:
    return list(STUDENTS.values())[skip : skip + limit]


def get_student(student_id: int) -> StudentOut | None:
    return STUDENTS.get(student_id)


def create_student(data: StudentCreate) -> StudentOut:
    new_id = max(STUDENTS, default=0) + 1
    student = StudentOut(id=new_id, **data.model_dump())
    STUDENTS[new_id] = student
    return student
