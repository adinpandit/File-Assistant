from fastapi import Depends,HTTPException,status
from fastapi.security import (HTTPAuthorizationCredentials,HTTPBearer,)
from app.services.user_store import UserStore
from app.core.security import decode_access_token


class ForbiddenHTTPBearer(HTTPBearer):
    # FastAPI >= 0.122 returns 401 for a missing/malformed Authorization
    # header; keep the API's 403 for unauthenticated requests.
    def make_not_authenticated_error(self) -> HTTPException:
        return HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authenticated",
        )


security = ForbiddenHTTPBearer()

user_store = UserStore()

def get_current_user(credentials:HTTPAuthorizationCredentials = Depends(security),):
    token = credentials.credentials

    try:
        payload = decode_access_token(token,)

    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
        ) from exc

    user_id = payload.get("sub")

    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication token",
        )

    user = user_store.get_user_by_id(
        user_id,
    )

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
        )

    return user


def require_admin(
    current_user=Depends(
        get_current_user
    ),
):
    if current_user["role"] != "ADMIN":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required",
        )

    return current_user