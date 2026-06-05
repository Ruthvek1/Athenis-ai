#!/bin/bash
# Athenis Deployment Verification Script

echo "Checking Athenis API Health..."
API_STATUS=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/health)

if [ "$API_STATUS" -eq 200 ]; then
    echo "✅ API is Healthy"
else
    echo "❌ API check failed (Status: $API_STATUS)"
    exit 1
fi

echo "Checking Athenis Frontend..."
FRONTEND_STATUS=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:3000)

if [ "$FRONTEND_STATUS" -eq 200 ]; then
    echo "✅ Frontend is Healthy"
else
    echo "❌ Frontend check failed (Status: $FRONTEND_STATUS)"
    exit 1
fi

echo "Checking Observability Stack..."
METRICS_STATUS=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/metrics)

if [ "$METRICS_STATUS" -eq 200 ]; then
    echo "✅ Prometheus Metrics Endpoint is Active"
else
    echo "❌ Metrics Endpoint failed (Status: $METRICS_STATUS)"
    exit 1
fi

echo "🎉 All deployment checks passed!"
exit 0
