from flask import render_template, request, url_for, flash
from flask_login import current_user
from . import blogs
from ..models import Blog
from .. import db

@blogs.route('/new_post', methods=['GET', 'POST'])
def new_post():
    if request.method == "POST":
        # Initialize input variables
        title = request.form.get("title")
        body = request.form.get("body")

        # Check they are not null
        if not title:
            flash("Must enter a title")
            return render_template('blogs/new_post.html')
        if not body:
            flash("Must enter a body")
            return render_template('blogs/new_post.html')
        
        # Initialize Blog object
        blog = Blog(title=title, body=body, author=current_user.id)

        # Add blog to the session
        db.session.add(blog)

        # Commit
        db.session.commit()

    # If accesed view by GET method
    return render_template('blogs/new_post.html')
