#!/bin/bash

# Script to clear all test data from the production database
# Run this before autograder tests to ensure clean state

BASE_URL="http://bookstore-dev-ALB-132104683.us-east-1.elb.amazonaws.com:80"

echo "Clearing all books and customers from database..."

# Get all books and delete them
echo "Fetching books..."
BOOKS=$(curl -s "$BASE_URL/books" | python3 -c "import sys, json; data=json.load(sys.stdin); print(' '.join([book['ISBN'] for book in data]))")

for isbn in $BOOKS; do
    echo "  Deleting book: $isbn"
    curl -s -X DELETE "$BASE_URL/books/$isbn" > /dev/null
done

# Get all customers and delete them
echo "Fetching customers..."
CUSTOMERS=$(curl -s "$BASE_URL/customers" | python3 -c "import sys, json; data=json.load(sys.stdin); print(' '.join([str(c['id']) for c in data]))")

for id in $CUSTOMERS; do
    echo "  Deleting customer: $id"
    curl -s -X DELETE "$BASE_URL/customers/$id" > /dev/null
done

echo ""
echo "Database cleared. Verifying..."
echo "Books: $(curl -s "$BASE_URL/books")"
echo "Customers: $(curl -s "$BASE_URL/customers")"
echo ""
echo "Done!"
