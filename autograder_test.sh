#!/bin/bash

BASE_URL="http://bookstore-dev-ALB-132104683.us-east-1.elb.amazonaws.com:80"

echo "=== AUTOGRADER SIMULATION (FIXED) ==="

# Reset
echo "1. Resetting database..."
curl -s -X POST "$BASE_URL/reset-db"
sleep 1

# Test 1: Add Book
echo -e "\n2. Add Book - Happy case"
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" -X POST "$BASE_URL/books" \
  -H "Content-Type: application/json" \
  -d '{"ISBN":"978-1234567890","title":"Test Book","author":"Test Author","description":"A test book description","genre":"fiction","price":19.99,"quantity":5}')
echo "   Status: $HTTP_CODE (expect 201)"
[ "$HTTP_CODE" = "201" ] && echo "   ✅ PASS" || { echo "   ❌ FAIL"; exit 1; }

# Test 2: Add duplicate
echo -e "\n3. Add Book - Duplicate"
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" -X POST "$BASE_URL/books" \
  -H "Content-Type: application/json" \
  -d '{"ISBN":"978-1234567890","title":"Test Book","author":"Test Author","description":"A test book description","genre":"fiction","price":19.99,"quantity":5}')
echo "   Status: $HTTP_CODE (expect 422)"
[ "$HTTP_CODE" = "422" ] && echo "   ✅ PASS" || { echo "   ❌ FAIL"; exit 1; }

# Test 3: Update Book
echo -e "\n4. Update Book - Happy case"
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" -X PUT "$BASE_URL/books/978-1234567890" \
  -H "Content-Type: application/json" \
  -d '{"ISBN":"978-1234567890","title":"Updated Title","author":"Test Author","description":"A test book description","genre":"fiction","price":29.99,"quantity":10}')
echo "   Status: $HTTP_CODE (expect 200)"
[ "$HTTP_CODE" = "200" ] && echo "   ✅ PASS" || { echo "   ❌ FAIL"; exit 1; }

# Test 4: Retrieve Book
echo -e "\n5. Retrieve Book - Happy case"
RESPONSE=$(curl -s "$BASE_URL/books/978-1234567890")
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" "$BASE_URL/books/978-1234567890")
echo "   Status: $HTTP_CODE (expect 200)"
[ "$HTTP_CODE" = "200" ] && echo "   ✅ PASS" || { echo "   ❌ FAIL"; exit 1; }

# Check summary
SUMMARY_LEN=$(echo "$RESPONSE" | python3 -c "import sys,json; d=json.load(sys.stdin); print(len(d.get('summary','')))" 2>/dev/null)
echo "   Summary length: $SUMMARY_LEN chars (expect 200+)"
[ "$SUMMARY_LEN" -ge 200 ] && echo "   ✅ PASS" || { echo "   ❌ FAIL - Summary too short"; exit 1; }

# Test 5: Update Unknown
echo -e "\n6. Update Book - Unknown"
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" -X PUT "$BASE_URL/books/UNKNOWN-999" \
  -H "Content-Type: application/json" \
  -d '{"ISBN":"UNKNOWN-999","title":"Test","author":"Author","description":"Desc","genre":"fiction","price":19.99,"quantity":5}')
echo "   Status: $HTTP_CODE (expect 404)"
[ "$HTTP_CODE" = "404" ] && echo "   ✅ PASS" || { echo "   ❌ FAIL"; exit 1; }

# Test 6: Retrieve with ISBN endpoint
echo -e "\n7. Retrieve Book - ISBN endpoint"
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" "$BASE_URL/books/isbn/978-1234567890")
echo "   Status: $HTTP_CODE (expect 200)"
[ "$HTTP_CODE" = "200" ] && echo "   ✅ PASS" || { echo "   ❌ FAIL"; exit 1; }

# Test 7: LLM Summary with technical term
echo -e "\n8. LLM Summary - Technical term check"
RESPONSE=$(curl -s "$BASE_URL/books/978-1234567890")
HAS_TERM=$(echo "$RESPONSE" | python3 -c "import sys,json; d=json.load(sys.stdin); s=d.get('summary','').lower(); print('yes' if any(t in s for t in ['architecture','system','latency','distributed']) else 'no')" 2>/dev/null)
echo "   Has technical term: $HAS_TERM (expect yes)"
[ "$HAS_TERM" = "yes" ] && echo "   ✅ PASS" || { echo "   ❌ FAIL"; exit 1; }

echo -e "\n=== ✅ ALL TESTS PASSED ==="
