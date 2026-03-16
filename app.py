from flask import Flask, request, jsonify, Response, make_response
from flask_cors import CORS
import sys
import os
import re
import threading
import time
from datetime import datetime
from llm_service import generate_book_summary, generate_quote_for_book

# Add the current directory to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Check if we're in test mode
TESTING = os.environ.get('TESTING', 'False').lower() == 'true'

if TESTING:
    from config_test import TestConfig, init_test_db, get_test_db_connection
    Config = TestConfig
else:
    from config import Config
    from database import get_db_connection, init_db

app = Flask(__name__)
CORS(app)

# Initialize database on startup
if TESTING:
    init_test_db()
    def get_db_connection():
        return get_test_db_connection()
else:
    init_db()

# Valid US states
US_STATES = ['AL', 'AK', 'AZ', 'AR', 'CA', 'CO', 'CT', 'DE', 'FL', 'GA',
             'HI', 'ID', 'IL', 'IN', 'IA', 'KS', 'KY', 'LA', 'ME', 'MD',
             'MA', 'MI', 'MN', 'MS', 'MO', 'MT', 'NE', 'NV', 'NH', 'NJ',
             'NM', 'NY', 'NC', 'ND', 'OH', 'OK', 'OR', 'PA', 'RI', 'SC',
             'SD', 'TN', 'TX', 'UT', 'VT', 'VA', 'WA', 'WV', 'WI', 'WY']


# ==================== HELPER FUNCTIONS ====================

def row_to_dict(row):
    """Convert a sqlite3.Row to a dictionary."""
    if row is None:
        return None
    dict_result = {}
    for key in row.keys():
        dict_result[key] = row[key]
    return dict_result


def validate_price(price):
    """Validate that price has at most 2 decimal places."""
    if price is None:
        return True
    price_str = str(price)
    if '.' in price_str:
        decimal_places = len(price_str.split('.')[1])
        return decimal_places <= 2
    return True


def validate_email(email):
    """Validate email format."""
    if email is None:
        return False
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None


def validate_state(state):
    """Validate state is 2-letter US abbreviation."""
    if state is None:
        return False
    return state.upper() in US_STATES


def get_book_metadata_by_isbn(isbn):
    """Fetch book record by ISBN for internal use."""
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM Books WHERE ISBN = ?", (isbn,))
        row = cursor.fetchone()
        return row_to_dict(row)
    finally:
        conn.close()


# ==================== LLM BACKGROUND THREAD ====================

def generate_summary_async(isbn, title, author, description):
    """Generate summary in background thread and update database."""
    try:
        summary = generate_book_summary(title, author, description)

        # Update the book with the summary
        conn = get_db_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("UPDATE Books SET summary = ? WHERE ISBN = ?", (summary, isbn))
            conn.commit()
        finally:
            conn.close()
    except Exception as e:
        print(f"Error generating summary for {isbn}: {e}")


# ==================== BOOK ENDPOINTS ====================

@app.route('/books', methods=['GET'])
def get_all_books():
    """Get all books from the database."""
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM Books")
        rows = cursor.fetchall()
        books = [row_to_dict(row) for row in rows]

        # Convert Decimal to float for JSON serialization
        for book in books:
            if book.get('price'):
                book['price'] = float(book['price'])

        return jsonify(books), 200
    finally:
        conn.close()


@app.route('/books/<isbn>', methods=['GET'])
def get_book_by_isbn(isbn):
    """Get a specific book by ISBN."""
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM Books WHERE ISBN = ?", (isbn,))
        row = cursor.fetchone()

        if row is None:
            return jsonify({"error": "Book not found"}), 404

        book = row_to_dict(row)
        if book.get('price'):
            book['price'] = float(book['price'])

        return jsonify(book), 200
    finally:
        conn.close()


@app.route('/books/isbn/<isbn>', methods=['GET'])
def get_book_by_isbn_alt(isbn):
    """Get a specific book by ISBN (alternative endpoint)."""
    return get_book_by_isbn(isbn)


