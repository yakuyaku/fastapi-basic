#!/bin/bash

echo "🚀 운영 환경으로 시작합니다..."
export APP_ENV=production
uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4