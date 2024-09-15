import pymysql
import pymysql.cursors
import sys

def connect_db():
    return pymysql.connect(host='localhost', user='root', db='notice',charset='utf8mb4', cursorclass=pymysql.cursors.DictCursor)

def init_db():
    db = pymysql.connect(host='localhost', user='root', charset='utf8mb4')
    try:
        with db.cursor() as cursor:
            cursor.execute("CREATE DATABASE IF NOT EXISTS notice")
            cursor.execute("USE notice")
            cursor.execute("CREATE TABLE IF NOT EXISTS User (id INTEGER AUTO_INCREMENT PRIMARY KEY, username VARCHAR(10) NOT NULL UNIQUE, password VARCHAR(20) NOT NULL, name varchar(5) NOT NULL, gender varchar(7) NOT NULL, birth DATE, school varchar(20) NOT NULL)")
            cursor.execute("SELECT * FROM User WHERE username = 'admin'")
            if not cursor.fetchone():
                cursor.execute("INSERT INTO User (id, username, password,name, gender, birth, school) VALUES (1,'admin','admin','관리자','male','2001-11-25','school')")
                db.commit()
            cursor.execute("CREATE TABLE IF NOT EXISTS Post (Post_id INTEGER AUTO_INCREMENT PRIMARY KEY, title VARCHAR(100) NOT NULL, content TEXT NOT NULL, time TIMESTAMP DEFAULT CURRENT_TIMESTAMP, user_id INTEGER, view INTEGER DEFAULT 0, filename varchar(100), post_password VARCHAR(20),FOREIGN KEY (user_id) REFERENCES User(id))")
    except Exception as e:
        print(f"오류 \n{e}")
        sys.exit()
    finally:
        db.close()

