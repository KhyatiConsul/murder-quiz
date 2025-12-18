from flask import Flask, request, jsonify, render_template, Response
import json
import os
import psycopg2
from psycopg2.extras import RealDictCursor
from contextlib import contextmanager

def get_db_connection():
    """
    Create a connection to the PostgreSQL database.
    """
    return psycopg2.connect(os.environ["DATABASE_URL"], sslmode="require")

@contextmanager
def get_db_cursor(commit=False):
    """
    Context manager for database operations.
    Automatically handles connection, cursor, commit/rollback, and cleanup.
    
    Args:
        commit: If True, commits the transaction on success
    """
    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    try:
        yield cursor
        if commit:
            conn.commit()
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        cursor.close()
        conn.close()

def init_db():
    """
    Creates the quiz_responses table if it doesn't exist.
    """
    try:
        with get_db_cursor(commit=True) as cursor:
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS quiz_responses (
                    id SERIAL PRIMARY KEY,
                    name TEXT NOT NULL,
                    city TEXT,
                    birthyear INTEGER,
                    nickname TEXT,
                    traits JSONB,
                    raw_answers JSONB,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            # Create indexes for better query performance
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_nickname ON quiz_responses(nickname)
            ''')
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_city ON quiz_responses(city)
            ''')
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_timestamp ON quiz_responses(timestamp DESC)
            ''')
        print("Database initialized successfully!")
        return True
    except Exception as e:
        print(f"Database initialization error: {e}")
        return False

def validate_quiz_data(data):
    """
    Validates quiz data before saving to database.
    Returns (is_valid, error_message)
    """
    if not isinstance(data, dict):
        return False, "Data must be a dictionary"
    
    # Check required fields
    if not data.get("name"):
        return False, "Name is required"
    
    # Validate name length
    if len(data.get("name", "")) > 100:
        return False, "Name is too long (max 100 characters)"
    
    # Validate birthyear if provided
    raw_answers = data.get("raw_answers", {})
    if raw_answers.get("birthyear"):
        try:
            birthyear = int(raw_answers["birthyear"])
            if birthyear < 1900 or birthyear > 2025:
                return False, "Birth year must be between 1900 and 2025"
        except (ValueError, TypeError):
            return False, "Birth year must be a valid number"
    
    # Validate city length
    if raw_answers.get("city") and len(raw_answers.get("city", "")) > 100:
        return False, "City name is too long (max 100 characters)"
    
    # Validate nickname length
    if data.get("nickname") and len(data.get("nickname", "")) > 100:
        return False, "Nickname is too long (max 100 characters)"
    
    return True, None

def save_to_db(data):
    """
    Saves quiz data into the Postgres DB.
    Returns (success, error_message)
    """
    # Validate data first
    is_valid, error_msg = validate_quiz_data(data)
    if not is_valid:
        return False, error_msg
    
    try:
        with get_db_cursor(commit=True) as cursor:
            cursor.execute('''
                INSERT INTO quiz_responses (name, city, birthyear, nickname, traits, raw_answers)
                VALUES (%s, %s, %s, %s, %s, %s)
            ''', (
                data.get("name", ""),
                data.get("raw_answers", {}).get("city", ""),
                data.get("raw_answers", {}).get("birthyear"),
                data.get("nickname", ""),
                json.dumps(data.get("traits", {})),
                json.dumps(data.get("raw_answers", {}))
            ))
        
        print(f"Saved data for {data.get('name', 'Unknown')}")
        return True, None

    except Exception as e:
        error_msg = f"Database error: {str(e)}"
        print(f"{error_msg}")
        return False, error_msg

def verify_admin_password(password):
    """
    Verifies the admin password from request.
    Returns True if valid, False otherwise.
    """
    admin_password = os.environ.get("ADMIN_PASSWORD", "key2007")
    return password == admin_password

# Flask App
app = Flask(__name__)

@app.route("/")
@app.route("/api")
@app.route("/api/")
def index():
    """Shows the quiz form"""
    return render_template("index.html")

@app.route("/api/init-db")
def initialize_database():
    """
    Manually initialize the database.
    Call this once after first deployment.
    Example: https://your-app.vercel.app/api/init-db
    """
    success = init_db()
    if success:
        return jsonify({"status": "success", "message": "Database initialized!"})
    else:
        return jsonify({"error": "Failed to initialize database"}), 500

@app.route("/api/save", methods=["POST"])
def save_data():
    """
    Receives quiz data from frontend and saves it to DB
    """
    data = request.get_json()
    if not data or not isinstance(data, dict):
        return jsonify({"error": "Invalid data format"}), 400

    success, error_msg = save_to_db(data)
    if success:
        return jsonify({"status": "success", "message": "Data saved successfully!"})
    else:
        return jsonify({"error": error_msg or "Failed to save data"}), 500

@app.route("/api/data")
def view_data():
    """
    View all quiz responses (password protected).
    Example: /api/data?pass=your_password
    """
    password = request.args.get("pass")
    
    if not verify_admin_password(password):
        return jsonify({"error": "Unauthorized"}), 401

    try:
        with get_db_cursor() as cursor:
            cursor.execute('SELECT * FROM quiz_responses ORDER BY timestamp DESC')
            rows = cursor.fetchall()
        
        return jsonify({
            "total_responses": len(rows),
            "data": rows
        })

    except Exception as e:
        return jsonify({"error": f"Error reading data: {str(e)}"}), 500

@app.route("/api/export-csv")
def export_csv():
    """
    Export quiz responses as CSV (password protected).
    Example: /api/export-csv?pass=your_password
    """
    password = request.args.get("pass")
    
    if not verify_admin_password(password):
        return jsonify({"error": "Unauthorized"}), 401

    try:
        with get_db_cursor() as cursor:
            cursor.execute('SELECT * FROM quiz_responses ORDER BY timestamp DESC')
            rows = cursor.fetchall()
            colnames = [desc[0] for desc in cursor.description]

        # Create CSV content
        csv_content = ",".join(colnames) + "\n"
        for row in rows:
            escaped_row = []
            for item in row:
                if item is None:
                    escaped_row.append("")
                else:
                    # Properly escape CSV values
                    str_item = str(item).replace('"', '""')
                    escaped_row.append(f'"{str_item}"')
            csv_content += ",".join(escaped_row) + "\n"

        return Response(
            csv_content,
            mimetype="text/csv",
            headers={"Content-disposition": "attachment; filename=quiz_responses.csv"}
        )

    except Exception as e:
        return jsonify({"error": f"Error exporting data: {str(e)}"}), 500

@app.route("/api/stats")
def get_stats():
    """
    Returns basic statistics about the dataset (password protected).
    Example: /api/stats?pass=your_password
    """
    password = request.args.get("pass")
    
    if not verify_admin_password(password):
        return jsonify({"error": "Unauthorized"}), 401

    try:
        with get_db_cursor() as cursor:
            # Total count
            cursor.execute('SELECT COUNT(*) as count FROM quiz_responses')
            total_count = cursor.fetchone()['count']

            # Nickname distribution
            cursor.execute('''
                SELECT nickname, COUNT(*) as count 
                FROM quiz_responses 
                WHERE nickname IS NOT NULL
                GROUP BY nickname 
                ORDER BY count DESC
            ''')
            nickname_stats = {row['nickname']: row['count'] for row in cursor.fetchall()}

            # City distribution
            cursor.execute('''
                SELECT city, COUNT(*) as count 
                FROM quiz_responses 
                WHERE city IS NOT NULL
                GROUP BY city 
                ORDER BY count DESC 
                LIMIT 10
            ''')
            city_stats = {row['city']: row['count'] for row in cursor.fetchall()}

            # Birth year distribution
            cursor.execute('''
                SELECT birthyear, COUNT(*) as count 
                FROM quiz_responses 
                WHERE birthyear IS NOT NULL
                GROUP BY birthyear 
                ORDER BY birthyear DESC
            ''')
            year_stats = {row['birthyear']: row['count'] for row in cursor.fetchall()}

        return jsonify({
            "total_responses": total_count,
            "nickname_distribution": nickname_stats,
            "top_cities": city_stats,
            "birth_year_distribution": year_stats
        })
        
    except Exception as e:
        return jsonify({"error": f"Error getting stats: {str(e)}"}), 500

@app.route("/api/health")
def health_check():
    """
    Health check endpoint to verify the app and database are working.
    """
    try:
        with get_db_cursor() as cursor:
            cursor.execute('SELECT 1')
        return jsonify({"status": "healthy", "database": "connected"}), 200
    except Exception as e:
        return jsonify({"status": "unhealthy", "error": str(e)}), 503

if __name__ == "__main__":
    # This is for local testing only
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)