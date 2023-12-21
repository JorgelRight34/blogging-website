from werkzeug.security import generate_password_hash, check_password_hash
from itsdangerous import TimedSerializer as Serializer
from flask import current_app
from flask_login import UserMixin, current_user
from . import db, login_manager
from datetime import datetime


class Blog(db.Model):
    __tablename__ = 'blogs'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(64), nullable=False)
    body = db.Column(db.Text, nullable=False)
    author = db.Column(db.Integer, db.ForeignKey('users.id'))
    date = db.Column(db.DateTime, default=datetime.utcnow, index=True)

    @property
    def author(self):
        from .models import User
        user = User.query.filter_by(id=self.author).first()
        return user

    def __repr__(self):
        return self.title
    

class User(UserMixin, db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(64), unique=True, index=True)
    username = db.Column(db.String(64), unique=True, index=True)
    password_hash = db.Column(db.String(128))
    blogs = db.relationship('Blog', backref='user', lazy='dynamic')
    followers = db.relationship('Follower', backref='followee')

    confirmed = db.Column(db.Boolean, default=False)
    
    def generate_confirmation_token(self, expiration=3600):
        s = Serializer(current_app.config['SECRET_KEY'], expiration)
        return s.dumps({'confirm': self.id}.decode('utf-8'))
    
    def confirm(self, token):
        s = Serializer(current_app.config['SECRET_KEY'])
        try:
            data = s.loads(token.encode('utf-8'))
        except:
            return False
        
        if data.get('confirm') != self.id:
            return False
        
        self.confirmed = True
        db.session.add(self)
        return True

    def follow(self, username):
        # Get username from the database
        user = User.query.filter_by(username=username).first()

        # Follow
        follower = Follow(follower=current_user.id, followee=user.id)

        # Add follower to the session
        db.session.add(follower)

        # Commit changes
        db.session.commit()
        return

    @property
    def password(self):
        raise AttributeError('password is not readable')
    
    @password.setter
    def password(self, password):
        self.password_hash = generate_password_hash(password)

    def verify_password(self, password):
        return check_password_hash(self.password_hash, password)
    

    def __repr__(self):
        return '<User %r>' % self.username

    
class Follow(db.Model):
    __tablename__ = 'follows'
    follower_id = db.Column(db.Integer, db.ForeignKey('users.id'), primary_key=True, name='follower_id')
    followed_id = db.Column(db.Integer, db.ForeignKey('users.id'), primary_key=True, name='followee_id')
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

