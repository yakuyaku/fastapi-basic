"""
Shop service - Business logic for shop operations
app/services/shop_service.py
"""
import re
from typing import Optional, List
from fastapi import HTTPException, status
from app.domain.entities.shop import ShopEntity, ShopType, ShopStatus
from app.domain.entities.user import UserEntity
from app.domain.interfaces.shop_repository import ShopRepositoryProtocol
from app.schemas.shop import ShopCreate, ShopUpdate
from app.core.logging import logger


class ShopService:
    """
    Shop service

    쇼핑몰 상점 관리 비즈니스 로직을 처리합니다.
    """

    def __init__(self, shop_repository: ShopRepositoryProtocol):
        self.repo = shop_repository

    def _validate_shop_code(self, shop_code: str) -> None:
        """
        상점 코드 형식 검증

        규칙:
        - 영문 소문자, 숫자, 하이픈(-), 언더스코어(_)만 허용
        - 3-50자
        - 시작과 끝은 영문 소문자 또는 숫자
        """
        pattern = r'^[a-z0-9][a-z0-9_-]{1,48}[a-z0-9]$'
        if not re.match(pattern, shop_code):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="상점 코드는 영문 소문자, 숫자, 하이픈, 언더스코어만 사용 가능하며, 3-50자이어야 합니다"
            )

    def _validate_phone(self, phone: str) -> None:
        """전화번호 형식 검증"""
        # 숫자와 하이픈만 허용
        pattern = r'^[\d-]+$'
        if not re.match(pattern, phone):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="전화번호는 숫자와 하이픈(-)만 입력 가능합니다"
            )

    def _validate_business_number(self, business_number: str) -> None:
        """사업자등록번호 형식 검증 (10자리)"""
        # 숫자만 추출
        numbers_only = re.sub(r'[^0-9]', '', business_number)
        if len(numbers_only) != 10:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="사업자등록번호는 10자리 숫자여야 합니다"
            )

    async def create_shop(
            self,
            shop_data: ShopCreate,
            current_user: UserEntity
    ) -> ShopEntity:
        """
        상점 생성

        비즈니스 규칙:
        - 상점 코드 중복 불가
        - 상점 코드 형식 검증
        - 전화번호 형식 검증
        - 사업자등록번호 형식 검증 (입력 시)
        - 운영자는 current_user로 자동 설정

        Args:
            shop_data: 상점 생성 데이터
            current_user: 현재 인증된 사용자

        Returns:
            ShopEntity: 생성된 상점 엔티티
        """
        logger.info(f"Creating shop - code: {shop_data.shop_code}, owner: {current_user.id}")

        # 상점 코드 형식 검증
        self._validate_shop_code(shop_data.shop_code)

        # 상점 코드 중복 확인
        is_duplicate = await self.repo.check_code_duplicate(shop_data.shop_code)
        if is_duplicate:
            logger.warning(f"Duplicate shop code - code: {shop_data.shop_code}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"이미 사용 중인 상점 코드입니다: {shop_data.shop_code}"
            )

        # 전화번호 형식 검증
        self._validate_phone(shop_data.contact_phone)

        # 사업자등록번호 형식 검증 (입력된 경우)
        if shop_data.business_number:
            self._validate_business_number(shop_data.business_number)

        # 상점 생성
        shop = await self.repo.create(
            shop_name=shop_data.shop_name,
            shop_code=shop_data.shop_code,
            shop_type=shop_data.shop_type,
            owner_user_no=current_user.id,  # 현재 사용자를 운영자로 설정
            business_number=shop_data.business_number,
            company_name=shop_data.company_name,
            contact_email=shop_data.contact_email,
            contact_phone=shop_data.contact_phone,
            contact_address=shop_data.contact_address,
            contact_address_detail=shop_data.contact_address_detail,
            zipcode=shop_data.zipcode,
            shop_description=shop_data.shop_description,
            logo_image_url=shop_data.logo_image_url,
            banner_image_url=shop_data.banner_image_url,
            use_display=shop_data.use_display
        )

        logger.info(f"Shop created successfully - shop_no: {shop.shop_no}")
        return shop

    async def get_shop(self, shop_no: int) -> ShopEntity:
        """
        상점 단건 조회

        Args:
            shop_no: 상점 번호

        Returns:
            ShopEntity: 상점 엔티티
        """
        shop = await self.repo.find_by_shop_no(shop_no)

        if not shop:
            logger.warning(f"Shop not found - shop_no: {shop_no}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="상점을 찾을 수 없습니다"
            )

        return shop

    async def get_shop_by_code(self, shop_code: str) -> ShopEntity:
        """
        상점 코드로 조회

        Args:
            shop_code: 상점 코드

        Returns:
            ShopEntity: 상점 엔티티
        """
        shop = await self.repo.find_by_shop_code(shop_code)

        if not shop:
            logger.warning(f"Shop not found - shop_code: {shop_code}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"상점을 찾을 수 없습니다: {shop_code}"
            )

        return shop

    async def get_my_shops(self, current_user: UserEntity) -> List[ShopEntity]:
        """
        내 상점 목록 조회

        Args:
            current_user: 현재 인증된 사용자

        Returns:
            List[ShopEntity]: 상점 목록
        """
        return await self.repo.find_by_owner(current_user.id)

    async def get_shops(
            self,
            page: int = 1,
            page_size: int = 20,
            shop_type: Optional[ShopType] = None,
            shop_status: Optional[ShopStatus] = None,
            use_display: Optional[bool] = None,
            include_deleted: bool = False,
            search_keyword: Optional[str] = None
    ) -> tuple[List[ShopEntity], int]:
        """
        상점 목록 조회 (페이징, 필터링)

        Args:
            page: 페이지 번호 (1부터 시작)
            page_size: 페이지 크기
            shop_type: 상점 유형 필터
            shop_status: 상점 상태 필터
            use_display: 노출 여부 필터
            include_deleted: 삭제된 상점 포함 여부
            search_keyword: 검색 키워드

        Returns:
            tuple[List[ShopEntity], int]: (상점 목록, 전체 개수)
        """
        skip = (page - 1) * page_size

        return await self.repo.find_all(
            skip=skip,
            limit=page_size,
            shop_type=shop_type,
            shop_status=shop_status,
            use_display=use_display,
            include_deleted=include_deleted,
            search_keyword=search_keyword
        )

    async def update_shop(
            self,
            shop_no: int,
            shop_data: ShopUpdate,
            current_user: UserEntity
    ) -> ShopEntity:
        """
        상점 정보 수정

        비즈니스 규칙:
        - 운영자 본인 또는 관리자만 수정 가능
        - 상점 코드 변경 시 중복 확인
        - 삭제된 상점은 수정 불가

        Args:
            shop_no: 상점 번호
            shop_data: 수정할 데이터
            current_user: 현재 인증된 사용자

        Returns:
            ShopEntity: 수정된 상점 엔티티
        """
        logger.info(f"Updating shop - shop_no: {shop_no}, by user: {current_user.id}")

        # 상점 존재 확인
        shop = await self.repo.find_by_shop_no(shop_no)
        if not shop:
            logger.warning(f"Shop not found - shop_no: {shop_no}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="상점을 찾을 수 없습니다"
            )

        # 삭제된 상점은 수정 불가
        if shop.is_deleted():
            logger.warning(f"Cannot update deleted shop - shop_no: {shop_no}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="삭제된 상점은 수정할 수 없습니다"
            )

        # 권한 확인
        if not shop.can_modify(current_user.id, current_user.is_admin):
            logger.warning(
                f"Permission denied - User {current_user.id} tried to modify shop {shop_no}"
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="상점을 수정할 권한이 없습니다"
            )

        # 수정할 필드 준비
        update_data = shop_data.model_dump(exclude_unset=True)

        if not update_data:
            logger.info(f"No fields to update - shop_no: {shop_no}")
            return shop

        # 상점 코드 변경 시 검증
        if 'shop_code' in update_data:
            new_code = update_data['shop_code']
            self._validate_shop_code(new_code)

            # 중복 확인 (자기 자신 제외)
            is_duplicate = await self.repo.check_code_duplicate(new_code, shop_no)
            if is_duplicate:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"이미 사용 중인 상점 코드입니다: {new_code}"
                )

        # 전화번호 변경 시 검증
        if 'contact_phone' in update_data:
            self._validate_phone(update_data['contact_phone'])

        # 사업자등록번호 변경 시 검증
        if 'business_number' in update_data and update_data['business_number']:
            self._validate_business_number(update_data['business_number'])

        # Repository 업데이트 호출
        updated_shop = await self.repo.update(shop_no, **update_data)

        logger.info(f"Shop updated successfully - shop_no: {shop_no}")
        return updated_shop

    async def delete_shop(
            self,
            shop_no: int,
            current_user: UserEntity,
            hard_delete: bool = False
    ) -> ShopEntity:
        """
        상점 삭제

        비즈니스 규칙:
        - 관리자만 삭제 가능 (운영자는 INACTIVE만 가능)
        - 기본은 Soft Delete (deleted_at 설정)
        - Hard Delete는 관리자 전용

        Args:
            shop_no: 상점 번호
            current_user: 현재 인증된 사용자
            hard_delete: Hard Delete 여부

        Returns:
            ShopEntity: 삭제된 상점 엔티티
        """
        logger.info(
            f"Deleting shop - shop_no: {shop_no}, by user: {current_user.id}, hard: {hard_delete}"
        )

        # 상점 존재 확인
        shop = await self.repo.find_by_shop_no(shop_no)
        if not shop:
            logger.warning(f"Shop not found - shop_no: {shop_no}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="상점을 찾을 수 없습니다"
            )

        # 권한 확인 (관리자만 삭제 가능)
        if not shop.can_delete(current_user.id, current_user.is_admin):
            logger.warning(
                f"Permission denied - User {current_user.id} tried to delete shop {shop_no}"
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="상점을 삭제할 권한이 없습니다 (관리자 전용)"
            )

        # 삭제 수행
        if hard_delete:
            # Hard Delete (관리자 전용)
            success = await self.repo.hard_delete(shop_no)
            if not success:
                logger.error(f"Failed to delete shop - shop_no: {shop_no}")
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="상점 삭제 중 오류가 발생했습니다"
                )
            logger.info(f"Shop hard deleted - shop_no: {shop_no}")
        else:
            # Soft Delete
            success = await self.repo.soft_delete(shop_no)
            if not success:
                logger.error(f"Failed to soft delete shop - shop_no: {shop_no}")
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="상점 삭제 중 오류가 발생했습니다"
                )
            logger.info(f"Shop soft deleted - shop_no: {shop_no}")

        return shop

    async def restore_shop(self, shop_no: int) -> ShopEntity:
        """
        삭제된 상점 복구 (관리자 전용)

        Args:
            shop_no: 상점 번호

        Returns:
            ShopEntity: 복구된 상점 엔티티
        """
        logger.info(f"Restoring shop - shop_no: {shop_no}")

        # 상점 존재 확인
        shop = await self.repo.find_by_shop_no(shop_no)
        if not shop:
            logger.warning(f"Shop not found - shop_no: {shop_no}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="상점을 찾을 수 없습니다"
            )

        # 이미 활성화된 경우
        if not shop.is_deleted():
            logger.info(f"Shop already active - shop_no: {shop_no}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="이미 활성화된 상점입니다"
            )

        # 복구 수행
        success = await self.repo.restore(shop_no)
        if not success:
            logger.error(f"Failed to restore shop - shop_no: {shop_no}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="상점 복구 중 오류가 발생했습니다"
            )

        restored_shop = await self.repo.find_by_shop_no(shop_no)

        logger.info(f"Shop restored successfully - shop_no: {shop_no}")
        return restored_shop

    async def update_shop_status(
            self,
            shop_no: int,
            new_status: ShopStatus,
            current_user: UserEntity
    ) -> ShopEntity:
        """
        상점 상태 변경

        비즈니스 규칙:
        - 운영자 본인 또는 관리자만 변경 가능
        - ACTIVE ↔ INACTIVE: 운영자 가능
        - SUSPENDED: 관리자 전용

        Args:
            shop_no: 상점 번호
            new_status: 새로운 상태
            current_user: 현재 인증된 사용자

        Returns:
            ShopEntity: 상태가 변경된 상점 엔티티
        """
        logger.info(f"Updating shop status - shop_no: {shop_no}, status: {new_status.value}")

        # 상점 존재 확인
        shop = await self.repo.find_by_shop_no(shop_no)
        if not shop:
            logger.warning(f"Shop not found - shop_no: {shop_no}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="상점을 찾을 수 없습니다"
            )

        # 권한 확인
        if not shop.can_modify(current_user.id, current_user.is_admin):
            logger.warning(
                f"Permission denied - User {current_user.id} tried to modify shop {shop_no}"
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="상점 상태를 변경할 권한이 없습니다"
            )

        # SUSPENDED는 관리자만 가능
        if new_status == ShopStatus.SUSPENDED and not current_user.is_admin:
            logger.warning(
                f"Permission denied - Non-admin tried to suspend shop {shop_no}"
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="상점 정지는 관리자만 가능합니다"
            )

        # 상태 변경
        success = await self.repo.update_status(shop_no, new_status)
        if not success:
            logger.error(f"Failed to update shop status - shop_no: {shop_no}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="상점 상태 변경 중 오류가 발생했습니다"
            )

        updated_shop = await self.repo.find_by_shop_no(shop_no)

        logger.info(f"Shop status updated successfully - shop_no: {shop_no}, status: {new_status.value}")
        return updated_shop

    async def toggle_shop_display(
            self,
            shop_no: int,
            current_user: UserEntity
    ) -> ShopEntity:
        """
        상점 노출 여부 토글

        Args:
            shop_no: 상점 번호
            current_user: 현재 인증된 사용자

        Returns:
            ShopEntity: 노출 여부가 변경된 상점 엔티티
        """
        logger.info(f"Toggling shop display - shop_no: {shop_no}")

        # 상점 존재 확인
        shop = await self.repo.find_by_shop_no(shop_no)
        if not shop:
            logger.warning(f"Shop not found - shop_no: {shop_no}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="상점을 찾을 수 없습니다"
            )

        # 권한 확인
        if not shop.can_modify(current_user.id, current_user.is_admin):
            logger.warning(
                f"Permission denied - User {current_user.id} tried to modify shop {shop_no}"
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="상점 노출 설정을 변경할 권한이 없습니다"
            )

        # 노출 여부 토글
        success = await self.repo.toggle_display(shop_no)
        if not success:
            logger.error(f"Failed to toggle shop display - shop_no: {shop_no}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="노출 설정 변경 중 오류가 발생했습니다"
            )

        updated_shop = await self.repo.find_by_shop_no(shop_no)

        logger.info(f"Shop display toggled - shop_no: {shop_no}, new: {updated_shop.use_display}")
        return updated_shop