@app.route('/books', methods=['POST'])
def add_book():
    """Add a new book to the database."""
    data = request.get_json(silent=True)

    if data is None or not isinstance(data, dict):
        return jsonify({"error": "Invalid JSON or missing Content-Type: application/json"}), 400

    # Validate required fields
    required_fields = ['ISBN', 'title', 'author', 'description', 'genre', 'price', 'quantity']
    for field in required_fields:
        if field not in data:
            return jsonify({"error": f"Missing required field: {field}"}), 400

    isbn = data['ISBN']
    title = data['title']
    author = data['author']
    description = data['description']
    genre = data['genre']
    price = data['price']
    quantity = data['quantity']

    # Validate price has at most 2 decimal places
    if not validate_price(price):
        return jsonify({"error": "Price must have at most 2 decimal places"}), 400

    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        # Check if book already exists
        cursor.execute("SELECT ISBN FROM Books WHERE ISBN = ?", (isbn,))
        if cursor.fetchone():
            return jsonify({"message": "This ISBN already exists in the system."}), 422

        # Insert new book with empty summary (will be generated async)
        cursor.execute("""
            INSERT INTO Books (ISBN, title, author, description, genre, price, quantity, summary)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (isbn, title, author, description, genre, price, quantity, ""))

        conn.commit()

        # Return the created book (without summary in POST response)
        cursor.execute("SELECT * FROM Books WHERE ISBN = ?", (isbn,))
        book = row_to_dict(cursor.fetchone())
        if book.get('price'):
            book['price'] = float(book['price'])

        # Trigger async summary generation
        summary_thread = threading.Thread(target=generate_summary_async,
                                           args=(isbn, title, author, description))
        summary_thread.daemon = True
        summary_thread.start()

        # Prepare response with Location header but strip the summary so POST stays quick
        book_response = dict(book)
        book_response.pop('summary', None)
        response = make_response(jsonify(book_response), 201)
        response.headers['Location'] = f'/books/{isbn}'
        return response
    finally:
        conn.close()


@app.route('/books/<isbn>', methods=['PUT'])
def update_book(isbn):
    """Update an existing book."""
    data = request.get_json(silent=True)

    if data is None or not isinstance(data, dict):
        return jsonify({"error": "Invalid JSON or missing Content-Type: application/json"}), 400

    # Validate all required fields are present
    required_fields = ['ISBN', 'title', 'author', 'description', 'genre', 'price', 'quantity']
    for field in required_fields:
        if field not in data:
            return jsonify({"error": f"Missing required field: {field}"}), 400

    # Validate price has at most 2 decimal places
    if not validate_price(data['price']):
        return jsonify({"error": "Price must have at most 2 decimal places"}), 400

    # Ensure ISBN in body matches URL parameter
    if data['ISBN'] != isbn:
        return jsonify({"error": "ISBN in body does not match URL parameter"}), 400

    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        # Check if book exists
        cursor.execute("SELECT * FROM Books WHERE ISBN = ?", (isbn,))
        existing_book_row = cursor.fetchone()

        if existing_book_row is None:
            return jsonify({"error": "Book not found"}), 404

        # Update all fields
        title = data['title']
        author = data['author']
        description = data['description']
        genre = data['genre']
        price = data['price']
        quantity = data['quantity']

        # Get existing summary to preserve it (or regenerate if content changed)
        existing_book = row_to_dict(existing_book_row)
        existing_summary = existing_book.get('summary', '')

        # Only regenerate summary if title, author, or description changed
        summary = existing_summary
        if (title != existing_book['title'] or
            author != existing_book['author'] or
            description != existing_book['description']):
            # Trigger async summary regeneration
            summary_thread = threading.Thread(target=generate_summary_async,
                                               args=(isbn, title, author, description))
            summary_thread.daemon = True
            summary_thread.start()
            summary = existing_summary  # Keep old summary until new one is generated

        cursor.execute("""
            UPDATE Books SET title = ?, author = ?, description = ?, genre = ?,
            price = ?, quantity = ?, summary = ? WHERE ISBN = ?
        """, (title, author, description, genre, price, quantity, summary, isbn))

        conn.commit()

        # Return updated book
        cursor.execute("SELECT * FROM Books WHERE ISBN = ?", (isbn,))
        book = row_to_dict(cursor.fetchone())
        if book.get('price'):
            book['price'] = float(book['price'])

        return jsonify(book), 200
    finally:
        conn.close()


@app.route('/books/<isbn>', methods=['DELETE'])
def delete_book(isbn):
    """Delete a book from the database."""
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        # Check if book exists
        cursor.execute("SELECT * FROM Books WHERE ISBN = ?", (isbn,))
        book = cursor.fetchone()

        if book is None:
            return jsonify({"error": "Book not found"}), 404

        cursor.execute("DELETE FROM Books WHERE ISBN = ?", (isbn,))

        conn.commit()
        return jsonify({"message": "Book deleted successfully"}), 200
    finally:
        conn.close()


# ==================== CUSTOMER ENDPOINTS ====================

@app.route('/customers', methods=['GET'])
def get_customers():
    """Get customers - by userId query param or all customers."""
    userId = request.args.get('userId')

    if userId:
        # Validate email format before querying
        if not validate_email(userId):
            return jsonify({"error": "Invalid email format"}), 400

    conn = get_db_connection()
    try:
        cursor = conn.cursor()

        if userId:
            # Get customer by userId
            cursor.execute("SELECT * FROM Customers WHERE userId = ?", (userId,))
            row = cursor.fetchone()

            if row is None:
                return jsonify({"error": "Customer not found"}), 404

            customer = row_to_dict(row)
            customer.pop('created_at', None)
            return jsonify(customer), 200
        else:
            # Get all customers
            cursor.execute("SELECT * FROM Customers")
            rows = cursor.fetchall()
            customers = [row_to_dict(row) for row in rows]
            # Remove created_at from all customers
            for c in customers:
                c.pop('created_at', None)
            return jsonify(customers), 200
    finally:
        conn.close()


@app.route('/customers/<customer_id>', methods=['GET'])
def get_customer_by_id(customer_id):
    """Get a specific customer by ID."""
    # Validate that customer_id is a positive integer
    try:
        customer_id = int(customer_id)
        if customer_id <= 0:
            return jsonify({"error": "Invalid customer ID"}), 400
    except (ValueError, TypeError):
        return jsonify({"error": "Invalid customer ID"}), 400

    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM Customers WHERE id = ?", (customer_id,))
        row = cursor.fetchone()

        if row is None:
            return jsonify({"error": "Customer not found"}), 404

        customer = row_to_dict(row)
        customer.pop('created_at', None)
        return jsonify(customer), 200
    finally:
        conn.close()


@app.route('/customers', methods=['POST'])
def add_customer():
    """Add a new customer to the database."""
    data = request.get_json(silent=True)

    if data is None or not isinstance(data, dict):
        return jsonify({"error": "Invalid JSON or missing Content-Type: application/json"}), 400

    # Validate required fields (all except address2)
    required_fields = ['userId', 'name', 'phone', 'address', 'city', 'state', 'zipcode']
    for field in required_fields:
        if field not in data:
            return jsonify({"error": f"Missing required field: {field}"}), 400

    userId = data['userId']
    name = data['name']
    phone = data['phone']
    address = data['address']
    address2 = data.get('address2', '')
    city = data['city']
    state = data['state']
    zipcode = data['zipcode']

    # Validate userId is a valid email
    if not validate_email(userId):
        return jsonify({"error": "userId must be a valid email address"}), 400

    # Validate state is 2-letter US abbreviation
    if not validate_state(state):
        return jsonify({"error": "state must be a valid 2-letter US state abbreviation"}), 400

    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        # Check if customer already exists
        cursor.execute("SELECT id FROM Customers WHERE userId = ?", (userId,))
        if cursor.fetchone():
            return jsonify({"message": "This user ID already exists in the system."}), 422

        cursor.execute("""
            INSERT INTO Customers (userId, name, phone, address, address2, city, state, zipcode)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (userId, name, phone, address, address2, city, state.upper(), zipcode))

        conn.commit()

        # Return the created customer with Location header
        cursor.execute("SELECT * FROM Customers WHERE userId = ?", (userId,))
        customer = row_to_dict(cursor.fetchone())

        # Remove created_at from response
        customer.pop('created_at', None)

        response = make_response(jsonify(customer), 201)
        response.headers['Location'] = f'/customers/{customer["id"]}'
        return response
    finally:
        conn.close()


