"""
File service - Business logic for file operations
app/services/file_service.py
"""
import os
import uuid
import aiofiles
import filetype
from pathlib import Path
from typing import Optional, List
from datetime import datetime, timedelta
from fastapi import HTTPException, status, UploadFile
from app.domain.entities.file import FileEntity, PostAttachmentEntity, TempFileEntity
from app.domain.entities.user import UserEntity
from app.domain.interfaces.file_repository import (
    FileRepositoryProtocol,
    PostAttachmentRepositoryProtocol,
    TempFileRepositoryProtocol
)
from app.core.logging import logger
from app.core.config import settings


class FileService:
    """
    File service

    파일 업로드/다운로드 및 첨부파일 관리 비즈니스 로직을 처리합니다.
    """

    def __init__(
            self,
            file_repository: FileRepositoryProtocol,
            post_attachment_repository: PostAttachmentRepositoryProtocol,
            temp_file_repository: TempFileRepositoryProtocol
    ):
        self.file_repo = file_repository
        self.attachment_repo = post_attachment_repository
        self.temp_repo = temp_file_repository
        self.upload_dir = Path(settings.UPLOAD_DIR)
        self.upload_dir.mkdir(parents=True, exist_ok=True)

    def _get_file_extension(self, filename: str) -> Optional[str]:
        """파일 확장자 추출 (Path Traversal 방지)"""
        # Path.name을 사용하여 디렉터리 경로 제거
        safe_filename = Path(filename).name
        ext = Path(safe_filename).suffix
        return ext if ext else None

    def _sanitize_filename(self, filename: str) -> str:
        """
        파일명 정규화 (Path Traversal 방지)

        보안 규칙:
        - 상위 경로 접근 차단 (..)
        - 디렉터리 경로 제거 (일부 브라우저는 전체 경로 전송)
        """
        # Path Traversal 공격 차단 (..)
        if '..' in filename:
            logger.warning(f"Path traversal attempt detected: {filename}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="잘못된 파일명입니다"
            )

        # Path.name으로 디렉터리 경로 안전하게 제거
        # Windows: C:\Users\file.txt -> file.txt
        # Unix: /home/user/file.txt -> file.txt
        # Normal: file.txt -> file.txt
        safe_filename = Path(filename).name

        # 빈 파일명 방지
        if not safe_filename or safe_filename in ['.', '..']:
            logger.warning(f"Invalid filename: {filename}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="잘못된 파일명입니다"
            )

        return safe_filename

    def _generate_stored_filename(self, original_filename: str) -> str:
        """고유한 저장 파일명 생성 (보안 강화)"""
        # 파일명 정규화
        safe_filename = self._sanitize_filename(original_filename)
        ext = self._get_file_extension(safe_filename)
        unique_id = uuid.uuid4().hex
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        return f"{timestamp}_{unique_id}{ext if ext else ''}"

    def _validate_file_size(self, file_size: int, is_image: bool = False) -> None:
        """파일 크기 검증"""
        max_size = settings.MAX_IMAGE_SIZE if is_image else settings.MAX_DOCUMENT_SIZE

        if file_size > max_size:
            max_mb = max_size / (1024 * 1024)
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail=f"파일 크기는 {max_mb:.0f}MB를 초과할 수 없습니다"
            )

    def _validate_mime_type(self, mime_type: str) -> None:
        """MIME 타입 검증"""
        allowed_types = [
            # 이미지
            'image/jpeg', 'image/png', 'image/gif', 'image/webp', 'image/bmp', 'image/svg+xml',
            # 문서
            'application/pdf',
            'application/msword',
            'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
            'application/vnd.ms-excel',
            'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            'application/vnd.ms-powerpoint',
            'application/vnd.openxmlformats-officedocument.presentationml.presentation',
            'text/plain',
            # 압축 파일
            'application/zip',
            'application/x-rar-compressed',
            'application/x-7z-compressed',
            # 동영상
            'video/mp4', 'video/avi', 'video/quicktime'
        ]

        if mime_type not in allowed_types:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"지원하지 않는 파일 형식입니다: {mime_type}"
            )

    def _validate_file_content(self, content: bytes, claimed_mime_type: str) -> str:
        """
        Magic bytes로 실제 파일 타입 검증 (MIME Spoofing 방지)

        Args:
            content: 파일 내용 (bytes)
            claimed_mime_type: 클라이언트가 제공한 MIME 타입

        Returns:
            str: 검증된 실제 MIME 타입

        Raises:
            HTTPException: 파일 타입 불일치 또는 지원하지 않는 파일
        """
        # Magic bytes로 실제 파일 타입 확인
        kind = filetype.guess(content)

        if kind is None:
            # 텍스트 파일은 magic bytes가 없을 수 있음
            if claimed_mime_type == 'text/plain':
                logger.info("Text file detected (no magic bytes)")
                return claimed_mime_type
            else:
                logger.warning(f"Unknown file type - claimed: {claimed_mime_type}")
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="파일 형식을 확인할 수 없습니다"
                )

        actual_mime_type = kind.mime
        logger.info(f"File type validation - claimed: {claimed_mime_type}, actual: {actual_mime_type}")

        # 실제 MIME 타입이 허용 목록에 있는지 검증
        self._validate_mime_type(actual_mime_type)

        # 클라이언트가 제공한 MIME과 실제 MIME이 크게 다른 경우 경고
        claimed_category = claimed_mime_type.split('/')[0]
        actual_category = actual_mime_type.split('/')[0]

        if claimed_category != actual_category:
            logger.warning(
                f"MIME type mismatch - claimed: {claimed_mime_type}, actual: {actual_mime_type}"
            )
            # 보안을 위해 실제 타입 사용
            return actual_mime_type

        return actual_mime_type

    async def upload_file(
            self,
            file: UploadFile,
            current_user: Optional[UserEntity],
            upload_ip: Optional[str] = None,
            is_public: bool = True,
            is_temp: bool = True
    ) -> FileEntity:
        """
        파일 업로드

        비즈니스 규칙:
        - 파일 크기 제한
        - MIME 타입 검증
        - 고유 파일명 생성
        - 임시 파일로 저장 (기본값)
        - 게스트 사용자는 uploader_id = 0으로 설정

        Args:
            file: 업로드 파일
            current_user: 현재 사용자 (None이면 게스트)
            upload_ip: 업로드 IP
            is_public: 공개 여부
            is_temp: 임시 파일 여부 (True인 경우 24시간 후 삭제)

        Returns:
            FileEntity: 업로드된 파일 엔티티
        """
        # 게스트 사용자 처리
        uploader_id = current_user.id if current_user else settings.GUEST_USER_ID

        logger.info(f"Uploading file - user: {'guest' if uploader_id == settings.GUEST_USER_ID else uploader_id}, filename: {file.filename}")

        # 파일명 정규화 (Path Traversal 방지)
        safe_original_filename = self._sanitize_filename(file.filename)

        # 파일 읽기
        content = await file.read()
        file_size = len(content)

        # Magic bytes로 실제 파일 타입 검증 (MIME Spoofing 방지)
        claimed_mime_type = file.content_type or 'application/octet-stream'
        actual_mime_type = self._validate_file_content(content, claimed_mime_type)

        # 파일 크기 검증
        is_image = actual_mime_type.startswith('image/')
        self._validate_file_size(file_size, is_image)

        # 저장 파일명 생성 (보안 강화된 메서드 사용)
        stored_filename = self._generate_stored_filename(safe_original_filename)
        file_extension = self._get_file_extension(safe_original_filename)

        # 파일 저장
        file_path = self.upload_dir / stored_filename
        async with aiofiles.open(file_path, 'wb') as f:
            await f.write(content)

        logger.info(f"File saved to disk - path: {file_path}")

        # DB에 파일 정보 저장 (검증된 실제 MIME 타입 사용)
        file_entity = await self.file_repo.create(
            original_filename=safe_original_filename,
            stored_filename=stored_filename,
            file_path=str(file_path),
            file_size=file_size,
            mime_type=actual_mime_type,
            file_extension=file_extension,
            uploader_id=uploader_id,
            upload_ip=upload_ip,
            is_public=is_public
        )

        # 임시 파일로 등록 (24시간 후 만료)
        if is_temp:
            expires_at = datetime.now() + timedelta(hours=24)
            await self.temp_repo.create(
                file_id=file_entity.id,
                uploader_id=uploader_id,
                expires_at=expires_at
            )
            logger.info(f"Registered as temp file - expires at: {expires_at}")

        logger.info(f"File uploaded successfully - ID: {file_entity.id}")
        return file_entity

    async def attach_files_to_post(
            self,
            post_id: int,
            file_ids: List[int],
            current_user: UserEntity
    ) -> List[PostAttachmentEntity]:
        """
        게시글에 파일 첨부

        비즈니스 규칙:
        - 파일 존재 확인
        - 임시 파일인 경우 임시 테이블에서 제거
        - 첫 번째 이미지를 썸네일로 자동 설정

        Args:
            post_id: 게시글 ID
            file_ids: 첨부할 파일 ID 목록
            current_user: 현재 사용자

        Returns:
            List[PostAttachmentEntity]: 첨부된 파일 목록
        """
        logger.info(f"Attaching files to post - post: {post_id}, files: {file_ids}")

        attachments = []
        first_image_id = None

        for idx, file_id in enumerate(file_ids):
            # 파일 존재 확인
            file_entity = await self.file_repo.find_by_id(file_id)
            if not file_entity:
                logger.warning(f"File not found - ID: {file_id}")
                continue

            # 임시 파일 테이블에서 제거
            await self.temp_repo.delete_by_file_id(file_id)

            # 첨부파일 연결 생성
            attachment = await self.attachment_repo.create(
                post_id=post_id,
                file_id=file_id,
                display_order=idx,
                is_thumbnail=False  # 나중에 첫 번째 이미지를 썸네일로 설정
            )
            attachments.append(attachment)

            # 첫 번째 이미지 찾기
            if first_image_id is None and file_entity.is_image():
                first_image_id = file_id

        # 첫 번째 이미지를 썸네일로 설정
        if first_image_id:
            await self.attachment_repo.set_thumbnail(post_id, first_image_id)
            logger.info(f"Set thumbnail - post: {post_id}, file: {first_image_id}")

        logger.info(f"Attached {len(attachments)} files to post: {post_id}")
        return attachments

    async def get_post_attachments(self, post_id: int) -> List[PostAttachmentEntity]:
        """
        게시글의 첨부파일 목록 조회

        Args:
            post_id: 게시글 ID

        Returns:
            List[PostAttachmentEntity]: 첨부파일 목록
        """
        return await self.attachment_repo.find_by_post_id_with_files(post_id)

    async def download_file(
            self,
            file_id: int,
            current_user: Optional[UserEntity] = None
    ) -> tuple[Path, str]:
        """
        파일 다운로드

        비즈니스 규칙:
        - 파일 존재 확인
        - 접근 권한 확인
        - 다운로드 횟수 증가

        Args:
            file_id: 파일 ID
            current_user: 현재 사용자 (선택)

        Returns:
            tuple[Path, str]: (파일 경로, 원본 파일명)
        """
        # 파일 존재 확인
        file_entity = await self.file_repo.find_by_id(file_id)
        if not file_entity:
            logger.warning(f"File not found - ID: {file_id}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="파일을 찾을 수 없습니다"
            )

        # 접근 권한 확인
        user_id = current_user.id if current_user else 0
        is_admin = current_user.is_admin if current_user else False

        if not file_entity.can_access(user_id, is_admin):
            logger.warning(f"File access denied - file: {file_id}, user: {user_id}")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="파일에 접근할 권한이 없습니다"
            )

        # 다운로드 횟수 증가
        await self.file_repo.increment_download_count(file_id)

        file_path = Path(file_entity.file_path)
        if not file_path.exists():
            logger.error(f"File not found on disk - path: {file_path}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="파일을 찾을 수 없습니다"
            )

        logger.info(f"File downloaded - ID: {file_id}")
        return file_path, file_entity.original_filename

    async def delete_file(
            self,
            file_id: int,
            current_user: UserEntity,
            hard_delete: bool = False
    ) -> FileEntity:
        """
        파일 삭제

        비즈니스 규칙:
        - 본인 또는 관리자만 삭제 가능
        - 기본은 Soft Delete
        - Hard Delete시 실제 파일도 삭제

        Args:
            file_id: 파일 ID
            current_user: 현재 사용자
            hard_delete: 완전 삭제 여부

        Returns:
            FileEntity: 삭제된 파일 엔티티
        """
        logger.info(f"Deleting file - ID: {file_id}, user: {current_user.id}, hard: {hard_delete}")

        # 파일 존재 확인
        file_entity = await self.file_repo.find_by_id(file_id)
        if not file_entity:
            logger.warning(f"File not found - ID: {file_id}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="파일을 찾을 수 없습니다"
            )

        # 권한 확인
        if not file_entity.can_delete(current_user.id, current_user.is_admin):
            logger.warning(f"File delete permission denied - file: {file_id}, user: {current_user.id}")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="파일을 삭제할 권한이 없습니다"
            )

        if hard_delete:
            # 실제 파일 삭제
            file_path = Path(file_entity.file_path)
            if file_path.exists():
                file_path.unlink()
                logger.info(f"File deleted from disk - path: {file_path}")
        else:
            # Soft Delete
            await self.file_repo.soft_delete(file_id)
            logger.info(f"File soft deleted - ID: {file_id}")

        return file_entity

    async def cleanup_expired_temp_files(self) -> int:
        """
        만료된 임시 파일 정리

        Returns:
            int: 정리된 파일 수
        """
        logger.info("Starting expired temp files cleanup")

        # 만료된 임시 파일 목록 조회
        expired_files = await self.temp_repo.find_expired()

        deleted_count = 0
        for temp_file in expired_files:
            if temp_file.file:
                # 실제 파일 삭제
                file_path = Path(temp_file.file.file_path)
                if file_path.exists():
                    try:
                        file_path.unlink()
                        logger.info(f"Expired temp file deleted - path: {file_path}")
                    except Exception as e:
                        logger.error(f"Failed to delete file - path: {file_path}, error: {e}")

                # DB에서 파일 삭제
                await self.file_repo.soft_delete(temp_file.file_id)

            # 임시 파일 레코드 삭제
            await self.temp_repo.delete(temp_file.id)
            deleted_count += 1

        logger.info(f"Cleaned up {deleted_count} expired temp files")
        return deleted_count