"""
Post schemas - Request/Response models
app/schemas/post.py
"""
from pydantic import BaseModel, Field, field_validator
from typing import Optional
from datetime import datetime


class PostCreate(BaseModel):
    """게시글 생성 요청 스키마"""
    title: str = Field(..., min_length=1, max_length=200, description="게시글 제목")
    content: str = Field(..., min_length=1, description="게시글 내용")
    is_pinned: bool = Field(False, description="고정 게시글 여부 (관리자 전용)")

    @field_validator('title')
    @classmethod
    def validate_title(cls, v):
        """제목 검증"""
        if not v or v.strip() == "":
            raise ValueError('제목을 입력해주세요')
        return v.strip()

    @field_validator('content')
    @classmethod
    def validate_content(cls, v):
        """내용 검증"""
        if not v or v.strip() == "":
            raise ValueError('내용을 입력해주세요')
        return v.strip()


class PostUpdate(BaseModel):
    """게시글 수정 요청 스키마"""
    title: Optional[str] = Field(None, min_length=1, max_length=200, description="게시글 제목")
    content: Optional[str] = Field(None, min_length=1, description="게시글 내용")
    is_pinned: Optional[bool] = Field(None, description="고정 게시글 여부 (관리자 전용)")
    is_locked: Optional[bool] = Field(None, description="게시글 잠금 여부 (관리자 전용)")

    @field_validator('title')
    @classmethod
    def validate_title(cls, v):
        """제목 검증"""
        if v is not None:
            if not v or v.strip() == "":
                raise ValueError('제목을 입력해주세요')
            return v.strip()
        return v

    @field_validator('content')
    @classmethod
    def validate_content(cls, v):
        """내용 검증"""
        if v is not None:
            if not v or v.strip() == "":
                raise ValueError('내용을 입력해주세요')
            return v.strip()
        return v


class PostAuthor(BaseModel):
    """게시글 작성자 정보"""
    id: int
    username: str
    email: Optional[str] = None


class PostResponse(BaseModel):
    """게시글 응답 스키마"""
    id: int
    title: str
    content: str
    author_id: int
    view_count: int
    like_count: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    is_deleted: bool
    is_pinned: bool
    is_locked: bool

    # 작성자 정보 (JOIN시 포함)
    author_username: Optional[str] = None
    author_email: Optional[str] = None

    class Config:
        from_attributes = True


class PostListItem(BaseModel):
    """게시글 목록 아이템 스키마 (간략한 정보)"""
    id: int
    title: str
    author_id: int
    author_username: Optional[str] = None
    view_count: int
    like_count: int
    created_at: datetime
    is_pinned: bool
    is_locked: bool

    class Config:
        from_attributes = True


class PostListResponse(BaseModel):
    """게시글 목록 응답 스키마"""
    posts: list[PostResponse] = Field(..., description="게시글 목록")
    total: int = Field(..., description="전체 게시글 수")
    page: int = Field(..., description="현재 페이지")
    page_size: int = Field(..., description="페이지 크기")
    total_pages: int = Field(..., description="전체 페이지 수")


class PostCreateResponse(BaseModel):
    """게시글 생성 응답 스키마"""
    id: int
    title: str
    content: str
    author_id: int
    view_count: int
    like_count: int
    created_at: datetime
    is_pinned: bool
    message: str = "게시글이 성공적으로 작성되었습니다"

    class Config:
        from_attributes = True


class PostUpdateResponse(BaseModel):
    """게시글 수정 응답 스키마"""
    id: int
    title: str
    content: str
    author_id: int
    view_count: int
    like_count: int
    updated_at: datetime
    is_pinned: bool
    is_locked: bool
    message: str = "게시글이 성공적으로 수정되었습니다"

    class Config:
        from_attributes = True


class PostDeleteResponse(BaseModel):
    """게시글 삭제 응답 스키마"""
    id: int
    title: str
    message: str = "게시글이 성공적으로 삭제되었습니다"


class PostRestoreResponse(BaseModel):
    """게시글 복구 응답 스키마"""
    id: int
    title: str
    message: str = "게시글이 성공적으로 복구되었습니다"


class PostTogglePinResponse(BaseModel):
    """게시글 고정/해제 응답 스키마"""
    id: int
    title: str
    is_pinned: bool
    message: str = "게시글 고정 상태가 변경되었습니다"


class PostToggleLockResponse(BaseModel):
    """게시글 잠금/해제 응답 스키마"""
    id: int
    title: str
    is_locked: bool
    message: str = "게시글 잠금 상태가 변경되었습니다"


class PostLikeResponse(BaseModel):
    """좋아요 응답 스키마"""
    id: int
    like_count: int
    message: str = "좋아요가 반영되었습니다"