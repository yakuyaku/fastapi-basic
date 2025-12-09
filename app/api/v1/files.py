"""
File API endpoints (v1) - Controller Layer
app/api/v1/files.py
"""
from fastapi import APIRouter, Request, Depends, UploadFile, File, Query, status
from fastapi.responses import FileResponse
from typing import Optional
from app.schemas.file import (
    FileUploadResponse,
    FileResponse as FileResponseSchema,
    FileListResponse,
    PostAttachmentResponse,
    AttachFilesRequest,
    AttachFilesResponse,
    FileDeleteResponse
)
from app.services.file_service import FileService
from app.domain.entities.user import UserEntity
from app.api.dependencies import (
    get_file_service,
    get_current_user,
    get_optional_user,
    get_current_admin_user
)


router = APIRouter(prefix="/files", tags=["files"])


@router.post("/upload", response_model=FileUploadResponse, status_code=status.HTTP_201_CREATED)
async def upload_file(
        request: Request,
        file: UploadFile = File(...),
        current_user: Optional[UserEntity] = Depends(get_optional_user),
        file_service: FileService = Depends(get_file_service),
        is_public: bool = Query(True, description="공개 파일 여부"),
        is_temp: bool = Query(True, description="임시 파일 여부 (24시간 후 자동 삭제)")
):
    """
    파일 업로드

    **인증**: 선택 (게스트 사용자 허용)

    - **file**: 업로드할 파일
    - **is_public**: 공개 파일 여부 (기본값: true)
    - **is_temp**: 임시 파일 여부 (기본값: true, 24시간 후 자동 삭제)

    지원 파일:
    - 이미지: jpg, png, gif, webp, bmp, svg
    - 문서: pdf, doc, docx, xls, xlsx, ppt, pptx, txt
    - 압축: zip, rar, 7z
    - 동영상: mp4, avi, mov

    크기 제한:
    - 이미지: 10MB
    - 문서: 50MB

    인증된 사용자는 본인 이름으로, 게스트는 "guest"로 등록됩니다.
    """
    request_id = getattr(request.state, "request_id", "no-id")
    upload_ip = request.client.host if request.client else None

    # Service 계층 호출
    file_entity = await file_service.upload_file(
        file=file,
        current_user=current_user,
        upload_ip=upload_ip,
        is_public=is_public,
        is_temp=is_temp
    )

    # Entity를 Response schema로 변환
    return FileUploadResponse(
        id=file_entity.id,
        original_filename=file_entity.original_filename,
        stored_filename=file_entity.stored_filename,
        file_size=file_entity.file_size,
        mime_type=file_entity.mime_type,
        file_extension=file_entity.file_extension,
        created_at=file_entity.created_at,
        is_temp=is_temp
    )


@router.post("/posts/{post_id}/attach", response_model=AttachFilesResponse)
async def attach_files_to_post(
        request: Request,
        post_id: int,
        attach_data: AttachFilesRequest,
        current_user: UserEntity = Depends(get_current_user),
        file_service: FileService = Depends(get_file_service)
):
    """
    게시글에 파일 첨부

    **인증 필요**: Bearer Token

    - **post_id**: 게시글 ID
    - **file_ids**: 첨부할 파일 ID 목록 (최대 10개)

    첨부 시:
    - 임시 파일에서 정식 파일로 전환됩니다
    - 첫 번째 이미지가 자동으로 썸네일로 설정됩니다
    """
    request_id = getattr(request.state, "request_id", "no-id")

    # Service 계층 호출
    attachments = await file_service.attach_files_to_post(
        post_id=post_id,
        file_ids=attach_data.file_ids,
        current_user=current_user
    )

    # Entity를 Response schema로 변환
    return AttachFilesResponse(
        post_id=post_id,
        attached_count=len(attachments),
        attachments=[
            PostAttachmentResponse(
                id=att.id,
                post_id=att.post_id,
                file_id=att.file_id,
                display_order=att.display_order,
                is_thumbnail=att.is_thumbnail,
                created_at=att.created_at
            )
            for att in attachments
        ]
    )


@router.get("/posts/{post_id}/attachments", response_model=list[PostAttachmentResponse])
async def get_post_attachments(
        request: Request,
        post_id: int,
        file_service: FileService = Depends(get_file_service)
):
    """
    게시글의 첨부파일 목록 조회

    **인증**: 불필요

    - **post_id**: 게시글 ID

    Returns:
        첨부파일 목록 (파일 정보 포함)
    """
    request_id = getattr(request.state, "request_id", "no-id")

    # Service 계층 호출
    attachments = await file_service.get_post_attachments(post_id)

    # Entity를 Response schema로 변환
    return [
        PostAttachmentResponse(
            id=att.id,
            post_id=att.post_id,
            file_id=att.file_id,
            display_order=att.display_order,
            is_thumbnail=att.is_thumbnail,
            created_at=att.created_at,
            file=FileResponseSchema(
                id=att.file.id,
                original_filename=att.file.original_filename,
                stored_filename=att.file.stored_filename,
                file_path=att.file.file_path,
                file_size=att.file.file_size,
                mime_type=att.file.mime_type,
                file_extension=att.file.file_extension,
                uploader_id=att.file.uploader_id,
                upload_ip=att.file.upload_ip,
                download_count=att.file.download_count,
                created_at=att.file.created_at,
                is_deleted=att.file.is_deleted,
                is_public=att.file.is_public
            ) if att.file else None
        )
        for att in attachments
    ]


