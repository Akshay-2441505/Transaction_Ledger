import os
import sys
import urllib.parse

# Ensure root directory is on Python path
root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if root_dir not in sys.path:
    sys.path.insert(0, root_dir)

from app.main import app as fastapi_app  # noqa: E402


def resolve_request_path(scope):
    """
    Extracts the genuine requested path from Vercel rewrites, proxy headers, or query string.
    """
    headers = dict(scope.get("headers", []))
    resolved_path = None

    # 1. Check query_string for __url__ parameter
    query_str = scope.get("query_string", b"").decode("utf-8", errors="ignore")
    if query_str:
        params = urllib.parse.parse_qs(query_str)
        if "__url__" in params and params["__url__"]:
            resolved_path = params["__url__"][0]
            del params["__url__"]
            scope["query_string"] = urllib.parse.urlencode(params, doseq=True).encode("utf-8")

    # 2. Check Vercel proxy headers (x-matched-path, x-vercel-matched-path, etc.)
    if not resolved_path:
        for hk in [
            b"x-matched-path",
            b"x-vercel-matched-path",
            b"x-forwarded-uri",
            b"x-original-uri",
            b"x-rewrite-url",
        ]:
            val = headers.get(hk)
            if val:
                decoded = val.decode("utf-8", errors="ignore")
                parsed = urllib.parse.urlsplit(decoded)
                qs = urllib.parse.parse_qs(parsed.query)
                if "__url__" in qs and qs["__url__"]:
                    resolved_path = qs["__url__"][0]
                    break
                elif parsed.path and not any(
                    parsed.path == p or parsed.path.startswith(p + "/")
                    for p in ["/api/index.py", "/api/index", "/api"]
                ):
                    resolved_path = parsed.path
                    break

    # 3. Fallback to scope path normalization
    if not resolved_path:
        raw_path = scope.get("path", "")
        for p in ["/api/index.py", "/api/index", "/api"]:
            if raw_path == p or raw_path.startswith(p + "/"):
                raw_path = raw_path[len(p) :]
                break
        resolved_path = raw_path or "/"

    # 4. If query string is embedded in resolved_path, extract it into scope['query_string']
    if "?" in resolved_path:
        path_part, extra_query = resolved_path.split("?", 1)
        resolved_path = path_part
        current_qs = scope.get("query_string", b"").decode("utf-8", errors="ignore")
        if current_qs:
            scope["query_string"] = f"{current_qs}&{extra_query}".encode("utf-8")
        else:
            scope["query_string"] = extra_query.encode("utf-8")

    # 5. Clean leading and double slashes
    if not resolved_path.startswith("/"):
        resolved_path = "/" + resolved_path
    while "//" in resolved_path:
        resolved_path = resolved_path.replace("//", "/")

    return resolved_path


async def app(scope, receive, send):
    """
    ASGI entrypoint for Vercel serverless deployment.
    """
    if scope["type"] == "http":
        scope["path"] = resolve_request_path(scope)

    await fastapi_app(scope, receive, send)

