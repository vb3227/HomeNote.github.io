import flask
from flask import Flask, render_template, url_for, request, redirect, jsonify
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import os

app = Flask(__name__)
app.secret_key = '123456789'
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///database.db"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# Models
class MYP(db.Model):
    id    = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    intro = db.Column(db.String(300), nullable=False)
    text  = db.Column(db.Text, nullable=False)
    date  = db.Column(db.DateTime, default=datetime.now)
    submission = db.Column(db.DateTime, nullable=True)
    completed  = db.Column(db.Integer, default=0)
    grade = db.Column(db.String(10), nullable=True)

    def __repr__(self):
        return f'<Article {self.id}>'
    
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    user_name = db.Column(db.String(60), nullable=False)
    password = db.Column(db.String(60), nullable=False)
    subject = db.Column(db.String(60), nullable=True)
    ip = db.Column(db.String(100), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.now)
    role = db.Column(db.String(50), default='student')

    def __repr__(self):
        return f'<User {self.email}>'
    
    
# Utility CLI command to (re)initialize the database
@app.cli.command('init-db')
def init_db():
    """Initialize or reset the database."""
    db_path = app.config['SQLALCHEMY_DATABASE_URI'].replace('sqlite:///', '')
    if os.path.exists(db_path):
        confirm = input(f"Database file '{db_path}' exists. Delete and recreate? [y/N]: ")
        if confirm.lower() != 'y':
            print("Aborted database initialization.")
            return
        os.remove(db_path)
        print(f"Deleted existing database file '{db_path}'.")
    db.create_all()
    print("Database initialized (tables created). Remember passwords are stored in plain text.")

# Routes for articles/homework
@app.route('/', methods=['GET'])
def index():
    print(f"Request from IP: {request.remote_addr}")
    return render_template('index.html')

@app.route('/info', methods=['GET'])
def show_db():
    articles = MYP.query.order_by(MYP.date.desc()).all()
    return render_template("Info.html", articles=articles)

@app.route('/homework', methods=['GET'])
def show_text():
    text_from_article = MYP.query.order_by(MYP.date.desc()).all()
    return render_template("homework.html", text_from_article=text_from_article)

@app.route('/create', methods=['GET', 'POST'])
def create():
    # user = User.query.filter_by(username=username).first()
    # print(user.role)
    if request.method == "POST":
        title = request.form.get("title")
        intro = request.form.get("intro")
        text  = request.form.get("text")
        grade = request.form.get("grade")

        new_article = MYP(title=title, intro=intro, text=text, grade=grade)
        try:
            db.session.add(new_article)
            db.session.commit()
            return redirect(url_for('show_db'))
        except Exception as e:
            db.session.rollback()
            return f"An error occurred: {e}"

    # GET
    return render_template("create.html")

# User signup/login routes (plain-text passwords)
@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'GET':
        return render_template('signup.html')

    # POST: accept JSON or form data
    if request.is_json:
        data = request.get_json()
        username = data.get('user_name')
        email = data.get('email')
        password = data.get('password')
    else:
        username = request.form.get('user_name')
        email = request.form.get('email')
        password = request.form.get('password')

    if not username or not email or not password:
        return jsonify({'message': 'Username, email, and password required'}), 400

    try:
        existing = User.query.filter_by(email=email).first()
    except Exception as e:
        return jsonify({'message': f"Database error: {e}"}), 500

    if existing:
        return jsonify({'message': 'User already exists'}), 409

    new_user = User(email=email, user_name=username, password=password)
    new_user.ip = request.remote_addr
    try:
        db.session.add(new_user)
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        return jsonify({'message': f'Error creating user: {e}'}), 500

    jsonify({'message': 'User created successfully'}), 201
    redirect(url_for('show_db'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'GET':
        return render_template('login.html')

    # POST: accept JSON or form data
    if request.is_json:
        data = request.get_json()
        email = data.get('email')
        subject = data.get('subject')
        password = data.get('password')
    else:
        email = request.form.get('email')
        subject = request.form.get('subject')
        password = request.form.get('password')

    if not email or not password:
        return jsonify({'message': 'Email and password required'}), 400

    try:
        user = User.query.filter_by(email=email).first()
    except Exception as e:
        return jsonify({'message': f"Database error: {e}"}), 500

    if not user:
        return jsonify({'message': 'User not found'}), 404

    # Optionally verify subject if required:
    # if user.subject and subject and user.subject != subject:
    #     return jsonify({'message': 'Subject mismatch'}), 400

    if user.password != password:
        return jsonify({'message': 'Incorrect password'}), 401

    # TODO: set session or token here for authenticated user
    return jsonify({'message': f"Login successful for {user.user_name}"}), 200

if __name__ == '__main__':
    # If running directly, ensure tables exist
    with app.app_context():
        db.create_all()
    app.run('0.0.0.0', debug=True)