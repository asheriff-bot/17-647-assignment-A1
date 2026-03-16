import pymysql
from pymysql.cursors import DictCursor
from config import Config

class QmarkDictCursor(DictCursor):
    """Cursor that accepts '?' placeholders and forwards %s to MySQL."""

    def _replace_placeholders(self, query):
        if isinstance(query, str) and '?' in query:
            return query.replace('?', '%s')
        return query

    def execute(self, query, args=None):
        query = self._replace_placeholders(query)
        return super().execute(query, args)

    def executemany(self, query, args=None):
        query = self._replace_placeholders(query)
        return super().executemany(query, args)


def get_db_connection():
    """Create and return a database connection."""
    return pymysql.connect(
        host=Config.MYSQL_HOST,
        port=Config.MYSQL_PORT,
        user=Config.MYSQL_USER,
        password=Config.MYSQL_PASSWORD,
        database=Config.MYSQL_DATABASE,
        cursorclass=QmarkDictCursor
    )

def init_db():
    """Initialize the database with tables and sample data."""
    # First connect without database to create it
    conn = pymysql.connect(
        host=Config.MYSQL_HOST,
        port=Config.MYSQL_PORT,
        user=Config.MYSQL_USER,
        password=Config.MYSQL_PASSWORD,
        cursorclass=QmarkDictCursor
    )

    try:
        with conn.cursor() as cursor:
            # Create database if not exists
            cursor.execute(f"CREATE DATABASE IF NOT EXISTS {Config.MYSQL_DATABASE}")
        conn.commit()
    finally:
        conn.close()

    # Now connect to the database and create tables
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            # Create Books table - ISBN as primary key, quantity instead of stock
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
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
                )
            """)

            # Create Customers table - numeric ID as primary key, userId (email) as unique
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS Customers (
                    id INT AUTO_INCREMENT PRIMARY KEY,
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

            # Check if we need to populate with sample data
            cursor.execute("SELECT COUNT(*) as count FROM Books")
            if cursor.fetchone()['count'] == 0:
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
                    "INSERT IGNORE INTO Books (ISBN, title, author, description, genre, price, quantity) VALUES (%s, %s, %s, %s, %s, %s, %s)",
                    sample_books
                )

            # Check if customers need to be populated
            cursor.execute("SELECT COUNT(*) as count FROM Customers")
            if cursor.fetchone()['count'] == 0:
                # Add sample customers
                sample_customers = [
                    ("john.doe@example.com", "John Doe", "+15551234", "123 Main St", "", "New York", "NY", "10001"),
                    ("jane.smith@example.com", "Jane Smith", "+15555678", "456 Oak Ave", "", "Los Angeles", "CA", "90001"),
                    ("bob.johnson@example.com", "Bob Johnson", "+15559012", "789 Pine Rd", "", "Chicago", "IL", "60601"),
                ]
                cursor.executemany(
                    "INSERT IGNORE INTO Customers (userId, name, phone, address, address2, city, state, zipcode) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)",
                    sample_customers
                )

        conn.commit()
    finally:
        conn.close()
