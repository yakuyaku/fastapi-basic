"""
Comment service - Business logic for comment operations
app/services/comment_service.py
"""
from typing import Optional, List, Dict
from fastapi import HTTPException, status
from app.domain.entities.comment import CommentEntity
from app.domain.entities.user import UserEntity
from app.domain.interfaces.comment_repository import CommentRepositoryProtocol
from app.schemas.comment import CommentCreate, CommentUpdate
from app.core.logging import logger
from app.core.config import settings


class CommentService:
    """
    Comment service

    Tree 구조의 계층형 댓글 시스템 비즈니스 로직을 처리합니다.
    - 최대 깊이 제한 (예: 3단계까지)
    - path 자동 생성
    - order_num 자동 계산
    - Tree 구조 변환
    """

    MAX_DEPTH = 3  # 최대 댓글 깊이 (0: 최상위, 1: 1차 대댓글, 2: 2차 대댓글)

    def __init__(self, comment_repository: CommentRepositoryProtocol):
        self.repo = comment_repository

    async def create_comment(
            self,
            post_id: int,
            comment_data: CommentCreate,
            current_user: Optional[UserEntity]
    ) -> CommentEntity:
        """
        댓글 생성

        비즈니스 규칙:
        - 인증된 사용자 또는 게스트 사용자 작성 가능
        - 최대 깊이 제한
        - parent_id가 있으면 부모 댓글 존재 확인
        - depth, path, order_num 자동 계산
        - 게스트 사용자는 author_id = 0으로 설정

        Args:
            post_id: 게시글 ID
            comment_data: 댓글 생성 데이터
            current_user: 현재 인증된 사용자 (None이면 게스트)

        Returns:
            CommentEntity: 생성된 댓글 엔티티
        """
        # 게스트 사용자 처리
        author_id = current_user.id if current_user else settings.GUEST_USER_ID

        logger.info(
            f"Creating comment - post: {post_id}, user: {'guest' if author_id == settings.GUEST_USER_ID else author_id}, "
            f"parent: {comment_data.parent_id}"
        )

        parent_comment = None
        depth = 0
        path = None

        # 대댓글인 경우
        if comment_data.parent_id:
            # 부모 댓글 존재 확인
            parent_comment = await self.repo.find_by_id(comment_data.parent_id)
            if not parent_comment:
                logger.warning(f"Parent comment not found - ID: {comment_data.parent_id}")
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="부모 댓글을 찾을 수 없습니다"
                )

            # 삭제된 댓글에는 답글 불가
            if parent_comment.is_deleted:
                logger.warning(f"Cannot reply to deleted comment - ID: {comment_data.parent_id}")
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="삭제된 댓글에는 답글을 달 수 없습니다"
                )

            # 최대 깊이 체크
            depth = parent_comment.depth + 1
            if depth > self.MAX_DEPTH:
                logger.warning(f"Max depth exceeded - current: {depth}, max: {self.MAX_DEPTH}")
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"댓글은 최대 {self.MAX_DEPTH + 1}단계까지만 가능합니다"
                )

        # order_num 계산 (같은 레벨에서 마지막 순서)
        max_order = await self.repo.get_max_order_num(post_id, comment_data.parent_id)
        order_num = max_order + 1

        # path 임시 생성 (최상위: "0", 대댓글: parent_path + "/0")
        # 실제 path는 댓글 생성 후 ID로 업데이트
        if parent_comment and parent_comment.path:
            temp_path = f"{parent_comment.path}/0"
        else:
            temp_path = "0"

        # 댓글 생성
        comment = await self.repo.create(
            post_id=post_id,
            author_id=author_id,
            content=comment_data.content,
            parent_id=comment_data.parent_id,
            depth=depth,
            path=temp_path,  # 임시 path
            order_num=order_num
        )

        # path 업데이트 (실제 ID로 변경)
        if parent_comment and parent_comment.path:
            new_path = f"{parent_comment.path}/{comment.id}"
        else:
            new_path = str(comment.id)

        await self.repo.update(comment.id, path=new_path)
        comment.path = new_path

        logger.info(
            f"Comment created successfully - ID: {comment.id}, depth: {depth}, path: {new_path}"
        )
        return comment

    async def get_comment(self, comment_id: int) -> CommentEntity:
        """
        댓글 단건 조회

        Args:
            comment_id: 댓글 ID

        Returns:
            CommentEntity: 댓글 엔티티
        """
        comment = await self.repo.find_by_id_with_author(comment_id)

        if not comment:
            logger.warning(f"Comment not found - ID: {comment_id}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="댓글을 찾을 수 없습니다"
            )

        return comment

    async def get_post_comments(
            self,
            post_id: int,
            include_deleted: bool = False,
            as_tree: bool = True
    ) -> List[CommentEntity]:
        """
        게시글의 댓글 목록 조회

        Args:
            post_id: 게시글 ID
            include_deleted: 삭제된 댓글 포함 여부
            as_tree: Tree 구조로 변환 여부

        Returns:
            List[CommentEntity]: 댓글 목록 (Tree 구조 또는 Flat)
        """
        comments = await self.repo.find_by_post_id(post_id, include_deleted)

        if as_tree:
            # Flat 리스트를 Tree 구조로 변환
            return self._build_comment_tree(comments)

        return comments

    async def get_comment_count(self, post_id: int) -> int:
        """게시글의 댓글 개수 조회"""
        return await self.repo.count_by_post_id(post_id, include_deleted=False)

    async def update_comment(
            self,
            comment_id: int,
            comment_data: CommentUpdate,
            current_user: UserEntity
    ) -> CommentEntity:
        """
        댓글 수정

        비즈니스 규칙:
        - 본인이거나 관리자만 수정 가능
        - 삭제된 댓글은 수정 불가

        Args:
            comment_id: 댓글 ID
            comment_data: 수정할 데이터
            current_user: 현재 인증된 사용자

        Returns:
            CommentEntity: 수정된 댓글 엔티티
        """
        logger.info(f"Updating comment - ID: {comment_id}, by user: {current_user.id}")

        # 댓글 존재 확인
        comment = await self.repo.find_by_id(comment_id)
        if not comment:
            logger.warning(f"Comment not found - ID: {comment_id}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="댓글을 찾을 수 없습니다"
            )

        # 삭제된 댓글은 수정 불가
        if comment.is_deleted:
            logger.warning(f"Cannot update deleted comment - ID: {comment_id}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="삭제된 댓글은 수정할 수 없습니다"
            )

        # 권한 확인
        if not comment.can_modify(current_user.id, current_user.is_admin):
            logger.warning(
                f"Permission denied - User {current_user.id} tried to modify comment {comment_id}"
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="본인이 작성한 댓글만 수정할 수 있습니다"
            )

        # 수정할 필드 준비
        update_data = comment_data.model_dump(exclude_unset=True)

        if not update_data:
            logger.info(f"No fields to update - ID: {comment_id}")
            return comment

        # Repository 업데이트 호출
        updated_comment = await self.repo.update(comment_id, **update_data)

        logger.info(f"Comment updated successfully - ID: {comment_id}")
        return updated_comment

    async def delete_comment(
            self,
            comment_id: int,
            current_user: UserEntity,
            hard_delete: bool = False
    ) -> CommentEntity:
        """
        댓글 삭제

        비즈니스 규칙:
        - 본인이거나 관리자만 삭제 가능
        - 기본은 Soft Delete (내용을 "삭제된 댓글입니다"로 변경)
        - Hard Delete는 관리자 전용
        - 자식 댓글이 있어도 삭제 가능 (CASCADE)

        Args:
            comment_id: 댓글 ID
            current_user: 현재 인증된 사용자
            hard_delete: Hard Delete 여부

        Returns:
            CommentEntity: 삭제된 댓글 엔티티
        """
        logger.info(
            f"Deleting comment - ID: {comment_id}, by user: {current_user.id}, hard: {hard_delete}"
        )

        # 댓글 존재 확인
        comment = await self.repo.find_by_id(comment_id)
        if not comment:
            logger.warning(f"Comment not found - ID: {comment_id}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="댓글을 찾을 수 없습니다"
            )

        # 권한 확인
        if not comment.can_delete(current_user.id, current_user.is_admin):
            logger.warning(
                f"Permission denied - User {current_user.id} tried to delete comment {comment_id}"
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="본인이 작성한 댓글만 삭제할 수 있습니다"
            )

        # 삭제 수행
        if hard_delete and current_user.is_admin:
            # Hard Delete (관리자 전용, CASCADE로 자식 댓글도 삭제됨)
            success = await self.repo.delete(comment_id)
            if not success:
                logger.error(f"Failed to delete comment - ID: {comment_id}")
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="댓글 삭제 중 오류가 발생했습니다"
                )
            logger.info(f"Comment hard deleted - ID: {comment_id}")
        else:
            # Soft Delete (내용 변경 + is_deleted = 1)
            await self.repo.update(comment_id, content="삭제된 댓글입니다", is_deleted=True)
            logger.info(f"Comment soft deleted - ID: {comment_id}")

        return comment

    async def restore_comment(self, comment_id: int) -> CommentEntity:
        """
        삭제된 댓글 복구 (관리자 전용)

        Args:
            comment_id: 댓글 ID

        Returns:
            CommentEntity: 복구된 댓글 엔티티
        """
        logger.info(f"Restoring comment - ID: {comment_id}")

        # 댓글 존재 확인
        comment = await self.repo.find_by_id(comment_id)
        if not comment:
            logger.warning(f"Comment not found - ID: {comment_id}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="댓글을 찾을 수 없습니다"
            )

        # 이미 활성화된 경우
        if not comment.is_deleted:
            logger.info(f"Comment already active - ID: {comment_id}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="이미 활성화된 댓글입니다"
            )

        # 복구 수행
        success = await self.repo.restore(comment_id)
        if not success:
            logger.error(f"Failed to restore comment - ID: {comment_id}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="댓글 복구 중 오류가 발생했습니다"
            )

        restored_comment = await self.repo.find_by_id(comment_id)

        logger.info(f"Comment restored successfully - ID: {comment_id}")
        return restored_comment

    def _build_comment_tree(self, comments: List[CommentEntity]) -> List[CommentEntity]:
        """
        Flat 리스트를 Tree 구조로 변환

        Args:
            comments: Flat 댓글 리스트 (path 순서로 정렬되어 있어야 함)

        Returns:
            List[CommentEntity]: 최상위 댓글 리스트 (자식 댓글은 children에 포함)
        """
        # ID를 키로 하는 딕셔너리
        comment_dict: Dict[int, CommentEntity] = {}
        root_comments: List[CommentEntity] = []

        for comment in comments:
            # children 초기화
            comment.children = []
            comment_dict[comment.id] = comment

        # Tree 구조 생성
        for comment in comments:
            if comment.parent_id is None:
                # 최상위 댓글
                root_comments.append(comment)
            else:
                # 대댓글
                parent = comment_dict.get(comment.parent_id)
                if parent:
                    parent.add_child(comment)

        logger.debug(f"Built comment tree - root comments: {len(root_comments)}")
        return root_comments