@router.get("/{file_id}/download")
async def download_file(
        request: Request,
        file_id: int,
        current_user: Optional[UserEntity] = Depends(get_optional_user),
        file_service: FileService = Depends(get_file_service)
):
    """
    파일 다운로드

    **인증**: 선택 (비공개 파일은 권한 필요)

    - **file_id**: 파일 ID

    공개 파일은 누구나 다운로드 가능하며, 비공개 파일은 업로더 본인 또는 관리자만 다운로드 가능합니다.
    """
    request_id = getattr(request.state, "request_id", "no-id")

    # Service 계층 호출
    file_path, original_filename = await file_service.download_file(file_id, current_user)

    # 파일 응답 반환
    return FileResponse(
        path=str(file_path),
        filename=original_filename,
        media_type='application/octet-stream'
    )


@router.get("/{file_id}", response_model=FileResponseSchema)
async def get_file_info(
        request: Request,
        file_id: int,
        current_user: Optional[UserEntity] = Depends(get_optional_user),
        file_service: FileService = Depends(get_file_service)
):
    """
    파일 정보 조회

    **인증**: 선택

    - **file_id**: 파일 ID

    Returns:
        파일 상세 정보
    """
    request_id = getattr(request.state, "request_id", "no-id")

    # Service에서 파일 조회 (file_repo를 직접 사용)
    file_entity = await file_service.file_repo.find_by_id(file_id)

    if not file_entity:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="파일을 찾을 수 없습니다")

    # 접근 권한 확인
    user_id = current_user.id if current_user else 0
    is_admin = current_user.is_admin if current_user else False

    if not file_entity.can_access(user_id, is_admin):
        from fastapi import HTTPException
        raise HTTPException(status_code=403, detail="파일에 접근할 권한이 없습니다")

    # Entity를 Response schema로 변환
    return FileResponseSchema(
        id=file_entity.id,
        original_filename=file_entity.original_filename,
        stored_filename=file_entity.stored_filename,
        file_path=file_entity.file_path,
        file_size=file_entity.file_size,
        mime_type=file_entity.mime_type,
        file_extension=file_entity.file_extension,
        uploader_id=file_entity.uploader_id,
        upload_ip=file_entity.upload_ip,
        download_count=file_entity.download_count,
        created_at=file_entity.created_at,
        is_deleted=file_entity.is_deleted,
        is_public=file_entity.is_public,
        uploader_username=file_entity.uploader_username,
        uploader_email=file_entity.uploader_email
    )


@router.delete("/{file_id}", response_model=FileDeleteResponse)
async def delete_file(
        request: Request,
        file_id: int,
        current_user: UserEntity = Depends(get_current_user),
        file_service: FileService = Depends(get_file_service),
        hard_delete: bool = Query(False, description="완전 삭제 여부")
):
    """
    파일 삭제

    **인증 필요**: Bearer Token

    - **file_id**: 파일 ID
    - **hard_delete**: 완전 삭제 여부 (기본값: false)

    기본적으로 Soft Delete되며, hard_delete=true인 경우 실제 파일도 삭제됩니다.
    본인이 업로드한 파일 또는 관리자만 삭제 가능합니다.
    """
    request_id = getattr(request.state, "request_id", "no-id")

    # Service 계층 호출
    file_entity = await file_service.delete_file(file_id, current_user, hard_delete)

    # Entity를 Response schema로 변환
    return FileDeleteResponse(
        id=file_entity.id,
        original_filename=file_entity.original_filename
    )


@router.post("/cleanup-temp", status_code=status.HTTP_200_OK)
async def cleanup_expired_temp_files(
        request: Request,
        current_user: UserEntity = Depends(get_current_admin_user),
        file_service: FileService = Depends(get_file_service)
):
    """
    만료된 임시 파일 정리 - 관리자 전용

    **인증 필요**: Bearer Token (관리자)

    24시간 이상 지난 임시 파일을 삭제합니다.
    """
    request_id = getattr(request.state, "request_id", "no-id")

    # Service 계층 호출
    deleted_count = await file_service.cleanup_expired_temp_files()

    return {
        "deleted_count": deleted_count,
        "message": f"{deleted_count}개의 임시 파일이 정리되었습니다"
    }