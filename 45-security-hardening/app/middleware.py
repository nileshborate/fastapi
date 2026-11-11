# Two small ASGI middlewares: a body size limit and security headers
from fastapi import HTTPException
from starlette.types import ASGIApp, Message, Receive, Scope, Send

TOO_LARGE = b'{"detail":"Request body too large"}'


class BodySizeLimit:
    """reject bodies over max_bytes - BEFORE we read them into memory"""

    def __init__(self, app: ASGIApp, max_bytes: int) -> None:
        self.app = app
        self.max_bytes = max_bytes

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
        length = dict(scope["headers"]).get(b"content-length")
        if length is not None and int(length) > self.max_bytes:     # the honest client
            await self.reject(send)
            return
        received = 0

        async def counting_receive() -> Message:          # no Content-Length? count the bytes
            nonlocal received
            message = await receive()
            if message["type"] == "http.request":
                received += len(message.get("body", b""))
                if received > self.max_bytes:
                    raise BodyTooLarge()
            return message

        try:
            await self.app(scope, counting_receive, send)
        except BodyTooLarge:
            await self.reject(send)

    async def reject(self, send: Send) -> None:
        await send({"type": "http.response.start", "status": 413,
                    "headers": [(b"content-type", b"application/json"),
                                (b"content-length", str(len(TOO_LARGE)).encode())]})
        await send({"type": "http.response.body", "body": TOO_LARGE})


class BodyTooLarge(HTTPException):
    """an HTTPException: FastAPI passes it through while it reads the body -> our 413"""

    def __init__(self) -> None:
        super().__init__(status_code=413, detail="Request body too large")


class SecurityHeaders:
    """headers that tell the BROWSER to be careful with our answers"""

    def __init__(self, app: ASGIApp, hsts: bool) -> None:
        self.app = app
        self.headers = [
            (b"x-content-type-options", b"nosniff"),          # JSON stays JSON
            (b"x-frame-options", b"DENY"),                    # no hiding us in an <iframe>
            (b"referrer-policy", b"no-referrer"),             # URLs don't leak to others
            (b"cache-control", b"no-store"),                  # no caching of private data
        ]
        if hsts:                                              # production only - HTTPS!
            self.headers.append((b"strict-transport-security",
                                 b"max-age=31536000; includeSubDomains"))

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        async def send_with_headers(message: Message) -> None:
            if message["type"] == "http.response.start":
                message["headers"] = list(message.get("headers", [])) + self.headers
            await send(message)

        await self.app(scope, receive, send_with_headers)
