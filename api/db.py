import os
import logging
import psycopg2
import psycopg2.extras
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables from .env file (when running locally)
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)

def get_db_connection():
    """Create a connection to the database."""
    try:
        # Get the DATABASE_URL from environment variables
        database_url = os.getenv('DATABASE_URL')
        if not database_url:
            logging.error("DATABASE_URL environment variable not set")
            return None
            
        # Connect to the database
        conn = psycopg2.connect(database_url)
        conn.autocommit = True
        return conn
    except Exception as e:
        logging.error(f"Database connection error: {e}")
        return None

def get_preferences():
    """Fetch all preferences from the database."""
    conn = get_db_connection()
    if not conn:
        return []
        
    try:
        with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cursor:
            cursor.execute("""
                SELECT user_name, event_date, preference_type 
                FROM preferences 
                ORDER BY event_date, user_name
            """)
            results = [dict(row) for row in cursor.fetchall()]
            
            # Convert date objects to strings for JSON serialization
            for row in results:
                row['event_date'] = row['event_date'].strftime('%Y-%m-%d')
                
            return results
    except Exception as e:
        logging.error(f"Error fetching preferences: {e}")
        return []
    finally:
        conn.close()

def save_preference(user_name, event_date_str, preference_type):
    """Save or update a preference in the database."""
    conn = get_db_connection()
    if not conn:
        return False
        
    try:
        with conn.cursor() as cursor:
            # First try to delete any existing preference for this user and date
            cursor.execute("""
                DELETE FROM preferences
                WHERE user_name = %s AND event_date = %s
            """, (user_name, event_date_str))
            
            # Then insert the new preference
            cursor.execute("""
                INSERT INTO preferences (user_name, event_date, preference_type)
                VALUES (%s, %s, %s)
            """, (user_name, event_date_str, preference_type))
            
        return True
    except Exception as e:
        logging.error(f"Error saving preference: {e}")
        return False
    finally:
        conn.close()

def delete_preference(user_name, event_date_str):
    """Delete a preference from the database."""
    conn = get_db_connection()
    if not conn:
        return False
        
    try:
        with conn.cursor() as cursor:
            cursor.execute("""
                DELETE FROM preferences
                WHERE user_name = %s AND event_date = %s
            """, (user_name, event_date_str))
            
            # Return True if a row was deleted
            return cursor.rowcount > 0
    except Exception as e:
        logging.error(f"Error deleting preference: {e}")
        return False
    finally:
        conn.close()