"""
Category repository protocol (interface)
app/domain/interfaces/category_repository.py
"""
from typing import Protocol, Optional, List
from app.domain.entities.category import CategoryEntity


class CategoryRepositoryProtocol(Protocol):
    """Category repository 인터페이스"""

    async def create(
            self,
            shop_no: int,
            category_name: str,
            parent_category_no: Optional[int] = None,
            category_depth: int = 1,
            category_path: str = "",
            full_category_name: Optional[str] = None,
            display_order: int = 0,
            use_display: bool = True,
            category_code: Optional[str] = None,
            category_description: Optional[str] = None,
            category_image_url: Optional[str] = None,
            hash_tags: Optional[List[str]] = None,
            meta_keywords: Optional[str] = None
    ) -> CategoryEntity:
        """카테고리 생성"""
        ...

    async def find_by_id(self, shop_no: int, category_no: int) -> Optional[CategoryEntity]:
        """카테고리 조회"""
        ...

    async def find_by_code(self, shop_no: int, category_code: str) -> Optional[CategoryEntity]:
        """카테고리 코드로 조회"""
        ...

    async def find_root_categories(
            self,
            shop_no: int,
            use_display: Optional[bool] = None,
            include_deleted: bool = False
    ) -> List[CategoryEntity]:
        """최상위 카테고리 목록 조회"""
        ...

    async def find_children(
            self,
            shop_no: int,
            parent_category_no: int,
            use_display: Optional[bool] = None,
            include_deleted: bool = False
    ) -> List[CategoryEntity]:
        """직속 자식 카테고리 목록 조회"""
        ...

    async def find_descendants(
            self,
            shop_no: int,
            category_no: int,
            include_self: bool = False,
            use_display: Optional[bool] = None,
            include_deleted: bool = False
    ) -> List[CategoryEntity]:
        """하위 카테고리 전체 조회 (category_path 활용)"""
        ...

    async def find_ancestors(
            self,
            shop_no: int,
            category_no: int,
            include_self: bool = False
    ) -> List[CategoryEntity]:
        """상위 카테고리 전체 조회 (breadcrumb용)"""
        ...

    async def find_all(
            self,
            shop_no: int,
            category_depth: Optional[int] = None,
            use_display: Optional[bool] = None,
            include_deleted: bool = False,
            search_keyword: Optional[str] = None
    ) -> List[CategoryEntity]:
        """카테고리 목록 조회 (필터링)"""
        ...

    async def find_by_depth(
            self,
            shop_no: int,
            depth: int,
            use_display: Optional[bool] = None
    ) -> List[CategoryEntity]:
        """특정 깊이의 카테고리만 조회"""
        ...

    async def update(self, shop_no: int, category_no: int, **fields) -> Optional[CategoryEntity]:
        """카테고리 정보 업데이트"""
        ...

    async def update_path(self, shop_no: int, category_no: int, new_path: str) -> bool:
        """카테고리 경로 업데이트"""
        ...

    async def update_full_name(
            self,
            shop_no: int,
            category_no: int,
            full_name: str
    ) -> bool:
        """전체 경로명 업데이트"""
        ...

    async def update_product_count(
            self,
            shop_no: int,
            category_no: int,
            count: int
    ) -> bool:
        """상품 수 업데이트 (비정규화 필드)"""
        ...

    async def increment_product_count(
            self,
            shop_no: int,
            category_no: int,
            delta: int = 1
    ) -> bool:
        """상품 수 증감"""
        ...

    async def soft_delete(self, shop_no: int, category_no: int) -> bool:
        """카테고리 소프트 삭제"""
        ...

    async def restore(self, shop_no: int, category_no: int) -> bool:
        """삭제된 카테고리 복구"""
        ...

    async def hard_delete(self, shop_no: int, category_no: int) -> bool:
        """카테고리 완전 삭제"""
        ...

    async def check_code_duplicate(
            self,
            shop_no: int,
            category_code: str,
            exclude_category_no: Optional[int] = None
    ) -> bool:
        """카테고리 코드 중복 체크"""
        ...

    async def toggle_display(self, shop_no: int, category_no: int) -> bool:
        """노출 여부 토글"""
        ...

    async def get_max_display_order(
            self,
            shop_no: int,
            parent_category_no: Optional[int] = None
    ) -> int:
        """같은 레벨에서 최대 display_order 조회"""
        ...

    async def has_children(self, shop_no: int, category_no: int) -> bool:
        """하위 카테고리 존재 여부"""
        ...

    async def count_descendants(self, shop_no: int, category_no: int) -> int:
        """하위 카테고리 개수"""
        ...