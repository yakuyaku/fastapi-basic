"""
Category service - Business logic for hierarchical categories
app/services/category_service.py
"""
import re
from typing import Optional, List, Dict
from fastapi import HTTPException, status
from app.domain.entities.category import CategoryEntity
from app.domain.entities.user import UserEntity
from app.domain.interfaces.category_repository import CategoryRepositoryProtocol
from app.schemas.category import CategoryCreate, CategoryUpdate
from app.core.logging import logger


class CategoryService:
    """Category service - 계층형 카테고리 비즈니스 로직"""

    MAX_DEPTH = 4  # 최대 깊이

    def __init__(self, category_repository: CategoryRepositoryProtocol):
        self.repo = category_repository

    def _validate_category_code(self, code: str) -> None:
        """카테고리 코드 형식 검증"""
        pattern = r'^[a-z0-9][a-z0-9_-]{0,48}[a-z0-9]$'
        if not re.match(pattern, code):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="카테고리 코드는 영문 소문자, 숫자, 하이픈, 언더스코어만 가능합니다 (2-50자)"
            )

    def _build_full_name(self, ancestors: List[CategoryEntity], current_name: str) -> str:
        """전체 경로명 생성 (예: 의류 > 하의 > 청바지)"""
        names = [cat.category_name for cat in ancestors]
        names.append(current_name)
        return " > ".join(names)

    def _build_category_tree(
            self,
            categories: List[CategoryEntity],
            parent_id: Optional[int] = None
    ) -> List[CategoryEntity]:
        """Flat 리스트를 Tree 구조로 변환"""
        tree = []
        for cat in categories:
            if cat.parent_category_no == parent_id:
                cat.children = self._build_category_tree(categories, cat.category_no)
                tree.append(cat)
        return tree

    async def create_category(
            self,
            shop_no: int,
            category_data: CategoryCreate,
            current_user: UserEntity
    ) -> CategoryEntity:
        """카테고리 생성"""
        logger.info(f"Creating category - shop: {shop_no}, name: {category_data.category_name}")

        # 카테고리 코드 검증 (입력된 경우)
        if category_data.category_code:
            self._validate_category_code(category_data.category_code)

            # 중복 확인
            is_duplicate = await self.repo.check_code_duplicate(shop_no, category_data.category_code)
            if is_duplicate:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"이미 사용 중인 카테고리 코드입니다: {category_data.category_code}"
                )

        # 부모 카테고리 확인
        parent_category = None
        category_depth = 1
        category_path = "0"  # 임시 경로
        full_category_name = category_data.category_name

        if category_data.parent_category_no:
            parent_category = await self.repo.find_by_id(shop_no, category_data.parent_category_no)

            if not parent_category:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="부모 카테고리를 찾을 수 없습니다"
                )

            if parent_category.is_deleted():
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="삭제된 카테고리에는 하위 카테고리를 생성할 수 없습니다"
                )

            if not parent_category.can_have_children():
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"카테고리는 최대 {self.MAX_DEPTH}단계까지만 생성할 수 있습니다"
                )

            category_depth = parent_category.get_next_depth()
            category_path = f"{parent_category.category_path}0/"  # 임시

            # 전체 경로명 생성
            ancestors = await self.repo.find_ancestors(shop_no, parent_category.category_no, include_self=True)
            full_category_name = self._build_full_name(ancestors, category_data.category_name)

        # display_order 자동 계산
        max_order = await self.repo.get_max_display_order(shop_no, category_data.parent_category_no)
        display_order = category_data.display_order if category_data.display_order is not None else max_order + 1

        # 카테고리 생성
        category = await self.repo.create(
            shop_no=shop_no,
            category_name=category_data.category_name,
            parent_category_no=category_data.parent_category_no,
            category_depth=category_depth,
            category_path=category_path,
            full_category_name=full_category_name,
            display_order=display_order,
            use_display=category_data.use_display,
            category_code=category_data.category_code,
            category_description=category_data.category_description,
            category_image_url=category_data.category_image_url,
            hash_tags=category_data.hash_tags,
            meta_keywords=category_data.meta_keywords
        )

        # 실제 경로 업데이트
        if parent_category:
            new_path = f"{parent_category.category_path}{category.category_no}/"
        else:
            new_path = f"{category.category_no}/"

        await self.repo.update_path(shop_no, category.category_no, new_path)
        category.category_path = new_path

        logger.info(f"Category created - shop: {shop_no}, category: {category.category_no}, path: {new_path}")
        return category

    async def get_category(self, shop_no: int, category_no: int) -> CategoryEntity:
        """카테고리 단건 조회"""
        category = await self.repo.find_by_id(shop_no, category_no)

        if not category:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="카테고리를 찾을 수 없습니다"
            )

        return category

    async def get_category_by_code(self, shop_no: int, category_code: str) -> CategoryEntity:
        """카테고리 코드로 조회"""
        category = await self.repo.find_by_code(shop_no, category_code)

        if not category:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"카테고리를 찾을 수 없습니다: {category_code}"
            )

        return category

    async def get_root_categories(
            self,
            shop_no: int,
            use_display: Optional[bool] = True
    ) -> List[CategoryEntity]:
        """최상위 카테고리 목록 조회"""
        return await self.repo.find_root_categories(shop_no, use_display=use_display)

    async def get_children(
            self,
            shop_no: int,
            parent_category_no: int,
            use_display: Optional[bool] = True
    ) -> List[CategoryEntity]:
        """직속 자식 카테고리 목록 조회"""
        return await self.repo.find_children(shop_no, parent_category_no, use_display=use_display)

    async def get_descendants(
            self,
            shop_no: int,
            category_no: int,
            include_self: bool = False,
            use_display: Optional[bool] = None
    ) -> List[CategoryEntity]:
        """하위 카테고리 전체 조회"""
        return await self.repo.find_descendants(
            shop_no, category_no, include_self=include_self, use_display=use_display
        )

    async def get_category_tree(
            self,
            shop_no: int,
            parent_category_no: Optional[int] = None,
            use_display: Optional[bool] = True
    ) -> List[CategoryEntity]:
        """카테고리 Tree 구조 조회"""
        if parent_category_no:
            # 특정 카테고리 하위 트리
            categories = await self.repo.find_descendants(
                shop_no, parent_category_no, include_self=True, use_display=use_display
            )
        else:
            # 전체 트리
            categories = await self.repo.find_all(shop_no, use_display=use_display)

        return self._build_category_tree(categories, parent_category_no)

    async def get_breadcrumb(self, shop_no: int, category_no: int) -> List[CategoryEntity]:
        """Breadcrumb용 상위 카테고리 조회"""
        return await self.repo.find_ancestors(shop_no, category_no, include_self=True)

    async def get_categories_by_depth(
            self,
            shop_no: int,
            depth: int,
            use_display: Optional[bool] = True
    ) -> List[CategoryEntity]:
        """특정 깊이의 카테고리 목록 조회"""
        if depth < 1 or depth > self.MAX_DEPTH:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"카테고리 깊이는 1-{self.MAX_DEPTH} 사이여야 합니다"
            )

        return await self.repo.find_by_depth(shop_no, depth, use_display=use_display)

    async def search_categories(
            self,
            shop_no: int,
            keyword: str,
            category_depth: Optional[int] = None,
            use_display: Optional[bool] = None
    ) -> List[CategoryEntity]:
        """카테고리 검색"""
        return await self.repo.find_all(
            shop_no=shop_no,
            category_depth=category_depth,
            use_display=use_display,
            search_keyword=keyword
        )

    async def update_category(
            self,
            shop_no: int,
            category_no: int,
            category_data: CategoryUpdate,
            current_user: UserEntity
    ) -> CategoryEntity:
        """카테고리 정보 수정"""
        logger.info(f"Updating category - shop: {shop_no}, category: {category_no}")

        # 카테고리 존재 확인
        category = await self.repo.find_by_id(shop_no, category_no)
        if not category:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="카테고리를 찾을 수 없습니다"
            )

        if category.is_deleted():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="삭제된 카테고리는 수정할 수 없습니다"
            )

        # 수정할 필드 준비
        update_data = category_data.model_dump(exclude_unset=True)

        if not update_data:
            return category

        # 카테고리 코드 변경 시 검증
        if 'category_code' in update_data and update_data['category_code']:
            self._validate_category_code(update_data['category_code'])

            is_duplicate = await self.repo.check_code_duplicate(
                shop_no, update_data['category_code'], category_no
            )
            if is_duplicate:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"이미 사용 중인 카테고리 코드입니다: {update_data['category_code']}"
                )

        # 카테고리명 변경 시 full_category_name도 업데이트
        if 'category_name' in update_data:
            ancestors = await self.repo.find_ancestors(shop_no, category_no, include_self=False)
            new_full_name = self._build_full_name(ancestors, update_data['category_name'])
            update_data['full_category_name'] = new_full_name

        updated_category = await self.repo.update(shop_no, category_no, **update_data)

        logger.info(f"Category updated - shop: {shop_no}, category: {category_no}")
        return updated_category

    async def delete_category(
            self,
            shop_no: int,
            category_no: int,
            current_user: UserEntity,
            hard_delete: bool = False
    ) -> CategoryEntity:
        """카테고리 삭제"""
        logger.info(f"Deleting category - shop: {shop_no}, category: {category_no}, hard: {hard_delete}")

        # 카테고리 존재 확인
        category = await self.repo.find_by_id(shop_no, category_no)
        if not category:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="카테고리를 찾을 수 없습니다"
            )

        # 하위 카테고리 존재 확인
        has_children = await self.repo.has_children(shop_no, category_no)
        if has_children:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="하위 카테고리가 있는 카테고리는 삭제할 수 없습니다. 먼저 하위 카테고리를 삭제하세요."
            )

        # 상품이 등록된 경우 확인 (product_count > 0)
        if category.product_count > 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"상품이 등록된 카테고리는 삭제할 수 없습니다 (상품 수: {category.product_count})"
            )

        # 삭제 수행
        if hard_delete:
            success = await self.repo.hard_delete(shop_no, category_no)
        else:
            success = await self.repo.soft_delete(shop_no, category_no)

        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="카테고리 삭제 중 오류가 발생했습니다"
            )

        logger.info(f"Category deleted - shop: {shop_no}, category: {category_no}")
        return category

    async def restore_category(self, shop_no: int, category_no: int) -> CategoryEntity:
        """삭제된 카테고리 복구"""
        category = await self.repo.find_by_id(shop_no, category_no)
        if not category:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="카테고리를 찾을 수 없습니다"
            )

        if not category.is_deleted():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="이미 활성화된 카테고리입니다"
            )

        success = await self.repo.restore(shop_no, category_no)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="카테고리 복구 중 오류가 발생했습니다"
            )

        return await self.repo.find_by_id(shop_no, category_no)

    async def toggle_display(self, shop_no: int, category_no: int) -> CategoryEntity:
        """노출 여부 토글"""
        category = await self.repo.find_by_id(shop_no, category_no)
        if not category:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="카테고리를 찾을 수 없습니다"
            )

        success = await self.repo.toggle_display(shop_no, category_no)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="노출 설정 변경 중 오류가 발생했습니다"
            )

        return await self.repo.find_by_id(shop_no, category_no)

    async def update_product_count(
            self,
            shop_no: int,
            category_no: int,
            delta: int
    ) -> bool:
        """
        상품 수 업데이트 (비정규화 필드)

        Args:
            shop_no: 상점 번호
            category_no: 카테고리 번호
            delta: 증감량 (+1: 상품 추가, -1: 상품 삭제)
        """
        return await self.repo.increment_product_count(shop_no, category_no, delta)