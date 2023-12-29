from flask import abort, current_app, render_template, request, redirect, url_for, flash, make_response
from flask_login import current_user, login_required
from . import blogs
from ..models import Blog, Comment, Like, File, Notification, New
from .. import db
from ..main.views import get_users_widget_context, get_posts_widget_context
import os
import requests
from uuid import uuid1
from werkzeug.utils import secure_filename
from sqlalchemy import or_
from datetime import datetime
from dateutil import parser
from pprint import pprint

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
        return redirect(url_for('main.index'))
    except:
        return redirect(url_for('main.index'))


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
    print("\n\nUnliking post\n\n")
    # Like post
    #try:
    current_user.unlike_post(post_id)
    #except:
        # If user has already liked post notify
        #pass
    
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


def find_news(url, news_page, q=''):
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
    if q:
        return render_template('blogs/news.html', posts=posts, users=users, users_pagination=users_pagination, other_posts=other_posts, news_page=news_page, next=next, previous=previous, q=q)
    else:
        return render_template('blogs/news.html', posts=posts, users=users, users_pagination=users_pagination, other_posts=other_posts, news_page=news_page, next=next, previous=previous, q=q)
    

@blogs.route('/search_news')
def search_news():
    # Get query
    q = request.args.get('q')

    # Api key
    API_KEY = current_app.config['NEWS_API_KEY']

    # Get asked page
    news_page = request.args.get('news_page', 1, type=int)

    # Defining url
    # url = f'https://newsapi.org/v2/everything?q={q}&pageSize={current_app.config["POSTS_PER_PAGE"]}&page={news_page}&apiKey={API_KEY}'
    url = f'https://newsapi.org/v2/everything?q={q}&pageSize={current_app.config["POSTS_PER_PAGE"]}&page={news_page}&sortBy=popularity&apiKey={API_KEY}'

    # Render template
    return find_news(url, news_page, q)


@blogs.route('/news')
def news():
    # Api key
    API_KEY = current_app.config['NEWS_API_KEY']

    # Get asked page
    news_page = request.args.get('news_page', 1, type=int)

    # Define url
    url = f'https://newsapi.org/v2/top-headlines?country=us&pageSize={current_app.config["POSTS_PER_PAGE"]}&page={news_page}&apiKey={API_KEY}'

    # Find news
    return find_news(url, news_page)


@blogs.route('/new_post', methods=['GET', 'POST'])
@login_required
def new_post():
    new = request.args.get('new')
    responded_post = request.args.get('responded_post')

    if new and request.args.get('image'):
        new = New(author=request.args.get('author'), title=request.args.get('title'), content=request.args.get('content'), date=parser.parse(request.args.get('date')), url=request.args.get('url'), image=request.args.get('image'))
    elif new:
         new = New(author=request.args.get('author'), title=request.args.get('title'), content=request.args.get('content'), date=parser.parse(request.args.get('date')), url=request.args.get('url'))
    elif responded_post:
         # Fecth post which is being responded to
        responded_post = Blog.query.filter_by(id=responded_post).first()

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
        blog = ''

        # If post comes in response to a new
        if new:
            blog = Blog(title=title, body=body, author=current_user.id, new=new.id, responded_title=new.title)
            # Add blog to the database
            db.session.add(blog)
            db.session.commit()

        elif responded_post:
            # Create post
            blog = Blog(title=title, body=body, author=current_user.id, responded_blog=responded_post.id, responded_title=responded_post.title)
            # Add blog to the database
            db.session.add(blog)
            db.session.commit()
        else:
            blog = Blog(title=title, body=body, author=current_user.id)
            # Add blog to the database
            db.session.add(blog)
            db.session.commit()

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
                static_path = f'images/post files/{filename}'
                
                # Define server path
                path = os.path.join(current_app.config["UPLOAD_DIRECTORY"], 'post files')

                # If server path doesn't exists then create it
                if not os.path.exists(path):
                    os.makedirs(path)

                # Join server's path with the file's name
                filename = os.path.join(path, filename)

                # Save file
                file.save(filename)

                # Create file object, and add it to the session 
                file = File(path=static_path, blog_id=blog.id)
                db.session.add(file)
                i += 1

        # Commit after adding each file
        db.session.commit()

        # Redirect
        flash("Post created!")
        return redirect(url_for('main.index'))

    # If accesed view via GET method
    # If post comes with a response to a news
    if new:
        return render_template('blogs/new_post.html', new=new)
    if responded_post:
        return render_template('blogs/new_post.html', responded_post=responded_post)
    
    # Else
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
    

   



