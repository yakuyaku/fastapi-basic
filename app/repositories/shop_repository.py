"""
Shop repository implementation
app/repositories/shop_repository.py
"""
from typing import Optional, List
from datetime import datetime
from app.repositories.base import BaseRepository
from app.domain.entities.shop import ShopEntity, ShopType, ShopStatus
from app.core.logging import logger


class ShopRepository(BaseRepository):
    """Shop repository implementation"""

    def _to_entity(self, row: Optional[dict]) -> Optional[ShopEntity]:
        """데이터베이스 row를 ShopEntity로 변환"""
        if not row:
            return None

        return ShopEntity(
            shop_no=row.get('shop_no'),
            shop_name=row.get('shop_name', ''),
            shop_code=row.get('shop_code', ''),
            shop_type=ShopType(row.get('shop_type', 'MALL')),
            owner_user_no=row.get('owner_user_no', 0),
            business_number=row.get('business_number'),
            company_name=row.get('company_name'),
            contact_email=row.get('contact_email', ''),
            contact_phone=row.get('contact_phone', ''),
            contact_address=row.get('contact_address'),
            contact_address_detail=row.get('contact_address_detail'),
            zipcode=row.get('zipcode'),
            shop_status=ShopStatus(row.get('shop_status', 'ACTIVE')),
            use_display=row.get('use_display') == 'T',  # CHAR(1) → bool
            shop_description=row.get('shop_description'),
            logo_image_url=row.get('logo_image_url'),
            banner_image_url=row.get('banner_image_url'),
            created_at=row.get('created_at'),
            updated_at=row.get('updated_at'),
            deleted_at=row.get('deleted_at'),
            # JOIN용 운영자 정보
            owner_username=row.get('owner_username'),
            owner_email=row.get('owner_email')
        )

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
        query = """
                INSERT INTO shops (
                    shop_name, shop_code, shop_type, owner_user_no,
                    business_number, company_name,
                    contact_email, contact_phone, contact_address, contact_address_detail, zipcode,
                    shop_status, use_display,
                    shop_description, logo_image_url, banner_image_url
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, 'ACTIVE', %s, %s, %s, %s) \
                """
        shop_no = await self._execute(
            query,
            (
                shop_name, shop_code, shop_type.value, owner_user_no,
                business_number, company_name,
                contact_email, contact_phone, contact_address, contact_address_detail, zipcode,
                'T' if use_display else 'F',
                shop_description, logo_image_url, banner_image_url
            )
        )

        logger.info(
            f"Shop created - shop_no: {shop_no}, code: {shop_code}, owner: {owner_user_no}"
        )

        return await self.find_by_shop_no(shop_no)

    async def find_by_shop_no(self, shop_no: int) -> Optional[ShopEntity]:
        """상점 번호로 조회 (운영자 정보 포함)"""
        query = """
                SELECT
                    s.*,
                    u.username as owner_username,
                    u.email as owner_email
                FROM shops s
                         LEFT JOIN users u ON s.owner_user_no = u.id
                WHERE s.shop_no = %s \
                """
        row = await self._fetch_one(query, (shop_no,))
        return self._to_entity(row)

    async def find_by_shop_code(self, shop_code: str) -> Optional[ShopEntity]:
        """상점 코드로 조회"""
        query = """
                SELECT
                    s.*,
                    u.username as owner_username,
                    u.email as owner_email
                FROM shops s
                         LEFT JOIN users u ON s.owner_user_no = u.id
                WHERE s.shop_code = %s \
                """
        row = await self._fetch_one(query, (shop_code,))
        return self._to_entity(row)

    async def find_by_owner(self, owner_user_no: int) -> List[ShopEntity]:
        """운영자로 상점 목록 조회"""
        query = """
                SELECT s.*
                FROM shops s
                WHERE s.owner_user_no = %s AND s.deleted_at IS NULL
                ORDER BY s.created_at DESC \
                """
        rows = await self._fetch_all(query, (owner_user_no,))
        return [self._to_entity(row) for row in rows]

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
        conditions = []
        params = []

        # 삭제 여부
        if not include_deleted:
            conditions.append("s.deleted_at IS NULL")

        # 상점 유형
        if shop_type:
            conditions.append("s.shop_type = %s")
            params.append(shop_type.value)

        # 상점 상태
        if shop_status:
            conditions.append("s.shop_status = %s")
            params.append(shop_status.value)

        # 노출 여부
        if use_display is not None:
            conditions.append("s.use_display = %s")
            params.append('T' if use_display else 'F')

        # 검색 키워드 (상점명, 상점코드, 회사명)
        if search_keyword:
            conditions.append(
                "(s.shop_name LIKE %s OR s.shop_code LIKE %s OR s.company_name LIKE %s)"
            )
            keyword_pattern = f"%{search_keyword}%"
            params.extend([keyword_pattern, keyword_pattern, keyword_pattern])

        where_clause = " AND ".join(conditions) if conditions else "1=1"

        # 전체 개수 조회
        count_query = f"SELECT COUNT(*) as total FROM shops s WHERE {where_clause}"
        count_row = await self._fetch_one(count_query, tuple(params))
        total = count_row['total'] if count_row else 0

        # 목록 조회
        query = f"""
            SELECT 
                s.*,
                u.username as owner_username,
                u.email as owner_email
            FROM shops s
            LEFT JOIN users u ON s.owner_user_no = u.id
            WHERE {where_clause}
            ORDER BY s.created_at DESC
            LIMIT %s OFFSET %s
        """
        params.extend([limit, skip])
        rows = await self._fetch_all(query, tuple(params))

        shops = [self._to_entity(row) for row in rows]

        logger.debug(f"Found {len(shops)} shops (total: {total})")

        return shops, total

    async def update(self, shop_no: int, **fields) -> Optional[ShopEntity]:
        """상점 정보 업데이트"""
        if not fields:
            return await self.find_by_shop_no(shop_no)

        # UPDATE 쿼리 동적 생성
        update_fields = []
        params = []

        for field, value in fields.items():
            if field == 'shop_type' and isinstance(value, ShopType):
                update_fields.append(f"{field} = %s")
                params.append(value.value)
            elif field == 'shop_status' and isinstance(value, ShopStatus):
                update_fields.append(f"{field} = %s")
                params.append(value.value)
            elif field == 'use_display' and isinstance(value, bool):
                update_fields.append(f"{field} = %s")
                params.append('T' if value else 'F')
            else:
                update_fields.append(f"{field} = %s")
                params.append(value)

        params.append(shop_no)

        query = f"""
            UPDATE shops
            SET {', '.join(update_fields)}
            WHERE shop_no = %s
        """

        await self._execute(query, tuple(params))

        logger.info(f"Shop updated - shop_no: {shop_no}, fields: {list(fields.keys())}")

        return await self.find_by_shop_no(shop_no)

    async def soft_delete(self, shop_no: int) -> bool:
        """상점 소프트 삭제"""
        query = """
                UPDATE shops
                SET deleted_at = %s
                WHERE shop_no = %s \
                """
        rows_affected = await self._execute(query, (datetime.now(), shop_no))

        success = rows_affected > 0
        if success:
            logger.info(f"Shop soft deleted - shop_no: {shop_no}")

        return success

    async def restore(self, shop_no: int) -> bool:
        """삭제된 상점 복구"""
        query = """
                UPDATE shops
                SET deleted_at = NULL
                WHERE shop_no = %s \
                """
        rows_affected = await self._execute(query, (shop_no,))

        success = rows_affected > 0
        if success:
            logger.info(f"Shop restored - shop_no: {shop_no}")

        return success

    async def hard_delete(self, shop_no: int) -> bool:
        """상점 완전 삭제"""
        query = "DELETE FROM shops WHERE shop_no = %s"
        rows_affected = await self._execute(query, (shop_no,))

        success = rows_affected > 0
        if success:
            logger.info(f"Shop hard deleted - shop_no: {shop_no}")

        return success

    async def check_code_duplicate(
            self,
            shop_code: str,
            exclude_shop_no: Optional[int] = None
    ) -> bool:
        """상점 코드 중복 체크"""
        if exclude_shop_no:
            query = """
                    SELECT COUNT(*) as count
                    FROM shops
                    WHERE shop_code = %s AND shop_no != %s \
                    """
            row = await self._fetch_one(query, (shop_code, exclude_shop_no))
        else:
            query = """
                    SELECT COUNT(*) as count
                    FROM shops
                    WHERE shop_code = %s \
                    """
            row = await self._fetch_one(query, (shop_code,))

        return row['count'] > 0 if row else False

    async def update_status(self, shop_no: int, shop_status: ShopStatus) -> bool:
        """상점 상태 변경"""
        query = """
                UPDATE shops
                SET shop_status = %s
                WHERE shop_no = %s \
                """
        rows_affected = await self._execute(query, (shop_status.value, shop_no))

        success = rows_affected > 0
        if success:
            logger.info(f"Shop status updated - shop_no: {shop_no}, status: {shop_status.value}")

        return success

    async def toggle_display(self, shop_no: int) -> bool:
        """노출 여부 토글"""
        query = """
                UPDATE shops
                SET use_display = CASE WHEN use_display = 'T' THEN 'F' ELSE 'T' END
                WHERE shop_no = %s \
                """
        rows_affected = await self._execute(query, (shop_no,))

        success = rows_affected > 0
        if success:
            logger.info(f"Shop display toggled - shop_no: {shop_no}")

        return success