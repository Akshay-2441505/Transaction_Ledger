import os
import sys

# Ensure root directory is on Python path
root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if root_dir not in sys.path:
    sys.path.insert(0, root_dir)

from app.main import app as fastapi_app  # noqa: E402


async def app(scope, receive, send):
    """
    ASGI middleware for Vercel serverless functions.
    Normalizes paths rewritten by Vercel (e.g. /api/index.py -> /).
    """
    if scope["type"] == "http":
        path = scope.get("path", "")
        for prefix in ["/api/index.py", "/api/index", "/api"]:
            if path == prefix:
                scope["path"] = "/"
                break
            elif path.startswith(prefix + "/"):
                scope["path"] = path[len(prefix) :]
                break
    await fastapi_app(scope, receive, send)
