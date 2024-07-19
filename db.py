import mysql.connector
from mysql.connector import errorcode

# Database configuration
config = {
    'user': 'root',
    'password': 'root',
    'host': '127.0.0.1',
    'database': 'lms',
    'raise_on_warnings': True
}

# Connect to MySQL server
try:
    connection = mysql.connector.connect(
        user=config['user'],
        password=config['password'],
        host=config['host']
    )
    cursor = connection.cursor()

    # Create database
    try:
        cursor.execute(f"CREATE DATABASE {config['database']}")
    except mysql.connector.Error as err:
        if err.errno == errorcode.ER_DB_CREATE_EXISTS:
            print("Database already exists.")
        else:
            print(err.msg)

    # Select the database
    connection.database = config['database']

    # Create tables
    tables = {}

    tables['users'] = (
        "CREATE TABLE `users` ("
        "  `id` int(11) NOT NULL AUTO_INCREMENT,"
        "  `username` varchar(50) NOT NULL,"
        "  `password` varchar(255) NOT NULL,"
        "  `role` varchar(20) NOT NULL,"
        "  PRIMARY KEY (`id`)"
        ") ENGINE=InnoDB"
    )

    tables['courses'] = (
        "CREATE TABLE `courses` ("
        "  `id` int(11) NOT NULL AUTO_INCREMENT,"
        "  `name` varchar(100) NOT NULL,"
        "  `teacher_id` int(11) NOT NULL,"
        "  PRIMARY KEY (`id`),"
        "  FOREIGN KEY (`teacher_id`) REFERENCES `users` (`id`)"
        ") ENGINE=InnoDB"
    )

    tables['lectures'] = (
        "CREATE TABLE `lectures` ("
        "  `id` int(11) NOT NULL AUTO_INCREMENT,"
        "  `course_id` int(11) NOT NULL,"
        "  `title` varchar(100) NOT NULL,"
        "  `description` text,"
        "  PRIMARY KEY (`id`),"
        "  FOREIGN KEY (`course_id`) REFERENCES `courses` (`id`)"
        ") ENGINE=InnoDB"
    )

    tables['assignments'] = (
        "CREATE TABLE `assignments` ("
        "  `id` int(11) NOT NULL AUTO_INCREMENT,"
        "  `lecture_id` int(11) NOT NULL,"
        "  `title` varchar(100) NOT NULL,"
        "  `description` text,"
        "  PRIMARY KEY (`id`),"
        "  FOREIGN KEY (`lecture_id`) REFERENCES `lectures` (`id`)"
        ") ENGINE=InnoDB"
    )

    tables['submissions'] = (
        "CREATE TABLE `submissions` ("
        "  `id` int(11) NOT NULL AUTO_INCREMENT,"
        "  `assignment_id` int(11) NOT NULL,"
        "  `student_id` int(11) NOT NULL,"
        "  `content` text,"
        "  `grade` varchar(10),"
        "  PRIMARY KEY (`id`),"
        "  FOREIGN KEY (`assignment_id`) REFERENCES `assignments` (`id`),"
        "  FOREIGN KEY (`student_id`) REFERENCES `users` (`id`)"
        ") ENGINE=InnoDB"
    )

    tables['course_applications'] = (
        "CREATE TABLE `course_applications` ("
        "  `id` int(11) NOT NULL AUTO_INCREMENT,"
        "  `student_id` int(11) NOT NULL,"
        "  `course_id` int(11) NOT NULL,"
        "  `status` varchar(20) NOT NULL,"
        "  PRIMARY KEY (`id`),"
        "  FOREIGN KEY (`student_id`) REFERENCES `users` (`id`),"
        "  FOREIGN KEY (`course_id`) REFERENCES `courses` (`id`)"
        ") ENGINE=InnoDB"
    )

    for table_name in tables:
        table_description = tables[table_name]
        try:
            print(f"Creating table {table_name}: ", end='')
            cursor.execute(table_description)
            print("OK")
        except mysql.connector.Error as err:
            if err.errno == errorcode.ER_TABLE_EXISTS_ERROR:
                print("already exists.")
            else:
                print(err.msg)

    # Insert initial data
    add_user = ("INSERT INTO users "
                "(username, password, role) "
                "VALUES (%s, %s, %s)")
    users = [
        ('admin', 'adminpassword', 'admin'),
        ('teacher1', 'teacherpassword', 'teacher'),
        ('student1', 'studentpassword', 'student'),
    ]

    for user in users:
        cursor.execute(add_user, user)
        connection.commit()

    print("Initial data inserted successfully")

except mysql.connector.Error as err:
    print(err)
finally:
    cursor.close()
    connection.close()
