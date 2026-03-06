from flask import Flask, render_template, request, redirect, url_for
import mysql.connector
import os
import time

app = Flask(__name__)


def get_db_connection():
    return mysql.connector.connect(
        host=os.getenv("MYSQL_HOST", "mysql"),
        user=os.getenv("MYSQL_USER", "root"),
        password=os.getenv("MYSQL_PASSWORD", "dkagh1."),
        database=os.getenv("MYSQL_DATABASE", "flaskdb")
    )


def init_db():
    max_retries = 10
    delay = 3

    for attempt in range(max_retries):
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS messages (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    username VARCHAR(50) NOT NULL,
                    message VARCHAR(255) NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            conn.commit()
            cursor.close()
            conn.close()
            print("Database initialized successfully.")
            return
        except Exception as e:
            print(f"[{attempt + 1}/{max_retries}] DB connection failed: {e}")
            time.sleep(delay)

    print("Failed to initialize database after retries.")


@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        message = request.form.get("message", "").strip()

        if username and message:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO messages (username, message) VALUES (%s, %s)",
                (username, message)
            )
            conn.commit()
            cursor.close()
            conn.close()

        return redirect(url_for("index"))

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT id, username, message, created_at
        FROM messages
        ORDER BY id DESC
    """)
    messages = cursor.fetchall()
    cursor.close()
    conn.close()

    return render_template("index.html", messages=messages)


@app.route("/health")
def health():
    return {"status": "ok"}, 200


if __name__ == "__main__":
    init_db()
    app.run(host="0.0.0.0", port=5000)
