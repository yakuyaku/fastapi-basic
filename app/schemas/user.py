from pydantic import BaseModel, EmailStr, Field, field_validator
from typing import Optional
from datetime import datetime
import re


class UserCreate(BaseModel):
    """사용자 생성 요청 스키마"""
    email: EmailStr = Field(..., description="이메일 주소")
    username: str = Field(..., min_length=3, max_length=50, description="사용자명")
    password: str = Field(..., min_length=8, max_length=100, description="비밀번호")
    is_admin: bool = Field(False, description="관리자 여부")

    @field_validator('username')
    @classmethod
    def validate_username(cls, v):
        """사용자명 검증"""
        if not re.match(r'^[a-zA-Z0-9_-]+$', v):
            raise ValueError('사용자명은 영문, 숫자, _, - 만 사용 가능합니다')
        return v

    @field_validator('password')
    @classmethod
    def validate_password(cls, v):
        """비밀번호 검증"""
        if not re.search(r'[A-Za-z]', v):
            raise ValueError('비밀번호는 최소 1개의 영문자를 포함해야 합니다')
        if not re.search(r'\d', v):
            raise ValueError('비밀번호는 최소 1개의 숫자를 포함해야 합니다')
        return v


class UserResponse(BaseModel):
    """사용자 응답 스키마"""
    id: int
    email: str
    username: str
    is_active: bool
    is_admin: bool
    created_at: datetime
    updated_at: Optional[datetime] = None
    last_login_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class UserCreateResponse(BaseModel):
    """사용자 생성 응답 스키마"""
    id: int
    email: str
    username: str
    is_active: bool
    is_admin: bool
    created_at: datetime
    message: str = "사용자가 성공적으로 생성되었습니다"


class UserListResponse(BaseModel):
    """사용자 목록 응답 스키마"""
    total: int
    page: int
    page_size: int
    total_pages: int
    users: list[UserResponse]

class UserDeleteResponse(BaseModel):
    """사용자 삭제 응답 스키마 (Hard Delete)"""
    id: int
    username: str
    email: str
    message: str = "사용자가 성공적으로 삭제되었습니다"


class UserSoftDeleteResponse(BaseModel):
    """사용자 비활성화 응답 스키마 (Soft Delete)"""
    id: int
    username: str
    email: str
    is_active: bool
    message: str = "사용자가 비활성화되었습니다"




class UserUpdate(BaseModel):
    """사용자 수정 요청 스키마"""
    email: Optional[EmailStr] = Field(None, description="이메일 주소")
    username: Optional[str] = Field(None, min_length=3, max_length=50, description="사용자명")
    password: Optional[str] = Field(None, min_length=8, max_length=100, description="새 비밀번호")
    is_admin: Optional[bool] = Field(None, description="관리자 여부")

    @field_validator('username')
    @classmethod
    def validate_username(cls, v):
        """사용자명 검증"""
        if v is not None:
            if not re.match(r'^[a-zA-Z0-9_-]+$', v):
                raise ValueError('사용자명은 영문, 숫자, _, - 만 사용 가능합니다')
        return v

    @field_validator('password')
    @classmethod
    def validate_password(cls, v):
        """비밀번호 검증"""
        if v is not None:
            if not re.search(r'[A-Za-z]', v):
                raise ValueError('비밀번호는 최소 1개의 영문자를 포함해야 합니다')
            if not re.search(r'\d', v):
                raise ValueError('비밀번호는 최소 1개의 숫자를 포함해야 합니다')
        return v


class UserUpdateResponse(BaseModel):
    """사용자 수정 응답 스키마"""
    id: int
    email: str
    username: str
    is_active: bool
    is_admin: bool
    updated_at: datetime
    message: str = "사용자 정보가 성공적으로 수정되었습니다"