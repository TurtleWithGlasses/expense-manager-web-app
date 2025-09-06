from itsdangerous import URLSafeTimedSerializer
from starlette.requests import Request
from starlette.responses import Response
from app.core.config import settings


serializer = URLSafeTimedSerializer(settings.SECRET_KEY)


SESSION_COOKIE = settings.SESSION_COOKIE_NAME
MAX_AGE = settings.SESSION_MAX_AGE_SECONDS


# Store minimal user info (id & email) in a signed cookie

def set_session(response: Response, data: dict):
    token = serializer.dumps(data)
    response.set_cookie(
        SESSION_COOKIE,
        token,
        max_age=MAX_AGE,
        httponly=True,
        samesite="lax",
        secure=False, # set True behind HTTPS in prod
        path="/",
    )

def get_session(request: Request) -> dict | None:
    token = request.cookies.get(SESSION_COOKIE)
    if not token:
        return None
    try:
        return serializer.loads(token, max_age=MAX_AGE)
    except Exception:
        return None


def clear_session(response: Response):
    response.delete_cookie(SESSION_COOKIE, path="/")