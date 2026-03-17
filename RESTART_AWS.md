# AWS Deployment Restart Instructions

The Docker image has been updated with all bug fixes, but AWS needs to be restarted to pull the new image.

## What Was Fixed

✅ Customer ID validation (returns 400 for invalid IDs, not 404)
✅ JSON validation for POST/PUT requests
✅ All error codes match autograder expectations
✅ Docker image rebuilt and pushed as `akramdocke/edss:v2.0` and `akramdocke/edss:latest`

## How to Restart AWS Deployment

The autograder is likely pulling from the running AWS instance. You need to **force AWS to pull the new Docker image**.

### Method 1: SSH into EC2 and Restart Container (Recommended)

If you're using EC2 with Docker/docker-compose:

```bash
# SSH into your EC2 instance
ssh -i your-key.pem ec2-user@<your-ec2-ip>

# Navigate to app directory
cd /path/to/app

# Pull the latest image
docker pull akramdocke/edss:latest

# Restart containers
docker-compose down
docker-compose up -d

# Verify it's running
curl localhost:5000/health
```

### Method 2: Using AWS ECS (if using ECS)

```bash
# Force new deployment (pulls latest :latest tag)
aws ecs update-service \
  --cluster <your-cluster-name> \
  --service <your-service-name> \
  --force-new-deployment \
  --region us-east-1
```

### Method 3: Using AWS Console

1. Go to AWS Console → EC2 or ECS
2. Find your running instance/service
3. Stop the instance/service
4. Start it again (will pull latest image)

### Method 4: Update docker-compose.yml to force pull

Update your docker-compose.yml to use the specific version tag:

```yaml
services:
  app:
    image: akramdocke/edss:v2.0  # Changed from :latest
    # ... rest of config
```

Then restart:
```bash
docker-compose pull
docker-compose up -d --force-recreate
```

## Verify the Fix is Deployed

After restarting, run this test:

```bash
BASE_URL="http://bookstore-dev-ALB-132104683.us-east-1.elb.amazonaws.com:80"

# Test 1: Invalid customer ID should return 400 (not 404)
curl -s "$BASE_URL/customers/invalid-id" | grep "Invalid customer ID"

# Test 2: Add book should return 201
curl -s -X POST "$BASE_URL/books" \
  -H "Content-Type: application/json" \
  -d '{"ISBN":"TEST-123","title":"Test","author":"Author","description":"Desc","genre":"fiction","price":19.99,"quantity":5}' \
  -w "\nStatus: %{http_code}\n"

# Should see Status: 201
```

## Before Running Autograder

**CRITICAL:** Clear the database first:

```bash
./clear_database.sh
```

This ensures no test data conflicts with autograder expectations.

## Troubleshooting

If tests still fail after restart:

1. **Check which image is running:**
   ```bash
   docker ps
   docker inspect <container-id> | grep Image
   ```

2. **Force remove old images:**
   ```bash
   docker rmi akramdocke/edss:latest
   docker pull akramdocke/edss:latest
   ```

3. **Check app logs:**
   ```bash
   docker logs <container-id>
   ```

4. **Verify the code is correct in the running container:**
   ```bash
   docker exec <container-id> grep -A 5 "def get_customer_by_id" /app/app.py
   ```

## Expected Test Results

After restart, all these should pass:

- ✅ Add Book - Happy case (201)
- ✅ Add Book - Duplicate (422)
- ✅ Update Book - Happy case (200)
- ✅ Update Book - Unknown (404)
- ✅ Retrieve Book (200)
- ✅ Retrieve Book - ISBN endpoint (200)
- ✅ LLM Summary (200 with 200+ char summary)
- ✅ Add Customer (201)
- ✅ Retrieve Customer by ID (200)
- ✅ Retrieve Customer by userID (200)
- ✅ Invalid Customer ID (400)

## Contact

If issues persist after restart, the problem may be:
1. AWS not pulling the new image
2. Multiple instances running (blue/green deployment)
3. ALB routing to an old instance
4. Autograder caching results
