from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
import sqlite3, hashlib, os
from functools import wraps

app = Flask(__name__)
app.secret_key = "lnf_secret_key_2025"
DB_PATH = os.path.join(os.path.dirname(__file__), "lost_found.db")


# ── helpers ──────────────────────────────────────────────────────────────────

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn

def hash_pw(pw):
    return hashlib.sha256(pw.encode()).hexdigest()

def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if "user_id" not in session:
            flash("Please log in first.", "warning")
            return redirect(url_for("login"))
        return f(*args, **kwargs)
    return decorated

def admin_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if session.get("role") != "admin":
            flash("Admin access required.", "danger")
            return redirect(url_for("dashboard"))
        return f(*args, **kwargs)
    return decorated


# ── auth ─────────────────────────────────────────────────────────────────────

@app.route("/")
def index():
    if "user_id" in session:
        return redirect(url_for("dashboard"))
    return redirect(url_for("login"))

@app.route("/register", methods=["GET","POST"])
def register():
    if request.method == "POST":
        name  = request.form["name"].strip()
        email = request.form["email"].strip().lower()
        phone = request.form["phone"].strip()
        pw    = request.form["password"]
        db = get_db()
        try:
            db.execute("INSERT INTO USER(Name,Email,Phone,Password) VALUES (?,?,?,?)",
                       (name, email, phone, hash_pw(pw)))
            db.commit()
            flash("Registered successfully! Please log in.", "success")
            return redirect(url_for("login"))
        except sqlite3.IntegrityError:
            flash("Email already registered.", "danger")
        finally:
            db.close()
    return render_template("register.html")

@app.route("/login", methods=["GET","POST"])
def login():
    if request.method == "POST":
        email = request.form["email"].strip().lower()
        pw    = request.form["password"]
        db = get_db()
        user = db.execute("SELECT * FROM USER WHERE Email=? AND Password=?",
                          (email, hash_pw(pw))).fetchone()
        db.close()
        if user:
            session["user_id"] = user["User_ID"]
            session["name"]    = user["Name"]
            session["role"]    = user["Role"]
            return redirect(url_for("dashboard"))
        flash("Invalid credentials.", "danger")
    return render_template("login.html")

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))


# ── dashboard ─────────────────────────────────────────────────────────────────

@app.route("/dashboard")
@login_required
def dashboard():
    db = get_db()
    stats = {
        "total_lost":    db.execute("SELECT COUNT(*) FROM LOST_ITEM").fetchone()[0],
        "total_found":   db.execute("SELECT COUNT(*) FROM FOUND_ITEM").fetchone()[0],
        "total_claimed": db.execute("SELECT COUNT(*) FROM CLAIM WHERE Status='Approved'").fetchone()[0],
        "pending":       db.execute("SELECT COUNT(*) FROM CLAIM WHERE Status='Pending'").fetchone()[0],
    }
    recent_lost = db.execute("""
        SELECT l.*, u.Name as Reporter, c.Category_Name
        FROM LOST_ITEM l JOIN USER u ON l.User_ID=u.User_ID
        LEFT JOIN CATEGORY c ON l.Category_ID=c.Category_ID
        ORDER BY l.Lost_ID DESC LIMIT 5""").fetchall()
    recent_found = db.execute("""
        SELECT f.*, u.Name as Reporter, c.Category_Name
        FROM FOUND_ITEM f JOIN USER u ON f.User_ID=u.User_ID
        LEFT JOIN CATEGORY c ON f.Category_ID=c.Category_ID
        ORDER BY f.Found_ID DESC LIMIT 5""").fetchall()
    db.close()
    return render_template("dashboard.html", stats=stats,
                           recent_lost=recent_lost, recent_found=recent_found)


# ── lost items ────────────────────────────────────────────────────────────────

@app.route("/lost")
@login_required
def lost_items():
    q    = request.args.get("q","")
    cat  = request.args.get("cat","")
    db   = get_db()
    cats = db.execute("SELECT * FROM CATEGORY ORDER BY Category_Name").fetchall()
    query = """
        SELECT l.*, u.Name as Reporter, c.Category_Name
        FROM LOST_ITEM l JOIN USER u ON l.User_ID=u.User_ID
        LEFT JOIN CATEGORY c ON l.Category_ID=c.Category_ID
        WHERE 1=1
    """
    params = []
    if q:
        query += " AND (l.Item_Name LIKE ? OR l.Description LIKE ? OR l.Location LIKE ?)"
        params += [f"%{q}%", f"%{q}%", f"%{q}%"]
    if cat:
        query += " AND l.Category_ID=?"
        params.append(cat)
    query += " ORDER BY l.Lost_ID DESC"
    items = db.execute(query, params).fetchall()
    db.close()
    return render_template("lost_items.html", items=items, cats=cats, q=q, cat=cat)

@app.route("/lost/report", methods=["GET","POST"])
@login_required
def report_lost():
    db = get_db()
    cats = db.execute("SELECT * FROM CATEGORY ORDER BY Category_Name").fetchall()
    if request.method == "POST":
        db.execute("""INSERT INTO LOST_ITEM(Item_Name,Description,Date_Lost,Location,User_ID,Category_ID)
                      VALUES (?,?,?,?,?,?)""",
                   (request.form["item_name"], request.form["description"],
                    request.form["date_lost"], request.form["location"],
                    session["user_id"], request.form["category_id"] or None))
        db.commit()
        db.close()
        flash("Lost item reported successfully.", "success")
        return redirect(url_for("lost_items"))
    db.close()
    return render_template("report_lost.html", cats=cats)


# ── found items ───────────────────────────────────────────────────────────────

