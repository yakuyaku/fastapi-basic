"""
수동 보안 테스트
Manual security test without pytest
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.file_service import FileService
from app.repositories.file_repository import FileRepository
from app.repositories.post_attachment_repository import PostAttachmentRepository
from app.repositories.temp_file_repository import TempFileRepository
from app.repositories.user_repository import UserRepository
from app.repositories.post_repository import PostRepository
from app.repositories.comment_repository import CommentRepository


def test_sql_injection_prevention():
    """SQL 인젝션 방지 테스트"""
    print("\n🔒 SQL Injection Prevention Tests")
    print("=" * 60)

    # User Repository 테스트
    print("\n[TEST 1] User Repository - Malicious field injection")
    try:
        repo = UserRepository()
        malicious_fields = {
            "email; DROP TABLE users; --": "attacker@evil.com"
        }
        # 이 코드는 실행되지 않아야 함 (ValueError 발생)
        print("❌ FAILED: SQL injection was NOT blocked!")
    except ValueError as e:
        if "허용되지 않은 필드" in str(e):
            print(f"✅ PASSED: {e}")
        else:
            print(f"❌ FAILED: Wrong error message: {e}")
    except Exception as e:
        print(f"❌ FAILED: Unexpected error: {e}")

    # Post Repository 테스트
    print("\n[TEST 2] Post Repository - Malicious field injection")
    try:
        repo = PostRepository()
        malicious_fields = {
            "title; DELETE FROM posts; --": "Hacked"
        }
        print("❌ FAILED: SQL injection was NOT blocked!")
    except ValueError as e:
        if "허용되지 않은 필드" in str(e):
            print(f"✅ PASSED: {e}")
        else:
            print(f"❌ FAILED: Wrong error message: {e}")
    except Exception as e:
        print(f"❌ FAILED: Unexpected error: {e}")

    # Comment Repository 테스트
    print("\n[TEST 3] Comment Repository - Malicious field injection")
    try:
        repo = CommentRepository()
        malicious_fields = {
            "author_id; UPDATE users SET is_admin=1; --": 999
        }
        print("❌ FAILED: SQL injection was NOT blocked!")
    except ValueError as e:
        if "허용되지 않은 필드" in str(e):
            print(f"✅ PASSED: {e}")
        else:
            print(f"❌ FAILED: Wrong error message: {e}")
    except Exception as e:
        print(f"❌ FAILED: Unexpected error: {e}")


def test_path_traversal_prevention():
    """Path Traversal 방지 테스트"""
    print("\n\n🔒 Path Traversal Prevention Tests")
    print("=" * 60)

    file_repo = FileRepository()
    attachment_repo = PostAttachmentRepository()
    temp_repo = TempFileRepository()
    service = FileService(file_repo, attachment_repo, temp_repo)

    # 테스트 1: .. 포함
    print("\n[TEST 4] Path Traversal - Double dot attack")
    try:
        malicious_filename = "../../etc/passwd"
        result = service._sanitize_filename(malicious_filename)
        print(f"❌ FAILED: Path traversal was NOT blocked! Result: {result}")
    except Exception as e:
        if "잘못된 파일명" in str(e):
            print(f"✅ PASSED: {e}")
        else:
            print(f"⚠️  PARTIAL: {e}")

    # 테스트 2: 정상 파일명
    print("\n[TEST 5] Path Traversal - Safe filename")
    try:
        safe_filename = "document.pdf"
        result = service._sanitize_filename(safe_filename)
        if result == "document.pdf":
            print(f"✅ PASSED: Safe filename accepted: {result}")
        else:
            print(f"❌ FAILED: Unexpected result: {result}")
    except Exception as e:
        print(f"❌ FAILED: Should accept safe filename: {e}")

    # 테스트 3: 경로 포함 파일명
    print("\n[TEST 6] Path Traversal - Filename with path")
    try:
        filename_with_path = "/uploads/user123/photo.jpg"
        result = service._sanitize_filename(filename_with_path)
        if result == "photo.jpg":
            print(f"✅ PASSED: Path stripped correctly: {result}")
        else:
            print(f"⚠️  PARTIAL: Got '{result}', expected 'photo.jpg'")
    except Exception as e:
        print(f"❌ FAILED: {e}")


def test_mime_spoofing_prevention():
    """MIME 스푸핑 방지 테스트"""
    print("\n\n🔒 MIME Spoofing Prevention Tests")
    print("=" * 60)

    file_repo = FileRepository()
    attachment_repo = PostAttachmentRepository()
    temp_repo = TempFileRepository()
    service = FileService(file_repo, attachment_repo, temp_repo)

    # 테스트 1: JPEG Magic bytes
    print("\n[TEST 7] Magic Bytes - Valid JPEG")
    try:
        jpeg_content = b'\xFF\xD8\xFF\xE0\x00\x10JFIF'
        actual_mime = service._validate_file_content(jpeg_content, "image/jpeg")
        if actual_mime == "image/jpeg":
            print(f"✅ PASSED: JPEG detected correctly: {actual_mime}")
        else:
            print(f"⚠️  PARTIAL: Got {actual_mime}, expected image/jpeg")
    except Exception as e:
        print(f"❌ FAILED: {e}")

    # 테스트 2: MIME 스푸핑 탐지
    print("\n[TEST 8] Magic Bytes - MIME spoofing detection")
    try:
        jpeg_content = b'\xFF\xD8\xFF\xE0\x00\x10JFIF'
        claimed_mime = "image/png"  # 거짓 주장
        actual_mime = service._validate_file_content(jpeg_content, claimed_mime)
        if actual_mime == "image/jpeg":
            print(f"✅ PASSED: Spoofing detected, real type returned: {actual_mime}")
        else:
            print(f"❌ FAILED: Expected image/jpeg, got {actual_mime}")
    except Exception as e:
        print(f"❌ FAILED: {e}")

    # 테스트 3: 텍스트 파일 (Magic bytes 없음)
    print("\n[TEST 9] Magic Bytes - Text file (no magic bytes)")
    try:
        text_content = b"This is a plain text file."
        claimed_mime = "text/plain"
        actual_mime = service._validate_file_content(text_content, claimed_mime)
        if actual_mime == "text/plain":
            print(f"✅ PASSED: Text file accepted: {actual_mime}")
        else:
            print(f"⚠️  PARTIAL: Got {actual_mime}")
    except Exception as e:
        print(f"❌ FAILED: {e}")

    # 테스트 4: PNG Magic bytes
    print("\n[TEST 10] Magic Bytes - Valid PNG")
    try:
        png_content = b'\x89PNG\r\n\x1a\n'
        actual_mime = service._validate_file_content(png_content, "image/png")
        if actual_mime == "image/png":
            print(f"✅ PASSED: PNG detected correctly: {actual_mime}")
        else:
            print(f"⚠️  PARTIAL: Got {actual_mime}, expected image/png")
    except Exception as e:
        print(f"❌ FAILED: {e}")


def main():
    """메인 테스트 실행"""
    print("\n" + "=" * 60)
    print("🔐 SECURITY VULNERABILITY TESTS")
    print("=" * 60)

    test_sql_injection_prevention()
    test_path_traversal_prevention()
    test_mime_spoofing_prevention()

    print("\n" + "=" * 60)
    print("✅ All security tests completed!")
    print("=" * 60 + "\n")


if __name__ == "__main__":
    main()
