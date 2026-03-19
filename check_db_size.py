import os
from urllib.parse import urlparse
from dotenv import load_dotenv
from sqlalchemy import create_engine, text

load_dotenv()
orig_url = os.getenv("DATABASE_URL", "")
orig_db = urlparse(orig_url).path.lstrip("/")
copy_db = orig_db + "_copia"

# Connect to the default 'postgres' database to check sizes safely
admin_url = orig_url.replace(orig_db, "postgres")
engine = create_engine(admin_url)

try:
    with engine.connect() as conn:
        size = conn.execute(text(f"SELECT pg_database_size('{copy_db}')")).scalar()
        size_pretty = conn.execute(text(f"SELECT pg_size_pretty(pg_database_size('{copy_db}'))")).scalar()
        print(f"Database: {copy_db}")
        print(f"Size: {size_pretty} ({size} bytes)")
except Exception as e:
    print(f"Error checking size: {e}")
