from flask import render_template, redirect, request, url_for, flash
from flask_login import login_user, logout_user, login_required, current_user
from . import auth
from .. import db
from ..models import User, Blog
from uuid import uuid1
from werkzeug.utils import secure_filename
import os


@auth.route('/delete_profile')
@login_required
def delete_profile():
    # Delete profile
    current_user.delete_profile()
    return redirect(request.referrer or url_for('main.index'))


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
            print("user == None")
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
    flash("You have logged out!")
    return redirect(request.referrer or url_for('main.index'))


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
            print(f"profile_pic = {profile_pic}")
            if profile_pic:
                print("If profile_pic")
                upload_profile_pic(profile_pic, user.username)

            # Redirect to home page with a flash message
            flash('You can now <a href="{{ url_for("auth.login") }}>log in!</a>')
            login_user(user, False)
            return redirect(url_for('main.index'))

    # If accesed view via GET method
    return render_template('auth/register.html')

@login_required
@auth.route("/<username>")
def profile(username):
    # Get username from the database
    user = User.query.filter_by(username=username).first()

    # Get user's posts
    posts = Blog.query.filter_by(author=user.id).all()

    # Render template
    return render_template('auth/user.html', user=user, posts=posts)

@login_required
@auth.route('/unfollow/<username>')
def unfollow(username):
    # Don't allow to ufollow oneself
    if current_user.username == username:
        flash("Cannot unfollow yourself")
        return redirect(request.referrer or url_for('main.index'))
    
    # Unfollow user if following
    try:
        current_user.unfollow(username)
    except:
        flash("Already not following")

    # Redirect user
    return redirect(request.referrer or url_for('main.index'))
    

@login_required
@auth.route('/follow/<username>')
def follow(username):
    # Don't allow to follow oneself
    if current_user.username == username:
        flash("Cannot follow yourself")
        return redirect(request.referrer or url_for('main.index'))
    
    # Follow user if not following
    try:
        current_user.follow(username)
    except:
        flash("Already following")

    # Redirect user
    return redirect(request.referrer or url_for('main.index'))
    

@auth.route('/upload_profile_pic', methods=["POST"])
@login_required
def set_profile_pic():
    file = request.files.get("profile_pic")
    upload_profile_pic(file, current_user.username)
    return redirect(request.referrer or url_for('auth.index'))



def upload_profile_pic(file, user):
    # Get user
    user = User.query.filter_by(username=user).first()

    # Embbed filename with uuid and make sure the filename
    # is safe with secure_filename
    filename = f'{uuid1()} {secure_filename(file.filename)}'
    print(filename)

    # Get filename
    static_path = f"images/profile photos/{filename}"
    filename = os.path.join("app\\static\\images\\profile photos", filename)

    # Save file
    file.save(filename)

    # Create file object, and add it to the session 
    user.profile_pic = static_path
    db.session.commit()





