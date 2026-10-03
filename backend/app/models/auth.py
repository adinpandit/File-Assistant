from pydantic import BaseModel, Field


class UserCreate(BaseModel):
    email: str = Field(
        ...,
        min_length=3,
        max_length=255,
    )

    password: str = Field(
        ...,
        min_length=8,
        max_length=128,
    )


class UserResponse(BaseModel):
    user_id: str
    email: str
    role: str


class LoginRequest(BaseModel):
    email: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str