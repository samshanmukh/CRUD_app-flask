from flask import Flask, render_template, flash, redirect, url_for, session, request, logging
from flask_mysqldb import MySQL
from wtforms import Form, StringField, TextAreaField, PasswordField, validators
from passlib.hash import sha256_crypt
from functools import wraps

app = Flask(__name__)

# Config MySQL
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = 'root'
app.config['MYSQL_DB'] = 'CRUD_app'
app.config['MYSQL_CURSORCLASS'] = 'DictCursor'

# init MySQL
mysql = MySQL(app)

# Home
@app.route('/')
def home():
	return render_template('home.html')

# About
@app.route('/about')
def about():
	return render_template('about.html')

# Articles
# from data import Articles
# Articles = Articles()
@app.route('/articles')
def articles():
	# Cretae cursor
	cur = mysql.connection.cursor()

	# Get articles
	result = cur.execute("SELECT * FROM articles")

	articles = cur.fetchall()

	if result > 0:
		return render_template('articles.html', articles = articles)
	else:
		msg = 'No Articles Found'
		return render_template('articles.html', msg = msg)

	# Close connection
	cur.close()

# Article by Id
@app.route('/article/<string:id>/')
def article(id):
	# Create cursor
	cur = mysql.connection.cursor()

	# Get Article
	result = cur.execute("SELECT * FROM articles WHERE id = %s", [id])

	artcile = cur.fetchone()

	return render_template('article.html', article = artcile)

# User Registration Form Class
class RegisterForm(Form):
	name = StringField('Name', [validators.Length(min=1, max=50)])
	email = StringField('Email', [validators.Length(min=6, max=50)])
	username = StringField('Username', [validators.Length(min=4, max=25)])
	password = PasswordField('Password', [
			validators.DataRequired(),
			validators.EqualTo('confirm', message='Password do not match')
		])
	confirm = PasswordField('Confirm Password')

# User Registration
@app.route('/register', methods=['GET', 'POST'])
def register():
	form = RegisterForm(request.form)
	if request.method == 'POST' and form.validate():
		name = form.name.data
		email = form.email.data
		username = form.username.data
		password = sha256_crypt.encrypt(str(form.password.data))

		# Crreate a cursor
		cur = mysql.connection.cursor()

		# Execute query
		cur.execute("INSERT INTO users(name, email, username, password) VALUES(%s, %s, %s, %s)", (name, email, username, password))

		# Commit to DB
		mysql.connection.commit()

		# Close the connection
		cur.close()

		flash('You are now registered and can login', 'success')

		return redirect(url_for('home'))

	return render_template('register.html', form = form)

# User Login
@app.route('/login', methods=['GET', 'POST'])
def login():
	if request.method == 'POST':
		# Get Form Fields
		username = request.form['username']
		password_candidate = request.form['password']

		# Create a cursor
		cur = mysql.connection.cursor()

		# Get user by username
		result = cur.execute("SELECT * FROM users WHERE username = %s", [username])

		if result > 0:
			# Get the stored hash
			data = cur.fetchone()
			password = data['password']

			# Compare the passwords
			if sha256_crypt.verify(password_candidate, password):
				# password matched
				session['logged_in'] = True
				session['username'] = username

				flash('Login successful!', 'success')
				return redirect(url_for('dashboard'))
			else:
				error = 'Invalid login!'
				return render_template('login.html', error = error)
			# Close connection
			cur.close()
		else:
			error = 'Username not found!'
			return render_template('login.html', error = error)

	return render_template('login.html')

# Check if users are logged in
def is_logged_in(f):
	@wraps(f)
	def wrap(*args, **kwargs):
		if 'logged_in' in session:
			return f(*args, **kwargs)
		else:
			flash('Unautherized!, Please login to your account.', 'danger')
			return redirect(url_for('login'))
	return wrap

# User Logout
@app.route('/logout')
@is_logged_in
def logout():
	session.clear()
	flash('You are logged out!', 'success')
	return redirect(url_for('login'))

# User Dashboard
@app.route('/dashboard')
@is_logged_in
def dashboard():
	# Cretae cursor
	cur = mysql.connection.cursor()

	# Get articles
	result = cur.execute("SELECT * FROM articles")

	articles = cur.fetchall()

	if result > 0:
		return render_template('dashboard.html', articles = articles)
	else:
		msg = 'No Articles Found'
		return render_template('dashboard.html', msg = msg)

	# Close connection
	cur.close()


# Articles Form Class
class ArticleForm(Form):
	title = StringField('Title', [validators.Length(min=1, max=200)])
	body = TextAreaField('Body', [validators.Length(min=30)])

# Add Articles
@app.route('/add_article', methods=['GET', 'POST'])
@is_logged_in
def add_article():
	form = ArticleForm(request.form)
	if request.method == 'POST' and form.validate():
		title = form.title.data
		body = form.body.data

		# Create cursor
		cur = mysql.connection.cursor()

		# Execute
		cur.execute("INSERT INTO articles(title, body, author) VALUES(%s,%s,%s)", (title, body, session['username']))

		# Commit
		mysql.connection.commit()

		# Close connection
		cur.close()

		flash('Article Created!', 'success')

		return redirect(url_for('dashboard'))

	return render_template('add_article.html', form=form)

# Edit Articles
@app.route('/edit_article/<string:id>', methods=['GET', 'POST'])
@is_logged_in
def edit_article(id):
	# Create cursor
	cur = mysql.connection.cursor()

	# Get article by id
	result = cur.execute("SELECT * FROM articles WHERE id = %s", [id])

	article = cur.fetchone()

	# Get From
	form = ArticleForm(request.form)

	# Populate article form Fields
	form.title.data = article['title']
	form.body.data = article['body']

	if request.method == 'POST' and form.validate():
		title = request.form['title']
		body = request.form['body']

		# Create cursor
		cur = mysql.connection.cursor()

		# Execute
		cur.execute("UPDATE articles SET title=%s, body=%s WHERE id=%s", (title, body, [id]))

		# Commit
		mysql.connection.commit()

		# Close connection
		cur.close()

		flash('Article Updated!', 'success')

		return redirect(url_for('dashboard'))

	return render_template('edit_article.html', form=form)

# Delete Article
@app.route('/delete_article/<string:id>', methods=['POST'])
@is_logged_in
def delete_article(id):
	# Cretae cursor
	cur = mysql.connection.cursor()

	# Execute
	cur .execute("DELETE FROM articles WHERE id = %s", [id])

	# Commit to DB
	mysql.connection.commit()

	# Close connection
	cur.close()

	flash('Article Deleted!', 'success')

	return redirect(url_for('dashboard'))


if __name__ == '__main__':
	app.secret_key='shanmukh@sain'
	app.run(debug=True)
