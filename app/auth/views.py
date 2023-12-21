from flask import render_template, redirect, request, url_for, flash
from flask_login import login_user, logout_user, login_required, current_user
from . import auth
from .. import db
from ..models import User, Blog

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

                # when a user wants to visit a protected url without
                # permission next stores the protected url, in case this
                # didn't occur then next is None.
                next = request.args.get('next')
                flash("You have logged in!")
                if next:
                    # Redirect to the protected url
                    return redirect(next)
                else:
                    # Redirect to main page
                    return redirect(url_for('main.index'))
        else:
            flash('Invalid username')
        
    # If accesed view via GET method
    return render_template('auth/login.html')

@auth.route('/logout')
@login_required
def logout():
    # Log current user out with flask_login method logout_user()
    logout_user()
    flash("You have logged out!")
    return redirect(url_for('main.index'))


@auth.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == "POST":
        # Initialize form inputs
        email = request.form.get('email')
        username = request.form.get('username')
        password = request.form.get('password')
        confirmation_password = request.form.get('confirmation_password')

        # Avoid empty inputs
        if not email:
            flash("Must enter an email")
        if not username:
            flash("Must enter a username")
        if not password:
            flash("Must enter a password")
        if not confirmation_password:
            flash("Must enter confirmation password")

        if password == confirmation_password:
            # Create instance of User
            user = User(email=email, username=username, password=password)

            # Add user to the session
            db.session.add(user)

            # Commit
            db.session.commit()

            # Redirect to home page with a flash message
            flash('You can now <a href="{{ url_for("auth.login") }}>log in!</a>')
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
    return render_template('auth/user.html', posts=posts)





