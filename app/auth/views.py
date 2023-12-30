import os
import time
from flask import current_app, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required, login_user, logout_user
from . import auth
from .. import db
from ..main.views import get_posts_widget_context, get_users_widget_context
from ..models import Post, User
from uuid import uuid1
from werkzeug.utils import secure_filename


@auth.route('/delete_profile')
@login_required
def delete_profile():
    # Delete profile
    current_user.delete_profile()
    return redirect(request.referrer or url_for('main.index'))


@auth.route('/edit_profile/', methods=["GET", "POST"])
@login_required
def edit_profile():
    if request.method == "POST":
        # Initialize form inputs
        email = request.form.get('email')
        username = request.form.get('username')
        profile_pic = request.files.get('profile_pic')

        # Avoid empty inputs
        if not email:
            flash("Must enter an email")
            print("Must enter an email")
            return render_template('auth/register.html')
        if current_user.email != email :
            if User.query.filter_by(email=email).first():
                flash("There's already an user with this email")
                print("There's already an user with this email")
                return render_template('auth/edit_profile.html')
        if not username:
            flash("Must enter a username")
            print("Must enter a username")
            return render_template('auth/edit_profile.html')
        if current_user.username != username:
            if User.query.filter_by(username=username).first():
                flash("There's  already an account with this username")
                return render_template('auth/edit_profile.html')
        
        current_user.email = email
        current_user.username = username

        # Commit
        db.session.commit()

        # Upload profile pic if given
        if profile_pic:
            # Remove previous profile pic
            if current_user.profile_pic:
                # Delete previous profile pic if it isn't the default
                if current_user.profile_pic != 'images/profile photos/default_profile_pic.jpg':
                    os.remove(os.path.join(current_app.config['UPLOAD_DIRECTORY'], current_user.profile_pic.replace('images/', '').replace('/', '\\')))

            # Upload new selected profile pic
            upload_profile_pic(profile_pic, current_user.username)

        # Redirect to profile page with a flash message
        return redirect(url_for('auth.profile', username=current_user.username))

    # If accesed view via GET method
    return render_template('auth/edit_profile.html')


@auth.route('/follow/<username>')
@login_required
def follow(username):
    # Don't allow to follow oneself
    if current_user.username == username:
        flash("Cannot follow yourself")
        return redirect(request.referrer or url_for('main.index'))
    
    # Follow user if not following
    current_user.follow(username)

    # If followed in the user page
    if (request.args.get('reload')):
        return redirect(request.referrer)
    
    # Redirect user
    return '', 204


@auth.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == "POST":
        # Initialize form inputs
        email = request.form.get("email")
        password = request.form.get("password")
        remember_me = request.form.get("remember_me")

        # Try to get user from the database
        user = User.query.filter_by(email=email).first()

        # Check if the given password matches the queried user
        if (user is not None):
            if not user.verify_password(password):
                flash('Invalid username or password')
            else:
                # Log user with the login_user function from flask_login
                # Which logs the user in and remembers the section if 
                # remember_me = True
                login_user(user, remember_me)

                # Register potential protected url
                next = request.args.get('next')

                # When a user wants to visit a protected url without
                # permission "next" stores the protected url, in case this
                # didn't occur then next is "None"
                if next is None or not next.startswith('/'):
                    next = url_for('main.index')

                # Redirect user to the corresponding url
                flash("You have logged in!")
                return redirect(next)
        else:
            flash('Invalid credentials')
        
    # If accesed view via GET method
    return render_template('auth/login.html')


@auth.route('/logout')
@login_required
def logout():
    # Log current user out with flask_login method logout_user()
    logout_user()
    flash('You have logged out!')
    return redirect(url_for('main.index'))


@auth.route('/<username>')
def profile(username):
    # Get username from the database
    user = User.query.filter_by(username=username).first()

    # Get asked page by the response, the 'type=int' means that if the
    # asked page can't be converted to int then return the default value '1'
    page = request.args.get('posts_page', 1, type=int)

    # Get user's (per_page) posts 
    pagination = Post.query.filter_by(author=user.id).paginate(
        page=page, per_page=current_app.config['POSTS_PER_PAGE'], error_out=False
    )

    # Save posts
    posts = pagination.items

    # Get posts widget context
    post_widget_context = get_posts_widget_context()
    other_posts = post_widget_context['posts']

    # Get users widget context
    users_widget_context = get_users_widget_context()
    users = users_widget_context['users']
    users_pagination = users_widget_context['users_pagination']

    # Render template
    return render_template('auth/user.html', user=user, posts=posts, pagination=pagination, users=users, users_pagination=users_pagination, other_posts=other_posts)


@auth.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == "POST":
        # Initialize form inputs
        email = request.form.get('email')
        username = request.form.get('username')
        password = request.form.get('password')
        confirmation_password = request.form.get('confirmation_password')
        profile_pic = request.files.get('profile_pic')

        # Avoid empty inputs
        if not email:
            flash("Must enter an email")
            return render_template('auth/register.html')
        if User.query.filter_by(email=email).first():
            flash("There's already an user with this email")
            return render_template('auth/register.html')
        if not username:
            flash("Must enter a username")
            return render_template('auth/register.html')
        if User.query.filter_by(username=username).first():
            flash("There's  already an account with this username")
            return render_template('auth/register.html')
        if not password:
            flash("Must enter a password")
            return render_template('auth/register.html')
        if not confirmation_password:
            flash("Must enter confirmation password")
            return render_template('auth/register.html')
        
        if password == confirmation_password:
            # Create instance of User
            user = User(email=email, username=username, password=password)

            # Add user to the session
            db.session.add(user)

            # Commit
            db.session.commit()

            # Upload profile pic if given
            if profile_pic:
                upload_profile_pic(profile_pic, user.username)

            # Redirect to home page with a flash message
            login_user(user, False)
            return redirect(url_for('main.index'))

    # If accesed view via GET method
    return render_template('auth/register.html')


@auth.route('/unfollow/<username>')
@login_required
def unfollow(username):
    # Don't allow to ufollow oneself
    if current_user.username == username:
        flash("Cannot unfollow yourself")
        return redirect(request.referrer or url_for('main.index'))
    
    # Unfollow user if following
    current_user.unfollow(username)

    # Redirect user
    return '', 204
    

def upload_profile_pic(file, user):
    # Get user
    user = User.query.filter_by(username=user).first()

    # Embbed filename with uuid and make sure the filename
    # is safe with secure_filename
    filename = f'{uuid1()} {secure_filename(file.filename)}'

    # Get filename
    static_path = f'images/profile photos/{filename}'

    # Server path
    path = os.path.join(current_app.config['UPLOAD_DIRECTORY'], 'profile photos')

    # Join server's path with the file's name
    filename = os.path.join(path, filename)

    # If path doesn't exists create it
    if not os.path.exists(path):
        os.makedirs(path)
    
    # Save file
    file.save(filename)

    # Create file object, and add it to the session 
    user.profile_pic = static_path
    db.session.commit()