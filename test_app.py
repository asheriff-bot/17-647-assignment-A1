import pytest
import json
import sys
import os
import time

# Ensure the Flask app initializes in testing mode so pytest uses the SQLite fixture instead of MySQL.
os.environ.setdefault('TESTING', 'True')

# Add the parent directory to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import app


@pytest.fixture
def client():
    """Create a test client for the Flask app."""
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client


@pytest.fixture
def sample_book():
    """Sample book data for testing."""
    return {
        "ISBN": "978-1234567890",
        "title": "Test Book",
        "author": "Test Author",
        "description": "A test book description",
        "genre": "fiction",
        "price": 19.99,
        "quantity": 5
    }


@pytest.fixture
def sample_customer():
    """Sample customer data for testing."""
    unique_id = int(time.time() * 1000)
    return {
        "userId": f"test_{unique_id}@example.com",
        "name": "Test Customer",
        "phone": "+15550000",
        "address": "123 Test St",
        "address2": "Apt 1",
        "city": "New York",
        "state": "NY",
        "zipcode": "10001"
    }


# ==================== BOOK TESTS ====================

class TestBooks:
    def test_health_check(self, client):
        """Test health check endpoint."""
        response = client.get('/health')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['status'] == 'healthy'

    def test_status_check(self, client):
        """Test status endpoint returns plain text."""
        response = client.get('/status')
        assert response.status_code == 200
        assert response.content_type == 'text/plain; charset=utf-8'
        assert response.data.decode() == 'OK'

    def test_get_all_books(self, client):
        """Test getting all books."""
        response = client.get('/books')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert isinstance(data, list)

    def test_get_book_by_isbn(self, client):
        """Test getting a specific book by ISBN."""
        response = client.get('/books')
        books = json.loads(response.data)

        if len(books) > 0:
            isbn = books[0]['ISBN']
            response = client.get(f'/books/{isbn}')
            assert response.status_code == 200
            data = json.loads(response.data)
            assert data['ISBN'] == isbn

    def test_get_book_by_isbn_alt(self, client):
        """Test getting a specific book by ISBN via /books/isbn/{isbn}."""
        response = client.get('/books')
        books = json.loads(response.data)

        if len(books) > 0:
            isbn = books[0]['ISBN']
            response = client.get(f'/books/isbn/{isbn}')
            assert response.status_code == 200
            data = json.loads(response.data)
            assert data['ISBN'] == isbn

    def test_get_nonexistent_book(self, client):
        """Test getting a book that doesn't exist."""
        response = client.get('/books/000-0000000000')
        assert response.status_code == 404

    def test_add_book(self, client, sample_book):
        """Test adding a new book."""
        response = client.post('/books',
                               data=json.dumps(sample_book),
                               content_type='application/json')
        assert response.status_code == 201
        data = json.loads(response.data)
        assert data['ISBN'] == sample_book['ISBN']
        assert data['title'] == sample_book['title']
        assert 'quantity' in data

    def test_add_book_missing_field(self, client):
        """Test adding a book with missing required fields."""
        incomplete_book = {
            "ISBN": "978-0000000000",
            "title": "Incomplete Book"
            # Missing author, description, genre, price, quantity
        }
        response = client.post('/books',
                               data=json.dumps(incomplete_book),
                               content_type='application/json')
        assert response.status_code == 400

    def test_add_book_invalid_price(self, client):
        """Test adding a book with invalid price (more than 2 decimal places)."""
        invalid_book = {
            "ISBN": "978-0000000001",
            "title": "Invalid Price Book",
            "author": "Test Author",
            "description": "Test description",
            "genre": "fiction",
            "price": 19.999,
            "quantity": 5
        }
        response = client.post('/books',
                               data=json.dumps(invalid_book),
                               content_type='application/json')
        assert response.status_code == 400

    def test_add_duplicate_book(self, client, sample_book):
        """Test adding a book with duplicate ISBN."""
        # Add first book
        client.post('/books',
                    data=json.dumps(sample_book),
                    content_type='application/json')

        # Try to add duplicate
        response = client.post('/books',
                               data=json.dumps(sample_book),
                               content_type='application/json')
        assert response.status_code == 422

    def test_update_book(self, client, sample_book):
        """Test updating an existing book."""
        # First add a book
        client.post('/books',
                    data=json.dumps(sample_book),
                    content_type='application/json')

        # Update the book
        update_data = {
            "ISBN": sample_book['ISBN'],
            "title": "Updated Title",
            "author": sample_book['author'],
            "description": sample_book['description'],
            "genre": sample_book['genre'],
            "price": 29.99,
            "quantity": 10
        }
        response = client.put(f"/books/{sample_book['ISBN']}",
                             data=json.dumps(update_data),
                             content_type='application/json')

        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['title'] == "Updated Title"
        assert float(data['price']) == 29.99
        assert data['quantity'] == 10

    def test_update_book_missing_field(self, client, sample_book):
        """Test updating a book with missing required fields."""
        # First add a book
        client.post('/books',
                    data=json.dumps(sample_book),
                    content_type='application/json')

        # Try to update with missing fields
        update_data = {
            "ISBN": sample_book['ISBN'],
            "title": "Updated Title"
            # Missing other fields
        }
        response = client.put(f"/books/{sample_book['ISBN']}",
                             data=json.dumps(update_data),
                             content_type='application/json')
        assert response.status_code == 400

    def test_update_nonexistent_book(self, client):
        """Test updating a book that doesn't exist."""
        update_data = {
            "ISBN": "000-0000000000",
            "title": "Updated Title",
            "author": "Author",
            "description": "Description",
            "genre": "fiction",
            "price": 19.99,
            "quantity": 5
        }
        response = client.put("/books/000-0000000000",
                             data=json.dumps(update_data),
                             content_type='application/json')
        assert response.status_code == 404

    def test_delete_book(self, client, sample_book):
        """Test deleting a book."""
        # First add a book
        client.post('/books',
                    data=json.dumps(sample_book),
                    content_type='application/json')

        # Delete the book
        response = client.delete(f"/books/{sample_book['ISBN']}")
        assert response.status_code == 200

        # Verify it's deleted
        response = client.get(f"/books/{sample_book['ISBN']}")
        assert response.status_code == 404

    def test_delete_nonexistent_book(self, client):
        """Test deleting a book that doesn't exist."""
        response = client.delete("/books/000-0000000000")
        assert response.status_code == 404


