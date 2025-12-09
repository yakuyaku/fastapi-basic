"""
Category repository implementation
app/repositories/category_repository.py
"""
from typing import Optional, List
from datetime import datetime
import json
from app.repositories.base import BaseRepository
from app.domain.entities.category import CategoryEntity
from app.core.logging import logger


class CategoryRepository(BaseRepository):
    """Category repository implementation"""

    def _to_entity(self, row: Optional[dict]) -> Optional[CategoryEntity]:
        """데이터베이스 row를 CategoryEntity로 변환"""
        if not row:
            return None

        # hash_tags JSON 처리
        hash_tags = None
        if row.get('hash_tags'):
            try:
                hash_tags = json.loads(row['hash_tags']) if isinstance(row['hash_tags'], str) else row['hash_tags']
            except:
                hash_tags = None

        return CategoryEntity(
            shop_no=row.get('shop_no', 0),
            category_no=row.get('category_no'),
            parent_category_no=row.get('parent_category_no'),
            category_depth=row.get('category_depth', 1),
            category_path=row.get('category_path', ''),
            category_name=row.get('category_name', ''),
            full_category_name=row.get('full_category_name'),
            display_order=row.get('display_order', 0),
            use_display=row.get('use_display') == 'T',
            category_code=row.get('category_code'),
            category_description=row.get('category_description'),
            category_image_url=row.get('category_image_url'),
            product_count=row.get('product_count', 0),
            hash_tags=hash_tags,
            meta_keywords=row.get('meta_keywords'),
            created_at=row.get('created_at'),
            updated_at=row.get('updated_at'),
            deleted_at=row.get('deleted_at'),
            shop_name=row.get('shop_name'),
            parent_category_name=row.get('parent_category_name')
        )

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
        hash_tags_json = json.dumps(hash_tags) if hash_tags else None

        query = """
                INSERT INTO shop_categories (
                    shop_no, parent_category_no, category_depth, category_path,
                    category_name, full_category_name, display_order, use_display,
                    category_code, category_description, category_image_url,
                    product_count, hash_tags, meta_keywords
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, 0, %s, %s) \
                """
        category_no = await self._execute(
            query,
            (
                shop_no, parent_category_no, category_depth, category_path,
                category_name, full_category_name, display_order, 'T' if use_display else 'F',
                category_code, category_description, category_image_url,
                hash_tags_json, meta_keywords
            )
        )

        logger.info(
            f"Category created - shop: {shop_no}, category: {category_no}, "
            f"name: {category_name}, depth: {category_depth}"
        )

        return await self.find_by_id(shop_no, category_no)

    async def find_by_id(self, shop_no: int, category_no: int) -> Optional[CategoryEntity]:
        """카테고리 조회"""
        query = """
                SELECT c.*, s.shop_name,
                       p.category_name as parent_category_name
                FROM shop_categories c
                         LEFT JOIN shops s ON c.shop_no = s.shop_no
                         LEFT JOIN shop_categories p ON c.shop_no = p.shop_no
                    AND c.parent_category_no = p.category_no
                WHERE c.shop_no = %s AND c.category_no = %s \
                """
        row = await self._fetch_one(query, (shop_no, category_no))
        return self._to_entity(row)

    async def find_by_code(self, shop_no: int, category_code: str) -> Optional[CategoryEntity]:
        """카테고리 코드로 조회"""
        query = """
                SELECT c.*, s.shop_name
                FROM shop_categories c
                         LEFT JOIN shops s ON c.shop_no = s.shop_no
                WHERE c.shop_no = %s AND c.category_code = %s \
                """
        row = await self._fetch_one(query, (shop_no, category_code))
        return self._to_entity(row)

    async def find_root_categories(
            self,
            shop_no: int,
            use_display: Optional[bool] = None,
            include_deleted: bool = False
    ) -> List[CategoryEntity]:
        """최상위 카테고리 목록 조회 (parent_category_no IS NULL)"""
        conditions = ["shop_no = %s", "parent_category_no IS NULL"]
        params = [shop_no]

        if not include_deleted:
            conditions.append("deleted_at IS NULL")

        if use_display is not None:
            conditions.append("use_display = %s")
            params.append('T' if use_display else 'F')

        query = f"""
            SELECT * FROM shop_categories
            WHERE {' AND '.join(conditions)}
            ORDER BY display_order ASC, category_no ASC
        """
        rows = await self._fetch_all(query, tuple(params))
        return [self._to_entity(row) for row in rows]

    async def find_children(
            self,
            shop_no: int,
            parent_category_no: int,
            use_display: Optional[bool] = None,
            include_deleted: bool = False
    ) -> List[CategoryEntity]:
        """직속 자식 카테고리 목록 조회"""
        conditions = ["shop_no = %s", "parent_category_no = %s"]
        params = [shop_no, parent_category_no]

        if not include_deleted:
            conditions.append("deleted_at IS NULL")

        if use_display is not None:
            conditions.append("use_display = %s")
            params.append('T' if use_display else 'F')

        query = f"""
            SELECT * FROM shop_categories
            WHERE {' AND '.join(conditions)}
            ORDER BY display_order ASC, category_no ASC
        """
        rows = await self._fetch_all(query, tuple(params))
        return [self._to_entity(row) for row in rows]

    async def find_descendants(
            self,
            shop_no: int,
            category_no: int,
            include_self: bool = False,
            use_display: Optional[bool] = None,
            include_deleted: bool = False
    ) -> List[CategoryEntity]:
        """하위 카테고리 전체 조회 (category_path LIKE 활용)"""
        # 먼저 부모의 path 조회
        parent = await self.find_by_id(shop_no, category_no)
        if not parent:
            return []

        conditions = ["shop_no = %s"]
        params = [shop_no]

        if include_self:
            conditions.append("category_path LIKE %s")
            params.append(f"{parent.category_path}%")
        else:
            # 자기 자신 제외
            conditions.append("category_path LIKE %s")
            conditions.append("category_no != %s")
            params.append(f"{parent.category_path}%")
            params.append(category_no)

        if not include_deleted:
            conditions.append("deleted_at IS NULL")

        if use_display is not None:
            conditions.append("use_display = %s")
            params.append('T' if use_display else 'F')

        query = f"""
            SELECT * FROM shop_categories
            WHERE {' AND '.join(conditions)}
            ORDER BY category_path ASC
        """
        rows = await self._fetch_all(query, tuple(params))
        return [self._to_entity(row) for row in rows]

    async def find_ancestors(
            self,
            shop_no: int,
            category_no: int,
            include_self: bool = False
    ) -> List[CategoryEntity]:
        """상위 카테고리 전체 조회 (breadcrumb용)"""
        category = await self.find_by_id(shop_no, category_no)
        if not category:
            return []

        path_ids = category.get_path_list()
        if not include_self and path_ids:
            path_ids = path_ids[:-1]

        if not path_ids:
            return []

        placeholders = ','.join(['%s'] * len(path_ids))
        query = f"""
            SELECT * FROM shop_categories
            WHERE shop_no = %s AND category_no IN ({placeholders})
            ORDER BY category_depth ASC
        """
        rows = await self._fetch_all(query, tuple([shop_no] + path_ids))
        return [self._to_entity(row) for row in rows]

    async def find_all(
            self,
            shop_no: int,
            category_depth: Optional[int] = None,
            use_display: Optional[bool] = None,
            include_deleted: bool = False,
            search_keyword: Optional[str] = None
    ) -> List[CategoryEntity]:
        """카테고리 목록 조회"""
        conditions = ["shop_no = %s"]
        params = [shop_no]

        if not include_deleted:
            conditions.append("deleted_at IS NULL")

        if category_depth is not None:
            conditions.append("category_depth = %s")
            params.append(category_depth)

        if use_display is not None:
            conditions.append("use_display = %s")
            params.append('T' if use_display else 'F')

        if search_keyword:
            conditions.append("(category_name LIKE %s OR full_category_name LIKE %s)")
            keyword_pattern = f"%{search_keyword}%"
            params.extend([keyword_pattern, keyword_pattern])

        query = f"""
            SELECT * FROM shop_categories
            WHERE {' AND '.join(conditions)}
            ORDER BY category_path ASC
        """
        rows = await self._fetch_all(query, tuple(params))
        return [self._to_entity(row) for row in rows]

    async def find_by_depth(
            self,
            shop_no: int,
            depth: int,
            use_display: Optional[bool] = None
    ) -> List[CategoryEntity]:
        """특정 깊이의 카테고리만 조회"""
        conditions = ["shop_no = %s", "category_depth = %s", "deleted_at IS NULL"]
        params = [shop_no, depth]

        if use_display is not None:
            conditions.append("use_display = %s")
            params.append('T' if use_display else 'F')

        query = f"""
            SELECT * FROM shop_categories
            WHERE {' AND '.join(conditions)}
            ORDER BY display_order ASC, category_no ASC
        """
        rows = await self._fetch_all(query, tuple(params))
        return [self._to_entity(row) for row in rows]

    async def update(self, shop_no: int, category_no: int, **fields) -> Optional[CategoryEntity]:
        """카테고리 정보 업데이트"""
        if not fields:
            return await self.find_by_id(shop_no, category_no)

        update_fields = []
        params = []

        for field, value in fields.items():
            if field == 'use_display' and isinstance(value, bool):
                update_fields.append(f"{field} = %s")
                params.append('T' if value else 'F')
            elif field == 'hash_tags' and isinstance(value, list):
                update_fields.append(f"{field} = %s")
                params.append(json.dumps(value))
            else:
                update_fields.append(f"{field} = %s")
                params.append(value)

        params.extend([shop_no, category_no])

        query = f"""
            UPDATE shop_categories
            SET {', '.join(update_fields)}
            WHERE shop_no = %s AND category_no = %s
        """
        await self._execute(query, tuple(params))

        logger.info(f"Category updated - shop: {shop_no}, category: {category_no}")
        return await self.find_by_id(shop_no, category_no)

    async def update_path(self, shop_no: int, category_no: int, new_path: str) -> bool:
        """카테고리 경로 업데이트"""
        query = """
                UPDATE shop_categories
                SET category_path = %s
                WHERE shop_no = %s AND category_no = %s \
                """
        rows_affected = await self._execute(query, (new_path, shop_no, category_no))
        return rows_affected > 0

    async def update_full_name(self, shop_no: int, category_no: int, full_name: str) -> bool:
        """전체 경로명 업데이트"""
        query = """
                UPDATE shop_categories
                SET full_category_name = %s
                WHERE shop_no = %s AND category_no = %s \
                """
        rows_affected = await self._execute(query, (full_name, shop_no, category_no))
        return rows_affected > 0

    async def update_product_count(self, shop_no: int, category_no: int, count: int) -> bool:
        """상품 수 업데이트"""
        query = """
                UPDATE shop_categories
                SET product_count = %s
                WHERE shop_no = %s AND category_no = %s \
                """
        rows_affected = await self._execute(query, (count, shop_no, category_no))
        return rows_affected > 0

    async def increment_product_count(self, shop_no: int, category_no: int, delta: int = 1) -> bool:
        """상품 수 증감"""
        query = """
                UPDATE shop_categories
                SET product_count = product_count + %s
                WHERE shop_no = %s AND category_no = %s \
                """
        rows_affected = await self._execute(query, (delta, shop_no, category_no))
        return rows_affected > 0

    async def soft_delete(self, shop_no: int, category_no: int) -> bool:
        """카테고리 소프트 삭제"""
        query = """
                UPDATE shop_categories
                SET deleted_at = %s
                WHERE shop_no = %s AND category_no = %s \
                """
        rows_affected = await self._execute(query, (datetime.now(), shop_no, category_no))

        if rows_affected > 0:
            logger.info(f"Category soft deleted - shop: {shop_no}, category: {category_no}")

        return rows_affected > 0

    async def restore(self, shop_no: int, category_no: int) -> bool:
        """삭제된 카테고리 복구"""
        query = """
                UPDATE shop_categories
                SET deleted_at = NULL
                WHERE shop_no = %s AND category_no = %s \
                """
        rows_affected = await self._execute(query, (shop_no, category_no))

        if rows_affected > 0:
            logger.info(f"Category restored - shop: {shop_no}, category: {category_no}")

        return rows_affected > 0

    async def hard_delete(self, shop_no: int, category_no: int) -> bool:
        """카테고리 완전 삭제"""
        query = "DELETE FROM shop_categories WHERE shop_no = %s AND category_no = %s"
        rows_affected = await self._execute(query, (shop_no, category_no))

        if rows_affected > 0:
            logger.info(f"Category hard deleted - shop: {shop_no}, category: {category_no}")

        return rows_affected > 0

    async def check_code_duplicate(
            self,
            shop_no: int,
            category_code: str,
            exclude_category_no: Optional[int] = None
    ) -> bool:
        """카테고리 코드 중복 체크"""
        if exclude_category_no:
            query = """
                    SELECT COUNT(*) as count
                    FROM shop_categories
                    WHERE shop_no = %s AND category_code = %s AND category_no != %s \
                    """
            row = await self._fetch_one(query, (shop_no, category_code, exclude_category_no))
        else:
            query = """
                    SELECT COUNT(*) as count
                    FROM shop_categories
                    WHERE shop_no = %s AND category_code = %s \
                    """
            row = await self._fetch_one(query, (shop_no, category_code))

        return row['count'] > 0 if row else False

    async def toggle_display(self, shop_no: int, category_no: int) -> bool:
        """노출 여부 토글"""
        query = """
                UPDATE shop_categories
                SET use_display = CASE WHEN use_display = 'T' THEN 'F' ELSE 'T' END
                WHERE shop_no = %s AND category_no = %s \
                """
        rows_affected = await self._execute(query, (shop_no, category_no))
        return rows_affected > 0

    async def get_max_display_order(
            self,
            shop_no: int,
            parent_category_no: Optional[int] = None
    ) -> int:
        """같은 레벨에서 최대 display_order 조회"""
        if parent_category_no:
            query = """
                    SELECT COALESCE(MAX(display_order), 0) as max_order
                    FROM shop_categories
                    WHERE shop_no = %s AND parent_category_no = %s \
                    """
            row = await self._fetch_one(query, (shop_no, parent_category_no))
        else:
            query = """
                    SELECT COALESCE(MAX(display_order), 0) as max_order
                    FROM shop_categories
                    WHERE shop_no = %s AND parent_category_no IS NULL \
                    """
            row = await self._fetch_one(query, (shop_no,))

        return row['max_order'] if row else 0

    async def has_children(self, shop_no: int, category_no: int) -> bool:
        """하위 카테고리 존재 여부"""
        query = """
                SELECT COUNT(*) as count
                FROM shop_categories
                WHERE shop_no = %s AND parent_category_no = %s \
                """
        row = await self._fetch_one(query, (shop_no, category_no))
        return row['count'] > 0 if row else False

    async def count_descendants(self, shop_no: int, category_no: int) -> int:
        """하위 카테고리 개수"""
        category = await self.find_by_id(shop_no, category_no)
        if not category:
            return 0

        query = """
                SELECT COUNT(*) as count
                FROM shop_categories
                WHERE shop_no = %s AND category_path LIKE %s AND category_no != %s \
                """
        row = await self._fetch_one(query, (shop_no, f"{category.category_path}%", category_no))
        return row['count'] if row else 0