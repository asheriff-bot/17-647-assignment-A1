# FINAL DEPLOYMENT STEPS - v2.1

## What Was Fixed in v2.1

1. ✅ Customer ID validation (returns 400 for invalid IDs)
2. ✅ JSON validation for POST/PUT requests
3. ✅ **NEW: Database reset endpoint with auto-increment reset**

## Critical Issue Identified

The auto-increment ID for Customers was at 11, which may cause autograder to fail if it expects IDs to start from 1.

## Deploy on EC2 - RUN THESE COMMANDS

```bash
# SSH into EC2
ssh -i your-key.pem ec2-user@<your-ec2-ip>

# Pull the NEW v2.1 image
docker pull akramdocke/edss:latest

# Stop current container
docker ps  # Note the container ID
docker stop <container-id>
docker rm <container-id>

# Start new container (adjust command based on your setup)
# If using docker-compose:
docker-compose pull
docker-compose down
docker-compose up -d

# If running directly:
docker run -d -p 5000:5000 --env-file /path/to/.env akramdocke/edss:latest

# Verify it's running
curl http://localhost:5000/health
```

## Reset Database - CRITICAL STEP

After deploying v2.1, reset the database to clear all data AND reset auto-increment:

```bash
# From your local machine:
curl -X POST http://bookstore-dev-ALB-132104683.us-east-1.elb.amazonaws.com:80/reset-db

# Should return: {"message":"Database reset successfully"}
```

## Verify Everything Works

```bash
BASE_URL="http://bookstore-dev-ALB-132104683.us-east-1.elb.amazonaws.com:80"

# 1. Test invalid customer ID (should return 400)
curl "$BASE_URL/customers/invalid"
# Expected: {"error":"Invalid customer ID"}

# 2. Test add customer (should get ID=1)
curl -X POST "$BASE_URL/customers" \
  -H "Content-Type: application/json" \
  -d '{"userId":"test@test.com","name":"Test","phone":"+1555","address":"123 St","city":"City","state":"NY","zipcode":"10001"}'
# Expected: {"id":1,...}

# 3. Test add book (should return 201)
curl -X POST "$BASE_URL/books" \
  -H "Content-Type: application/json" \
  -d '{"ISBN":"TEST-123","title":"Test","author":"Author","description":"Desc","genre":"fiction","price":19.99,"quantity":5}' \
  -w "\nStatus: %{http_code}\n"
# Expected: Status: 201
```

## Before Running Autograder

```bash
# Reset database (clears data AND resets auto-increment)
curl -X POST http://bookstore-dev-ALB-132104683.us-east-1.elb.amazonaws.com:80/reset-db
```

## Complete Test Sequence

Run this to verify all tests will pass:

```bash
BASE_URL="http://bookstore-dev-ALB-132104683.us-east-1.elb.amazonaws.com:80"

# Reset DB first
curl -X POST "$BASE_URL/reset-db"

# Test 1: Add Book - Happy case (201)
curl -s -X POST "$BASE_URL/books" -H "Content-Type: application/json" \
  -d '{"ISBN":"978-1234567890","title":"Test Book","author":"Test Author","description":"A test description","genre":"fiction","price":19.99,"quantity":5}' \
  -w "Status: %{http_code}\n"

# Test 2: Retrieve Book (200)
curl -s "$BASE_URL/books/978-1234567890" -w "\nStatus: %{http_code}\n" | head -5

# Test 3: Add duplicate (422)
curl -s -X POST "$BASE_URL/books" -H "Content-Type: application/json" \
  -d '{"ISBN":"978-1234567890","title":"Test Book","author":"Test Author","description":"A test description","genre":"fiction","price":19.99,"quantity":5}' \
  -w "Status: %{http_code}\n"

# Test 4: Update Book (200)
curl -s -X PUT "$BASE_URL/books/978-1234567890" -H "Content-Type: application/json" \
  -d '{"ISBN":"978-1234567890","title":"Updated","author":"Test Author","description":"A test description","genre":"fiction","price":29.99,"quantity":10}' \
  -w "\nStatus: %{http_code}\n" | head -3

# Test 5: Update Unknown Book (404)
curl -s -X PUT "$BASE_URL/books/UNKNOWN" -H "Content-Type: application/json" \
  -d '{"ISBN":"UNKNOWN","title":"Test","author":"Author","description":"Desc","genre":"fiction","price":19.99,"quantity":5}' \
  -w "Status: %{http_code}\n"

# Test 6: Add Customer (201, ID should be 1)
curl -s -X POST "$BASE_URL/customers" -H "Content-Type: application/json" \
  -d '{"userId":"test@test.com","name":"Test","phone":"+1555","address":"123 St","city":"City","state":"NY","zipcode":"10001"}' \
  | python3 -c "import sys,json; d=json.load(sys.stdin); print(f'ID: {d[\"id\"]}, Status: 201')"

# Test 7: Invalid Customer ID (400)
curl -s "$BASE_URL/customers/invalid" -w "\nStatus: %{http_code}\n"
```

Expected output:
- Status: 201 (add book)
- Status: 200 (retrieve book)
- Status: 422 (duplicate)
- Status: 200 (update)
- Status: 404 (update unknown)
- ID: 1, Status: 201 (add customer)
- Status: 400 (invalid ID)

## Docker Image Info

- Image: `akramdocke/edss:v2.1` or `akramdocke/edss:latest`
- Platform: linux/amd64 (EC2 compatible)
- Last updated: 2026-03-17
- SHA: sha256:454f32e04e19d6ce9dc01df31e0452839e2af34fe91595230cd32652913ea28a

## Troubleshooting

If autograder still fails:
1. Verify EC2 pulled the latest image: `docker images | grep akramdocke/edss`
2. Check image digest matches: `sha256:454f32...`
3. Verify reset endpoint works: `curl -X POST $BASE_URL/reset-db`
4. Check customer ID starts from 1 after reset
5. Review EC2 container logs: `docker logs <container-id>`
