"""
File schemas - Request/Response models
app/schemas/file.py
"""
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


class FileUploadResponse(BaseModel):
    """파일 업로드 응답 스키마"""
    id: int
    original_filename: str
    stored_filename: str
    file_size: int
    mime_type: str
    file_extension: Optional[str] = None
    created_at: datetime
    is_temp: bool = True
    generated_password: Optional[str] = Field(None, description="자동 생성된 비밀번호 (게스트 파일)")
    message: str = "파일이 성공적으로 업로드되었습니다"

    class Config:
        from_attributes = True


class FileResponse(BaseModel):
    """파일 응답 스키마"""
    id: int
    original_filename: str
    stored_filename: str
    file_path: str
    file_size: int
    mime_type: str
    file_extension: Optional[str] = None
    uploader_id: int
    upload_ip: Optional[str] = None
    download_count: int
    created_at: datetime
    is_deleted: bool
    is_public: bool

    # 업로더 정보 (JOIN시 포함)
    uploader_username: Optional[str] = None
    uploader_email: Optional[str] = None

    class Config:
        from_attributes = True


class FileListResponse(BaseModel):
    """파일 목록 응답 스키마"""
    files: List[FileResponse] = Field(..., description="파일 목록")
    total: int = Field(..., description="전체 파일 수")
    page: int = Field(..., description="현재 페이지")
    page_size: int = Field(..., description="페이지 크기")
    total_pages: int = Field(..., description="전체 페이지 수")


class PostAttachmentResponse(BaseModel):
    """게시글 첨부파일 응답 스키마"""
    id: int
    post_id: int
    file_id: int
    display_order: int
    is_thumbnail: bool
    created_at: datetime

    # 파일 정보
    file: Optional[FileResponse] = None

    class Config:
        from_attributes = True


class AttachFilesRequest(BaseModel):
    """파일 첨부 요청 스키마"""
    file_ids: List[int] = Field(..., min_length=1, max_length=10, description="첨부할 파일 ID 목록 (최대 10개)")


class AttachFilesResponse(BaseModel):
    """파일 첨부 응답 스키마"""
    post_id: int
    attached_count: int
    attachments: List[PostAttachmentResponse]
    message: str = "파일이 게시글에 첨부되었습니다"


class FileDeleteResponse(BaseModel):
    """파일 삭제 응답 스키마"""
    id: int
    original_filename: str
    message: str = "파일이 삭제되었습니다"