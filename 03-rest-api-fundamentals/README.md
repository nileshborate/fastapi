# Video 3 – REST API Fundamentals

REST = an architectural style: **resources** (nouns) + **HTTP methods** (verbs) + **JSON** + correct **status codes**.

## URL design rules
| Rule | ✅ Good | ❌ Avoid |
|------|---------|---------|
| Plural nouns | `/courses`, `/courses/7` | `/getCourses`, `/course` |
| Lowercase + hyphens | `/course-categories` | `/CourseCategories` |
| Nest for ownership (1–2 levels) | `/courses/7/lessons` | `/courses/7/lessons/3/comments/9/likes` |
| Query for filter / sort / page | `/courses?level=beginner&sort=price&page=2` | `/beginnerCoursesSortedByPrice` |
| Version your API | `/v1/courses` | – |

## The 5 main methods
| Method | Example | Action | Success code | Safe | Idempotent |
|--------|---------|--------|--------------|------|------------|
| GET | `/courses/7` | Read | 200 OK | ✅ | ✅ |
| POST | `/courses` | Create | 201 Created | ❌ | ❌ |
| PUT | `/courses/7` | Replace whole resource | 200 OK | ❌ | ✅ |
| PATCH | `/courses/7` | Update some fields | 200 OK | ❌ | depends |
| DELETE | `/courses/7` | Delete | 204 No Content (or 200) | ❌ | ✅ |

## Status codes you'll actually use
`200` OK · `201` Created · `204` No Content · `400` Bad Request · `401` Unauthorized (who are you?) · `403` Forbidden (not allowed) · `404` Not Found · `409` Conflict · `422` Unprocessable Content (FastAPI validation) · `500` Internal Server Error

## Course Hub API – our design (we build this in the playlist)
| Method | Endpoint | Purpose |
|--------|----------|---------|
| GET | `/courses` | List courses (filter: `level`, `sort`, `page`) |
| POST | `/courses` | Create a course |
| GET | `/courses/{id}` | Get one course |
| PATCH | `/courses/{id}` | Update a course |
| DELETE | `/courses/{id}` | Delete a course |
| GET | `/courses/{id}/lessons` | Lessons of a course |
| POST | `/students` | Register a student |
| GET | `/students/{id}/courses` | Courses a student is enrolled in |
| POST | `/enrolments` | Enrol a student in a course |
| DELETE | `/enrolments/{id}` | Cancel an enrolment |

## Try all 5 methods
```bash
curl -i https://jsonplaceholder.typicode.com/posts/1
curl -i -X POST   https://jsonplaceholder.typicode.com/posts   -H "Content-Type: application/json" -d '{"title":"New","body":"Hi","userId":1}'
curl -i -X PUT    https://jsonplaceholder.typicode.com/posts/1 -H "Content-Type: application/json" -d '{"id":1,"title":"Replaced","body":"All fields","userId":1}'
curl -i -X PATCH  https://jsonplaceholder.typicode.com/posts/1 -H "Content-Type: application/json" -d '{"title":"Only title"}'
curl -i -X DELETE https://jsonplaceholder.typicode.com/posts/1
```
Or with Python (no install): `python rest_methods.py`

## Interview questions
1. **PUT vs PATCH?** PUT replaces the whole resource; PATCH updates only the fields you send.
2. **What is idempotent? Which methods are?** Calling it many times gives the same final result as once. GET, PUT, DELETE are idempotent; POST is not.
3. **401 vs 403?** 401 = not authenticated (server doesn't know who you are). 403 = authenticated but not allowed.

## Homework
Design a REST API for a **library** with books, members and loans – at least 8 endpoints with method, URL and success status code. Post it in the YouTube comments. The answer comes at the start of Video 4.

## Homework answer – Library API
| Method | Endpoint | Purpose | Success |
|--------|----------|---------|---------|
| GET | `/books` | List books | 200 |
| GET | `/books/{id}` | Get one book | 200 |
| POST | `/books` | Add a book | 201 |
| PATCH | `/books/{id}` | Update a book | 200 |
| DELETE | `/books/{id}` | Remove a book | 204 |
| POST | `/members` | Register a member | 201 |
| GET | `/members/{id}` | Get one member | 200 |
| POST | `/loans` | Borrow a book (`book_id`, `member_id`) | 201 |
| PATCH | `/loans/{id}` | Return a book (set `returned_at`) | 200 |
| GET | `/members/{id}/loans` | A member's borrowed books | 200 |

No verbs in URLs, plural nouns, and "borrow" becomes the **loans** resource.
