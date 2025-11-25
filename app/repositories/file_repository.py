"""
File repository implementation
app/repositories/file_repository.py
"""
from typing import Optional, List
from app.repositories.base import BaseRepository
from app.domain.entities.file import FileEntity, PostAttachmentEntity, TempFileEntity
from app.core.logging import logger
from datetime import datetime


class FileRepository(BaseRepository):
    """File repository implementation"""

    def _to_entity(self, row: Optional[dict]) -> Optional[FileEntity]:
        """데이터베이스 row를 FileEntity로 변환"""
        if not row:
            return None

        return FileEntity(
            id=row.get('id'),
            original_filename=row.get('original_filename', ''),
            stored_filename=row.get('stored_filename', ''),
            file_path=row.get('file_path', ''),
            file_size=row.get('file_size', 0),
            mime_type=row.get('mime_type', ''),
            file_extension=row.get('file_extension'),
            uploader_id=row.get('uploader_id', 0),
            upload_ip=row.get('upload_ip'),
            download_count=row.get('download_count', 0),
            created_at=row.get('created_at'),
            is_deleted=bool(row.get('is_deleted', 0)),
            is_public=bool(row.get('is_public', 1)),
            # JOIN시 업로더 정보
            uploader_username=row.get('uploader_username'),
            uploader_email=row.get('uploader_email')
        )

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
        query = """
                INSERT INTO files (
                    original_filename, stored_filename, file_path, file_size, mime_type,
                    file_extension, uploader_id, upload_ip, is_public, is_deleted
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, 0) \
                """
        file_id = await self._execute(
            query,
            (
                original_filename, stored_filename, file_path, file_size, mime_type,
                file_extension, uploader_id, upload_ip, 1 if is_public else 0
            )
        )

        logger.info(
            f"File created in DB - ID: {file_id}, original: {original_filename}, "
            f"uploader: {uploader_id}"
        )

        return await self.find_by_id(file_id)

    async def find_by_id(self, file_id: int) -> Optional[FileEntity]:
        """ID로 파일 조회"""
        query = """
                SELECT
                    f.id, f.original_filename, f.stored_filename, f.file_path, f.file_size,
                    f.mime_type, f.file_extension, f.uploader_id, f.upload_ip,
                    f.download_count, f.created_at, f.is_deleted, f.is_public,
                    u.username as uploader_username, u.email as uploader_email
                FROM files f
                         LEFT JOIN users u ON f.uploader_id = u.id
                WHERE f.id = %s \
                """
        row = await self._fetch_one(query, (file_id,))
        return self._to_entity(row)

    async def find_by_stored_filename(self, stored_filename: str) -> Optional[FileEntity]:
        """저장된 파일명으로 조회"""
        query = """
                SELECT
                    f.id, f.original_filename, f.stored_filename, f.file_path, f.file_size,
                    f.mime_type, f.file_extension, f.uploader_id, f.upload_ip,
                    f.download_count, f.created_at, f.is_deleted, f.is_public
                FROM files f
                WHERE f.stored_filename = %s \
                """
        row = await self._fetch_one(query, (stored_filename,))
        return self._to_entity(row)

    async def find_by_uploader(
            self,
            uploader_id: int,
            skip: int = 0,
            limit: int = 100,
            include_deleted: bool = False
    ) -> tuple[List[FileEntity], int]:
        """업로더로 파일 목록 조회"""
        conditions = ["f.uploader_id = %s"]
        params = [uploader_id]

        if not include_deleted:
            conditions.append("f.is_deleted = 0")

        where_clause = " AND ".join(conditions)

        # 전체 개수 조회
        count_query = f"SELECT COUNT(*) as total FROM files f WHERE {where_clause}"
        count_row = await self._fetch_one(count_query, tuple(params))
        total = count_row['total'] if count_row else 0

        # 파일 목록 조회
        query = f"""
            SELECT 
                f.id, f.original_filename, f.stored_filename, f.file_path, f.file_size,
                f.mime_type, f.file_extension, f.uploader_id, f.upload_ip,
                f.download_count, f.created_at, f.is_deleted, f.is_public
            FROM files f
            WHERE {where_clause}
            ORDER BY f.created_at DESC
            LIMIT %s OFFSET %s
        """
        params.extend([limit, skip])
        rows = await self._fetch_all(query, tuple(params))

        files = [self._to_entity(row) for row in rows]

        logger.debug(f"Found {len(files)} files (total: {total}) for uploader: {uploader_id}")

        return files, total

    async def soft_delete(self, file_id: int) -> bool:
        """파일 소프트 삭제"""
        query = """
                UPDATE files
                SET is_deleted = 1
                WHERE id = %s \
                """
        rows_affected = await self._execute(query, (file_id,))

        success = rows_affected > 0
        if success:
            logger.info(f"File soft deleted - ID: {file_id}")

        return success

    async def restore(self, file_id: int) -> bool:
        """삭제된 파일 복구"""
        query = """
                UPDATE files
                SET is_deleted = 0
                WHERE id = %s \
                """
        rows_affected = await self._execute(query, (file_id,))

        success = rows_affected > 0
        if success:
            logger.info(f"File restored - ID: {file_id}")

        return success

    async def increment_download_count(self, file_id: int) -> None:
        """다운로드 횟수 증가"""
        query = """
                UPDATE files
                SET download_count = download_count + 1
                WHERE id = %s \
                """
        await self._execute(query, (file_id,))
        logger.debug(f"Download count incremented - ID: {file_id}")