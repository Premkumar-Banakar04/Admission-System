from doctest import debug
from flask import *
import secrets
import bcrypt
import sqlite3
import pandas as pd
from flask import send_file

app=Flask(__name__)
app.config['SECRET_KEY']=secrets.token_hex(16)

def admin():
    con=sqlite3.connect('database.db')
    cur=con.cursor()
    cur.execute('''CREATE TABLE IF NOT EXISTS admin(
                admin_id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                email_id TEXT UNIQUE NOT NULL,
                password BLOB NOT NULL
    )''')
    con.commit()
    con.close()
admin()

def student():
    con=sqlite3.connect('database.db')
    cur=con.cursor()
    cur.execute('''CREATE TABLE IF NOT EXISTS student(
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                std_id INTEGER UNIQUE,
                name TEXT NOT NULL,
                gender TEXT NOT NULL,
                course TEXT NOT NULL,
                sem INTEGER NOT NULL,
                fees REAL NOT NULL
    )''')
    con.commit()
    con.close()
student()

#create route to home
@app.route('/')
def home():
    return render_template('home.html')

#create a admin registration route
@app.route('/register',methods=['POST','GET'])
def register():
    if request.method=='POST':
        #get the form data
        username=request.form['name']
        username=str.upper(username)
        email=request.form['email']
        password=request.form['password']
        cpassword=request.form['cpassword']

        con = sqlite3.connect('database.db')
        cur = con.cursor()
        cur.execute("SELECT * FROM admin where email_id=?",(email,))
        existing_admin=cur.fetchone()

        #check if admin already registerd
        if existing_admin:
            con.close()
            return "<script> alert('Email Id is already taken, Please choose another..');window.location.href='/register';</script>"


        #check if passwords match
        if password!=cpassword:
            return "<script>alert('Password do not match');window.location.href='/register';</script>"
        
        #hash the password using bcrypt
        hashed_password=bcrypt.hashpw(password.encode('utf-8'),bcrypt.gensalt())

        # Insert admin details into the database
        cur.execute("INSERT INTO admin(name,email_id,password) VALUES(?,?,?)",(username,email,hashed_password))
        con.commit()
        con.close()
        return redirect(url_for('login'))
    return render_template('register.html')

#create a admin login route
@app.route('/login',methods=['POST','GET'])
def login():
    if request.method=='POST':
        email=request.form['email']
        password=request.form['password']

        con=sqlite3.connect('database.db')
        cur=con.cursor()
        cur.execute('SELECT email_id,password FROM admin where email_id=?',(email,))
        admin=cur.fetchone()
        con.close()

        if admin and bcrypt.checkpw(password.encode('utf-8'),admin[1]):
            session['admin_id']=admin[0]
            return "<script> alert('Login success'); window.location.href='/dashboard';</script>"
        else:
            return "<script> alert('Invalid username or password'); window.location.href='/login';</script>"
        
    return render_template('login.html')

#create a reset password route
@app.route('/reset_password',methods=['POST','GET'])
def reset_password():
    if request.method=='POST':
        email=request.form['email']
        newPassword=request.form['newPassword']

        #hash the new password
        hashed_password=bcrypt.hashpw(newPassword.encode('utf-8'),bcrypt.gensalt())

        con=sqlite3.connect('database.db')
        cur=con.cursor()
        cur.execute('UPDATE admin set password=? where email_id=?',(hashed_password,email))
        con.commit()
        con.close()

        return '<script>alert("Your password has been updated");window.location.href="/login";</script>'

    return render_template('reset_password.html')

#create a student dashboard route
@app.route('/dashboard',methods=['POST','GET'])
def dashboard():
    search_reg_no = request.args.get('reg_no')

    con=sqlite3.connect('database.db')
    cur=con.cursor()
    if search_reg_no:
        cur.execute('SELECT * FROM student WHERE std_id = ?', (search_reg_no,))
    else:
        cur.execute('SELECT * FROM student')
    students=cur.fetchall()
    con.close()

    return render_template('dashboard.html',students=students,search_reg_no=search_reg_no)

#create a admission route
@app.route('/admission',methods=['POST','GET'])
@app.route('/admission/<int:student_id>', methods=['POST', 'GET'])  
def admission(student_id=None):
    student_data = None

    if student_id:
        # Fetch existing student data
        con = sqlite3.connect('database.db')
        cur = con.cursor()
        cur.execute('SELECT * FROM student WHERE std_id=?', (student_id,))
        student_data = cur.fetchone()
        con.close()

    if request.method=='POST':
        reg_no=request.form['reg_no']
        sname=request.form['sname']
        sname=str.upper(sname)
        gender=request.form['gender']
        course=request.form['course']
        sem=request.form['sem']
        fees=request.form['fees']

        con=sqlite3.connect('database.db')
        cur=con.cursor()

        if student_id:
            # Update existing student record
            cur.execute('UPDATE student SET name=?, gender=?, course=?, sem=?, fees=? WHERE std_id=?',
                        (sname, gender, course, sem, fees, student_id))
        
        else:
            # Insert new student record
            cur.execute('INSERT INTO student (std_id, name, gender, course, sem, fees) VALUES(?,?,?,?,?,?)',
                        (reg_no, sname, gender, course, sem, fees))

        con.commit()
        con.close()

        return "<script>alert('Student information has been saved.'); window.location.href='/dashboard'</script>"

    return render_template('admission.html', student_data=student_data)


# Add a route for deleting a student record
@app.route('/delete_student/<int:student_id>', methods=['POST'])
def delete_student(student_id):
    con = sqlite3.connect('database.db')
    cur = con.cursor()
    cur.execute("DELETE FROM student WHERE std_id=?", (student_id,))
    con.commit()
    con.close()
    return redirect(url_for('dashboard'))


#Add a route for updating a student record
@app.route('/update_student/<int:student_id>', methods=['POST'])
def update_student(student_id):
    return redirect(url_for('admission', student_id=student_id))

# Route to generate and download Excel file
@app.route('/download_students', methods=['GET'])
def download_students():
    con = sqlite3.connect('database.db')
    cur = con.cursor()
    cur.execute('SELECT * FROM student')
    students = cur.fetchall()
    con.close()

    # Define column names
    column_names = ['ID', 'Register Number', 'Name', 'Gender', 'Course', 'Semester', 'Fees']

    # Create a DataFrame
    df = pd.DataFrame(students, columns=column_names)

    # Save the DataFrame to an Excel file
    excel_file_path = 'students.xlsx'
    df.to_excel(excel_file_path, index=False)

    return send_file(excel_file_path, as_attachment=True, download_name='students.xlsx')

# Route to logout
@app.route('/logout')
def logout():
    session.pop('admin_id', None)
    return redirect(url_for('home'))

if __name__ == '__main__':
    app.run(debug=True)