"""
Shop repository protocol (interface)
app/domain/interfaces/shop_repository.py
"""
from typing import Protocol, Optional, List
from app.domain.entities.shop import ShopEntity, ShopType, ShopStatus


class ShopRepositoryProtocol(Protocol):
    """Shop repository 인터페이스"""

    async def create(
            self,
            shop_name: str,
            shop_code: str,
            shop_type: ShopType,
            owner_user_no: int,
            contact_email: str,
            contact_phone: str,
            business_number: Optional[str] = None,
            company_name: Optional[str] = None,
            contact_address: Optional[str] = None,
            contact_address_detail: Optional[str] = None,
            zipcode: Optional[str] = None,
            shop_description: Optional[str] = None,
            logo_image_url: Optional[str] = None,
            banner_image_url: Optional[str] = None,
            use_display: bool = True
    ) -> ShopEntity:
        """상점 생성"""
        ...

    async def find_by_shop_no(self, shop_no: int) -> Optional[ShopEntity]:
        """상점 번호로 조회"""
        ...

    async def find_by_shop_code(self, shop_code: str) -> Optional[ShopEntity]:
        """상점 코드로 조회"""
        ...

    async def find_by_owner(self, owner_user_no: int) -> List[ShopEntity]:
        """운영자로 상점 목록 조회"""
        ...

    async def find_all(
            self,
            skip: int = 0,
            limit: int = 100,
            shop_type: Optional[ShopType] = None,
            shop_status: Optional[ShopStatus] = None,
            use_display: Optional[bool] = None,
            include_deleted: bool = False,
            search_keyword: Optional[str] = None
    ) -> tuple[List[ShopEntity], int]:
        """상점 목록 조회 (필터링, 페이징)"""
        ...

    async def update(self, shop_no: int, **fields) -> Optional[ShopEntity]:
        """상점 정보 업데이트"""
        ...

    async def soft_delete(self, shop_no: int) -> bool:
        """상점 소프트 삭제 (deleted_at 설정)"""
        ...

    async def restore(self, shop_no: int) -> bool:
        """삭제된 상점 복구"""
        ...

    async def hard_delete(self, shop_no: int) -> bool:
        """상점 완전 삭제"""
        ...

    async def check_code_duplicate(self, shop_code: str, exclude_shop_no: Optional[int] = None) -> bool:
        """상점 코드 중복 체크"""
        ...

    async def update_status(self, shop_no: int, shop_status: ShopStatus) -> bool:
        """상점 상태 변경"""
        ...

    async def toggle_display(self, shop_no: int) -> bool:
        """노출 여부 토글"""
        ...