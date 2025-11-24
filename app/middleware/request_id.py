import uuid
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp
import logging

logger = logging.getLogger("fastapi_app")


class RequestIdMiddleware(BaseHTTPMiddleware):
    """Request ID 생성 및 추적 미들웨어"""

    def __init__(self, app: ASGIApp):
        super().__init__(app)
        logger.info("🔧 RequestIdMiddleware 초기화")

    async def dispatch(self, request: Request, call_next):
        # 1. 클라이언트가 보낸 Request ID 확인 (있으면 사용)
        request_id = request.headers.get("X-Request-ID")

        # 2. 없으면 새로 생성
        if not request_id:
            request_id = str(uuid.uuid4())

        # 3. Request state에 저장 (다른 곳에서 접근 가능하도록)
        request.state.request_id = request_id

        # 4. 요청 처리
        response = await call_next(request)

        # 5. 응답 헤더에 Request ID 추가 (클라이언트가 확인 가능)
        response.headers["X-Request-ID"] = request_id

        return response