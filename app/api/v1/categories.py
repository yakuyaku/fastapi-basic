"""
Category API endpoints (v1)
app/api/v1/categories.py
"""
from fastapi import APIRouter, Depends, Query, Path, status
from typing import Optional, List
from app.schemas.category import *
from app.services.category_service import CategoryService
from app.domain.entities.user import UserEntity
from app.api.dependencies import get_category_service, get_current_user, get_current_admin_user

router = APIRouter(prefix="/categories", tags=["categories"])


@router.post("/shops/{shop_no}", response_model=CategoryResponse, status_code=status.HTTP_201_CREATED)
async def create_category(
        shop_no: int = Path(..., description="상점 번호"),
        category_data: CategoryCreate = ...,
        current_user: UserEntity = Depends(get_current_user),
        category_service: CategoryService = Depends(get_category_service)
):
    """카테고리 생성 (인증 필요)"""
    category = await category_service.create_category(shop_no, category_data, current_user)
    return CategoryResponse.model_validate(category)


@router.get("/shops/{shop_no}/roots", response_model=List[CategoryResponse])
async def get_root_categories(
        shop_no: int = Path(..., description="상점 번호"),
        use_display: Optional[bool] = Query(True, description="노출 여부 필터"),
        category_service: CategoryService = Depends(get_category_service)
):
    """최상위 카테고리 목록 조회"""
    categories = await category_service.get_root_categories(shop_no, use_display)
    return [CategoryResponse.model_validate(cat) for cat in categories]


@router.get("/shops/{shop_no}/tree", response_model=List[CategoryTreeResponse])
async def get_category_tree(
        shop_no: int = Path(..., description="상점 번호"),
        parent_category_no: Optional[int] = Query(None, description="부모 카테고리 번호 (전체 트리: null)"),
        use_display: Optional[bool] = Query(True, description="노출 여부 필터"),
        category_service: CategoryService = Depends(get_category_service)
):
    """카테고리 Tree 구조 조회"""
    tree = await category_service.get_category_tree(shop_no, parent_category_no, use_display)
    return [CategoryTreeResponse.model_validate(cat) for cat in tree]


@router.get("/shops/{shop_no}/depth/{depth}", response_model=List[CategoryResponse])
async def get_categories_by_depth(
        shop_no: int = Path(..., description="상점 번호"),
        depth: int = Path(..., ge=1, le=4, description="카테고리 깊이 (1:대, 2:중, 3:소, 4:세)"),
        use_display: Optional[bool] = Query(True, description="노출 여부 필터"),
        category_service: CategoryService = Depends(get_category_service)
):
    """특정 깊이의 카테고리 목록 조회"""
    categories = await category_service.get_categories_by_depth(shop_no, depth, use_display)
    return [CategoryResponse.model_validate(cat) for cat in categories]


@router.get("/shops/{shop_no}/search", response_model=List[CategoryResponse])
async def search_categories(
        shop_no: int = Path(..., description="상점 번호"),
        keyword: str = Query(..., min_length=1, description="검색 키워드"),
        depth: Optional[int] = Query(None, ge=1, le=4, description="카테고리 깊이 필터"),
        use_display: Optional[bool] = Query(None, description="노출 여부 필터"),
        category_service: CategoryService = Depends(get_category_service)
):
    """카테고리 검색 (이름, 전체 경로명)"""
    categories = await category_service.search_categories(shop_no, keyword, depth, use_display)
    return [CategoryResponse.model_validate(cat) for cat in categories]


@router.get("/shops/{shop_no}/code/{category_code}", response_model=CategoryResponse)
async def get_category_by_code(
        shop_no: int = Path(..., description="상점 번호"),
        category_code: str = Path(..., description="카테고리 코드"),
        category_service: CategoryService = Depends(get_category_service)
):
    """카테고리 코드로 조회"""
    category = await category_service.get_category_by_code(shop_no, category_code)
    return CategoryResponse.model_validate(category)


@router.get("/shops/{shop_no}/{category_no}", response_model=CategoryResponse)
async def get_category(
        shop_no: int = Path(..., description="상점 번호"),
        category_no: int = Path(..., description="카테고리 번호"),
        category_service: CategoryService = Depends(get_category_service)
):
    """카테고리 단건 조회"""
    category = await category_service.get_category(shop_no, category_no)
    return CategoryResponse.model_validate(category)


