"""
Category domain entity
app/domain/entities/category.py
"""
from dataclasses import dataclass
from datetime import datetime
from typing import Optional, List
import json


@dataclass
class CategoryEntity:
    """
    Category domain entity (계층형 카테고리)

    멀티샵을 지원하며, category_path를 통한 계층 구조 관리
    """
    # PK (복합키)
    shop_no: int = 0
    category_no: Optional[int] = None

    # 계층 구조
    parent_category_no: Optional[int] = None
    category_depth: int = 1  # 1:대, 2:중, 3:소, 4:세
    category_path: str = ""  # "1/27/105/"

    # 정보 필드
    category_name: str = ""
    full_category_name: Optional[str] = None  # "의류 > 하의 > 청바지"

    # 설정
    display_order: int = 0
    use_display: bool = True  # T/F → bool

    # SEO & 관리
    category_code: Optional[str] = None
    category_description: Optional[str] = None
    category_image_url: Optional[str] = None

    # 통계 (비정규화)
    product_count: int = 0

    # 부가 정보
    hash_tags: Optional[List[str]] = None  # JSON → List
    meta_keywords: Optional[str] = None

    # 시스템
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    deleted_at: Optional[datetime] = None

    # JOIN용 (Optional)
    shop_name: Optional[str] = None
    parent_category_name: Optional[str] = None

    # Tree 구조용 (Optional)
    children: Optional[List['CategoryEntity']] = None

    def is_root(self) -> bool:
        """최상위 카테고리인지 확인"""
        return self.parent_category_no is None and self.category_depth == 1

    def is_leaf(self) -> bool:
        """하위 카테고리가 없는 말단 카테고리인지 확인"""
        return self.children is None or len(self.children) == 0

    def is_active(self) -> bool:
        """활성 카테고리인지 확인"""
        return self.use_display and self.deleted_at is None

    def is_deleted(self) -> bool:
        """삭제된 카테고리인지 확인"""
        return self.deleted_at is not None

    def get_depth_name(self) -> str:
        """깊이에 따른 카테고리 레벨 이름"""
        depth_names = {
            1: "대분류",
            2: "중분류",
            3: "소분류",
            4: "세분류"
        }
        return depth_names.get(self.category_depth, f"{self.category_depth}단계")

    def get_parent_path(self) -> Optional[str]:
        """
        부모의 path 추출

        예: "1/27/105/" → "1/27/"
        """
        if not self.category_path or self.is_root():
            return None

        parts = self.category_path.rstrip('/').split('/')
        if len(parts) <= 1:
            return None

        return '/'.join(parts[:-1]) + '/'

    def get_path_list(self) -> List[int]:
        """
        경로를 리스트로 반환

        예: "1/27/105/" → [1, 27, 105]
        """
        if not self.category_path:
            return []

        return [int(x) for x in self.category_path.strip('/').split('/') if x]

    def is_descendant_of(self, ancestor_category_no: int) -> bool:
        """
        특정 카테고리의 하위 카테고리인지 확인

        Args:
            ancestor_category_no: 조상 카테고리 번호

        Returns:
            bool: 하위 카테고리이면 True
        """
        return ancestor_category_no in self.get_path_list()

    def get_hash_tags_list(self) -> List[str]:
        """해시태그 JSON을 리스트로 반환"""
        if isinstance(self.hash_tags, list):
            return self.hash_tags
        if isinstance(self.hash_tags, str):
            try:
                return json.loads(self.hash_tags)
            except:
                return []
        return []

    def can_have_children(self) -> bool:
        """하위 카테고리를 가질 수 있는지 확인 (최대 4단계)"""
        return self.category_depth < 4

    def get_next_depth(self) -> int:
        """다음 단계의 깊이 반환"""
        return min(self.category_depth + 1, 4)

    def build_full_path(self, parent_path: Optional[str] = None) -> str:
        """
        전체 경로 생성

        Args:
            parent_path: 부모의 경로 (없으면 자동 추출)

        Returns:
            str: "1/27/105/" 형태의 경로
        """
        if parent_path:
            return f"{parent_path.rstrip('/')}/{self.category_no}/"
        elif self.parent_category_no:
            # 부모가 있으면 부모 경로 필요
            return f"{self.get_parent_path()}{self.category_no}/"
        else:
            # 최상위
            return f"{self.category_no}/"