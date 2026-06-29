#!/bin/bash
set -e

# Configuration
URL="http://localhost:8000"
MAX_RETRIES=60
RETRY_INTERVAL=2

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo "==========================================="
echo "    Athenis Production Deployment Verifier "
echo "==========================================="

echo -e "\n[1/5] Building production images from scratch..."
docker compose -f docker-compose.prod.yml build --no-cache backend celery_worker

echo -e "\n[2/5] Starting production stack..."
docker compose -f docker-compose.prod.yml up -d

echo -e "\n[3/5] Waiting for backend to become healthy..."
count=0
until $(curl --output /dev/null --silent --fail "$URL/health"); do
    printf '.'
    sleep $RETRY_INTERVAL
    count=$((count + 1))
    if [ $count -ge $MAX_RETRIES ]; then
        echo -e "\n${RED}Error: Backend failed to become healthy within $((MAX_RETRIES * RETRY_INTERVAL)) seconds.${NC}"
        echo "Backend Logs:"
        docker compose -f docker-compose.prod.yml logs backend
        exit 1
    fi
done
echo -e "\n${GREEN}Backend is healthy!${NC}"

echo -e "\n[4/5] Running Integration Tests..."

# Test 1: Health endpoint
echo "Testing /health..."
HEALTH_STATUS=$(curl -s -o /dev/null -w "%{http_code}" "$URL/health")
if [ "$HEALTH_STATUS" != "200" ]; then
    echo -e "${RED}Failed: Health endpoint returned $HEALTH_STATUS${NC}"
    exit 1
fi
echo -e "${GREEN}Pass${NC}"

# Test 2: Check Celery Workers via backend API if possible or check logs
echo "Verifying Celery Workers..."
CELERY_LOGS=$(docker compose -f docker-compose.prod.yml logs celery_worker)
if echo "$CELERY_LOGS" | grep -q "ready."; then
    echo -e "${GREEN}Celery worker is ready and connected to broker.${NC}"
else
    echo -e "${RED}Warning: Celery worker may not be ready. Check logs.${NC}"
    # Wait a bit longer to see if it connects
    sleep 5
    if docker compose -f docker-compose.prod.yml logs celery_worker | grep -q "ready."; then
        echo -e "${GREEN}Celery worker is ready and connected to broker.${NC}"
    else
         echo -e "${RED}Failed to verify celery worker readiness.${NC}"
         exit 1
    fi
fi

# Test 3: Authenticated API endpoint simulation
# We can just check that a 401 is returned for protected routes instead of 500 error
echo "Testing Authentication flow (Expect 401 Unauthorized for /api/v1/documents)..."
AUTH_STATUS=$(curl -s -o /dev/null -w "%{http_code}" "$URL/api/v1/documents")
if [ "$AUTH_STATUS" != "401" ]; then
    echo -e "${RED}Failed: Expected 401, got $AUTH_STATUS${NC}"
    exit 1
fi
echo -e "${GREEN}Pass${NC}"

echo -e "\n[5/5] Gracefully tearing down environment..."
docker compose -f docker-compose.prod.yml down

echo -e "\n${GREEN}===========================================${NC}"
echo -e "${GREEN}  All Verification Tests Passed Successfully! ${NC}"
echo -e "${GREEN}===========================================${NC}"
