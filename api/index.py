import os
from flask import Flask, render_template, request, jsonify, session
import calendar
from datetime import datetime
import logging
import traceback

from .db import get_preferences, save_preference, delete_preference, get_db_connection
from .auth import require_admin, auth_bp  # NEW

# Logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

app = Flask(__name__, template_folder='../templates', static_folder='../static')

# --- Session / security config ---
secret_key = os.getenv('SECRET_KEY')
if not secret_key:
    # You can run locally without setting this, but set SECRET_KEY on Vercel!
    logger.warning("SECRET_KEY not set; using a temporary key (NOT for production).")
    secret_key = os.urandom(32)
app.config['SECRET_KEY'] = secret_key
# Secure cookies in prod; allow http for local dev
app.config['SESSION_COOKIE_SECURE'] = os.getenv('FLASK_ENV') != 'development'
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'

# Register auth blueprint
app.register_blueprint(auth_bp)

# Constants
USERS = ["Jack", "Payton", "Nick", "Alyssa"]
MONTHS_YEAR = [(2025, m) for m in range(5, 9)]  # May to August 2025
VALID_PREFERENCES = ['prefer_not', 'no', 'clear']

def get_calendar_data(year, month):
    try:
        calendar.setfirstweekday(6)  # Sunday
        month_calendar = calendar.monthcalendar(year, month)
        month_name = calendar.month_name[month]
        days = [day for week in month_calendar for day in week if day != 0]
        return {"year": year, "month": month, "month_name": month_name, "days": days, "calendar_grid": month_calendar}
    except Exception as e:
        logger.error(f"Error generating calendar data: {e}")
        return None

def process_preferences(raw_preferences):
    processed = {}
    try:
        for pref in raw_preferences:
            event_date = pref['event_date']
            user = pref['user_name']
            ptype = pref['preference_type']
            processed.setdefault(event_date, {})[user] = ptype
    except Exception as e:
        logger.error(f"Error processing preferences: {e}")
    return processed

def validate_date_format(date_str):
    try:
        datetime.strptime(date_str, '%Y-%m-%d')
        return True
    except ValueError:
        return False

@app.route('/')
def index():
    try:
        raw_prefs = get_preferences()
        processed_prefs = process_preferences(raw_prefs)
        calendar_months_data = [get_calendar_data(y, m) for y, m in MONTHS_YEAR]
        # Pass a boolean the client can use to render UI state
        is_admin = bool(session.get("is_admin"))
        return render_template('index.html',
                               users=USERS,
                               preferences=processed_prefs,
                               calendar_months=calendar_months_data,
                               is_admin=is_admin)
    except Exception as e:
        error_details = traceback.format_exc()
        logger.error(f"Error rendering index page: {e}\n{error_details}")
        return "An error occurred loading the page. Please check server logs.", 500

# --- API: READ (public) ---
@app.route('/api/preferences', methods=['GET'])
def get_all_preferences_api():
    try:
        raw_prefs = get_preferences()
        logger.info(f"Successfully fetched {len(raw_prefs)} preferences")
        return jsonify(raw_prefs)
    except Exception as e:
        error_details = traceback.format_exc()
        logger.error(f"Error fetching preferences via API: {e}\n{error_details}")
        return jsonify({"status": "error", "message": "Failed to fetch preferences"}), 500

# --- API: WRITE (protected) ---
@app.route('/api/preferences', methods=['POST'])
@require_admin
def update_preferences():
    data = request.get_json()
    if not data:
        logger.warning("Invalid request body - empty or not JSON")
        return jsonify({"status": "error", "message": "Invalid request body"}), 400

    user_name = data.get('user_name')
    event_date_str = data.get('event_date')
    preference_type = data.get('preference_type')
    logger.info(f"Preference update request: user={user_name}, date={event_date_str}, pref={preference_type}")

    if not user_name:
        return jsonify({"status": "error", "message": "Missing user_name"}), 400
    if user_name not in USERS:
        return jsonify({"status": "error", "message": f"Invalid user_name. Must be one of: {', '.join(USERS)}"}), 400
    if not event_date_str:
        return jsonify({"status": "error", "message": "Missing event_date"}), 400
    if not validate_date_format(event_date_str):
        return jsonify({"status": "error", "message": "Invalid date format. Use YYYY-MM-DD"}), 400
    if preference_type not in VALID_PREFERENCES:
        return jsonify({"status": "error", "message": f"Invalid preference_type. Must be one of: {', '.join(VALID_PREFERENCES)}"}), 400

    try:
        if preference_type == 'clear':
            success = delete_preference(user_name, event_date_str)
            if success:
                logger.info(f"Successfully cleared preference: {user_name}, {event_date_str}")
                return jsonify({"status": "success", "message": "Preference cleared"})
            else:
                logger.info(f"No preference found to clear: {user_name}, {event_date_str}")
                return jsonify({"status": "success", "message": "Preference not found or already clear"})
        else:
            logger.info(f"Attempting to save preference: {user_name}, {event_date_str}, {preference_type}")
            success = save_preference(user_name, event_date_str, preference_type)
            if success:
                logger.info(f"Successfully saved preference: {user_name}, {event_date_str}, {preference_type}")
                return jsonify({"status": "success", "message": "Preference saved"})
            else:
                logger.error(f"Failed to save preference: {user_name}, {event_date_str}, {preference_type}")
                return jsonify({"status": "error", "message": "Failed to save preference to database"}), 500
    except Exception as e:
        error_details = traceback.format_exc()
        logger.error(f"Error processing preference update: {e}\n{error_details}")
        return jsonify({"status": "error", "message": "An internal server error occurred", "error": str(e)}), 500

