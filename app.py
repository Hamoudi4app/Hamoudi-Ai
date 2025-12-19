import sqlite3
import smtplib
import random
import hashlib
from email.mime.text import MIMEText
from flask import Flask, render_template, request, redirect, session, jsonify
import requests
from datetime import timedelta

app = Flask(__name__)
app.secret_key = "CHANGE_THIS_SECRET_KEY"

# مدة الجلسة الدائمة
app.permanent_session_lifetime = timedelta(days=7)

# ---------------------------------------------------
# مفاتيح — املأها بنفسك
# ---------------------------------------------------
GROQ_API_KEY = "ضع مفتاحك هنا"
SMTP_EMAIL = "hamoudi4app@gmail.com"      # بريد Gmail الذي سيرسل OTP
SMTP_PASSWORD = "ضع كلمة مرور التطبيق هنا"

DB_NAME = "users.db"

# ---------------------------------------------------
# تهيئة قاعدة البيانات
# ---------------------------------------------------
def init_db():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT,
            email TEXT UNIQUE,
            password_hash TEXT
        )
    """)
    conn.commit()
    conn.close()

init_db()

# ---------------------------------------------------
# دوال مساعدة
# ---------------------------------------------------
def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode("utf-8")).hexdigest()

def send_otp_email(to_email: str, otp_code: str):
    subject = "رمز التحقق - Hamoudi AI"
    body = f"رمز التحقق الخاص بك هو: {otp_code}"

    msg = MIMEText(body, "plain", "utf-8")
    msg["Subject"] = subject
    msg["From"] = SMTP_EMAIL
    msg["To"] = to_email

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(SMTP_EMAIL, SMTP_PASSWORD)
        server.send_message(msg)

# ---------------------------------------------------
# تسجيل الدخول
# ---------------------------------------------------
@app.route("/", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        login_type = request.form.get("login_type", "password")

        # تسجيل دخول بكلمة مرور
        if login_type == "password":
            email = request.form.get("email", "").strip().lower()
            password = request.form.get("password", "")

            conn = sqlite3.connect(DB_NAME)
            c = conn.cursor()
            c.execute("SELECT id, username, email, password_hash FROM users WHERE email = ?", (email,))
            user = c.fetchone()
            conn.close()

            if not user:
                return render_template("login.html", error="لا يوجد حساب بهذا البريد.")

            user_id, username, email_db, password_hash_db = user
            if hash_password(password) != password_hash_db:
                return render_template("login.html", error="كلمة المرور غير صحيحة.")

            session["user_id"] = user_id
            session["username"] = username
            session["email"] = email_db
            session.permanent = True

            return redirect("/chat")

        # تسجيل دخول عبر OTP (مفتوح لأي بريد)
        elif login_type == "otp":
            email = request.form.get("email_otp", "").strip().lower()

            conn = sqlite3.connect(DB_NAME)
            c = conn.cursor()
            c.execute("SELECT id, username FROM users WHERE email = ?", (email,))
            user = c.fetchone()

            if not user:
                username = email.split("@")[0]
                c.execute(
                    "INSERT INTO users (username, email, password_hash) VALUES (?, ?, ?)",
                    (username, email, hash_password("temp"))
                )
                conn.commit()
                c.execute("SELECT id, username FROM users WHERE email = ?", (email,))
                user = c.fetchone()

            user_id, username = user
            conn.close()

            otp_code = str(random.randint(100000, 999999))
            session["pending_otp"] = otp_code
            session["pending_email"] = email
            session["pending_user_id"] = user_id
            session["pending_username"] = username

            try:
                send_otp_email(email, otp_code)
            except Exception as e:
                print("OTP Error:", repr(e))
                return render_template("login.html", error="تعذر إرسال رمز التحقق.")

            return redirect("/verify")

    if session.get("user_id"):
        return redirect("/chat")

    return render_template("login.html")

# ---------------------------------------------------
# صفحة التحقق من OTP
# ---------------------------------------------------
@app.route("/verify")
def verify():
    if "pending_email" not in session:
        return redirect("/")
    return render_template("verify.html", email=session.get("pending_email"))

@app.route("/verify_otp", methods=["POST"])
def verify_otp():
    if "pending_email" not in session:
        return redirect("/")

    user_input = request.form.get("otp", "")
    real_otp = session.get("pending_otp")

    if user_input != real_otp:
        return render_template("verify.html", email=session.get("pending_email"), error="رمز غير صحيح.")

    session["user_id"] = session.get("pending_user_id")
    session["username"] = session.get("pending_username")
    session["email"] = session.get("pending_email")
    session.permanent = True

    session.pop("pending_otp", None)
    session.pop("pending_email", None)
    session.pop("pending_user_id", None)
    session.pop("pending_username", None)

    return redirect("/chat")

# ---------------------------------------------------
# صفحة الشات
# ---------------------------------------------------
@app.route("/chat")
def chat():
    if "user_id" not in session:
        return redirect("/")

    email = (session.get("email") or "").lower().encode("utf-8")
    email_hash = hashlib.md5(email).hexdigest()
    profile_image = f"https://www.gravatar.com/avatar/{email_hash}?d=identicon"

    return render_template(
        "index.html",
        username=session.get("username"),
        email=session.get("email"),
        profile_image=profile_image
    )

# ---------------------------------------------------
# API الشات (Groq)
# ---------------------------------------------------
@app.route("/api/chat", methods=["POST"])
def api_chat():
    if "user_id" not in session:
        return jsonify({"error": "غير مصرح"}), 401

    user_message = (request.json.get("message") or "").strip()
    if not user_message:
        return jsonify({"error": "الرسالة فارغة"}), 400

    if not GROQ_API_KEY:
        return jsonify({"error": "API Key غير موجود"}), 500

    try:
        url = "https://api.groq.com/openai/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {GROQ_API_KEY}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": "llama-3.3-70b-versatile",
            "messages": [
                {
                    "role": "system",
                    "content": (
                        "أنت مساعد ذكي اسمه Hamoudi AI، تم تطويرك بواسطة محمد فيصل. "
                        "تجيب دائمًا بالعربية الفصحى بوضوح ومهنية. "
                        "عند سؤال الهوية مثل: من طورك؟ أو من صنعك؟ تؤكد: تم تطويري بواسطة محمد فيصل. "
                        "وعند سؤال الجنسية تجاوب بالنص التالي حرفيًا: جنسية المطور محمد فيصل سوداني. "
                        "وعند سؤال العمر تجاوب بالنص التالي حرفيًا: عمر المطور محمد فيصل 14 سنة. "
                        "وعند سؤال السكن تجاوب بالنص التالي حرفيًا: المطور محمد فيصل سوداني الجنسية ولكنه يعيش في مصر. "
                        "وعند سؤال طريقة التواصل مع المطور، تجاوب بالنص التالي حرفيًا: "
                        "تقدر تتواصل مع المطور محمد فيصل عبر الرابط التالي: https://my-profile-4w23.vercel.app/"
                    )
                },
                {"role": "user", "content": user_message},
            ]
        }

        r = requests.post(url, headers=headers, json=payload, timeout=60)
        r.raise_for_status()

        j = r.json()
        reply = j["choices"][0]["message"]["content"]
        return jsonify({"reply": reply})

    except Exception as e:
        print("Chat Error:", repr(e))
        return jsonify({"error": "حدث خطأ أثناء الاتصال بـ Hamoudi AI."}), 500

# ---------------------------------------------------
# تسجيل الخروج
# ---------------------------------------------------
@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")

# ---------------------------------------------------
# تشغيل السيرفر
# ---------------------------------------------------
if __name__ == "__main__":
    app.run(debug=True)
