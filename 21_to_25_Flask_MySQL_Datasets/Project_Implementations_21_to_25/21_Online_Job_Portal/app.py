import os, json
from functools import wraps
from flask import Flask, render_template, request, redirect, url_for, session, flash
import mysql.connector
from werkzeug.security import check_password_hash
from werkzeug.utils import secure_filename

APP_TITLE = "Online Job Portal"
DB_NAME = os.getenv("DB_NAME", "21onlinejobportal")
UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "change-this-local-development-key")
app.config["UPLOAD_FOLDER"] = UPLOAD_DIR

def db():
    return mysql.connector.connect(host=os.getenv("DB_HOST","localhost"),
        user=os.getenv("DB_USER","root"), password=os.getenv("DB_PASSWORD",""),
        database=DB_NAME)

def login_required(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        if not session.get("email"):
            return redirect(url_for("login"))
        return fn(*args, **kwargs)
    return wrapper

def roles(*allowed):
    def deco(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            if not session.get("email"):
                return redirect(url_for("login"))
            if session.get("role") not in allowed:
                flash("You do not have permission for this page.")
                return redirect(url_for("index"))
            return fn(*args, **kwargs)
        return wrapper
    return deco

@app.route("/")
def index():
    q = request.args.get("q","")
    kind = request.args.get("type","")
    con=db(); cur=con.cursor(dictionary=True)
    sql="SELECT * FROM records WHERE status IN ('active','Yes','Approved')"
    params=[]
    if q:
        sql += " AND (title LIKE %s OR location LIKE %s OR category LIKE %s OR description LIKE %s)"
        params += [f"%{q}%"]*4
    if kind:
        sql += " AND record_type=%s"; params.append(kind)
    sql += " ORDER BY created_at DESC"
    cur.execute(sql,params); rows=cur.fetchall()
    cur.close(); con.close()
    return render_template("index.html", title=APP_TITLE, rows=rows, q=q, kind=kind)

@app.route("/register", methods=["GET","POST"])
def register():
    if request.method=="POST":
        from werkzeug.security import generate_password_hash
        name=request.form["name"]; email=request.form["email"].lower().strip()
        role=request.form.get("role","user")
        allowed_roles=["user","director","driver","hospital","mechanic"]
        if role not in allowed_roles: role="user"
        con=db(); cur=con.cursor()
        try:
            cur.execute("INSERT INTO users(name,email,role,password_hash,status) VALUES(%s,%s,%s,%s,%s)",
                (name,email,role,generate_password_hash(request.form["password"]),
                 "pending" if role in ("director","mechanic") else "active"))
            con.commit(); flash("Registration successful. You can log in after approval if required.")
            return redirect(url_for("login"))
        except mysql.connector.Error as e:
            flash("Could not register: "+str(e))
        finally:
            cur.close(); con.close()
    return render_template("form.html", title="Register", fields=["name","email","password"], register=True)

@app.route("/login", methods=["GET","POST"])
def login():
    if request.method=="POST":
        con=db(); cur=con.cursor(dictionary=True)
        cur.execute("SELECT * FROM users WHERE email=%s",(request.form["email"].lower().strip(),))
        user=cur.fetchone(); cur.close(); con.close()
        if user and check_password_hash(user["password_hash"],request.form["password"]):
            if user["status"]=="pending":
                flash("Your account is awaiting admin approval."); return redirect(url_for("login"))
            session.update(email=user["email"],role=user["role"],name=user["name"])
            return redirect(url_for("index"))
        flash("Invalid email or password.")
    return render_template("form.html", title="Login", fields=["email","password"], register=False)

@app.route("/logout")
def logout():
    session.clear(); return redirect(url_for("index"))

@app.route("/add", methods=["GET","POST"])
@login_required
def add_record():
    if request.method=="POST":
        con=db(); cur=con.cursor()
        cur.execute("""INSERT INTO records(record_type,title,category,location,description,contact,owner_email,status,extra_json)
                       VALUES(%s,%s,%s,%s,%s,%s,%s,'active',%s)""",
            (request.form["record_type"],request.form["title"],request.form.get("category"),
             request.form.get("location"),request.form.get("description"),request.form.get("contact"),
             session["email"],json.dumps({})))
        con.commit(); cur.close(); con.close()
        flash("Record posted successfully."); return redirect(url_for("index"))
    return render_template("form.html", title="Add / Post Details",
        fields=["record_type","title","category","location","description","contact"], register=False)

@app.route("/apply/<int:record_id>", methods=["POST"])
@roles("user")
def apply(record_id):
    file=request.files.get("resume")
    filename=None
    if file and file.filename:
        filename=secure_filename(file.filename)
        file.save(os.path.join(app.config["UPLOAD_FOLDER"],filename))
    con=db(); cur=con.cursor()
    try:
        cur.execute("INSERT INTO applications(vacancy_id,applicant_email,resume_filename) VALUES(%s,%s,%s)",
                    (record_id,session["email"],filename))
        con.commit(); flash("Application submitted.")
    except mysql.connector.Error:
        flash("You may have already applied to this listing.")
    finally:
        cur.close(); con.close()
    return redirect(url_for("index"))

@app.route("/save/<int:record_id>", methods=["POST"])
@roles("user")
def save(record_id):
    con=db(); cur=con.cursor()
    cur.execute("INSERT IGNORE INTO saved_items(user_email,record_id) VALUES(%s,%s)",(session["email"],record_id))
    con.commit(); cur.close(); con.close(); flash("Saved.")
    return redirect(url_for("index"))

@app.route("/dashboard")
@login_required
def dashboard():
    con=db(); cur=con.cursor(dictionary=True)
    if session["role"]=="admin":
        cur.execute("SELECT role, COUNT(*) total FROM users GROUP BY role"); stats=cur.fetchall()
        cur.execute("SELECT status, COUNT(*) total FROM records GROUP BY status"); records=cur.fetchall()
        cur.execute("SELECT * FROM users ORDER BY created_at DESC"); users=cur.fetchall()
        cur.close(); con.close()
        return render_template("dashboard.html", title=APP_TITLE, stats=stats, records=records, users=users)
    cur.execute("SELECT * FROM records WHERE owner_email=%s ORDER BY created_at DESC",(session["email"],))
    own=cur.fetchall()
    cur.execute("""SELECT a.*,r.title FROM applications a JOIN records r ON r.id=a.vacancy_id
                   WHERE r.owner_email=%s ORDER BY a.created_at DESC""",(session["email"],))
    apps=cur.fetchall()
    cur.close(); con.close()
    return render_template("dashboard.html", title=APP_TITLE, stats=[], records=[], users=[], own=own, apps=apps)

@app.route("/admin/approve/<int:user_id>", methods=["POST"])
@roles("admin")
def approve(user_id):
    con=db(); cur=con.cursor()
    cur.execute("UPDATE users SET status='active' WHERE id=%s",(user_id,))
    con.commit(); cur.close(); con.close()
    flash("User approved."); return redirect(url_for("dashboard"))

@app.route("/admin/applications")
@roles("admin","director")
def applications():
    con=db(); cur=con.cursor(dictionary=True)
    if session["role"]=="director":
        cur.execute("""SELECT a.*,r.title FROM applications a JOIN records r ON r.id=a.vacancy_id
                       WHERE r.owner_email=%s ORDER BY a.created_at DESC""",(session["email"],))
    else:
        cur.execute("""SELECT a.*,r.title FROM applications a JOIN records r ON r.id=a.vacancy_id
                       ORDER BY a.created_at DESC""")
    rows=cur.fetchall(); cur.close(); con.close()
    return render_template("applications.html", rows=rows, title="Applications")

if __name__=="__main__":
    app.run(debug=True)
