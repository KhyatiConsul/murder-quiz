# Import the libraries we need
from flask import Flask, request, jsonify, render_template
import json
import sqlite3
import os
from datetime import datetime

# Function to create our database and table
def init_db():
    """
    This function creates our database file and the table to store quiz responses.
    It only runs once when the app starts.
    """
    # Connect to database (creates file if it doesn't exist)
    conn = sqlite3.connect('quiz_data.db')
    cursor = conn.cursor()
    
    # Create table with all the columns we need
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS quiz_responses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            city TEXT,
            birthyear INTEGER,
            nickname TEXT,
            traits TEXT,
            raw_answers TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Save changes and close connection
    conn.commit()
    conn.close()
    print("Database initialized successfully!")

# Function to save quiz data to database
def save_to_db(data):
    """
    This function takes the quiz data and saves it to our SQLite database.
    Returns True if successful, False if there's an error.
    """
    try:
        # Connect to database
        conn = sqlite3.connect('quiz_data.db')
        cursor = conn.cursor()
        
        # Insert new record
        cursor.execute('''
            INSERT INTO quiz_responses (name, city, birthyear, nickname, traits, raw_answers)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (
            data.get("name", ""),
            data.get("raw_answers", {}).get("city", ""),
            data.get("raw_answers", {}).get("birthyear", ""),
            data.get("nickname", ""),
            json.dumps(data.get("traits", {})),  # Convert list to JSON string
            json.dumps(data.get("raw_answers", {}))  # Convert dict to JSON string
        ))
        
        # Save changes and close
        conn.commit()
        conn.close()
        print(f"Successfully saved data for {data.get('name', 'Unknown')}")
        return True
        
    except Exception as e:
        print(f"Database error: {e}")
        return False

# Create Flask app
app = Flask(__name__)

# Initialize database when app starts
init_db()

# Route for the main page
@app.route("/")
def index():
    """Shows the quiz form"""
    return render_template("index.html")

# Route to save quiz responses
@app.route("/save", methods=["POST"])
def save_data():
    """
    This endpoint receives quiz data from the frontend and saves it to database
    """
    # Get the JSON data from the request
    data = request.get_json()
    
    # Check if data is valid
    if not data or not isinstance(data, dict):
        return jsonify({"error": "Invalid data"}), 400
    
    # Try to save to database
    success = save_to_db(data)
    
    if success:
        return jsonify({"status": "success", "message": "Data saved successfully!"})
    else:
        return jsonify({"error": "Failed to save data"}), 500

# Route to view all saved data (protected with password)
@app.route("/data")
def view_data():
    """
    This endpoint lets you view all saved quiz responses.
    You need to provide the password as a URL parameter.
    Example: /data?pass=your_password
    """
    # Get password from URL parameter
    password = request.args.get("pass")
    admin_password = os.environ.get("ADMIN_PASSWORD", "key2007")
    
    # Check password
    if password != admin_password:
        return jsonify({"error": "Unauthorized"}), 401
        
    try:
        # Connect to database
        conn = sqlite3.connect('quiz_data.db')
        cursor = conn.cursor()
        
        # Get all records, newest first
        cursor.execute('SELECT * FROM quiz_responses ORDER BY timestamp DESC')
        rows = cursor.fetchall()
        conn.close()
        
        # Convert database rows to list of dictionaries
        data = []
        for row in rows:
            data.append({
                "id": row[0],
                "name": row[1],
                "city": row[2],
                "birthyear": row[3],
                "nickname": row[4],
                "traits": json.loads(row[5]) if row[5] else {},
                "raw_answers": json.loads(row[6]) if row[6] else {},
                "timestamp": row[7]
            })
        
        return jsonify({
            "total_responses": len(data),
            "data": data
        })
        
    except Exception as e:
        return jsonify({"error": f"Error reading data: {str(e)}"}), 500

# Route to export data as CSV for ML projects
@app.route("/export-csv")
def export_csv():
    """
    This endpoint exports all quiz data as CSV format for machine learning.
    Also requires password protection.
    """
    password = request.args.get("pass")
    admin_password = os.environ.get("ADMIN_PASSWORD", "key2007")
    
    if password != admin_password:
        return jsonify({"error": "Unauthorized"}), 401
    
    try:
        conn = sqlite3.connect('quiz_data.db')
        cursor = conn.cursor()
        
        # Get all data
        cursor.execute('SELECT * FROM quiz_responses ORDER BY timestamp DESC')
        rows = cursor.fetchall()
        conn.close()
        
        # Create CSV content
        csv_content = "id,name,city,birthyear,nickname,traits,raw_answers,timestamp\n"
        
        for row in rows:
            # Escape commas and quotes in data
            escaped_row = []
            for item in row:
                if item is None:
                    escaped_row.append("")
                else:
                    # Convert to string and escape quotes
                    str_item = str(item).replace('"', '""')
                    escaped_row.append(f'"{str_item}"')
            
            csv_content += ",".join(escaped_row) + "\n"
        
        # Return CSV file
        from flask import Response
        return Response(
            csv_content,
            mimetype="text/csv",
            headers={"Content-disposition": "attachment; filename=quiz_responses.csv"}
        )
        
    except Exception as e:
        return jsonify({"error": f"Error exporting data: {str(e)}"}), 500

# Route to get statistics for ML analysis
@app.route("/stats")
def get_stats():
    """
    This endpoint provides basic statistics about your quiz data.
    Useful for understanding your dataset before ML analysis.
    """
    password = request.args.get("pass")
    admin_password = os.environ.get("ADMIN_PASSWORD", "key2007")
    
    if password != admin_password:
        return jsonify({"error": "Unauthorized"}), 401
    
    try:
        conn = sqlite3.connect('quiz_data.db')
        cursor = conn.cursor()
        
        # Get total count
        cursor.execute('SELECT COUNT(*) FROM quiz_responses')
        total_count = cursor.fetchone()[0]
        
        # Get nickname distribution
        cursor.execute('SELECT nickname, COUNT(*) FROM quiz_responses GROUP BY nickname')
        nickname_stats = cursor.fetchall()
        
        # Get city distribution
        cursor.execute('SELECT city, COUNT(*) FROM quiz_responses GROUP BY city ORDER BY COUNT(*) DESC')
        city_stats = cursor.fetchall()
        
        # Get birth year distribution
        cursor.execute('SELECT birthyear, COUNT(*) FROM quiz_responses GROUP BY birthyear ORDER BY birthyear DESC')
        year_stats = cursor.fetchall()
        
        conn.close()
        
        return jsonify({
            "total_responses": total_count,
            "nickname_distribution": dict(nickname_stats),
            "top_cities": dict(city_stats[:10]),  # Top 10 cities
            "birth_year_distribution": dict(year_stats)
        })
        
    except Exception as e:
        return jsonify({"error": f"Error getting stats: {str(e)}"}), 500

# Run the app
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)