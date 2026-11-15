import sqlite3

DATABASE = 'demo3c.db'

conn = sqlite3.connect(
    DATABASE,
    autocommit=True
)

conn.execute('PRAGMA foreign_keys = ON')


def show_courses(conn, student_id):
    # Print the student's current courses.
    sql = '''
        SELECT c.course_id, c.title
        FROM courses AS c
        JOIN enrollment AS e
          ON c.course_id = e.course_id
        WHERE e.student_id = ?
        ORDER BY c.course_id
    '''

    rows = conn.execute(
        sql,
        (student_id,)
    ).fetchall()

    print(f'Courses for student {student_id}:')

    for row in rows:
        print(f'  {row[0]}: {row[1]}')

    print()


def reset_alice(conn):
    # Put Alice (student 1) back in courses 101 and 103.
    conn.execute(
        'DELETE FROM enrollment WHERE student_id = ?',
        (1,)
    )

    conn.execute(
        '''
        INSERT INTO enrollment(student_id, course_id)
        VALUES (?, ?)
        ''',
        (1, 101)
    )

    conn.execute(
        '''
        INSERT INTO enrollment(student_id, course_id)
        VALUES (?, ?)
        ''',
        (1, 103)
    )


delete_sql = '''
    DELETE FROM enrollment
    WHERE student_id = ?
      AND course_id = ?
'''

insert_sql = '''
    INSERT INTO enrollment(student_id, course_id)
    VALUES (?, ?)
'''


def move_student(conn, student_id, old_id, new_id):
    try:
        conn.execute('BEGIN')
        conn.execute(delete_sql, (student_id, old_id))
        conn.execute(insert_sql, (student_id, new_id))
        conn.execute('COMMIT')
        print('Move completed.')

    except sqlite3.Error as e:
        if conn.in_transaction:
            conn.execute('ROLLBACK')
        print('Move failed:', e)


# Required tests

reset_alice(conn)

print('Starting state:')
show_courses(conn, 1)

print('Test 1: successful move 101 -> 102')
move_student(conn, 1, 101, 102)
show_courses(conn, 1)

print('Test 2: failed move 103 -> 102')
move_student(conn, 1, 103, 102)
show_courses(conn, 1)

conn.close()