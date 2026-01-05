from Model import User, db
from sqlalchemy.orm.attributes import flag_modified
from flask import abort
class Get:
    def getUser(self, user_id):
        try:
            res = User.query.filter_by(id=user_id).first()
            if not res:
                print("Missed user")
                return None
            
            return res
        except Exception as e:
            print(f"Something went wrong: str({e})")

        return None
    
    def getUserByEmail(self, email):
        try:
            res = User.query.filter_by(email=email).first()
            if not res:
                print("User wasn't found")
                return None
            
            return res
        except Exception as e:
            print(f"Mistake of getting information from the db: str({e})")
        
    def Tag(self, class_name, NAME):
        find_user = User.query.filter_by(user_name=NAME).first()
        # print(type(find_user.classes), find_user.classes)
        if find_user.classes is None:
            find_user.classes = []

        if class_name not in find_user.classes:
            find_user.classes.append(class_name)

        flag_modified(find_user, 'classes')

        db.session.commit()

        print(find_user.classes)

        return None
    
    def Role(self, ID):
        res = User.query.filter_by(id=ID).first()
        if res.role == "student":
            abort(404)
