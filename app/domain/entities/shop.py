"""
Shop domain entity
app/domain/entities/shop.py
"""
from dataclasses import dataclass
from datetime import datetime
from typing import Optional
from enum import Enum


class ShopType(str, Enum):
    """상점 유형"""
    MALL = "MALL"          # 종합몰
    BRAND = "BRAND"        # 브랜드샵
    PERSONAL = "PERSONAL"  # 개인샵


class ShopStatus(str, Enum):
    """상점 상태"""
    ACTIVE = "ACTIVE"          # 활성
    INACTIVE = "INACTIVE"      # 비활성
    SUSPENDED = "SUSPENDED"    # 정지


@dataclass
class ShopEntity:
    """
    Shop domain entity (순수 비즈니스 객체)
    
    쇼핑몰의 상점 정보를 표현하는 엔티티입니다.
    """
    # PK
    shop_no: Optional[int] = None

    # 기본 정보
    shop_name: str = ""
    shop_code: str = ""
    shop_type: ShopType = ShopType.MALL

    # 운영자 정보
    owner_user_no: int = 0
    business_number: Optional[str] = None
    company_name: Optional[str] = None

    # 연락처
    contact_email: str = ""
    contact_phone: str = ""
    contact_address: Optional[str] = None
    contact_address_detail: Optional[str] = None
    zipcode: Optional[str] = None

    # 설정
    shop_status: ShopStatus = ShopStatus.ACTIVE
    use_display: bool = True  # T/F → bool 변환

    # 부가 정보
    shop_description: Optional[str] = None
    logo_image_url: Optional[str] = None
    banner_image_url: Optional[str] = None

    # 시스템 필드
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    deleted_at: Optional[datetime] = None

    # JOIN용 운영자 정보 (Optional)
    owner_username: Optional[str] = None
    owner_email: Optional[str] = None

    def is_active(self) -> bool:
        """활성 상점인지 확인"""
        return (
                self.shop_status == ShopStatus.ACTIVE
                and self.use_display
                and self.deleted_at is None
        )

    def is_deleted(self) -> bool:
        """삭제된 상점인지 확인 (Soft Delete)"""
        return self.deleted_at is not None

    def is_suspended(self) -> bool:
        """정지된 상점인지 확인"""
        return self.shop_status == ShopStatus.SUSPENDED

    def can_modify(self, user_no: int, is_admin: bool) -> bool:
        """
        상점을 수정할 수 있는 권한이 있는지 확인
        
        Args:
            user_no: 현재 사용자 번호
            is_admin: 관리자 여부
            
        Returns:
            bool: 관리자이거나 운영자 본인인 경우 True
        """
        return is_admin or self.owner_user_no == user_no

    def can_delete(self, user_no: int, is_admin: bool) -> bool:
        """
        상점을 삭제할 수 있는 권한이 있는지 확인
        
        Args:
            user_no: 현재 사용자 번호
            is_admin: 관리자 여부
            
        Returns:
            bool: 관리자만 삭제 가능
        """
        # 실제 상점 삭제는 관리자만 가능 (운영자는 INACTIVE만 가능)
        return is_admin

    def can_display(self) -> bool:
        """노출 가능한 상점인지 확인"""
        return (
                self.shop_status == ShopStatus.ACTIVE
                and self.use_display
                and self.deleted_at is None
        )

    def has_business_info(self) -> bool:
        """사업자 정보가 등록되어 있는지 확인"""
        return bool(self.business_number and self.company_name)