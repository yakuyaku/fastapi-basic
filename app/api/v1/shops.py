"""
Shop API endpoints (v1)
app/api/v1/shops.py
"""
from fastapi import APIRouter, Depends, Query, status
from typing import Optional
from app.schemas.shop import *
from app.services.shop_service import ShopService
from app.domain.entities.user import UserEntity
from app.domain.entities.shop import ShopType, ShopStatus
from app.api.dependencies import get_shop_service, get_current_user, get_current_admin_user
import math

router = APIRouter(prefix="/shops", tags=["shops"])

@router.post("/", response_model=ShopResponse, status_code=status.HTTP_201_CREATED)
async def create_shop(
        shop_data: ShopCreate,
        current_user: UserEntity = Depends(get_current_user),
        shop_service: ShopService = Depends(get_shop_service)
):
    """상점 생성 (인증 필요)"""
    shop = await shop_service.create_shop(shop_data, current_user)
    return ShopResponse.model_validate(shop)

@router.get("/", response_model=ShopListResponse)
async def get_shops(
        page: int = Query(1, ge=1),
        page_size: int = Query(20, ge=1, le=100),
        shop_type: Optional[ShopType] = None,
        shop_status: Optional[ShopStatus] = None,
        use_display: Optional[bool] = None,
        search: Optional[str] = None,
        shop_service: ShopService = Depends(get_shop_service)
):
    """상점 목록 조회"""
    shops, total = await shop_service.get_shops(
        page=page,
        page_size=page_size,
        shop_type=shop_type,
        shop_status=shop_status,
        use_display=use_display,
        search_keyword=search
    )
    return ShopListResponse(
        shops=[ShopResponse.model_validate(shop) for shop in shops],
        total=total,
        page=page,
        page_size=page_size,
        total_pages=math.ceil(total / page_size) if total > 0 else 0
    )

@router.get("/my", response_model=list[ShopResponse])
async def get_my_shops(
        current_user: UserEntity = Depends(get_current_user),
        shop_service: ShopService = Depends(get_shop_service)
):
    """내 상점 목록 조회 (인증 필요)"""
    shops = await shop_service.get_my_shops(current_user)
    return [ShopResponse.model_validate(shop) for shop in shops]

@router.get("/code/{shop_code}", response_model=ShopResponse)
async def get_shop_by_code(
        shop_code: str,
        shop_service: ShopService = Depends(get_shop_service)
):
    """상점 코드로 조회"""
    shop = await shop_service.get_shop_by_code(shop_code)
    return ShopResponse.model_validate(shop)

@router.get("/{shop_no}", response_model=ShopResponse)
async def get_shop(
        shop_no: int,
        shop_service: ShopService = Depends(get_shop_service)
):
    """상점 단건 조회"""
    shop = await shop_service.get_shop(shop_no)
    return ShopResponse.model_validate(shop)

@router.put("/{shop_no}", response_model=ShopResponse)
async def update_shop(
        shop_no: int,
        shop_data: ShopUpdate,
        current_user: UserEntity = Depends(get_current_user),
        shop_service: ShopService = Depends(get_shop_service)
):
    """상점 수정 (운영자/관리자)"""
    shop = await shop_service.update_shop(shop_no, shop_data, current_user)
    return ShopResponse.model_validate(shop)

@router.delete("/{shop_no}")
async def delete_shop(
        shop_no: int,
        current_user: UserEntity = Depends(get_current_admin_user),
        shop_service: ShopService = Depends(get_shop_service),
        hard_delete: bool = Query(False)
):
    """상점 삭제 (관리자 전용)"""
    await shop_service.delete_shop(shop_no, current_user, hard_delete)
    return {"message": "상점이 삭제되었습니다"}

@router.patch("/{shop_no}/restore", response_model=ShopResponse)
async def restore_shop(
        shop_no: int,
        current_user: UserEntity = Depends(get_current_admin_user),
        shop_service: ShopService = Depends(get_shop_service)
):
    """상점 복구 (관리자 전용)"""
    shop = await shop_service.restore_shop(shop_no)
    return ShopResponse.model_validate(shop)

@router.patch("/{shop_no}/status", response_model=ShopResponse)
async def update_shop_status(
        shop_no: int,
        status_data: ShopStatusUpdate,
        current_user: UserEntity = Depends(get_current_user),
        shop_service: ShopService = Depends(get_shop_service)
):
    """상점 상태 변경 (운영자/관리자, SUSPENDED는 관리자만)"""
    shop = await shop_service.update_shop_status(shop_no, status_data.shop_status, current_user)
    return ShopResponse.model_validate(shop)

@router.patch("/{shop_no}/toggle-display", response_model=ShopResponse)
async def toggle_display(
        shop_no: int,
        current_user: UserEntity = Depends(get_current_user),
        shop_service: ShopService = Depends(get_shop_service)
):
    """노출 여부 토글 (운영자/관리자)"""
    shop = await shop_service.toggle_shop_display(shop_no, current_user)
    return ShopResponse.model_validate(shop)