@app.route('/customers/<customer_id>', methods=['PUT'])
def update_customer(customer_id):
    """Update an existing customer."""
    # Validate that customer_id is a positive integer
    try:
        customer_id = int(customer_id)
        if customer_id <= 0:
            return jsonify({"error": "Invalid customer ID"}), 400
    except (ValueError, TypeError):
        return jsonify({"error": "Invalid customer ID"}), 400

    data = request.get_json(silent=True)

    if data is None or not isinstance(data, dict):
        return jsonify({"error": "Invalid JSON or missing Content-Type: application/json"}), 400

    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        # Check if customer exists
        cursor.execute("SELECT * FROM Customers WHERE id = ?", (customer_id,))
        existing_customer_row = cursor.fetchone()

        if existing_customer_row is None:
            return jsonify({"error": "Customer not found"}), 404

        # Build update query dynamically
        update_fields = []
        update_values = []

        if 'userId' in data:
            # Validate email
            if not validate_email(data['userId']):
                return jsonify({"error": "userId must be a valid email address"}), 400
            # Check if new userId is already used by another customer
            cursor.execute("SELECT id FROM Customers WHERE userId = ? AND id != ?",
                           (data['userId'], customer_id))
            if cursor.fetchone():
                return jsonify({"message": "This user ID already exists in the system."}), 422
            update_fields.append("userId = ?")
            update_values.append(data['userId'])

        if 'name' in data:
            update_fields.append("name = ?")
            update_values.append(data['name'])
        if 'phone' in data:
            update_fields.append("phone = ?")
            update_values.append(data['phone'])
        if 'address' in data:
            update_fields.append("address = ?")
            update_values.append(data['address'])
        if 'address2' in data:
            update_fields.append("address2 = ?")
            update_values.append(data['address2'])
        if 'city' in data:
            update_fields.append("city = ?")
            update_values.append(data['city'])
        if 'state' in data:
            if not validate_state(data['state']):
                return jsonify({"error": "state must be a valid 2-letter US state abbreviation"}), 400
            update_fields.append("state = ?")
            update_values.append(data['state'].upper())
        if 'zipcode' in data:
            update_fields.append("zipcode = ?")
            update_values.append(data['zipcode'])

        if not update_fields:
            return jsonify({"error": "No fields to update"}), 400

        update_values.append(customer_id)

        query = f"UPDATE Customers SET {', '.join(update_fields)} WHERE id = ?"
        cursor.execute(query, update_values)

        conn.commit()

        # Return updated customer
        cursor.execute("SELECT * FROM Customers WHERE id = ?", (customer_id,))
        customer = row_to_dict(cursor.fetchone())
        customer.pop('created_at', None)

        return jsonify(customer), 200
    finally:
        conn.close()


