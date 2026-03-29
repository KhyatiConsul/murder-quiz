from flask import Flask, request, jsonify, render_template, Response
from contextlib import contextmanager
import psycopg2
from psycopg2.extras import RealDictCursor
import json
import os

app = Flask(__name__,
            template_folder="../templates",
            static_folder="../static")

def get_conn():
    url = os.environ.get("DATABASE_URL")
    if not url:
        raise RuntimeError("DATABASE_URL is not set")
    return psycopg2.connect(url, cursor_factory=RealDictCursor)

@contextmanager
def db(commit=False):
    conn = get_conn()
    cur = conn.cursor()
    try:
        yield cur
        if commit:
            conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        cur.close()
        conn.close()

@app.route("/")
@app.route("/api")
@app.route("/api/")
def index():
    return render_template("index.html")

@app.route("/api/health")
def health():
    try:
        with db() as cur:
            cur.execute("SELECT 1")
        return jsonify({"status": "healthy", "database": "connected"})
    except Exception as e:
        return jsonify({"status": "unhealthy", "error": str(e)}), 503

@app.route("/api/init-db")
def init_db():
    """Run once after first deploy to create the table."""
    try:
        with db(commit=True) as cur:
            cur.execute("""
                CREATE TABLE IF NOT EXISTS quiz_responses (
                    id        SERIAL PRIMARY KEY,
                    name      TEXT NOT NULL,
                    city      TEXT,
                    birthyear INTEGER,
                    nickname  TEXT,
                    traits    JSONB,
                    raw_answers JSONB,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            cur.execute("CREATE INDEX IF NOT EXISTS idx_city      ON quiz_responses(city)")
            cur.execute("CREATE INDEX IF NOT EXISTS idx_nickname  ON quiz_responses(nickname)")
            cur.execute("CREATE INDEX IF NOT EXISTS idx_timestamp ON quiz_responses(timestamp DESC)")
        return jsonify({"status": "ok", "message": "Table ready"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/save", methods=["POST"])
def save():
    data = request.get_json()
    if not data or not data.get("name"):
        return jsonify({"error": "name is required"}), 400

    raw = data.get("raw_answers", {})

    birthyear = None
    if raw.get("birthyear"):
        try:
            birthyear = int(raw["birthyear"])
            if not (1900 <= birthyear <= 2025):
                return jsonify({"error": "birthyear out of range"}), 400
        except ValueError:
            return jsonify({"error": "birthyear must be a number"}), 400

    try:
        with db(commit=True) as cur:
            cur.execute("""
                INSERT INTO quiz_responses (name, city, birthyear, nickname, traits, raw_answers)
                VALUES (%s, %s, %s, %s, %s, %s)
            """, (
                data["name"][:100],
                raw.get("city", "")[:100],
                birthyear,
                data.get("nickname", "")[:200],
                json.dumps(data.get("traits", {})),
                json.dumps(raw)
            ))
        return jsonify({"status": "ok"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

def check_auth():
    pw = request.args.get("pass")
    return pw == os.environ.get("ADMIN_PASSWORD", "key2007")

@app.route("/api/data")
def view_data():
    if not check_auth():
        return jsonify({"error": "Unauthorized"}), 401
    try:
        with db() as cur:
            cur.execute("SELECT * FROM quiz_responses ORDER BY timestamp DESC")
            rows = cur.fetchall()
        return jsonify({"total": len(rows), "data": rows})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/stats")
def stats():
    if not check_auth():
        return jsonify({"error": "Unauthorized"}), 401
    try:
        with db() as cur:
            cur.execute("SELECT COUNT(*) as n FROM quiz_responses")
            total = cur.fetchone()["n"]

            cur.execute("""
                SELECT nickname, COUNT(*) as n FROM quiz_responses
                WHERE nickname IS NOT NULL GROUP BY nickname ORDER BY n DESC
            """)
            by_archetype = {r["nickname"]: r["n"] for r in cur.fetchall()}

            cur.execute("""
                SELECT city, COUNT(*) as n FROM quiz_responses
                WHERE city IS NOT NULL GROUP BY city ORDER BY n DESC LIMIT 20
            """)
            by_city = {r["city"]: r["n"] for r in cur.fetchall()}

        return jsonify({"total": total, "by_archetype": by_archetype, "by_city": by_city})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/export-csv")
def export_csv():
    if not check_auth():
        return jsonify({"error": "Unauthorized"}), 401
    try:
        with db() as cur:
            cur.execute("SELECT * FROM quiz_responses ORDER BY timestamp DESC")
            rows = cur.fetchall()
            cols = [d[0] for d in cur.description]

        lines = [",".join(cols)]
        for row in rows:
            lines.append(",".join(
                f'"{str(v).replace(chr(34), chr(34)*2)}"' if v is not None else ""
                for v in row.values()
            ))

        return Response(
            "\n".join(lines),
            mimetype="text/csv",
            headers={"Content-Disposition": "attachment; filename=quiz_responses.csv"}
        )
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(debug=True, port=int(os.environ.get("PORT", 5000)))