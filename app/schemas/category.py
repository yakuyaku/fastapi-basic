"""
Category schemas - Request/Response models
app/schemas/category.py
"""
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


class CategoryCreate(BaseModel):
    """카테고리 생성 요청"""
    category_name: str = Field(..., min_length=1, max_length=100)
    parent_category_no: Optional[int] = None
    display_order: Optional[int] = None
    use_display: bool = True
    category_code: Optional[str] = Field(None, max_length=50)
    category_description: Optional[str] = None
    category_image_url: Optional[str] = Field(None, max_length=500)
    hash_tags: Optional[List[str]] = None
    meta_keywords: Optional[str] = Field(None, max_length=255)


class CategoryUpdate(BaseModel):
    """카테고리 수정 요청"""
    category_name: Optional[str] = Field(None, min_length=1, max_length=100)
    display_order: Optional[int] = None
    use_display: Optional[bool] = None
    category_code: Optional[str] = Field(None, max_length=50)
    category_description: Optional[str] = None
    category_image_url: Optional[str] = Field(None, max_length=500)
    hash_tags: Optional[List[str]] = None
    meta_keywords: Optional[str] = Field(None, max_length=255)


class CategoryResponse(BaseModel):
    """카테고리 응답"""
    shop_no: int
    category_no: int
    parent_category_no: Optional[int]
    category_depth: int
    category_path: str
    category_name: str
    full_category_name: Optional[str]
    display_order: int
    use_display: bool
    category_code: Optional[str]
    category_description: Optional[str]
    category_image_url: Optional[str]
    product_count: int
    hash_tags: Optional[List[str]]
    meta_keywords: Optional[str]
    created_at: datetime
    updated_at: datetime
    deleted_at: Optional[datetime]
    shop_name: Optional[str]
    parent_category_name: Optional[str]

    class Config:
        from_attributes = True


class CategoryTreeResponse(CategoryResponse):
    """카테고리 Tree 구조 응답 (재귀)"""
    children: Optional[List['CategoryTreeResponse']] = None

    class Config:
        from_attributes = True


# Pydantic 순환 참조 해결
CategoryTreeResponse.model_rebuild()


class CategoryListResponse(BaseModel):
    """카테고리 목록 응답"""
    categories: List[CategoryResponse]
    total: int