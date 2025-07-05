from flask import Flask, request, jsonify
import json
import os

app = Flask(__name__)
DATA_FILE = 'quiz_data.json'

# Load existing data or create empty list
if os.path.exists(DATA_FILE):
    with open(DATA_FILE, 'r') as f:
        all_profiles = json.load(f)
else:
    all_profiles = []

@app.route('/save', methods=['POST'])
def save_profile():
    global all_profiles
    data = request.get_json()

    # Append new profile to the list
    all_profiles.append(data)

    # Save back to JSON file
    with open(DATA_FILE, 'w') as f:
        json.dump(all_profiles, f, indent=2)

    return jsonify({"status": "success", "message": "Profile saved."})

if __name__ == '__main__':
    app.run(debug=True)