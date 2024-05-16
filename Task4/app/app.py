from flask import Flask, render_template, request, redirect, url_for, session
import psycopg2
from datetime import datetime, timedelta
from uuid import uuid4
import html
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

@app.route('/')
def index():
    if 'email' in session:
        return redirect(url_for('home'))
    else:
        return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if 'email' in session:
        return redirect(url_for('home'))
    
    if request.method == 'POST':
        return redirect('https://10.0.2.11/login?redirect_uri=https://10.0.2.15/login/callback')
    
    return render_template('login.html')

@app.route('/login/callback', methods=['GET'])
def login_callback():

    token = request.args.get('token')

    if token:
        try:
            # Verify the token using the authentication service's secret
            payload = jwt.decode(token, authorization_key, algorithms=['HS256'])

            # Extract user information from the token
            email = str(payload.get('email'))
            cur.execute("SELECT * FROM users WHERE email = %s", (email,))
            user = cur.fetchone()
            if user:
                session['email'] = email
                session.permanent = True
                app.permanent_session_lifetime = timedelta(days=1)
                return redirect(url_for('home'))
            else:
                return "Email not in Database. <a href='/login'>Try again</a>"

        except jwt.ExpiredSignatureError:
            return 'Token expired. Please log in again.', 401
        except jwt.InvalidTokenError:
            return 'Invalid token. Please log in again.', 401
    else:
        return 'Token not provided.', 400

@app.route('/home', methods=['GET', 'POST'])
def home():
    if 'email' in session:
        if request.method == 'POST':
            content = request.form['content']
            email = session['email']
            timestamp = datetime.now()
            content = html.escape(content,quote=True)
            cur.execute("INSERT INTO posts (postid, owner, content, timestamp) VALUES (%s, %s, %s, %s)", (str(uuid4()), email, content, timestamp))
            conn.commit()
            return redirect(url_for('home'))
        
        cur.execute("SELECT * FROM posts ORDER BY timestamp")
        posts = cur.fetchall()
        return render_template('home.html', posts=posts)
    else:
        return redirect(url_for('login'))

@app.route('/posts/<uuid:postid>/delete', methods=['POST'])
def delete_post(postid):
    if 'email' in session:
        cur.execute("SELECT owner FROM posts WHERE postid = %s", (str(postid),))
        post = cur.fetchone()
        if post and post[0] == session['email']:
            cur.execute("DELETE FROM posts WHERE postid = %s", (str(postid),))
            conn.commit()
    return redirect(url_for('home'))
