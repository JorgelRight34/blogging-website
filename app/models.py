import os
from datetime import datetime
from flask import current_app, flash, url_for
from flask_login import UserMixin, current_user, logout_user
from itsdangerous import TimedSerializer as Serializer
from werkzeug.security import generate_password_hash, check_password_hash
from . import db, login_manager


class Post(db.Model):
    __tablename__ = 'posts'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(64), nullable=False)
    body = db.Column(db.Text, nullable=False)
    author = db.Column(db.Integer, db.ForeignKey('users.id'))
    date = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    comments = db.relationship('Comment', backref='post', cascade='all, delete-orphan')
    likes = db.relationship('Like', backref='post', cascade='all, delete-orphan')
    files = db.relationship('File', backref='post', cascade='all, delete-orphan')
    new = db.Column(db.Integer, db.ForeignKey('news.id'), nullable=True)
    responded_title = db.Column(db.String, nullable=True)
    responded_post = db.Column(db.Integer, db.ForeignKey('posts.id'), nullable=True)
    
    def delete_post(self):
        if current_user == self.user:
            # Delete post files
            for file in self.files:
                path = os.path.join(current_app.config['UPLOAD_DIRECTORY'], file.path.replace('images/', '').replace('/','\\'))
                os.remove(path)

            # Delete from the session
            db.session.delete(self)
            
            # Commit changes
            db.session.commit()
        else:
           raise ValueError
        
    @property
    def get_new(self):
        new = New.query.filter_by(id=self.new).first()
        if new:
            return new
        else:
            raise ValueError
        
    def get_responded_post(self):
        print("We are in")
        responded_post = Post.query.filter_by(id=self.responded_post).first()
        return responded_post
        
    @property
    def new_title(self):
        new = self.get_new
        if new:
            return new.title
        else:
            return ''

    def __repr__(self):
        return self.title


class Comment(db.Model):
    __tablename__ = 'comments'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    post_id = db.Column(db.Integer, db.ForeignKey('posts.id'), nullable=False)
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


class New(db.Model):
    __tablename__ = 'news'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(64), nullable=False)
    content = db.Column(db.Text, nullable=False)
    author = db.Column(db.String(64), nullable=False)
    date = db.Column(db.DateTime, index=True)
    url = db.Column(db.String, nullable=False)
    image = db.Column(db.String, nullable=True)
    posts = db.relationship('Post', backref='post_new', cascade='all, delete-orphan')
    

