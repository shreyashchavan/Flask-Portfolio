from flask import Flask, render_template, redirect, request, url_for
from flask_login import logout_user, LoginManager, current_user, login_required, login_user
import sqlite3
from sqlite3 import IntegrityError
from datetime import date
from flask_login import UserMixin
from flask_mail import Mail, Message


app= Flask(__name__)
app.secret_key = 'your secret key'

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'admin'


app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 465
app.config['MAIL_USE_SSL'] = True
app.config['MAIL_USERNAME'] = 'wredmansola@gmail.com'
app.config['MAIL_PASSWORD'] = 'Shreyash@77'

mail = Mail(app)


class User(UserMixin):
    def __init__(self, email, password, name):
        self.email = email
        self.password = password
        self.author = name
    
    def is_authenticated(self):
        return True
    
    def get_id(self):
        return self.email


@login_manager.user_loader
def load_user(email):
    conn = sqlite3.connect('mydatabase.db')
    c = conn.cursor()
    c.execute("SELECT * FROM users WHERE email=?", (email,))
    user = c.fetchone()
    if user:
        return User(user[0], user[1], user[2])
    return None


@app.route('/')
def index():
    return render_template('index.html')

@app.route('/portfolio')
def portfolio():
    return render_template('portfolio.html')

@app.route('/contact')
def contact():
    return render_template('contact.html')

@app.route('/resume')
def resume():
    file = 'static/resume.pdf'
    return render_template('resume.html', file=file)

@app.route('/blogs/<int:page>')
def all_blog(page):
    per_page = 4 
    offset = (page - 1) * per_page
    conn = sqlite3.connect('mydatabase.db')
    c = conn.cursor()
    c.execute('SELECT * FROM blogs ORDER BY publihed_at DESC LIMIT ? OFFSET ?', (per_page, offset,))
    files = c.fetchall()
    c.execute('SELECT COUNT(*) FROM blogs')
    total = c.fetchone()[0]    
    pages = total // per_page + 1
    return render_template('blog.html', files=files, page=page, pages=pages)

@app.route('/<id>')
def content(id):
    conn = sqlite3.connect('mydatabase.db')
    c = conn.cursor()
    c.execute("SELECT content,author,publihed_at,title,image FROM blogs WHERE title=?", (id,))
    blog = c.fetchall()
    return render_template('single.html', content=blog , id=id)

@app.route('/send', methods=['POST','GET'])
def msg():
    if request.method == 'POST':
        name= request.form['fullname']
        email = request.form['email']
        msg = request.form['message']
        msg = Message(subject='Contact Form',
                  sender=app.config['MAIL_USERNAME'],
                  recipients=['shreyashchavan77@gmail.com'],
                  body=f'From: {name}\nEmail: {email}\nMessage: {msg}')
        mail.send(msg) 
        return redirect( url_for('msg'))
    return redirect(url_for('contact')) 


@app.route('/admin-panel', methods=['POST','GET'])
def admin():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        conn = sqlite3.connect('mydatabase.db')
        c = conn.cursor()
        c.execute("SELECT email, password, name FROM users WHERE email=?", (email,))
        user = c.fetchone()
        if user and email == user[0] and password == user[1]:
            login_user(load_user(email))
        else:
            return render_template('admin.html', msg="Try again")
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    else:
        return render_template('admin.html')


@app.route('/dashboard')
@login_required
def dashboard():
    msg=""
    error=""
    if request.args:
        msg=request.args.get['msg']
        error = request.args.get['error']
    conn = sqlite3.connect('mydatabase.db')
    c = conn.cursor()
    c.execute("SELECT * FROM blogs")
    blogs = c.fetchall()
    if current_user.is_authenticated:
        if error or msg:
            return render_template('admin-index.html', blogs=blogs, msg=msg, error=error)
        else:
            return render_template('admin-index.html', blogs=blogs)


@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('admin'))
            

@app.route('/edit/<id>')
@login_required
def edit(id):
    conn = sqlite3.connect('mydatabase.db')
    c = conn.cursor()
    c.execute("SELECT * FROM blogs where id=?",(id,))
    res = c.fetchone()
    return render_template('editpost.html', blog=res)

@app.route('/save/<id>', methods=['POST'])
@login_required
def save(id):
    title = request.form['title']
    published = request.form['created']
    content = request.form['editPostEditor']
    file = request.files['image']
    file.save('static/images/'+ file.filename)
    link = 'images/' + file.filename
    conn = sqlite3.connect('mydatabase.db')
    c = conn.cursor()
    c.execute("UPDATE blogs SET title=?, publihed_at=?, content=?, image=? where id=?",(title,published,content,link,id))
    conn.commit()
    conn.close()
    return redirect(url_for('edit', id=id) )

@app.route('/users')
@login_required
def users():
    conn = sqlite3.connect('mydatabase.db')
    c = conn.cursor()
    c.execute("select * from users")
    users = c.fetchall()
    return render_template('users.html', users= users)

@app.route('/adduser', methods=['POST'])
@login_required
def adduser():
    email = request.form['email']
    name = request.form['name']
    password = request.form['pass']
    conn = sqlite3.connect('mydatabase.db')
    c = conn.cursor()
    c.execute("INSERT INTO users (name, email, password) VALUES (?,?,?)",(name, email, password))
    if c.rowcount == 1:
        conn.commit()
        conn.close()
        return render_template('users.html', users= users, msg="User added successfully")
    else:
        conn.close()
        return render_template('users.html', users= users, msg="Error adding user")

@app.route('/delete/<id>')
@login_required
def delete(id):
    conn = sqlite3.connect('mydatabase.db')
    c = conn.cursor()
    c.execute("DELETE FROM blogs WHERE id=?",(id,))
    conn.commit()
    conn.close()
    return redirect(url_for('dashboard'))

@app.route('/submit', methods=['POST'])
@login_required
def submit():
    title = request.form['title']
    content = request.form['addPostEditor']
    file = request.files['img']
    today = date.today()
    author = current_user.author
    file.save('static/images/'+ file.filename)
    link = 'images/' + file.filename
    conn = sqlite3.connect('mydatabase.db')
    c = conn.cursor()
    c.execute("INSERT INTO blogs (content,title,author,publihed_at, image) VALUES (?,?,?,?,?)",(content,title,author,today,link,))
    try:
        conn.commit()
    except IntegrityError:
        conn.rollback()
        return redirect(url_for('dashboard'), error="Add more lines")  
    conn.close()
    return redirect(url_for('dashboard'))   

if __name__ == '__main__':
    app.run(debug=True)