@app.route("/found")
@login_required
def found_items():
    q    = request.args.get("q","")
    cat  = request.args.get("cat","")
    db   = get_db()
    cats = db.execute("SELECT * FROM CATEGORY ORDER BY Category_Name").fetchall()
    query = """
        SELECT f.*, u.Name as Reporter, c.Category_Name
        FROM FOUND_ITEM f JOIN USER u ON f.User_ID=u.User_ID
        LEFT JOIN CATEGORY c ON f.Category_ID=c.Category_ID
        WHERE 1=1
    """
    params = []
    if q:
        query += " AND (f.Item_Name LIKE ? OR f.Description LIKE ? OR f.Location LIKE ?)"
        params += [f"%{q}%", f"%{q}%", f"%{q}%"]
    if cat:
        query += " AND f.Category_ID=?"
        params.append(cat)
    query += " ORDER BY f.Found_ID DESC"
    items = db.execute(query, params).fetchall()
    db.close()
    return render_template("found_items.html", items=items, cats=cats, q=q, cat=cat)

@app.route("/found/report", methods=["GET","POST"])
@login_required
def report_found():
    db = get_db()
    cats = db.execute("SELECT * FROM CATEGORY ORDER BY Category_Name").fetchall()
    if request.method == "POST":
        db.execute("""INSERT INTO FOUND_ITEM(Item_Name,Description,Date_Found,Location,User_ID,Category_ID)
                      VALUES (?,?,?,?,?,?)""",
                   (request.form["item_name"], request.form["description"],
                    request.form["date_found"], request.form["location"],
                    session["user_id"], request.form["category_id"] or None))
        db.commit()
        db.close()
        flash("Found item reported successfully.", "success")
        return redirect(url_for("found_items"))
    db.close()
    return render_template("report_found.html", cats=cats)


# ── claims ────────────────────────────────────────────────────────────────────

@app.route("/claims")
@login_required
def claims():
    db = get_db()
    rows = db.execute("""
        SELECT cl.*, l.Item_Name as Lost_Name, f.Item_Name as Found_Name,
               ul.Name as Lost_Reporter, uf.Name as Found_Reporter
        FROM CLAIM cl
        JOIN LOST_ITEM  l  ON cl.Lost_ID  = l.Lost_ID
        JOIN FOUND_ITEM f  ON cl.Found_ID = f.Found_ID
        JOIN USER ul ON l.User_ID = ul.User_ID
        JOIN USER uf ON f.User_ID = uf.User_ID
        ORDER BY cl.Claim_ID DESC
    """).fetchall()
    db.close()
    return render_template("claims.html", claims=rows)

@app.route("/claim/new", methods=["GET","POST"])
@login_required
def new_claim():
    db = get_db()
    if request.method == "POST":
        lost_id  = request.form["lost_id"]
        found_id = request.form["found_id"]
        # check duplicate
        existing = db.execute(
            "SELECT 1 FROM CLAIM WHERE Lost_ID=? AND Found_ID=?", (lost_id, found_id)
        ).fetchone()
        if existing:
            flash("This claim already exists.", "warning")
        else:
            db.execute("INSERT INTO CLAIM(Lost_ID,Found_ID) VALUES (?,?)", (lost_id, found_id))
            db.commit()
            flash("Claim submitted. Awaiting admin approval.", "success")
        db.close()
        return redirect(url_for("claims"))
    lost  = db.execute("SELECT * FROM LOST_ITEM  WHERE Status='Lost'").fetchall()
    found = db.execute("SELECT * FROM FOUND_ITEM WHERE Status='Unclaimed'").fetchall()
    db.close()
    return render_template("new_claim.html", lost_items=lost, found_items=found)

@app.route("/claim/<int:claim_id>/update", methods=["POST"])
@login_required
@admin_required
def update_claim(claim_id):
    status = request.form["status"]
    db = get_db()
    db.execute("UPDATE CLAIM SET Status=? WHERE Claim_ID=?", (status, claim_id))
    db.commit()
    db.close()
    flash(f"Claim {claim_id} updated to {status}.", "success")
    return redirect(url_for("claims"))


# ── admin ─────────────────────────────────────────────────────────────────────

@app.route("/admin")
@login_required
@admin_required
def admin_panel():
    db = get_db()
    users = db.execute("SELECT * FROM USER ORDER BY User_ID").fetchall()
    cat_stats = db.execute("""
        SELECT c.Category_Name,
               COUNT(DISTINCT l.Lost_ID)  as lost_count,
               COUNT(DISTINCT f.Found_ID) as found_count
        FROM CATEGORY c
        LEFT JOIN LOST_ITEM  l ON l.Category_ID = c.Category_ID
        LEFT JOIN FOUND_ITEM f ON f.Category_ID = c.Category_ID
        GROUP BY c.Category_ID
        ORDER BY lost_count DESC
    """).fetchall()
    db.close()
    return render_template("admin.html", users=users, cat_stats=cat_stats)


# ── API (for JS fetch) ────────────────────────────────────────────────────────

@app.route("/api/match/<int:lost_id>")
@login_required
def api_match(lost_id):
    """Return found items that potentially match a lost item (same category)."""
    db = get_db()
    lost = db.execute("SELECT * FROM LOST_ITEM WHERE Lost_ID=?", (lost_id,)).fetchone()
    if not lost:
        return jsonify([])
    matches = db.execute("""
        SELECT f.*, c.Category_Name
        FROM FOUND_ITEM f
        LEFT JOIN CATEGORY c ON f.Category_ID=c.Category_ID
        WHERE f.Category_ID=? AND f.Status='Unclaimed'
    """, (lost["Category_ID"],)).fetchall()
    db.close()
    return jsonify([dict(m) for m in matches])


if __name__ == "__main__":
    app.run(debug=True, port=5000)
