#!/bin/bash

BASE_URL="http://bookstore-dev-ALB-132104683.us-east-1.elb.amazonaws.com:80"

# Reset database
echo "Resetting database..."
curl -X POST "$BASE_URL/reset-db"
echo ""

# Add a book (ALL ON ONE LINE - CRITICAL!)
echo "Adding book..."
curl -s -X POST "$BASE_URL/books" -H "Content-Type: application/json" -d '{"ISBN":"978-1234567890","title":"Test Book","author":"Test Author","description":"A test book description","genre":"fiction","price":19.99,"quantity":5}'
echo ""

# Wait 1 second
sleep 1

# Test summary length 10 times
echo "Testing summary length (should be 1649+ chars)..."
for i in {1..10}; do
    SUMMARY_LEN=$(curl -s "$BASE_URL/books/978-1234567890" | python3 -c "import sys,json; d=json.load(sys.stdin); print(len(d.get('summary','')))" 2>/dev/null)
    echo "Request $i: Summary = $SUMMARY_LEN chars"
    sleep 0.5
done
