import io
import sqlite3
from flask import Flask, render_template, request, redirect, url_for, send_file
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle
from reportlab.lib import colors

app = Flask(__name__)
DB = "users.db"

def get_db_connection():
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            age INTEGER,
            mobile TEXT,
            email TEXT
        )
    """)
    conn.commit()
    conn.close()

init_db()

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/submit", methods=["POST"])
def submit():
    name = request.form["name"]
    age = request.form["age"]
    mobile = request.form["mobile"]
    email = request.form["email"]

    conn = get_db_connection()
    conn.execute(
        "INSERT INTO users (name, age, mobile, email) VALUES (?, ?, ?, ?)",
        (name, age, mobile, email)
    )
    conn.commit()
    conn.close()

    return redirect(url_for("view"))

@app.route("/view")
def view():
    conn = get_db_connection()
    users = conn.execute("SELECT * FROM users").fetchall()
    conn.close()
    return render_template("view.html", users=users)

@app.route("/delete/<int:id>", methods=["POST"])
def delete(id):
    conn = get_db_connection()
    conn.execute("DELETE FROM users WHERE id = ?", (id,))
    conn.commit()
    conn.close()
    return redirect(url_for("view"))

@app.route("/update/<int:id>", methods=["GET", "POST"])
def update(id):
    conn = get_db_connection()
    user = conn.execute("SELECT * FROM users WHERE id = ?", (id,)).fetchone()

    if request.method == "POST":
        name = request.form["name"]
        age = request.form["age"]
        mobile = request.form["mobile"]
        email = request.form["email"]

        conn.execute("""
            UPDATE users SET name = ?, age = ?, mobile = ?, email = ?
            WHERE id = ?
        """, (name, age, mobile, email, id))
        conn.commit()
        conn.close()
        return redirect(url_for("view"))

    conn.close()
    return render_template("update.html", user=user)

@app.route("/download_pdf")
def download_pdf():
    conn = get_db_connection()
    users = conn.execute("SELECT * FROM users").fetchall()
    conn.close()

    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter)

    # Prepare data with headers
    data = [["ID", "Name", "Age", "Mobile", "Email"]]
    for user in users:
        data.append([str(user["id"]), user["name"], str(user["age"]), user["mobile"], user["email"]])

    # Column widths to fit data (adjust if needed)
    col_widths = [40, 120, 40, 120, 180]

    table = Table(data, colWidths=col_widths)

    style = TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#4F81BD')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ])

    table.setStyle(style)

    elements = [table]
    doc.build(elements)

    buffer.seek(0)
    return send_file(buffer, as_attachment=True, download_name="users.pdf", mimetype="application/pdf")

if __name__ == "__main__":
    app.run(debug=True)
