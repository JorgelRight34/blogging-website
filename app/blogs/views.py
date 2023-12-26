from flask import abort, current_app, render_template, request, redirect, url_for, flash, make_response
from flask_login import current_user, login_required
from . import blogs
from ..models import Blog, Comment, Like, File, Notification
from .. import db
from ..main.views import get_users_widget_context, get_posts_widget_context
import os
import requests
from uuid import uuid1
from werkzeug.utils import secure_filename
from sqlalchemy import or_
from datetime import datetime
from dateutil import parser

@blogs.route('/comment/<int:post_id>', methods=['GET', 'POST'])
@login_required
def comment(post_id):
    if request.method == "POST":
        # Get body
        body = request.form.get("body")

        # Comment
        current_user.comment(post_id, body)

        # Redirect
        return redirect(request.referrer or url_for('main.index'))
    
    # If accesed view by GET method
    return render_template('blogs/comment.html')


@blogs.route('/delete_comment/<int:comment_id>')
@login_required
def delete_comment(comment_id):
    # Get comment
    comment = Comment.query.filter_by(id=comment_id).first()

    try:
        # Delete comment
        comment.delete_comment()
    except:
        # Notify user he can't delete other's people comments
        flash("You are not the owner of the comment")
        return redirect(request.referrer or url_for('main.index'))

    # Redirect if succesful
    flash("Comment deleted!")
    return redirect(request.referrer or url_for('main.index'))


@blogs.route('/delete_notification/<int:notification_id>')
@login_required
def delete_notification(notification_id):
    # Get notification
    notification = Notification.query.filter_by(id=notification_id).first()

    if notification:
        try:
            notification.delete_notification()
        except:
            flash("Notification is not yours")
            redirect(request.referrer or url_for('main.index'))
    else:
        flash("Notification doesn't exist")

    # Redirect
    return redirect(request.referrer or url_for('main.index'))


@blogs.route('/delete_post/<int:post_id>')
@login_required
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


@blogs.route('/like_post/<int:post_id>')
@login_required
def like_post(post_id):
    # Like post
    try:
        current_user.like_post(post_id)
    except:
        # If user has already liked post notify
        pass
    
    # Redirect to the last page they were in or to the main page
    return '', 204


@blogs.route('/like_comment/<int:comment_id>')
@login_required
def like_comment(comment_id):
    # Like post
    try:
        current_user.like_comment(comment_id)
    except:
        # If user has already liked post notify
        pass
    
    # Redirect to the last page they were in or to the main page
    return '', 204


@blogs.route('/unlike_post/<int:post_id>')
@login_required
def unlike_post(post_id):
    # Like post
    try:
        current_user.unlike_post(post_id)
    except:
        # If user has already liked post notify
        pass
    
    # Redirect to the last page they were in or to the main page
    return '', 204


@blogs.route('/unlike_comment/<int:comment_id>')
@login_required
def unlike_comment(comment_id):
    # Like post
    try:
        current_user.unlike_comment(comment_id)
    except:
        # If user has already liked post notify
        pass
    
    # Redirect to the last page they were in or to the main page
    return '', 204

@blogs.route('/search_news')
def search_news():
    # Get query
    q = request.args.get('q')

    # Api key
    API_KEY = current_app.config['NEWS_API_KEY']

    # Get asked page
    news_page = request.args.get('news_page', 1, type=int)

    # Defining url
    url = f'https://newsapi.org/v2/top-headlines?q={q}&country=us&pageSize={current_app.config["POSTS_PER_PAGE"]}&page={news_page}&apiKey={API_KEY}'

    # Populate posts list
    response = requests.get(url)
    posts = []

    # Verify if a response was received
    if response.status_code == 200:
        posts = response.json()
        if posts['totalResults'] == 0:
            print(posts['totalResults'])
            flash("Couldn't find what you are looking for")
            return (redirect(url_for('blogs.news')))
    else:
        return '', 404
    
    posts = response['articles']

    # Get users widget context
    users_widget_context = get_users_widget_context()
    users = users_widget_context['users']
    users_pagination = users_widget_context['users_pagination']

    # Get posts
    posts_widget_context = get_posts_widget_context()
    other_posts = posts_widget_context['posts']

    # Define if there's next
    next = True
    if int(response['totalResults']) - (int(current_app.config['POSTS_PER_PAGE']) * int(news_page)) > 0:
        next = True
    else:
        next = False

    # Define if there's previous
    previous = False
    if news_page > 1:
        previous = True

    # Render template
    return render_template('blogs/news.html', posts=posts, users=users, users_pagination=users_pagination, other_posts=other_posts, news_page=news_page, next=next, previous=previous, q=q)


