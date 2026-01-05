from Model import db, Classes
from signup import app
with app.app_context():
    db.session.query(Classes).delete()
    db.session.commit()
