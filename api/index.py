import os
from flask import Flask, render_template, request, jsonify
import calendar
from datetime import date
import logging
from .db import get_preferences, save_preference, delete_preference # Relative import

# Configure logging
logging.basicConfig(level=logging.INFO)

app = Flask(__name__, template_folder='../templates', static_folder='../static')

# Define users and months
USERS = ["Jack", "Payton", "Nick", "Alyssa"]
MONTHS_YEAR = [(2025, m) for m in range(5, 9)] # May to August 2025

def get_calendar_data(year, month):
    """Generates calendar data for a given month and year."""
    month_calendar = calendar.monthcalendar(year, month)
    month_name = calendar.month_name[month]
    # Flatten list and filter out 0s (days not in the month)
    days = [day for week in month_calendar for day in week if day != 0]
    # Get weekday of the 1st day (0=Mon, 6=Sun)
    first_day_weekday = calendar.weekday(year, month, 1)
    return {
        "year": year,
        "month": month,
        "month_name": month_name,
        "days": days,
        "calendar_grid": month_calendar # Pass the grid structure for layout
    }

def process_preferences(raw_preferences):
    """Processes raw db preferences into a nested dict for easier template lookup."""
    processed = {}
    for pref in raw_preferences:
        event_date = pref['event_date']
        user = pref['user_name']
        ptype = pref['preference_type']
        if event_date not in processed:
            processed[event_date] = {}
        processed[event_date][user] = ptype
    return processed


@app.route('/')
def index():
    """Renders the main calendar page."""
    try:
        raw_prefs = get_preferences()
        processed_prefs = process_preferences(raw_prefs)
        
        calendar_months_data = [get_calendar_data(y, m) for y, m in MONTHS_YEAR]
        
        return render_template(
            'index.html', 
            users=USERS, 
            preferences=processed_prefs, 
            calendar_months=calendar_months_data
        )
    except Exception as e:
        logging.error(f"Error rendering index page: {e}")
        return "An error occurred loading the page.", 500

@app.route('/api/preferences', methods=['POST'])
def update_preferences():
    """API endpoint to save or delete preferences."""
    data = request.get_json()
    
    if not data:
        return jsonify({"status": "error", "message": "Invalid request body"}), 400

    user_name = data.get('user_name')
    event_date_str = data.get('event_date')
    preference_type = data.get('preference_type') # can be 'prefer_not', 'no', or 'clear'

    # Basic validation
    if not user_name or user_name not in USERS:
        return jsonify({"status": "error", "message": "Invalid or missing user_name"}), 400
    if not event_date_str:
        return jsonify({"status": "error", "message": "Missing event_date"}), 400
    # Further date validation could be added here
    
    try:
        if preference_type == 'clear':
            # Handle deletion
            success = delete_preference(user_name, event_date_str)
            if success:
                 return jsonify({"status": "success", "message": "Preference cleared"})
            else:
                 # It's okay if nothing was deleted, maybe it wasn't set
                 return jsonify({"status": "success", "message": "Preference not found or already clear"})
        elif preference_type in ['prefer_not', 'no']:
            # Handle saving/updating
            success = save_preference(user_name, event_date_str, preference_type)
            if success:
                return jsonify({"status": "success", "message": "Preference saved"})
            else:
                return jsonify({"status": "error", "message": "Failed to save preference"}), 500
        else:
            return jsonify({"status": "error", "message": "Invalid preference_type"}), 400

    except Exception as e:
        logging.error(f"Error processing preference update: {e}")
        return jsonify({"status": "error", "message": "An internal server error occurred"}), 500

# Route for GET might be useful for JS fetching, but currently handled by Jinja template
@app.route('/api/preferences', methods=['GET'])
def get_all_preferences_api():
     try:
        raw_prefs = get_preferences()
        return jsonify(raw_prefs)
     except Exception as e:
        logging.error(f"Error fetching preferences via API: {e}")
        return jsonify({"status": "error", "message": "Failed to fetch preferences"}), 500

@app.route('/tests')
def tests():
    """Renders the test page."""
    try:
        return render_template('tests.html')
    except Exception as e:
        logging.error(f"Error rendering tests page: {e}")
        return "An error occurred loading the tests page.", 500

# This is needed if running locally with `python api/index.py`
# Vercel uses a WSGI server specified elsewhere
if __name__ == '__main__':
    # Make sure debug=False for production environments
    # Vercel handles the server, this is just for local testing
    app.run(debug=os.getenv('FLASK_ENV') == 'development', port=5000)