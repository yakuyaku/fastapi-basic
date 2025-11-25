"""
Temp File repository implementation
app/repositories/temp_file_repository.py
"""
from typing import Optional, List
from datetime import datetime
from app.repositories.base import BaseRepository
from app.domain.entities.file import TempFileEntity, FileEntity
from app.core.logging import logger


class TempFileRepository(BaseRepository):
    """TempFile repository implementation"""

    def _to_entity(self, row: Optional[dict]) -> Optional[TempFileEntity]:
        """데이터베이스 row를 TempFileEntity로 변환"""
        if not row:
            return None

        temp_file = TempFileEntity(
            id=row.get('id'),
            file_id=row.get('file_id', 0),
            uploader_id=row.get('uploader_id', 0),
            expires_at=row.get('expires_at'),
            created_at=row.get('created_at')
        )

        # JOIN으로 파일 정보가 있는 경우
        if row.get('file_original_filename'):
            temp_file.file = FileEntity(
                id=row.get('file_id'),
                original_filename=row.get('file_original_filename', ''),
                stored_filename=row.get('file_stored_filename', ''),
                file_path=row.get('file_path', ''),
                file_size=row.get('file_size', 0),
                mime_type=row.get('mime_type', ''),
                file_extension=row.get('file_extension'),
                uploader_id=row.get('file_uploader_id', 0),
                download_count=row.get('download_count', 0),
                created_at=row.get('file_created_at'),
                is_deleted=bool(row.get('file_is_deleted', 0)),
                is_public=bool(row.get('file_is_public', 1))
            )

        return temp_file

    async def create(
            self,
            file_id: int,
            uploader_id: int,
            expires_at: datetime
    ) -> TempFileEntity:
        """임시 파일 생성"""
        query = """
                INSERT INTO TEMP_files (file_id, uploader_id, expires_at)
                VALUES (%s, %s, %s) \
                """
        temp_file_id = await self._execute(query, (file_id, uploader_id, expires_at))

        logger.info(f"Temp file created - ID: {temp_file_id}, file: {file_id}, uploader: {uploader_id}")

        # 생성된 임시 파일 조회
        query = """
                SELECT id, file_id, uploader_id, expires_at, created_at
                FROM TEMP_files
                WHERE id = %s \
                """
        row = await self._fetch_one(query, (temp_file_id,))
        return self._to_entity(row)

    async def find_by_file_id(self, file_id: int) -> Optional[TempFileEntity]:
        """파일 ID로 임시 파일 조회"""
        query = """
                SELECT id, file_id, uploader_id, expires_at, created_at
                FROM TEMP_files
                WHERE file_id = %s \
                """
        row = await self._fetch_one(query, (file_id,))
        return self._to_entity(row)

    async def find_expired(self) -> List[TempFileEntity]:
        """만료된 임시 파일 목록 조회 (파일 정보 포함)"""
        query = """
                SELECT
                    tf.id, tf.file_id, tf.uploader_id, tf.expires_at, tf.created_at,
                    f.original_filename as file_original_filename,
                    f.stored_filename as file_stored_filename,
                    f.file_path,
                    f.file_size,
                    f.mime_type,
                    f.file_extension,
                    f.uploader_id as file_uploader_id,
                    f.download_count,
                    f.created_at as file_created_at,
                    f.is_deleted as file_is_deleted,
                    f.is_public as file_is_public
                FROM TEMP_files tf
                         INNER JOIN files f ON tf.file_id = f.id
                WHERE tf.expires_at < NOW() \
                """
        rows = await self._fetch_all(query, ())
        temp_files = [self._to_entity(row) for row in rows]

        logger.debug(f"Found {len(temp_files)} expired temp files")

        return temp_files

    async def delete(self, temp_file_id: int) -> bool:
        """임시 파일 레코드 삭제"""
        query = "DELETE FROM TEMP_files WHERE id = %s"
        rows_affected = await self._execute(query, (temp_file_id,))

        success = rows_affected > 0
        if success:
            logger.info(f"Temp file deleted - ID: {temp_file_id}")

        return success

    async def delete_by_file_id(self, file_id: int) -> bool:
        """파일 ID로 임시 파일 레코드 삭제"""
        query = "DELETE FROM TEMP_files WHERE file_id = %s"
        rows_affected = await self._execute(query, (file_id,))

        success = rows_affected > 0
        if success:
            logger.info(f"Temp file deleted by file_id: {file_id}")

        return success

    async def cleanup_expired(self) -> int:
        """만료된 임시 파일 정리 (레코드만 삭제)"""
        query = "DELETE FROM TEMP_files WHERE expires_at < NOW()"
        rows_affected = await self._execute(query, ())

        if rows_affected > 0:
            logger.info(f"Cleaned up {rows_affected} expired temp files")

        return rows_affected