# Run: python -m demos.login_form   - what the OAuth2 password flow sends, byte by byte
import asyncio

import httpx

from app.main import app


async def main() -> None:
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        await client.post("/users", json={"email": "asha@example.com",
                                          "full_name": "Asha Patil",
                                          "password": "blue-river-42"})
        form = {"username": "asha@example.com", "password": "blue-river-42"}
        response = await client.post("/token", data=form)          # data= -> a FORM
        print("1. content-type:", response.request.headers["content-type"])
        print("2. body:        ", response.request.content.decode())
        print("3. answer:      ", response.json()["token_type"],
              response.json()["access_token"][:24], "...")
        as_json = await client.post("/token", json=form)           # JSON -> not OAuth2
        print("4. as JSON:     ", as_json.status_code, as_json.json()["detail"][0]["msg"])
        scheme = app.openapi()["components"]["securitySchemes"]
        print("5. openapi:     ", scheme)


if __name__ == "__main__":
    asyncio.run(main())
