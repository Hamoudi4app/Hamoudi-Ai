import sqlite3
import smtplib
import random
import hashlib
from email.mime.text import MIMEText
from flask import Flask, render_template, request, redirect, session, jsonify
import requests
from datetime import timedelta

app = Flask(name)
app.secretkey = "CHANGETHISSECRETKEY"

مدة الجلسة الدائمة
app.permanentsessionlifetime = timedelta(days=7)

---------------------------------------------------

مفاتيح — املأها بنفسك

---------------------------------------------------
GROQAPIKEY = "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"
SMTP_EMAIL = "hamoudi4app@gmail.com"      # بريد Gmail الذي سيرسل OTP
SMTP_PASSWORD = "plai shuq mokq ijdl"

DB_NAME = "users.db"

---------------------------------------------------

تهيئة قاعدة البيانات

---------------------------------------------------
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

---------------------------------------------------

دوال مساعدة

---------------------------------------------------
def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode("utf-8")).hexdigest()

def sendotpemail(toemail: str, otpcode: str):
    subject = "رمز التحقق - Hamoudi AI"
    body = f"رمز التحقق الخاص بك هو: {otp_code}"

    msg = MIMEText(body, "plain", "utf-8")
    msg["Subject"] = subject
    msg["From"] = SMTP_EMAIL
    msg["To"] = to_email

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(SMTPEMAIL, SMTPPASSWORD)
        server.send_message(msg)

---------------------------------------------------

تسجيل الدخول

---------------------------------------------------
@app.route("/", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        logintype = request.form.get("logintype", "password")

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

            userid, username, emaildb, passwordhashdb = user
            if hashpassword(password) != passwordhash_db:
                return render_template("login.html", error="كلمة المرور غير صحيحة.")

            session["userid"] = userid
            session["username"] = username
            session["email"] = email_db
            session.permanent = True

            return redirect("/chat")

        # تسجيل دخول عبر OTP
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
            session["pendingotp"] = otpcode
            session["pending_email"] = email
            session["pendinguserid"] = user_id
            session["pending_username"] = username

            try:
                sendotpemail(email, otp_code)
            except Exception as e:
                print("OTP Error:", repr(e))
                return render_template("login.html", error="تعذر إرسال رمز التحقق.")

            return redirect("/verify")

    if session.get("user_id"):
        return redirect("/chat")

    return render_template("login.html")

---------------------------------------------------

صفحة التحقق من OTP

---------------------------------------------------
@app.route("/verify")
def verify():
    if "pending_email" not in session:
        return redirect("/")
    return rendertemplate("verify.html", email=session.get("pendingemail"))

@app.route("/verify_otp", methods=["POST"])
def verify_otp():
    if "pending_email" not in session:
        return redirect("/")

    user_input = request.form.get("otp", "")
    realotp = session.get("pendingotp")

    if userinput != realotp:
        return rendertemplate("verify.html", email=session.get("pendingemail"), error="رمز غير صحيح.")

    session["userid"] = session.get("pendinguser_id")
    session["username"] = session.get("pending_username")
    session["email"] = session.get("pending_email")
    session.permanent = True

    session.pop("pending_otp", None)
    session.pop("pending_email", None)
    session.pop("pendinguserid", None)
    session.pop("pending_username", None)

    return redirect("/chat")

---------------------------------------------------

صفحة الشات

---------------------------------------------------
@app.route("/chat")
def chat():
    if "user_id" not in session:
        return redirect("/")

    email = (session.get("email") or "").lower().encode("utf-8")
    email_hash = hashlib.md5(email).hexdigest()
    profileimage = f"https://www.gravatar.com/avatar/{emailhash}?d=identicon"

    return render_template(
        "index.html",
        username=session.get("username"),
        email=session.get("email"),
        profileimage=profileimage
    )

---------------------------------------------------

API الشات (Groq) مع هوية وتواصل وجنسية وعمر وسكن

---------------------------------------------------
@app.route("/api/chat", methods=["POST"])
def api_chat():
    if "user_id" not in session:
        return jsonify({"error": "غير مصرح"}), 401

    user_message = (request.json.get("message") or "").strip()
    if not user_message:
        return jsonify({"error": "الرسالة فارغة"}), 400

    if not GROQAPIKEY:
        return jsonify({"error": "API Key غير موجود"}), 500

    try:
        url = "https://api.groq.com/openai/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {GROQAPIKEY}",
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
        r.raiseforstatus()

        j = r.json()
        reply = j["choices"][0]["message"]["content"]
        return jsonify({"reply": reply})

    except Exception as e:
        print("Chat Error:", repr(e))
        return jsonify({"error": "حدث خطأ أثناء الاتصال بـ Hamoudi AI."}), 500

---------------------------------------------------

تسجيل الخروج

---------------------------------------------------
@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")

---------------------------------------------------

تشغيل السيرفر

---------------------------------------------------
if name == "main":
    app.run(debug=True)