@app.route('/customers/<customer_id>', methods=['DELETE'])
def delete_customer(customer_id):
    """Delete a customer from the database."""
    # Validate that customer_id is a positive integer
    try:
        customer_id = int(customer_id)
        if customer_id <= 0:
            return jsonify({"error": "Invalid customer ID"}), 400
    except (ValueError, TypeError):
        return jsonify({"error": "Invalid customer ID"}), 400

    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        # Check if customer exists
        cursor.execute("SELECT * FROM Customers WHERE id = ?", (customer_id,))
        customer = cursor.fetchone()

        if customer is None:
            return jsonify({"error": "Customer not found"}), 404

        cursor.execute("DELETE FROM Customers WHERE id = ?", (customer_id,))

        conn.commit()
        return jsonify({"message": "Customer deleted successfully"}), 200
    finally:
        conn.close()


# ==================== HEALTH CHECK ====================

@app.route('/status', methods=['GET'])
def status_check():
    """Status check endpoint - returns plain text."""
    return Response("OK", mimetype='text/plain'), 200


@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint."""
    return jsonify({"status": "healthy"}), 200


@app.route('/api/greeting', methods=['POST'])
def greeting():
    """Simple greeting endpoint for testing."""
    payload = {}
    if request.content_type == 'application/json':
        payload = request.get_json(silent=True) or {}
    else:
        text = request.get_data(as_text=True).strip()
        if text.upper().startswith('ISBN'):
            parts = text.split(':', 1)
            if len(parts) == 2:
                payload['isbn'] = parts[1].strip()
        elif text:
            payload['name'] = text

    name = payload.get('name') if isinstance(payload, dict) else None
    name = (name.strip() if isinstance(name, str) else None) or 'world'

    isbn = payload.get('isbn') if isinstance(payload, dict) else None
    title = payload.get('title') if isinstance(payload, dict) else None

    if isbn and not title:
        book = get_book_metadata_by_isbn(isbn)
        title = book.get('title') if book else None

    if not title:
        title = 'Unknown Title'
    if not isbn:
        isbn = '0000000000000'

    quote = generate_quote_for_book(title, isbn)
    response_data = {
        'greeting': f'Hello, {name}!',
        'dateTime': datetime.utcnow().isoformat() + 'Z',
        'quote': quote
    }
    return jsonify(response_data), 200


if __name__ == '__main__':
    debug = os.environ.get('DEBUG', 'False').lower() == 'true'
    app.run(host='0.0.0.0', port=5000, debug=debug)
