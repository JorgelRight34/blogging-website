from werkzeug.security import generate_password_hash, check_password_hash
from itsdangerous import TimedSerializer as Serializer
from flask import current_app, url_for
from flask_login import UserMixin, current_user, logout_user
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
    likes = db.relationship('Like', backref='blog', cascade='all, delete-orphan')
    files = db.relationship('File', backref='blog', cascade='all, delete-orphan')
    topic = db.Column(db.String, nullable=True)
    
    def delete_post(self):
        if current_user == self.user:
            # Delete from the session
            db.session.delete(self)
            
            # Commit changes
            db.session.commit()
        else:
           raise ValueError
        
    def __repr__(self):
        return self.title


class Comment(db.Model):
    __tablename__ = 'comments'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    blog_id = db.Column(db.Integer, db.ForeignKey('blogs.id'), nullable=False)
    comment_id = db.Column(db.Integer, db.ForeignKey('comments.id'), nullable=True)
    body = db.Column(db.Text, nullable=False)
    date = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    likes = db.relationship('Like', backref='comment', cascade='all, delete-orphan')
    replies = db.relationship('Comment', backref='comment_replies', remote_side=[id], cascade='all, delete-orphan', single_parent=True)
    
    def delete_comment(self):
        # Verify if user is the owner of the comment
        if not current_user == self.user:
            raise ValueError
        
        # Delete comment from the database
        db.session.delete(self)
        db.session.commit()


class User(UserMixin, db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(64), unique=True, index=True)
    username = db.Column(db.String(64), unique=True, index=True)
    password_hash = db.Column(db.String(128))
    profile_pic = db.Column(db.String, default='images/profile photos/default_profile_pic.jpg')
    posts = db.relationship('Blog', backref='user', cascade='all, delete-orphan')
    comments = db.relationship('Comment', backref='user', cascade='all, delete-orphan')
    followers = db.relationship('Follow', backref='user', foreign_keys='Follow.followed_id', cascade='all, delete-orphan')
    likes = db.relationship('Like', backref='user', cascade='all, delete-orphan')
    notifications = db.relationship('Notification', backref='user', foreign_keys='Notification.user_id', cascade='all, delete-orphan')
    actions = db.relationship('Notification', backref='notificator', foreign_keys='Notification.notificator_id', cascade='all, delete-orphan')

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
    
    def like_post(self, post_id):
        # Get post
        post = Blog.query.filter_by(id=int(post_id)).first()

        # Verify if user has already liked the post
        like = Like.query.filter_by(blog_id=post.id, user_id=current_user.id).first()
        if like:
            raise ValueError
        
        # Make like instance and save it to the database
        like = Like(blog_id=post.id, user_id=current_user.id)
        db.session.add(like)

        # Make notification for post's author
        if post.get_author().id != self.id:
            action = f'{self.username} has liked your post "{post.title}"'
            notification = Notification(user_id=post.get_author().id, notificator_id=self.id, action=action)
            db.session.add(notification)

        # Commit
        db.session.commit()

    def like_comment(self, comment_id):
        # Get post
        comment = Comment.query.filter_by(id=int(comment_id)).first()

        # Verify if user has already liked the post
        like = Like.query.filter_by(comment_id=comment.id, user_id=current_user.id).first()
        if like:
            print(like)
            raise ValueError
        
        # Make like instance and save it to the database
        like = Like(comment_id=comment.id, user_id=current_user.id)
        db.session.add(like)

        # Make notification for post's author
        if comment.get_author().id != self.id:
            action = f'{self.username} has liked your post "{comment.body}"'
            notification = Notification(user_id=comment.get_author().id, notificator_id=self.id, action=action)
            db.session.add(notification)

        # Commit
        db.session.commit()

    def likes_post(self, post_id):
        # Return True if user likes the post with its id as 'post_id'
        like = Like.query.filter_by(blog_id=post_id, user_id=self.id).first()

        if like:
            return True
        else:
            return False
        
    def likes_comment(self, comment_id):
        # Return True if user likes the post with its id as 'post_id'
        like= Like.query.filter_by(comment_id=comment_id, user_id=self.id).first()
        print(like)
        if like:
            return True
        else:
            return False
        
    def unlike_post(self, post_id):
        # Search for like
        like = Like.query.filter_by(blog_id=post_id, user_id=self.id).first()

        if like:
            # If user has liked delete the like
            db.session.delete(like)
            db.session.commit()
        else:
            return ValueError
        
    def unlike_comment(self, comment_id):
        # Search for like
        like = Like.query.filter_by(comment_id=comment_id, user_id=self.id).first()

        if like:
            # If user has liked delete the like
            db.session.delete(like)
            db.session.commit()
        else:
            return ValueError
        
    def unfollow(self, username):
        # Follow user if user is not following user
        if username != self.username:
            if not self.is_following(username):
                # If user is following user then ufollow the user
                # Get user with 'username' as username
                user = User.query.filter_by(username=username).first()

                # Get follow instance if user was found
                if user:
                    follow = Follow.query.filter_by(follower_id=self.id, followed_id=user.id).first()

                    # Save to the database
                    db.session.delete(follow)
                    db.session.commit()
                else:
                    raise ValueError
            else:
                raise ValueError
        else:
            raise ValueError


    @property
    def password(self):
        raise AttributeError('password is not readable')
    
    @password.setter
    def password(self, password):
        self.password_hash = generate_password_hash(password)

    def verify_password(self, password):
        return check_password_hash(self.password_hash, password)

    def follow(self, username):
        # Follow user if user is not following user
        if username != self.username:
            if not self.is_following(username):
                # If user is not following user then follow the user
                # Get user with 'username' as username
                user = User.query.filter_by(username=username).first()

                # Make a follow instance if user was found
                if user:
                    follow = Follow(follower_id=current_user.id, followed_id=user.id)
                    action = f'{self.username} is following you'

                    # Make notification
                    notification = Notification(user_id=user.id, notificator_id=self.id, action=action)
                    db.session.add(notification)

                    # Save to the database
                    db.session.add(follow)
                    db.session.commit()
                else:
                    raise ValueError
            else:
                raise ValueError
        else:
            raise ValueError

    @property
    def following(self):
        # Get users who self is following
        following = Follow.query.filter_by(follower_id=self.id).all()
        return following

        
    def get_followers(self):
        # Get followers
        followers = Follow.query.filter_by(followed_id=self.id)

        # Return numbers of followers
        return followers.count()
    
    def is_following(self, username):
        # Find user with username 'username'
        user = User.query.filter_by(username=username).first()

        # Check if user already following user
        if user:
            print("If user")
            follow = Follow.query.filter_by(follower_id=self.id, followed_id=user.id).first()
            # Return True if user is following, return False otherwise
            if follow:
                return True
            else:
                return False
        else:
            return False
        

    def unfollow(self, username):
        # If user is following then unfollow
        user = User.query.filter_by(username=username).first()

        if self.is_following(user.username):
            # Get follow
            follow = Follow.query.filter_by(follower_id=self.id, followed_id=user.id).first()
            
            # Eliminate follow from the session
            db.session.delete(follow)
            db.session.commit()
        else:
            raise ValueError
        
        
    def comment(self, post_id, body):
        # Comment post
        comment = Comment(user_id=self.id, blog_id=post_id, body=body)

        # Save to database
        db.session.add(comment)
        db.session.commit()

    def delete_profile(self):
        # Delete current user
        db.session.delete(current_user)

        # Log out before deleting
        logout_user()

        # Delete current user
        db.session.commit()


    def __repr__(self):
        return '<User %r>' % self.username
    
    def __str__(self):
        return self.username
    

