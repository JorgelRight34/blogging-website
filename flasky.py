import os
from app import create_app, db
from app.models import User, Blog, File, Follow
from flask_migrate import Migrate

if __name__=='__main__':
    app = create_app(os.getenv('FLASK_CONFIG') or 'default')
    app.run(debug=True)

@app.shell_context_processor
def make_shell_context():
    return dict(db=db, User=User, Blog=Blog, File=File, Follow=Follow)
