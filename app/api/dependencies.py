"""
API dependencies - Dependency Injection setup
"""
from fastapi import Depends, HTTPException, status
from app.services.user_service import UserService
from app.services.auth_service import AuthService
from app.services.post_service import PostService
from app.services.file_service import FileService
from app.services.shop_service import ShopService
from app.services.comment_service import CommentService
from app.repositories.user_repository import UserRepository
from app.repositories.post_repository import PostRepository
from app.repositories.file_repository import FileRepository
from app.repositories.post_attachment_repository import PostAttachmentRepository
from app.repositories.temp_file_repository import TempFileRepository
from app.repositories.comment_repository import CommentRepository
from app.repositories.shop_repository import ShopRepository
from app.domain.entities.user import UserEntity
from app.core.dependencies import get_current_user as get_user_dict, get_optional_user as get_optional_user_dict


def get_shop_service() -> ShopService:
    shop_repository = ShopRepository()
    return ShopService(shop_repository)

# Repository factories
def get_user_repository() -> UserRepository:
    """
    UserRepository 인스턴스 생성

    Returns:
        UserRepository: 사용자 repository 인스턴스
    """
    return UserRepository()

def get_post_service() -> PostService:
    """
    PostService 인스턴스 생성 (의존성 주입)

    Returns:
        PostService: 게시글 서비스 인스턴스
    """
    post_repository = PostRepository()
    return PostService(post_repository)

def get_file_service() -> FileService:
    """
    FileService 인스턴스 생성 (의존성 주입)

    Returns:
        FileService: 파일 서비스 인스턴스
    """
    file_repository = FileRepository()
    post_attachment_repository = PostAttachmentRepository()
    temp_file_repository = TempFileRepository()
    return FileService(
        file_repository,
        post_attachment_repository,
        temp_file_repository
    )


def get_comment_service() -> CommentService:
    """
    CommentService 인스턴스 생성 (의존성 주입)

    Returns:
        CommentService: 댓글 서비스 인스턴스
    """
    comment_repository = CommentRepository()
    return CommentService(comment_repository)


# Service factories (with dependency injection)
def get_user_service(
    user_repo: UserRepository = Depends(get_user_repository)
) -> UserService:
    """
    UserService 인스턴스 생성 (Repository 주입)

    Args:
        user_repo: 주입될 UserRepository 인스턴스

    Returns:
        UserService: 사용자 service 인스턴스
    """
    return UserService(user_repository=user_repo)


def get_auth_service(
    user_repo: UserRepository = Depends(get_user_repository)
) -> AuthService:
    """
    AuthService 인스턴스 생성 (Repository 주입)

    Args:
        user_repo: 주입될 UserRepository 인스턴스

    Returns:
        AuthService: 인증 service 인스턴스
    """
    return AuthService(user_repository=user_repo)


# Current user dependencies (convert dict to entity)
async def get_current_user(
    user_dict: dict = Depends(get_user_dict)
) -> UserEntity:
    """
    현재 인증된 사용자를 UserEntity로 변환

    기존 core/dependencies.py의 get_current_user는 dict를 반환하므로,
    이를 UserEntity로 변환하여 Service 계층에서 사용하기 쉽게 만듭니다.

    Args:
        user_dict: 기존 dependency에서 반환된 사용자 dict

    Returns:
        UserEntity: 사용자 엔티티
    """
    return UserEntity(**user_dict)


async def get_optional_user(
    user_dict: dict | None = Depends(get_optional_user_dict)
) -> UserEntity | None:
    """
    현재 인증된 사용자를 UserEntity로 변환 (선택적)

    토큰이 없거나 유효하지 않으면 None을 반환합니다.
    게스트 사용자를 허용하는 엔드포인트에서 사용합니다.

    Args:
        user_dict: 기존 dependency에서 반환된 사용자 dict (또는 None)

    Returns:
        UserEntity | None: 사용자 엔티티 또는 None
    """
    if user_dict is None:
        return None
    return UserEntity(**user_dict)


async def get_current_admin_user(
    current_user: UserEntity = Depends(get_current_user)
) -> UserEntity:
    """
    현재 인증된 관리자 사용자 가져오기

    Args:
        current_user: 현재 인증된 사용자

    Returns:
        UserEntity: 관리자 사용자 엔티티

    Raises:
        HTTPException: 관리자 권한이 없는 경우
    """
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="관리자 권한이 필요합니다"
        )
    return current_user
