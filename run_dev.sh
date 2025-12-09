#!/bin/bash

echo "🚀 개발 환경으로 시작합니다..."
export APP_ENV=development
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000