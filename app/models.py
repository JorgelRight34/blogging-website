from werkzeug.security import generate_password_hash, check_password_hash
from . import db
from itsdangerous import TimedSerializer as Serializer
from flask import current_app, flash
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
    comments = db.relationship('Comment', backref='blog', cascade='all, delete-orphan')

    def get_author(self):
        # Get author's user
        user = User.query.filter_by(id=self.author).first()
        return user
    
    def delete_post(self):
        if current_user.id == self.author:
            # Delete from the session
            db.session.delete(self)
            
            # Commit changes
            db.session.commit()
        else:
           raise ValueError
        
    def __repr__(self):
        return self.title


class User(UserMixin, db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(64), unique=True, index=True)
    username = db.Column(db.String(64), unique=True, index=True)
    password_hash = db.Column(db.String(128))
    blogs = db.relationship('Blog', backref='user')
    comments = db.relationship('Comment', backref='user')

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

    @property
    def password(self):
        raise AttributeError('password is not readable')
    
    @password.setter
    def password(self, password):
        self.password_hash = generate_password_hash(password)

    def verify_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    @staticmethod
    def get_user(username):
        # Get user with 'username' as username
        user = User.query.filter_by(username=username).first()

        # Return user
        return user

    def follow(self, username):
        print("Entramos al follow")
        # Follow user if user is not following user
        if username != self.username:
            if not self.is_following(username):
                print("If not...")
                # If user is not following user then follow the user
                # Get user with 'username' as username
                user = User.get_user(username)

                # Make a follow instance if user was found
                if user:
                    print("If user...")
                    follow = Follow(follower_id=current_user.id, followed_id=user.id)

                    # Save to the database
                    db.session.add(follow)
                    db.session.commit()
                else:
                    print("Else 1")
                    raise ValueError
            else:
                print("Else 2")
                raise ValueError
        else:
            raise ValueError
        
    def followers(self):
        # Get followers
        followers = Follow.query.filter_by(followed_id=self.id)

        # Return numbers of followers
        print(followers.count())
        return followers.count()
    
    def is_following(self, username):
        # Find user with username 'username'
        user = User.get_user(username)
        print(f"User = {user}")

        # Check if user already following user
        if user:
            print("If user")
            follow = Follow.query.filter_by(follower_id=self.id, followed_id=user.id).first()
            print(follow)
            # Return True if user is following, return False otherwise
            if follow:
                print("if follow")
                print(follow.follower_id)
                return True
            else:
                print("Else is_following 1")
                return False
        else:
            print("Else 3")
            return False
        

    def unfollow(self, username):
        # If user is following the unfollow
        user = User.get_user(username)
        if self.is_following(user.username):
            # Get follow
            follow = Follow.query.filter_by(follower_id=self.id, followed_id=user.id)
            
            # Eliminate follow from the session
            db.session.delete(follow)
            db.session.commit()
        else:
            raise ValueError
        
    def comment(self, post_id, body):
        # Comment post

        # Get post
        post = Blog.query.filter_by(id=post_id)

        # Comment post
        comment = Comment(user_id=self.id, blog_id=post_id, body=body)

        # Save to database
        db.session.add(comment)
        db.session.commit()


    def __repr__(self):
        return '<User %r>' % self.username
    

class Follow(db.Model):
    __tablename__ = 'follows'
    follower_id = db.Column(db.Integer, db.ForeignKey('users.id'), primary_key=True)
    followed_id = db.Column(db.Integer, db.ForeignKey('users.id'), primary_key=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    

class Comment(db.Model):
    __tablename__ = 'comments'
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), primary_key=True)
    blog_id = db.Column(db.Integer, db.ForeignKey('blogs.id'), primary_key=True)
    body = db.Column(db.Text, nullable=False)
    date = db.Column(db.DateTime, default=datetime.utcnow)

    def get_author(self):
        # Get author's user
        user = User.query.filter_by(id=self.user_id).first()
        return user
    
    def delete_comment(self):
        # Delete comment from the database
        db.session.delete(self)
        db.session.commit()

    


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

