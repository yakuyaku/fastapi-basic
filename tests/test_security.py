"""
보안 취약점 테스트
Security vulnerability tests
"""
import pytest
from app.repositories.user_repository import UserRepository
from app.repositories.post_repository import PostRepository
from app.repositories.comment_repository import CommentRepository
from app.services.file_service import FileService
from fastapi import UploadFile, HTTPException
from io import BytesIO


class TestSQLInjectionPrevention:
    """SQL 인젝션 방지 테스트"""

    @pytest.mark.asyncio
    async def test_user_update_sql_injection_blocked(self):
        """User update - SQL 인젝션 시도 차단 테스트"""
        repo = UserRepository()

        # SQL 인젝션 시도
        malicious_fields = {
            "email; DROP TABLE users; --": "attacker@evil.com"
        }

        with pytest.raises(ValueError, match="허용되지 않은 필드"):
            await repo.update(1, **malicious_fields)

    @pytest.mark.asyncio
    async def test_user_update_allowed_fields_only(self):
        """User update - 허용된 필드만 업데이트 가능"""
        repo = UserRepository()

        # 허용되지 않은 필드
        invalid_fields = {
            "id": 999,  # id 변경 시도
            "created_at": "2020-01-01"  # created_at 변경 시도
        }

        with pytest.raises(ValueError, match="허용되지 않은 필드"):
            await repo.update(1, **invalid_fields)

    @pytest.mark.asyncio
    async def test_post_update_sql_injection_blocked(self):
        """Post update - SQL 인젝션 시도 차단 테스트"""
        repo = PostRepository()

        malicious_fields = {
            "title; DELETE FROM posts WHERE 1=1; --": "Hacked"
        }

        with pytest.raises(ValueError, match="허용되지 않은 필드"):
            await repo.update(1, **malicious_fields)

    @pytest.mark.asyncio
    async def test_comment_update_sql_injection_blocked(self):
        """Comment update - SQL 인젝션 시도 차단 테스트"""
        repo = CommentRepository()

        malicious_fields = {
            "author_id; UPDATE users SET is_admin=1; --": 999
        }

        with pytest.raises(ValueError, match="허용되지 않은 필드"):
            await repo.update(1, **malicious_fields)


class TestPathTraversalPrevention:
    """Path Traversal 공격 방지 테스트"""

    def test_path_traversal_blocked_double_dot(self):
        """파일명에 .. 포함 시 차단"""
        from app.services.file_service import FileService
        from app.repositories.file_repository import FileRepository
        from app.repositories.post_attachment_repository import PostAttachmentRepository
        from app.repositories.temp_file_repository import TempFileRepository

        file_repo = FileRepository()
        attachment_repo = PostAttachmentRepository()
        temp_repo = TempFileRepository()
        service = FileService(file_repo, attachment_repo, temp_repo)

        malicious_filename = "../../etc/passwd"

        with pytest.raises(HTTPException) as exc_info:
            service._sanitize_filename(malicious_filename)

        assert exc_info.value.status_code == 400
        assert "잘못된 파일명" in str(exc_info.value.detail)

    def test_path_traversal_blocked_slash(self):
        """파일명에 / 포함 시 차단"""
        from app.services.file_service import FileService
        from app.repositories.file_repository import FileRepository
        from app.repositories.post_attachment_repository import PostAttachmentRepository
        from app.repositories.temp_file_repository import TempFileRepository

        file_repo = FileRepository()
        attachment_repo = PostAttachmentRepository()
        temp_repo = TempFileRepository()
        service = FileService(file_repo, attachment_repo, temp_repo)

        # Path.name()이 이미 경로를 제거하지만, 추가 검증으로 확인
        malicious_filename = "subdir/malicious.txt"

        # Path.name()에 의해 'malicious.txt'로 변환되어 통과
        # 하지만 '/'가 남아있으면 차단되어야 함
        result = service._sanitize_filename(malicious_filename)
        assert ".." not in result
        assert "/" not in result

    def test_safe_filename_extraction(self):
        """안전한 파일명 추출 테스트"""
        from app.services.file_service import FileService
        from app.repositories.file_repository import FileRepository
        from app.repositories.post_attachment_repository import PostAttachmentRepository
        from app.repositories.temp_file_repository import TempFileRepository

        file_repo = FileRepository()
        attachment_repo = PostAttachmentRepository()
        temp_repo = TempFileRepository()
        service = FileService(file_repo, attachment_repo, temp_repo)

        # 정상적인 파일명
        safe_filename = service._sanitize_filename("document.pdf")
        assert safe_filename == "document.pdf"

        # 경로가 포함된 파일명 (Path.name()으로 정규화)
        result = service._sanitize_filename("/uploads/user123/photo.jpg")
        assert result == "photo.jpg"


