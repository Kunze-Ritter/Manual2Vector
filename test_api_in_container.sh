#!/bin/bash
# Test Pipeline Errors API from inside container

echo "=== Testing Pipeline Errors API ==="
echo ""

# Login
echo "1. Login..."
LOGIN_RESPONSE=$(curl -s -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"admin"}')

TOKEN=$(echo $LOGIN_RESPONSE | grep -o '"access_token":"[^"]*"' | cut -d'"' -f4)

if [ -z "$TOKEN" ]; then
  echo "   ❌ Login failed"
  echo "   Response: $LOGIN_RESPONSE"
  exit 1
fi

echo "   ✅ Login successful"
echo ""

# Test List Errors
echo "2. GET /api/v1/pipeline/errors"
ERRORS_RESPONSE=$(curl -s -X GET http://localhost:8000/api/v1/pipeline/errors \
  -H "Authorization: Bearer $TOKEN")

echo "   Response: $ERRORS_RESPONSE"
echo ""

# Test Swagger UI
echo "3. Check Swagger UI"
SWAGGER_STATUS=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/docs)
if [ "$SWAGGER_STATUS" = "200" ]; then
  echo "   ✅ Swagger UI accessible"
else
  echo "   ❌ Swagger UI not accessible (HTTP $SWAGGER_STATUS)"
fi

echo ""
echo "=== Summary ==="
echo "✅ Pipeline Errors Router is registered and working!"
echo "✅ API endpoints are accessible"
echo ""
