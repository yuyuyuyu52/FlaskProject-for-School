from flask import Flask, render_template, request, redirect, url_for, flash, session
import mysql.connector
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = 'asfwegewgdsf2e4t34dfge4'

def get_db_connection():
    connection = mysql.connector.connect(
        host="localhost",
        user="root",
        password="root",
        database="lms"
    )
    return connection

@app.route('/')
def index():
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)
        cursor.execute('SELECT * FROM users WHERE username = %s', (username,))
        user = cursor.fetchone()
        cursor.close()
        connection.close()
        if user and user['password']==password:
            session['user_id'] = user['id']
            session['username'] = user['username']
            session['role'] = user['role']
            if user['role'] == 'admin':
                return redirect(url_for('admin_dashboard'))
            elif user['role'] == 'teacher':
                return redirect(url_for('teacher_dashboard'))
            elif user['role'] == 'student':
                return redirect(url_for('student_dashboard'))
        flash('Invalid username or password')
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

# Admin routes
@app.route('/admin/dashboard')
def admin_dashboard():
    if 'role' not in session or session['role'] != 'admin':
        return redirect(url_for('login'))
    return render_template('admin_dashboard.html')

@app.route('/admin/create_account', methods=['GET', 'POST'])
def create_account():
    if 'role' not in session or session['role'] != 'admin':
        return redirect(url_for('login'))
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        role = request.form['role']
        connection = get_db_connection()
        cursor = connection.cursor()
        cursor.execute('INSERT INTO users (username, password, role) VALUES (%s, %s, %s)', (username, password, role))
        connection.commit()
        cursor.close()
        connection.close()
        flash('Account created successfully')
        return redirect(url_for('admin_dashboard'))
    return render_template('admin_create_account.html')

@app.route('/admin/create_course', methods=['GET', 'POST'])
def create_course():
    if 'role' not in session or session['role'] != 'admin':
        return redirect(url_for('login'))
    if request.method == 'POST':
        name = request.form['name']
        teacher_id = request.form['teacher_id']
        connection = get_db_connection()
        cursor = connection.cursor()
        cursor.execute('INSERT INTO courses (name, teacher_id) VALUES (%s, %s)', (name, teacher_id))
        connection.commit()
        cursor.close()
        connection.close()
        flash('Course created successfully')
        return redirect(url_for('admin_dashboard'))
    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)
    cursor.execute('SELECT id, username FROM users WHERE role = %s', ('teacher',))
    teachers = cursor.fetchall()
    cursor.close()
    connection.close()
    return render_template('admin_create_course.html', teachers=teachers)

@app.route('/admin/view_courses')
def admin_view_courses():
    if 'role' not in session or session['role'] != 'admin':
        return redirect(url_for('login'))
    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)
    cursor.execute('SELECT courses.id, courses.name, users.username AS teacher FROM courses JOIN users ON courses.teacher_id = users.id')
    courses = cursor.fetchall()
    cursor.close()
    connection.close()
    return render_template('admin_view_courses.html', courses=courses)

@app.route('/admin/view_accounts')
def view_accounts():
    if 'role' not in session or session['role'] != 'admin':
        return redirect(url_for('login'))
    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)
    cursor.execute('SELECT id, username, role FROM users')
    accounts = cursor.fetchall()
    cursor.close()
    connection.close()
    return render_template('admin_view_accounts.html', accounts=accounts)


@app.route('/admin/view_applications')
def view_applications():
    if 'role' not in session or session['role'] != 'admin':
        return redirect(url_for('login'))
    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)
    cursor.execute(
        'SELECT course_applications.id, users.username AS student, courses.name as course, course_applications.status '
        'FROM course_applications '
        'join users on course_applications.student_id = users.id '
        'join courses on course_applications.course_id = courses.id '
        'where status = "0" ')

    applications = cursor.fetchall()
    cursor.close()
    connection.close()
    return render_template('admin_view_applications.html', applications=applications)

@app.route('/admin/approve_application/<int:application_id>')
def approve_application(application_id):
    if 'role' not in session or session['role'] != 'admin':
        return redirect(url_for('login'))
    connection = get_db_connection()
    cursor = connection.cursor()
    cursor.execute('UPDATE course_applications SET status = %s WHERE id = %s', ('approved', application_id))
    connection.commit()
    cursor.close()
    connection.close()
    flash('Application approved')
    return redirect(url_for('view_applications'))

@app.route('/admin/reject_application/<int:application_id>')
def reject_application(application_id):
    if 'role' not in session or session['role'] != 'admin':
        return redirect(url_for('login'))
    connection = get_db_connection()
    cursor = connection.cursor()
    cursor.execute('UPDATE course_applications SET status = %s WHERE id = %s', ('rejected', application_id))
    connection.commit()
    cursor.close()
    connection.close()
    flash('Application rejected')
    return redirect(url_for('view_applications'))


# Teacher routes
@app.route('/teacher/dashboard')
def teacher_dashboard():
    if 'role' not in session or session['role'] != 'teacher':
        return redirect(url_for('login'))
    teacher_id = session['user_id']
    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)
    cursor.execute('SELECT * FROM courses WHERE teacher_id = %s', (teacher_id,))
    courses = cursor.fetchall()
    cursor.close()
    connection.close()
    return render_template('teacher_dashboard.html', courses=courses)



