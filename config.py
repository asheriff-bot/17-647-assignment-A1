import os

# Only load .env file if not running in Docker (no environment variables set)
if not os.environ.get('MYSQL_HOST') and not os.environ.get('DB_HOST'):
    from dotenv import load_dotenv
    load_dotenv(override=True)

class Config:
    # Database configuration - AWS RDS
    # These should be set via environment variables
    MYSQL_HOST = os.getenv('DB_HOST', os.getenv('MYSQL_HOST', ''))
    MYSQL_PORT = int(os.getenv('DB_PORT', os.getenv('MYSQL_PORT', 3306)))
    MYSQL_USER = os.getenv('DB_USER', os.getenv('MYSQL_USER', 'admin'))
    MYSQL_PASSWORD = os.getenv('DB_PASSWORD', os.getenv('MYSQL_PASSWORD', ''))
    MYSQL_DATABASE = os.getenv('DB_NAME', os.getenv('MYSQL_DATABASE', 'bookstore'))

    # LLM API configuration - should be set via environment variables
    LLM_API_URL = os.getenv('LLM_API_URL', os.getenv('GROQ_API_URL', 'https://api.groq.com/openai/v1/responses'))
    LLM_API_KEY = os.getenv('LLM_API_KEY', os.getenv('GROQ_API_KEY', ''))
    LLM_MODEL = os.getenv('LLM_MODEL', os.getenv('GROQ_LLM_MODEL', 'openai/gpt-oss-20b'))

    # App configuration
    DEBUG = os.getenv('DEBUG', 'False').lower() == 'true'
    BASEURL = os.getenv('BASEURL', 'http://localhost:5000')
