from flask import Flask, render_template, request, redirect, url_for, session
import psycopg2
from datetime import datetime, timedelta
from uuid import uuid4
import html

app = Flask(__name__)
app.secret_key = 'your_secret_key_cs745'

# Database connection
conn = psycopg2.connect(
    dbname="cs745db",
    user="cs745user",
    password="cs745password",
    host="localhost",
    port="5432"
)
cur = conn.cursor()


@app.route('/')
def index():
    if 'email' in session:
        return redirect(url_for('home'))
    else:
        return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        cur.execute("SELECT * FROM users WHERE email = %s AND password = %s", (email, password))
        user = cur.fetchone()
        if user:
            session['email'] = email
            session.permanent = True
            app.permanent_session_lifetime = timedelta(days=1)
            return redirect(url_for('home'))
        else:
            return "Invalid email or password. <a href='/login'>Try again</a>"
    return render_template('login.html')

@app.route('/home', methods=['GET', 'POST'])
def home():
    if 'email' in session:
        if request.method == 'POST':
            content = request.form['content']
            content = html.escape(content, quote=True)
            email = session['email']
            timestamp = datetime.now()
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
