import bcrypt
from flask import Flask, render_template, request, redirect, url_for, session, flash
import mysql.connector
import requests, datetime
from flask_bcrypt import Bcrypt

app = Flask(__name__, template_folder='Templates')

app.secret_key = 'your_secret_key'
API_KEY = 'b1645cec058c1e5a993bd1aaa83c561f'
conn = mysql.connector.connect(
    host="localhost",
    user="root",
    password="nisha@1002",
    database="weather_app")
cursor = conn.cursor()

@app.route('/')
def login():
    return render_template("login.html")

@app.route('/login_validation', methods=['POST'])
def login_validation():
    username = request.form.get('Uname')
    password = request.form.get('Pass')
    
    # Validate the login credentials
    cursor.execute("SELECT * FROM login WHERE username = %s", (username,))
    user = cursor.fetchone()

    if user and bcrypt.checkpw(password.encode('utf-8'), user[2].encode('utf-8')):  # Assuming `user[2]` is the password field
        session['username'] = username  # Set username in session
        return redirect(url_for('home'))
    else:
        flash('Invalid username or password. Please try again.')
        return redirect(url_for('login'))


@app.route('/home')
def home():
    if 'username' not in session:
        flash('Please log in to continue.')
        return redirect(url_for('login'))
    return render_template("home.html")

@app.route('/add_user', methods=['POST'])
def add_user():
    username = request.form.get('Uname')
    email = request.form.get('Email')
    password = request.form.get('Pass')

    # Hash the password
    hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())

    # Store the hashed password in the database
    cursor.execute("INSERT INTO login (username, password, email) VALUES (%s, %s, %s)", (username, hashed_password, email))
    conn.commit()

    flash('User registered successfully! Please log in.')
    return redirect(url_for('login'))

@app.route('/register')
def register():
    return render_template("register.html")

# Weather route
@app.route('/weather', methods=['POST'])
def weather():
    if 'username' not in session:
        flash('Please log in to access weather data.')
        return redirect(url_for('login'))

    city = request.form['city']
    # Current weather API call
    current_url = f'http://api.openweathermap.org/data/2.5/weather?q={city}&appid={API_KEY}&units=metric'
    current_response = requests.get(current_url)
    current_data = current_response.json()

    if current_data['cod'] == 200:
        weather_data = {
            'city': city,
            'country': current_data['sys']['country'],
            'temperature': current_data['main']['temp'],
            'description': current_data['weather'][0]['description'],
            'icon': current_data['weather'][0]['icon'],
            'wind_speed': current_data['wind']['speed'],
            'pressure': current_data['main']['pressure'],
            'humidity': current_data['main']['humidity'],
            'sunrise': datetime.datetime.fromtimestamp(current_data['sys']['sunrise']).strftime('%H:%M:%S'),
            'sunset': datetime.datetime.fromtimestamp(current_data['sys']['sunset']).strftime('%H:%M:%S'),
            'day': datetime.datetime.now().strftime('%A'),
            'date': datetime.datetime.now().strftime('%Y-%m-%d')
        }
        
        # Save weather search history in the database
        username = session['username']
        search_time = datetime.datetime.now().strftime('%H:%M:%S')
        search_date = datetime.datetime.now().strftime('%Y-%m-%d')

        cursor.execute('''
    INSERT INTO weather_search_history 
    (username, city, country, temperature, description, wind_speed, pressure, humidity, sunrise, sunset, search_date, search_time, icon)
    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
''', (username, city, weather_data['country'], weather_data['temperature'], 
      weather_data['description'], weather_data['wind_speed'], weather_data['pressure'], 
      weather_data['humidity'], weather_data['sunrise'], weather_data['sunset'], search_date, search_time, weather_data['icon']))

        
        conn.commit()

        return render_template('weather.html', weather=weather_data)
    else:
        error_message = current_data['message']
        return error_message

@app.route('/history')
def history():
    if 'username' not in session:
        flash('Please log in to view your search history.')
        return redirect(url_for('login'))

    username = session['username']

    # Fetch weather search history for the logged-in user
    cursor.execute('''
        SELECT city, country, temperature, description, wind_speed, pressure, humidity, sunrise, sunset, search_date, search_time, icon
        FROM weather_search_history
        WHERE username = %s
        ORDER BY search_date DESC, search_time DESC
    ''', (username,))
    
    search_history = cursor.fetchall()

    return render_template('history.html', history=search_history)




@app.route('/logout')
def logout():
    session.pop('username', None)
    flash('You have successfully logged out.')
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(debug=True)
