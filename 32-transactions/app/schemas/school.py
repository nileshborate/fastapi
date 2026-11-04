from pydantic import BaseModel, ConfigDict, Field


class StudentCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str = Field(min_length=2, max_length=50)
    balance: int = Field(ge=0)


class StudentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    balance: int


class CourseCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    title: str = Field(min_length=3, max_length=100)
    fee: int = Field(ge=0)
    seats_left: int = Field(ge=0)


class CourseUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    fee: int = Field(ge=0)
    version: int                    # the version the client READ - "I changed THIS one"


class CourseOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    fee: int
    seats_left: int
    version: int


class EnrollmentCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    student_id: int
    course_id: int


class TopUp(BaseModel):                     # homework (Video 32)
    model_config = ConfigDict(extra="forbid")

    amount: int = Field(gt=0, le=10_000)


class EnrollmentOut(BaseModel):
    student_id: int
    course_id: int
    balance: int                    # the student's balance AFTER paying
    seats_left: int                 # the course's seats AFTER this enrollment
