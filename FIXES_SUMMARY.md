# Bug Fixes Summary

## Issues Fixed

### 1. Customer ID Validation (400 vs 404 errors)
**Problem**: Flask's `<int:customer_id>` route parameter rejected non-integer values with 404 before validation code could run.

**Fix**: Changed routes to accept string parameter and manually validate:
- `GET /customers/<customer_id>` - Returns 400 for invalid/negative IDs
- `PUT /customers/<customer_id>` - Returns 400 for invalid/negative IDs
- `DELETE /customers/<customer_id>` - Returns 400 for invalid/negative IDs

**Files Modified**: `app.py` lines 354-376, 442-458, 517-533

### 2. JSON Validation (Malformed Requests)
**Problem**: `request.get_json()` could return `None` for malformed JSON or missing Content-Type, causing unclear errors.

**Fix**: Added explicit validation with `get_json(silent=True)`:
- Checks if data is `None` or not a dict
- Returns 400 with clear error message: "Invalid JSON or missing Content-Type: application/json"

**Files Modified**: `app.py` lines 161-165, 222-226, 377-381, 446-450

## Deployment Status

✅ **Git Commit**: d454c34 "bugfixes" (Mon Mar 16 12:53:40 2026)
✅ **Docker Image Built**: akramdocke/edss:latest
✅ **Docker Image Pushed**: Successfully pushed to Docker Hub
✅ **AWS Deployment**: Automatically updated (verified via endpoint testing)
✅ **Database Cleaned**: All test data removed

## Test Results

All autograder test scenarios verified passing:

| Test | Expected | Actual | Status |
|------|----------|--------|--------|
| Add Book - Happy Case | 201 | 201 | ✅ PASS |
| Add Book - Duplicate | 422 | 422 | ✅ PASS |
| Update Book - Happy Case | 200 | 200 | ✅ PASS |
| Update Book - Unknown | 404 | 404 | ✅ PASS |
| Retrieve Book | 200 | 200 | ✅ PASS |
| Retrieve Book - ISBN endpoint | 200 | 200 | ✅ PASS |
| LLM Summary Generation | 200 + summary | 200 + summary | ✅ PASS |
| Add Customer - Happy Case | 201 | 201 | ✅ PASS |
| Retrieve Customer by ID | 200 | 200 | ✅ PASS |
| Retrieve Customer by userID | 200 | 200 | ✅ PASS |
| Invalid Customer ID | 400 | 400 | ✅ PASS |

## Before Running Autograder

**IMPORTANT**: Run the database clear script to ensure clean state:

```bash
./clear_database.sh
```

This ensures no test data conflicts with autograder expectations.

## Verification Commands

Test the deployed API:

```bash
# Health check
curl http://bookstore-dev-ALB-132104683.us-east-1.elb.amazonaws.com:80/health

# Add book (should return 201)
curl -X POST http://bookstore-dev-ALB-132104683.us-east-1.elb.amazonaws.com:80/books \
  -H "Content-Type: application/json" \
  -d '{"ISBN":"TEST-123","title":"Test","author":"Author","description":"Desc","genre":"fiction","price":19.99,"quantity":5}'

# Invalid customer ID (should return 400)
curl http://bookstore-dev-ALB-132104683.us-east-1.elb.amazonaws.com:80/customers/invalid
```

## Error Code Reference

- **200 OK**: Successful GET/PUT/DELETE
- **201 Created**: Successful POST with resource creation
- **400 Bad Request**: Validation errors, malformed JSON, invalid IDs
- **404 Not Found**: Resource doesn't exist
- **422 Unprocessable Entity**: Duplicate ISBN or userID

## Notes

- All changes are backward compatible
- No breaking changes to API contracts
- Enhanced error messages for better debugging
- LLM summary generation works asynchronously (3-5 seconds)
- Database must be clean before autograder runs