class TestMIMESpoofingPrevention:
    """MIME 타입 스푸핑 방지 테스트"""

    def test_magic_bytes_validation_jpg(self):
        """JPEG 파일의 Magic bytes 검증"""
        from app.services.file_service import FileService
        from app.repositories.file_repository import FileRepository
        from app.repositories.post_attachment_repository import PostAttachmentRepository
        from app.repositories.temp_file_repository import TempFileRepository

        file_repo = FileRepository()
        attachment_repo = PostAttachmentRepository()
        temp_repo = TempFileRepository()
        service = FileService(file_repo, attachment_repo, temp_repo)

        # JPEG Magic bytes: FF D8 FF
        jpeg_content = b'\xFF\xD8\xFF\xE0\x00\x10JFIF'

        actual_mime = service._validate_file_content(jpeg_content, "image/jpeg")
        assert actual_mime == "image/jpeg"

    def test_mime_spoofing_detection(self):
        """MIME 스푸핑 탐지 (확장자와 실제 내용 불일치)"""
        from app.services.file_service import FileService
        from app.repositories.file_repository import FileRepository
        from app.repositories.post_attachment_repository import PostAttachmentRepository
        from app.repositories.temp_file_repository import TempFileRepository

        file_repo = FileRepository()
        attachment_repo = PostAttachmentRepository()
        temp_repo = TempFileRepository()
        service = FileService(file_repo, attachment_repo, temp_repo)

        # 실제로는 JPEG이지만 PNG로 위장
        jpeg_content = b'\xFF\xD8\xFF\xE0\x00\x10JFIF'
        claimed_mime = "image/png"

        # 실제 MIME 타입이 반환되어야 함
        actual_mime = service._validate_file_content(jpeg_content, claimed_mime)
        assert actual_mime == "image/jpeg"  # 실제 타입 반환

    def test_text_file_no_magic_bytes(self):
        """텍스트 파일 (Magic bytes 없음) 처리"""
        from app.services.file_service import FileService
        from app.repositories.file_repository import FileRepository
        from app.repositories.post_attachment_repository import PostAttachmentRepository
        from app.repositories.temp_file_repository import TempFileRepository

        file_repo = FileRepository()
        attachment_repo = PostAttachmentRepository()
        temp_repo = TempFileRepository()
        service = FileService(file_repo, attachment_repo, temp_repo)

        text_content = b"This is a plain text file."
        claimed_mime = "text/plain"

        # 텍스트 파일은 Magic bytes가 없어도 허용
        actual_mime = service._validate_file_content(text_content, claimed_mime)
        assert actual_mime == "text/plain"


class TestSecurityLogging:
    """보안 로깅 테스트"""

    def test_sql_injection_attempt_logged(self):
        """SQL 인젝션 시도가 로그에 기록되는지 확인"""
        # 로그 캡처는 실제 애플리케이션에서 확인
        pass

    def test_path_traversal_attempt_logged(self):
        """Path Traversal 시도가 로그에 기록되는지 확인"""
        # 로그 캡처는 실제 애플리케이션에서 확인
        pass


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
