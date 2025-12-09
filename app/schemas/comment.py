"""
Comment schemas - Request/Response models
app/schemas/comment.py
"""
from pydantic import BaseModel, Field, field_validator
from typing import Optional, List
from datetime import datetime


class CommentCreate(BaseModel):
    """댓글 생성 요청 스키마"""
    content: str = Field(..., min_length=1, max_length=1000, description="댓글 내용")
    parent_id: Optional[int] = Field(None, description="부모 댓글 ID (대댓글인 경우)")
    password: Optional[str] = Field(None, min_length=4, max_length=50, description="게스트 댓글 비밀번호 (미입력시 자동생성)")

    @field_validator('content')
    @classmethod
    def validate_content(cls, v):
        """내용 검증"""
        if not v or v.strip() == "":
            raise ValueError('댓글 내용을 입력해주세요')
        return v.strip()


class CommentUpdate(BaseModel):
    """댓글 수정 요청 스키마"""
    content: str = Field(..., min_length=1, max_length=1000, description="댓글 내용")
    password: Optional[str] = Field(None, min_length=4, max_length=50, description="게스트 댓글 비밀번호 (수정시 필수)")

    @field_validator('content')
    @classmethod
    def validate_content(cls, v):
        """내용 검증"""
        if not v or v.strip() == "":
            raise ValueError('댓글 내용을 입력해주세요')
        return v.strip()


class CommentAuthor(BaseModel):
    """댓글 작성자 정보"""
    id: int
    username: str
    email: Optional[str] = None


class CommentResponse(BaseModel):
    """댓글 응답 스키마 (단일)"""
    id: int
    post_id: int
    parent_id: Optional[int] = None
    author_id: int
    content: str
    depth: int
    path: Optional[str] = None
    order_num: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    is_deleted: bool

    # 작성자 정보 (JOIN시 포함)
    author_username: Optional[str] = None
    author_email: Optional[str] = None

    # Tree 구조용 (선택적)
    children: Optional[List['CommentResponse']] = None

    class Config:
        from_attributes = True


# Pydantic v2에서 순환 참조 해결
CommentResponse.model_rebuild()


class CommentTreeResponse(BaseModel):
    """댓글 Tree 응답 스키마"""
    id: int
    post_id: int
    parent_id: Optional[int] = None
    author_id: int
    content: str
    depth: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    is_deleted: bool

    # 작성자 정보
    author_username: Optional[str] = None

    # 자식 댓글
    children: List['CommentTreeResponse'] = Field(default_factory=list)

    class Config:
        from_attributes = True


# Pydantic v2에서 순환 참조 해결
CommentTreeResponse.model_rebuild()


class CommentListResponse(BaseModel):
    """댓글 목록 응답 스키마 (Flat)"""
    comments: List[CommentResponse] = Field(..., description="댓글 목록")
    total: int = Field(..., description="전체 댓글 수")
    post_id: int = Field(..., description="게시글 ID")


class CommentTreeListResponse(BaseModel):
    """댓글 목록 응답 스키마 (Tree)"""
    comments: List[CommentTreeResponse] = Field(..., description="댓글 트리")
    total: int = Field(..., description="전체 댓글 수")
    post_id: int = Field(..., description="게시글 ID")


class CommentCreateResponse(BaseModel):
    """댓글 생성 응답 스키마"""
    id: int
    post_id: int
    parent_id: Optional[int] = None
    content: str
    depth: int
    path: Optional[str] = None
    author_id: int
    created_at: datetime
    generated_password: Optional[str] = Field(None, description="자동 생성된 비밀번호 (게스트 댓글)")
    message: str = "댓글이 성공적으로 작성되었습니다"

    class Config:
        from_attributes = True


class CommentUpdateResponse(BaseModel):
    """댓글 수정 응답 스키마"""
    id: int
    content: str
    updated_at: datetime
    message: str = "댓글이 성공적으로 수정되었습니다"

    class Config:
        from_attributes = True


class CommentDeleteResponse(BaseModel):
    """댓글 삭제 응답 스키마"""
    id: int
    message: str = "댓글이 성공적으로 삭제되었습니다"