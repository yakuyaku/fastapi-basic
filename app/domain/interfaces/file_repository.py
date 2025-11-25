"""
File repository protocol (interface)
app/domain/interfaces/file_repository.py
"""
from typing import Protocol, Optional, List
from app.domain.entities.file import FileEntity, PostAttachmentEntity, TempFileEntity
from datetime import datetime


class FileRepositoryProtocol(Protocol):
    """File repository 인터페이스"""

    async def create(
            self,
            original_filename: str,
            stored_filename: str,
            file_path: str,
            file_size: int,
            mime_type: str,
            file_extension: Optional[str],
            uploader_id: int,
            upload_ip: Optional[str],
            is_public: bool = True
    ) -> FileEntity:
        """파일 생성"""
        ...

    async def find_by_id(self, file_id: int) -> Optional[FileEntity]:
        """ID로 파일 조회"""
        ...

    async def find_by_stored_filename(self, stored_filename: str) -> Optional[FileEntity]:
        """저장된 파일명으로 조회"""
        ...

    async def find_by_uploader(
            self,
            uploader_id: int,
            skip: int = 0,
            limit: int = 100,
            include_deleted: bool = False
    ) -> tuple[List[FileEntity], int]:
        """업로더로 파일 목록 조회"""
        ...

    async def soft_delete(self, file_id: int) -> bool:
        """파일 소프트 삭제"""
        ...

    async def restore(self, file_id: int) -> bool:
        """삭제된 파일 복구"""
        ...

    async def increment_download_count(self, file_id: int) -> None:
        """다운로드 횟수 증가"""
        ...


class PostAttachmentRepositoryProtocol(Protocol):
    """PostAttachment repository 인터페이스"""

    async def create(
            self,
            post_id: int,
            file_id: int,
            display_order: int = 0,
            is_thumbnail: bool = False
    ) -> PostAttachmentEntity:
        """게시글-파일 연결 생성"""
        ...

    async def find_by_post_id(self, post_id: int) -> List[PostAttachmentEntity]:
        """게시글 ID로 첨부파일 목록 조회"""
        ...

    async def find_by_post_id_with_files(self, post_id: int) -> List[PostAttachmentEntity]:
        """게시글 ID로 첨부파일 목록 조회 (파일 정보 포함)"""
        ...

    async def delete_by_post_id(self, post_id: int) -> bool:
        """게시글의 모든 첨부파일 연결 삭제"""
        ...

    async def delete_by_file_id(self, post_id: int, file_id: int) -> bool:
        """특정 첨부파일 연결 삭제"""
        ...

    async def update_display_order(self, attachment_id: int, display_order: int) -> bool:
        """표시 순서 업데이트"""
        ...

    async def set_thumbnail(self, post_id: int, file_id: int) -> bool:
        """썸네일 설정 (기존 썸네일 해제 후 설정)"""
        ...


class TempFileRepositoryProtocol(Protocol):
    """TempFile repository 인터페이스"""

    async def create(
            self,
            file_id: int,
            uploader_id: int,
            expires_at: datetime
    ) -> TempFileEntity:
        """임시 파일 생성"""
        ...

    async def find_by_file_id(self, file_id: int) -> Optional[TempFileEntity]:
        """파일 ID로 임시 파일 조회"""
        ...

    async def find_expired(self) -> List[TempFileEntity]:
        """만료된 임시 파일 목록 조회"""
        ...

    async def delete(self, temp_file_id: int) -> bool:
        """임시 파일 레코드 삭제"""
        ...

    async def delete_by_file_id(self, file_id: int) -> bool:
        """파일 ID로 임시 파일 레코드 삭제"""
        ...

    async def cleanup_expired(self) -> int:
        """만료된 임시 파일 정리"""
        ...