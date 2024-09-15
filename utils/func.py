from flask import render_template, request, redirect, url_for, session
from utils.db import connect_db
from utils.user import find_user
import os
import pymysql
import pymysql.cursors

UPLOAD_FOLDER = os.path.join(os.getcwd(), 'uploads')
ALLOWED_EXTENSIONS = set(['text', 'pdf', 'png', 'jpg', 'jpeg', 'gif'])

def func_page(app):
    def allow_file(filename):
        return '.' in filename and filename.rsplit('.', 1)[1] in ALLOWED_EXTENSIONS

    @app.route("/search", methods=['GET', 'POST'])
    def search():
        search_type = request.args.get('search_type', 'title')
        search_db = request.args.get('search_db', '').strip()
        if not search_db:
            return redirect(url_for('post'))
        try:
            db = connect_db()
            cursor = db.cursor(pymysql.cursors.DictCursor)
            cursor.execute("SELECT * FROM User WHERE id = %s", (session['user_id'],))
            current_user = cursor.fetchone()

            if search_type == 'all':
                cursor.execute("SELECT Post.Post_id, Post.title, User.username, Post.time, Post.view FROM Post JOIN User ON Post.user_id = User.id WHERE Post.title LIKE %s OR User.username LIKE %s OR Post.content LIKE %s ORDER BY Post.time DESC", (f'%{search_db}%', f'%{search_db}%', f'%{search_db}%'))
            elif search_type == 'title':
                cursor.execute("SELECT Post_id, Post.title, User.username, Post.time, Post.view FROM Post Join User ON Post.user_id = User.id WHERE Post.title LIKE %s ORDER BY time DESC", (f'%{search_db}%',))
            elif search_type == 'content':
                cursor.execute("SELECT Post.Post_id, Post.title, User.username, Post.time, Post.view FROM Post JOIN User ON Post.user_id = User.id WHERE Post.content LIKE %s ORDER BY Post.time DESC", (f'%{search_db}%',))
            elif search_type == 'writeman':
                cursor.execute("SELECT Post_id, Post.title, User.username, Post.time, Post.view FROM Post Join User ON Post.user_id = User.id WHERE User.username LIKE %s ORDER BY Post.time DESC", (f'%{search_db}%',))
            posts = cursor.fetchall()
        except Exception as e:
            return "error", 500
        finally:
            db.close()
            return render_template("post.html", posts=posts, search_db=search_db, search_type=search_type, current_user=current_user)

    @app.route("/create_post", methods=['GET', 'POST'])
    def create_post():
        global UPLOAD_FOLDER
        if 'user_id' not in session:
            return redirect(url_for('login'))

        if request.method == 'GET':
            return render_template('create_post.html')

        if request.method == 'POST':
            try:
                db = connect_db()
                cursor = db.cursor()
                create_title = request.form.get('title', '')
                create_content = request.form.get('content', '')
                post_pw = request.form.get('pw')
                file = request.files['file']

                cursor.execute("INSERT INTO Post(title, content, user_id, post_password) VALUES (%s, %s, %s, %s)", (create_title, create_content, session['user_id'], post_pw))

                Post_id = cursor.lastrowid

                post_folder = os.path.join(UPLOAD_FOLDER, str(Post_id))

                if not os.path.exists(post_folder):
                    os.makedirs(post_folder)

                if file and allow_file(file.filename):
                    filename = file.filename
                    filesave = os.path.join(post_folder, filename)
                    file.save(filesave)
                else:
                    filename = None

                cursor.execute("UPDATE Post SET filename = %s WHERE Post_id = %s", (filename, Post_id))

                db.commit()
                return redirect(url_for('post'))
            except Exception as e:
                db.rollback()
                print(e)
                return "error", 500

            finally:
                db.close()

    @app.route("/register", methods=['GET', 'POST'])
    def register():
        message = ""
        if request.method == 'POST':
            username = request.form.get('username')
            password = request.form.get('password')
            re_password = request.form.get("re_password")
            name = request.form.get("name")
            birth = request.form.get("birth")
            gender = request.form.get("gender")
            school = request.form.get("school")

            existing_user = find_user(username)
            if existing_user:
                message = "이미 존재합니다."
            elif password != re_password:
                message = "패스워드가 일치하지 않습니다."
            else:
                try:
                    db = connect_db()
                    cursor = db.cursor()
                    cursor.execute("INSERT INTO User (username, password, name, birth, gender, school) VALUES (%s, %s, %s, %s, %s, %s)",
                                   (username, password, name, birth, gender, school))
                    db.commit()
                    return redirect(url_for('login', success='1'))
                except Exception as e:
                    db.rollback()
                    message = f"회원가입 실패: {str(e)}"
                finally:
                    db.close()
        return render_template("register.html", message=message)

    @app.route("/logout")
    def logout():
        session.pop('user_id', None)
        return redirect(url_for('login'))
