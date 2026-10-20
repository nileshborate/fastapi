# Video 2 – How the Web Works: HTTP in Depth

Everything a FastAPI app receives and sends is an HTTP message. In this video we read real requests and responses.

## 1. Chrome DevTools
1. Open Chrome and press **F12** → **Network** tab
2. Visit https://jsonplaceholder.typicode.com/posts/1 (a free practice API)
3. Click the request → see **General** (URL, method, status), **Headers**, **Response**

## 2. curl commands
curl comes with Windows 10+, macOS and Linux.

```bash
# GET – show response headers + body
curl -i https://jsonplaceholder.typicode.com/posts/1

# Verbose – lines with > are the request you sent, < are the response
curl -v https://jsonplaceholder.typicode.com/posts/1

# POST – send JSON (server replies 201 Created)
curl -i -X POST https://jsonplaceholder.typicode.com/posts \
  -H "Content-Type: application/json" \
  -d '{"title": "Hello", "body": "From curl", "userId": 1}'
```

**Windows (Command Prompt)** – use double quotes and escape the inner ones:
```bat
curl -i -X POST https://jsonplaceholder.typicode.com/posts -H "Content-Type: application/json" -d "{\"title\": \"Hello\", \"body\": \"From curl\", \"userId\": 1}"
```

## 3. Python – see every part of the response
No install needed (standard library only):
```bash
python http_inspect.py
python http_inspect.py https://jsonplaceholder.typicode.com/users/1
```

## Cheat sheet
| Part | Request | Response |
|------|---------|----------|
| First line | `GET /courses/7 HTTP/1.1` | `HTTP/1.1 200 OK` |
| Headers | Host, Accept, Content-Type, Authorization | Content-Type, Content-Length, Cache-Control |
| Body | Usually empty for GET, JSON for POST/PUT/PATCH | The data (usually JSON) |

**Status code families:** 1xx info · 2xx success · 3xx redirect · 4xx client error · 5xx server error

## Homework
Run `curl -v` on any public API. Note the method, 3 request headers, the status code and the response Content-Type. Share it in the YouTube comments!