# --- Utility/diagnostics: protect everything that touches the DB or schema ---
@app.route('/database-status')
@require_admin
def database_status():
    try:
        prefs = get_preferences()
        return jsonify({"status": "connected", "preferences_count": len(prefs), "message": "Database connection successful"})
    except Exception as e:
        return jsonify({"status": "error", "message": f"Database connection error: {str(e)}"}), 500

@app.route('/database-schema')
@require_admin
def database_schema():
    conn = get_db_connection()
    if not conn:
        return jsonify({"status": "error", "message": "Connection failed"}), 500
    try:
        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'preferences')
            """)
            table_exists = cursor.fetchone()[0]
            if not table_exists:
                return jsonify({"status": "error", "message": "Table does not exist"}), 404

            cursor.execute("""
                SELECT column_name, data_type, is_nullable, column_default
                FROM information_schema.columns
                WHERE table_name = 'preferences'
            """)
            columns = [dict(zip(['column_name', 'data_type', 'is_nullable', 'column_default'], row)) for row in cursor.fetchall()]

            cursor.execute("""
                SELECT pgc.conname AS constraint_name, pg_get_constraintdef(pgc.oid) AS constraint_definition
                FROM pg_constraint pgc
                JOIN pg_namespace nsp ON nsp.oid = pgc.connamespace
                JOIN pg_class cls ON pgc.conrelid = cls.oid
                WHERE cls.relname = 'preferences' AND pgc.contype = 'c'
            """)
            check_constraints = [dict(zip(['constraint_name', 'constraint_definition'], row)) for row in cursor.fetchall()]

            cursor.execute("""
                SELECT tc.constraint_name, tc.constraint_type, kcu.column_name
                FROM information_schema.table_constraints tc
                JOIN information_schema.key_column_usage kcu ON tc.constraint_name = kcu.constraint_name
                WHERE tc.table_name = 'preferences'
            """)
            constraints = [dict(zip(['constraint_name', 'constraint_type', 'column_name'], row)) for row in cursor.fetchall()]

            return jsonify({"status": "success", "table_exists": table_exists, "columns": columns,
                            "check_constraints": check_constraints, "constraints": constraints})
    except Exception as e:
        error_details = traceback.format_exc()
        logger.error(f"Error checking schema: {e}\n{error_details}")
        return jsonify({"status": "error", "message": str(e)}), 500
    finally:
        conn.close()

@app.route('/test-insert')
@require_admin
def test_insert():
    conn = get_db_connection()
    if not conn:
        return jsonify({"status": "error", "message": "Connection failed"}), 500
    try:
        with conn.cursor() as cursor:
            cursor.execute("""DELETE FROM preferences WHERE user_name = 'Jack' AND event_date = '2025-05-15'""")
            cursor.execute("""INSERT INTO preferences (user_name, event_date, preference_type) VALUES ('Jack', '2025-05-15', 'prefer_not')""")
            cursor.execute("""SELECT count(*) FROM preferences WHERE user_name = 'Jack' AND event_date = '2025-05-15'""")
            count = cursor.fetchone()[0]
            return jsonify({"status": "success", "message": "Test insert successful", "count": count})
    except Exception as e:
        error_details = traceback.format_exc()
        logger.error(f"Test insert failed: {e}\n{error_details}")
        return jsonify({"status": "error", "message": "Test insert failed", "error": str(e)}), 500
    finally:
        conn.close()

@app.route('/init-database')
@require_admin
def init_database():
    conn = get_db_connection()
    if not conn:
        return jsonify({"status": "error", "message": "Database connection failed"}), 500
    try:
        with conn.cursor() as cursor:
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS preferences (
                    id SERIAL PRIMARY KEY,
                    user_name VARCHAR(50) NOT NULL CHECK (user_name IN ('Jack', 'Payton', 'Nick', 'Alyssa')),
                    event_date DATE NOT NULL,
                    preference_type VARCHAR(20) NOT NULL CHECK (preference_type IN ('prefer_not', 'no')),
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(user_name, event_date)
                )
            """)
            cursor.execute("""
                SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'preferences')
            """)
            table_exists = cursor.fetchone()[0]
            if table_exists:
                return jsonify({"status": "success", "message": "Preferences table created successfully"})
            else:
                return jsonify({"status": "error", "message": "Failed to verify table creation"}), 500
    except Exception as e:
        error_details = traceback.format_exc()
        logger.error(f"Database initialization failed: {e}\n{error_details}")
        return jsonify({"status": "error", "message": "Database initialization failed", "error": str(e)}), 500
    finally:
        conn.close()

# Optional extra route; now protected as well (if you keep it)
@app.route('/tests')
@require_admin
def tests():
    try:
        return render_template('tests.html')
    except Exception as e:
        error_details = traceback.format_exc()
        logger.error(f"Error rendering tests page: {e}\n{error_details}")
        return "An error occurred loading the tests page.", 500

if __name__ == '__main__':
    debug_mode = os.getenv('FLASK_ENV') == 'development'
    logger.info(f"Starting Flask app in {'debug' if debug_mode else 'production'} mode")
    app.run(debug=debug_mode, port=5000)
