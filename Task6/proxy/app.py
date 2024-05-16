from flask import Flask, render_template, request, redirect, url_for, session
import psycopg2
from datetime import datetime, timedelta, timezone
from uuid import uuid4
import html
from cryptography import x509
from cryptography.hazmat.backends import default_backend

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

@app.route('/', methods=['GET', 'POST'])
def index():
    
    if request.method == 'POST':
        client_cert = request.environ.get('SSL_CLIENT_CERT')

        if client_cert:
            try:
                cert = x509.load_pem_x509_certificate(client_cert.encode(), default_backend())
                
            except Exception as e:
                return 'Error validating client certificate.', 400
        else:
            return 'Client certificate not provided.', 400    
