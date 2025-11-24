import time
import logging
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

logger = logging.getLogger("fastapi_app")


class LoggingMiddleware(BaseHTTPMiddleware):
    """요청/응답 로깅 미들웨어"""

    def __init__(self, app: ASGIApp):
        super().__init__(app)
        logger.info("🔧 LoggingMiddleware 초기화")

    async def dispatch(self, request: Request, call_next):
        # 요청 시작 시간
        start_time = time.time()

        # Request ID 가져오기 (RequestIdMiddleware에서 설정한 값)
        request_id = getattr(request.state, "request_id", "no-id")

        # 요청 정보
        method = request.method
        url = str(request.url)
        client_host = request.client.host if request.client else "unknown"

        # 요청 로깅 (Request ID 포함)
        logger.info(
            f"[{request_id}] → {method} {url} - Client: {client_host}"
        )

        # 쿼리 파라미터 로깅
        if request.query_params:
            logger.debug(
                f"[{request_id}] Query: {dict(request.query_params)}"
            )

        try:
            # 요청 처리
            response = await call_next(request)

            # 처리 시간 계산
            process_time = time.time() - start_time

            # 응답 로깅 (Request ID 포함)
            logger.info(
                f"[{request_id}] ← {method} {url} - "
                f"Status: {response.status_code} - "
                f"Duration: {process_time:.3f}s"
            )

            # 응답 헤더에 처리 시간 추가
            response.headers["X-Process-Time"] = str(process_time)

            return response

        except Exception as e:
            # 에러 로깅
            process_time = time.time() - start_time
            logger.error(
                f"[{request_id}] ✗ {method} {url} - "
                f"Error: {str(e)} - "
                f"Duration: {process_time:.3f}s",
                exc_info=True
            )
            raise


class DetailedLoggingMiddleware(BaseHTTPMiddleware):
    """상세 로깅 미들웨어 (개발 환경용)"""

    def __init__(self, app: ASGIApp):
        super().__init__(app)
        logger.info("🔧 DetailedLoggingMiddleware 초기화")

    async def dispatch(self, request: Request, call_next):
        start_time = time.time()

        # Request ID 가져오기
        request_id = getattr(request.state, "request_id", "no-id")

        # 요청 상세 정보
        logger.info(
            f"[{request_id}] → {request.method} {request.url}"
        )
        logger.debug(
            f"[{request_id}] Client: {request.client.host if request.client else 'unknown'}"
        )

        if request.query_params:
            logger.debug(
                f"[{request_id}] Query: {dict(request.query_params)}"
            )

        if request.headers:
            # 민감한 헤더는 제외
            safe_headers = {
                k: v for k, v in request.headers.items()
                if k.lower() not in ['authorization', 'cookie']
            }
            logger.debug(
                f"[{request_id}] Headers: {safe_headers}"
            )

        try:
            response = await call_next(request)
            process_time = time.time() - start_time

            logger.info(
                f"[{request_id}] ← {request.method} {request.url} - "
                f"Status: {response.status_code} - "
                f"Duration: {process_time:.3f}s"
            )

            response.headers["X-Process-Time"] = str(process_time)
            return response

        except Exception as e:
            process_time = time.time() - start_time
            logger.error(
                f"[{request_id}] ✗ {request.method} {request.url} - "
                f"Error: {str(e)} - Duration: {process_time:.3f}s",
                exc_info=True
            )
            raise