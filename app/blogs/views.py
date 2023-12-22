from flask import abort, render_template, request, redirect, url_for, flash
from flask_login import current_user, login_required
from . import blogs
from ..models import Blog, Comment, File
from .. import db
import os
from uuid import uuid1
from werkzeug.utils import secure_filename


@login_required
@blogs.route('/comment/<int:post_id>', methods=['GET', 'POST'])
def comment(post_id):
    if request.method == "POST":
        # Get body
        body = request.form.get("body")

        # Comment
        current_user.comment(post_id, body)

        # Redirect
        return redirect(url_for('main.index'))
    
    # If accesed view by GET method
    return render_template('blogs/comment.html')


@login_required
@blogs.route('/delete_comment/<int:comment_id>')
def delete_comment(comment_id):
    # Get comment
    comment = Comment.query.filter_by(id=comment_id).first()

    # Verify if user is the owner of the comment
    if not current_user.id == comment.id:
        flash("You are not the owner of the comment")
        return redirect(request.referrer or url_for('main.index'))
    
    # Delete comment
    comment.delete_comment()

    # Redirect
    flash("Comment deleted!")
    return redirect(request.referrer or url_for('main.index'))


@login_required
@blogs.route('/delete_post/<int:post_id>')
def delete_post(post_id):
    # Get post
    post = Blog.query.filter_by(id=int(post_id)).first()

    # Delete post if possible
    post.delete_post()
    try:
        post.delete_post()
        flash("Post deleted")
        return redirect(request.referrer or url_for('main.index'))
    except:
        return redirect(request.referrer or url_for('main.index'))


@login_required
@blogs.route('/new_post', methods=['GET', 'POST'])
def new_post():
    if request.method == "POST":
        # Initialize input variables
        title = request.form.get("title")
        body = request.form.get("body")
        files = request.files.getlist("files")

        # Check they are not null
        if not title:
            flash("Must enter a title")
            return render_template('blogs/new_post.html')
        if not body:
            flash("Must enter a body")
            return render_template('blogs/new_post.html')
        
        # Initialize Blog object
        blog = Blog(title=title, body=body, author=current_user.id)

        # Add blog to the database
        db.session.add(blog)
        db.session.commit()

        # Get blog object
        # Save files
        if files:
            for file in files:
                # Embbed filename with uuid and make sure the filename
                # is safe with secure_filename
                filename = f'{uuid1()} {secure_filename(file.filename)}'
                
                # Get filename
                static_path = f"static\\images\\post files\\{filename}"
                filename = os.path.join("app\\static\\images\\post files", filename)

                # Save file
                file.save(filename)

                # Create file object, and add it to the session 
                file = File(path=static_path, blog_id=blog.id)
                db.session.add(file)

        # Commit after adding each file
        db.session.commit()

        # Redirect
        flash("Post created!")
        return redirect(url_for('main.index'))

    # If accesed view via GET method
    return render_template('blogs/new_post.html')


@blogs.route('/post/<int:post_id>')
def post(post_id):
    # Get post
    post = Blog.query.filter_by(id=post_id).first()

    # Render template
    return render_template("blogs/post.html", post=post)



