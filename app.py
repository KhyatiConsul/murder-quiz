# Import libraries
from flask import Flask, request, jsonify, render_template, Response
import json
import os
import psycopg2
from psycopg2.extras import RealDictCursor

# Database Helpers

def get_connection():
    """
    Create a connection to the PostgreSQL database using DATABASE_URL env variable.
    Example DATABASE_URL: postgres://user:pass@host:5432/dbname
    """
    return psycopg2.connect(os.environ["DATABASE_URL"], sslmode="require")

def init_db():
    """
    Creates the quiz_responses table if it doesn't exist.
    Runs once on app startup.
    """
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS quiz_responses (
            id SERIAL PRIMARY KEY,
            name TEXT,
            city TEXT,
            birthyear INTEGER,
            nickname TEXT,
            traits JSONB,
            raw_answers JSONB,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()
    print("Database initialized successfully!")

def save_to_db(data):
    """
    Saves quiz data into the Postgres DB.
    Returns True if successful, False otherwise.
    """
    try:
        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute('''
            INSERT INTO quiz_responses (name, city, birthyear, nickname, traits, raw_answers)
            VALUES (%s, %s, %s, %s, %s, %s)
        ''', (
            data.get("name", ""),
            data.get("raw_answers", {}).get("city", ""),
            data.get("raw_answers", {}).get("birthyear", ""),
            data.get("nickname", ""),
            json.dumps(data.get("traits", {})),
            json.dumps(data.get("raw_answers", {}))
        ))

        conn.commit()
        conn.close()
        print(f"✅ Saved data for {data.get('name', 'Unknown')}")
        return True

    except Exception as e:
        print(f"❌ Database error: {e}")
        return False

# Flask App

app = Flask(__name__)

# Initialize DB when app starts
init_db()

@app.route("/")
def index():
    """Shows the quiz form"""
    return render_template("index.html")

@app.route("/save", methods=["POST"])
def save_data():
    """
    Receives quiz data from frontend and saves it to DB
    """
    data = request.get_json()
    if not data or not isinstance(data, dict):
        return jsonify({"error": "Invalid data"}), 400

    success = save_to_db(data)
    if success:
        return jsonify({"status": "success", "message": "Data saved successfully!"})
    else:
        return jsonify({"error": "Failed to save data"}), 500

@app.route("/data")
def view_data():
    """
    View all quiz responses (password protected).
    Example: /data?pass=your_password
    """
    password = request.args.get("pass")
    admin_password = os.environ.get("ADMIN_PASSWORD", "key2007")

    if password != admin_password:
        return jsonify({"error": "Unauthorized"}), 401

    try:
        conn = get_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        cursor.execute('SELECT * FROM quiz_responses ORDER BY timestamp DESC')
        rows = cursor.fetchall()
        conn.close()

        return jsonify({
            "total_responses": len(rows),
            "data": rows
        })

    except Exception as e:
        return jsonify({"error": f"Error reading data: {str(e)}"}), 500

@app.route("/export-csv")
def export_csv():
    """
    Export quiz responses as CSV (password protected).
    """
    password = request.args.get("pass")
    admin_password = os.environ.get("ADMIN_PASSWORD", "key2007")

    if password != admin_password:
        return jsonify({"error": "Unauthorized"}), 401

    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM quiz_responses ORDER BY timestamp DESC')
        rows = cursor.fetchall()
        colnames = [desc[0] for desc in cursor.description]
        conn.close()

        # Create CSV content
        csv_content = ",".join(colnames) + "\n"
        for row in rows:
            escaped_row = []
            for item in row:
                if item is None:
                    escaped_row.append("")
                else:
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

@app.route("/stats")
def get_stats():
    """
    Returns basic statistics about the dataset (password protected).
    """
    password = request.args.get("pass")
    admin_password = os.environ.get("ADMIN_PASSWORD", "key2007")

    if password != admin_password:
        return jsonify({"error": "Unauthorized"}), 401

    try:
        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute('SELECT COUNT(*) FROM quiz_responses')
        total_count = cursor.fetchone()[0]

        cursor.execute('SELECT nickname, COUNT(*) FROM quiz_responses GROUP BY nickname')
        nickname_stats = cursor.fetchall()

        cursor.execute('SELECT city, COUNT(*) FROM quiz_responses GROUP BY city ORDER BY COUNT(*) DESC')
        city_stats = cursor.fetchall()

        cursor.execute('SELECT birthyear, COUNT(*) FROM quiz_responses GROUP BY birthyear ORDER BY birthyear DESC')
        year_stats = cursor.fetchall()

        conn.close()

        return jsonify({
            "total_responses": total_count,
            "nickname_distribution": dict(nickname_stats),
            "top_cities": dict(city_stats[:10]),
            "birth_year_distribution": dict(year_stats)
        })
    except Exception as e:
        return jsonify({"error": f"Error getting stats: {str(e)}"}), 500

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)