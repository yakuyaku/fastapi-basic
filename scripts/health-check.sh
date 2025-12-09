#!/bin/bash

# 설정
API_URL="https://wejeju.com/api"
MAX_RETRIES=5
RETRY_DELAY=2

echo "🏥 Health Check Starting..."

for i in $(seq 1 $MAX_RETRIES); do
    echo "Attempt $i/$MAX_RETRIES..."

    # Health endpoint 확인
    if curl -f -s "$API_URL/health" > /dev/null 2>&1; then
        echo "✅ Health check passed!"

        # 응답 내용 확인
        RESPONSE=$(curl -s "$API_URL/health")
        echo "Response: $RESPONSE"
        exit 0
    fi

    if [ $i -lt $MAX_RETRIES ]; then
        echo "Retrying in ${RETRY_DELAY}s..."
        sleep $RETRY_DELAY
    fi
done

echo "❌ Health check failed after $MAX_RETRIES attempts"
exit 1