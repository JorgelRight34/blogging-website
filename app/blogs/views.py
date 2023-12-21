from flask import abort, render_template, request, redirect, url_for, flash
from flask_login import current_user, login_required
from . import blogs
from ..models import Blog
from .. import db

@login_required
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
        print("Post saved")
        return redirect(url_for('main.index'))

    # If accesed view by GET method
    return render_template('blogs/new_post.html')

@login_required
@blogs.route('/delete/<int:post>')
def delete_post(post):
    # Get post
    post = Blog.query.filter_by(id=int(post)).first()

    if current_user.id == post.author:
        # Delete from the session
        db.session.delete(post)
        
        # Commit changes
        db.session.commit()
        return redirect(url_for('main.index'))
    else:
        flash("Cannot delete a post that is not yours")
        return redirect(url_for('main.index'))
    

