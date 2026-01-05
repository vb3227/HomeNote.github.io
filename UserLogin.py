from flask_login import UserMixin

class UserLogin():
    def fromDB(self, user_id):
        from Get import Get
        user = Get().getUser(user_id)
        if not user:
            return None
        self.__user = user
        return self

    def make(self, user):
        self.__user = user
        return self
    
    def is_authenticated(self):
        return True

    def is_active(self):
        return True
    
    @property
    def confirmed(self):
        return self.__user.confirmed

    def is_anonymous(self):
        return False

    def get_id(self):
        return str(self.__user.id)
