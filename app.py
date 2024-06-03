from flask import Flask, render_template, request, redirect, url_for, session
import sqlite3

app = Flask(__name__)


def get_db_connection():
    conn = sqlite3.connect('database.db')
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS Users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL
        )
    ''')
    c.execute('''
        CREATE TABLE IF NOT EXISTS TravelDetails (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            travel_date TEXT NOT NULL,
            travel_time TEXT NOT NULL,
            departure TEXT NOT NULL,
            destination TEXT NOT NULL,
            FOREIGN KEY (user_id) REFERENCES Users (id)
        )
    ''')
    conn.commit()
    conn.close()

@app.route('/')
def index():
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        conn = get_db_connection()
        user = conn.execute('SELECT * FROM Users WHERE username = ? AND password = ?', (username, password)).fetchone()
        conn.close()
        if user:
            session['username'] = user['username']
            return redirect(url_for('travel_details'))
        else:
            return render_template('login.html', error='Invalid username or password')
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        conn = get_db_connection()
        try:
            conn.execute('INSERT INTO Users (username, password) VALUES (?, ?)', (username, password))
            conn.commit()
        except sqlite3.IntegrityError:
            return render_template('register.html', error='Username already exists')
        conn.close()
        return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/add_travel_detail', methods=['GET', 'POST'])
def add_travel_detail():
    if 'username' not in session:
        return redirect(url_for('login'))
    if request.method == 'POST':
        username = session['username']
        travel_date = request.form['travel_date']
        travel_time = request.form['travel_time']
        departure = request.form['departure']
        destination = request.form['destination']
        conn = get_db_connection()
        conn.execute('INSERT INTO TravelDetails (user_id, travel_date, travel_time, departure, destination) VALUES ((SELECT id FROM Users WHERE username = ?), ?, ?, ?, ?)',
                     (username, travel_date, travel_time, departure, destination))
        conn.commit()
        conn.close()
        return redirect(url_for('travel_details'))
    return render_template('add_travel_detail.html')

@app.route('/travel_details')
def travel_details():
    if 'username' not in session:
        return redirect(url_for('login'))
    conn = get_db_connection()
    travel_details = conn.execute('SELECT * FROM TravelDetails WHERE user_id = (SELECT id FROM Users WHERE username = ?)', (session['username'],)).fetchall()
    conn.close()
    return render_template('travel_details.html', travel_details=travel_details)

@app.route('/delete_travel_detail/<int:travel_id>', methods=['POST'])
def delete_travel_detail(travel_id):
    if 'username' not in session:
        return redirect(url_for('login'))
    conn = get_db_connection()
    conn.execute('DELETE FROM TravelDetails WHERE id = ? AND user_id = (SELECT id FROM Users WHERE username = ?)', (travel_id, session['username']))
    conn.commit()
    conn.close()
    return redirect(url_for('travel_details'))

@app.route('/edit_travel_detail/<int:travel_id>', methods=['GET', 'POST'])
def edit_travel_detail(travel_id):
    if 'username' not in session:
        return redirect(url_for('login'))
    conn = get_db_connection()
    travel_detail = conn.execute('SELECT * FROM TravelDetails WHERE id = ? AND user_id = (SELECT id FROM Users WHERE username = ?)', (travel_id, session['username'])).fetchone()
    if request.method == 'POST':
        travel_date = request.form['travel_date']
        travel_time = request.form['travel_time']
        departure = request.form['departure']
        destination = request.form['destination']
        conn.execute('UPDATE TravelDetails SET travel_date = ?, travel_time = ?, departure = ?, destination = ? WHERE id = ? AND user_id = (SELECT id FROM Users WHERE username = ?)',
                     (travel_date, travel_time, departure, destination, travel_id, session['username']))
        conn.commit()
        conn.close()
        return redirect(url_for('travel_details'))
    conn.close()
    return render_template('edit_travel_detail.html', travel_detail=travel_detail)

@app.route('/logout')
def logout():
    session.pop('username', None)
    return redirect(url_for('login'))

if __name__ == '__main__':
    init_db()
    app.run(debug=True)
