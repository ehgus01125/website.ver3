from flask import render_template, request, redirect, url_for, session, send_file, flash
from utils.db import connect_db
import pymysql
import pymysql.cursors
import os

UPLOAD_FOLDER = os.path.join(os.getcwd(), 'images')
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def king(user_id):
        db = connect_db()
        cursor = db.cursor(pymysql.cursors.DictCursor)
        cursor.execute("SELECT username FROM User WHERE id = %s", (user_id,))
        user=cursor.fetchone()
        db.close()
        return user and user['username'] == 'admin'

def find_user(username):
        db = connect_db()
        cursor = db.cursor()
        cursor.execute("SELECT * FROM User WHERE username = %s", (username,))
        user = cursor.fetchone()
        db.close()
        if user:
            return user
        else : 
            return None

def check_password(username, password):
        user = find_user(username)
        if user and user['password'] == password:
            return True
        return False

def root_page(app):
    @app.route("/", methods=['GET', 'POST'])
    def login():
        if request.method == 'POST':
            username = request.form['username']
            password = request.form['password']

            if not username or not password:
                return render_template("index.html", message="제대로 입력해주세요.")
            
            if check_password(username, password):
                user = find_user(username)
                session['user_id'] = user['id']
                return redirect(url_for('post'))
            else:
                return render_template("index.html", message="로그인 실패")
        return render_template("index.html", success=request.args.get('success'))
    
    @app.route("/profile", methods=['GET','POST'])
    def profile():
        if 'user_id' not in session:
            return redirect(url_for('login'))
        
        user_id=session['user_id']

        db = connect_db()
        cursor = db.cursor(pymysql.cursors.DictCursor)

        cursor.execute("SELECT * FROM User WHERE id = %s", (user_id,))
        user = cursor.fetchone()
        db.close()

        profile_img = get_profile_image(user_id)

        return render_template("profile.html", user = user, profile_img=profile_img)
    
    @app.route("/profile_edit", methods=['GET', 'POST'])
    def profile_edit():
        if 'user_id' not in session:
            return redirect(url_for('login'))

        user_id = session['user_id']
        db = connect_db()
        cursor = db.cursor(pymysql.cursors.DictCursor)

        if request.method == 'POST':
            name = request.form['name']
            gender = request.form['gender']
            school = request.form['school']

            cursor.execute("UPDATE User SET name=%s, gender=%s, school=%s WHERE id=%s", (name, gender, school, user_id))
            db.commit()

            if 'img' in request.files:
                file = request.files['img']
                if file and allowed_file(file.filename):
                    filename = f"profile_{user_id}.{file.filename.rsplit('.', 1)[1].lower()}"
                    file.save(os.path.join(UPLOAD_FOLDER, filename))

            db.close()
            return redirect(url_for('profile'))

        cursor.execute("SELECT * FROM User WHERE id = %s", (user_id,))
        user = cursor.fetchone()
        db.close()

        return render_template("profile_edit.html", user=user)

    @app.route("/images/<path:filename>")
    def serve_image(filename):
        return send_file(os.path.join(UPLOAD_FOLDER, filename))
    
    @app.route("/users")
    def user_list():
        if 'user_id' not in session:
            return redirect(url_for('login'))
        
        db = connect_db()
        cursor = db.cursor(pymysql.cursors.DictCursor)
        cursor.execute("SELECT id, username, name FROM User")
        users = cursor.fetchall()
        db.close()

        for user in users:
            user['admin'] = king(user['id'])

        return render_template("user_list.html", users=users)
    
    @app.route("/user/<int:user_id>")
    def user_profile(user_id):
        if 'user_id' not in session:
            return redirect(url_for('login'))
        
        db = connect_db()
        cursor = db.cursor(pymysql.cursors.DictCursor)
        cursor.execute("SELECT * FROM User WHERE id = %s", (user_id,))
        user = cursor.fetchone()
        db.close()

        profile_img = get_profile_image(user_id)
        is_own_profile = session['user_id'] == user_id

        return render_template("user_profile.html", user=user, profile_img=profile_img, is_own_profile=is_own_profile)
    
    @app.route('/recovery', methods=['GET', 'POST'])
    def recovery():
        if request.method == 'POST':
            action = request.form.get('action')
            
            if action == 'find_id':
                name = request.form['name']
                gender = request.form['gender']
                school = request.form['school']
                
                db = connect_db()
                cursor = db.cursor(pymysql.cursors.DictCursor)
                cursor.execute("SELECT username FROM User WHERE name = %s AND gender = %s AND school = %s", (name, gender, school))
                user = cursor.fetchone()
                db.close()

                if user:
                    flash(f"당신의 아이디는 {user['username']}입니다.")
                else:
                    flash("일치하는 사용자 정보가 없습니다.")
            
            elif action == 'reset_password':
                username = request.form['username']
                birth = request.form['birth']
                school = request.form['school']
                
                db = connect_db()
                cursor = db.cursor(pymysql.cursors.DictCursor)
                cursor.execute("SELECT id FROM User WHERE username = %s AND birth = %s AND school = %s", (username, birth, school))
                user = cursor.fetchone()
                db.close()

                if user:
                    session['reset_user_id'] = user['id']
                    return redirect(url_for('set_new_password'))
                else:
                    flash("일치하는 사용자 정보가 없습니다.")
            
            return redirect(url_for('recovery'))
        
        return render_template('recovery.html')

    @app.route('/set_new_password', methods=['GET', 'POST'])
    def set_new_password():
        if 'reset_user_id' not in session:
            return redirect(url_for('recovery'))

        if request.method == 'POST':
            new_password = request.form['new_password']
            confirm_password = request.form['confirm_password']

            if new_password != confirm_password:
                flash("비밀번호가 일치하지 않습니다.")
                return redirect(url_for('set_new_password'))

            db = connect_db()
            cursor = db.cursor()
            cursor.execute("UPDATE User SET password = %s WHERE id = %s", (new_password, session['reset_user_id']))
            db.commit()
            db.close()

            session.pop('reset_user_id', None)
            flash("비밀번호가 성공적으로 변경되었습니다.")
            return redirect(url_for('login'))

        return render_template('new_password.html')

def get_profile_image(user_id):
    for ext in ALLOWED_EXTENSIONS:
        profile_pic_path = os.path.join(UPLOAD_FOLDER, f"profile_{user_id}.{ext}")
        if os.path.exists(profile_pic_path):
            return f"/images/profile_{user_id}.{ext}"
    return "/images/default.jpg"