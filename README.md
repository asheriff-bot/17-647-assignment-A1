# Bookstore REST API

A Flask-based REST API for managing books and customers in a bookstore system. The application uses MySQL for data persistence and integrates with an LLM service to generate book summaries.

## Table of Contents

- [Technology Stack](#technology-stack)
- [Project Structure](#project-structure)
- [API Endpoints](#api-endpoints)
  - [Book Endpoints](#book-endpoints)
  - [Customer Endpoints](#customer-endpoints)
  - [Health Check](#health-check)
- [Configuration](#configuration)
- [Getting Started](#getting-started)
  - [Prerequisites](#prerequisites)
  - [Local Development](#local-development)
  - [Docker Deployment](#docker-deployment)
- [Data Validation](#data-validation)
- [LLM Integration](#llm-integration)
- [Database Schema](#database-schema)

## Technology Stack

| Component | Technology |
|-----------|------------|
| Web Framework | Flask 3.0.0 |
| Language | Python 3.11 |
| Database | MySQL 8.0 |
| ORM | PyMySQL (raw SQL) |
| API Client | Requests |
| Production Server | Gunicorn 21.2.0 |
| CORS Support | Flask-CORS 4.0.0 |

## Project Structure

```
assign_1_aws/
├── app.py              # Main Flask application with all routes
├── config.py           # Configuration class for database and LLM
├── database.py         # Database connection and schema initialization
├── llm_service.py      # LLM integration for book summaries
├── requirements.txt    # Python dependencies
├── docker-compose.yml  # Docker services (MySQL + Flask app)
├── Dockerfile          # Python container image
├── .env                # Environment variables (local)
├── .env.example        # Environment template
├── mysql/
│   └── init.sql        # MySQL initialization script
└── test_app.py         # Test file
```

## API Endpoints

### Book Endpoints

#### Add Book
```
POST /books
```

Creates a new book in the system. The ISBN serves as the unique identifier. An LLM-generated summary is created asynchronously.

**Request Body:**
```json
{
    "ISBN": "978-0136886099",
    "title": "Software Architecture in Practice",
    "author": "Bass, L.",
    "description": "The definitive guide to architecting modern software",
    "genre": "non-fiction",
    "price": 59.95,
    "quantity": 106
}
```

**Responses:**
- **201 Created**: Book created successfully
  - Header: `Location: /books/{ISBN}`
  - Body: Created book object
- **400 Bad Request**: Invalid or missing input
- **422 Unprocessable Entity**: ISBN already exists

---

#### Update Book
```
PUT /books/{ISBN}
```

Updates an existing book's information.

**Request Body:**
```json
{
    "ISBN": "978-0136886099",
    "title": "Software Architecture in Practice",
    "author": "Bass, L.",
    "description": "The definitive guide to architecting modern software",
    "genre": "non-fiction",
    "price": 59.95,
    "quantity": 99
}
```

**Responses:**
- **200 OK**: Book updated successfully
  - Body: Updated book object
- **400 Bad Request**: Invalid or missing input
- **404 Not Found**: ISBN not found

---

#### Retrieve Book
```
GET /books/{ISBN}
GET /books/isbn/{ISBN}
```

Retrieves a book by its ISBN. Both endpoints return the same response including the LLM-generated summary.

**Responses:**
- **200 OK**: Returns book object with summary
- **404 Not Found**: ISBN not found

**Response Body:**
```json
{
    "ISBN": "978-0136886099",
    "title": "Software Architecture in Practice",
    "author": "Bass, L.",
    "description": "The definitive guide to architecting modern software",
    "genre": "non-fiction",
    "price": 59.95,
    "quantity": 99,
    "summary": "\"Software Architecture in Practice\" is a comprehensive guide..."
}
```

---

#### Get All Books
```
GET /books
```

Retrieves all books in the system.

**Responses:**
- **200 OK**: Returns array of book objects

---

#### Delete Book
```
DELETE /books/{ISBN}
```

Deletes a book from the system.

**Responses:**
- **200 OK**: Book deleted successfully
- **404 Not Found**: ISBN not found

---

### Customer Endpoints

#### Add Customer
```
POST /customers
```

Creates a new customer (self-registration). A unique numeric ID is generated automatically.

**Request Body:**
```json
{
    "userId": "starlord2002@gmail.com",
    "name": "Star Lord",
    "phone": "+14122144122",
    "address": "48 Galaxy Rd",
    "address2": "suite 4",
    "city": "Fargo",
    "state": "ND",
    "zipcode": "58102"
}
```

**Note:** All fields are required except `address2`.

**Responses:**
- **201 Created**: Customer created successfully
  - Header: `Location: /customers/{id}`
  - Body: Created customer object with generated ID
- **400 Bad Request**: Invalid or missing input (invalid email, invalid state)
- **422 Unprocessable Entity**: User ID already exists

---

#### Retrieve Customer by ID
```
GET /customers/{id}
```

Retrieves a customer by their numeric ID.

**Responses:**
- **200 OK**: Returns customer object
- **400 Bad Request**: Invalid ID format
- **404 Not Found**: Customer not found

---

#### Retrieve Customer by User ID
```
GET /customers?userId={userId}
```

Retrieves a customer by their user ID (email address).

**Note:** The `@` character in the email should be URL-encoded (e.g., `userId=starlord2002%40gmail.com`).

**Responses:**
- **200 OK**: Returns customer object
- **400 Bad Request**: Invalid userId format
- **404 Not Found**: Customer not found

---

#### Update Customer
```
PUT /customers/{id}
```

Updates an existing customer's information.

**Responses:**
- **200 OK**: Customer updated successfully
- **400 Bad Request**: Invalid input
- **404 Not Found**: Customer not found
- **422 Unprocessable Entity**: User ID already exists (for another customer)

---

#### Delete Customer
```
DELETE /customers/{id}
```

Deletes a customer from the system.

**Responses:**
- **200 OK**: Customer deleted successfully
- **404 Not Found**: Customer not found

---

### Health Check

#### Status Endpoint
```
GET /status
```

Basic health check endpoint that returns plain text "OK".

**Responses:**
- **200 OK**
  - Header: `Content-Type: text/plain`
  - Body: `OK`

---

#### Health Endpoint
```
GET /health
```

Detailed health check endpoint returning JSON status.

**Responses:**
- **200 OK**
  - Body: `{"status": "healthy"}`

---

## Configuration

Configuration is managed through environment variables. Create a `.env` file based on `.env.example`.

### Database Configuration

| Variable | Description | Default |
|----------|-------------|---------|
| `DB_HOST` | MySQL host | - |
| `DB_PORT` | MySQL port | 3306 |
| `DB_USER` | MySQL username | admin |
| `DB_PASSWORD` | MySQL password | - |
| `DB_NAME` | Database name | bookstore |
| `MYSQL_HOST` | Alternative MySQL host | - |
| `MYSQL_PORT` | Alternative MySQL port | 3306 |
| `MYSQL_USER` | Alternative MySQL user | admin |
| `MYSQL_PASSWORD` | Alternative MySQL password | - |
| `MYSQL_DATABASE` | Alternative database name | bookstore |

### LLM Configuration

| Variable | Description | Default |
|----------|-------------|---------|
| `LLM_API_URL` | LLM API endpoint | https://api.groq.com/openai/v1/responses |
| `LLM_API_KEY` | LLM API key | - |
| `LLM_MODEL` | LLM model name | openai/gpt-oss-20b |
| `GROQ_API_URL` | Alternative LLM API URL | - |
| `GROQ_API_KEY` | Alternative LLM API key | - |
| `GROQ_LLM_MODEL` | Alternative LLM model | - |

### Application Configuration

| Variable | Description | Default |
|----------|-------------|---------|
| `DEBUG` | Enable debug mode | False |
| `BASEURL` | Base URL for the application | http://localhost:5000 |
| `TESTING` | Enable test mode (uses SQLite) | False |

## Getting Started

### Prerequisites

- Python 3.11+
- MySQL 8.0 (or Docker for containerized setup)
- LLM API key (for book summary generation)

### Local Development

1. **Clone the repository and navigate to the project directory**

2. **Create a virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Create environment file**
   ```bash
   cp .env.example .env
   ```

5. **Edit `.env` with your configuration**
   ```
   MYSQL_HOST=localhost
   MYSQL_USER=root
   MYSQL_PASSWORD=your_password
   MYSQL_DATABASE=bookstore
   LLM_API_KEY=your_llm_api_key
   ```

6. **Run the application**
   ```bash
   python app.py
   ```

   The API will be available at `http://localhost:5000`

### Docker Deployment

1. **Build and run with Docker Compose**
   ```bash
   docker-compose up --build
   ```

   This will start:
   - MySQL 8.0 on port 3306
   - Flask application on port 5001

2. **Access the API**
   ```
   http://localhost:5001
   ```

## Data Validation

The API implements the following validation rules:

### Book Validation
- **All fields required**: ISBN, title, author, description, genre, price, quantity
- **Price**: Must be a valid number with 0-2 decimal places
  - Valid: `59.95`, `59`, `59.00`, `59.0`
  - Invalid: `59.001`

### Customer Validation
- **Required fields**: userId, name, phone, address, city, state, zipcode
- **Optional fields**: address2
- **userId**: Must be a valid email address
- **state**: Must be a valid 2-letter US state abbreviation (e.g., CA, NY, TX)

## LLM Integration

When a book is added or updated, the application automatically triggers an asynchronous request to the LLM API to generate a 500-word summary. This happens in a background thread to avoid blocking the API response.

### Summary Generation
- Triggered automatically when adding a new book
- Regenerated when title, author, or description is updated
- Falls back to a placeholder if LLM API is unavailable

### LLM API Requirements
- The application supports any LLM API compatible with the OpenAI chat completion format
- Configure the API URL and key in environment variables
- Model should support text generation with at least 1024 output tokens

## Database Schema

### Books Table

| Column | Type | Constraints |
|--------|------|-------------|
| ISBN | VARCHAR(20) | PRIMARY KEY |
| title | VARCHAR(255) | NOT NULL |
| author | VARCHAR(255) | NOT NULL |
| description | TEXT | - |
| genre | VARCHAR(100) | - |
| price | DECIMAL(10,2) | - |
| quantity | INT | DEFAULT 0 |
| summary | TEXT | - |
| created_at | TIMESTAMP | DEFAULT CURRENT_TIMESTAMP |
| updated_at | TIMESTAMP | AUTO UPDATE CURRENT_TIMESTAMP |

### Customers Table

| Column | Type | Constraints |
|--------|------|-------------|
| id | INT | PRIMARY KEY, AUTO_INCREMENT |
| userId | VARCHAR(255) | UNIQUE, NOT NULL |
| name | VARCHAR(255) | NOT NULL |
| phone | VARCHAR(20) | - |
| address | VARCHAR(255) | - |
| address2 | VARCHAR(255) | - |
| city | VARCHAR(100) | - |
| state | VARCHAR(2) | - |
| zipcode | VARCHAR(20) | - |
| created_at | TIMESTAMP | DEFAULT CURRENT_TIMESTAMP |

---

For questions or issues, please refer to the source code in `app.py` for implementation details.