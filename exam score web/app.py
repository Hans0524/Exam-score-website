import sqlite3

from flask import Flask, render_template, redirect, url_for, request, g, session
DATABASE = './assignment3.db'
app=Flask(__name__)


app.secret_key = 'stupidcovid'

def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE)
    return db

def make_dicts(cursor, row):
    return dict((cursor.description[idx][0], value)
                for idx, value in enumerate(row))

def query_db(query, args=(), one=False):
    cur = get_db().execute(query, args)
    rv = cur.fetchall()
    cur.close()
    return (rv[0] if rv else None) if one else rv
# this function gets called when the Flask app shuts down
# tears down the database connection
@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        # close the database if we are connected to it
        db.close()

Account_name=''
Account_type=''
user={}



@app.route('/')
def home():
	session.pop('user_id', None)
#if back to login page, you are kicked out of the session.
	return render_template('login.html')

@app.route('/login', methods=['GET','POST'])
def login():
	db = get_db()
	db.row_factory = make_dicts
	username = request.form['Account']
	password = request.form['Password']
	
	user = query_db('select * from users where username = ? and password = ?', [username, password], one = True)
	db.close()
	if  user == None:
		db.close()
		return render_template('login.html', message='Wrong password or account does not exist')
	global Account_name, Account_type
	Account_name = username
	session['user_id'] = username
	if user['type'] =='instructor':
		Account_type = 'instructor'
		return render_template('instructor.html')
	if user['type'] =='student':
		Account_type = 'student'
		return render_template('student.html')

@app.route("/signup/")
def sign():
	return render_template('signup.html')


@app.route('/signuppro', methods=['GET', 'POST'])
def sign_up():
	db = get_db()
	db.row_factory = make_dicts
	cur = db.cursor()
	new_username = request.form['Account']
	new_password = request.form['Password']
	new_type = request.form['Type']
	user = query_db('select * from users where username = ?', [new_username],one=True)
	if user != None:
		return render_template('signup.html', message='Account already exists! Choose another name!')
	cur.execute('insert into users (username, password, type) values (?, ?, ?)',[new_username, new_password,new_type])
	db.commit()
	cur.close()
	return render_template('login.html', congrats='You have created your account!')



@app.route('/getback', methods=['POST'])
def getback():
	if Account_type == 'student':
		return render_template('student.html')
	if Account_type == 'instructor':
		return render_template('instructor.html')

@app.route('/logout', methods=['POST'])
def logout():
	return redirect('/')

@app.route('/studentgrade')
def grade():
	if not ('user_id' in session and Account_type=='student'):
		return redirect('/')
	db = get_db()
	db.row_factory = make_dicts
	global user
	user = query_db('select * from marks where studentname = ?', [Account_name], one = True)
	db.close()
	return render_template('studentgrade.html', post=user)

@app.route('/instructorgrade', methods=['GET', 'POST'])
def instructorgrade():
	if not ('user_id' in session and Account_type=='instructor'):
		return redirect('/')
	db = get_db()
	db.row_factory = make_dicts
	marks = query_db('select * from marks')
	
	db.close()
	return render_template('instructorgrade.html',post = Account_name,marks = marks  )

@app.route('/instructorfeedback', methods=['GET', 'POST'])
def instructorfeedback():
	if not ('user_id' in session and Account_type=='instructor'):
		return redirect('/')
	db = get_db()
	db.row_factory = make_dicts
	feedbacks = query_db('select * from feedback where instructorname = ?', [Account_name])
	
	db.close()
	return render_template('instructorfeedback.html',post = Account_name, feedbacks = feedbacks )

@app.route('/remarkpage', methods=['GET', 'POST'])
def showremarkrequest():
	if not ('user_id' in session and Account_type=='instructor'):
		return redirect('/')
	db = get_db()
	db.row_factory = make_dicts
	requests = query_db('select * from remarkrequests')
	
	db.close()
	return render_template('instructorremark.html', requests=requests )



@app.route('/remark', methods=['POST'])
def sendremark():
	if not ('user_id' in session and Account_type=='student'):
		return redirect('/')
	db = get_db()
	db.row_factory = make_dicts
	cur = db.cursor()
	info = request.form
	cur.execute('insert into remarkrequests (studentname, reason, remarkof) values (?, ?, ?)', 
		[Account_name,
		info['reasoning'],
		info['test']])

	db.commit()
	cur.close()

	return render_template('studentgrade.html', post=user, send='Last request has been sent!') 





@app.route('/updatestudentmark', methods=['POST'])
def updatemark():
	if not ('user_id' in session and Account_type=='instructor'):
		return redirect('/')
	db = get_db()
	db.row_factory = make_dicts
	cur = db.cursor()
	student = request.form['studentname']
	requests = query_db('select * from remarkrequests')
	exist = query_db('select * from marks where studentname = ?', [student], one = True)
	if exist == None:
		return render_template('instructorremark.html', warning='No such student found!')
	test = request.form['test']
	newmark = request.form['newmark']
	cur.execute('update marks set '+ test +'=' + newmark + ' where studentname = ' +  "'" + student + "'")
	
	db.commit()
	cur.close()

	return render_template('instructorremark.html', message='Last remark has been done!', requests = requests) 

@app.route('/studentfeedback')
def studentfeedback():
	if not ('user_id' in session and Account_type == 'student'):
		return redirect('/')
	return render_template('studentfeedback.html')

@app.route('/sendfeedback')
def sendfeedback():
	if not ('user_id' in session and Account_type == 'student'):
		return redirect('/')
	db = get_db()
	db.row_factory = make_dicts
	cur = db.cursor()
	info = request.args.get
	cur.execute('insert into feedback (instructorname, feedback) values (?, ?)', [info('instructorname'), info('reasoning')])
	db.commit()
	cur.close()

	return render_template('studentfeedback.html')






@app.route('/home')
def general():
	if not 'user_id' in session:
		return redirect('/')
	return render_template('index.html')


@app.route('/assignments')
def assignments():
	if not 'user_id' in session:
		return redirect('/')
	return render_template('assignments.html')

@app.route('/calendar')
def calendar():
	if not 'user_id' in session:
		return redirect('/')
	return render_template('calendar.html')

@app.route('/feedback')
def feedback():
	if not 'user_id' in session:
		return redirect('/')
	return render_template('feedback.html')

@app.route('/instructor')
def instructor():
	if not ('user_id' in session and Account_type == 'instructor'):
		return redirect('/')
	return render_template('instructor.html')

@app.route('/labs')
def labs():
	if not 'user_id' in session:
		return redirect('/')
	return render_template('labs.html')

@app.route('/lectures')
def lectures():
	if not 'user_id' in session:
		return redirect('/')
	return render_template('lectures.html')

@app.route('/news')
def news():
	if not 'user_id' in session:
		return redirect('/')
	return render_template('news.html')

@app.route('/resources')
def resources():
	if not 'user_id' in session:
		return redirect('/')
	return render_template('resources.html')

@app.route('/tests')
def tests():
	if not 'user_id' in session:
		return redirect('/')
	return render_template('tests.html')




if __name__=="__main__":
	app.run(debug=True)