# ==================== CUSTOMER TESTS ====================

class TestCustomers:
    def test_get_all_customers(self, client):
        """Test getting all customers."""
        response = client.get('/customers')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert isinstance(data, list)

    def test_get_customer_by_id(self, client):
        """Test getting a specific customer by ID."""
        response = client.get('/customers')
        customers = json.loads(response.data)

        if len(customers) > 0:
            customer_id = customers[0]['id']
            response = client.get(f'/customers/{customer_id}')
            assert response.status_code == 200
            data = json.loads(response.data)
            assert data['id'] == customer_id

    def test_get_customer_by_userid(self, client):
        """Test getting a specific customer by userId."""
        response = client.get('/customers?userId=john.doe@example.com')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['userId'] == 'john.doe@example.com'

    def test_get_nonexistent_customer(self, client):
        """Test getting a customer that doesn't exist."""
        response = client.get('/customers/99999')
        assert response.status_code == 404

    def test_get_customer_by_nonexistent_userid(self, client):
        """Test getting a customer by non-existent userId."""
        response = client.get('/customers?userId=nonexistent@example.com')
        assert response.status_code == 404

    def test_add_customer(self, client, sample_customer):
        """Test adding a new customer."""
        response = client.post('/customers',
                               data=json.dumps(sample_customer),
                               content_type='application/json')
        assert response.status_code == 201
        data = json.loads(response.data)
        assert data['name'] == sample_customer['name']
        assert data['userId'] == sample_customer['userId']
        assert 'id' in data

    def test_add_customer_missing_field(self, client):
        """Test adding a customer with missing required fields."""
        incomplete_customer = {
            "name": "Incomplete Customer"
            # Missing userId, phone, address, city, state, zipcode
        }
        response = client.post('/customers',
                               data=json.dumps(incomplete_customer),
                               content_type='application/json')
        assert response.status_code == 400

    def test_add_customer_invalid_email(self, client):
        """Test adding a customer with invalid email."""
        invalid_customer = {
            "userId": "invalid-email",
            "name": "Test Customer",
            "phone": "+15550000",
            "address": "123 Test St",
            "city": "New York",
            "state": "NY",
            "zipcode": "10001"
        }
        response = client.post('/customers',
                               data=json.dumps(invalid_customer),
                               content_type='application/json')
        assert response.status_code == 400

    def test_add_customer_invalid_state(self, client):
        """Test adding a customer with invalid state."""
        unique_id = int(time.time() * 1000)
        invalid_customer = {
            "userId": f"test_{unique_id}@example.com",
            "name": "Test Customer",
            "phone": "+15550000",
            "address": "123 Test St",
            "city": "New York",
            "state": "XX",
            "zipcode": "10001"
        }
        response = client.post('/customers',
                               data=json.dumps(invalid_customer),
                               content_type='application/json')
        assert response.status_code == 400

    def test_add_duplicate_customer(self, client, sample_customer):
        """Test adding a customer with duplicate userId."""
        # Add first customer
        client.post('/customers',
                    data=json.dumps(sample_customer),
                    content_type='application/json')

        # Try to add duplicate
        response = client.post('/customers',
                               data=json.dumps(sample_customer),
                               content_type='application/json')
        assert response.status_code == 422

    def test_update_customer(self, client, sample_customer):
        """Test updating an existing customer."""
        # First add a customer
        response = client.post('/customers',
                               data=json.dumps(sample_customer),
                               content_type='application/json')
        created_customer = json.loads(response.data)
        customer_id = created_customer['id']

        # Update the customer
        update_data = {"name": "Updated Name", "phone": "+15559999"}
        response = client.put(f"/customers/{customer_id}",
                             data=json.dumps(update_data),
                             content_type='application/json')

        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['name'] == "Updated Name"
        assert data['phone'] == "+15559999"

    def test_update_nonexistent_customer(self, client):
        """Test updating a customer that doesn't exist."""
        update_data = {"name": "Updated Name"}
        response = client.put("/customers/99999",
                             data=json.dumps(update_data),
                             content_type='application/json')
        assert response.status_code == 404

    def test_delete_customer(self, client, sample_customer):
        """Test deleting a customer."""
        # First add a customer
        response = client.post('/customers',
                               data=json.dumps(sample_customer),
                               content_type='application/json')
        created_customer = json.loads(response.data)
        customer_id = created_customer['id']

        # Delete the customer
        response = client.delete(f"/customers/{customer_id}")
        assert response.status_code == 200

        # Verify it's deleted
        response = client.get(f"/customers/{customer_id}")
        assert response.status_code == 404

    def test_delete_nonexistent_customer(self, client):
        """Test deleting a customer that doesn't exist."""
        response = client.delete("/customers/99999")
        assert response.status_code == 404


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