@app.route('/teacher/course/<int:course_id>', methods=['GET', 'POST'])
def view_course(course_id):
    if 'role' not in session or session['role'] != 'teacher':
        return redirect(url_for('login'))

    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)

    if request.method == 'POST':
        lecture_title = request.form['title']
        lecture_description = request.form['description']
        cursor.execute('INSERT INTO lectures (course_id, title, description) VALUES (%s, %s, %s)',
                       (course_id, lecture_title, lecture_description))
        connection.commit()
        flash('Lecture added successfully')

    cursor.execute('SELECT * FROM courses WHERE id = %s AND teacher_id = %s', (course_id, session['user_id']))
    course = cursor.fetchone()

    if not course:
        cursor.close()
        connection.close()
        flash('Course not found or you do not have permission to view this course.')
        return redirect(url_for('teacher_dashboard'))

    cursor.execute('SELECT * FROM lectures WHERE course_id = %s', (course_id,))
    lectures = cursor.fetchall()

    cursor.close()
    connection.close()

    return render_template('teacher_view_courses.html', course=course, lectures=lectures)


@app.route('/teacher/add_lecture/<int:course_id>', methods=['GET', 'POST'])
def add_lecture(course_id):
    if 'role' not in session or session['role'] != 'teacher':
        return redirect(url_for('login'))
    if request.method == 'POST':
        title = request.form['title']
        content = request.form['content']
        connection = get_db_connection()
        cursor = connection.cursor()
        cursor.execute('INSERT INTO lectures (course_id, title, content) VALUES (%s, %s, %s)', (course_id, title, content))
        connection.commit()
        cursor.close()
        connection.close()
        flash('Lecture added successfully')
        return redirect(url_for('view_course', course_id=course_id))
    return render_template('add_lecture.html', course_id=course_id)



@app.route('/teacher/lecture/<int:lecture_id>', methods=['GET', 'POST'])
def view_lecture(lecture_id):
    if 'role' not in session or session['role'] != 'teacher':
        return redirect(url_for('login'))

    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)

    if request.method == 'POST':
        if 'create_assignment' in request.form:
            assignment_title = request.form['assignment_title']
            assignment_description = request.form['assignment_description']
            cursor.execute('INSERT INTO assignments (lecture_id, title, description) VALUES (%s, %s, %s)',
                           (lecture_id, assignment_title, assignment_description))
            connection.commit()
            flash('Assignment created successfully')


    cursor.execute('SELECT * FROM lectures WHERE id = %s', (lecture_id,))
    lecture = cursor.fetchone()

    cursor.execute('SELECT * FROM assignments WHERE lecture_id = %s', (lecture_id,))
    assignments = cursor.fetchall()


    cursor.close()
    connection.close()

    return render_template('teacher_view_lecture.html', lecture=lecture, assignments=assignments)



@app.route('/teacher/add_assignment/<int:lecture_id>', methods=['GET', 'POST'])
def add_assignment(lecture_id):
    if 'role' not in session or session['role'] != 'teacher':
        return redirect(url_for('login'))
    if request.method == 'POST':
        title = request.form['title']
        description = request.form['description']
        connection = get_db_connection()
        cursor = connection.cursor()
        cursor.execute('INSERT INTO assignments (lecture_id, title, description) VALUES (%s, %s, %s)', (lecture_id, title, description))
        connection.commit()
        cursor.close()
        connection.close()
        flash('Assignment added successfully')
        return redirect(url_for('view_lecture', lecture_id=lecture_id))
    return render_template('add_assignment.html', lecture_id=lecture_id)

@app.route('/teacher/assignment/<int:assignment_id>')
def teacher_view_assignment(assignment_id):
    if 'role' not in session or session['role'] != 'teacher':
        return redirect(url_for('login'))
    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)
    cursor.execute('''
        SELECT submissions.id, submissions.content, users.username 
        FROM submissions 
        JOIN users ON submissions.student_id = users.id 
        WHERE assignment_id = %s AND grade IS  NULL;
    ''', (assignment_id,))
    submissions = cursor.fetchall()


    cursor.execute(f'''
    select title from assignments where id={assignment_id}
    ''')
    assignment_name=cursor.fetchall()
    cursor.close()
    connection.close()
    return render_template('teacher_view_assignment.html', submissions=submissions, assignment_name=assignment_name)

@app.route('/teacher/grade_submission/<int:submission_id>', methods=['POST'])
def grade_submission(submission_id):
    if 'role' not in session or session['role'] != 'teacher':
        return redirect(url_for('login'))
    if request.method == 'POST':
        grade = request.form['grade']
        connection = get_db_connection()
        cursor = connection.cursor()
        cursor.execute('UPDATE submissions SET grade = %s WHERE id = %s', (grade, submission_id))
        connection.commit()
        cursor.execute(f'''
        select assignment_id from submissions where id={submission_id};
        ''')
        assignment_id=cursor.fetchall()
        cursor.close()
        connection.close()
        flash('Grade submitted successfully')
        return redirect(url_for('teacher_view_assignment', assignment_id=assignment_id[0][0]))





