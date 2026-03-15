import os
import sys
import tempfile
from config import Config

# Override database configuration for testing using SQLite
class TestConfig(Config):
    # Use in-memory SQLite for testing
    DATABASE_TYPE = 'sqlite'

    # Create a temporary file for SQLite database
    db_file = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
    SQLITE_DATABASE = db_file.name
    db_file.close()

    TESTING = True


def get_test_db_connection():
    """Create a test database connection using SQLite."""
    import sqlite3
    conn = sqlite3.connect(TestConfig.SQLITE_DATABASE)
    conn.row_factory = sqlite3.Row
    return conn


def init_test_db():
    """Initialize the test database with tables and sample data."""
    conn = get_test_db_connection()
    cursor = conn.cursor()

    # Create Books table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS Books (
            ISBN VARCHAR(20) PRIMARY KEY,
            title VARCHAR(255) NOT NULL,
            author VARCHAR(255) NOT NULL,
            description TEXT,
            genre VARCHAR(100),
            price DECIMAL(10, 2),
            quantity INT DEFAULT 0,
            summary TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Create Customers table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS Customers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            userId VARCHAR(255) UNIQUE NOT NULL,
            name VARCHAR(255) NOT NULL,
            phone VARCHAR(20),
            address VARCHAR(255),
            address2 VARCHAR(255),
            city VARCHAR(100),
            state VARCHAR(2),
            zipcode VARCHAR(20),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Add sample books
    sample_books = [
        ("978-0136886099", "Software Architecture in Practice", "Bass, L.",
         "The definitive guide to architecting modern software", "non-fiction", 59.95, 106),
        ("978-0596007989", "JavaScript: The Good Parts", "Crockford, D.",
         "Most programming languages contain good and bad parts", "programming", 29.99, 15),
        ("978-0201633610", "Design Patterns", "Gamma, E.",
         "Elements of Reusable Object-Oriented Software", "programming", 54.99, 8),
    ]
    cursor.executemany(
        "INSERT OR IGNORE INTO Books (ISBN, title, author, description, genre, price, quantity) VALUES (?, ?, ?, ?, ?, ?, ?)",
        sample_books
    )

    # Add sample customers
    sample_customers = [
        ("john.doe@example.com", "John Doe", "+15551234", "123 Main St", "", "New York", "NY", "10001"),
        ("jane.smith@example.com", "Jane Smith", "+15555678", "456 Oak Ave", "", "Los Angeles", "CA", "90001"),
        ("bob.johnson@example.com", "Bob Johnson", "+15559012", "789 Pine Rd", "", "Chicago", "IL", "60601"),
    ]
    cursor.executemany(
        "INSERT OR IGNORE INTO Customers (userId, name, phone, address, address2, city, state, zipcode) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
        sample_customers
    )

    conn.commit()
    conn.close()