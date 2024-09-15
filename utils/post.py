from flask import render_template, request, redirect, url_for, session, send_file
from utils.db import connect_db
import os
import pymysql
import pymysql.cursors
from utils.user import king

UPLOAD_FOLDER = os.path.join(os.getcwd(),'uploads')
ALLOWED_EXTENSIONS = {'text', 'pdf', 'png', 'jpg', 'jpeg', 'gif'}

def post_page(app):
    def allow_file(filename):
        return '.' in filename and filename.rsplit('.',1)[1] in ALLOWED_EXTENSIONS

    @app.route("/post")
    def post():
        try:
            if 'user_id' not in session:
                return redirect(url_for('login'))

            db = connect_db()
            cursor = db.cursor(pymysql.cursors.DictCursor)

            cursor.execute("SELECT * FROM User WHERE id = %s", (session['user_id'],))
            current_user = cursor.fetchone()

            king = current_user['username'] == 'admin'

            cursor.execute("SELECT Post.Post_id, Post.user_id, Post.title, Post.post_password, User.username, Post.time, Post.view FROM Post JOIN User ON Post.user_id = User.id ORDER BY Post.time DESC ")
            posts = cursor.fetchall()

            for post in posts:
                post_password = post.get('post_password', '').strip()
                post['is_locked'] = bool(post_password)

            return render_template("post.html", current_user=current_user, posts=posts, king=king)
        except Exception as e:
            print(e)
            return "error", 500
        finally:
            db.close()


    @app.route("/post/<int:Post_id>", methods=['GET'])
    def read_post(Post_id):
        if 'user_id' not in session:
            return redirect(url_for('login'))
        
        try:
            db = connect_db()
            cursor = db.cursor(pymysql.cursors.DictCursor)
            cursor.execute("SELECT Post.*, User.username FROM Post JOIN User ON Post.user_id = User.id WHERE Post.Post_id = %s", (Post_id,))
            post = cursor.fetchone()
            
            current_user = session['user_id']
            admin = king(current_user)
            
            if post['post_password'] and not admin:
                return redirect(url_for('check_post_password', Post_id=Post_id))
            
            cursor.execute("UPDATE Post SET view = view + 1 WHERE Post_id = %s", (Post_id,))
            db.commit()
            return render_template("read_post.html", post=post, current_user=current_user, king=admin)
        except Exception as e:
            print(e)
            return "error", 400
        finally:

            db.close()

    @app.route("/post/<int:Post_id>/check_password", methods=['GET', 'POST'])
    def check_password(Post_id):
        if 'user_id' not in session:
            return redirect(url_for('login'))

        current_user = session['user_id']
        admin = king(current_user)

        if admin:
            return redirect(url_for('read_post', Post_id=Post_id))

        if request.method == 'POST':
            password = request.form.get('password')
            db = connect_db()
            cursor = db.cursor(pymysql.cursors.DictCursor)
            cursor.execute("SELECT * FROM Post WHERE Post_id = %s", (Post_id,))
            post = cursor.fetchone()
            
            if post and post['post_password'] == password:
                cursor.execute("UPDATE Post SET view = view + 1 WHERE Post_id = %s", (Post_id,))
                db.commit()
                db.close()
                return redirect(url_for('read_post', Post_id=Post_id))
            else:
                db.close()
                return render_template("post_password.html", Post_id=Post_id, error="비밀번호가 일치하지 않습니다.")

        return render_template("post_password.html", Post_id=Post_id)


    @app.route("/post/<int:Post_id>/edit", methods=['GET','POST'])
    def edit_post(Post_id):
        if 'user_id' not in session:
            return redirect(url_for('login'))
        
        db = connect_db()
        cursor = db.cursor(pymysql.cursors.DictCursor)
        cursor.execute("SELECT * FROM Post WHERE Post_id = %s", (Post_id,))
        post = cursor.fetchone()

        if post['user_id'] != session['user_id']:
            db.close()
            return render_template('edit_post.html', error_message="수정 할 수 없습니다.")

        if request.method =='POST':
            title=request.form['title']
            content=request.form['content']
            post_pw = request.form.get('pw')
            file = request.files['file']

            file_path = os.path.join(UPLOAD_FOLDER, str(Post_id))
            if not os.path.exists(file_path):
                    os.makedirs(file_path)

            if file and allow_file(file.filename):
                    filename = file.filename
                    filesave = os.path.join(file_path, filename)
                    file.save(filesave)
            else: filename = post['filename']
            
            if not post_pw:
                post_pw = None

            if not title or not content:
                return render_template('edit_post.html', post=post, error_message="빈칸이 있습니다.")

            cursor.execute("UPDATE Post SET title = %s, content = %s, filename = %s, post_password = %s WHERE Post_id = %s", (title, content, filename, post_pw, Post_id))

            db.commit()
            db.close()
            return redirect(url_for('read_post', Post_id=Post_id))
        db.close()
        return render_template('edit_post.html', post=post)

    @app.route("/post/<int:Post_id>/delete", methods=['POST'])
    def delete_post(Post_id):
        if 'user_id' not in session:
            return redirect(url_for('login'))
        
        try:
            db = connect_db()
            cursor = db.cursor(pymysql.cursors.DictCursor)
            cursor.execute("SELECT * FROM Post WHERE Post_id = %s", (Post_id,))
            post = cursor.fetchone()
            if post:
                if post['user_id'] == session['user_id'] or king(session['user_id']):
                    cursor.execute("DELETE FROM Post WHERE Post_id = %s", (Post_id,))
                    db.commit()
                    return redirect(url_for("post"))
        except Exception as e:
            print(e)
        finally:
            db.close()

    @app.route("/post/<int:Post_id>/download")
    def download_file(Post_id):
        if 'user_id' not in session:
            return redirect(url_for('login'))
        try:
            db = connect_db()
            cursor = db.cursor(pymysql.cursors.DictCursor)
            cursor.execute("SELECT filename FROM post WHERE Post_id = %s", (Post_id,))
            post = cursor.fetchone()

            if post and post['filename']:
                file_path = os.path.join(UPLOAD_FOLDER, str(Post_id), post['filename'])
                if os.path.exists(file_path):
                    return send_file(file_path, as_attachment=True)
                else :
                    return "File not FOUND", 404
            else: return "File not FOUND", 404 
        except Exception as e:
            return "error", 500
        finally: db.close()
