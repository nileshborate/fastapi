from app.schemas.teacher import TeacherCreate, TeacherOut

TEACHERS: dict[int, TeacherOut] = {}


def list_teachers(skip: int = 0, limit: int = 10) -> list[TeacherOut]:
    return list(TEACHERS.values())[skip : skip + limit]


def get_teacher(teacher_id: int) -> TeacherOut | None:
    return TEACHERS.get(teacher_id)


def create_teacher(data: TeacherCreate) -> TeacherOut:
    new_id = max(TEACHERS, default=0) + 1
    teacher = TeacherOut(id=new_id, **data.model_dump())
    TEACHERS[new_id] = teacher
    return teacher
