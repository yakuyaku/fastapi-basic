from pydantic import BaseModel, EmailStr, Field
from typing import Optional


class LoginRequest(BaseModel):
    """로그인 요청 스키마"""
    email: EmailStr = Field(..., description="이메일")
    password: str = Field(..., min_length=8, description="비밀번호")


class LoginResponse(BaseModel):
    """로그인 응답 스키마"""
    access_token: str
    token_type: str = "bearer"
    user: dict


class TokenData(BaseModel):
    """토큰 데이터 스키마"""
    user_id: Optional[int] = None
    username: Optional[str] = None
    email: Optional[str] = None