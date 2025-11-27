"""
Shop schemas - Request/Response models
app/schemas/shop.py
"""
from pydantic import BaseModel, Field, field_validator, EmailStr
from typing import Optional
from datetime import datetime
from app.domain.entities.shop import ShopType, ShopStatus


class ShopCreate(BaseModel):
    """상점 생성 요청"""
    shop_name: str = Field(..., min_length=1, max_length=100)
    shop_code: str = Field(..., min_length=3, max_length=50, pattern=r'^[a-z0-9][a-z0-9_-]*[a-z0-9]$')
    shop_type: ShopType = ShopType.MALL
    business_number: Optional[str] = None
    company_name: Optional[str] = Field(None, max_length=100)
    contact_email: EmailStr
    contact_phone: str = Field(..., max_length=20)
    contact_address: Optional[str] = Field(None, max_length=255)
    contact_address_detail: Optional[str] = Field(None, max_length=255)
    zipcode: Optional[str] = Field(None, max_length=10)
    shop_description: Optional[str] = None
    logo_image_url: Optional[str] = Field(None, max_length=500)
    banner_image_url: Optional[str] = Field(None, max_length=500)
    use_display: bool = True


class ShopUpdate(BaseModel):
    """상점 수정 요청"""
    shop_name: Optional[str] = Field(None, min_length=1, max_length=100)
    shop_code: Optional[str] = Field(None, min_length=3, max_length=50)
    shop_type: Optional[ShopType] = None
    business_number: Optional[str] = None
    company_name: Optional[str] = Field(None, max_length=100)
    contact_email: Optional[EmailStr] = None
    contact_phone: Optional[str] = Field(None, max_length=20)
    contact_address: Optional[str] = Field(None, max_length=255)
    contact_address_detail: Optional[str] = Field(None, max_length=255)
    zipcode: Optional[str] = Field(None, max_length=10)
    shop_description: Optional[str] = None
    logo_image_url: Optional[str] = Field(None, max_length=500)
    banner_image_url: Optional[str] = Field(None, max_length=500)
    use_display: Optional[bool] = None


class ShopResponse(BaseModel):
    """상점 응답"""
    shop_no: int
    shop_name: str
    shop_code: str
    shop_type: ShopType
    owner_user_no: int
    business_number: Optional[str]
    company_name: Optional[str]
    contact_email: str
    contact_phone: str
    contact_address: Optional[str]
    contact_address_detail: Optional[str]
    zipcode: Optional[str]
    shop_status: ShopStatus
    use_display: bool
    shop_description: Optional[str]
    logo_image_url: Optional[str]
    banner_image_url: Optional[str]
    created_at: datetime
    updated_at: datetime
    deleted_at: Optional[datetime]
    owner_username: Optional[str]
    owner_email: Optional[str]

    class Config:
        from_attributes = True


class ShopListResponse(BaseModel):
    """상점 목록 응답"""
    shops: list[ShopResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


class ShopStatusUpdate(BaseModel):
    """상점 상태 변경 요청"""
    shop_status: ShopStatus