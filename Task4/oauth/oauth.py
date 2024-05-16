from flask import Flask, render_template, request, redirect, url_for, session
import psycopg2
from datetime import timedelta, datetime, timezone
from uuid import uuid4
import jwt

app = Flask(__name__)
app.secret_key = 'your_secret_key_cs745'
authorization_key = 'authorization_key_cs745'

# Database connection
conn = psycopg2.connect(
    dbname="cs745db",
    user="cs745user",
    password="cs745password",
    host="localhost",
    port="5432"
)
cur = conn.cursor()

def generate_csrf_token():
    if 'csrf_token' not in session:
        session['csrf_token'] = str(uuid4())
    return session['csrf_token']

#@app.before_request
def csrf_protect():
    if request.method == "POST":
        token = session.pop('csrf_token',None)
        if not token or token != request.form.get('csrf_token'):
            return "CSRF Attack Detected!!", 403

app.jinja_env.globals['csrf_token'] = generate_csrf_token

@app.route('/login', methods=['GET', 'POST'])
def login():
    if 'redirect_uri' in request.args:
        session['redirect_uri'] = request.args["redirect_uri"]
    
    if 'email' in session:
        if 'redirect_uri' not in session:
            return "redirect_uri missing!!", 400
        else:
            token = jwt.encode({'email': session['email'], 'exp': datetime.now(tz=timezone.utc) + timedelta(days=1)}, authorization_key, algorithm='HS256')

            return redirect(session["redirect_uri"]+'?token={}'.format(token))
            
    if request.method == 'POST':
        
        if 'redirect_uri' not in session:
            return "redirect_uri missing!!", 400
    
        email = request.form['email']
        password = request.form['password']
        cur.execute("SELECT * FROM users WHERE email = %s AND password = %s", (email, password))
        user = cur.fetchone()
        if user:
            session['email'] = email
            session.permanent = True
            app.permanent_session_lifetime = timedelta(days=30)

            token = jwt.encode({'email': email, 'exp': datetime.now(tz=timezone.utc) + timedelta(days=1)}, authorization_key, algorithm='HS256')

            return redirect(session["redirect_uri"]+'?token={}'.format(token))
        else:
            return "Invalid email or password. <a href='/login'>Try again</a>"

    return render_template('login.html')
