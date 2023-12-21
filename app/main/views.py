from datetime import datetime
from flask import render_template, session, redirect, url_for
from . import main
from .. import db
from ..models import User, Blog

@main.route('/', methods=['GET', 'POST'])
def index():
    # Get all posts from the blogs table ordered descended by date
    posts = Blog.query.order_by(Blog.date.desc()).all()

    # Render home template
    return render_template('home.html', posts=posts)