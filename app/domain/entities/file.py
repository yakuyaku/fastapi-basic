"""
File domain entity
app/domain/entities/file.py
"""
from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass
class FileEntity:
    """
    File domain entity (순수 비즈니스 객체)

    파일 정보를 표현하는 순수한 비즈니스 엔티티입니다.
    """
    id: Optional[int] = None
    original_filename: str = ""
    stored_filename: str = ""
    file_path: str = ""
    file_size: int = 0
    mime_type: str = ""
    file_extension: Optional[str] = None
    uploader_id: int = 0
    upload_ip: Optional[str] = None
    download_count: int = 0
    created_at: Optional[datetime] = None
    is_deleted: bool = False
    is_public: bool = True

    # JOIN용 업로더 정보 (Optional)
    uploader_username: Optional[str] = None
    uploader_email: Optional[str] = None

    def is_image(self) -> bool:
        """이미지 파일 여부 확인"""
        image_extensions = ['.jpg', '.jpeg', '.png', '.gif', '.webp', '.bmp', '.svg']
        if self.file_extension:
            return self.file_extension.lower() in image_extensions
        return self.mime_type.startswith('image/')

    def is_video(self) -> bool:
        """동영상 파일 여부 확인"""
        video_extensions = ['.mp4', '.avi', '.mov', '.wmv', '.flv', '.webm']
        if self.file_extension:
            return self.file_extension.lower() in video_extensions
        return self.mime_type.startswith('video/')

    def is_document(self) -> bool:
        """문서 파일 여부 확인"""
        doc_extensions = ['.pdf', '.doc', '.docx', '.xls', '.xlsx', '.ppt', '.pptx', '.txt']
        if self.file_extension:
            return self.file_extension.lower() in doc_extensions
        return False

    def can_access(self, user_id: int, is_admin: bool) -> bool:
        """
        파일 접근 권한 확인

        Args:
            user_id: 사용자 ID
            is_admin: 관리자 여부

        Returns:
            bool: 공개 파일이거나, 업로더 본인이거나, 관리자인 경우 True
        """
        if self.is_deleted:
            return is_admin  # 삭제된 파일은 관리자만 접근 가능

        if self.is_public:
            return True

        return is_admin or self.uploader_id == user_id

    def can_delete(self, user_id: int, is_admin: bool) -> bool:
        """
        파일 삭제 권한 확인

        Args:
            user_id: 사용자 ID
            is_admin: 관리자 여부

        Returns:
            bool: 업로더 본인이거나 관리자인 경우 True
        """
        return is_admin or self.uploader_id == user_id

    def get_human_readable_size(self) -> str:
        """파일 크기를 읽기 쉬운 형식으로 변환"""
        size = self.file_size
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if size < 1024.0:
                return f"{size:.2f} {unit}"
            size /= 1024.0
        return f"{size:.2f} PB"


@dataclass
class PostAttachmentEntity:
    """
    PostAttachment domain entity

    게시글과 파일의 연결 정보를 표현하는 엔티티입니다.
    """
    id: Optional[int] = None
    post_id: int = 0
    file_id: int = 0
    display_order: int = 0
    is_thumbnail: bool = False
    created_at: Optional[datetime] = None

    # JOIN용 파일 정보 (Optional)
    file: Optional[FileEntity] = None


@dataclass
class TempFileEntity:
    """
    TempFile domain entity

    임시 파일 정보를 표현하는 엔티티입니다.
    게시글 작성 중 업로드된 파일을 임시로 저장합니다.
    """
    id: Optional[int] = None
    file_id: int = 0
    uploader_id: int = 0
    expires_at: Optional[datetime] = None
    created_at: Optional[datetime] = None

    # JOIN용 파일 정보 (Optional)
    file: Optional[FileEntity] = None

    def is_expired(self) -> bool:
        """만료 여부 확인"""
        if not self.expires_at:
            return False
        return datetime.now() > self.expires_at