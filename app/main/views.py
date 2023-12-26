from flask import current_app, render_template, session, redirect, url_for, request, flash
from sqlalchemy import or_
from sqlalchemy.orm import Query
from . import main
from .. import db
from ..models import User, Blog

def get_posts_widget_context():
    # Get asked page by the response, the 'type=int' means that if the
    # asked page can't be converted to int then return the default value '1'
    page = request.args.get('posts_page', 1, type=int)

    # Get page of posts from the blogs table ordered descended by date 
    # return the asked page (set of elements), which has a set of elements of 
    # 3, error_out returns 404 when the asked elements per page exceeds the avaible
    posts_pagination = Blog.query.order_by(Blog.date.desc()).paginate(
        page=page, 
        per_page=current_app.config['POSTS_PER_PAGE'], 
        error_out=False
    )

    # Get posts items
    posts = posts_pagination.items

    return {'posts': posts, 'posts_pagination': posts_pagination}


def get_users_widget_context():
    # Get asked page by the response, the 'type=int' means that if the
    # asked page can't be converted to int then return the default value '1'
    page = request.args.get('users_page', type=int)

    # Get page of users from the users table ordered descended by date 
    # return the asked page (set of elements), which has a set of elements 
    # defined in the global variable 'POSTS_PER_PAGE', 
    # error_out returns 404 when the asked elements per page exceeds the avaible
    users_pagination = User.query.paginate(
        page=page, 
        per_page=current_app.config['USERS_PER_PAGE'], 
        error_out=False
    )

    # Get posts items
    users = users_pagination.items

    return {'users': users, 'users_pagination': users_pagination}

@main.route('/', methods=['GET', 'POST'])
def index():
    # Get posts widget context
    post_widget_context = get_posts_widget_context()
    posts = post_widget_context['posts']
    posts_pagination = post_widget_context['posts_pagination']

    # Get users widget context
    users_widget_context = get_users_widget_context()
    users = users_widget_context['users']
    users_pagination = users_widget_context['users_pagination']

    # Render home template
    return render_template('home.html', posts=posts, users=users, posts_pagination=posts_pagination, users_pagination=users_pagination)


@main.route('/search_post')
def search_post():
    # Get search's input
    search = f'%{request.args.get("q")}%'

    # Get asked page
    page = request.args.get('posts_page', 1, type=int)

    # Search post's titles like 'q'
    posts_pagination = Blog.query.filter(or_((Blog.body.ilike(search)), (Blog.title.ilike(search)))).paginate(
        page=page, per_page=current_app.config['POSTS_PER_PAGE'], error_out=False
    )

    # Define posts
    posts = posts_pagination.items

    # If there are not matches notify user
    if not posts:
        flash("No matches found")
        return redirect(request.referrer or url_for('main.index'))
    
    # Get posts widget context
    other_posts = Blog.query.limit(5).all()

    # Get users widget context
    users_widget_context = get_users_widget_context()
    users = users_widget_context['users']
    users_pagination = users_widget_context['users_pagination']

    # Render template
    return render_template('home.html', posts=posts, users=users, posts_pagination=posts_pagination, users_pagination=users_pagination, other_posts=other_posts)


@main.route('/search_user')
def search_user():
    # Get query
    q = f'%{request.args.get("q")}%'

    # Get asked page
    page = request.args.get('search_user_page', 1, type=int)

    # Return page of asked users
    pagination = User.query.filter((User.username.ilike(q))).paginate(
        page=page, per_page=current_app.config['USERS_PER_PAGE'], error_out=False
    )

    # Define users
    users = pagination.items

    # Get posts widget context
    post_widget_context = get_posts_widget_context()
    posts = post_widget_context['posts']

    # Get users widget context
    users_widget_context = get_users_widget_context()
    other_users = users_widget_context['users']
    other_users_pagination = users_widget_context['users_pagination']

    # Render template
    return render_template('auth/users.html', posts=posts, users=users, other_users=other_users, pagination=pagination, other_users_pagination=other_users_pagination, q=request.args.get('q'))