class User(UserMixin, db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(64), unique=True, index=True)
    username = db.Column(db.String(64), unique=True, index=True)
    password_hash = db.Column(db.String(128))
    profile_pic = db.Column(db.String, default='images/profile photos/default_profile_pic.jpg')
    posts = db.relationship('Post', backref='user', cascade='all, delete-orphan')
    comments = db.relationship('Comment', backref='user', cascade='all, delete-orphan')
    followers = db.relationship('Follow', backref='user', foreign_keys='Follow.followed_id', cascade='all, delete-orphan')
    follows = db.relationship('Follow', backref='follower_user', foreign_keys='Follow.follower_id', cascade='all, delete-orphan')
    likes = db.relationship('Like', backref='user', cascade='all, delete-orphan')
    notifications = db.relationship('Notification', backref='user', foreign_keys='Notification.user_id', cascade='all, delete-orphan')
    actions = db.relationship('Notification', backref='notificator', foreign_keys='Notification.notificator_id', cascade='all, delete-orphan')

    confirmed = db.Column(db.Boolean, default=False)
    
    def generate_confirmation_token(self, expiration=3600):
        s = Serializer(current_app.config['SECRET_KEY'], expiration)
        return s.dumps({'confirm': self.id}.decode('utf-8'))
    

    def comment(self, post_id, body):
        # Comment post
        comment = Comment(user_id=self.id, post_id=post_id, body=body)

        # Save to database
        db.session.add(comment)
        db.session.commit()
    

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
    

    def delete_profile(self):
        # Delete current user
        db.session.delete(current_user)

        # Log out before deleting
        logout_user()

        # Delete current user
        db.session.commit()

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
                    db.session.add(follow)
                    db.session.commit()

                    # Make notification
                    notification = Notification(user_id=user.id, notificator_id=self.id, action=action)
                    db.session.add(notification)

                    # Save to the database
                    db.session.add(notification)
                    db.session.commit()
                else:
                    raise ValueError
            else:
                flash('Already following')
                raise ValueError
        else:
            flash('Cannot follow yourself')
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
            follow = Follow.query.filter_by(follower_id=self.id, followed_id=user.id).first()
            # print(f'{follow.follower_id} follows {follow.followed_id}')
            # Return True if user is following, return False otherwise
            if follow:
                return True
            else:
                return False
        else:
            return False
    

    def like_comment(self, comment_id):
        # Get post
        comment = Comment.query.filter_by(id=int(comment_id)).first()

        # Verify if user has already liked the post
        like = Like.query.filter_by(comment_id=comment.id, user_id=current_user.id).first()
        if like:
            raise ValueError
        
        # Make like instance and save it to the database
        like = Like(comment_id=comment.id, user_id=current_user.id)
        db.session.add(like)
        db.session.commit()

        # Make notification for post's author
        if comment.get_author().id != self.id:
            action = f'{self.username} has liked your post "{comment.body}"'
            notification = Notification(user_id=comment.get_author().id, notificator_id=self.id, action=action)
            db.session.add(notification)
            db.session.commit()

    
    def likes_comment(self, comment_id):
        # Return True if user likes the post with its id as 'post_id'
        like= Like.query.filter_by(comment_id=comment_id, user_id=self.id).first()
        if like:
            return True
        else:
            return False
    

    def like_post(self, post_id):
        # Get post
        post = Post.query.filter_by(id=int(post_id)).first()

        # Verify if user has already liked the post
        like = Like.query.filter_by(post_id=post.id, user_id=current_user.id).first()
        if like:
            raise ValueError
        
        # Make like instance and save it to the database
        like = Like(post_id=post.id, user_id=current_user.id)
        db.session.add(like)
        db.session.commit()

        # Make notification for post's author
        if post.author != self.id:
            action = f'{self.username} has liked your post "{post.title}"'
            notification = Notification(user_id=post.author, notificator_id=self.id, action=action)
            db.session.add(notification)

        # Commit
        db.session.commit()


    def likes_post(self, post_id):
        # Return True if user likes the post with its id as 'post_id'
        like = Like.query.filter_by(post_id=post_id, user_id=self.id).first()

        if like:
            return True
        else:
            return False
        

    @property
    def password(self):
        raise AttributeError('password is not readable')
    
    
    @password.setter
    def password(self, password):
        self.password_hash = generate_password_hash(password)


    def unlike_comment(self, comment_id):
        # Search for like
        like = Like.query.filter_by(comment_id=comment_id, user_id=self.id).first()

        if like:
            # If user has liked delete the like
            db.session.delete(like)
            db.session.commit()
        else:
            return ValueError
        

    def unlike_post(self, post_id):
        # Search for like
        like = Like.query.filter_by(post_id=post_id, user_id=self.id).first()

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
        

    def unfollow(self, username):
        # If user is following then unfollow
        user = User.query.filter_by(username=username).first()

        if self.is_following(username) == True:
            # Get follow
            follow = Follow.query.filter_by(follower_id=self.id, followed_id=user.id).first()
            
            # Eliminate follow from the session
            db.session.delete(follow)
            db.session.commit()
        else:
            flash('Already not following')
            raise ValueError


    def verify_password(self, password):
        return check_password_hash(self.password_hash, password)
    

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
    post_id = db.Column(db.Integer, db.ForeignKey('posts.id'))
    alt = db.Column(db.String, nullable=False)


    @property
    def file_extension(self):
        # Get file .extension
        type = self.path.split('.')
        max_index = len(type) - 1
        return type[max_index]
    

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
        

class Like(db.Model):
    __tablename__ = 'Likes'
    id = db.Column(db.Integer, primary_key=True)
    post_id = db.Column(db.Integer, db.ForeignKey('posts.id'), nullable=True)
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