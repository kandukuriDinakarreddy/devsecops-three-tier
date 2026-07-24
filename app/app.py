from flask import Flask, render_template, request, redirect, url_for, jsonify
import mysql.connector
import os
import time
import json

app = Flask(__name__)

def get_db():
    retries = 10
    while retries:
        try:
            conn = mysql.connector.connect(
                host=os.environ.get("MYSQL_HOST", "mysql"),
                user=os.environ.get("MYSQL_USER", "root"),
                password=os.environ.get("MYSQL_PASSWORD", "root"),
                database=os.environ.get("MYSQL_DB", "devops")
            )
            return conn
        except Exception as e:
            retries -= 1
            print(f"DB not ready, retrying in 5s... ({e})")
            time.sleep(5)
    raise Exception("Could not connect to database")

def init_db():
    conn = get_db()
    cursor = conn.cursor()

    # Create table with new columns (category, author, votes)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS messages (
            id INT AUTO_INCREMENT PRIMARY KEY,
            message VARCHAR(255) NOT NULL,
            category VARCHAR(50) DEFAULT 'announce',
            author VARCHAR(40) DEFAULT 'Anonymous',
            votes INT DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Add columns safely if upgrading from old schema
    for col, definition in [
        ("category", "VARCHAR(50) DEFAULT 'announce'"),
        ("author",   "VARCHAR(40) DEFAULT 'Anonymous'"),
        ("votes",    "INT DEFAULT 0"),
    ]:
        try:
            cursor.execute(f"ALTER TABLE messages ADD COLUMN {col} {definition}")
        except Exception:
            pass  # column already exists

    conn.commit()
    conn.close()

@app.route("/")
def index():
    conn = get_db()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT id, message, category, author, votes, created_at FROM messages ORDER BY created_at DESC")
    messages = cursor.fetchall()
    conn.close()

    # Serialize for JS (convert datetime to string)
    notices_json = []
    for m in messages:
        notices_json.append({
            "id":         m["id"],
            "message":    m["message"],
            "category":   m.get("category") or "announce",
            "author":     m.get("author") or "Anonymous",
            "votes":      m.get("votes") or 0,
            "created_at": m["created_at"].strftime("%Y-%m-%dT%H:%M:%S") if m["created_at"] else "",
        })

    return render_template("index.html", notices_json=notices_json)

@app.route("/add", methods=["POST"])
def add():
    msg      = request.form.get("message", "").strip()
    category = request.form.get("category", "announce").strip()
    author   = request.form.get("author", "").strip() or "Anonymous"

    # Validate category
    valid_cats = {"help", "lost", "event", "announce", "free"}
    if category not in valid_cats:
        category = "announce"

    if msg:
        conn   = get_db()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO messages (message, category, author) VALUES (%s, %s, %s)",
            (msg[:255], category, author[:40])
        )
        conn.commit()
        conn.close()

    return redirect(url_for("index"))

@app.route("/upvote/<int:msg_id>", methods=["POST"])
def upvote(msg_id):
    conn   = get_db()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("UPDATE messages SET votes = votes + 1 WHERE id = %s", (msg_id,))
    conn.commit()
    cursor.execute("SELECT votes FROM messages WHERE id = %s", (msg_id,))
    row = cursor.fetchone()
    conn.close()
    return jsonify({"votes": row["votes"] if row else 0})

@app.route("/health")
def health():
    try:
        conn = get_db()
        conn.close()
        return {"status": "healthy"}, 200
    except Exception as e:
        return {"status": "unhealthy", "error": str(e)}, 500

if __name__ == "__main__":
    print("Waiting for database...")
    time.sleep(10)
    init_db()
    print("Database ready!")
    app.run(host="0.0.0.0", port=5000, debug=True)