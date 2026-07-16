from collections.abc import Awaitable, Callable

from starlette.requests import Request
from starlette.responses import Response


class SecurityHeadersMiddleware:
    def __init__(self, app: Callable[[Request], Awaitable[Response]]) -> None:
        self.app = app

    async def __call__(self, scope, receive, send):
        async def send_with_headers(message):
            if message["type"] == "http.response.start":
                headers = message.setdefault("headers", [])
                existing = {name.lower() for name, _ in headers}
                security_headers = {
                    b"x-content-type-options": b"nosniff",
                    b"x-frame-options": b"DENY",
                    b"referrer-policy": b"strict-origin-when-cross-origin",
                    b"permissions-policy": b"geolocation=(), microphone=(), camera=()",
                }
                for name, value in security_headers.items():
                    if name not in existing:
                        headers.append((name, value))
            await send(message)

        await self.app(scope, receive, send_with_headers)
