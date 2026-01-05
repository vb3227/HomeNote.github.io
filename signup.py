import flask
from flask import Flask, render_template, url_for, request, redirect, jsonify, flash, url_for, abort
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import os
from sqlalchemy.orm.attributes import flag_modified
import os
from flask import Flask, request, redirect, url_for, render_template, send_file
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import LoginManager, login_user, login_required, logout_user, current_user
from UserLogin import UserLogin
from Get import Get
from Model import User, MYP, Classes, db
from flask_mail import Mail, Message
from itsdangerous import URLSafeTimedSerializer
from confirm import confirmed_required


app = Flask(__name__)

app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USE_SSL'] = False
app.config['MAIL_USERNAME'] = 'vanya2010b@gmail.com'
app.config['MAIL_PASSWORD'] = 'jpsdbsvgkjqeykca'

mail = Mail(app)

app.secret_key = '123456789'
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///database.db"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

app.config["UPLOAD_FOLDER"] = "uploads"
UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), "uploads")
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Разрешённые расширения
ALLOWED_EXTENSIONS = {'pdf', 'docx', 'png', 'jpg', 'jpeg', 'zip', 'pptx'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

db.init_app(app)
login_manager = LoginManager(app)

login_manager.login_view = "login"


def generate_confirmation_token(email):
    serializer = URLSafeTimedSerializer(app.config['SECRET_KEY'])
    return serializer.dumps(email, salt='email-confirm-salt')

def confirm_token(token, expiration=3600):
    serializer = URLSafeTimedSerializer(app.config['SECRET_KEY'])
    try:
        email = serializer.loads(token, salt='email-confirm-salt', max_age=expiration)
    except:
        return False
    return email


@login_manager.user_loader
def load_user(user_id):
    userlogin = UserLogin().fromDB(user_id)
    return userlogin

def Loged():
    loged = current_user.get_id()
    user = User.query.filter_by(id=loged).first()
    try:
        loged = user.role
    except Exception as e:
        print("User is not in his account!")
        return None
    return loged

class DBHelper:
    def __init__(self, db_session):
        self.db_session = db_session

    def ConfirmUser(self, email):
        existing_user = self.db_session.query(User).filter_by(email=email).first()
        if existing_user:
            return "user already exists!"
        existing_user.confirmed = True
        self.db_session.add(existing_user)
        self.db_session.commit()

        # return "confirmation_required"

    def checkUser(self, user_name, email, hash):
        try:
            existing_user = self.db_session.query(User).filter_by(email=email).first()
            if existing_user:
                return False
                
            send_confirmation_email(email)
            new_user = User(
                email=email,
                user_name=user_name,
                password=hash,
                created_at=datetime.now(),
                role='student'
            )
            self.db_session.add(new_user)
            self.db_session.commit()
            print("User added successfully, confirmation required")
            return True
        except Exception as e:
            self.db_session.rollback()
            print(f"Something went wrong: {e}")
            return False
    def confirmUser(self, email):
        try:
            user = self.db_session.query(User).filter_by(email=email).first()
            user.confirmed = True
            self.db_session.add(user)
            self.db_session.commit()
            print("User confirmed successefully!")
            return True
        except Exception as e:
            self.db_session.rollback()
            print(f"Something went wrong: {e}")
            return False

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
    return render_template('index.html', loged=Loged())

@app.route('/info/<subject>', methods=['GET'])
@login_required
@confirmed_required
def sorting(subject):
    USER_ID = current_user.get_id()
    user = User.query.filter_by(id=int(USER_ID)).first()
    gtt = f"_{USER_ID}"
    if user.role == "teacher":
        homework_list = MYP.query.order_by(MYP.date.desc()).filter_by(grade=subject+gtt).all()
        print(subject)
        print(homework_list)
        all_homework = MYP.query.order_by(MYP.date.desc()).filter_by(teacher=user.user_name).all()
    else:
        homework_list = MYP.query.order_by(MYP.date.desc()).filter_by(subject=subject).all()
        all_homework = MYP.query.order_by(MYP.date.desc()).all()

    return render_template("Sorted_hw.html", homework=homework_list, user=user, loged=Loged(), gtt=gtt, all_homework=all_homework)

@app.route('/info', methods=['GET'])
@login_required
@confirmed_required
def show_db():
    homework = MYP.query.order_by(MYP.date.desc()).all()
    USER_ID = current_user.get_id()
    user = User.query.filter_by(id=int(USER_ID)).first()
    homework_for_teacher = MYP.query.order_by(MYP.date.desc()).filter_by(teacher=user.user_name).all()
    gtt = f"_{USER_ID}"
    subjects_list = []
    
    if user.classes == None:
        return render_template("Info.html", homework=homework, user=user, loged=Loged(), homework_for_teacher=homework_for_teacher, gtt=gtt)

    if user.role == "teacher":
        print(homework_for_teacher)
    else:
        homework_for_teacher = None
        gtt = None

    print(subjects_list)
    return render_template("Info.html", homework=homework, user=user, loged=Loged(), homework_for_teacher=homework_for_teacher, gtt=gtt, subjects_list=subjects_list)

@app.route('/homework', methods=['GET'])
@login_required
@confirmed_required
def show_text():
    return render_template("homework.html")

@app.route('/info/<int:homework_id>', methods=["GET"])
@login_required
@confirmed_required
def homework_detail(homework_id):
    text_from_article = MYP.query.filter_by(id=homework_id).first()
    return render_template('homework.html', homework=text_from_article, loged=Loged())

@app.route("/download/<filename>", methods=["GET"])
@login_required
@confirmed_required
def download_file(filename):
    safe_name = secure_filename(filename)
    path = os.path.join(UPLOAD_FOLDER, safe_name)
    if os.path.exists(path):
        return send_file(path, as_attachment=True)
    else:
        abort(404)

@app.route('/create', methods=['GET', 'POST'])
@login_required
@confirmed_required
def create():

    IDD = current_user.get_id()
    respawn = User.query.filter_by(id=IDD).first()
    if respawn.role == "student":
        abort(403)

    gtt = f"_{IDD}"

    classes = []
    for c in Classes.query.all():
        if c.grade.endswith(gtt):
            classes.append(c)
            
    if request.method == "POST":
        files_name = []
        title = request.form.get("title")
        intro = request.form.get("intro")
        text  = request.form.get("text")
        grade = request.form.get("grade")
        subject = request.form.get("subject")
        teacher = User.query.filter_by(id=IDD).first().user_name
        if 'files' not in request.files:
            pass
        else:
            file = request.files['files']
            if file and allowed_file(file.filename):
                os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
                # Путь для сохранения
                files = request.files.getlist('files')
                for file in files:
                    file.save(os.path.join(app.config['UPLOAD_FOLDER'], secure_filename(file.filename)))
                    files_name.append(secure_filename(file.filename))
            else:
                file_path = None

        new_article = MYP(title=title, intro=intro, text=text, grade=grade, teacher=teacher, files=files_name, subject=subject)
        try:
            db.session.add(new_article)
            db.session.commit()
            print("START SENDING EMAILS")
            print(new_article.grade)
            print(User.classes.contains(new_article.grade))
            print(f"Students: {User.query.filter(User.classes.contains(new_article.grade)).all()}")
            for student in User.query.filter(User.classes.contains(new_article.grade)).all():
                print(f"""student_email: {student.email}
                      homework_title: {new_article.title}
                        teacher_name: {new_article.teacher}""")
                send_homework_notification(student_email=student.email, homework_title=new_article.title, teacher_name=new_article.teacher)
                print(student.email)
            return redirect(url_for('show_db'))
        except Exception as e:
            db.session.rollback()
            print("error")
            return f"An error occurred: {e}"

    # GET
    return render_template("create.html", classes=classes, loged=Loged(), gtt=gtt)

def send_homework_notification(student_email, homework_title, teacher_name):
    print("sending the message...")
    msg = Message(
        subject=f"New homework task: {homework_title}",
        sender=app.config["MAIL_USERNAME"],
        recipients=[student_email]
    )
    msg.body = f"""
    HomeNote Message

    Teacher: {teacher_name} created a new task called: {homework_title}.

    Please, enter the website to check details.

    HomeNote
    """
    mail.send(msg)
    print(f"Message sent to the email: {student_email}")


@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == "POST":
        if request.form['password'] == request.form['password2'] and len(request.form['email']) > 4:
            hash = generate_password_hash(request.form['password'])
            DBHelper_object = DBHelper(db.session)
            res = DBHelper_object.checkUser(request.form['user_name'], request.form['email'], hash)
            if res:
                flash("Successful registration! Check your email to confirm your account.", "success")
                return redirect(url_for('login'))
            else:
                flash("This email already exists! Choose another one", "error")
                return render_template("signup.html")
        else:
            flash("Field confirm password or email filled wrong!", "error")
            return render_template("signup.html")
    return render_template("signup.html")


def send_confirmation_email(user_email):
    token = generate_confirmation_token(user_email)
    confirm_url = url_for('confirm_email', token=token, _external=True)
    html = f'<p>Welcome to HomeNote! Click to confirm your email: <a href="{confirm_url}">{confirm_url}</a></p>'
    msg = Message(subject="Please confirm your email",
                  recipients=[user_email],
                  html=html,
                  sender=app.config['MAIL_USERNAME'])
    mail.send(msg)


@app.route('/confirm/<token>')
def confirm_email(token):
    email = confirm_token(token)
    if not email:
        flash('The confirmation link is invalid or has expired.', 'danger')
        return redirect(url_for('login'))
    DBHelper_object = DBHelper(db.session)
    user = Get().getUserByEmail(email)
    if not user.confirmed:
        DBHelper_object.confirmUser(email)  # метод для установки confirmed=True
        flash('You have confirmed your account. Thanks!', 'success')
    else:
        flash('Account already confirmed.', 'success')
    return redirect(url_for('login'))


@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated and current_user.confirmed == True:
        return redirect(url_for("profile"))
    if request.method == "POST":
        email = request.form["email"]
        user = Get().getUserByEmail(email)
        if not user:
            flash('Please confirm your email first.', 'warning')
            return redirect(url_for('login'))
        if not user.confirmed:
            flash('Please confirm your email first.', 'warning')
            return redirect(url_for('login'))
        if user and check_password_hash(user.password, request.form["password"]):
            userlogin = UserLogin().make(user)
            rm = True if request.form.get("remainme") else False
            login_user(userlogin, remember=rm)
            return redirect(request.args.get("next") or url_for("profile"))


    return render_template('login.html', loged=Loged())

@app.route('/logout')
@login_required
@confirmed_required
def logout():
    logout_user()
    flash("I have succesefully loged out!", "success")
    return redirect(url_for('login'))

@app.route("/profile", methods=["GET"])
@login_required
@confirmed_required
def profile():
    user_id = current_user.get_id()
    user = User.query.filter_by(id=user_id).first()
    return render_template("profile.html", user_name=user_id, loged=Loged(), user=user)


@app.route('/delete_class/<int:class_id>', methods=['POST'])
@login_required
@confirmed_required
def delete_class(class_id):
    class_to_delete = Classes.query.get_or_404(class_id)

    # Finish later!
    users_in_classes = class_to_delete.students
    for student in users_in_classes:
        user = User.query.filter_by(user_name=student).first()
        h = user.classes
        h_index = h.index(class_to_delete.grade)
        h.pop(h_index)
        add = User(user_name=user.user_name, classes=h)
        flag_modified(add,'classes')
        db.session.commit()
    try:
        db.session.delete(class_to_delete)
        db.session.commit()
        flash("Class has been succesefully deleted!", "success")
    except Exception as e:
        db.session.rollback()
        flash("Something went wrong", "error")

    return redirect(url_for("Classes_for_teacher"))


@app.route("/Classes", methods=["POST","GET"])
@login_required
@confirmed_required
def Classes_for_teacher():
    kklasses = []
    IDD = current_user.get_id()
    gtt = f"_{IDD}"
    respawn = User.query.filter_by(id=IDD).first()
    if respawn.role == "student":
        abort(403)
    students = User.query.all()
    Klasses = Classes.query.all()
    for klass in Klasses:
        name = klass.grade
        before, after = name.split("_", 1)
        after = f"_{after}"
        if after == gtt:
            kklasses.append(klass)
    return render_template("Classes.html", students=students, Klasses=kklasses, loged=Loged(), gtt=gtt)


students_to_add = dict()

@app.route("/Classes/add_class", methods=["POST","GET"])
@login_required
@confirmed_required
def CreateClass():
    IDD = current_user.get_id()
    respawn = User.query.filter_by(id=IDD).first()
    if respawn.role == "student":
        abort(403)
    students_raw = User.query.all()

    # сериализуем для шаблона (id и имя)
    students = [{'id': s.id, 'name': s.user_name} for s in students_raw]

    idd = str(current_user.get_id())

    if request.method == "POST":
        student_ids = request.form.getlist("students[]")
        for ID in student_ids:
            class_name = request.form.get("class_name")
            user = User.query.filter_by(id=int(ID)).first()
            if not user:
                flash("Student not found", "error")
                return render_template("ClassCreation.html", students=students, loged=Loged())

            NAME = user.user_name
            class_name = class_name + str(f"_{idd}")
            try:
                if NAME in students_to_add.get(class_name):
                    flash(f"Sorry, but student {NAME} has been added to the class before", "error")
                else:
                    students_to_add[class_name].append(NAME)
                    flash(f"{NAME} was added to the class: {class_name}.", "success")
                    Get_object = Get()
                    Get_object.Tag(class_name, NAME)
            except:
                students_to_add[class_name] = [NAME]
                Get_object = Get()
                Get_object.Tag(class_name, NAME)

        print(f"New class:{students_to_add}")
        g = Classes.query.filter_by(grade=class_name).first()

        add = Classes(grade=class_name, students=students_to_add[class_name])

        if g: 
            g.students = students_to_add[class_name]
            flag_modified(add,'students')
            db.session.commit()
            return redirect(url_for('Classes_for_teacher'))
        try:
            db.session.add(add)
            flag_modified(add, 'students')
            db.session.commit()
            return redirect(url_for('Classes_for_teacher'))
        except Exception as e:
            db.session.rollback()
            return f"An error occurred: {e}"
            

    return render_template("ClassCreation.html", students=students, loged=Loged())


if __name__ == '__main__':
    # If running directly, ensure tables exist
    with app.app_context():
        db.create_all()
    app.run('0.0.0.0', debug=True)