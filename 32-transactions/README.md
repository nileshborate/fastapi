# 32 – Transactions & Concurrency: All or Nothing, and Two Requests on One Row

**FastAPI Mastery: Zero to Production** – Video 32 · Nilesh Technology

Enrolling a student is **three** changes: take a seat, take the fee, save the enrollment.
If one fails, none may stay. And when two requests want the **last seat** at the same moment,
only one may get it. Today: transactions, rollbacks, and three ways to stay correct under concurrency.

## The project (fresh and small – Alembic)
```
32-transactions/
├── alembic/versions/0001_initial.py   # students (balance) · courses (seats_left, version) · enrollments
├── app/
│   ├── models/    student.py · course.py (version_id_col) · enrollment.py
│   ├── services/  school_service.py   (enroll: one transaction · update_course: optimistic lock)
│   └── routers/   school.py
├── demos/lost_update.py                # python -m demos.lost_update - two sessions, step by step
└── tests/         test_transactions.py · test_concurrency.py   (10 tests, 1 runs on PostgreSQL only)
```

## Run it
```bash
cd 32-transactions
pip install -r requirements.txt
copy .env.example .env          # Linux/Mac: cp .env.example .env
alembic upgrade head
fastapi dev app/main.py
python -m demos.lost_update     # the four cases below - in your terminal
pytest -v                       # 13 passed, 1 skipped (SQLite)  ·  14 passed on PostgreSQL
```

## 1. A transaction: all or nothing
```python
try:
    seat = db.execute(update(Course).where(Course.id == course.id, Course.seats_left > 0)
                      .values(seats_left=Course.seats_left - 1))
    if seat.rowcount == 0:
        raise ConflictError("Course is full")
    paid = db.execute(update(Student).where(Student.id == student.id, Student.balance >= course.fee)
                      .values(balance=Student.balance - course.fee))
    if paid.rowcount == 0:
        raise ConflictError("Not enough balance")      # the seat from step 1? rolled back
    db.add(Enrollment(student_id=student.id, course_id=course.id))
    db.commit()                                        # ALL three ...
except IntegrityError:
    db.rollback()                                      # ... or NONE
    raise ConflictError("Already enrolled") from None
except ConflictError:
    db.rollback()
    raise
```

## 2. Two requests, one row
| Case | What happens | |
|---|---|---|
| read → change in Python → write | A and B both read `1`, both write `0` – **two** students got the last seat | ❌ lost update |
| `UPDATE ... WHERE seats_left > 0` | the check and the change in ONE statement – B gets `rowcount == 0` | ✅ atomic |
| `version_id_col` | `UPDATE ... WHERE id = ? AND version = ?` – B: `StaleDataError` → 409 | ✅ optimistic |
| `select(...).with_for_update()` | PostgreSQL: `SELECT ... FOR UPDATE` – B **waits** for A (SQLite: no FOR UPDATE – it locks the whole file) | ✅ pessimistic |

## Optimistic locking in the API
```python
class Course(Base):
    version: Mapped[int] = mapped_column(default=1)
    __mapper_args__ = {"version_id_col": version}

# PATCH /courses/1  {"fee": 349, "version": 1}  -> 200, version 2
# PATCH /courses/1  {"fee": 399, "version": 1}  -> 409 "Course was changed by someone else - reload it"
```

## Interview questions
1. **What is a transaction, and what does ACID mean?** A group of changes that succeeds or fails as one. Atomicity (all or nothing), Consistency (constraints hold), Isolation (concurrent transactions don't see each other's half-done work), Durability (committed = saved, even after a crash).
2. **What is a lost update, and how do you prevent it?** Two transactions read the same value, both change it in the application, and the second write overwrites the first. Prevent it with an atomic UPDATE (the check in the WHERE), optimistic locking (a version column), or pessimistic locking (SELECT … FOR UPDATE).
3. **Optimistic or pessimistic locking – when which?** Optimistic: conflicts are rare, nobody waits, the loser gets an error and retries (great for edit forms – 409). Pessimistic: conflicts are common or a retry is expensive – the second transaction waits for the lock, but locks cost throughput and can deadlock.

## Homework
1. `DELETE /enrollments/{student_id}/{course_id}` – unenroll: give the seat back AND refund the fee, in ONE transaction (404 if not enrolled).
2. `POST /students/{student_id}/top-up` `{"amount": 200}` – add money with an atomic UPDATE (`balance = balance + :amount`), never read-modify-write. Max 10 000 per top-up (422).
3. Tests for each – including two sessions that top up at the same time: both amounts must arrive.

Answer at the start of Video 33 (Async Database Part 1).

## Homework answer
Shown at the start of Video 33. The code is in THIS folder (`services/school_service.py`, `routers/school.py`,
`schemas/school.py`, `tests/test_homework32.py`) – now **13 passed + 1 skipped** (14 on PostgreSQL).
```python
# 1. DELETE /enrollments/{student_id}/{course_id} - three changes back, ONE transaction
removed = db.execute(delete(Enrollment).where(Enrollment.student_id == student_id,
                                              Enrollment.course_id == course_id))
if removed.rowcount == 0:
    raise NotFoundError("Enrollment")                       # nothing changed yet
db.execute(update(Course).where(Course.id == course_id)
           .values(seats_left=Course.seats_left + 1))        # the seat back
db.execute(update(Student).where(Student.id == student_id)
           .values(balance=Student.balance + course.fee))    # the money back
db.commit()

# 2. POST /students/{student_id}/top-up {"amount": 200} - atomic, never read-modify-write
class TopUp(BaseModel):
    amount: int = Field(gt=0, le=10_000)
db.execute(update(Student).where(Student.id == student_id)
           .values(balance=Student.balance + data.amount))  # balance = balance + :amount
```
Two sessions that both read 500 and top up 100 and 200: the balance is **800** – nothing is lost.
