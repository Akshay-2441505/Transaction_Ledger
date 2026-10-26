import os
import sys
import urllib.parse

# Ensure root directory is on Python path
root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if root_dir not in sys.path:
    sys.path.insert(0, root_dir)

from app.main import app as fastapi_app  # noqa: E402


async def app(scope, receive, send):
    """
    ASGI middleware for Vercel serverless functions.
    Extracts the genuine requested path from Vercel rewrites and headers.
    """
    if scope["type"] == "http":
        # 1. Check for path forwarded via rewrite query param
        query_bytes = scope.get("query_string", b"")
        query_str = query_bytes.decode("utf-8", errors="ignore")
        params = urllib.parse.parse_qs(query_str)

        resolved_path = None
        if "__url__" in params and params["__url__"]:
            raw_url = params["__url__"][0]
            # Normalize leading slash and double slashes
            if not raw_url.startswith("/"):
                raw_url = "/" + raw_url
            while "//" in raw_url:
                raw_url = raw_url.replace("//", "/")
            resolved_path = raw_url
            # Clean up __url__ so endpoints don't see it
            del params["__url__"]
            scope["query_string"] = urllib.parse.urlencode(params, doseq=True).encode(
                "utf-8"
            )

        # 2. Check for x-matched-path header fallback
        if not resolved_path:
            headers = dict(scope.get("headers", []))
            matched_header = headers.get(b"x-matched-path")
            if matched_header:
                decoded = matched_header.decode("utf-8", errors="ignore")
                if not decoded.startswith("/api/index"):
                    resolved_path = decoded

        # 3. Fallback to scope path normalization
        if not resolved_path:
            raw_path = scope.get("path", "")
            for prefix in ["/api/index.py", "/api/index", "/api"]:
                if raw_path == prefix:
                    resolved_path = "/"
                    break
                elif raw_path.startswith(prefix + "/"):
                    resolved_path = raw_path[len(prefix) :]
                    break
            if not resolved_path:
                resolved_path = raw_path or "/"

        scope["path"] = resolved_path

    await fastapi_app(scope, receive, send)
