from flask import Flask, request, jsonify, render_template
import json

app = Flask(__name__)

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/save", methods=["POST"])
def save_data():
    data = request.get_json()

    with open("quiz_data.json", "r") as file:
        current_data = json.load(file)

    current_data.append(data)

    with open("quiz_data.json", "w") as file:
        json.dump(current_data, file, indent=2)

    return jsonify({"status": "success"})

if __name__ == "__main__":
    import os
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)

from flask import Response

@app.route("/data")
def view_data():
    password = request.args.get("pass")
    if password != "key2007":
        return Response("Unauthorized", status=401)
    try:
        with open("quiz_data.json", "r") as file:
            data = json.load(file)

        return Response(
            json.dumps(data, indent=2),
            mimetype='application/json'
        )
    except Exception as e:
        return Response(f"Error reading data: {str(e)}", status = 500)
