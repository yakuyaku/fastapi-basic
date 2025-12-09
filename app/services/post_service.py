"""
Post service - Business logic for post operations
app/services/post_service.py
"""
from typing import Optional, Tuple
from fastapi import HTTPException, status
from app.domain.entities.post import PostEntity
from app.domain.entities.user import UserEntity
from app.domain.interfaces.post_repository import PostRepositoryProtocol
from app.schemas.post import PostCreate, PostUpdate
from app.core.logging import logger
from app.core.config import settings
from app.core.security import hash_password, verify_password, generate_random_password
import math


class PostService:
    """
    Post service

    게시글 관련 비즈니스 로직을 처리합니다.
    - 권한 검증
    - 데이터 검증
    - Repository 조합
    """

    def __init__(self, post_repository: PostRepositoryProtocol):
        """
        Args:
            post_repository: PostRepositoryProtocol을 구현한 repository 인스턴스
        """
        self.repo = post_repository

    async def create_post(
            self,
            post_data: PostCreate,
            current_user: Optional[UserEntity]
    ) -> Tuple[PostEntity, Optional[str]]:
        """
        게시글 생성 (비즈니스 로직)

        비즈니스 규칙:
        - 인증된 사용자 또는 게스트 사용자 작성 가능
        - 제목/내용 필수
        - 고정 게시글은 관리자만 생성 가능
        - 게스트 사용자는 author_id = 0으로 설정

        Args:
            post_data: 게시글 생성 데이터
            current_user: 현재 인증된 사용자 (None이면 게스트)

        Returns:
            PostEntity: 생성된 게시글 엔티티

        Raises:
            HTTPException: 권한 없음
        """
        # 게스트 사용자 처리
        author_id = current_user.id if current_user else settings.GUEST_USER_ID
        is_admin = current_user.is_admin if current_user else False
        is_guest = (author_id == settings.GUEST_USER_ID)

        logger.info(f"Creating post - user: {'guest' if is_guest else author_id}, title: {post_data.title}")

        # 비즈니스 규칙: 고정 게시글은 관리자만 생성 가능
        if post_data.is_pinned and not is_admin:
            logger.warning(f"Non-admin user tried to create pinned post - user: {author_id}")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="고정 게시글은 관리자만 생성할 수 있습니다"
            )

        # 비밀번호 처리 (게스트 게시글)
        plain_password = None
        hashed_password = None

        if is_guest:
            if post_data.password:
                # 사용자가 비밀번호를 입력한 경우
                plain_password = post_data.password
                hashed_password = hash_password(plain_password)
            else:
                # 비밀번호 자동 생성
                plain_password = generate_random_password(8)
                hashed_password = hash_password(plain_password)
                logger.info(f"Auto-generated password for guest post")

        # Repository 호출
        post = await self.repo.create(
            title=post_data.title,
            content=post_data.content,
            author_id=author_id,
            is_pinned=post_data.is_pinned,
            password=hashed_password
        )

        logger.info(f"Post created successfully - ID: {post.id}, author: {author_id}")

        # 게스트 게시글의 경우 평문 비밀번호 반환 (응답에서 사용)
        return post, plain_password if is_guest else None

    async def get_post(
            self,
            post_id: int,
            current_user: Optional[UserEntity] = None,
            increment_view: bool = True
    ) -> PostEntity:
        """
        게시글 조회 (작성자 정보 포함)

        비즈니스 규칙:
        - 삭제된 게시글은 관리자만 조회 가능
        - 조회수 자동 증가 (선택적)

        Args:
            post_id: 조회할 게시글 ID
            current_user: 현재 인증된 사용자 (선택)
            increment_view: 조회수 증가 여부

        Returns:
            PostEntity: 조회된 게시글 엔티티

        Raises:
            HTTPException: 게시글 없음 또는 접근 권한 없음
        """
        post = await self.repo.find_by_id_with_author(post_id)

        if not post:
            logger.warning(f"Post not found - ID: {post_id}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="게시글을 찾을 수 없습니다"
            )

        # 비즈니스 규칙: 삭제된 게시글은 관리자만 조회 가능
        if post.is_deleted:
            if not current_user or not current_user.is_admin:
                logger.warning(f"Unauthorized access to deleted post - ID: {post_id}")
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="게시글을 찾을 수 없습니다"
                )

        # 조회수 증가 (삭제된 게시글은 제외)
        if increment_view and not post.is_deleted:
            await self.repo.increment_view_count(post_id)

        logger.info(f"Post retrieved - ID: {post_id}")
        return post

    async def list_posts(
            self,
            page: int,
            page_size: int,
            search: Optional[str] = None,
            author_id: Optional[int] = None,
            is_pinned: Optional[bool] = None,
            include_deleted: bool = False,
            sort_by: str = "created_at",
            sort_order: str = "desc",
            current_user: Optional[UserEntity] = None
    ) -> dict:
        """
        게시글 목록 조회 (페이징)

        비즈니스 규칙:
        - 삭제된 게시글은 관리자만 조회 가능

        Args:
            page: 페이지 번호 (1부터 시작)
            page_size: 페이지당 항목 수
            search: 검색어 (제목 또는 내용)
            author_id: 작성자 필터
            is_pinned: 고정 게시글 필터
            include_deleted: 삭제된 게시글 포함 여부
            sort_by: 정렬 기준
            sort_order: 정렬 순서
            current_user: 현재 인증된 사용자 (선택)

        Returns:
            dict: {posts, total, page, page_size, total_pages}
        """
        # 비즈니스 규칙: 삭제된 게시글은 관리자만 조회 가능
        if include_deleted and (not current_user or not current_user.is_admin):
            include_deleted = False

        offset = (page - 1) * page_size

        posts, total = await self.repo.find_all(
            skip=offset,
            limit=page_size,
            search=search,
            author_id=author_id,
            is_pinned=is_pinned,
            include_deleted=include_deleted,
            sort_by=sort_by,
            sort_order=sort_order
        )

        total_pages = math.ceil(total / page_size) if total > 0 else 0

        logger.info(f"Listed {len(posts)} posts (page {page}/{total_pages}, total: {total})")

        return {
            "posts": posts,
            "total": total,
            "page": page,
            "page_size": page_size,
            "total_pages": total_pages
        }

    async def update_post(
            self,
            post_id: int,
            post_data: PostUpdate,
            current_user: Optional[UserEntity]
    ) -> PostEntity:
        """
        게시글 정보 수정

        비즈니스 규칙:
        - 본인이거나 관리자만 수정 가능
        - 잠긴 게시글은 관리자만 수정 가능
        - 삭제된 게시글은 수정 불가
        - 고정/잠금 설정은 관리자만 가능

        Args:
            post_id: 수정할 게시글 ID
            post_data: 수정할 데이터
            current_user: 현재 인증된 사용자

        Returns:
            PostEntity: 수정된 게시글 엔티티

        Raises:
            HTTPException: 권한 없음, 게시글 없음
        """
        user_id = current_user.id if current_user else 0
        is_admin = current_user.is_admin if current_user else False

        logger.info(f"Updating post - ID: {post_id}, by user: {user_id}")

        # 게시글 존재 확인
        post = await self.repo.find_by_id(post_id)
        if not post:
            logger.warning(f"Post not found - ID: {post_id}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="게시글을 찾을 수 없습니다"
            )

        # 비즈니스 규칙: 삭제된 게시글은 수정 불가
        if post.is_deleted:
            logger.warning(f"Cannot update deleted post - ID: {post_id}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="삭제된 게시글은 수정할 수 없습니다"
            )

        # 게스트 게시글 비밀번호 검증
        is_guest_post = (post.author_id == settings.GUEST_USER_ID)
        if is_guest_post:
            if not post_data.password:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="게스트 게시글 수정을 위해서는 비밀번호가 필요합니다"
                )

            if not post.password or not verify_password(post_data.password, post.password):
                logger.warning(f"Invalid password for guest post - ID: {post_id}")
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="비밀번호가 일치하지 않습니다"
                )
            logger.info(f"Password verified for guest post - ID: {post_id}")

        # 비즈니스 규칙: 권한 체크 (인증된 사용자)
        elif not post.can_modify(user_id, is_admin):
            logger.warning(
                f"Permission denied - User {user_id} tried to modify post {post_id}"
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="본인이 작성한 게시글만 수정할 수 있습니다"
            )

        # 비즈니스 규칙: 잠긴 게시글은 관리자만 수정 가능
        if post.is_locked and not is_admin:
            logger.warning(f"Cannot update locked post - ID: {post_id}, user: {user_id}")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="잠긴 게시글은 관리자만 수정할 수 있습니다"
            )

        # 업데이트할 필드 준비
        update_data = post_data.model_dump(exclude_unset=True)

        # password 필드 제거 (업데이트하지 않음)
        if 'password' in update_data:
            del update_data['password']

        # 비즈니스 규칙: 고정/잠금 설정은 관리자만 가능
        if 'is_pinned' in update_data and not is_admin:
            logger.warning(f"Non-admin tried to change pin status - user: {user_id}")
            del update_data['is_pinned']

        if 'is_locked' in update_data and not is_admin:
            logger.warning(f"Non-admin tried to change lock status - user: {user_id}")
            del update_data['is_locked']

        # 수정할 필드가 없으면 현재 상태 반환
        if not update_data:
            logger.info(f"No fields to update - ID: {post_id}")
            return post

        # Repository 업데이트 호출
        updated_post = await self.repo.update(post_id, **update_data)

        logger.info(f"Post updated successfully - ID: {post_id}")
        return updated_post

    async def delete_post(
            self,
            post_id: int,
            current_user: Optional[UserEntity],
            hard_delete: bool = False,
            password: Optional[str] = None
    ) -> PostEntity:
        """
        게시글 삭제

        비즈니스 규칙:
        - 본인이거나 관리자만 삭제 가능
        - Hard Delete는 관리자만 가능
        - 기본은 Soft Delete

        Args:
            post_id: 삭제할 게시글 ID
            current_user: 현재 인증된 사용자
            hard_delete: Hard Delete 여부 (관리자 전용)

        Returns:
            PostEntity: 삭제된 게시글 엔티티

        Raises:
            HTTPException: 권한 없음, 게시글 없음
        """
        user_id = current_user.id if current_user else 0
        is_admin = current_user.is_admin if current_user else False

        logger.info(f"Deleting post - ID: {post_id}, by user: {user_id}, hard: {hard_delete}")

        # 게시글 존재 확인
        post = await self.repo.find_by_id(post_id)
        if not post:
            logger.warning(f"Post not found - ID: {post_id}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="게시글을 찾을 수 없습니다"
            )

        # 게스트 게시글 비밀번호 검증
        is_guest_post = (post.author_id == settings.GUEST_USER_ID)
        if is_guest_post:
            if not password:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="게스트 게시글 삭제를 위해서는 비밀번호가 필요합니다"
                )

            if not post.password or not verify_password(password, post.password):
                logger.warning(f"Invalid password for guest post deletion - ID: {post_id}")
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="비밀번호가 일치하지 않습니다"
                )
            logger.info(f"Password verified for guest post deletion - ID: {post_id}")

        # 비즈니스 규칙: 권한 체크 (인증된 사용자)
        elif not post.can_delete(user_id, is_admin):
            logger.warning(
                f"Permission denied - User {user_id} tried to delete post {post_id}"
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="본인이 작성한 게시글만 삭제할 수 있습니다"
            )

        # 삭제 수행
        if hard_delete and is_admin:
            # Hard Delete (관리자 전용)
            success = await self.repo.delete(post_id)
            if not success:
                logger.error(f"Failed to delete post - ID: {post_id}")
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="게시글 삭제 중 오류가 발생했습니다"
                )
            logger.info(f"Post hard deleted - ID: {post_id}")
        else:
            # Soft Delete (기본)
            success = await self.repo.soft_delete(post_id)
            if not success:
                logger.error(f"Failed to soft delete post - ID: {post_id}")
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="게시글 삭제 중 오류가 발생했습니다"
                )
            logger.info(f"Post soft deleted - ID: {post_id}")

        return post

    async def restore_post(self, post_id: int) -> PostEntity:
        """
        삭제된 게시글 복구 (관리자 전용)

        비즈니스 규칙:
        - 이미 활성화된 게시글은 에러

        Args:
            post_id: 복구할 게시글 ID

        Returns:
            PostEntity: 복구된 게시글 엔티티

        Raises:
            HTTPException: 이미 활성화된 경우, 게시글 없음
        """
        logger.info(f"Restoring post - ID: {post_id}")

        # 게시글 존재 확인
        post = await self.repo.find_by_id(post_id)
        if not post:
            logger.warning(f"Post not found - ID: {post_id}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="게시글을 찾을 수 없습니다"
            )

        # 비즈니스 규칙: 이미 활성화된 경우
        if not post.is_deleted:
            logger.info(f"Post already active - ID: {post_id}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="이미 활성화된 게시글입니다"
            )

        # 복구 수행
        success = await self.repo.restore(post_id)
        if not success:
            logger.error(f"Failed to restore post - ID: {post_id}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="게시글 복구 중 오류가 발생했습니다"
            )

        # 복구된 게시글 조회
        restored_post = await self.repo.find_by_id(post_id)

        logger.info(f"Post restored successfully - ID: {post_id}")
        return restored_post

    async def toggle_pin(self, post_id: int, current_user: UserEntity) -> PostEntity:
        """
        게시글 고정/고정 해제 (관리자 전용)

        Args:
            post_id: 게시글 ID
            current_user: 현재 인증된 사용자 (관리자)

        Returns:
            PostEntity: 업데이트된 게시글 엔티티

        Raises:
            HTTPException: 게시글 없음
        """
        logger.info(f"Toggling pin - ID: {post_id}, by admin: {current_user.id}")

        # 게시글 존재 확인
        post = await self.repo.find_by_id(post_id)
        if not post:
            logger.warning(f"Post not found - ID: {post_id}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="게시글을 찾을 수 없습니다"
            )

        # 고정/해제 토글
        new_state = await self.repo.toggle_pin(post_id)

        # 업데이트된 게시글 조회
        updated_post = await self.repo.find_by_id(post_id)

        logger.info(f"Post pin toggled - ID: {post_id}, is_pinned: {new_state}")
        return updated_post

    async def toggle_lock(self, post_id: int, current_user: UserEntity) -> PostEntity:
        """
        게시글 잠금/잠금 해제 (관리자 전용)

        Args:
            post_id: 게시글 ID
            current_user: 현재 인증된 사용자 (관리자)

        Returns:
            PostEntity: 업데이트된 게시글 엔티티

        Raises:
            HTTPException: 게시글 없음
        """
        logger.info(f"Toggling lock - ID: {post_id}, by admin: {current_user.id}")

        # 게시글 존재 확인
        post = await self.repo.find_by_id(post_id)
        if not post:
            logger.warning(f"Post not found - ID: {post_id}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="게시글을 찾을 수 없습니다"
            )

        # 잠금/해제 토글
        new_state = await self.repo.toggle_lock(post_id)

        # 업데이트된 게시글 조회
        updated_post = await self.repo.find_by_id(post_id)

        logger.info(f"Post lock toggled - ID: {post_id}, is_locked: {new_state}")
        return updated_post

    async def increment_like(self, post_id: int) -> PostEntity:
        """
        좋아요 수 증가

        Args:
            post_id: 게시글 ID

        Returns:
            PostEntity: 업데이트된 게시글 엔티티

        Raises:
            HTTPException: 게시글 없음
        """
        # 게시글 존재 확인
        post = await self.repo.find_by_id(post_id)
        if not post:
            logger.warning(f"Post not found - ID: {post_id}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="게시글을 찾을 수 없습니다"
            )

        if post.is_deleted:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="게시글을 찾을 수 없습니다"
            )

        await self.repo.increment_like_count(post_id)

        # 업데이트된 게시글 조회
        updated_post = await self.repo.find_by_id(post_id)

        logger.info(f"Like count incremented - ID: {post_id}")
        return updated_post

    async def decrement_like(self, post_id: int) -> PostEntity:
        """
        좋아요 수 감소

        Args:
            post_id: 게시글 ID

        Returns:
            PostEntity: 업데이트된 게시글 엔티티

        Raises:
            HTTPException: 게시글 없음
        """
        # 게시글 존재 확인
        post = await self.repo.find_by_id(post_id)
        if not post:
            logger.warning(f"Post not found - ID: {post_id}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="게시글을 찾을 수 없습니다"
            )

        if post.is_deleted:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="게시글을 찾을 수 없습니다"
            )

        await self.repo.decrement_like_count(post_id)

        # 업데이트된 게시글 조회
        updated_post = await self.repo.find_by_id(post_id)

        logger.info(f"Like count decremented - ID: {post_id}")
        return updated_post