@router.get("/shops/{shop_no}/{category_no}/children", response_model=List[CategoryResponse])
async def get_children(
        shop_no: int = Path(..., description="상점 번호"),
        category_no: int = Path(..., description="부모 카테고리 번호"),
        use_display: Optional[bool] = Query(True, description="노출 여부 필터"),
        category_service: CategoryService = Depends(get_category_service)
):
    """직속 자식 카테고리 목록 조회"""
    children = await category_service.get_children(shop_no, category_no, use_display)
    return [CategoryResponse.model_validate(cat) for cat in children]


@router.get("/shops/{shop_no}/{category_no}/descendants", response_model=List[CategoryResponse])
async def get_descendants(
        shop_no: int = Path(..., description="상점 번호"),
        category_no: int = Path(..., description="카테고리 번호"),
        include_self: bool = Query(False, description="본인 포함 여부"),
        use_display: Optional[bool] = Query(None, description="노출 여부 필터"),
        category_service: CategoryService = Depends(get_category_service)
):
    """하위 카테고리 전체 조회 (category_path 활용)"""
    descendants = await category_service.get_descendants(shop_no, category_no, include_self, use_display)
    return [CategoryResponse.model_validate(cat) for cat in descendants]


@router.get("/shops/{shop_no}/{category_no}/breadcrumb", response_model=List[CategoryResponse])
async def get_breadcrumb(
        shop_no: int = Path(..., description="상점 번호"),
        category_no: int = Path(..., description="카테고리 번호"),
        category_service: CategoryService = Depends(get_category_service)
):
    """Breadcrumb용 상위 카테고리 조회 (홈 > 의류 > 하의 > 청바지)"""
    breadcrumb = await category_service.get_breadcrumb(shop_no, category_no)
    return [CategoryResponse.model_validate(cat) for cat in breadcrumb]


@router.put("/shops/{shop_no}/{category_no}", response_model=CategoryResponse)
async def update_category(
        shop_no: int = Path(..., description="상점 번호"),
        category_no: int = Path(..., description="카테고리 번호"),
        category_data: CategoryUpdate = ...,
        current_user: UserEntity = Depends(get_current_user),
        category_service: CategoryService = Depends(get_category_service)
):
    """카테고리 수정 (인증 필요)"""
    category = await category_service.update_category(shop_no, category_no, category_data, current_user)
    return CategoryResponse.model_validate(category)


@router.delete("/shops/{shop_no}/{category_no}")
async def delete_category(
        shop_no: int = Path(..., description="상점 번호"),
        category_no: int = Path(..., description="카테고리 번호"),
        hard_delete: bool = Query(False, description="완전 삭제 여부 (기본: Soft Delete)"),
        current_user: UserEntity = Depends(get_current_admin_user),
        category_service: CategoryService = Depends(get_category_service)
):
    """카테고리 삭제 (관리자 전용)"""
    await category_service.delete_category(shop_no, category_no, current_user, hard_delete)
    return {"message": "카테고리가 삭제되었습니다"}


@router.patch("/shops/{shop_no}/{category_no}/restore", response_model=CategoryResponse)
async def restore_category(
        shop_no: int = Path(..., description="상점 번호"),
        category_no: int = Path(..., description="카테고리 번호"),
        current_user: UserEntity = Depends(get_current_admin_user),
        category_service: CategoryService = Depends(get_category_service)
):
    """카테고리 복구 (관리자 전용)"""
    category = await category_service.restore_category(shop_no, category_no)
    return CategoryResponse.model_validate(category)


@router.patch("/shops/{shop_no}/{category_no}/toggle-display", response_model=CategoryResponse)
async def toggle_display(
        shop_no: int = Path(..., description="상점 번호"),
        category_no: int = Path(..., description="카테고리 번호"),
        current_user: UserEntity = Depends(get_current_user),
        category_service: CategoryService = Depends(get_category_service)
):
    """노출 여부 토글 (인증 필요)"""
    category = await category_service.toggle_display(shop_no, category_no)
    return CategoryResponse.model_validate(category)