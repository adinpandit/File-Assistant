from fastapi import (APIRouter,HTTPException,status,)
from app.core.security import (create_access_token,verify_password,)
from app.models.auth import (LoginRequest,TokenResponse,UserCreate,UserResponse,)
from app.services.user_store import UserStore


router = APIRouter(
    prefix="/auth",
    tags=["Authentication"],
)

user_store = UserStore()


@router.post("/register",response_model=UserResponse,)
def register(request: UserCreate,):
    email = request.email.strip().lower()

    existing_user = user_store.get_user_by_email(email,)

    if existing_user is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="User already exists",
        )

    try:
        user = user_store.create_user(email=email,password=request.password,role="USER",)

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail="Failed to create user",
        ) from exc

    return user


@router.post("/login",response_model=TokenResponse,)
def login(request: LoginRequest,):
    email = request.email.strip().lower()

    user = user_store.get_user_by_email(email,)

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )

    password_valid = verify_password(request.password,user["password_hash"],)

    if not password_valid:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )

    token = create_access_token(user_id=str(user["user_id"]),role=user["role"],)

    return TokenResponse(
        access_token=token,
        token_type="bearer",
    )