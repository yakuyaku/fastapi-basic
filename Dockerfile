# Python 3.11 slim 이미지 사용
FROM python:3.11-slim

# 작업 디렉토리 설정
WORKDIR /app

# 시스템 패키지 업데이트 및 필요한 패키지 설치
RUN apt-get update && apt-get install -y \
    gcc \
    default-libmysqlclient-dev \
    pkg-config \
    && rm -rf /var/lib/apt/lists/*

# 비root 사용자 생성 (보안 강화)
RUN groupadd -r appuser && useradd -r -g appuser appuser

# Python 의존성 파일 복사
COPY requirements.txt .

# Python 패키지 설치
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# 애플리케이션 코드 복사
COPY ./app ./app

# 로그 디렉토리 생성 및 권한 설정
RUN mkdir -p /app/logs && \
    chmod 755 /app/logs && \
    chown -R appuser:appuser /app/logs

# 업로드 디렉토리 생성 및 권한 설정
RUN mkdir -p /app/uploads && \
    chmod 755 /app/uploads && \
    chown -R appuser:appuser /app/uploads

# 애플리케이션 디렉토리 권한 설정
RUN chown -R appuser:appuser /app

# 비root 사용자로 전환
USER appuser

# 포트 노출 (Railway가 자동으로 PORT 환경변수 설정)
EXPOSE 8000

# 애플리케이션 실행
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]