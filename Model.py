from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import JSON, Boolean
from datetime import datetime
db = SQLAlchemy()
# Models
class MYP(db.Model):
    id    = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    intro = db.Column(db.String(300), nullable=False)
    text  = db.Column(db.Text, nullable=False)
    date  = db.Column(db.DateTime, default=datetime.now)
    teacher = db.Column(db.String(60), nullable=True)
    completed  = db.Column(db.Integer, default=0)
    subject = db.Column(db.String(40), default="No subject")
    grade = db.Column(db.String(10), nullable=True)
    files = db.Column(JSON, nullable=True)

    def __repr__(self):
        return f'<Article {self.id}>'
    
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    user_name = db.Column(db.String(60), nullable=False)
    password = db.Column(db.String(256), nullable=False)
    confirmed = db.Column(Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.now)
    role = db.Column(db.String(50), default='student')
    classes = db.Column(db.JSON, nullable=True)
    def get_classes(self):
        return self.classes or []

    def add_class(self, new_class):
        current = self.get_classes()
        if new_class not in current:
            current.append(new_class)
            self.classes = current

    def __repr__(self):
        return f'<User {self.email}>'
    


class Classes(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    date  = db.Column(db.DateTime, default=datetime.now)
    grade = db.Column(db.String(200), nullable=True)
    students = db.Column(db.JSON, nullable=True)

    def __repr__(self):
        return f'<Article {self.id}>'
    
