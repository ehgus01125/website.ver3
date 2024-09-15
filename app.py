from flask import Flask
from utils.db import init_db
import os



def create_app():
    app = Flask(__name__)
    app.secret_key = 'ddd'
    
    from utils.func import func_page
    from utils.post import post_page
    from utils.user import root_page

    func_page(app)
    post_page(app)
    root_page(app)
    
    return app

if __name__ == "__main__":
    app = create_app()
    init_db()
    app.run(debug=True)