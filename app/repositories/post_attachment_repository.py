"""
Post Attachment repository implementation
app/repositories/post_attachment_repository.py
"""
from typing import Optional, List
from app.repositories.base import BaseRepository
from app.domain.entities.file import PostAttachmentEntity, FileEntity
from app.core.logging import logger


class PostAttachmentRepository(BaseRepository):
    """PostAttachment repository implementation"""

    def _to_entity(self, row: Optional[dict]) -> Optional[PostAttachmentEntity]:
        """데이터베이스 row를 PostAttachmentEntity로 변환"""
        if not row:
            return None

        attachment = PostAttachmentEntity(
            id=row.get('id'),
            post_id=row.get('post_id', 0),
            file_id=row.get('file_id', 0),
            display_order=row.get('display_order', 0),
            is_thumbnail=bool(row.get('is_thumbnail', 0)),
            created_at=row.get('created_at')
        )

        # JOIN으로 파일 정보가 있는 경우
        if row.get('file_original_filename'):
            attachment.file = FileEntity(
                id=row.get('file_id'),
                original_filename=row.get('file_original_filename', ''),
                stored_filename=row.get('file_stored_filename', ''),
                file_path=row.get('file_path', ''),
                file_size=row.get('file_size', 0),
                mime_type=row.get('mime_type', ''),
                file_extension=row.get('file_extension'),
                uploader_id=row.get('uploader_id', 0),
                download_count=row.get('download_count', 0),
                created_at=row.get('file_created_at'),
                is_deleted=bool(row.get('file_is_deleted', 0)),
                is_public=bool(row.get('file_is_public', 1))
            )

        return attachment

    async def create(
            self,
            post_id: int,
            file_id: int,
            display_order: int = 0,
            is_thumbnail: bool = False
    ) -> PostAttachmentEntity:
        """게시글-파일 연결 생성"""
        query = """
                INSERT INTO post_attachments (post_id, file_id, display_order, is_thumbnail)
                VALUES (%s, %s, %s, %s) \
                """
        attachment_id = await self._execute(
            query,
            (post_id, file_id, display_order, 1 if is_thumbnail else 0)
        )

        logger.info(f"Post attachment created - ID: {attachment_id}, post: {post_id}, file: {file_id}")

        # 생성된 연결 정보 조회
        query = """
                SELECT id, post_id, file_id, display_order, is_thumbnail, created_at
                FROM post_attachments
                WHERE id = %s \
                """
        row = await self._fetch_one(query, (attachment_id,))
        return self._to_entity(row)

    async def find_by_post_id(self, post_id: int) -> List[PostAttachmentEntity]:
        """게시글 ID로 첨부파일 목록 조회"""
        query = """
                SELECT id, post_id, file_id, display_order, is_thumbnail, created_at
                FROM post_attachments
                WHERE post_id = %s
                ORDER BY display_order ASC, id ASC \
                """
        rows = await self._fetch_all(query, (post_id,))
        return [self._to_entity(row) for row in rows]

    async def find_by_post_id_with_files(self, post_id: int) -> List[PostAttachmentEntity]:
        """게시글 ID로 첨부파일 목록 조회 (파일 정보 포함)"""
        query = """
                SELECT
                    pa.id, pa.post_id, pa.file_id, pa.display_order, pa.is_thumbnail, pa.created_at,
                    f.original_filename as file_original_filename,
                    f.stored_filename as file_stored_filename,
                    f.file_path,
                    f.file_size,
                    f.mime_type,
                    f.file_extension,
                    f.uploader_id,
                    f.download_count,
                    f.created_at as file_created_at,
                    f.is_deleted as file_is_deleted,
                    f.is_public as file_is_public
                FROM post_attachments pa
                         INNER JOIN files f ON pa.file_id = f.id
                WHERE pa.post_id = %s AND f.is_deleted = 0
                ORDER BY pa.display_order ASC, pa.id ASC \
                """
        rows = await self._fetch_all(query, (post_id,))
        attachments = [self._to_entity(row) for row in rows]

        logger.debug(f"Found {len(attachments)} attachments for post: {post_id}")

        return attachments

    async def delete_by_post_id(self, post_id: int) -> bool:
        """게시글의 모든 첨부파일 연결 삭제"""
        query = "DELETE FROM post_attachments WHERE post_id = %s"
        rows_affected = await self._execute(query, (post_id,))

        success = rows_affected > 0
        if success:
            logger.info(f"All attachments deleted for post: {post_id}")

        return success

    async def delete_by_file_id(self, post_id: int, file_id: int) -> bool:
        """특정 첨부파일 연결 삭제"""
        query = "DELETE FROM post_attachments WHERE post_id = %s AND file_id = %s"
        rows_affected = await self._execute(query, (post_id, file_id))

        success = rows_affected > 0
        if success:
            logger.info(f"Attachment deleted - post: {post_id}, file: {file_id}")

        return success

    async def update_display_order(self, attachment_id: int, display_order: int) -> bool:
        """표시 순서 업데이트"""
        query = """
                UPDATE post_attachments
                SET display_order = %s
                WHERE id = %s \
                """
        rows_affected = await self._execute(query, (display_order, attachment_id))

        success = rows_affected > 0
        if success:
            logger.info(f"Display order updated - attachment: {attachment_id}, order: {display_order}")

        return success

    async def set_thumbnail(self, post_id: int, file_id: int) -> bool:
        """썸네일 설정 (기존 썸네일 해제 후 설정)"""
        # 트랜잭션 필요 (간단히 두 개의 쿼리로 처리)

        # 1. 기존 썸네일 해제
        query1 = """
                 UPDATE post_attachments
                 SET is_thumbnail = 0
                 WHERE post_id = %s \
                 """
        await self._execute(query1, (post_id,))

        # 2. 새 썸네일 설정
        query2 = """
                 UPDATE post_attachments
                 SET is_thumbnail = 1
                 WHERE post_id = %s AND file_id = %s \
                 """
        rows_affected = await self._execute(query2, (post_id, file_id))

        success = rows_affected > 0
        if success:
            logger.info(f"Thumbnail set - post: {post_id}, file: {file_id}")

        return success