@blogs.route('/news')
def news():
    # Api key
    API_KEY = current_app.config['NEWS_API_KEY']

    # Get asked page
    news_page = request.args.get('news_page', 1, type=int)

    # Defining url
    url = f'https://newsapi.org/v2/top-headlines?country=us&pageSize={current_app.config["POSTS_PER_PAGE"]}&page={news_page}&apiKey={API_KEY}'

    # Populate posts list
    response = requests.get(url)
    posts = []

    # Verify if a response was received
    if response.status_code == 200:
        response = response.json()
        if response['totalResults'] == 0:
            flash("Couldn't find what you are looking for")
            return (request.referrer or redirect(url_for('main.index')) )
    else:
        flash("Couldn't load page")
        return '', 404
    
    # Define posts
    posts = response['articles']

    # Convert each date in posts to date objects
    for post in posts:
        post['publishedAt'] =  parser.parse(post['publishedAt'])
        
    # Get users widget context
    users_widget_context = get_users_widget_context()
    users = users_widget_context['users']
    users_pagination = users_widget_context['users_pagination']

    # Get posts
    posts_widget_context = get_posts_widget_context()
    other_posts = posts_widget_context['posts']

    # Define if there's next
    next = True
    if int(response['totalResults']) - (int(current_app.config['POSTS_PER_PAGE']) * int(news_page)) > 0:
        next = True
    else:
        next = False

    # Define if there's previous
    previous = False
    if news_page > 1:
        previous = True

    # Render template
    return render_template('blogs/news.html', posts=posts, users=users, users_pagination=users_pagination, other_posts=other_posts, news_page=news_page, next=next, previous=previous)


@blogs.route('/new_news_post/<topic>', methods=['GET', 'POST'])
@login_required
def new_news_post(topic):
    if request.method == "POST":
        # Initialize input variables
        title = request.form.get("title")
        body = request.form.get("body")
        files = request.files.getlist("files")

        # Check they are not null
        if not title:
            flash("Must enter a title")
            return render_template('blogs/new_post.html', topic=topic)
        if not body:
            flash("Must enter a body")
            return render_template('blogs/new_post.html', topic=topic)
        
        # Initialize Blog object
        blog = Blog(title=title, body=body, author=current_user.id, topic=topic)

        # Add blog to the database
        db.session.add(blog)
        db.session.commit()

        # Get blog object
        # Save files
        if files:
            files_len = len(files) 
            # Counter
            i = 1
            for file in files:
                # Avoid empty file
                if i == files_len:
                    break

                # Embbed filename with uuid and make sure the filename
                # is safe with secure_filename
                filename = f'{uuid1()} {secure_filename(file.filename)}'

                # Define static_path which is the relative path to look for the file for flask
                static_path = f"images/users/{current_user}/post files/{filename}"
                
                # Define server path
                path = os.path.join(current_app.config["UPLOAD_DIRECTORY"], str(current_user), 'post files')

                # If server path doesn't exists then create it
                if not os.path.exists(path):
                    os.makedirs(path)

                # Join server's path with the file's name
                filename = os.path.join(path, filename)

                # Save file
                file.save(filename)

                # Create file object, and add it to the session 
                file = File(path=static_path, blog_id=blog.id)
                print(file)
                db.session.add(file)
                i += 1

        # Commit after adding each file
        db.session.commit()

        # Redirect
        flash("Post created!")
        return redirect(url_for('main.index'))

    # If accesed view via GET method
    return render_template('blogs/new_post.html', topic=topic)


@blogs.route('/new_post', methods=['GET', 'POST'])
@login_required
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
        print("Post saved")

        # Get blog object
        # Save files
        if files:
            files_len = len(files) 
            # Counter
            i = 1
            for file in files:
                # Avoid empty file
                if i == files_len:
                    break

                # Embbed filename with uuid and make sure the filename
                # is safe with secure_filename
                filename = f'{uuid1()} {secure_filename(file.filename)}'

                # Define static_path which is the relative path to look for the file for flask
                static_path = f"images/users/{current_user}/post files/{filename}"
                
                # Define server path
                path = os.path.join(current_app.config["UPLOAD_DIRECTORY"], str(current_user), 'post files')

                # If server path doesn't exists then create it
                if not os.path.exists(path):
                    os.makedirs(path)

                # Join server's path with the file's name
                filename = os.path.join(path, filename)

                # Save file
                file.save(filename)

                # Create file object, and add it to the session 
                file = File(path=static_path, blog_id=blog.id)
                print(file)
                db.session.add(file)
                i += 1

        # Commit after adding each file
        db.session.commit()

        # Redirect
        flash("Post created!")
        return redirect(url_for('main.index'))

    # If accesed view via GET method
    return render_template('blogs/new_post.html')


@blogs.route('/post/<int:post_id>')
@login_required
def post(post_id):
    # Get post
    post = Blog.query.filter_by(id=post_id).first()

    # Render template
    return render_template("blogs/post.html", post=post)


@blogs.route('/reply_comment/<comment_id>')
def reply_comment(comment_id):
    if request.method == "POST":
        # Get body
        body = request.form.get("body")

        # Comment
        current_user.reply_comment(comment_id, body)

        # Redirect
        return redirect(url_for('main.index'))
    
    # If accesed view by GET method
    return render_template('blogs/comment.html')
    

   