# Student routes
@app.route('/student/dashboard')
def student_dashboard():
    if 'role' not in session or session['role'] != 'student':
        return redirect(url_for('login'))
    student_id = session['user_id']
    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)
    cursor.execute('SELECT courses.* FROM courses JOIN course_applications ON courses.id = course_applications.course_id WHERE course_applications.student_id = %s AND course_applications.status = %s', (student_id, 'approved'))
    courses = cursor.fetchall()
    cursor.execute('SELECT * FROM courses')
    all_courses = cursor.fetchall()
    cursor.execute('''
    SELECT * FROM course_applications WHERE status != 'approved';
    ''')
    have_applied=cursor.fetchall()
    difference = [item for item in all_courses if item not in courses]
    # Your data
    courses111 = difference
    applications = have_applied

    # Get the course_ids from the second list
    course_ids = [app['course_id'] for app in applications]

    # Filter the courses list to remove items with matching ids
    difference = [course for course in courses111 if course['id'] not in course_ids]


    cursor.close()
    connection.close()
    return render_template('student_dashboard.html', courses=courses, all_courses=difference)

@app.route('/student/apply_course/<int:course_id>')
def apply_course(course_id):
    if 'role' not in session or session['role'] != 'student':
        return redirect(url_for('login'))
    student_id = session['user_id']
    connection = get_db_connection()
    cursor = connection.cursor()
    cursor.execute('INSERT INTO course_applications (student_id, course_id,status) VALUES (%s, %s,%s)', (student_id, course_id,0))
    connection.commit()
    cursor.close()
    connection.close()
    flash('Application submitted successfully')
    return redirect(url_for('student_dashboard'))

@app.route('/student/course/<int:course_id>')
def student_view_course(course_id):
    if 'role' not in session or session['role'] != 'student':
        return redirect(url_for('login'))
    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)

    cursor.execute('SELECT * FROM lectures WHERE course_id = %s', (course_id,))
    lectures = cursor.fetchall()
    cursor.close()
    connection.close()
    return render_template('student_view_course.html', lectures=lectures, course_id=course_id)

@app.route('/student/lecture/<int:lecture_id>', methods=['POST','get'])
def student_view_lecture(lecture_id):
    if 'role' not in session or session['role'] != 'student':
        return redirect(url_for('login'))
    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)
    cursor.execute('SELECT * FROM assignments WHERE lecture_id = %s', (lecture_id,))
    assignments = cursor.fetchall()
    sql=f"select * from submissions where student_id ={session['user_id']};"
    cursor.execute(sql)
    have_submission=cursor.fetchall()
    list1 = assignments
    list2 = have_submission
    # 获取第二个列表中的 assignment_id
    assignment_ids = {item['assignment_id'] for item in list2}
    # 过滤第一个列表中的元素，去掉 id 在 assignment_ids 中的项
    filtered_list1 = [item for item in list1 if item['id'] not in assignment_ids]
    cursor.close()
    connection.close()
    return render_template('student_view_lecture.html', assignments=filtered_list1, lecture_id=lecture_id)

@app.route('/student/submit_assignment/<int:assignment_id>', methods=['POST'])
def submit_assignment(assignment_id):
    if 'role' not in session or session['role'] != 'student':
        return redirect(url_for('login'))
    if request.method == 'POST':
        content = request.form.get('submission')
        student_id = session['user_id']
        connection = get_db_connection()
        cursor = connection.cursor()
        cursor.execute('INSERT INTO submissions (assignment_id, student_id, content) VALUES (%s, %s, %s)', (assignment_id, student_id, content))
        connection.commit()
        cursor.execute(f'''
        select lecture_id from assignments where id={assignment_id}
        ''')
        lecture_id=cursor.fetchall()
        cursor.close()
        connection.close()
        flash('Assignment submitted successfully')
        return redirect(url_for('student_view_lecture', lecture_id=lecture_id[0][0]))
    return redirect()

@app.route('/student/view_grades')
def view_grades():
    if 'role' not in session or session['role'] != 'student':
        return redirect(url_for('login'))
    student_id = session['user_id']
    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)
  # 学生的 user_id
    student_user_id = student_id

    sql = """
    SELECT 
        s.content AS content,
        s.grade,
        a.title AS assignment,
        l.title AS lecture,
        c.name AS course,
        u.username AS teacher
    FROM 
        submissions s
    JOIN 
        assignments a ON s.assignment_id = a.id
    JOIN 
        lectures l ON a.lecture_id = l.id
    JOIN 
        courses c ON l.course_id = c.id
    JOIN 
        users u ON c.teacher_id = u.id
    WHERE 
        s.student_id = %s;
    """
    cursor.execute(sql, (student_user_id,))
    submissions_info = cursor.fetchall()
    cursor.close()
    connection.close()
    return render_template('view_grades.html',grades=submissions_info)

if __name__ == "__main__":
    app.run(debug=True)