class Follow(db.Model):
    __tablename__ = 'follows'
    follower_id = db.Column(db.Integer, db.ForeignKey('users.id'), primary_key=True)
    followed_id = db.Column(db.Integer, db.ForeignKey('users.id'), primary_key=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)


class File(db.Model):
    __tablename__ = 'files'
    path = db.Column(db.String, primary_key=True)
    blog_id = db.Column(db.Integer, db.ForeignKey('blogs.id'))

    @property
    def type(self):
        # Image file types extensions
        image_file_types = [
            'jpg', 'jpeg', 'png', 'gif', 'tiff', 'tif', 'bmp', 'webp', 'svg', 'ico',
            'raw', 'heif', 'heic', 'crx'
        ]

        # Video file types extensions
        video_file_types = [
            'mp4', 'avi', 'mkv', 'mov', 'wmv', 'flv', 'webm', '3gp', 'ogg', 'mpg', 'mpeg', 'ts'
        ]

        # Get file .extension
        type = self.path.split('.')
        max_index = len(type) - 1
        type = type[max_index]

        # Return "image" if file is an image
        if type in image_file_types:
            print('image')
            return 'image'
        # Return "video" if file is a video
        elif type in video_file_types:
            return 'video'
        else:
            print('else')
            return type

    @property
    def file_extension(self):
        # Get file .extension
        type = self.path.split('.')
        max_index = len(type) - 1
        return type[max_index]
        



class Like(db.Model):
    __tablename__ = 'Likes'
    id = db.Column(db.Integer, primary_key=True)
    blog_id = db.Column(db.Integer, db.ForeignKey('blogs.id'), nullable=True)
    comment_id = db.Column(db.Integer, db.ForeignKey('comments.id'), nullable=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    date = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    

class Notification(db.Model):
    __tablename__ = 'notifications'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    notificator_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    action = db.Column(db.String, nullable=False)
    date = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    def delete_notification(self):
        # Check if user is owner of the notification
        if current_user != self.user:
            raise ValueError

        # Delete notification
        db.session.delete(self)
        db.session.commit()
    
    def __str__(self):
        return f'{self.action} | {self.date.strftime("%Y-%m-%d %H:%M:%S")}'

    
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

